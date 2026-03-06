import pandas as pd
import re
import os

def clean_price(price):
    if pd.isna(price):
        return None
    price = str(price)
    price = re.sub(r"[^\d]", "", price)
    if price == "":
        return None
    return int(price)

def clean_price_m2(p):
    if pd.isna(p):
        return None
    p = str(p)
    p = re.sub(r"[^\d]", "", p)
    if p == "":
        return None
    return int(p)

def extract_surface(title):
    if pd.isna(title):
        return None
    match = re.search(r"(\d+)\s*m²", title)
    if match:
        return int(match.group(1))
    return None

def extract_type(title):
    if pd.isna(title):
        return None
    if "Appartement" in title:
        return "Appartement"
    elif "Maison" in title:
        return "Maison"
    else:
        return "Autre"

def extract_quartier(address):
    if pd.isna(address):
        return None
    match = re.search(r"\((.*?)\)", address)
    if match:
        return match.group(1)
    return None

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    csv_file = "annonces_toulon_bienici.csv"
    df = pd.read_csv(csv_file)

    df["Prix_total_net"] = df["ad-price__the-price"].apply(clean_price)
    df["Prix_m2_net"] = df["ad-price__price-per-square-meter"].apply(clean_price_m2)
    df["Surface_m2"] = df["ad-overview-details__ad-title"].apply(extract_surface)

    df["Prix_m2_calculé"] = df.apply(
        lambda row: row["Prix_m2_net"] if pd.notna(row["Prix_m2_net"]) 
        else (row["Prix_total_net"] / row["Surface_m2"] 
              if pd.notna(row["Prix_total_net"]) and pd.notna(row["Surface_m2"]) else None),
        axis=1
    )

    df["Type_bien"] = df["ad-overview-details__ad-title"].apply(extract_type)
    df["Quartier"] = df["ad-overview-details__address-title"].apply(extract_quartier)

    clean_df = df[["detailedSheetLink href", "Type_bien", "Quartier", "Surface_m2", "Prix_total_net", "Prix_m2_calculé"]]

    clean_df = clean_df.dropna(subset=["Prix_total_net", "Surface_m2"])

    clean_df.to_csv("annonces_toulon_clean.csv", index=False)

    print("Fichier nettoyé créé : annonces_toulon_clean.csv")

if __name__ == "__main__":
    main()
