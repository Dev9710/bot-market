"""
Vérifier si les tokens performants du 20 déc ont été détectés
À exécuter avec: railway run python check_tokens.py
"""
import sqlite3
import os

db_path = os.getenv("DB_PATH", "/data/alerts_history.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tokens à rechercher
tokens_recherches = ['snowball', 'testicle', 'water', 'fireball']

print("=== Recherche tokens performants du 20 dec ===\n")

for token_name in tokens_recherches:
    cursor.execute("""
        SELECT id, token_name, network, score, price_at_alert, created_at
        FROM alerts
        WHERE LOWER(token_name) LIKE ?
        ORDER BY created_at DESC
    """, (f'%{token_name}%',))

    results = cursor.fetchall()

    if results:
        print(f"✅ {token_name.upper()} - {len(results)} alerte(s) trouvée(s):")
        for alert_id, name, network, score, price, created in results:
            print(f"   ID {alert_id} - {name} ({network})")
            print(f"   Score: {score} - Prix: ${price}")
            print(f"   Date: {created}\n")
    else:
        print(f"❌ {token_name.upper()} - Non détecté\n")

# Statistiques générales
cursor.execute("SELECT COUNT(*) FROM alerts WHERE created_at >= '2025-12-20'")
count_20dec = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM alerts WHERE network = 'arbitrum'")
count_arb = cursor.fetchone()[0]

print(f"\n📊 Stats:")
print(f"   Alertes depuis 20 déc: {count_20dec}")
print(f"   Alertes Arbitrum (total): {count_arb}")

conn.close()
