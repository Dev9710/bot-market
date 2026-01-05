"""
Module principal pour lancer le scanner GeckoTerminal V3 en boucle continue.
Ce fichier ajoute la fonction main() manquante.
"""

import time
from geckoterminal_scanner_v3 import (
    scan_geckoterminal,
    security_checker,
    alert_tracker,
    SecurityChecker,
    AlertTracker,
    log,
)

# Initialiser les systèmes globaux
def init_systems():
    """Initialise les systèmes de sécurité et tracking."""
    global security_checker, alert_tracker

    if security_checker is None:
        security_checker = SecurityChecker()
        log("✅ SecurityChecker initialisé")

    if alert_tracker is None:
        alert_tracker = AlertTracker()
        log("✅ AlertTracker initialisé")


def main():
    """
    Fonction principale - Boucle de scan continue.
    """
    # Initialiser les systèmes
    init_systems()

    # Importer dans le module pour que les variables globales soient mises à jour
    import geckoterminal_scanner_v3 as scanner
    scanner.security_checker = security_checker
    scanner.alert_tracker = alert_tracker

    log("🚀 Démarrage du scanner GeckoTerminal V3...")
    log("🔄 Mode: Scan continu toutes les 2 minutes")
    log("⛓️ Réseaux surveillés: ETH, BSC, Base, Solana, Polygon, Avalanche")
    log("")

    scan_count = 0

    try:
        while True:
            scan_count += 1
            log(f"\n{'='*80}")
            log(f"🔍 SCAN #{scan_count}")
            log(f"{'='*80}\n")

            try:
                # Lancer un scan
                scan_geckoterminal()

            except Exception as e:
                log(f"❌ Erreur durant le scan: {e}")
                import traceback
                log(f"Traceback: {traceback.format_exc()}")

            # Attendre 2 minutes avant le prochain scan
            log(f"\n⏳ Attente de 120 secondes avant le prochain scan...")
            time.sleep(120)

    except KeyboardInterrupt:
        log("\n\n⏹️ Arrêt du scanner demandé par l'utilisateur")
        log("👋 Scanner arrêté proprement")


if __name__ == "__main__":
    main()
