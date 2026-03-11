"""
Crawler LeBonCoin - Analyse du marché immobilier Toulon
Scrape les annonces vendeurs pour analyser l'offre et inférer la demande acheteur.
Note : LeBonCoin n'a pas de section "acheteur" dédiée en immobilier.
       Ce crawler analyse donc l'offre pour comprendre les tendances du marché.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
import json
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

BASE_URL = "https://www.leboncoin.fr/recherche"

SEARCH_QUERIES = [
    "appartement toulon",
    "maison toulon",
    "villa toulon",
    "studio toulon",
]

SEARCH_PARAMS_BASE = {
    "category": "9",
    "locations": "Toulon_83000",
    "sort": "time",
    "order": "desc",
}

QUARTIERS_TOULON = [
    'mourillon', 'cap brun', 'haute ville', 'saint-jean', 'pont du las',
    'brunet', 'sainte-musse', 'la rode', 'centre ville', 'le pradet',
    'la valette', 'la garde', 'six-fours', 'sanary', 'ollioules',
    'bandol', 'carqueiranne', 'hyeres', 'claret', 'faron', 'beaulieu',
    'bon rencontre', 'saint-roch', 'saint-antoine',
]


def extract_surface(text):
    match = re.search(r'(\d+)\s*m[2²]', text.lower())
    if match:
        val = int(match.group(1))
        if 10 < val < 1000:
            return val
    return None


def extract_pieces(text):
    match = re.search(r'(\d)\s*(?:pieces?|pi[eè]ces?|p\b)|(?:t|f)(\d)\b', text.lower())
    if match:
        return int(next(g for g in match.groups() if g))
    return None


def extract_type_bien(text):
    t = text.lower()
    if any(w in t for w in ['maison', 'villa', 'pavillon']): return 'Maison'
    if any(w in t for w in ['studio']): return 'Studio'
    if any(w in t for w in ['appartement', 'appart', 'duplex', 'loft']): return 'Appartement'
    if 'terrain' in t: return 'Terrain'
    return 'Non precis'


def extract_quartier(text):
    t = text.lower()
    found = [q for q in QUARTIERS_TOULON if q in t]
    return ', '.join(found) if found else 'Non precise'


def extract_criteres(text):
    criteres = {
        'parking/garage': ['parking', 'garage'],
        'jardin/terrasse': ['jardin', 'terrasse', 'balcon'],
        'vue mer': ['vue mer'],
        'proche mer': ['proche mer', 'bord de mer', 'plage'],
        'calme': ['calme', 'tranquille'],
        'lumineux': ['lumineux', 'ensoleille'],
        'travaux': ['travaux', 'renover'],
        'ascenseur': ['ascenseur'],
        'cave': ['cave'],
    }
    t = text.lower()
    found = [k for k, syns in criteres.items() if any(s in t for s in syns)]
    return ', '.join(found) if found else ''


def fetch_page(query, page=1):
    params = {**SEARCH_PARAMS_BASE, "text": query, "page": page}
    try:
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  Erreur page {page}: {e}")
        return None


def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find('script', id='__NEXT_DATA__')
    if script:
        try:
            data = json.loads(script.string)
            props = data.get('props', {}).get('pageProps', {})
            ads = (
                props.get('searchData', {}).get('ads', []) or
                props.get('ads', []) or
                props.get('initialAds', []) or
                []
            )
            return ads
        except Exception:
            pass
    # Fallback HTML
    cards = soup.find_all('article', attrs={'data-qa-id': 'aditem_container'})
    ads = []
    for card in cards:
        title_el = card.find(attrs={'data-qa-id': 'aditem_title'})
        price_el = card.find(attrs={'data-qa-id': 'aditem_price'})
        link_el = card.find('a', href=True)
        ads.append({
            'subject': title_el.get_text(strip=True) if title_el else '',
            'body': '',
            'price': [price_el.get_text(strip=True)] if price_el else [],
            'url': 'https://www.leboncoin.fr' + link_el['href'] if link_el else '',
            'attributes': [],
        })
    return ads


def crawl_leboncoin(max_pages=3, output_file="acheteur/data/marche_leboncoin.csv"):
    print("=== Crawler LeBonCoin - Marche immobilier Toulon ===")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    all_listings = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        print(f"\nRecherche : '{query}'")
        for page in range(1, max_pages + 1):
            print(f"  Page {page}/{max_pages}...")
            html = fetch_page(query, page)
            if not html:
                break

            ads = parse_page(html)
            print(f"    {len(ads)} annonces")

            if not ads:
                break

            for ad in ads:
                title = ad.get('subject', '') or ''
                desc = ad.get('body', '') or ''
                full_text = title + ' ' + desc
                url = ad.get('url', '')

                if url and url in seen_urls:
                    continue
                seen_urls.add(url)

                attrs = {}
                for a in ad.get('attributes', []):
                    if isinstance(a, dict):
                        attrs[a.get('key', '')] = a.get('value_label') or a.get('value')

                price_raw = ad.get('price', [])
                price_val = price_raw[0] if price_raw else None
                if isinstance(price_val, str):
                    nums = re.findall(r'\d+', price_val.replace(' ', '').replace('\xa0', ''))
                    price_val = int(''.join(nums)) if nums else None

                surface = attrs.get('square') or extract_surface(full_text)
                prix_m2 = None
                if price_val and surface:
                    try:
                        prix_m2 = round(int(price_val) / int(surface))
                    except Exception:
                        pass

                listing = {
                    'source': 'LeBonCoin',
                    'date_crawl': datetime.now().strftime('%Y-%m-%d'),
                    'titre': title,
                    'type_bien': attrs.get('real_estate_type') or extract_type_bien(full_text),
                    'prix': price_val,
                    'surface': surface,
                    'prix_m2': prix_m2,
                    'nb_pieces': attrs.get('rooms') or extract_pieces(full_text),
                    'quartier': extract_quartier(full_text),
                    'criteres': extract_criteres(full_text),
                    'url': url,
                }
                all_listings.append(listing)

            time.sleep(2)

    if not all_listings:
        print("Aucune annonce trouvee.")
        return pd.DataFrame()

    df = pd.DataFrame(all_listings)
    # Nettoyage colonnes numériques
    for col in ['prix', 'prix_m2', 'surface']:
        df[col] = pd.to_numeric(df[col].astype(str).str.extract(r'([\d.]+)')[0], errors='coerce')
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nOK {len(df)} annonces sauvegardees dans {output_file}")

    # Stats rapides
    print(f"\n--- Stats marche Toulon (LeBonCoin) ---")
    print(f"Prix median  : {df['prix'].median():,.0f} EUR") if df['prix'].notna().any() else None
    print(f"Prix/m2 med  : {df['prix_m2'].median():,.0f} EUR/m2") if df['prix_m2'].notna().any() else None
    print(f"Surface med  : {df['surface'].median():.0f} m2") if df['surface'].notna().any() else None
    print(f"\nRepartition type bien :\n{df['type_bien'].value_counts()}")
    print(f"\nQuartiers :\n{df['quartier'].value_counts().head(10)}")

    return df


def crawl_acheteurs_leboncoin(max_pages=5, output_file="acheteur/data/acheteurs_leboncoin.csv"):
    """Cherche spécifiquement les annonces de RECHERCHE de bien (Acheteurs)."""
    print("\n=== Crawler LeBonCoin - Profils Acheteurs Toulon ===")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    queries = ["cherche appartement", "recherche maison", "recherche appartement toulon", "cherche villa"]
    all_profiles = []
    seen_urls = set()

    for query in queries:
        print(f"Recherche acheteurs : '{query}'")
        for page in range(1, max_pages + 1):
            html = fetch_page(query, page)
            if not html: break
            
            ads = parse_page(html)
            if not ads: break

            for ad in ads:
                title = ad.get('subject', '').lower()
                desc = ad.get('body', '').lower()
                full_text = title + ' ' + desc
                url = ad.get('url', '')

                # On ne garde que si le titre contient un mot-clé de recherche
                if not any(w in title for w in ['cherche', 'recherche', 'recherchons', 'souhaite']):
                    continue

                if url in seen_urls: continue
                seen_urls.add(url)

                # Extraction budget (souvent dans le titre ou description)
                budget = None
                nums = re.findall(r'(\d{2,}[\d\s]{3,})', full_text.replace(' ', '').replace('\xa0', ''))
                if nums:
                    val = int(nums[0])
                    if 10000 < val < 2000000: budget = val

                profile = {
                    'source': 'LeBonCoin (Acheteur)',
                    'date_annonce': datetime.now().strftime('%Y-%m-%d'),
                    'date_crawl': datetime.now().strftime('%Y-%m-%d'),
                    'titre': ad.get('subject', ''),
                    'type_bien': extract_type_bien(full_text),
                    'type_achat': 'Residence principale' if 'habiter' in full_text else 'Non precise',
                    'budget_max': budget,
                    'surface_min': extract_surface(full_text),
                    'nb_pieces': extract_pieces(full_text),
                    'quartier_souhaite': extract_quartier(full_text),
                    'criteres': extract_criteres(full_text),
                    'url': url,
                    'description': desc[:400]
                }
                all_profiles.append(profile)
            time.sleep(1)

    if all_profiles:
        df = pd.DataFrame(all_profiles)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"OK {len(df)} profils acheteurs trouves.")
        return df
    print("Aucun profil acheteur trouve.")
    return pd.DataFrame()


if __name__ == "__main__":
    crawl_leboncoin(max_pages=2)
    crawl_acheteurs_leboncoin(max_pages=2)
