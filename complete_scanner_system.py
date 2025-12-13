# -*- coding: utf-8 -*-
"""
Système de Scan Complet avec Sécurité et Tracking
Combine:
- Scanner GeckoTerminal
- Vérification de sécurité (Honeypot + LP Lock + Contract Safety)
- Sauvegarde en base de données
- Tracking automatique des performances
"""

import time
from typing import Dict, List

# Import des modules (qui gèrent déjà l'encodage)
from security_checker import SecurityChecker
from alert_tracker import AlertTracker

class CompleteScanner:
    """
    Scanner complet avec toutes les protections de sécurité.
    """

    def __init__(self, min_security_score=50):
        """
        Initialise le scanner complet.

        Args:
            min_security_score: Score minimum de sécurité pour envoyer une alerte (défaut: 50)
        """
        print("="*80)
        print("🚀 INITIALISATION DU SYSTÈME COMPLET")
        print("="*80)

        # Initialiser les composants
        self.security_checker = SecurityChecker()
        self.alert_tracker = AlertTracker()
        self.min_security_score = min_security_score

        # Statistiques
        self.tokens_scanned = 0
        self.tokens_rejected = 0
        self.tokens_accepted = 0
        self.rejection_reasons = {}

        print(f"✅ Système initialisé")
        print(f"⚙️ Score minimum de sécurité: {min_security_score}/100")
        print("="*80 + "\n")

    def process_token(self, pool_data: Dict) -> bool:
        """
        Traite un token détecté par le scanner.

        Args:
            pool_data: Dictionnaire avec les données du pool/token

        Returns:
            True si l'alerte a été envoyée, False si rejetée
        """
        self.tokens_scanned += 1

        token_name = pool_data.get('name', 'UNKNOWN')
        token_address = pool_data['address']
        network = pool_data['network']
        price = pool_data.get('price', 0)

        print(f"\n{'='*80}")
        print(f"🔍 ANALYSE TOKEN #{self.tokens_scanned}: {token_name}")
        print(f"{'='*80}")
        print(f"📍 Address: {token_address}")
        print(f"🌐 Network: {network}")
        print(f"💰 Prix: ${price}")
        print(f"📊 Score opportunité: {pool_data.get('score', 'N/A')}")
        print()

        # ==========================================
        # ÉTAPE 1: VÉRIFICATION DE SÉCURITÉ
        # ==========================================
        print("🔒 [1/3] Vérification de sécurité...")

        security_result = self.security_checker.check_token_security(
            token_address,
            network
        )

        # Afficher les résultats de sécurité
        print(f"   Honeypot: {'❌ DÉTECTÉ' if security_result['checks']['honeypot']['is_honeypot'] else '✅ Safe'}")
        print(f"   LP Lock: {'✅ Lockée' if security_result['checks']['lp_lock']['is_locked'] else '❌ Non lockée'}")
        print(f"   Ownership: {'✅ Renoncée' if security_result['checks']['contract'].get('is_renounced', False) else '⚠️ Non renoncée'}")
        print(f"   Score sécurité: {security_result['security_score']}/100")
        print(f"   Niveau risque: {security_result['risk_level']}")

        # Décision: Envoyer l'alerte?
        should_send, reason = self.security_checker.should_send_alert(
            security_result,
            min_security_score=self.min_security_score
        )

        if not should_send:
            print(f"\n⛔ TOKEN REJETÉ: {reason}")
            print(f"{'='*80}\n")

            self.tokens_rejected += 1
            # Compter les raisons de rejet
            self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1

            return False

        print(f"\n✅ Sécurité validée: {reason}")

        # ==========================================
        # ÉTAPE 2: CALCUL DES NIVEAUX DE PRIX
        # ==========================================
        print(f"\n💹 [2/3] Calcul des niveaux de prix...")

        entry_price = price
        stop_loss_price = price * 0.90  # -10%
        tp1_price = price * 1.05  # +5%
        tp2_price = price * 1.10  # +10%
        tp3_price = price * 1.15  # +15%

        print(f"   🎯 Entrée: ${entry_price}")
        print(f"   ⛔ Stop Loss: ${stop_loss_price} (-10%)")
        print(f"   🎯 TP1: ${tp1_price} (+5%)")
        print(f"   🎯 TP2: ${tp2_price} (+10%)")
        print(f"   🎯 TP3: ${tp3_price} (+15%)")

        # ==========================================
        # ÉTAPE 3: SAUVEGARDE EN BASE DE DONNÉES
        # ==========================================
        print(f"\n💾 [3/3] Sauvegarde en base de données...")

        alert_data = {
            'token_name': token_name,
            'token_address': token_address,
            'network': network,
            'price_at_alert': price,
            'score': pool_data.get('score', 0),
            'base_score': pool_data.get('base_score', 0),
            'momentum_bonus': pool_data.get('momentum_bonus', 0),
            'confidence_score': security_result['security_score'],
            'volume_24h': pool_data.get('volume_24h', 0),
            'volume_6h': pool_data.get('volume_6h', 0),
            'volume_1h': pool_data.get('volume_1h', 0),
            'liquidity': pool_data.get('liquidity', 0),
            'buys_24h': pool_data.get('buys_24h', 0),
            'sells_24h': pool_data.get('sells_24h', 0),
            'buy_ratio': pool_data.get('buy_ratio', 0),
            'total_txns': pool_data.get('total_txns', 0),
            'age_hours': pool_data.get('age_hours', 0),
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'stop_loss_percent': -10,
            'tp1_price': tp1_price,
            'tp1_percent': 5,
            'tp2_price': tp2_price,
            'tp2_percent': 10,
            'tp3_price': tp3_price,
            'tp3_percent': 15,
            'alert_message': self.format_alert_message(pool_data, security_result, entry_price, stop_loss_price, tp1_price, tp2_price, tp3_price)
        }

        # Sauvegarder (lance aussi le tracking automatique)
        alert_id = self.alert_tracker.save_alert(alert_data)

        if alert_id > 0:
            print(f"   ✅ Alerte sauvegardée (ID: {alert_id})")
            print(f"   📊 Tracking automatique démarré (15min, 1h, 4h, 24h)")
            self.tokens_accepted += 1
        else:
            print(f"   ⚠️ Échec sauvegarde (probablement déjà existant)")

        print(f"\n{'='*80}")
        print(f"✅ TOKEN ACCEPTÉ ET ENREGISTRÉ")
        print(f"{'='*80}\n")

        # TODO: Ici, envoyer l'alerte Telegram
        # send_telegram_alert(alert_data)

        return True

    def format_alert_message(self, pool_data: Dict, security_result: Dict,
                            entry: float, sl: float, tp1: float, tp2: float, tp3: float) -> str:
        """
        Formate le message d'alerte complet.

        Args:
            pool_data: Données du pool
            security_result: Résultats de sécurité
            entry, sl, tp1, tp2, tp3: Prix calculés

        Returns:
            Message formaté pour Telegram
        """
        token_name = pool_data.get('name', 'UNKNOWN')
        network = pool_data['network'].upper()
        score = pool_data.get('score', 0)

        message = f"""
🔥 NOUVEAU TOKEN DÉTECTÉ

🪙 {token_name}
🌐 Réseau: {network}
📊 Score: {score}/100

💰 PRIX ET NIVEAUX:
   🎯 Entrée: ${entry}
   ⛔ Stop Loss: ${sl} (-10%)
   🎯 TP1: ${tp1} (+5%)
   🎯 TP2: ${tp2} (+10%)
   🎯 TP3: ${tp3} (+15%)

{self.security_checker.format_security_warning(security_result)}

📊 MÉTRIQUES:
   💧 Liquidité: ${pool_data.get('liquidity', 0):,.0f}
   📈 Volume 24h: ${pool_data.get('volume_24h', 0):,.0f}
   🔄 Txns 24h: {pool_data.get('total_txns', 0)}
   📊 Buy Ratio: {pool_data.get('buy_ratio', 0):.2f}

⚠️ RISQUE: {security_result['risk_level']}

🔗 DexScreener: https://dexscreener.com/{network}/{pool_data['address']}
"""
        return message.strip()

    def print_statistics(self):
        """Affiche les statistiques du scanner."""
        print("\n" + "="*80)
        print("📊 STATISTIQUES DE SCAN")
        print("="*80)
        print(f"Tokens scannés: {self.tokens_scanned}")
        print(f"Tokens acceptés: {self.tokens_accepted} ({self.tokens_accepted/self.tokens_scanned*100 if self.tokens_scanned > 0 else 0:.1f}%)")
        print(f"Tokens rejetés: {self.tokens_rejected} ({self.tokens_rejected/self.tokens_scanned*100 if self.tokens_scanned > 0 else 0:.1f}%)")

        if self.rejection_reasons:
            print(f"\nRaisons de rejet:")
            for reason, count in sorted(self.rejection_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"  {count}x - {reason}")

        print("="*80 + "\n")

        # Afficher aussi les stats de la DB
        self.alert_tracker.print_stats()

    def close(self):
        """Ferme les connexions."""
        self.alert_tracker.close()


# ==============================================
# EXEMPLE D'UTILISATION
# ==============================================

if __name__ == "__main__":
    # Initialiser le système
    scanner = CompleteScanner(min_security_score=50)

    # Simuler la détection de quelques tokens
    test_tokens = [
        {
            'name': 'TestToken1',
            'address': '0x6982508145454Ce325dDbE47a25d4ec3d2311933',  # PEPE (pour test)
            'network': 'eth',
            'price': 0.00000123,
            'score': 85,
            'volume_24h': 500000,
            'liquidity': 300000,
            'total_txns': 2000,
            'buy_ratio': 1.5,
            'age_hours': 12
        },
        # Ajoutez d'autres tokens ici pour tester
    ]

    print("\n🚀 DÉMARRAGE DU SCAN DE TEST\n")

    for token in test_tokens:
        scanner.process_token(token)
        time.sleep(1)  # Pause entre les scans

    # Afficher les statistiques
    scanner.print_statistics()

    # Fermer
    scanner.close()

    print("\n✅ TEST TERMINÉ\n")