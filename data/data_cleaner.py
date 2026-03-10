import pandas as pd
import re
import os
from datetime import datetime, timedelta


def clean_price(value):
    if pd.isna(value):
        return None
    value = re.sub(r"[^\d]", "", str(value))
    return int(value) if value else None


def extract_surface(title):
    if pd.isna(title):
        return None
    match = re.search(r"(\d+)\s*m²", str(title))
    return int(match.group(1)) if match else None


def extract_type(title):
    if pd.isna(title):
        return None

    title = str(title)

    if "Appartement" in title:
        return "Appartement"

    if "Maison" in title:
        return "Maison"

    return "Autre"


def extract_quartier(address):
    if pd.isna(address):
        return None

    match = re.search(r"\((.*?)\)", str(address))

    if match:
        return match.group(1)

    return None



def extract_publication_date(text):

    if pd.isna(text):
        return None

    text = str(text).lower()
    today = datetime.today()

    mois = {
        "janvier": 1,
        "janv": 1,
        "janv.": 1,

        "février": 2,
        "fevrier": 2,
        "févr": 2,
        "févr.": 2,

        "mars": 3,

        "avril": 4,
        "avr": 4,
        "avr.": 4,

        "mai": 5,

        "juin": 6,

        "juillet": 7,
        "juil": 7,
        "juil.": 7,

        "août": 8,
        "aout": 8,

        "septembre": 9,
        "sept": 9,
        "sept.": 9,

        "octobre": 10,
        "oct": 10,
        "oct.": 10,

        "novembre": 11,
        "nov": 11,
        "nov.": 11,

        "décembre": 12,
        "decembre": 12,
        "déc": 12,
        "déc.": 12
    }

    match = re.search(r"publiée le (\d{1,2}) ([a-zéûô\.]+) (\d{4})", text)

    if match:
        jour = int(match.group(1))
        mois_str = match.group(2).strip()
        annee = int(match.group(3))

        if mois_str in mois:
            date = datetime(annee, mois[mois_str], jour)
            return date.strftime("%Y-%m-%d")

    match = re.search(r"il y a (\d+) jour", text)
    if match:
        days = int(match.group(1))
        date = today - timedelta(days=days)
        return date.strftime("%Y-%m-%d")

    match = re.search(r"il y a (\d+) semaine", text)
    if match:
        weeks = int(match.group(1))
        date = today - timedelta(weeks=weeks)
        return date.strftime("%Y-%m-%d")

    match = re.search(r"il y a (\d+) mois", text)
    if match:
        months = int(match.group(1))
        date = today - timedelta(days=30 * months)
        return date.strftime("%Y-%m-%d")

    match = re.search(r"plus de (\d+) mois", text)
    if match:
        months = int(match.group(1))
        date = today - timedelta(days=30 * months)
        return date.strftime("%Y-%m-%d")

    return None


def main():

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    df = pd.read_csv("brutbienici.csv")

    df["prix_total"] = df["ad-price__the-price"].apply(clean_price)
    df["prix_m2"] = df["ad-price__price-per-square-meter"].apply(clean_price)

    df["surface"] = df["ad-overview-details__ad-title"].apply(extract_surface)

    df["type_bien"] = df["ad-overview-details__ad-title"].apply(extract_type)

    df["quartier"] = df["ad-overview-details__address-title"].apply(extract_quartier)

    df["date_publication"] = df["ad-overview-list__details-infos"].apply(extract_publication_date)

    df["prix_m2_final"] = df.apply(
        lambda row: row["prix_m2"]
        if pd.notna(row["prix_m2"])
        else (
            row["prix_total"] / row["surface"]
            if pd.notna(row["prix_total"]) and pd.notna(row["surface"])
            else None
        ),
        axis=1,
    )

    clean_df = df[
        [
            "detailedSheetLink href",
            "type_bien",
            "quartier",
            "surface",
            "prix_total",
            "prix_m2_final",
            "date_publication",
            "account-logo__display-name",
        ]
    ]

    clean_df = clean_df.rename(
        columns={
            "detailedSheetLink href": "url",
            "account-logo__display-name": "agence",
        }
    )

    clean_df = clean_df.dropna(subset=["prix_total", "surface"])
    clean_df = clean_df.drop_duplicates(subset=["url"])

    clean_df.to_csv("annonces_toulon_clean.csv", index=False)

    print("Dataset nettoyé créé : annonces_toulon.csv")
    print("Nombre d'annonces :", len(clean_df))


if __name__ == "__main__":
    main()
