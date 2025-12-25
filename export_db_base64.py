#!/usr/bin/env python3
"""
Script à exécuter SUR Railway pour exporter la DB en base64
À déployer puis exécuter via: railway run python export_db_base64.py
"""
import base64
import sys
import os

DB_PATH = os.getenv("DB_PATH", "/data/alerts_history.db")

print("Lecture DB...", file=sys.stderr)
try:
    with open(DB_PATH, "rb") as f:
        db_content = f.read()

    print(f"DB lue: {len(db_content)} bytes", file=sys.stderr)

    # Encoder en base64
    encoded = base64.b64encode(db_content).decode('ascii')

    # Afficher SEULEMENT le base64 sur stdout (pour redirection)
    print(encoded)

except Exception as e:
    print(f"ERREUR: {e}", file=sys.stderr)
    sys.exit(1)
