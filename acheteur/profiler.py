"""
Profiler acheteurs - Consolide et analyse les profils collectés.
Génère des segments de profils types d'acheteurs à Toulon.
"""

import pandas as pd
import os


def load_all(data_dir="acheteur/data"):
    dfs = []
    for f in os.listdir(data_dir):
        if f.endswith('.csv'):
            path = os.path.join(data_dir, f)
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')
                dfs.append(df)
                print(f"  Chargé: {f} ({len(df)} lignes)")
            except Exception as e:
                print(f"  Erreur {f}: {e}")
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['titre', 'source'])


def segment_acheteurs(df):
    """Segmente les acheteurs en profils types."""
    if df.empty:
        return df

    conditions = [
        (df['type_achat'] == 'Investissement locatif'),
        (df['budget_max'] < 150_000),
        (df['budget_max'].between(150_000, 300_000)),
        (df['budget_max'] > 300_000),
        (df['type_bien'] == 'Maison'),
    ]
    labels = [
        'Investisseur',
        'Primo-accédant (petit budget)',
        'Acheteur intermédiaire',
        'Acheteur premium',
        'Chercheur maison/villa',
    ]

    df['segment'] = 'Non classifié'
    for cond, label in zip(conditions, labels):
        df.loc[cond & (df['segment'] == 'Non classifié'), 'segment'] = label

    return df


def generate_report(df, output_file="acheteur/data/rapport_acheteurs.csv"):
    """Génère un rapport consolidé."""
    if df.empty:
        print("Aucune donnée à analyser.")
        return

    for col in ['budget_max', 'surface_min', 'nb_pieces']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = segment_acheteurs(df)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nOK Rapport sauvegarde : {output_file}")

    print("\n=== Statistiques acheteurs Toulon ===")
    print(f"Total profils : {len(df)}")
    print(f"\nType de bien recherche :\n{df['type_bien'].value_counts()}")
    print(f"\nType d'achat :\n{df['type_achat'].value_counts()}")
    print(f"\nSegments :\n{df['segment'].value_counts()}")
    if df['budget_max'].notna().any():
        print(f"\nBudget moyen : {df['budget_max'].mean():,.0f} EUR")
        print(f"Budget median : {df['budget_max'].median():,.0f} EUR")
    if df['surface_min'].notna().any():
        print(f"\nSurface moyenne souhaitee : {df['surface_min'].mean():.0f} m2")

    print(f"\nQuartiers les plus demandes :")
    quartier_counts = {}
    for val in df['quartier_souhaite'].dropna():
        for q in val.split(', '):
            q = q.strip()
            if q and q != 'Non precise':
                quartier_counts[q] = quartier_counts.get(q, 0) + 1
    for q, count in sorted(quartier_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {q}: {count}")

    print(f"\nCriteres les plus demandes :")
    critere_counts = {}
    for val in df['criteres'].dropna():
        for c in val.split(', '):
            c = c.strip()
            if c:
                critere_counts[c] = critere_counts.get(c, 0) + 1
    for c, count in sorted(critere_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {c}: {count}")


if __name__ == "__main__":
    print("=== Consolidation des profils acheteurs ===\n")
    df = load_all("acheteur/data")
    generate_report(df)
