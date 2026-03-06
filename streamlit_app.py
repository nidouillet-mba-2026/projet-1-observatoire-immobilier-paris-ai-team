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
    # Sidebar Filters
    st.sidebar.header("🔍 Filtres globaux")
    quartiers = st.sidebar.multiselect("Sélectionner les Quartiers", options=sorted(df['quartier'].unique()), default=df['quartier'].unique())
    date_range = st.sidebar.date_input("Période d'analyse", [df['date_mutation'].min(), df['date_mutation'].max()])
    
    # Filtered Data
    mask = (df['quartier'].isin(quartiers)) & \
           (df['date_mutation'].dt.date >= date_range[0]) & \
           (df['date_mutation'].dt.date <= date_range[1])
    df_filtered = df.loc[mask]

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Vue d'ensemble", "🏠 Quartiers", "📍 Adresses & Rues", "📋 Données Brutes"])

    with tab1:
        st.header("État du Marché Immobilier")
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Ventes totales", f"{len(df_filtered):,}")
        k2.metric("Prix Médian", f"{df_filtered['budget'].median():,.0f} €")
        k3.metric("Prix m² Moyen", f"{df_filtered['prix_m2'].mean():,.0f} €/m²")
        k4.metric("Surface Moyenne", f"{df_filtered['surface'].mean():.1f} m²")

        st.markdown("---")
        st.subheader("📈 Évolution temporelle du prix au m²")
        df_trend = df_filtered.resample('ME', on='date_mutation')['prix_m2'].mean().reset_index()
        fig_trend = px.line(df_trend, x='date_mutation', y='prix_m2', 
                            labels={'prix_m2': 'Prix moyen au m² (€)', 'date_mutation': 'Date'},
                            template='plotly_white')
        st.plotly_chart(fig_trend, use_container_width=True)

        st.subheader("📏 Répartition des surfaces vendues")
        fig_surf = px.histogram(df_filtered, x='surface', nbins=50, range_x=[0, 200],
                                labels={'surface': 'Surface (m²)', 'count': 'Nombre de ventes'},
                                template='plotly_white', color_discrete_sequence=['#31333F'])
        st.plotly_chart(fig_surf, use_container_width=True)

    with tab2:
        st.header("Analyse par Secteur / Section Cadastrale")
        
        # Aggregating small sections into "Autres" for clarity
        top_n = 15
        df_vol = df_filtered.groupby('quartier').size().sort_values(ascending=False).reset_index(name='nb_ventes')
        top_sections = df_vol.head(top_n)['quartier'].tolist()
        
        df_pie_clean = df_vol.copy()
        df_pie_clean.loc[~df_pie_clean['quartier'].isin(top_sections), 'quartier'] = 'Autres sections'
        df_pie_clean = df_pie_clean.groupby('quartier')['nb_ventes'].sum().reset_index()

        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader(f"💰 Top {top_n} Prix au m² (Médian)")
            df_q = df_filtered.groupby('quartier')['prix_m2'].median().sort_values(ascending=False).head(top_n).reset_index()
            fig_q = px.bar(df_q, x='prix_m2', y='quartier', orientation='h', 
                           color='prix_m2', color_continuous_scale='Blues',
                           labels={'prix_m2': 'Prix m² Médian (€)', 'quartier': 'Section'})
            fig_q.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_q, use_container_width=True)

        with c2:
            st.subheader(f"🥧 Part de marché (Top {top_n} + Autres)")
            fig_pie = px.pie(df_pie_clean, values='nb_ventes', names='quartier', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textinfo='percent')
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        st.header("Analyse détaillée des Adresses")
        
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
            st.subheader("🔥 Top 10 des adresses les plus actives")
            df_top_addr = df_filtered.groupby(['adresse_nom_voie', 'quartier']).size().reset_index(name='nb_ventes')
            df_top_addr = df_top_addr.sort_values('nb_ventes', ascending=False).head(10)
            fig_top_addr = px.bar(df_top_addr, x='nb_ventes', y='adresse_nom_voie', orientation='h',
                                  labels={'nb_ventes': 'Nombre de ventes', 'adresse_nom_voie': 'Rue / Adresse'})
            st.plotly_chart(fig_top_addr, use_container_width=True)

    with tab4:
        st.header("Liste des dernières transactions")
        st.write("Retrouvez ici le détail des 200 dernières ventes filtrées.")
        st.dataframe(df_filtered.sort_values('date_mutation', ascending=False).head(200), use_container_width=True)

else:
    st.info("⚠️ Aucune donnée disponible. Vérifiez vos filtres ou lancez le crawler.")
