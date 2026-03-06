import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Observatoire Immobilier Toulon", layout="wide")

st.title("🏙️ Observatoire Immobilier - Toulon (DVF)")

@st.cache_data
def load_data():
    file_path = "data/dvf_toulon_2020_now.csv"
    if not os.path.exists(file_path):
        st.error(f"Fichier {file_path} introuvable. Veuillez lancer le crawler d'abord.")
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    df['date_mutation'] = pd.to_datetime(df['date_mutation'])
    df['prix_m2'] = df['budget'] / df['surface']
    # Nettoyage des valeurs infinies ou aberrantes pour le prix au m2
    df.loc[df['surface'] <= 0, 'prix_m2'] = None
    return df

df = load_data()

if not df.empty:
    # ---------------- Sidebar Filters ----------------
    st.sidebar.header("Filtres")

    quartiers = st.sidebar.multiselect(
        "Quartiers", 
        options=sorted(df['quartier'].unique()), 
        default=df['quartier'].unique()
    )

    # Gestion des dates (plage ou date unique)
    default_dates = [df['date_mutation'].min().date(), df['date_mutation'].max().date()]
    date_range = st.sidebar.date_input("Période", value=default_dates)

    # S'assurer que date_range est toujours une liste de deux dates
    if isinstance(date_range, tuple) or isinstance(date_range, list):
        if len(date_range) == 1:
            date_range = [date_range[0], date_range[0]]
    else:
        date_range = [date_range, date_range]

    # ---------------- Filtrage des données ----------------
    mask = (df['quartier'].isin(quartiers)) & \
           (df['date_mutation'].dt.date >= date_range[0]) & \
           (df['date_mutation'].dt.date <= date_range[1])
    df_filtered = df.loc[mask]
    # ---------------- KPIs ----------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions", f"{len(df_filtered):,}")
    col2.metric("Prix Médian", f"{df_filtered['budget'].median():,.0f} €")
    col3.metric("Prix m² Moyen", f"{df_filtered['prix_m2'].mean():,.0f} €/m²")
    col4.metric("Surface Moyenne", f"{df_filtered['surface'].mean():.1f} m²")

    # ---------------- Graphiques ----------------
    st.subheader("Évolution du prix m² moyen")
    df_trend = df_filtered.resample('ME', on='date_mutation')['prix_m2'].mean().reset_index()
    fig_trend = px.line(
        df_trend, 
        x='date_mutation', 
        y='prix_m2', 
        labels={'prix_m2': 'Prix m² (€)', 'date_mutation': 'Date'}
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Prix m² par quartier")
        df_q = df_filtered.groupby('quartier')['prix_m2'].median().sort_values().reset_index()
        fig_q = px.bar(df_q, x='prix_m2', y='quartier', orientation='h', color='prix_m2')
        st.plotly_chart(fig_q, use_container_width=True)
        
    with col_b:
        st.subheader("Répartition des surfaces")
        fig_surf = px.histogram(df_filtered, x='surface', nbins=50, range_x=[0, 200])
        st.plotly_chart(fig_surf, use_container_width=True)

    # ---------------- Dernières transactions ----------------
    st.subheader("Dernières transactions")
    st.dataframe(
        df_filtered.sort_values('date_mutation', ascending=False).head(100), 
        use_container_width=True
    )

else:
    st.info("En attente de données...")