"""
Migration de la base PostgreSQL Railway
Ajoute les 18 nouvelles colonnes pour le tracking prix
"""

import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("[SKIP] DATABASE_URL not found - Running locally (migration not needed)")
    exit(0)

def migrate_database():
    """Ajoute les colonnes manquantes pour le tracking"""

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("=" * 80)
    print("MIGRATION BASE DE DONNEES RAILWAY - AJOUT COLONNES TRACKING")
    print("=" * 80)
    print()

    migrations = [
        # Prix tracking
        ("price_1h_after", "REAL", "Prix 1h apres alerte"),
        ("price_2h_after", "REAL", "Prix 2h apres alerte"),
        ("price_4h_after", "REAL", "Prix 4h apres alerte"),
        ("price_24h_after", "REAL", "Prix 24h apres alerte"),
        ("price_max_reached", "REAL", "Prix maximum atteint"),
        ("price_min_reached", "REAL", "Prix minimum atteint"),

        # Temps tracking
        ("time_to_tp1", "REAL", "Heures pour atteindre TP1"),
        ("time_to_tp2", "REAL", "Heures pour atteindre TP2"),
        ("time_to_tp3", "REAL", "Heures pour atteindre TP3"),
        ("time_to_sl", "REAL", "Heures pour atteindre SL"),

        # Résultats
        ("highest_tp_reached", "TEXT", "Plus haut TP atteint"),
        ("sl_hit", "INTEGER", "SL atteint (0/1)"),
        ("final_outcome", "TEXT", "Resultat final"),
        ("final_gain_percent", "REAL", "Gain final en %"),
        ("final_gain_usd", "REAL", "Gain final en USD"),
        ("is_closed", "INTEGER DEFAULT 0", "Alerte cloturee (0/1)"),
        ("closed_at", "TEXT", "Date de cloture"),

        # Metadata
        ("token_symbol", "TEXT", "Symbole du token"),
    ]

    print("[1/3] Verification des colonnes existantes...")

    # Verifier quelles colonnes existent deja
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'alerts'
    """)

    existing_columns = [row[0] for row in cursor.fetchall()]
    print(f"      OK {len(existing_columns)} colonnes existantes")
    print()

    print("[2/3] Ajout des colonnes manquantes...")

    added = 0
    skipped = 0
    errors = 0

    for column_name, column_type, description in migrations:
        if column_name in existing_columns:
            print(f"      SKIP {column_name} (deja existante)")
            skipped += 1
        else:
            try:
                sql = f"ALTER TABLE alerts ADD COLUMN {column_name} {column_type}"
                cursor.execute(sql)
                conn.commit()
                print(f"      OK   {column_name} - {description}")
                added += 1
            except Exception as e:
                print(f"      ERR  {column_name} - {e}")
                errors += 1

    print()

    print("[3/3] Verification finale...")

    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'alerts'
    """)

    final_columns = [row[0] for row in cursor.fetchall()]
    print(f"      OK {len(final_columns)} colonnes au total")
    print()

    print("=" * 80)
    print("MIGRATION TERMINEE")
    print("=" * 80)
    print()
    print(f"Colonnes ajoutees: {added}")
    print(f"Colonnes deja existantes: {skipped}")
    print(f"Erreurs: {errors}")
    print()

    if errors == 0:
        print("OK Migration reussie!")
        print()
        print("La base Railway est maintenant prete pour le price tracking.")
        print("Vous pouvez maintenant deployer le cron job.")
    else:
        print("(!!) Des erreurs sont survenues pendant la migration")

    conn.close()

if __name__ == '__main__':
    migrate_railway_db()
