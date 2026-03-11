"""
Crawler Annonces Acheteurs - PAP.fr & Logic-Immo
PAP.fr a une section "Demande" où les acheteurs publient leur recherche.
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
    "Accept-Language": "fr-FR,fr;q=0.9",
}

QUARTIERS_TOULON = [
    'mourillon', 'cap brun', 'haute ville', 'saint-jean', 'pont du las',
    'brunet', 'sainte-musse', 'la rode', 'centre ville', 'le pradet',
    'la valette', 'la garde', 'six-fours', 'sanary', 'ollioules',
    'bandol', 'carqueiranne', 'hyeres', 'claret', 'faron', 'beaulieu',
    'bon rencontre', 'saint-roch', 'saint-antoine',
]

CRITERES_MAP = {
    'parking/garage': ['parking', 'garage'],
    'jardin/terrasse': ['jardin', 'terrasse', 'balcon'],
    'vue mer': ['vue mer'],
    'proche mer': ['proche mer', 'bord de mer', 'plage'],
    'calme': ['calme', 'tranquille'],
    'lumineux': ['lumineux', 'ensoleille'],
    'travaux acceptes': ['travaux', 'renover', 'rafraichir'],
    'ascenseur': ['ascenseur'],
    'cave': ['cave'],
}


# ─────────────────────────────────────────────
# Extracteurs communs
# ─────────────────────────────────────────────

def _extract_budget(text):
    text = text.lower()
    for pattern in [
        r'(\d[\d\s]*)\s*(?:eur|euro|euros)',
        r'budget[:\s]+(\d[\d\s]*)',
        r"jusqu['\s]*[a-z]*\s*(\d[\d\s]*)",
        r'max[^\d]*(\d[\d\s]*)',
        r'(\d{2,}[\d\s]{3,})',   # Nombres >= 5 chiffres
    ]:
        match = re.search(pattern, text)
        if match:
            val = int(re.sub(r'\s', '', match.group(1)))
            if 10_000 < val < 5_000_000:
                return val
    return None


def _extract_surface(text):
    match = re.search(r'(\d+)\s*m[2²]', text.lower())
    if match:
        val = int(match.group(1))
        if 10 < val < 1000:
            return val
    return None


def _extract_pieces(text):
    match = re.search(r'(\d)\s*(?:pieces?|pi[eè]ces?)|(?:t|f)(\d)\b|(\d)\s*chambre', text.lower())
    if match:
        return int(next(g for g in match.groups() if g))
    return None


def _extract_type_bien(text):
    t = text.lower()
    if any(w in t for w in ['maison', 'villa', 'pavillon']): return 'Maison'
    if any(w in t for w in ['studio']): return 'Studio'
    if any(w in t for w in ['appartement', 'appart', 'duplex']): return 'Appartement'
    if 'terrain' in t: return 'Terrain'
    return 'Non precise'


def _extract_type_achat(text):
    t = text.lower()
    if any(w in t for w in ['investissement', 'locatif', 'rendement', 'louer']): return 'Investissement locatif'
    if any(w in t for w in ['residence secondaire', 'vacances']): return 'Residence secondaire'
    if any(w in t for w in ['residence principale', 'habiter', 'vivre', 'emmenager']): return 'Residence principale'
    return 'Non precise'


def _extract_quartier(text):
    t = text.lower()
    found = [q for q in QUARTIERS_TOULON if q in t]
    return ', '.join(found) if found else 'Non precise'


def _extract_criteres(text):
    t = text.lower()
    found = [k for k, syns in CRITERES_MAP.items() if any(s in t for s in syns)]
    return ', '.join(found) if found else ''


def _build_profile(source, title, desc, price_text, url, date=''):
    if not title and not desc:
        return None
    full_text = title + ' ' + desc
    return {
        'source': source,
        'date_annonce': date,
        'date_crawl': datetime.now().strftime('%Y-%m-%d'),
        'titre': title,
        'type_bien': _extract_type_bien(full_text),
        'type_achat': _extract_type_achat(full_text),
        'budget_max': _extract_budget(price_text + ' ' + full_text),
        'surface_min': _extract_surface(full_text),
        'nb_pieces': _extract_pieces(full_text),
        'quartier_souhaite': _extract_quartier(full_text),
        'criteres': _extract_criteres(full_text),
        'url': url,
        'description': desc[:400],
    }


# ─────────────────────────────────────────────
# PAP.fr - Section "Demande" (acheteurs)
# ─────────────────────────────────────────────

PAP_URLS = [
    "https://www.pap.fr/annonce/achat-immobilier-toulon-g439967",
    "https://www.pap.fr/annonce/achat-appartement-toulon-g439967",
    "https://www.pap.fr/annonce/achat-maison-toulon-g439967",
]


def scrape_pap(max_pages=5):
    profiles = []
    print("=== Scraping PAP.fr ===")

    for base_url in PAP_URLS:
        print(f"  URL : {base_url}")
        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"

            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                # PAP.fr utilise des balises article pour les annonces
                cards = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'item|annonce|listing'))

                if not cards:
                    break

                for card in cards:
                    title_el = card.find(['h2', 'h3', 'h4', 'a'])
                    title = title_el.get_text(strip=True) if title_el else ''

                    desc_el = card.find('p') or card.find(class_=re.compile(r'desc|text|resume'))
                    desc = desc_el.get_text(strip=True) if desc_el else ''

                    price_el = card.find(class_=re.compile(r'price|prix'))
                    price_text = price_el.get_text(strip=True) if price_el else ''

                    link_el = card.find('a', href=True)
                    ad_url = ''
                    if link_el:
                        href = link_el['href']
                        ad_url = href if href.startswith('http') else 'https://www.pap.fr' + href

                    date_el = card.find(class_=re.compile(r'date|time'))
                    date = date_el.get_text(strip=True) if date_el else ''

                    profile = _build_profile('PAP.fr', title, desc, price_text, ad_url, date)
                    if profile:
                        profiles.append(profile)

                print(f"    Page {page} : {len(cards)} annonces")
                time.sleep(2)

            except Exception as e:
                print(f"    Erreur page {page}: {e}")
                break

    print(f"  Total PAP.fr : {len(profiles)} profils")
    return profiles


# ─────────────────────────────────────────────
# Logic-Immo - Annonces achat Toulon
# ─────────────────────────────────────────────

LOGIC_BASE = "https://www.logic-immo.com/achat-immobilier/toulon-83000/"


def scrape_logic_immo(max_pages=3):
    profiles = []
    print("=== Scraping Logic-Immo ===")

    for page in range(1, max_pages + 1):
        url = LOGIC_BASE if page == 1 else f"{LOGIC_BASE}?pcs={page}"
        print(f"  Page {page}...")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Essai via JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string or '{}')
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get('@type') in ('Apartment', 'House', 'RealEstateListing'):
                            title = item.get('name', '')
                            desc = item.get('description', '')
                            price = str(item.get('offers', {}).get('price', ''))
                            ad_url = item.get('url', '')
                            profile = _build_profile('Logic-Immo', title, desc, price, ad_url)
                            if profile:
                                profiles.append(profile)
                except Exception:
                    continue

            # Fallback HTML
            cards = soup.find_all(['article', 'div'], class_=re.compile(r'offer-card|annonce|listing-item'))
            for card in cards[:20]:
                title_el = card.find(['h2', 'h3', 'span'], class_=re.compile(r'title|name'))
                title = title_el.get_text(strip=True) if title_el else ''

                desc_el = card.find(['p', 'div'], class_=re.compile(r'desc|summary'))
                desc = desc_el.get_text(strip=True) if desc_el else ''

                price_el = card.find(class_=re.compile(r'price|prix'))
                price_text = price_el.get_text(strip=True) if price_el else ''

                link_el = card.find('a', href=True)
                ad_url = link_el['href'] if link_el else ''

                profile = _build_profile('Logic-Immo', title, desc, price_text, ad_url)
                if profile:
                    profiles.append(profile)

        except Exception as e:
            print(f"  Erreur: {e}")

        time.sleep(2)

    print(f"  Total Logic-Immo : {len(profiles)} profils")
    return profiles


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def crawl_forums(output_file="acheteur/data/acheteurs_annonces.csv"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    all_profiles = []

    all_profiles.extend(scrape_pap(max_pages=5))
    all_profiles.extend(scrape_logic_immo(max_pages=3))

    if not all_profiles:
        print("Aucun profil trouve.")
        return pd.DataFrame()

    df = pd.DataFrame(all_profiles).drop_duplicates(subset=['titre', 'source'])
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nOK {len(df)} profils sauvegardes dans {output_file}")
    return df


if __name__ == "__main__":
    df = crawl_forums()
    if not df.empty:
        print(df[['source', 'type_bien', 'budget_max', 'quartier_souhaite']].head(10).to_string())
