import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Observatoire Immobilier Toulon",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME & CSS
# ─────────────────────────────────────────────
NAVY   = "#1B3A5C"
GOLD   = "#C9A84C"
BLUE   = "#2E86AB"
LIGHT  = "#F4F6F9"
WHITE  = "#FFFFFF"
GREY   = "#6B7280"
GREEN  = "#10B981"
RED    = "#EF4444"

CHART_COLORS = [BLUE, GOLD, "#E74C3C", "#2ECC71", "#9B59B6", "#F39C12", "#1ABC9C"]

def apply_css():
    st.markdown(f"""
    <style>
    /* ── Fonts & base ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* ── App background ── */
    .stApp {{ background-color: {LIGHT}; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {NAVY} 0%, #0f2337 100%);
        border-right: none;
    }}
    [data-testid="stSidebar"] * {{ color: #E2E8F0 !important; }}
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {{
        color: {GOLD} !important;
        font-weight: 600;
    }}
    [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.15) !important; }}
    [data-testid="stSidebar"] label {{ color: #CBD5E1 !important; font-size: 0.82rem; }}
    [data-testid="stSidebar"] .stRadio > label {{ color: {GOLD} !important; font-weight: 600; font-size: 0.9rem; }}

    /* ── Hide default streamlit header ── */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}

    /* ── Metric cards ── */
    .kpi-card {{
        background: {WHITE};
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04);
        border-left: 4px solid {BLUE};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }}
    .kpi-card.gold {{ border-left-color: {GOLD}; }}
    .kpi-card.green {{ border-left-color: {GREEN}; }}
    .kpi-card.navy {{ border-left-color: {NAVY}; }}
    .kpi-label {{
        font-size: 0.78rem;
        font-weight: 500;
        color: {GREY};
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {NAVY};
        line-height: 1;
    }}
    .kpi-sub {{
        font-size: 0.75rem;
        color: {GREY};
        margin-top: 4px;
    }}

    /* ── Section headers ── */
    .section-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {NAVY};
        margin: 0 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid {GOLD};
        display: inline-block;
    }}

    /* ── Chart cards ── */
    .chart-card {{
        background: {WHITE};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }}

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: {WHITE};
        border-radius: 10px;
        padding: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        font-size: 0.9rem;
        color: {GREY};
        background: transparent;
    }}
    .stTabs [aria-selected="true"] {{
        background: {NAVY} !important;
        color: {WHITE} !important;
    }}

    /* ── Hero banner ── */
    .hero {{
        background: linear-gradient(135deg, {NAVY} 0%, #2563EB 100%);
        border-radius: 16px;
        padding: 32px 40px;
        margin-bottom: 28px;
        color: white;
        position: relative;
        overflow: hidden;
    }}
    .hero::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: rgba(255,255,255,0.04);
        border-radius: 50%;
    }}
    .hero-title {{
        font-size: 1.9rem;
        font-weight: 700;
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }}
    .hero-subtitle {{
        font-size: 1rem;
        opacity: 0.75;
        margin: 0;
        font-weight: 400;
    }}
    .hero-badge {{
        display: inline-block;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-bottom: 12px;
        backdrop-filter: blur(4px);
    }}

    /* ── Dataframe ── */
    .stDataFrame {{ border-radius: 10px; overflow: hidden; }}

    /* ── Download button ── */
    .stDownloadButton > button {{
        background: {NAVY};
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 20px;
        font-weight: 500;
        font-size: 0.875rem;
    }}
    .stDownloadButton > button:hover {{ background: {BLUE}; }}

    /* ── Divider ── */
    .divider {{
        height: 1px;
        background: linear-gradient(90deg, {GOLD}, transparent);
        margin: 24px 0;
        border: none;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_css()

# ─────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#374151"),
    margin=dict(l=0, r=0, t=32, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0"),
    yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0"),
    coloraxis_colorbar=dict(tickfont=dict(size=10)),
)

def styled_chart(fig, height=360):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig

def kpi(label, value, color="", sub=""):
    return f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
    </div>"""

def section_title(text):
    st.markdown(f'<p class="section-title">{text}</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────
@st.cache_data
def load_acheteurs():
    dfs = []
    files = {
        "acheteur/data/acheteurs_annonces.csv": "Annonces (PAP/Logic-Immo)",
        "acheteur/data/acheteurs_leboncoin.csv": "LeBonCoin",
        "acheteur/data/marche_leboncoin.csv": "Marché LeBonCoin",
        "acheteur/data/facebook_manuel.csv": "Facebook (manuel)",
    }
    for path, label in files.items():
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')
                df['_source_file'] = label
                dfs.append(df)
            except Exception:
                pass
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    for col in ['budget_max', 'surface_min', 'nb_pieces', 'prix', 'surface', 'prix_m2']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.extract(r'(\d[\d\s]*)')[0]
            df[col] = df[col].str.replace(r'\s', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data
def load_data(data_type="DVF"):
    if data_type == "DVF":
        file_path = "data/dvf_toulon_2020_now.csv"
        if not os.path.exists(file_path):
            st.error(f"Fichier {file_path} introuvable.")
            return pd.DataFrame()
        df = pd.read_csv(file_path)
        df['date_mutation'] = pd.to_datetime(df['date_mutation'])
        df['prix_m2'] = df['budget'] / df['surface']
        df.loc[df['surface'] <= 0, 'prix_m2'] = None
    else:
        file_path = "data/annonces_toulon_clean.csv"
        if not os.path.exists(file_path):
            st.error(f"Fichier {file_path} introuvable.")
            return pd.DataFrame()
        df = pd.read_csv(file_path)
        df = df.rename(columns={
            'Prix_total_net': 'budget',
            'Surface_m2': 'surface',
            'Quartier': 'quartier',
            'Prix_m2_calculé': 'prix_m2'
        })
        df['date_mutation'] = pd.Timestamp.now()
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
        ["Ventes Passées (DVF)", "Annonces Actuelles (Bien'Ici)", "Profils Acheteurs"],
        label_visibility="collapsed"
    )
    mode_key = "DVF" if "DVF" in data_mode else ("Acheteurs" if "Acheteurs" in data_mode else "Annonces")

# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────
MODE_META = {
    "DVF":      ("Ventes Passées",        "Transactions notariales depuis 2020 · Source DVF Étalab",      "📊"),
    "Annonces": ("Annonces Actuelles",    "Offres en cours sur le marché toulonnais · Source Bien'Ici",   "🏠"),
    "Acheteurs":("Profils Acheteurs",     "Demandes & critères des acheteurs à Toulon · Multi-sources",   "👥"),
}
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
    df_ach = load_acheteurs()

    if df_ach.empty:
        st.warning("Aucune donnée acheteur. Lancez : `python acheteur/run_all.py`")
    else:
        with st.sidebar:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748B; font-weight:600; margin-bottom:8px;">Filtres</p>', unsafe_allow_html=True)
            sources_dispo = sorted(df_ach['source'].dropna().unique().tolist()) if 'source' in df_ach.columns else []
            sources_sel = st.multiselect("Source", sources_dispo, default=sources_dispo)
            types_bien = sorted(df_ach['type_bien'].dropna().unique().tolist()) if 'type_bien' in df_ach.columns else []
            types_sel = st.multiselect("Type de bien", types_bien, default=types_bien)

        mask_ach = pd.Series([True] * len(df_ach), index=df_ach.index)
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
                                 values='count', names='type_bien', hole=0.45,
                                 color_discrete_sequence=CHART_COLORS)
                    fig.update_traces(textposition='outside', textinfo='percent+label',
                                      marker=dict(line=dict(color='white', width=2)))
                    st.plotly_chart(styled_chart(fig), use_container_width=True)

            with col2:
                if 'type_achat' in dfa.columns:
                    section_title("Motif d'achat")
                    fig = px.pie(dfa['type_achat'].value_counts().reset_index(),
                                 values='count', names='type_achat', hole=0.45,
                                 color_discrete_sequence=[NAVY, GOLD, BLUE, GREEN])
                    fig.update_traces(textposition='outside', textinfo='percent+label',
                                      marker=dict(line=dict(color='white', width=2)))
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
            st.dataframe(dfa[cols_display], use_container_width=True, hide_index=True)
            st.download_button(
                "Télécharger CSV",
                dfa.to_csv(index=False, encoding='utf-8-sig'),
                "acheteurs_toulon.csv", "text/csv"
            )

# ─────────────────────────────────────────────
# MODE : DVF / ANNONCES
# ─────────────────────────────────────────────
else:
    df = load_data(mode_key)

if mode_key != "Acheteurs" and not df.empty:

    with st.sidebar:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748B; font-weight:600; margin-bottom:8px;">Filtres</p>', unsafe_allow_html=True)

        unique_quartiers = sorted([str(q) for q in df['quartier'].unique() if pd.notna(q)])
        quartiers = st.multiselect("Secteurs / Quartiers", options=unique_quartiers, default=unique_quartiers)

        if mode_key == "DVF":
            default_dates = [df['date_mutation'].min().date(), df['date_mutation'].max().date()]
            date_range = st.date_input("Période d'analyse", value=default_dates)
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_date, end_date = date_range
            elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
                start_date = end_date = date_range[0]
            else:
                start_date = end_date = date_range
            mask = (df['quartier'].isin(quartiers)) & \
                   (df['date_mutation'].dt.date >= start_date) & \
                   (df['date_mutation'].dt.date <= end_date)
        else:
            mask = df['quartier'].isin(quartiers)

    df_filtered = df.loc[mask]

    # TABS
    if mode_key == "DVF":
        tab_titles = ["Vue d'ensemble", "Analyse par quartier", "Adresses & Rues", "Données brutes"]
    else:
        tab_titles = ["Vue d'ensemble", "Analyse par quartier", "Liste des annonces"]

    tabs = st.tabs(tab_titles)
    t1, t2, t3 = tabs[0], tabs[1], tabs[2]
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

        df_pie = df_vol.copy()
        if len(df_vol) > top_n:
            df_pie.loc[~df_pie['quartier'].isin(top_sections), 'quartier'] = 'Autres'
            df_pie = df_pie.groupby('quartier')['nb'].sum().reset_index()

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
            section_title("Part de marché")
            fig = px.pie(df_pie, values='nb', names='quartier', hole=0.45,
                         color_discrete_sequence=CHART_COLORS)
            fig.update_traces(textposition='outside', textinfo='percent+label',
                              marker=dict(line=dict(color='white', width=2)))
            st.plotly_chart(styled_chart(fig, height=460), use_container_width=True)

    # ── Tab 3 : Adresses (DVF) ou Annonces ──
    if mode_key == "DVF" and t4:
        with t3:
            section_title("Volume de ventes par rue et quartier")
            df_tree = df_filtered.groupby(['quartier', 'adresse_nom_voie']).size().reset_index(name='nb_ventes')
            fig = px.treemap(df_tree, path=['quartier', 'adresse_nom_voie'], values='nb_ventes',
                             color='nb_ventes', color_continuous_scale=[[0, '#DBEAFE'], [1, NAVY]])
            st.plotly_chart(styled_chart(fig, height=440), use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                section_title("Dynamique moyenne par quartier")
                df_addr = df_filtered.groupby(['quartier', 'adresse_nom_voie']).size().reset_index(name='nb')
                df_avg  = df_addr.groupby('quartier')['nb'].mean().sort_values().tail(12).reset_index()
                fig = px.bar(df_avg, x='nb', y='quartier', orientation='h',
                             color='nb', color_continuous_scale=[[0, BLUE], [1, NAVY]],
                             labels={'nb': 'Ventes moy./adresse', 'quartier': ''})
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(styled_chart(fig), use_container_width=True)

            with col2:
                section_title("Top 10 adresses actives")
                df_top = df_filtered.groupby(['adresse_nom_voie', 'quartier']).size().reset_index(name='nb')
                df_top = df_top.sort_values('nb').tail(10)
                fig = px.bar(df_top, x='nb', y='adresse_nom_voie', orientation='h',
                             color='nb', color_continuous_scale=[[0, '#FDE68A'], [1, GOLD]],
                             labels={'nb': 'Nb ventes', 'adresse_nom_voie': ''})
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with t4:
            section_title("Dernières transactions DVF")
            st.dataframe(
                df_filtered.sort_values('date_mutation', ascending=False).head(200),
                use_container_width=True, hide_index=True
            )

    elif mode_key == "Annonces":
        with t3:
            section_title("Annonces en cours — Bien'Ici")
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)

elif mode_key != "Acheteurs":
    st.info("Aucune donnée disponible. Vérifiez vos filtres ou lancez le crawler.")
