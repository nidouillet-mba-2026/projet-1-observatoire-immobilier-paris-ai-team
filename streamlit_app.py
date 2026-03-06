import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Observatoire Immobilier Toulon", layout="wide")

st.title("🏙️ Observatoire Immobilier - Toulon (DVF)")

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
        # Standardize columns for the app
        df = df.rename(columns={
            'Prix_total_net': 'budget',
            'Surface_m2': 'surface',
            'Quartier': 'quartier',
            'Prix_m2_calculé': 'prix_m2'
        })
        # Annonces don't have a mutation date, we can use a dummy or skip time charts
        df['date_mutation'] = pd.Timestamp.now()
    return df

# Sidebar Filters
st.sidebar.header("🔍 Configuration")
data_mode = st.sidebar.radio("Source des données", ["Ventes Passées (DVF)", "Annonces Actuelles (Bien'Ici)"])
mode_key = "DVF" if "DVF" in data_mode else "Annonces"

df = load_data(mode_key)

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("📍 Filtres")
    
    # Handle NaNs and mix of types in 'quartier' for sorting
    unique_quartiers = sorted([str(q) for q in df['quartier'].unique() if pd.notna(q)])
    quartiers = st.sidebar.multiselect("Sélectionner les Secteurs/Quartiers", options=unique_quartiers, default=unique_quartiers)
    
    if mode_key == "DVF":
        date_range = st.sidebar.date_input("Période d'analyse", [df['date_mutation'].min(), df['date_mutation'].max()])
        mask = (df['quartier'].isin(quartiers)) & \
               (df['date_mutation'].dt.date >= date_range[0]) & \
               (df['date_mutation'].dt.date <= date_range[1])
    else:
        mask = (df['quartier'].isin(quartiers))
        
    df_filtered = df.loc[mask]

    # --- TABS ---
    tab_titles = ["📊 Vue d'ensemble", "🏠 Quartiers", "📍 Adresses & Rues", "📋 Données Brutes"]
    if mode_key == "Annonces":
        tab_titles = ["📊 Vue d'ensemble", "🏠 Quartiers", "📋 Liste des Annonces"]
    
    tabs = st.tabs(tab_titles)
    
    # Check if we have 4 or 3 tabs based on mode
    t1 = tabs[0]
    t2 = tabs[1]
    t3 = tabs[2]
    t4 = tabs[3] if len(tabs) > 3 else None

    with t1:
        st.header(f"État du Marché - {data_mode}")
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Nombre d'entrées", f"{len(df_filtered):,}")
        k2.metric("Prix Médian", f"{df_filtered['budget'].median():,.0f} €")
        k3.metric("Prix m² Moyen", f"{df_filtered['prix_m2'].mean():,.0f} €/m²")
        k4.metric("Surface Moyenne", f"{df_filtered['surface'].mean():.1f} m²")

        if mode_key == "DVF":
            st.markdown("---")
            st.subheader("📈 Évolution temporelle du prix au m²")
            df_trend = df_filtered.resample('ME', on='date_mutation')['prix_m2'].mean().reset_index()
            fig_trend = px.line(df_trend, x='date_mutation', y='prix_m2', 
                                labels={'prix_m2': 'Prix moyen au m² (€)', 'date_mutation': 'Date'},
                                template='plotly_white')
            st.plotly_chart(fig_trend, use_container_width=True)

        st.subheader("📏 Répartition des surfaces")
        fig_surf = px.histogram(df_filtered, x='surface', nbins=50, range_x=[0, 200],
                                labels={'surface': 'Surface (m²)', 'count': 'Nombre'},
                                template='plotly_white', color_discrete_sequence=['#31333F'])
        st.plotly_chart(fig_surf, use_container_width=True)

    with t2:
        st.header("Analyse par Secteur")
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("💰 Prix au m²")
            df_q = df_filtered.groupby('quartier')['prix_m2'].median().sort_values(ascending=False).head(20).reset_index()
            fig_q = px.bar(df_q, x='prix_m2', y='quartier', orientation='h', 
                           color='prix_m2', color_continuous_scale='Blues',
                           labels={'prix_m2': 'Prix m² Médian (€)', 'quartier': 'Secteur'})
            fig_q.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_q, use_container_width=True)

        with c2:
            st.subheader("🥧 Répartition du volume")
            # For pie, grouping others if too many
            df_vol = df_filtered.groupby('quartier').size().sort_values(ascending=False).reset_index(name='nb')
            if len(df_vol) > 15:
                top_15 = df_vol.head(15)['quartier'].tolist()
                df_vol.loc[~df_vol['quartier'].isin(top_15), 'quartier'] = 'Autres'
                df_vol = df_vol.groupby('quartier')['nb'].sum().reset_index()
                
            fig_pie = px.pie(df_vol, values='nb', names='quartier', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textinfo='percent')
            st.plotly_chart(fig_pie, use_container_width=True)

    if mode_key == "DVF" and t4:
        with t3:
            st.header("Analyse détaillée des Adresses (DVF)")
            
            st.subheader("🌍 Vue d'ensemble des volumes par rue")
            df_tree = df_filtered.groupby(['quartier', 'adresse_nom_voie']).size().reset_index(name='nb_ventes')
            fig_tree = px.treemap(df_tree, path=['quartier', 'adresse_nom_voie'], values='nb_ventes',
                                  color='nb_ventes', color_continuous_scale='RdBu',
                                  labels={'nb_ventes': 'Volume de ventes'})
            st.plotly_chart(fig_tree, use_container_width=True)

            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                st.subheader("🏘️ Dynamique par adresse")
                df_addr = df_filtered.groupby(['quartier', 'adresse_nom_voie']).size().reset_index(name='nb_ventes')
                df_avg_addr = df_addr.groupby('quartier')['nb_ventes'].mean().sort_values(ascending=False).reset_index()
                fig_avg_addr = px.bar(df_avg_addr, x='nb_ventes', y='quartier', orientation='h', 
                                     labels={'nb_ventes': 'Nb Moyen de Ventes / Adresse'},
                                     color='nb_ventes', color_continuous_scale='Viridis')
                st.plotly_chart(fig_avg_addr, use_container_width=True)
                
            with col_v2:
                st.subheader("🔥 Top 10 des adresses actives")
                df_top_addr = df_filtered.groupby(['adresse_nom_voie', 'quartier']).size().reset_index(name='nb_ventes')
                df_top_addr = df_top_addr.sort_values('nb_ventes', ascending=False).head(10)
                fig_top_addr = px.bar(df_top_addr, x='nb_ventes', y='adresse_nom_voie', orientation='h',
                                      labels={'nb_ventes': 'Nombre de ventes', 'adresse_nom_voie': 'Rue / Adresse'})
                st.plotly_chart(fig_top_addr, use_container_width=True)

        with t4:
            st.header("Liste des dernières transactions (DVF)")
            st.dataframe(df_filtered.sort_values('date_mutation', ascending=False).head(200), use_container_width=True)
    
    elif mode_key == "Annonces":
        with t3:
            st.header("Liste des Annonces en cours")
            st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("⚠️ Aucune donnée disponible. Vérifiez vos filtres ou lancez le crawler.")
