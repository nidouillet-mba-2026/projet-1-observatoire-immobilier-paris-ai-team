"""
Template import manuel - Données Facebook Groups / Forums privés
Facebook bloque le scraping automatique (authentification + anti-bot).

UTILISATION :
1. Rejoindre les groupes Facebook pertinents :
   - "Immobilier Toulon et alentours"
   - "Achat immobilier Toulon 83"
   - "Investissement immobilier Var 83"
2. Copier manuellement les posts intéressants dans le CSV ci-dessous
3. Lancer : python facebook_template.py

FORMAT CSV ATTENDU (acheteur/data/facebook_manuel.csv) :
date, auteur_pseudo, titre, description, type_bien, budget_max, surface_min, nb_pieces, quartier, type_achat, criteres
"""

import pandas as pd
import os

TEMPLATE_DATA = [
    {
        "source": "Facebook - Immobilier Toulon",
        "date_annonce": "2025-03-01",
        "titre": "Recherche appartement T3 Mourillon",
        "description": "Bonjour, nous cherchons un T3 minimum 60m2 au Mourillon ou centre-ville, budget 280 000€, résidence principale. Terrasse ou balcon souhaité.",
        "type_bien": "Appartement",
        "type_achat": "Résidence principale",
        "budget_max": 280000,
        "surface_min": 60,
        "nb_pieces": 3,
        "quartier_souhaite": "mourillon, centre ville",
        "criteres": "jardin/terrasse",
        "url": "",
        "date_crawl": "2025-03-09",
    },
    {
        "source": "Facebook - Investissement immobilier Var",
        "date_annonce": "2025-02-20",
        "titre": "Cherche T2 investissement locatif Toulon",
        "description": "Investisseur cherche T2 ou T3 pour mise en location, rendement brut minimum 5%, budget 150 000€ max. Quartier Brunet ou Pont du Las.",
        "type_bien": "Appartement",
        "type_achat": "Investissement locatif",
        "budget_max": 150000,
        "surface_min": 40,
        "nb_pieces": 2,
        "quartier_souhaite": "brunet, pont du las",
        "criteres": "",
        "url": "",
        "date_crawl": "2025-03-09",
    },
]

def load_or_create_template(filepath="acheteur/data/facebook_manuel.csv"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if os.path.exists(filepath):
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        print(f"OK Fichier existant charge : {len(df)} entrees")
        return df

    # Crée un fichier template avec des exemples
    df = pd.DataFrame(TEMPLATE_DATA)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"OK Template cree : {filepath}")
    print("  -> Remplis ce fichier avec les donnees des groupes Facebook puis relance.")
    return df

if __name__ == "__main__":
    df = load_or_create_template()
    print(df[['source', 'type_bien', 'budget_max', 'quartier_souhaite']].to_string())
