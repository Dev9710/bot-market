#!/usr/bin/env python3
"""
Export de la base PostgreSQL Railway vers JSON.
Usage:
    1. railway shell
    2. pip install psycopg2-binary
    3. python export_railway_db.py
"""

import os
import sys
import json
from datetime import datetime

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("ERREUR: DATABASE_URL non trouve")
    print("Vous devez etre dans 'railway shell'")
    sys.exit(1)

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Installation psycopg2...")
    os.system("pip install psycopg2-binary")
    import psycopg2
    import psycopg2.extras

print("Connexion a PostgreSQL Railway...")
conn = psycopg2.connect(database_url)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Compter les alertes
cursor.execute("SELECT COUNT(*) as total FROM alerts")
total = cursor.fetchone()['total']
print(f"Total alertes: {total}")

# Exporter
print("Export en cours...")
cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
alerts = cursor.fetchall()

# Convertir dates en string
for alert in alerts:
    if alert.get('created_at'):
        alert['created_at'] = alert['created_at'].isoformat()

# Sauvegarder
filename = f"railway_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump({
        'export_date': datetime.now().isoformat(),
        'total': total,
        'alerts': alerts
    }, f, indent=2, ensure_ascii=False)

print(f"Export termine: {filename}")
print(f"Alertes exportees: {total}")

conn.close()
