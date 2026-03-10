"""
Utilitaires pour Streamlit App - Fonctions, thèmes et loaders de données.
"""

import streamlit as st
import pandas as pd
import os
import re as _re

# ─────────────────────────────────────────────
# THEME & CSS COLORS
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

# ─────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(family="Inter", color="#111827", size=12),
    margin=dict(l=8, r=8, t=36, b=8),
    legend=dict(bgcolor=WHITE, font=dict(size=12, color="#111827")),
    xaxis=dict(
        gridcolor="#E5E7EB",
        linecolor="#D1D5DB",
        tickfont=dict(color="#111827", size=11),
        title=dict(font=dict(color="#111827", size=12)),
    ),
    yaxis=dict(
        gridcolor="#E5E7EB",
        linecolor="#D1D5DB",
        tickfont=dict(color="#111827", size=11),
        title=dict(font=dict(color="#111827", size=12)),
    ),
    coloraxis_colorbar=dict(
        tickfont=dict(size=11, color="#111827"),
        title=dict(font=dict(size=12, color="#111827")),
    ),
)

# ─────────────────────────────────────────────
# MODE METADATA
# ─────────────────────────────────────────────
MODE_META = {
    "DVF":      ("Ventes Passées",          "Transactions notariales depuis 2020 · Source DVF Étalab",          "📊"),
    "Annonces": ("Annonces Vendeurs",       "Offres en cours sur le marché toulonnais · Source Bien'Ici",       "🏠"),
    "LBC":      ("Annonces Vendeurs",       "Offres en cours sur le marché toulonnais · Source LeBonCoin",      "🔖"),
    "Acheteurs":("Profils Acheteurs",       "Demandes & critères des acheteurs à Toulon · PAP / Facebook",      "👥"),
    "Comparaison":("Comparaison Marché",     "Analyse des écarts de prix : Annonces vs Marché DVF",              "⚖️"),
}

# ─────────────────────────────────────────────
# FORMATTING FUNCTIONS
# ─────────────────────────────────────────────
def format_price(price):
    """Format price to short notation (ex: 205k, 1.2M)"""
    try:
        if pd.isnull(price) or price is None or (isinstance(price, str) and price == ""):
            return ""
        price = float(price)
        if price >= 1_000_000:
            return f"{price / 1_000_000:.1f}M"
        elif price >= 1_000:
            return f"{price / 1_000:.0f}k"
        else:
            return f"{price:.0f}"
    except (ValueError, TypeError):
        return str(price)

# ─────────────────────────────────────────────
# STYLING FUNCTIONS
# ─────────────────────────────────────────────
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

    /* ── Header : transparent, pas de barre visible ── */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
    }}
    #MainMenu {{ visibility: hidden !important; }}
    footer {{ visibility: hidden !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stToolbarActions"] {{ display: none !important; }}
    /* Boutons du header (toggle sidebar) toujours visibles */
    header button {{
        visibility: visible !important;
        display: inline-flex !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }}

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

    /* ── Main content text ── */

    /* ── Section headers ── */
    .section-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: {NAVY};
        margin: 8px 0 14px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid {GOLD};
        display: inline-block;
        letter-spacing: -0.01em;
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

    /* ── Calendar & Date Input ── */
    [data-testid="stDateInput"] input,
    [data-testid="stDateInput"] input[type="text"],
    input[type="date"],
    .stDateInput input {{
        color: #000000 !important;
    }}

    /* Calendar dropdown/picker */
    [data-baseweb="popover"] {{
        color: #000000 !important;
    }}
    
    [data-baseweb="popover"] * {{
        color: #000000 !important;
    }}

    /* Ensure date input text is black */
    [data-testid="stDateInput"] input::placeholder {{
        color: #666666 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def styled_chart(fig, height=360):
    """Style a Plotly chart with the app's theme."""
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    # Force dark text on all annotations and hover
    fig.update_traces(
        hoverlabel=dict(bgcolor=WHITE, font_color="#111827", font_size=12),
    )
    # Fix pie/donut label color
    if fig.data and fig.data[0].type in ('pie', 'sunburst', 'treemap'):
        fig.update_traces(textfont=dict(color="#111827", size=12))
    return fig

def kpi(label, value, color="", sub=""):
    """Generate a KPI card HTML."""
    return f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
    </div>"""

def section_title(text):
    """Display a section title."""
    st.markdown(f'<p class="section-title">{text}</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────
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

@st.cache_data
def load_acheteurs():
    """Charge les profils acheteurs depuis les fichiers disponibles."""
    dfs = []
    # Uniquement les vraies sources de profils acheteurs
    files = {
        "acheteur/data/acheteurs_annonces.csv":  "PAP / Logic-Immo",
        "acheteur/data/facebook_manuel.csv":     "Facebook (manuel)",
    }
    seen_paths = set()
    for path, label in files.items():
        if path in seen_paths or not os.path.exists(path):
            continue
        seen_paths.add(path)
        try:
            df = pd.read_csv(path, encoding='utf-8-sig')
            df = _extract_from_title(df)   # enrichit surface/pièces depuis les titres
            df['_source_file'] = label
            dfs.append(df)
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    # Normalise : surface_m2 / surface → surface_min (colonne unique pour l'onglet acheteurs)
    for alt in ['surface_m2', 'surface']:
        if alt in df.columns and 'surface_min' not in df.columns:
            df['surface_min'] = df[alt]
        elif alt in df.columns:
            df['surface_min'] = df['surface_min'].fillna(df[alt])
    # Prix marché → budget_max si manquant
    for alt in ['prix']:
        if alt in df.columns and 'budget_max' not in df.columns:
            df['budget_max'] = df[alt]
        elif alt in df.columns:
            df['budget_max'] = df['budget_max'].fillna(df[alt]) if 'budget_max' in df.columns else df[alt]
    for col in ['budget_max', 'surface_min', 'nb_pieces', 'prix', 'surface', 'prix_m2']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.extract(r'(\d[\d\s]*)')[0]
            df[col] = df[col].str.replace(r'\s', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data
def load_data(data_type="DVF"):
    """Charge les données selon le type (DVF, LBC, Annonces)."""
    if data_type == "DVF":
        file_path = "data/dvf_clean.csv" if os.path.exists("data/dvf_clean.csv") else "data/dvf_toulon_2020_now.csv"
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
