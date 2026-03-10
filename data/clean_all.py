"""
Nettoyage global des données - Observatoire Immobilier Toulon
Produit des fichiers *_clean.csv lisibles et fiables.
"""

import pandas as pd
import re
import os

# ─────────────────────────────────────────────
# Mapping sections cadastrales → quartiers Toulon
# Source: géographie cadastrale commune 83137
# ─────────────────────────────────────────────
SECTION_TO_QUARTIER = {
    # Centre-ville & Vieille ville
    "000AB": "Centre-ville",  "000AC": "Centre-ville",  "000AD": "Centre-ville",
    "000AE": "Haute-ville",   "000AF": "Haute-ville",   "000AG": "Haute-ville",
    "000AH": "Champs-de-Mars","000AI": "Champs-de-Mars","000AJ": "Champs-de-Mars",
    "000AK": "Saint-Roch",    "000AL": "Saint-Roch",    "000AM": "Saint-Roch",
    "000AN": "Saint-Roch",    "000AO": "Saint-Roch",    "000AP": "Saint-Roch",
    "000AQ": "Pont du Las",   "000AR": "Pont du Las",   "000AS": "Pont du Las",
    "000AT": "Pont du Las",   "000AU": "La Rode",        "000AV": "La Rode",
    "000AW": "Aguillon",      "000AX": "Aguillon",      "000AY": "Aguillon",
    "000AZ": "Aguillon",
    # Mourillon & Cap Brun
    "000BA": "Le Mourillon",  "000BB": "Le Mourillon",  "000BC": "Le Mourillon",
    "000BD": "Le Mourillon",  "000BE": "Le Mourillon",  "000BF": "Cap Brun",
    "000BG": "Cap Brun",      "000BH": "Cap Brun",      "000BI": "Cap Brun",
    "000BJ": "Cap Brun",      "000BK": "Saint-Jean du Var","000BL": "Saint-Jean du Var",
    "000BM": "Beaulieu",      "000BN": "Beaulieu",      "000BO": "Beaulieu",
    "000BP": "Pont du Las",   "000BQ": "Pont du Las",   "000BR": "Brunet",
    "000BS": "Brunet",        "000BT": "Brunet",        "000BU": "Sainte-Musse",
    "000BV": "Sainte-Musse",  "000BW": "Sainte-Musse",  "000BX": "La Serinette",
    "000BY": "La Serinette",  "000BZ": "Valbertrand",
    # Claret, Faron, nord
    "000CA": "Claret",        "000CB": "Claret",        "000CC": "Claret",
    "000CD": "Porte d'Italie","000CE": "Porte d'Italie","000CF": "Siblas",
    "000CG": "Siblas",        "000CH": "La Chapelle",   "000CI": "La Chapelle",
    "000CJ": "Valbertrand",   "000CK": "Valbertrand",   "000CL": "Bon Rencontre",
    "000CM": "Bon Rencontre", "000CN": "Bon Rencontre", "000CO": "Saint-Antoine",
    "000CP": "Saint-Antoine", "000CQ": "Saint-Antoine", "000CR": "Les Routes",
    "000CS": "Les Routes",    "000CT": "Les Routes",    "000CU": "Faron",
    "000CV": "Faron",         "000CW": "Saint-Roch",    "000CX": "Saint-Roch",
    "000CY": "Haute-ville",   "000CZ": "Haute-ville",
    # Ouest & périphérie
    "000DA": "La Valette",    "000DB": "La Valette",    "000DC": "La Valette",
    "000DD": "Ollioules",     "000DE": "Ollioules",     "000DF": "Six-Fours",
    "000DG": "Le Pradet",     "000DH": "Le Pradet",     "000DI": "La Garde",
    "000DJ": "La Garde",      "000DK": "La Garde",      "000DL": "La Garde",
}

def section_to_quartier(section_str):
    """Convertit 'Section 000BV' → 'Sainte-Musse'."""
    if pd.isna(section_str):
        return "Inconnu"
    code = str(section_str).replace("Section ", "").strip()
    return SECTION_TO_QUARTIER.get(code, f"Sect. {code[-2:]}")  # fallback: 2 lettres


def type_bien_from_surface(surface):
    """Infère le type de bien depuis la surface."""
    if pd.isna(surface) or surface <= 0:
        return "Inconnu"
    if surface < 30:
        return "Studio"
    if surface < 65:
        return "Appartement (T2-T3)"
    if surface < 120:
        return "Appartement (T3-T4)"
    if surface < 200:
        return "Grande surface / Maison"
    return "Bien exceptionnel"


# ─────────────────────────────────────────────
# 1. DVF
# ─────────────────────────────────────────────
def clean_dvf(src="data/dvf_toulon_2020_now.csv", dst="data/dvf_clean.csv"):
    print("Nettoyage DVF...")
    df = pd.read_csv(src, encoding='utf-8-sig')

    initial = len(df)

    # Filtres qualité
    df = df[df['surface'] > 5]                        # exclut parkings/caves
    df = df[df['surface'] < 500]                       # exclut locaux industriels
    df = df[df['budget'] >= 10_000]                    # exclut valeurs aberrantes
    df = df[df['budget'] <= 5_000_000]                 # exclut ultra-luxe/lots

    # Recalcul prix_m2 propre
    df['prix_m2'] = (df['budget'] / df['surface']).round(0)
    df = df[df['prix_m2'].between(500, 20_000)]        # filtre prix/m² absurdes

    # Quartier lisible
    df['quartier'] = df['quartier'].apply(section_to_quartier)

    # Type de bien
    df['type_bien'] = df['surface'].apply(type_bien_from_surface)

    # Adresse en titre (plus lisible)
    df['adresse_nom_voie'] = df['adresse_nom_voie'].str.title().fillna("Adresse inconnue")

    # Date propre
    df['date_mutation'] = pd.to_datetime(df['date_mutation']).dt.strftime('%Y-%m-%d')
    df['annee'] = pd.to_datetime(df['date_mutation']).dt.year
    df['mois'] = pd.to_datetime(df['date_mutation']).dt.to_period('M').astype(str)

    # Renommer pour clarté
    df = df.rename(columns={
        'budget': 'prix_vente',
        'surface': 'surface_m2',
        'adresse_nom_voie': 'adresse',
    })

    # Réordonner colonnes
    df = df[['date_mutation', 'annee', 'mois', 'type_bien', 'prix_vente',
             'surface_m2', 'prix_m2', 'quartier', 'adresse']]

    df.to_csv(dst, index=False, encoding='utf-8-sig')
    print(f"  {initial} → {len(df)} lignes ({initial - len(df)} supprimées). Sauvé : {dst}")
    return df


# ─────────────────────────────────────────────
# 2. Annonces Bien'Ici
# ─────────────────────────────────────────────
def clean_annonces(src="data/annonces_toulon_clean.csv", dst="data/annonces_clean.csv"):
    print("Nettoyage Annonces...")
    df = pd.read_csv(src, encoding='utf-8-sig')

    initial = len(df)

    # Renommer colonnes
    df = df.rename(columns={
        'detailedSheetLink href': 'url',
        'Type_bien': 'type_bien',
        'Quartier': 'quartier',
        'Surface_m2': 'surface_m2',
        'Prix_total_net': 'prix_vente',
    })
    # Trouver la colonne prix_m2 (peut avoir un nom encodé)
    pm2_col = [c for c in df.columns if 'prix_m2' in c.lower() or 'm2' in c.lower() and 'calcul' in c.lower()]
    if pm2_col:
        df = df.rename(columns={pm2_col[0]: 'prix_m2'})

    # Filtres qualité
    df = df[df['surface_m2'] > 5]
    df = df[df['surface_m2'] < 500]
    df = df[df['prix_vente'] >= 10_000]
    df = df[df['prix_vente'] <= 5_000_000]

    # Recalcul prix_m2 propre
    df['prix_m2'] = (df['prix_vente'] / df['surface_m2']).round(0)
    df = df[df['prix_m2'].between(500, 20_000)]

    # Nettoyage quartier : fix encodages, strip whitespace
    df['quartier'] = df['quartier'].str.strip()
    df['quartier'] = df['quartier'].str.replace('â€™', "'", regex=False)
    df['quartier'] = df['quartier'].str.replace('Ã©', 'é', regex=False)
    df['quartier'] = df['quartier'].str.replace('Ã ', 'à', regex=False)
    df['quartier'] = df['quartier'].fillna("Quartier inconnu")

    # Simplifier type_bien
    df['type_bien'] = df['type_bien'].str.strip()
    df.loc[df['type_bien'] == 'Autre', 'type_bien'] = 'Autre bien'

    # Colonnes finales (sans l'URL qui encombre)
    cols = ['type_bien', 'quartier', 'surface_m2', 'prix_vente', 'prix_m2', 'url']
    df = df[[c for c in cols if c in df.columns]]

    df.to_csv(dst, index=False, encoding='utf-8-sig')
    print(f"  {initial} → {len(df)} lignes. Sauvé : {dst}")
    return df


# ─────────────────────────────────────────────
# 3. LeBonCoin marché
# ─────────────────────────────────────────────
def clean_leboncoin(src="acheteur/data/marche_leboncoin.csv", dst="acheteur/data/marche_leboncoin_clean.csv"):
    print("Nettoyage LeBonCoin...")
    df = pd.read_csv(src, encoding='utf-8-sig')

    initial = len(df)

    # Fix surface : "49 m²" → 49
    df['surface_m2'] = df['surface'].astype(str).str.extract(r'(\d+)')[0]
    df['surface_m2'] = pd.to_numeric(df['surface_m2'], errors='coerce')

    # Fix prix
    df['prix'] = pd.to_numeric(df['prix'].astype(str).str.replace(r'\s', '', regex=True), errors='coerce')

    # Recalcul prix_m2
    mask = df['surface_m2'] > 0
    df.loc[mask, 'prix_m2'] = (df.loc[mask, 'prix'] / df.loc[mask, 'surface_m2']).round(0)

    # Fix nb_pieces
    df['nb_pieces'] = pd.to_numeric(df['nb_pieces'], errors='coerce')

    # Nettoyage titre : fix encodage
    df['titre'] = df['titre'].str.encode('latin-1', errors='ignore').str.decode('utf-8', errors='ignore')

    # Filtres qualité
    df = df[df['surface_m2'].between(5, 500)]
    df = df[df['prix'].between(10_000, 5_000_000)]
    df = df[df['prix_m2'].between(500, 20_000)]

    # Quartier : remplacer "Non precise" par NaN → plus honnête
    df['quartier'] = df['quartier'].replace({'Non precise': None, 'Non précisé': None})

    # Colonnes finales (date_publication prioritaire sur date_crawl)
    cols = ['source', 'date_publication', 'date_crawl', 'type_bien', 'nb_pieces', 'surface_m2',
            'prix', 'prix_m2', 'quartier', 'criteres', 'titre', 'url']
    df = df[[c for c in cols if c in df.columns]]

    df.to_csv(dst, index=False, encoding='utf-8-sig')
    print(f"  {initial} → {len(df)} lignes. Sauvé : {dst}")
    return df


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("=== Nettoyage des données ===\n")
    df_dvf  = clean_dvf()
    df_ann  = clean_annonces()
    df_lbc  = clean_leboncoin()
    print("\n=== Aperçu DVF (5 lignes) ===")
    print(df_dvf.head())
    print("\n=== Aperçu Annonces (5 lignes) ===")
    print(df_ann.head())
    print("\n=== Aperçu LeBonCoin (5 lignes) ===")
    print(df_lbc.head())
    print("\nTermine !")
