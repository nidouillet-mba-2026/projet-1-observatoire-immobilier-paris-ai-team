import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Observatoire Immobilier Toulon", layout="wide")

st.title("🏙️ Observatoire Immobilier - Toulon (DVF)")

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
    # Nettoie les colonnes numériques (peuvent contenir "95 m²", "250 000 €", etc.)
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
        # Standardize columns for the app
        df = df.rename(columns={
            'Prix_total_net': 'budget',
            'Surface_m2': 'surface',
            'Quartier': 'quartier',
            'Prix_m2_calculé': 'prix_m2'
        })
        # Annonces don't have a mutation date, we use today's date to avoid errors in filtering logic
        df['date_mutation'] = pd.Timestamp.now()
    return df

# Sidebar Filters
st.sidebar.header("🔍 Configuration")
data_mode = st.sidebar.radio("Source des données", ["Ventes Passées (DVF)", "Annonces Actuelles (Bien'Ici)", "Profils Acheteurs"])
mode_key = "DVF" if "DVF" in data_mode else ("Acheteurs" if "Acheteurs" in data_mode else "Annonces")

if mode_key == "Acheteurs":
    df_ach = load_acheteurs()

    if df_ach.empty:
        st.warning("Aucune donnée acheteur trouvée. Lancez d'abord : `python acheteur/run_all.py`")
    else:
        st.sidebar.markdown("---")
        st.sidebar.header("Filtres Acheteurs")

        sources_dispo = sorted(df_ach['source'].dropna().unique().tolist()) if 'source' in df_ach.columns else []
        sources_sel = st.sidebar.multiselect("Source", sources_dispo, default=sources_dispo)

        types_bien = sorted(df_ach['type_bien'].dropna().unique().tolist()) if 'type_bien' in df_ach.columns else []
        types_sel = st.sidebar.multiselect("Type de bien", types_bien, default=types_bien)

        mask_ach = pd.Series([True] * len(df_ach), index=df_ach.index)
        if 'source' in df_ach.columns and sources_sel:
            mask_ach &= df_ach['source'].isin(sources_sel)
        if 'type_bien' in df_ach.columns and types_sel:
            mask_ach &= df_ach['type_bien'].isin(types_sel)

        dfa = df_ach[mask_ach].copy()

        tab_a1, tab_a2, tab_a3, tab_a4 = st.tabs(["📊 Vue d'ensemble", "💰 Budgets & Surfaces", "📍 Quartiers & Critères", "📋 Données brutes"])

        with tab_a1:
            st.header("Profils Acheteurs - Toulon")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Profils collectés", f"{len(dfa):,}")

            budget_med = dfa['budget_max'].median() if 'budget_max' in dfa.columns and dfa['budget_max'].notna().any() else None
            k2.metric("Budget médian", f"{budget_med:,.0f} €" if budget_med else "N/A")

            surf_med = dfa['surface_min'].median() if 'surface_min' in dfa.columns and dfa['surface_min'].notna().any() else None
            k3.metric("Surface souhaitée (méd.)", f"{surf_med:.0f} m²" if surf_med else "N/A")

            pieces_med = dfa['nb_pieces'].median() if 'nb_pieces' in dfa.columns and dfa['nb_pieces'].notna().any() else None
            k4.metric("Nb pièces (méd.)", f"{pieces_med:.0f}" if pieces_med else "N/A")

            c1, c2 = st.columns(2)

            with c1:
                if 'type_bien' in dfa.columns:
                    st.subheader("Type de bien recherché")
                    fig = px.pie(dfa['type_bien'].value_counts().reset_index(),
                                 values='count', names='type_bien', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig, use_container_width=True)

            with c2:
                if 'type_achat' in dfa.columns:
                    st.subheader("Motif d'achat")
                    fig = px.pie(dfa['type_achat'].value_counts().reset_index(),
                                 values='count', names='type_achat', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                    st.plotly_chart(fig, use_container_width=True)

            if 'source' in dfa.columns:
                st.subheader("Répartition par source")
                fig = px.bar(dfa['source'].value_counts().reset_index(),
                             x='source', y='count',
                             labels={'source': 'Source', 'count': 'Nombre de profils'},
                             color='count', color_continuous_scale='Blues',
                             template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)

        with tab_a2:
            st.header("Budgets & Surfaces")

            if 'budget_max' in dfa.columns and dfa['budget_max'].notna().any():
                df_b = dfa[dfa['budget_max'].between(50_000, 2_000_000)]
                st.subheader("Distribution des budgets")
                fig = px.histogram(df_b, x='budget_max', nbins=40,
                                   labels={'budget_max': 'Budget max (€)', 'count': 'Nb acheteurs'},
                                   template='plotly_white', color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig, use_container_width=True)

                if 'type_bien' in dfa.columns:
                    st.subheader("Budget médian par type de bien")
                    df_btype = dfa.groupby('type_bien')['budget_max'].median().reset_index()
                    fig = px.bar(df_btype, x='type_bien', y='budget_max',
                                 labels={'type_bien': 'Type de bien', 'budget_max': 'Budget médian (€)'},
                                 color='budget_max', color_continuous_scale='Teal',
                                 template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)

            if 'surface_min' in dfa.columns and dfa['surface_min'].notna().any():
                df_s = dfa[dfa['surface_min'].between(10, 500)]
                st.subheader("Surface souhaitée")
                fig = px.histogram(df_s, x='surface_min', nbins=30,
                                   labels={'surface_min': 'Surface min souhaitée (m²)', 'count': 'Nb acheteurs'},
                                   template='plotly_white', color_discrete_sequence=['#EF553B'])
                st.plotly_chart(fig, use_container_width=True)

        with tab_a3:
            st.header("Quartiers & Critères")

            if 'quartier_souhaite' in dfa.columns or 'quartier' in dfa.columns:
                col_q = 'quartier_souhaite' if 'quartier_souhaite' in dfa.columns else 'quartier'
                st.subheader("Quartiers les plus demandés")
                quartier_counts = {}
                for val in dfa[col_q].dropna():
                    for q in str(val).split(','):
                        q = q.strip()
                        if q and q not in ('Non precise', 'Non précisé', ''):
                            quartier_counts[q] = quartier_counts.get(q, 0) + 1
                if quartier_counts:
                    df_q = pd.DataFrame(list(quartier_counts.items()), columns=['quartier', 'nb']).sort_values('nb', ascending=False).head(15)
                    fig = px.bar(df_q, x='nb', y='quartier', orientation='h',
                                 color='nb', color_continuous_scale='Oranges',
                                 labels={'nb': 'Nombre de demandes', 'quartier': 'Quartier'},
                                 template='plotly_white')
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Pas encore de données de quartier.")

            if 'criteres' in dfa.columns:
                st.subheader("Critères les plus recherchés")
                critere_counts = {}
                for val in dfa['criteres'].dropna():
                    for c in str(val).split(','):
                        c = c.strip()
                        if c:
                            critere_counts[c] = critere_counts.get(c, 0) + 1
                if critere_counts:
                    df_c = pd.DataFrame(list(critere_counts.items()), columns=['critere', 'nb']).sort_values('nb', ascending=False)
                    fig = px.bar(df_c, x='nb', y='critere', orientation='h',
                                 color='nb', color_continuous_scale='Purples',
                                 labels={'nb': 'Nombre de mentions', 'critere': 'Critère'},
                                 template='plotly_white')
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)

        with tab_a4:
            st.header("Données brutes acheteurs")
            cols_display = [c for c in ['source', 'date_annonce', 'type_bien', 'type_achat',
                                         'budget_max', 'surface_min', 'nb_pieces',
                                         'quartier_souhaite', 'criteres', 'titre', 'url'] if c in dfa.columns]
            st.dataframe(dfa[cols_display], use_container_width=True)
            csv = dfa.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("Télécharger CSV", csv, "acheteurs_toulon.csv", "text/csv")

else:
    df = load_data(mode_key)

if mode_key != "Acheteurs" and not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("📍 Filtres")
    
    # Handle NaNs and mix of types in 'quartier' for sorting
    unique_quartiers = sorted([str(q) for q in df['quartier'].unique() if pd.notna(q)])
    quartiers = st.sidebar.multiselect("Sélectionner les Secteurs/Quartiers", options=unique_quartiers, default=unique_quartiers)
    
    if mode_key == "DVF":
        # Robust date range handling (from Alexis' branch)
        default_dates = [df['date_mutation'].min().date(), df['date_mutation'].max().date()]
        date_range = st.sidebar.date_input("Période d'analyse", value=default_dates)
        
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
        mask = (df['quartier'].isin(quartiers))
        
    df_filtered = df.loc[mask]

    # --- TABS ---
    tab_titles = ["📊 Vue d'ensemble", "🏠 Quartiers", "📍 Adresses & Rues", "📋 Données Brutes"]
    if mode_key == "Annonces":
        tab_titles = ["📊 Vue d'ensemble", "🏠 Quartiers", "📋 Liste des Annonces"]
    
    tabs = st.tabs(tab_titles)
    
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
        
        # Aggregating small sections into "Autres" for clarity
        top_n = 15
        df_vol = df_filtered.groupby('quartier').size().sort_values(ascending=False).reset_index(name='nb_ventes')
        top_sections = df_vol.head(top_n)['quartier'].tolist()
        
        df_pie_clean = df_vol.copy()
        if len(df_vol) > top_n:
            df_pie_clean.loc[~df_pie_clean['quartier'].isin(top_sections), 'quartier'] = 'Autres sections'
            df_pie_clean = df_pie_clean.groupby('quartier')['nb_ventes'].sum().reset_index()

        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader(f"💰 Top {top_n} Prix au m² (Médian)")
            df_q_data = df_filtered.groupby('quartier')['prix_m2'].median().sort_values(ascending=False).head(top_n).reset_index()
            fig_q = px.bar(df_q_data, x='prix_m2', y='quartier', orientation='h', 
                           color='prix_m2', color_continuous_scale='Blues',
                           labels={'prix_m2': 'Prix m² Médian (€)', 'quartier': 'Section'})
            fig_q.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_q, use_container_width=True)

        with c2:
            st.subheader(f"🥧 Part de marché (Top {top_n} + Autres)")
            fig_pie = px.pie(df_pie_clean, values='nb_ventes', names='quartier', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textinfo='percent+label')
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
            st.write("Source : Bien'Ici")
            st.dataframe(df_filtered, use_container_width=True)

elif mode_key != "Acheteurs":
    st.info("⚠️ Aucune donnée disponible. Vérifiez vos filtres ou lancez le crawler.")
