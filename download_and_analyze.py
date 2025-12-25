#!/usr/bin/env python3
"""
Script automatique pour télécharger la DB depuis Railway et lancer le backtest
"""
import subprocess
import os
import sys

print("=" * 80)
print("TÉLÉCHARGEMENT DB DEPUIS RAILWAY")
print("=" * 80)

# Étape 1: Exporter DB en SQL depuis Railway
print("\n1. Export SQL depuis Railway...")
print("   (Cela peut prendre 1-2 minutes...)")
try:
    # Utiliser railway run avec la commande complète
    result = subprocess.run(
        ["railway", "run", "sh", "-c", "sqlite3 /data/alerts_history.db .dump"],
        capture_output=True,
        text=True,
        timeout=300,
        shell=True
    )

    if result.returncode != 0:
        print(f"❌ Erreur export: {result.stderr}")
        print(f"   Output: {result.stdout[:200]}")
        sys.exit(1)

    # Sauvegarder le dump SQL
    if result.stdout and len(result.stdout) > 1000:  # Vérifier que c'est pas vide
        with open("db_dump.sql", "w", encoding="utf-8") as f:
            f.write(result.stdout)
        print(f"✅ Export SQL réussi ({len(result.stdout):,} caractères)")
    else:
        print(f"❌ Export vide ou trop petit: {len(result.stdout)} caractères")
        sys.exit(1)

except subprocess.TimeoutExpired:
    print("❌ Timeout (>5min) - DB trop grosse, essayez méthode manuelle")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Étape 2: Créer DB locale
print("\n2. Création DB locale...")
if os.path.exists("alerts_history_local.db"):
    os.remove("alerts_history_local.db")

result = subprocess.run(
    ["sqlite3", "alerts_history_local.db"],
    input=open("db_dump.sql", "r", encoding="utf-8").read(),
    text=True
)

if result.returncode == 0:
    print("✅ DB locale créée")
else:
    print("❌ Erreur création DB")
    sys.exit(1)

# Étape 3: Lancer backtest
print("\n3. Lancement backtest...")
print("=" * 80)

import backtest_network_comparison
backtest_network_comparison.DB_PATH = "alerts_history_local.db"
backtest_network_comparison.analyze_network_performance()

print("\n" + "=" * 80)
print("✅ ANALYSE TERMINÉE")
print("=" * 80)
