import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

from analysis.regression import (
    run_main_if_models_missing_or_empty,
    predict_price_by_quartier_surface
)

from streamlit_utils import (
    format_price, apply_css, styled_chart, kpi, section_title, insight_card,
    load_acheteurs, load_data,
    NAVY, GOLD, BLUE, LIGHT, WHITE, GREY, GREEN, RED,
    CHART_COLORS, PLOTLY_LAYOUT, MODE_META
)

st.set_page_config(
    page_title="Observatoire Immobilier Toulon",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# INITIALIZATION & MODELS
# ─────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[0]
models_path = project_root / "data" / "models_by_quartier.json"
run_main_if_models_missing_or_empty(models_path)

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "selected_quartiers" not in st.session_state:
    st.session_state.selected_quartiers = []
if "selected_sources" not in st.session_state:
    st.session_state.selected_sources = []
if "selected_types" not in st.session_state:
    st.session_state.selected_types = []

# ─────────────────────────────────────────────
# SIDEBAR VISIBILITY MANAGEMENT
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Keep sidebar toggle button always visible */
    [data-testid="stSidebarCollapseButton"] {
        display: block !important;
        visibility: visible !important;
        z-index: 999 !important;
    }
    
    /* Keep header minimal but with toggle button visible */
    header {
        display: flex !important;
        align-items: center !important;
        min-height: 60px !important;
        background: transparent !important;
        border: none !important;
    }
    
    /* Ensure toggle button is always clickable */
    header button {
        visibility: visible !important;
        display: inline-flex !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_comparaison():
    file_path = "data/comparaison_marche.csv"
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

@st.cache_data
def compute_comparaison_lbc():
    """Compare annonces LeBonCoin vs médiane DVF par type de bien et surface similaire."""
    lbc_path = "acheteur/data/marche_leboncoin_clean.csv"
    dvf_path = "data/dvf_toulon.csv" if os.path.exists("data/dvf_toulon.csv") else "data/dvf_toulon_2020_now.csv"
    if not os.path.exists(lbc_path) or not os.path.exists(dvf_path):
        return pd.DataFrame()
    try:
        lbc = pd.read_csv(lbc_path, encoding='utf-8-sig')
        dvf = pd.read_csv(dvf_path, encoding='utf-8-sig')
    except Exception:
        return pd.DataFrame()

    # Normalise DVF
    if 'surface_m2' in dvf.columns:
        dvf = dvf.rename(columns={'surface_m2': 'surface'})
    dvf['prix_m2'] = pd.to_numeric(dvf['prix_m2'], errors='coerce')
    dvf['surface']  = pd.to_numeric(dvf['surface'],  errors='coerce')

    # Normalise LBC
    for col in ['prix_m2', 'surface_m2', 'prix']:
        if col in lbc.columns:
            lbc[col] = pd.to_numeric(lbc[col], errors='coerce')

    resultats = []
    for _, row in lbc.iterrows():
        pm2  = row.get('prix_m2')
        surf = row.get('surface_m2')
        prix_annonce = row.get('prix')
        quartier = row.get('quartier', '')
        
        if pd.isna(pm2) or pm2 <= 0 or pd.isna(surf) or surf <= 0:
            continue

        # --- NOUVELLE LOGIQUE : PREDICTION PAR REGRESSION ---
        prix_predit = None
        if pd.notna(quartier) and str(quartier).strip():
            try:
                prix_predit = predict_price_by_quartier_surface(quartier, surf, models_path)
            except Exception:
                prix_predit = None
        
        # Fallback sur l'ancienne méthode si pas de prédiction possible
        type_b = str(row.get('type_bien', ''))
        keyword = type_b.split()[0] if type_b else ''

        # Comparables DVF : même type, surface ±30%
        dvf_type = dvf[dvf['type_bien'].str.contains(keyword, case=False, na=False)] if keyword and 'type_bien' in dvf.columns else dvf
        comparables = dvf_type[
            dvf_type['surface'].between(surf * 0.7, surf * 1.3) &
            dvf_type['prix_m2'].notna() & (dvf_type['prix_m2'] > 0)
        ]
        
        # Fallback : juste par type si pas assez de comparables
        if len(comparables) < 3:
            comparables = dvf_type[dvf_type['prix_m2'].notna() & (dvf_type['prix_m2'] > 0)]
        
        prix_marche_m2 = comparables['prix_m2'].mean() if len(comparables) >= 3 else None
        
        # Utilisation du prix prédit (total) si disponible, sinon prix marché m2 * surface
        if prix_predit is not None:
            prix_comparaison = prix_predit
            methode = "Régression"
        elif prix_marche_m2 is not None:
            prix_comparaison = prix_marche_m2 * surf
            methode = "Moyenne Quartier"
        else:
            continue

        ecart = prix_annonce - prix_comparaison
        ecart_pct = (ecart / prix_comparaison) * 100
        
        # Définition "Bonne Affaire" : si prix annonce est au moins 10% sous le prix prédit
        is_bonne_affaire = ecart_pct <= -10

        resultats.append({
            'url':            row.get('url', ''),
            'source':         'LeBonCoin',
            'quartier':       str(quartier) if pd.notna(quartier) and str(quartier).strip() else 'Non renseigné',
            'surface':        surf,
            'type_bien':      type_b,
            'titre':          row.get('titre', ''),
            'prix_annonce':   prix_annonce,
            'prix_estime':    round(prix_comparaison, 0),
            'ecart_pct':      round(ecart_pct, 1),
            'bonne_affaire':  "OUI" if is_bonne_affaire else "NON",
            'methode':        methode
        })
    return pd.DataFrame(resultats)

# ─────────────────────────────────────────────
# THEME & CSS
# ─────────────────────────────────────────────
# (Couleurs et styles importés depuis streamlit_utils)

apply_css()
st.title("🏙️ Observatoire Immobilier - Toulon (DVF)")

# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────
import re as _re

def _extract_from_title(df):
    """Extrait surface et nb_pièces depuis les titres quand les colonnes sont vides."""
    if 'titre' not in df.columns:
        return df

    titles = df['titre'].astype(str)

    # Surface : "95 m²", "95 m2", "95 m", "95m²"
    surf_from_title = titles.str.extract(r'(\d{2,3})\s*m[²2]?\b', expand=False)
    surf_from_title = pd.to_numeric(surf_from_title, errors='coerce')
    # Filtre valeurs aberrantes
    surf_from_title = surf_from_title.where(surf_from_title.between(10, 500))

    # Pièces : "4 pièces", "4 pieces", "4 p ", "T4", "F4"
    pieces_from_title = titles.str.extract(
        r'(\d)\s*(?:pi[eè]ces?|p\b)|(?:[tTfF])(\d)\b', expand=True
    ).bfill(axis=1).iloc[:, 0]
    pieces_from_title = pd.to_numeric(pieces_from_title, errors='coerce')
    pieces_from_title = pieces_from_title.where(pieces_from_title.between(1, 10))

    # Colonnes cibles selon le fichier (acheteurs = surface_min, marché = surface_m2/surface)
    for surf_col in ['surface_min', 'surface_m2', 'surface']:
        if surf_col in df.columns:
            df[surf_col] = pd.to_numeric(df[surf_col], errors='coerce')
            df[surf_col] = df[surf_col].fillna(surf_from_title)
            break
    else:
        df['surface_min'] = surf_from_title

    for pieces_col in ['nb_pieces']:
        if pieces_col in df.columns:
            df[pieces_col] = pd.to_numeric(df[pieces_col], errors='coerce')
            df[pieces_col] = df[pieces_col].fillna(pieces_from_title)
        else:
            df['nb_pieces'] = pieces_from_title

    return df

@st.cache_data(ttl=60)
def load_acheteurs_data():
    path = "acheteur/data/rapport_acheteurs.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, encoding='utf-8-sig')
        # S'assurer que les colonnes numériques sont bien typées pour Streamlit
        for col in ['budget_max', 'surface_min', 'nb_pieces']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data
def load_data(data_type="DVF"):
    if data_type == "DVF":
        file_path = "data/dvf_toulon.csv" if os.path.exists("data/dvf_toulon.csv") else "data/dvf_toulon_2020_now.csv"
        if not os.path.exists(file_path):
            st.error(f"Fichier {file_path} introuvable.")
            return pd.DataFrame()
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df['date_mutation'] = pd.to_datetime(df['date_mutation'])
        if 'prix_vente' in df.columns:
            df = df.rename(columns={'prix_vente': 'budget', 'surface_m2': 'surface'})
        else:
            df['prix_m2'] = df['budget'] / df['surface']
            df.loc[df['surface'] <= 0, 'prix_m2'] = None

    elif data_type == "LBC":
        file_path = "acheteur/data/marche_leboncoin_clean.csv"
        if not os.path.exists(file_path):
            file_path = "acheteur/data/marche_leboncoin.csv"
        if not os.path.exists(file_path):
            st.error("Fichier LeBonCoin introuvable. Lancez : python acheteur/leboncoin_crawler.py")
            return pd.DataFrame()
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df = _extract_from_title(df)
        # Normalise vers les colonnes standard de l'app
        df = df.rename(columns={'prix': 'budget', 'surface_m2': 'surface'})
        if 'surface' not in df.columns and 'surface_m2' in df.columns:
            df = df.rename(columns={'surface_m2': 'surface'})
        # Nettoyage numérique
        for col in ['budget', 'surface', 'prix_m2']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.extract(r'(\d[\d\s]*)')[0].str.replace(r'\s','',regex=True),
                    errors='coerce'
                )
        # Recalcul prix_m2 si manquant
        mask = df['surface'].gt(0) & df['budget'].notna()
        df.loc[mask, 'prix_m2'] = (df.loc[mask, 'budget'] / df.loc[mask, 'surface']).round(0)
        # Quartier : null si "Non precise"
        if 'quartier' in df.columns:
            df['quartier'] = df['quartier'].replace({'Non precise': None, 'Non précisé': None})
            df['quartier'] = df['quartier'].fillna("Quartier non renseigné")
        # Date de publication réelle de l'annonce
        date_col = next((c for c in ['date_publication', 'date_crawl'] if c in df.columns), None)
        if date_col:
            df['date_mutation'] = pd.to_datetime(df[date_col], errors='coerce').fillna(pd.Timestamp.now())
        else:
            df['date_mutation'] = pd.Timestamp.now()

    else:  # Annonces Bien'Ici
        # Priorité : fichier le plus récent de la branche data
        candidates = [
            "data/annonces_toulon.csv",
            "data/clean_annonces_toulon_clean.csv",
            "data/annonces_clean.csv",
            "data/annonces_toulon_clean.csv",
        ]
        file_path = next((p for p in candidates if os.path.exists(p)), None)
        if file_path is None:
            st.error("Aucun fichier d'annonces Bien'Ici trouvé.")
            return pd.DataFrame()
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        # Normalisation colonnes selon le fichier chargé
        if 'prix_total' in df.columns:
            # Format clean_annonces_toulon_clean.csv
            df = df.rename(columns={
                'prix_total': 'budget',
                'prix_m2_final': 'prix_m2',
                'date_publication': 'date_mutation',
            })
        elif 'prix_vente' in df.columns:
            df = df.rename(columns={'prix_vente': 'budget', 'surface_m2': 'surface'})
        else:
            df = df.rename(columns={'Prix_total_net': 'budget', 'Surface_m2': 'surface', 'Quartier': 'quartier'})
            pm2 = [c for c in df.columns if 'm2' in c.lower() and c != 'surface']
            if pm2:
                df = df.rename(columns={pm2[0]: 'prix_m2'})

        if 'date_mutation' not in df.columns:
            df['date_mutation'] = pd.Timestamp.now()
        else:
            df['date_mutation'] = pd.to_datetime(df['date_mutation'], errors='coerce').fillna(pd.Timestamp.now())
    return df

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 16px 0 24px;">
        <div style="font-size:2rem;">🏙️</div>
        <div style="font-size:1.1rem; font-weight:700; color:{GOLD}; margin-top:6px;">Observatoire</div>
        <div style="font-size:0.8rem; color:#94A3B8; margin-top:2px;">Immobilier Toulon</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748B; font-weight:600; margin-bottom:8px;">Source de données</p>', unsafe_allow_html=True)
    data_mode = st.radio(
        "",
        ["Ventes Passées (DVF)", "Annonces Vendeurs (Bien'Ici)", "Annonces Vendeurs (LeBonCoin)", "Comparaison Marché", "Profils Acheteurs"],
        label_visibility="collapsed"
    )
    mode_key = (
        "DVF"      if "DVF"        in data_mode else
        "LBC"      if "LeBonCoin"  in data_mode else
        "Acheteurs" if "Acheteurs" in data_mode else
        "Comparaison" if "Comparaison" in data_mode else
        "Annonces"
    )

# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────
# MODE_META importé depuis streamlit_utils
title, subtitle, icon = MODE_META[mode_key]

st.markdown(f"""
<div class="hero">
    <div class="hero-badge">{icon} Toulon · Var (83)</div>
    <h1 class="hero-title">Observatoire Immobilier — {title}</h1>
    <p class="hero-subtitle">{subtitle}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MODE : ACHETEURS
# ─────────────────────────────────────────────
if mode_key == "Acheteurs":
    df_ach = load_acheteurs_data()

    if df_ach.empty:
        st.warning("Aucune donnée acheteur. Lancez : `python acheteur/run_all.py`")
    else:
        with st.sidebar:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748B; font-weight:600; margin-bottom:8px;">Filtres</p>', unsafe_allow_html=True)
            budget_range = st.slider(
                "Budget acheteur (€)",
                min_value=0,
                max_value=500000,
                value=(0, 500000),
                step=10000
            )

            budget_min, budget_max = budget_range
            # ─────────────────────────────
            # FILTRE BUDGET
            # ─────────────────────────────
            mask_budget = (
                (df_ach["budget_max"] >= budget_min) &
                (df_ach["budget_max"] <= budget_max)
            )

            df_ach = df_ach[mask_budget]

            df_ach["budget_format"] = df_ach["budget_max"].apply(format_price)
            sources_dispo = sorted(df_ach['source'].dropna().unique().tolist()) if 'source' in df_ach.columns else []
            # Filtrer la sélection précédente pour ne garder que les sources disponibles
            sources_sel = st.multiselect("Source", sources_dispo, 
                                         default=[s for s in st.session_state.selected_sources if s in sources_dispo],
                                         key="selected_sources")
            
            types_bien = sorted(df_ach['type_bien'].dropna().unique().tolist()) if 'type_bien' in df_ach.columns else []
            types_sel = st.multiselect("Type de bien", types_bien, 
                                       default=[t for t in st.session_state.selected_types if t in types_bien],
                                       key="selected_types")

        mask_ach = (
            (df_ach["budget_max"] >= budget_min) &
            (df_ach["budget_max"] <= budget_max)
        )
        if 'source' in df_ach.columns and sources_sel:
            mask_ach &= df_ach['source'].isin(sources_sel)
        if 'type_bien' in df_ach.columns and types_sel:
            mask_ach &= df_ach['type_bien'].isin(types_sel)
        dfa = df_ach[mask_ach].copy()

        tab_a1, tab_a2, tab_a3, tab_a4 = st.tabs([
            "Vue d'ensemble", "Budgets & Surfaces", "Quartiers & Critères", "Données brutes"
        ])

        with tab_a1:
            budget_med = dfa['budget_max'].median() if 'budget_max' in dfa.columns and dfa['budget_max'].notna().any() else None
            surf_med   = dfa['surface_min'].median() if 'surface_min' in dfa.columns and dfa['surface_min'].notna().any() else None
            pieces_med = dfa['nb_pieces'].median()   if 'nb_pieces' in dfa.columns   and dfa['nb_pieces'].notna().any()   else None

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(kpi("Profils collectés", f"{len(dfa):,}", "navy"), unsafe_allow_html=True)
            c2.markdown(kpi("Budget médian", f"{budget_med:,.0f} €" if budget_med else "N/A", "gold"), unsafe_allow_html=True)
            c3.markdown(kpi("Surface souhaitée", f"{surf_med:.0f} m²" if surf_med else "N/A", ""), unsafe_allow_html=True)
            c4.markdown(kpi("Nb pièces médian", f"{pieces_med:.0f}" if pieces_med else "N/A", "green"), unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if 'type_bien' in dfa.columns:
                    section_title("Type de bien recherché")
                    fig = px.pie(dfa['type_bien'].value_counts().reset_index(),
                                 values='count', names='type_bien', hole=0.5,
                                 color_discrete_sequence=CHART_COLORS)
                    fig.update_traces(
                        textposition='inside', textinfo='percent',
                        insidetextfont=dict(size=12, color='white'),
                        marker=dict(line=dict(color='white', width=2)),
                        hovertemplate='<b>%{label}</b><br>%{value} profils<br>%{percent}<extra></extra>',
                    )
                    fig.update_layout(legend=dict(orientation='v', x=1.0, y=0.5,
                        font=dict(size=11, color='#111827'), bgcolor='rgba(0,0,0,0)'))
                    st.plotly_chart(styled_chart(fig), use_container_width=True)

            with col2:
                if 'type_achat' in dfa.columns:
                    section_title("Motif d'achat")
                    fig = px.pie(dfa['type_achat'].value_counts().reset_index(),
                                 values='count', names='type_achat', hole=0.5,
                                 color_discrete_sequence=[NAVY, GOLD, BLUE, GREEN])
                    fig.update_traces(
                        textposition='inside', textinfo='percent',
                        insidetextfont=dict(size=12, color='white'),
                        marker=dict(line=dict(color='white', width=2)),
                        hovertemplate='<b>%{label}</b><br>%{value} profils<br>%{percent}<extra></extra>',
                    )
                    fig.update_layout(legend=dict(orientation='v', x=1.0, y=0.5,
                        font=dict(size=11, color='#111827'), bgcolor='rgba(0,0,0,0)'))
                    st.plotly_chart(styled_chart(fig), use_container_width=True)

            if 'source' in dfa.columns:
                section_title("Profils par source de données")
                df_src = dfa['source'].value_counts().reset_index()
                fig = px.bar(df_src, x='source', y='count',
                             color='count', color_continuous_scale=[[0, BLUE], [1, NAVY]],
                             labels={'source': '', 'count': 'Nb profils'})
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(styled_chart(fig, height=280), use_container_width=True)

        with tab_a2:
            col1, col2 = st.columns(2)

            with col1:
                if 'budget_max' in dfa.columns and dfa['budget_max'].notna().any():
                    section_title("Distribution des budgets")
                    df_b = dfa[dfa['budget_max'].between(50_000, 2_000_000)]
                    fig = px.histogram(df_b, x='budget_max', nbins=35,
                                       labels={'budget_max': 'Budget (€)', 'count': 'Nb acheteurs'},
                                       color_discrete_sequence=[BLUE])
                    fig.update_traces(marker_line_color='white', marker_line_width=1)
                    st.plotly_chart(styled_chart(fig), use_container_width=True)

            with col2:
                if 'surface_min' in dfa.columns and dfa['surface_min'].notna().any():
                    section_title("Surface souhaitée")
                    df_s = dfa[dfa['surface_min'].between(10, 500)]
                    fig = px.histogram(df_s, x='surface_min', nbins=25,
                                       labels={'surface_min': 'Surface (m²)', 'count': 'Nb acheteurs'},
                                       color_discrete_sequence=[GOLD])
                    fig.update_traces(marker_line_color='white', marker_line_width=1)
                    st.plotly_chart(styled_chart(fig), use_container_width=True)

            if 'type_bien' in dfa.columns and 'budget_max' in dfa.columns and dfa['budget_max'].notna().any():
                section_title("Budget médian par type de bien")
                df_btype = dfa.groupby('type_bien')['budget_max'].median().reset_index().sort_values('budget_max', ascending=True)
                fig = px.bar(df_btype, x='budget_max', y='type_bien', orientation='h',
                             color='budget_max', color_continuous_scale=[[0, BLUE], [1, NAVY]],
                             labels={'type_bien': '', 'budget_max': 'Budget médian (€)'})
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(styled_chart(fig, height=300), use_container_width=True)

        with tab_a3:
            col1, col2 = st.columns(2)

            with col1:
                col_q = 'quartier_souhaite' if 'quartier_souhaite' in dfa.columns else ('quartier' if 'quartier' in dfa.columns else None)
                if col_q:
                    section_title("Quartiers les plus demandés")
                    q_counts = {}
                    for val in dfa[col_q].dropna():
                        for q in str(val).split(','):
                            q = q.strip()
                            if q and q not in ('Non precise', 'Non précisé', ''):
                                q_counts[q] = q_counts.get(q, 0) + 1
                    if q_counts:
                        df_q = pd.DataFrame(list(q_counts.items()), columns=['quartier', 'nb']).sort_values('nb').tail(15)
                        fig = px.bar(df_q, x='nb', y='quartier', orientation='h',
                                     color='nb', color_continuous_scale=[[0, '#FDE68A'], [1, GOLD]],
                                     labels={'nb': 'Demandes', 'quartier': ''})
                        fig.update_traces(marker_line_width=0)
                        st.plotly_chart(styled_chart(fig), use_container_width=True)
                    else:
                        st.info("Pas encore de données de quartier.")

            with col2:
                if 'criteres' in dfa.columns:
                    section_title("Critères les plus recherchés")
                    c_counts = {}
                    for val in dfa['criteres'].dropna():
                        for c in str(val).split(','):
                            c = c.strip()
                            if c:
                                c_counts[c] = c_counts.get(c, 0) + 1
                    if c_counts:
                        df_c = pd.DataFrame(list(c_counts.items()), columns=['critere', 'nb']).sort_values('nb').tail(12)
                        fig = px.bar(df_c, x='nb', y='critere', orientation='h',
                                     color='nb', color_continuous_scale=[[0, '#C7D2FE'], [1, NAVY]],
                                     labels={'nb': 'Mentions', 'critere': ''})
                        fig.update_traces(marker_line_width=0)
                        st.plotly_chart(styled_chart(fig), use_container_width=True)

        with tab_a4:
            section_title("Données brutes acheteurs")
            cols_display = [c for c in ['source', 'date_annonce', 'type_bien', 'type_achat',
                                         'budget_max', 'surface_min', 'nb_pieces',
                                         'quartier_souhaite', 'criteres', 'titre', 'url'] if c in dfa.columns]
            df_a4_display = dfa[cols_display].copy()
            # Convertir en datetime pour le tri
            if 'date_annonce' in df_a4_display.columns:
                df_a4_display['date_annonce'] = pd.to_datetime(df_a4_display['date_annonce'])
            # Utiliser column_config pour afficher sans heures et URLs cliquables
            column_config = {}
            if 'date_annonce' in df_a4_display.columns:
                column_config['date_annonce'] = st.column_config.DateColumn(
                    "date_annonce",
                    format="DD/MM/YYYY"
                )
            if 'url' in df_a4_display.columns:
                column_config['url'] = st.column_config.LinkColumn("url")
            st.dataframe(df_a4_display, use_container_width=True, hide_index=True,
                        column_config=column_config if column_config else None)
            st.download_button(
                "Télécharger CSV",
                dfa.to_csv(index=False, encoding='utf-8-sig'),
                "acheteurs_toulon.csv", "text/csv"
            )

# ─────────────────────────────────────────────
# MODE : COMPARAISON MARCHÉ
# ─────────────────────────────────────────────
elif mode_key == "Comparaison":
    df_comp = load_comparaison()
    if df_comp.empty:
        st.warning("Aucune donnée de comparaison. Lancez : `python data/comparateur.py`")
    else:
        with st.sidebar:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748B; font-weight:600; margin-bottom:8px;">Filtres</p>', unsafe_allow_html=True)
            
            unique_quartiers = sorted(df_comp['quartier'].dropna().unique())
            q_selected = st.multiselect("Filtrer par quartier", options=unique_quartiers, default=[])

            # Filtre écart
            ecart_min = st.slider("Écart minimum (%)", -100, 100, -100)
            ecart_max = st.slider("Écart maximum (%)", -100, 100, 100)

        # Filtrage
        mask = (df_comp['ecart_pct'] >= ecart_min) & (df_comp['ecart_pct'] <= ecart_max)
        if q_selected:
            mask = mask & (df_comp['quartier'].isin(q_selected))
        df_filtered = df_comp.loc[mask]

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi("Biens analysés", f"{len(df_filtered)}", "navy"), unsafe_allow_html=True)
        c2.markdown(kpi("Sous-cotés (<-5%)", f"{len(df_filtered[df_filtered['ecart_pct'] < -5])}", "green"), unsafe_allow_html=True)
        c3.markdown(kpi("Écart moyen", f"{df_filtered['ecart_pct'].mean():.1f}%", "gold"), unsafe_allow_html=True)
        c4.markdown(kpi("Sur-cotés (>+5%)", f"{len(df_filtered[df_filtered['ecart_pct'] > 5])}", "red"), unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ── Insights : bonnes affaires Bien'Ici + LBC ──
        def _render_bonnes_affaires(df_ba, source_label, url_label, n=3):
            bonnes = df_ba[df_ba['ecart_pct'] < -10].nsmallest(n, 'ecart_pct')
            if bonnes.empty:
                return False
            cols_ba = st.columns(min(3, len(bonnes)))
            for i, (_, row) in enumerate(bonnes.iterrows()):
                with cols_ba[i % 3]:
                    q    = row.get('quartier', 'N/A')
                    surf = row.get('surface', None)
                    prix = row.get('prix_annonce', row.get('prix_annonce_m2', None))
                    url  = row.get('url', '')
                    methode = row.get('methode', 'DVF')
                    
                    titre = str(row.get('titre', '')) if row.get('titre') else ''
                    parts = []
                    if q and q != 'Non renseigné':
                        parts.append(f"Quartier : {q}")
                    if surf and not pd.isna(surf):
                        parts.append(f"{surf:.0f} m²")
                    if prix and not pd.isna(prix):
                        if prix > 10000: # Probablement un prix total
                            parts.append(f"{format_price(prix)} €")
                        else:
                            parts.append(f"{prix:,.0f} €/m²")
                    if titre:
                        parts.append(titre[:40] + ("…" if len(titre) > 40 else ""))
                    
                    st.markdown(insight_card(
                        f"💎 Bonne affaire · {source_label}",
                        f"Ce bien est {abs(row['ecart_pct']):.1f}% sous-évalué (via {methode})",
                        sub=" · ".join(parts), color="green",
                        url=url if isinstance(url, str) and url.startswith("http") else "",
                        source=url_label
                    ), unsafe_allow_html=True)
            return True

        showed_any = False
        bonnes_bienici = df_filtered[df_filtered['ecart_pct'] < -10]
        if not bonnes_bienici.empty:
            section_title("Meilleures opportunités · Bien'Ici vs DVF")
            _render_bonnes_affaires(df_filtered, "Bien'Ici", "Voir l'annonce Bien'Ici", n=3)
            showed_any = True

        df_lbc_comp = compute_comparaison_lbc()
        if not df_lbc_comp.empty:
            bonnes_lbc = df_lbc_comp[df_lbc_comp['ecart_pct'] < -10]
            if not bonnes_lbc.empty:
                section_title("Meilleures opportunités · LeBonCoin vs DVF")
                _render_bonnes_affaires(df_lbc_comp, "LeBonCoin", "Voir l'annonce LeBonCoin", n=3)
                showed_any = True

        if showed_any:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Analyse Graphique", "Liste des Opportunités"])
        
        with tab1:
            col1, col2 = st.columns([2, 1])
            with col1:
                section_title("Analyse des prix : Annonce vs Marché")
                fig = px.scatter(df_filtered, x='prix_marche_m2', y='prix_annonce_m2',
                                 hover_data=['quartier', 'surface', 'ecart_pct'],
                                 color='ecart_pct', color_continuous_scale='RdYlGn_r',
                                 labels={'prix_marche_m2': 'Prix Marché (€/m²)', 'prix_annonce_m2': 'Prix Annonce (€/m²)'})
                max_v = max(df_filtered['prix_marche_m2'].max(), df_filtered['prix_annonce_m2'].max()) if not df_filtered.empty else 10000
                fig.add_shape(type='line', x0=0, y0=0, x1=max_v, y1=max_v, line=dict(color='grey', dash='dash'))
                st.plotly_chart(styled_chart(fig), use_container_width=True)
            
            with col2:
                section_title("Distribution des écarts (%)")
                fig = px.histogram(df_filtered, x='ecart_pct', nbins=30, color_discrete_sequence=[BLUE])
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with tab2:
            section_title("Détails des annonces et écarts")
            st.dataframe(df_filtered.sort_values('ecart_pct'), use_container_width=True, hide_index=True,
                         column_config={"url": st.column_config.LinkColumn("url")})

# ─────────────────────────────────────────────
# MODE : DVF / ANNONCES
# ─────────────────────────────────────────────
else:
    df = load_data(mode_key)

if mode_key not in ("Acheteurs", "Comparaison") and not df.empty:

    with st.sidebar:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748B; font-weight:600; margin-bottom:8px;">Filtres</p>', unsafe_allow_html=True)

        unique_quartiers = sorted([str(q) for q in df['quartier'].unique() if pd.notna(q)])
        # Filtrer la sélection précédente pour ne garder que les quartiers disponibles
        quartiers = st.multiselect("Secteurs / Quartiers", options=unique_quartiers, 
                                   default=[q for q in st.session_state.selected_quartiers if q in unique_quartiers],
                                   key="selected_quartiers")
        budget_range = st.slider(
        "Budget (€)",
        min_value=0,
        max_value=500000,
        value=(0, 500000),
        step=10000
    )

        budget_min, budget_max = budget_range
        if mode_key == "DVF":
            default_dates = [df['date_mutation'].min().date(), df['date_mutation'].max().date()]
            date_range = st.date_input("Période d'analyse", value=default_dates)
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_date, end_date = date_range
            elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
                start_date = end_date = date_range[0]
            else:
                start_date = end_date = date_range
            mask =  (df['quartier'].isin(quartiers)) & \
                    (df['date_mutation'].dt.date >= start_date) & \
                    (df['date_mutation'].dt.date <= end_date) & \
                    (df['budget'] >= budget_min) & \
                    (df['budget'] <= budget_max)
        else:
            mask = (df['quartier'].isin(quartiers)) & \
                (df['budget'] >= budget_min) & \
                (df['budget'] <= budget_max)

    df_filtered = df.loc[mask]

    # TABS
    if mode_key == "DVF":
        tab_titles = ["Vue d'ensemble", "Analyse par quartier", "Adresses & Rues", "Insights marché", "Données brutes"]
    else:
        tab_titles = ["Vue d'ensemble", "Analyse par quartier", "Liste des annonces"]

    tabs = st.tabs(tab_titles)
    t1, t2, t3 = tabs[0], tabs[1], tabs[2]
    if mode_key == "DVF":
        t_insights = tabs[3]
        t4 = tabs[4]
    else:
        t_insights = None
        t4 = tabs[3] if len(tabs) > 3 else None

    # ── Tab 1 : Vue d'ensemble ──
    with t1:
        c1, c2, c3, c4 = st.columns(4)
        nb   = len(df_filtered)
        prix = df_filtered['budget'].median()
        pm2  = df_filtered['prix_m2'].mean()
        surf = df_filtered['surface'].mean()

        label_nb = "Transactions" if mode_key == "DVF" else "Annonces"
        c1.markdown(kpi(label_nb, f"{nb:,}", "navy"), unsafe_allow_html=True)
        c2.markdown(kpi("Prix médian", f"{prix:,.0f} €", "gold"), unsafe_allow_html=True)
        c3.markdown(kpi("Prix moyen / m²", f"{pm2:,.0f} €", ""), unsafe_allow_html=True)
        c4.markdown(kpi("Surface moyenne", f"{surf:.0f} m²", "green"), unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        if mode_key == "DVF":
            section_title("Évolution du prix au m² (moyenne mensuelle)")
            df_trend = df_filtered.resample('ME', on='date_mutation')['prix_m2'].mean().reset_index()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trend['date_mutation'], y=df_trend['prix_m2'],
                mode='lines+markers',
                line=dict(color=BLUE, width=2.5),
                marker=dict(color=GOLD, size=6, line=dict(color=WHITE, width=1.5)),
                fill='tozeroy',
                fillcolor=f'rgba(46,134,171,0.08)',
                name='Prix/m²'
            ))
            st.plotly_chart(styled_chart(fig, height=320), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            section_title("Répartition des surfaces")
            fig = px.histogram(df_filtered, x='surface', nbins=50, range_x=[0, 200],
                               labels={'surface': 'Surface (m²)', 'count': 'Nombre'},
                               color_discrete_sequence=[NAVY])
            fig.update_traces(marker_line_color='white', marker_line_width=1)
            st.plotly_chart(styled_chart(fig), use_container_width=True)

        with col2:
            section_title("Répartition des prix")
            df_prix = df_filtered[df_filtered['budget'].between(50_000, 2_000_000)]
            fig = px.histogram(df_prix, x='budget', nbins=40,
                               labels={'budget': 'Prix (€)', 'count': 'Nombre'},
                               color_discrete_sequence=[GOLD])
            fig.update_traces(marker_line_color='white', marker_line_width=1)
            st.plotly_chart(styled_chart(fig), use_container_width=True)

    # ── Tab 2 : Quartiers ──
    with t2:
        top_n = 15
        df_vol = df_filtered.groupby('quartier').size().sort_values(ascending=False).reset_index(name='nb')
        top_sections = df_vol.head(top_n)['quartier'].tolist()

        # Pie : top 8 quartiers + Autres
        top_pie = 8
        df_pie = df_vol.head(top_pie).copy()
        if len(df_vol) > top_pie:
            autres_nb = df_vol.iloc[top_pie:]['nb'].sum()
            df_pie = pd.concat([df_pie, pd.DataFrame([{'quartier': 'Autres', 'nb': autres_nb}])], ignore_index=True)

        col1, col2 = st.columns([3, 2])

        with col1:
            section_title(f"Prix au m² médian — Top {top_n} secteurs")
            df_q = df_filtered.groupby('quartier')['prix_m2'].median().sort_values().tail(top_n).reset_index()
            fig = px.bar(df_q, x='prix_m2', y='quartier', orientation='h',
                         color='prix_m2', color_continuous_scale=[[0, BLUE], [1, NAVY]],
                         labels={'prix_m2': '€/m²', 'quartier': ''})
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(styled_chart(fig, height=460), use_container_width=True)

        with col2:
            section_title("Part de marché — Top 8 quartiers")
            fig = px.pie(df_pie, values='nb', names='quartier', hole=0.5,
                         color_discrete_sequence=CHART_COLORS)
            fig.update_traces(
                textposition='inside',
                textinfo='percent',
                insidetextfont=dict(size=12, color='white'),
                marker=dict(line=dict(color='white', width=2)),
                hovertemplate='<b>%{label}</b><br>%{value} annonces<br>%{percent}<extra></extra>',
            )
            fig.update_layout(legend=dict(
                orientation='v', x=1.0, y=0.5,
                font=dict(size=11, color='#111827'),
                bgcolor='rgba(0,0,0,0)',
            ))
            st.plotly_chart(styled_chart(fig, height=460), use_container_width=True)

    # ── Tab Insights : DVF uniquement ──
    if mode_key == "DVF" and t_insights:
        with t_insights:
            section_title("Insights marché — Toulon")

            col_ins1, col_ins2 = st.columns(2)

            # Insight 1 : Tendance prix sur 2 ans
            with col_ins1:
                if df_filtered['prix_m2'].notna().any() and 'date_mutation' in df_filtered.columns:
                    now_dt = df_filtered['date_mutation'].max()
                    recent = df_filtered[df_filtered['date_mutation'] >= now_dt - pd.DateOffset(months=6)]
                    ref_start = now_dt - pd.DateOffset(months=30)
                    ref_end   = now_dt - pd.DateOffset(months=18)
                    old = df_filtered[
                        (df_filtered['date_mutation'] >= ref_start) &
                        (df_filtered['date_mutation'] <= ref_end)
                    ]
                    pm2_recent = recent['prix_m2'].mean()
                    pm2_old    = old['prix_m2'].mean()

                    if pm2_old and pm2_old > 0 and not pd.isna(pm2_recent):
                        evo = (pm2_recent - pm2_old) / pm2_old * 100
                        direction = "augmenté" if evo > 0 else "baissé"
                        ins_color = "green" if evo > 0 else "red"
                        sub_txt = (
                            f"Récent (6 derniers mois) : {pm2_recent:,.0f} €/m² "
                            f"· Référence (il y a 2 ans) : {pm2_old:,.0f} €/m²"
                        )
                        st.markdown(insight_card(
                            "📈 Tendance 2 ans",
                            f"Les prix ont {direction} de {abs(evo):.1f}% sur les 2 dernières années",
                            sub=sub_txt, color=ins_color
                        ), unsafe_allow_html=True)
                    else:
                        st.info("Pas assez d'historique pour calculer la tendance sur 2 ans.")

            # Insight 2 : Comparaison quartiers
            with col_ins2:
                if 'quartier' in df_filtered.columns and df_filtered['prix_m2'].notna().any():
                    q_prices = df_filtered.groupby('quartier')['prix_m2'].median().dropna()
                    q_prices = q_prices[q_prices > 0]
                    if len(q_prices) >= 2:
                        most_exp_q  = q_prices.idxmax()
                        least_exp_q = q_prices.idxmin()
                        diff_pct = (q_prices[most_exp_q] - q_prices[least_exp_q]) / q_prices[least_exp_q] * 100
                        sub_txt = (
                            f"{most_exp_q} : {q_prices[most_exp_q]:,.0f} €/m²"
                            f" · {least_exp_q} : {q_prices[least_exp_q]:,.0f} €/m²"
                        )
                        st.markdown(insight_card(
                            "🏘️ Comparaison quartiers",
                            f"{most_exp_q} est {diff_pct:.0f}% plus cher que {least_exp_q}",
                            sub=sub_txt, color="gold"
                        ), unsafe_allow_html=True)

            # Classement complet des quartiers
            if 'quartier' in df_filtered.columns and df_filtered['prix_m2'].notna().any():
                q_prices = df_filtered.groupby('quartier')['prix_m2'].median().dropna()
                q_prices = q_prices[q_prices > 0]
                if len(q_prices) >= 2:
                    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                    section_title("Classement des quartiers par prix au m²")
                    df_q_rank = q_prices.sort_values(ascending=False).reset_index()
                    df_q_rank.columns = ['Quartier', 'Prix médian (€/m²)']
                    df_q_rank['Prix médian (€/m²)'] = df_q_rank['Prix médian (€/m²)'].round(0).astype(int)
                    min_price = df_q_rank['Prix médian (€/m²)'].min()
                    df_q_rank['vs. moins cher'] = df_q_rank['Prix médian (€/m²)'].apply(
                        lambda x: f"+{((x - min_price) / min_price * 100):.0f}%" if x > min_price else "référence"
                    )
                    df_q_rank.index = range(1, len(df_q_rank) + 1)
                    st.dataframe(df_q_rank, use_container_width=True)

            # ── Corrélations DVF ──
            import numpy as np
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            section_title("Corrélations — Facteurs influençant le prix de vente")

            df_reg = df_filtered[['surface', 'budget', 'prix_m2']].copy()
            if 'annee' in df_filtered.columns:
                df_reg['annee'] = df_filtered['annee']
            df_reg = df_reg.dropna()
            df_reg = df_reg[df_reg['surface'].between(10, 400) & df_reg['budget'].between(10_000, 3_000_000)]

            col_c1, col_c2 = st.columns(2)

            with col_c1:
                section_title("Surface vs Prix de vente")
                if len(df_reg) >= 5:
                    coeffs = np.polyfit(df_reg['surface'], df_reg['budget'], 1)
                    r_corr = np.corrcoef(df_reg['surface'], df_reg['budget'])[0, 1]
                    r2 = r_corr ** 2
                    fig = px.scatter(
                        df_reg, x='surface', y='budget', opacity=0.35,
                        labels={'surface': 'Surface (m²)', 'budget': 'Prix de vente (€)'},
                        color_discrete_sequence=[BLUE],
                    )
                    x0, x1 = df_reg['surface'].min(), df_reg['surface'].max()
                    fig.add_trace(go.Scatter(
                        x=[x0, x1], y=[coeffs[0]*x0 + coeffs[1], coeffs[0]*x1 + coeffs[1]],
                        mode='lines',
                        line=dict(color=GOLD, width=2.5, dash='dash'),
                        name=f'Régression (R²={r2:.2f})',
                    ))
                    fig.update_layout(annotations=[dict(
                        x=0.02, y=0.97, xref='paper', yref='paper',
                        text=f'R² = {r2:.3f}  ·  {coeffs[0]:,.0f} €/m²',
                        showarrow=False,
                        bgcolor='rgba(255,255,255,0.85)',
                        bordercolor=NAVY, borderwidth=1,
                        font=dict(size=11, color=NAVY),
                        align='left',
                    )])
                    st.plotly_chart(styled_chart(fig), use_container_width=True)

            with col_c2:
                section_title("Matrice de corrélation")
                num_cols = {
                    'Surface (m²)': 'surface',
                    'Prix vente (€)': 'budget',
                    'Prix/m²': 'prix_m2',
                }
                if 'annee' in df_reg.columns:
                    num_cols['Année'] = 'annee'
                df_corr_data = df_filtered[[v for v in num_cols.values() if v in df_filtered.columns]].dropna()
                df_corr_data.columns = [k for k, v in num_cols.items() if v in df_filtered.columns]
                corr_mat = df_corr_data.corr()
                labels = corr_mat.columns.tolist()
                z_vals = corr_mat.values.tolist()
                fig = go.Figure(data=go.Heatmap(
                    z=z_vals, x=labels, y=labels,
                    colorscale='RdBu_r', zmin=-1, zmax=1,
                    text=[[f'{v:.2f}' for v in row] for row in z_vals],
                    texttemplate='%{text}',
                    textfont=dict(size=13),
                    hoverongaps=False,
                ))
                st.plotly_chart(styled_chart(fig, height=300), use_container_width=True)

            # Box plots : type de bien + secteur
            col_box1, col_box2 = st.columns(2)

            with col_box1:
                if 'type_bien' in df_filtered.columns:
                    section_title("Prix de vente par type de bien")
                    df_box = df_filtered[df_filtered['budget'].between(10_000, 3_000_000)].copy()
                    fig = px.box(
                        df_box, x='type_bien', y='budget',
                        color='type_bien', color_discrete_sequence=CHART_COLORS,
                        labels={'type_bien': '', 'budget': 'Prix de vente (€)'},
                        points=False,
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(styled_chart(fig, height=380), use_container_width=True)

            with col_box2:
                if 'quartier' in df_filtered.columns:
                    section_title("Prix de vente par secteur (top 12)")
                    df_box_q = df_filtered[df_filtered['budget'].between(10_000, 3_000_000)].copy()
                    # Garder les 12 quartiers les plus représentés
                    top_q = df_box_q['quartier'].value_counts().head(12).index
                    df_box_q = df_box_q[df_box_q['quartier'].isin(top_q)]
                    # Trier par médiane décroissante
                    ordre = df_box_q.groupby('quartier')['budget'].median().sort_values(ascending=True).index.tolist()
                    fig = px.box(
                        df_box_q, x='budget', y='quartier',
                        orientation='h',
                        color='quartier', color_discrete_sequence=CHART_COLORS,
                        category_orders={'quartier': ordre},
                        labels={'quartier': '', 'budget': 'Prix de vente (€)'},
                        points=False,
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(styled_chart(fig, height=380), use_container_width=True)

            # Insight 3 : Bonnes affaires Bien'Ici + LBC
            df_comp_ins = load_comparaison()
            df_lbc_ins  = compute_comparaison_lbc()
            has_bienici = not df_comp_ins.empty and 'ecart_pct' in df_comp_ins.columns
            has_lbc     = not df_lbc_ins.empty  and 'ecart_pct' in df_lbc_ins.columns

            if has_bienici or has_lbc:
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

            if has_bienici:
                section_title("Bonnes affaires · Bien'Ici vs DVF")
                bonnes_bi = df_comp_ins[df_comp_ins['ecart_pct'] < -10].nsmallest(6, 'ecart_pct')
                if not bonnes_bi.empty:
                    cols_b = st.columns(min(3, len(bonnes_bi)))
                    for i, (_, row) in enumerate(bonnes_bi.iterrows()):
                        with cols_b[i % 3]:
                            q    = row.get('quartier', 'N/A')
                            surf = row.get('surface', None)
                            prix = row.get('prix_annonce_m2', None)
                            url  = row.get('url', '')
                            parts = [f"Quartier : {q}"]
                            if surf and not pd.isna(surf):
                                parts.append(f"{surf:.0f} m²")
                            if prix and not pd.isna(prix):
                                parts.append(f"{prix:,.0f} €/m²")
                            st.markdown(insight_card(
                                "💎 Bonne affaire",
                                f"Ce bien est {abs(row['ecart_pct']):.0f}% sous-évalué",
                                sub=" · ".join(parts), color="green",
                                url=url if isinstance(url, str) and url.startswith("http") else "",
                                source="Voir l'annonce Bien'Ici"
                            ), unsafe_allow_html=True)
                else:
                    st.info("Aucune bonne affaire Bien'Ici avec un écart > 10%.")

            if has_lbc:
                section_title("Bonnes affaires · LeBonCoin vs DVF")
                bonnes_lbc = df_lbc_ins[df_lbc_ins['ecart_pct'] < -10].nsmallest(6, 'ecart_pct')
                if not bonnes_lbc.empty:
                    cols_l = st.columns(min(3, len(bonnes_lbc)))
                    for i, (_, row) in enumerate(bonnes_lbc.iterrows()):
                        with cols_l[i % 3]:
                            q     = row.get('quartier', 'Non renseigné')
                            surf  = row.get('surface', None)
                            prix  = row.get('prix_annonce_m2', None)
                            url   = row.get('url', '')
                            titre = str(row.get('titre', ''))
                            parts = []
                            if q and q != 'Non renseigné':
                                parts.append(f"Quartier : {q}")
                            if surf and not pd.isna(surf):
                                parts.append(f"{surf:.0f} m²")
                            if prix and not pd.isna(prix):
                                parts.append(f"{prix:,.0f} €/m²")
                            if titre:
                                parts.append(titre[:40] + ("…" if len(titre) > 40 else ""))
                            st.markdown(insight_card(
                                "💎 Bonne affaire",
                                f"Ce bien est {abs(row['ecart_pct']):.0f}% sous-évalué",
                                sub=" · ".join(parts), color="green",
                                url=url if isinstance(url, str) and url.startswith("http") else "",
                                source="Voir l'annonce LeBonCoin"
                            ), unsafe_allow_html=True)
                else:
                    st.info("Aucune bonne affaire LeBonCoin avec un écart > 10%.")

    # ── Tab 3 : Adresses (DVF) ou Annonces ──
    if mode_key == "DVF" and t4:
        with t3:
            section_title("Volume de ventes par rue et quartier")
            df_tree = df_filtered.groupby(['quartier', 'adresse']).size().reset_index(name='nb_ventes')
            fig = px.treemap(df_tree, path=['quartier', 'adresse'], values='nb_ventes',
                             color='nb_ventes', color_continuous_scale=[[0, '#DBEAFE'], [1, NAVY]])
            st.plotly_chart(styled_chart(fig, height=440), use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                section_title("Dynamique moyenne par quartier")
                df_addr = df_filtered.groupby(['quartier', 'adresse']).size().reset_index(name='nb')
                df_avg  = df_addr.groupby('quartier')['nb'].mean().sort_values().tail(12).reset_index()
                fig = px.bar(df_avg, x='nb', y='quartier', orientation='h',
                             color='nb', color_continuous_scale=[[0, BLUE], [1, NAVY]],
                             labels={'nb': 'Ventes moy./adresse', 'quartier': ''})
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(styled_chart(fig), use_container_width=True)

            with col2:
                section_title("Top 10 adresses actives")
                df_top = df_filtered.groupby(['adresse', 'quartier']).size().reset_index(name='nb')
                df_top = df_top.sort_values('nb').tail(10)
                fig = px.bar(df_top, x='nb', y='adresse', orientation='h',
                             color='nb', color_continuous_scale=[[0, '#FDE68A'], [1, GOLD]],
                             labels={'nb': 'Nb ventes', 'adresse': ''})
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with t4:
            section_title("Dernières transactions DVF")
            df_display_dvf = df_filtered.sort_values('date_mutation', ascending=False).head(200).copy()
            # Rename columns
            df_display_dvf = df_display_dvf.rename(columns={'date_mutation': 'date_publication'})
            # Format columns
            if 'budget' in df_display_dvf.columns:
                df_display_dvf['budget'] = df_display_dvf['budget'].apply(format_price)
            # Sélectionner seulement les colonnes pertinentes
            cols_to_display = [c for c in df_display_dvf.columns if c in 
                              ['date_publication', 'budget', 'prix_m2', 'surface', 'quartier', 'adresse', 'type_local']]
            df_display_dvf = df_display_dvf[cols_to_display]
            # Convertir en datetime pour le tri
            if 'date_publication' in df_display_dvf.columns:
                df_display_dvf['date_publication'] = pd.to_datetime(df_display_dvf['date_publication'])
            # Utiliser column_config pour afficher sans heures
            column_config = {}
            if 'date_publication' in df_display_dvf.columns:
                column_config['date_publication'] = st.column_config.DateColumn(
                    "date_publication",
                    format="DD/MM/YYYY"
                )
            st.dataframe(
                df_display_dvf,
                use_container_width=True, hide_index=True,
                column_config=column_config if column_config else None
            )

    elif mode_key in ("Annonces", "LBC"):
        # ── Tab 3 : Liste des annonces ──
        with t3:
            label = "Bien'Ici" if mode_key == "Annonces" else "LeBonCoin"
            section_title(f"Annonces en cours — {label}")
            df_display_annonces = df_filtered.copy()
            
            # Handle date column - rename date_mutation to date_publication if needed
            if 'date_mutation' in df_display_annonces.columns and 'date_publication' not in df_display_annonces.columns:
                df_display_annonces = df_display_annonces.rename(columns={'date_mutation': 'date_publication'})
            elif 'date_mutation' in df_display_annonces.columns and 'date_publication' in df_display_annonces.columns:
                # Drop date_mutation if date_publication already exists
                df_display_annonces = df_display_annonces.drop(columns=['date_mutation'])
            
            # Format columns
            if 'budget' in df_display_annonces.columns:
                df_display_annonces['budget'] = df_display_annonces['budget'].apply(format_price)
            
            # Sélectionner seulement les colonnes pertinentes
            cols_to_display = [c for c in df_display_annonces.columns if c in 
                              ['date_publication', 'budget', 'prix_m2', 'surface', 'quartier', 'adresse', 'type_bien', 'titre', 'url']]
            df_display_annonces = df_display_annonces[cols_to_display]
            
            # Remove any duplicate columns
            df_display_annonces = df_display_annonces.loc[:, ~df_display_annonces.columns.duplicated()]
            
            # Convertir en datetime pour le tri
            if 'date_publication' in df_display_annonces.columns:
                df_display_annonces['date_publication'] = pd.to_datetime(df_display_annonces['date_publication'])
            
            # Utiliser column_config pour afficher sans heures et URLs cliquables
            column_config = {}
            if 'date_publication' in df_display_annonces.columns:
                column_config['date_publication'] = st.column_config.DateColumn(
                    "date_publication",
                    format="DD/MM/YYYY"
                )
            if 'url' in df_display_annonces.columns:
                column_config['url'] = st.column_config.LinkColumn("url")
            st.dataframe(df_display_annonces, use_container_width=True, hide_index=True,
                        column_config=column_config if column_config else None)

elif mode_key not in ("Acheteurs", "Comparaison"):
    st.info("Aucune donnée disponible. Vérifiez vos filtres ou lancez le crawler.")
