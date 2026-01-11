"""
Script de verification rapide du schema Railway
Verifie si les 18 nouvelles colonnes de tracking sont presentes
"""

import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL non trouve - Doit etre execute sur Railway")
    print("\nPour executer:")
    print("  railway run python check_railway_schema.py")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("=" * 80)
    print("VERIFICATION SCHEMA RAILWAY")
    print("=" * 80)
    print()

    # Recuperer toutes les colonnes de la table alerts
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'alerts'
        ORDER BY ordinal_position
    """)

    columns = [row[0] for row in cursor.fetchall()]

    print(f"Total colonnes trouvees: {len(columns)}")
    print()

    # Colonnes de tracking a verifier
    tracking_columns = [
        'price_1h_after',
        'price_2h_after',
        'price_4h_after',
        'price_24h_after',
        'price_max_reached',
        'price_min_reached',
        'time_to_tp1',
        'time_to_tp2',
        'time_to_tp3',
        'time_to_sl',
        'highest_tp_reached',
        'sl_hit',
        'final_outcome',
        'final_gain_percent',
        'final_gain_usd',
        'is_closed',
        'closed_at',
        'token_symbol'
    ]

    print("Verification des colonnes de tracking:")
    print("-" * 80)

    missing = []
    present = []

    for col in tracking_columns:
        if col in columns:
            print(f"  OK   {col}")
            present.append(col)
        else:
            print(f"  (!!) MANQUANT: {col}")
            missing.append(col)

    print()
    print("=" * 80)
    print("RESULTAT")
    print("=" * 80)
    print()
    print(f"Colonnes presentes: {len(present)}/18")
    print(f"Colonnes manquantes: {len(missing)}/18")
    print()

    if len(missing) == 0:
        print("OK Toutes les colonnes de tracking sont presentes!")
        print("Le price tracker peut fonctionner.")
    else:
        print("(!!) Des colonnes manquent - La migration doit etre executee")
        print()
        print("Colonnes manquantes:")
        for col in missing:
            print(f"  - {col}")
        print()
        print("Action requise:")
        print("  railway run python migrate_railway_db.py")

    conn.close()

except Exception as e:
    print(f"ERREUR: {e}")
    exit(1)
