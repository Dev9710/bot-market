#!/usr/bin/env python3
"""
Script SIMPLIFIÉ pour télécharger la DB depuis Railway via base64
"""
import subprocess
import base64
import sys

print("=" * 80)
print("TÉLÉCHARGEMENT DB DEPUIS RAILWAY (Méthode Base64)")
print("=" * 80)

print("\n📥 Téléchargement en cours (peut prendre 2-3 minutes)...")
print("   Taille attendue: ~50-100 MB")

try:
    # Exporter la DB en base64 depuis Railway
    result = subprocess.run(
        ["railway", "run", "sh", "-c", "base64 /data/alerts_history.db"],
        capture_output=True,
        text=True,
        timeout=300,
        shell=True
    )

    if result.returncode != 0:
        print(f"\n❌ Erreur: {result.stderr}")
        sys.exit(1)

    if not result.stdout or len(result.stdout) < 1000:
        print(f"\n❌ Données reçues trop petites: {len(result.stdout)} caractères")
        sys.exit(1)

    print(f"✅ Données reçues: {len(result.stdout):,} caractères base64")

    # Décoder base64
    print("\n🔓 Décodage base64...")
    try:
        db_bytes = base64.b64decode(result.stdout)
        print(f"✅ Décodé: {len(db_bytes):,} bytes")
    except Exception as e:
        print(f"❌ Erreur décodage: {e}")
        sys.exit(1)

    # Sauvegarder
    print("\n💾 Sauvegarde dans alerts_history_railway.db...")
    with open("alerts_history_railway.db", "wb") as f:
        f.write(db_bytes)

    print(f"✅ DB sauvegardée: alerts_history_railway.db ({len(db_bytes):,} bytes)")

    # Lancer le backtest
    print("\n" + "=" * 80)
    print("LANCEMENT DU BACKTEST")
    print("=" * 80 + "\n")

    import backtest_network_comparison
    backtest_network_comparison.DB_PATH = "alerts_history_railway.db"
    backtest_network_comparison.analyze_network_performance()

except subprocess.TimeoutExpired:
    print("\n❌ Timeout après 5 minutes")
    print("   La DB est peut-être trop grosse pour cette méthode")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n\n❌ Annulé par l'utilisateur")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ TERMINÉ!")
print("=" * 80)
