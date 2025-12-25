#!/usr/bin/env python3
"""
Export des données de la DB Railway vers CSV
À exécuter SUR Railway: railway run python export_to_csv.py
"""
import sqlite3
import csv
import sys
import os

DB_PATH = os.getenv("DB_PATH", "/data/alerts_history.db")

print("Connexion à la DB...", file=sys.stderr)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer toutes les alertes avec les données nécessaires pour le backtest
    cursor.execute("""
        SELECT
            id,
            network,
            token_name,
            token_address,
            score,
            entry_price,
            tp1_price,
            tp2_price,
            tp3_price,
            stop_loss_price,
            prix_max_atteint,
            created_at
        FROM alerts
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    print(f"Données récupérées: {len(rows)} alertes", file=sys.stderr)

    # Écrire en CSV sur stdout
    writer = csv.writer(sys.stdout)

    # Header
    writer.writerow([
        'id', 'network', 'token_name', 'token_address', 'score',
        'entry_price', 'tp1_price', 'tp2_price', 'tp3_price',
        'stop_loss_price', 'prix_max_atteint', 'created_at'
    ])

    # Données
    for row in rows:
        writer.writerow(row)

    conn.close()
    print("Export terminé!", file=sys.stderr)

except Exception as e:
    print(f"ERREUR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
