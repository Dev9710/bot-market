"""
Test de vérification du schéma DB avec colonnes RÈGLE 5
"""
import sqlite3
import os

DB_PATH = "alerts.db"

def test_schema():
    """Vérifie que toutes les colonnes RÈGLE 5 existent."""

    # Créer ou ouvrir la DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Lister les colonnes de la table alerts
    cursor.execute("PRAGMA table_info(alerts)")
    columns = cursor.fetchall()

    print("=" * 80)
    print("VÉRIFICATION SCHÉMA DB - RÈGLE 5")
    print("=" * 80)

    # Colonnes attendues pour RÈGLE 5
    expected_columns = [
        'velocite_pump',
        'type_pump',
        'decision_tp_tracking',
        'temps_depuis_alerte_precedente',
        'is_alerte_suivante'
    ]

    # Colonnes existantes
    existing_columns = [col[1] for col in columns]

    print(f"\n📊 Nombre total de colonnes: {len(existing_columns)}")
    print(f"\n🔍 Vérification colonnes RÈGLE 5:")

    all_ok = True
    for col in expected_columns:
        if col in existing_columns:
            # Trouver le type
            col_info = next((c for c in columns if c[1] == col), None)
            col_type = col_info[2] if col_info else "UNKNOWN"
            default = col_info[4] if col_info else "UNKNOWN"
            print(f"   ✅ {col:40s} | Type: {col_type:10s} | Default: {default}")
        else:
            print(f"   ❌ {col:40s} | MANQUANTE")
            all_ok = False

    print("\n" + "=" * 80)
    if all_ok:
        print("✅ TOUTES LES COLONNES RÈGLE 5 SONT PRÉSENTES")
    else:
        print("❌ CERTAINES COLONNES RÈGLE 5 SONT MANQUANTES")
        print("\n💡 Solution: Lancer alert_tracker.py pour créer les colonnes manquantes")
    print("=" * 80)

    # Afficher toutes les colonnes pour référence
    print("\n📋 Liste complète des colonnes:")
    for i, col in enumerate(columns, 1):
        print(f"   {i:2d}. {col[1]:40s} | Type: {col[2]:10s}")

    conn.close()

    return all_ok

if __name__ == "__main__":
    # Vérifier si la DB existe
    if not os.path.exists(DB_PATH):
        print(f"⚠️ Base de données '{DB_PATH}' introuvable")
        print("💡 La DB sera créée au premier lancement du scanner")
    else:
        test_schema()
