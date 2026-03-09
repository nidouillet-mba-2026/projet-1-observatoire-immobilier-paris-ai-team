"""
Point d'entrée principal - Lance tous les crawlers et génère le rapport.
Usage : python acheteur/run_all.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acheteur.leboncoin_crawler import crawl_leboncoin
from acheteur.forum_crawler import crawl_forums
from acheteur.facebook_template import load_or_create_template
from acheteur.profiler import load_all, generate_report

def main():
    print("=" * 50)
    print("  CRAWLER ACHETEURS IMMOBILIER - TOULON")
    print("=" * 50)

    print("\n[1/3] LeBonCoin...")
    crawl_leboncoin(max_pages=10)

    print("\n[2/3] Forums (PAP, Logic-Immo)...")
    crawl_forums()

    print("\n[3/3] Données Facebook (template)...")
    load_or_create_template()

    print("\n[Rapport] Consolidation...")
    df = load_all("acheteur/data")
    generate_report(df, "acheteur/data/rapport_acheteurs.csv")

    print("\n✓ Terminé ! Fichiers dans acheteur/data/")

if __name__ == "__main__":
    main()
