"""
Script a executer SUR Railway pour exporter les alertes en JSON
A copier-coller dans Railway SSH
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = "/app/alerts_history.db"
OUTPUT_FILE = "/tmp/alerts_export.json"

print("Export des alertes en JSON...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Recuperer toutes les alertes
cursor.execute("""
    SELECT
        id, token_name, token_address, network,
        price_at_alert, score, base_score, momentum_bonus,
        confidence_score, volume_24h, volume_6h, volume_1h,
        liquidity, buys_24h, sells_24h, buy_ratio,
        total_txns, age_hours, created_at,
        volume_acceleration_1h_vs_6h, volume_acceleration_6h_vs_24h
    FROM alerts
    ORDER BY created_at ASC
""")

columns = [desc[0] for desc in cursor.description]
alerts = []

for row in cursor.fetchall():
    alert = dict(zip(columns, row))
    alerts.append(alert)

conn.close()

# Sauvegarder en JSON
with open(OUTPUT_FILE, 'w') as f:
    json.dump({
        'exported_at': datetime.now().isoformat(),
        'total_alerts': len(alerts),
        'alerts': alerts
    }, f)

print(f"OK - {len(alerts)} alertes exportees dans {OUTPUT_FILE}")
print(f"Telechargez avec: railway ssh -- cat {OUTPUT_FILE}")
