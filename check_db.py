import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/alerts_history.db')
cursor = conn.cursor()

# Total et dates
cursor.execute("SELECT COUNT(*) as total, MIN(created_at) as plus_ancienne, MAX(created_at) as plus_recente FROM alerts")
row = cursor.fetchone()
print(f"Total alertes: {row[0]}")
print(f"Plus ancienne: {row[1]}")
print(f"Plus récente: {row[2]}")

# Alertes des dernières 24h
cutoff_24h = (datetime.now() - timedelta(days=1)).isoformat()
cursor.execute("SELECT COUNT(*) FROM alerts WHERE created_at >= ?", [cutoff_24h])
print(f"\nAlertes dernières 24h: {cursor.fetchone()[0]}")

# Alertes des derniers 7 jours
cutoff_7d = (datetime.now() - timedelta(days=7)).isoformat()
cursor.execute("SELECT COUNT(*) FROM alerts WHERE created_at >= ?", [cutoff_7d])
print(f"Alertes derniers 7 jours: {cursor.fetchone()[0]}")

# Les 5 plus récentes avec leurs dates
cursor.execute("SELECT token_name, created_at, score FROM alerts ORDER BY created_at DESC LIMIT 5")
print("\n5 alertes les plus récentes:")
for row in cursor.fetchall():
    print(f"  - {row[0]} | {row[1]} | Score: {row[2]}")

conn.close()
