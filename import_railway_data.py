#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Railway JSON export into local SQLite database
"""
import json
import sqlite3
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

JSON_FILE = "alerts_railway_export_utf8.json"
DB_FILE = "alerts_history.db"

print("📥 Import des données Railway vers SQLite local\n")
print(f"Fichier source: {JSON_FILE}")
print(f"Database cible: {DB_FILE}\n")

# Read JSON
print("1️⃣  Lecture du fichier JSON...")
with open(JSON_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

total_alerts = data.get('total_alerts') or data.get('total', 0)
alerts = data.get('alerts', [])

print(f"   ✅ {len(alerts)} alertes chargées (total: {total_alerts})\n")

# Connect to SQLite
print("2️⃣  Connexion à la base SQLite...")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Drop existing table and create new
cursor.execute("DROP TABLE IF EXISTS alerts")
cursor.execute("""
    CREATE TABLE alerts (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        token_name TEXT,
        token_address TEXT,
        network TEXT,
        price_at_alert REAL,
        score INTEGER,
        base_score INTEGER,
        momentum_bonus INTEGER,
        confidence_score INTEGER,
        volume_24h REAL,
        volume_6h REAL,
        volume_1h REAL,
        liquidity REAL,
        buys_24h INTEGER,
        sells_24h INTEGER,
        buy_ratio REAL,
        total_txns INTEGER,
        age_hours REAL,
        entry_price REAL,
        stop_loss_price REAL,
        stop_loss_percent REAL,
        tp1_price REAL,
        tp1_percent REAL,
        tp2_price REAL,
        tp2_percent REAL,
        tp3_price REAL,
        tp3_percent REAL,
        alert_message TEXT,
        created_at TEXT,
        volume_acceleration_1h_vs_6h REAL,
        volume_acceleration_6h_vs_24h REAL,
        velocite_pump REAL,
        type_pump TEXT,
        decision_tp_tracking TEXT,
        temps_depuis_alerte_precedente REAL,
        is_alerte_suivante INTEGER,
        version TEXT,
        pool_address TEXT,
        tier TEXT
    )
""")

print("   ✅ Table créée\n")

# Insert alerts
print("3️⃣  Import des alertes...")
imported = 0
errors = 0

for alert in alerts:
    try:
        cursor.execute("""
            INSERT INTO alerts (
                id, timestamp, token_name, token_address, network,
                price_at_alert, score, base_score, momentum_bonus, confidence_score,
                volume_24h, volume_6h, volume_1h, liquidity,
                buys_24h, sells_24h, buy_ratio, total_txns, age_hours,
                entry_price, stop_loss_price, stop_loss_percent,
                tp1_price, tp1_percent, tp2_price, tp2_percent, tp3_price, tp3_percent,
                alert_message, created_at,
                volume_acceleration_1h_vs_6h, volume_acceleration_6h_vs_24h,
                velocite_pump, type_pump, decision_tp_tracking,
                temps_depuis_alerte_precedente, is_alerte_suivante,
                version, pool_address, tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.get('id'),
            alert.get('timestamp'),
            alert.get('token_name'),
            alert.get('token_address'),
            alert.get('network'),
            alert.get('price_at_alert'),
            alert.get('score'),
            alert.get('base_score'),
            alert.get('momentum_bonus'),
            alert.get('confidence_score'),
            alert.get('volume_24h'),
            alert.get('volume_6h'),
            alert.get('volume_1h'),
            alert.get('liquidity'),
            alert.get('buys_24h'),
            alert.get('sells_24h'),
            alert.get('buy_ratio'),
            alert.get('total_txns'),
            alert.get('age_hours'),
            alert.get('entry_price'),
            alert.get('stop_loss_price'),
            alert.get('stop_loss_percent'),
            alert.get('tp1_price'),
            alert.get('tp1_percent'),
            alert.get('tp2_price'),
            alert.get('tp2_percent'),
            alert.get('tp3_price'),
            alert.get('tp3_percent'),
            alert.get('alert_message'),
            alert.get('created_at'),
            alert.get('volume_acceleration_1h_vs_6h'),
            alert.get('volume_acceleration_6h_vs_24h'),
            alert.get('velocite_pump'),
            alert.get('type_pump'),
            alert.get('decision_tp_tracking'),
            alert.get('temps_depuis_alerte_precedente'),
            alert.get('is_alerte_suivante'),
            alert.get('version'),
            alert.get('pool_address'),
            alert.get('tier')
        ))
        imported += 1

        if imported % 500 == 0:
            print(f"   ... {imported} alertes importées")

    except Exception as e:
        errors += 1
        if errors < 10:  # Show first 10 errors
            print(f"   ⚠️  Erreur alerte {alert.get('id')}: {e}")

conn.commit()
print(f"\n   ✅ Import terminé: {imported} alertes importées, {errors} erreurs\n")

# Stats
cursor.execute("SELECT COUNT(*) FROM alerts")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT network) FROM alerts")
networks = cursor.fetchone()[0]

cursor.execute("SELECT network, COUNT(*) FROM alerts GROUP BY network ORDER BY COUNT(*) DESC")
by_network = cursor.fetchall()

print("📊 STATISTIQUES:\n")
print(f"   Total alertes: {total}")
print(f"   Réseaux: {networks}\n")
print("   Par réseau:")
for net, count in by_network:
    print(f"     • {net:15}: {count:>5} alertes")

conn.close()

print("\n✅ Import terminé! Vous pouvez maintenant lancer les analyses:\n")
print("   python analyze_all_tokens.py")
print("   python analyze_winners.py\n")
