import requests
import pandas as pd
import time
from datetime import datetime
import os

def get_sections(commune_code="83137"):
    """Fetch all cadastral sections for a given commune."""
    url = f"https://cadastre.data.gouv.fr/bundler/cadastre-etalab/communes/{commune_code}/geojson/sections"
    try:
        response = requests.get(url)
        response.raise_for_status()
        geojson = response.json()
        sections = [feature['id'] for feature in geojson['features']]
        return sections
    except Exception as e:
        print(f"Error fetching sections: {e}")
        return []

def get_mutations(section_id):
    """Fetch mutations for a specific cadastral section."""
    commune_code = section_id[:5]
    section_code = section_id[5:]
    url = f"https://app.dvf.etalab.gouv.fr/api/mutations3/{commune_code}/{section_code}"
    try:
        response = requests.get(url)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json().get('mutations', [])
    except Exception as e:
        print(f"Error fetching mutations for {section_id}: {e}")
        return []

def crawl_dvf_toulon(output_file="data/dvf_toulon_2020_now.csv"):
    print("Starting DVF Crawler for Toulon...")
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    sections = get_sections("83137")
    print(f"Found {len(sections)} sections.")
    
    all_data = []
    start_date = "2020-01-01"
    
    for i, section in enumerate(sections):
        if i % 20 == 0:
            print(f"Processing section {i}/{len(sections)}...")
        
        mutations = get_mutations(section)
        for mut in mutations:
            if mut.get('date_mutation') and mut['date_mutation'] >= start_date:
                all_data.append(mut)
        
        time.sleep(0.1)

    if not all_data:
        print("No data found.")
        return

    df = pd.DataFrame(all_data)
    
    # Convert numeric columns
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce').fillna(0)
    df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce').fillna(0)
    
    agg_rules = {
        'date_mutation': 'first',
        'valeur_fonciere': 'first',
        'surface_reelle_bati': 'sum',
        'surface_terrain': 'sum',
        'adresse_nom_voie': 'first',
        'code_postal': 'first',
        'nom_commune': 'first',
        'section_prefixe': 'first' # Use prefix for neighborhood proxy if needed
    }
    
    df_clean = df.groupby('id_mutation').agg(agg_rules).reset_index()
    df_clean = df_clean.dropna(subset=['valeur_fonciere'])
    
    df_clean['budget'] = df_clean['valeur_fonciere']
    df_clean['surface'] = df_clean['surface_reelle_bati']
    
    # For Toulon, we use postcode or section prefix for quartier
    def format_cp(cp):
        try:
            if pd.isnull(cp) or str(cp).lower() == 'none':
                return "Toulon"
            return f"Toulon {int(float(cp))}"
        except:
            return f"Toulon {cp}"
            
    df_clean['quartier'] = df_clean['code_postal'].apply(format_cp)
    
    result = df_clean[['date_mutation', 'budget', 'surface', 'quartier', 'adresse_nom_voie']]
    result = result.sort_values('date_mutation', ascending=False)
    
    result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Success! Saved {len(result)} transactions to {output_file}")

if __name__ == "__main__":
    crawl_dvf_toulon()
