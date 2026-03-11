import pandas as pd
import os

# Changer le répertoire de travail pour le dossier du script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

annonces = pd.read_csv("annonces_toulon.csv")
dvf = pd.read_csv("dvf_toulon.csv")

resultats = []

for _, annonce in annonces.iterrows():

    surface = annonce["surface"]
    quartier = annonce["quartier"]
    type_bien = annonce["type_bien"]

    comparables = dvf[
        (dvf["quartier"] == quartier) &
        (dvf["type_bien"].str.contains(type_bien, case=False, na=False)) &
        (dvf["surface_m2"] > surface * 0.8) &
        (dvf["surface_m2"] < surface * 1.2)
    ]

    if len(comparables) > 3:

        prix_marche = comparables["prix_m2"].mean()

        prix_annonce = annonce["prix_m2_final"]

        ecart = prix_annonce - prix_marche

        ecart_pct = (ecart / prix_marche) * 100

        resultats.append({
            "url": annonce["url"],
            "quartier": quartier,
            "surface": surface,
            "prix_annonce_m2": prix_annonce,
            "prix_marche_m2": round(prix_marche,2),
            "ecart_m2": round(ecart,2),
            "ecart_pct": round(ecart_pct,2)
        })

comparaison = pd.DataFrame(resultats)

comparaison.to_csv("comparaison_marche.csv", index=False)

print("Comparaison créée dans comparaison_marche.csv")