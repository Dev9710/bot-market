"""
Migration de la base SQLite Railway
Ajoute les colonnes manquantes pour le tracking prix
Compatible Railway (SQLite sur /data/) et local
"""

import os
import sqlite3
from datetime import datetime

# Determiner le chemin de la base SQLite
if os.path.exists('/data/alerts_history.db'):
    # Railway: volume monte a /data/
    DB_PATH = '/data/alerts_history.db'
    print(f"[INFO] Mode Railway - SQLite: {DB_PATH}")
else:
    # Local development
    DB_PATH = os.path.join(os.path.dirname(__file__), 'alerts_history.db')
    print(f"[INFO] Mode Local - SQLite: {DB_PATH}")

def migrate_database():
    """Ajoute les colonnes manquantes pour le tracking"""

    if not os.path.exists(DB_PATH):
        print(f"[SKIP] Database not found: {DB_PATH}")
        print("[INFO] Database will be created when scanner starts")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("MIGRATION BASE DE DONNEES SQLITE - AJOUT COLONNES TRACKING")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")
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

        # Resultats
        ("highest_tp_reached", "TEXT", "Plus haut TP atteint"),
        ("sl_hit", "INTEGER", "SL atteint (0/1)"),
        ("final_outcome", "TEXT", "Resultat final"),
        ("final_gain_percent", "REAL", "Gain final en %"),
        ("final_gain_usd", "REAL", "Gain final en USD"),
        ("is_closed", "INTEGER DEFAULT 0", "Alerte cloturee (0/1)"),
        ("closed_at", "TEXT", "Date de cloture"),

        # Metadata additionnelle
        ("token_symbol", "TEXT", "Symbole du token"),
        ("tier", "TEXT", "Tier de l'alerte"),
        ("velocite_pump", "REAL", "Velocite du pump"),
        ("type_pump", "TEXT", "Type de pump"),
        ("volume_acceleration_1h_vs_6h", "REAL", "Acceleration volume 1h vs 6h"),
        ("volume_acceleration_6h_vs_24h", "REAL", "Acceleration volume 6h vs 24h"),
    ]

    print("[1/3] Verification des colonnes existantes...")

    # Verifier quelles colonnes existent deja
    cursor.execute("PRAGMA table_info(alerts)")
    existing_columns = [row[1] for row in cursor.fetchall()]
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
                # SQLite utilise ADD COLUMN sans parentheses
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

    cursor.execute("PRAGMA table_info(alerts)")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"      OK {len(final_columns)} colonnes au total")
    print()

    # Afficher les colonnes ajoutees
    print("Colonnes de tracking disponibles:")
    tracking_cols = ['price_1h_after', 'price_2h_after', 'price_4h_after', 'price_24h_after',
                     'price_max_reached', 'price_min_reached', 'highest_tp_reached',
                     'sl_hit', 'is_closed', 'final_outcome']
    for col in tracking_cols:
        status = "OK" if col in final_columns else "MISSING"
        print(f"      [{status}] {col}")
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
        print("La base SQLite est maintenant prete pour le price tracking.")
    else:
        print("(!!) Des erreurs sont survenues pendant la migration")

    conn.close()

if __name__ == '__main__':
    migrate_database()
