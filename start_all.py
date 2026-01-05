"""
Script de démarrage combiné pour Railway
Lance le scanner V3 ET l'API Dashboard en parallèle dans des threads séparés
"""

import subprocess
import threading
import time
import sys
import signal

def run_scanner():
    """Lance le scanner V3"""
    print("🔍 Démarrage du Scanner V3...")
    subprocess.run([sys.executable, "geckoterminal_scanner_v3_main.py"])

def run_api():
    """Lance l'API Dashboard avec Gunicorn"""
    import os
    port = os.getenv('PORT', '5000')
    print(f"📊 Démarrage de l'API Dashboard sur port {port}...")
    subprocess.run([
        "gunicorn",
        "--bind", f"0.0.0.0:{port}",
        "--workers", "2",
        "--timeout", "120",
        "--access-logfile", "-",
        "wsgi:app"
    ])

def signal_handler(sig, frame):
    """Gestion de l'arrêt propre"""
    print("\n🛑 Arrêt des services...")
    sys.exit(0)

if __name__ == "__main__":
    # Capturer SIGTERM pour arrêt propre
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("🚀 Démarrage du scanner V3 + Dashboard API")

    # Lancer les deux processus dans des threads séparés
    api_thread = threading.Thread(target=run_api, daemon=True)
    scanner_thread = threading.Thread(target=run_scanner, daemon=True)

    api_thread.start()
    time.sleep(3)  # Attendre que l'API démarre
    scanner_thread.start()

    # Attendre indéfiniment
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé...")
        sys.exit(0)
