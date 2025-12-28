#!/usr/bin/env python3
"""
Importe un export JSON Railway vers une base SQLite locale pour backtest.

Usage:
    python import_json_to_sqlite.py alerts_railway_export.json
"""

import sys
import json
import sqlite3
from pathlib import Path

def import_json_to_sqlite(json_file: str, db_file: str = "railway_backtest.db"):
    """Importe JSON vers SQLite."""

    print(f"\n{'='*70}")
    print(f"   IMPORT JSON → SQLite POUR BACKTEST")
    print(f"{'='*70}\n")

    # Charger JSON
    print(f"📖 Lecture de {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    alerts = data.get('alerts', [])
    total = data.get('total_alerts', len(alerts))

    print(f"✅ {total} alertes trouvées")

    # Créer base SQLite
    print(f"\n💾 Création de {db_file}...")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Créer table alerts (structure compatible avec alert_tracker.py)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_name TEXT NOT NULL,
            token_address TEXT NOT NULL,
            network TEXT NOT NULL,
            price_at_alert REAL NOT NULL,
            score INTEGER NOT NULL,
            base_score INTEGER,
            momentum_bonus INTEGER,
            confidence_score INTEGER,
            volume_24h REAL,
            volume_6h REAL,
            volume_1h REAL,
            liquidity REAL NOT NULL,
            buys_24h INTEGER,
            sells_24h INTEGER,
            buy_ratio REAL,
            total_txns INTEGER,
            age_hours REAL,
            entry_price REAL NOT NULL,
            stop_loss_price REAL NOT NULL,
            stop_loss_percent REAL NOT NULL,
            tp1_price REAL NOT NULL,
            tp1_percent REAL NOT NULL,
            tp2_price REAL NOT NULL,
            tp2_percent REAL NOT NULL,
            tp3_price REAL NOT NULL,
            tp3_percent REAL NOT NULL,
            alert_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            volume_acceleration_1h_vs_6h REAL,
            volume_acceleration_6h_vs_24h REAL,
            velocite_pump REAL,
            type_pump TEXT,
            decision_tp_tracking TEXT,
            temps_depuis_alerte_precedente INTEGER,
            is_alerte_suivante INTEGER DEFAULT 0
        )
    """)

    # Créer table alert_analysis (pour tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            current_price REAL,
            price_change_percent REAL,
            roi_at_1h REAL,
            roi_at_4h REAL,
            roi_at_24h REAL,
            max_price_reached REAL,
            max_roi_percent REAL,
            tp1_was_hit BOOLEAN DEFAULT 0,
            tp2_was_hit BOOLEAN DEFAULT 0,
            tp3_was_hit BOOLEAN DEFAULT 0,
            sl_was_hit BOOLEAN DEFAULT 0,
            was_coherent BOOLEAN DEFAULT 0,
            FOREIGN KEY (alert_id) REFERENCES alerts(id)
        )
    """)

    print(f"✅ Tables créées")

    # Insérer les alertes
    print(f"\n📥 Insertion des alertes...")

    inserted = 0
    skipped = 0

    for alert in alerts:
        try:
            cursor.execute("""
                INSERT INTO alerts (
                    token_name, token_address, network, price_at_alert,
                    score, base_score, momentum_bonus, confidence_score,
                    volume_24h, volume_6h, volume_1h, liquidity,
                    buys_24h, sells_24h, buy_ratio, total_txns, age_hours,
                    entry_price, stop_loss_price, stop_loss_percent,
                    tp1_price, tp1_percent, tp2_price, tp2_percent,
                    tp3_price, tp3_percent, alert_message, created_at,
                    volume_acceleration_1h_vs_6h, volume_acceleration_6h_vs_24h,
                    velocite_pump, type_pump, decision_tp_tracking,
                    temps_depuis_alerte_precedente, is_alerte_suivante
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                alert.get('is_alerte_suivante', 0)
            ))
            inserted += 1

            if inserted % 10 == 0:
                print(f"   Importées: {inserted}/{total}", end='\r')

        except Exception as e:
            skipped += 1
            print(f"\n⚠️  Erreur alerte #{alert.get('id', '?')}: {e}")

    conn.commit()

    print(f"\n\n{'='*70}")
    print(f"✅ IMPORT TERMINÉ!")
    print(f"{'='*70}")
    print(f"📊 Statistiques:")
    print(f"   - Alertes importées: {inserted}")
    print(f"   - Alertes ignorées: {skipped}")
    print(f"   - Base de données: {db_file}")

    # Stats par réseau
    cursor.execute("SELECT network, COUNT(*) FROM alerts GROUP BY network ORDER BY COUNT(*) DESC")
    print(f"\n📈 Répartition par réseau:")
    for network, count in cursor.fetchall():
        print(f"   {network}: {count} alertes")

    # Stats par score
    cursor.execute("""
        SELECT
            CASE
                WHEN score >= 80 THEN '80+'
                WHEN score >= 70 THEN '70-79'
                WHEN score >= 60 THEN '60-69'
                ELSE '<60'
            END as score_range,
            COUNT(*)
        FROM alerts
        GROUP BY score_range
        ORDER BY score_range DESC
    """)
    print(f"\n🎯 Répartition par score:")
    for score_range, count in cursor.fetchall():
        print(f"   {score_range}: {count} alertes")

    print(f"\n💡 Prochaines étapes:")
    print(f"1. Lancer un backtest:")
    print(f"   python ultimate_simple_analyzer.py --db {db_file}")
    print(f"\n2. Ou analyser avec alert_tracker:")
    print(f"   from alert_tracker import AlertTracker")
    print(f"   tracker = AlertTracker(db_path='{db_file}')")
    print(f"   tracker.print_stats()")

    print(f"\n{'='*70}\n")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_json_to_sqlite.py alerts_railway_export.json")
        sys.exit(1)

    json_file = sys.argv[1]

    if not Path(json_file).exists():
        print(f"❌ Fichier non trouvé: {json_file}")
        sys.exit(1)

    import_json_to_sqlite(json_file)
