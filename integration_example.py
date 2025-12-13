"""
EXEMPLE D'INTÉGRATION - Alert Tracker + Security Checker
Comment intégrer dans ton bot GeckoTerminal Scanner V2
"""

from alert_tracker import AlertTracker
from security_checker import SecurityChecker

# ============================================
# INITIALISATION (à faire au démarrage du bot)
# ============================================

# Créer les instances
tracker = AlertTracker(db_path='alerts_history.db')
security = SecurityChecker()

print("✅ Système de tracking et sécurité initialisé")


# ============================================
# INTÉGRATION DANS geckoterminal_scanner_v2.py
# ============================================

def generer_alerte_complete_avec_tracking(pool_data, score, base_score, momentum_bonus,
                                          momentum, multi_pool_data, signals,
                                          resistance_data):
    """
    Version modifiée de generer_alerte_complete() avec:
    1. Vérification sécurité AVANT génération
    2. Sauvegarde dans DB avec tracking automatique
    3. Ajout warnings sécurité dans l'alerte
    """

    # ========== 1. VÉRIFICATION SÉCURITÉ ==========
    token_address = pool_data["pool_address"]
    network = pool_data["network"]

    print(f"\n🔍 Vérification sécurité pour {pool_data['name']}...")

    # Checker la sécurité du token
    security_result = security.check_token_security(token_address, network)

    # Décider si on envoie l'alerte
    should_send, reason = security.should_send_alert(
        security_result,
        min_security_score=50  # Configurable selon tes besoins
    )

    if not should_send:
        print(f"❌ Alerte bloquée: {reason}")
        return None  # Ne pas envoyer l'alerte

    print(f"✅ Sécurité OK: {reason}")

    # ========== 2. CALCUL DES NIVEAUX PRIX ==========
    price = pool_data["price_usd"]

    # Entry (prix actuel avec petite marge)
    entry_low = price * 0.98
    entry_high = price * 1.02
    entry_price = price  # Prix médian

    # Stop loss (-10%)
    stop_loss_price = price * 0.90
    stop_loss_percent = -10.0

    # Take profits
    tp1_price = price * 1.05
    tp1_percent = 5.0

    tp2_price = price * 1.10
    tp2_percent = 10.0

    tp3_price = price * 1.15
    tp3_percent = 15.0

    # ========== 3. GÉNÉRATION MESSAGE ALERTE ==========
    # (Copier ton code actuel de generer_alerte_complete ici)
    # Pour l'exemple, version simplifiée:

    name = pool_data["name"]
    network_display = pool_data.get("network_display", network.upper())
    vol_24h = pool_data["volume_24h"]
    liq = pool_data["liquidity"]

    txt = f"\n🆕 *NOUVEAU TOKEN DEX*\n"
    txt += f"━━━━━━━━━━━━━━━━\n"
    txt += f"💎 {name}\n"
    txt += f"⛓️ Blockchain: {network_display}\n\n"

    # SCORE
    txt += f"🎯 *SCORE: {score}/100*\n"
    txt += f"   Base: {base_score} | Momentum: {momentum_bonus:+d}\n\n"

    # SÉCURITÉ (NOUVEAU)
    txt += f"━━━ SÉCURITÉ ━━━\n"
    txt += security.format_security_warning(security_result)
    txt += "\n"

    # PRIX & MOMENTUM
    txt += f"━━━ PRIX & MOMENTUM ━━━\n"
    txt += f"💰 Prix: ${price:.8f}\n"
    txt += f"📊 Vol 24h: ${vol_24h/1000:.0f}K\n"
    txt += f"💧 Liquidité: ${liq/1000:.0f}K\n\n"

    # ACTION RECOMMANDÉE
    txt += f"━━━ ACTION RECOMMANDÉE ━━━\n"
    txt += f"⚡ Entry: ${entry_low:.8f} - ${entry_high:.8f}\n"
    txt += f"🛑 Stop loss: ${stop_loss_price:.8f} ({stop_loss_percent:.0f}%)\n"
    txt += f"🎯 TP1 (50%): ${tp1_price:.8f} (+{tp1_percent:.0f}%)\n"
    txt += f"🎯 TP2 (30%): ${tp2_price:.8f} (+{tp2_percent:.0f}%)\n"
    txt += f"🎯 TP3 (20%): ${tp3_price:.8f} (+{tp3_percent:.0f}%)\n"
    txt += f"🔄 Trail stop: -5% après TP1\n\n"

    # Lien GeckoTerminal
    txt += f"📍 GeckoTerminal: https://geckoterminal.com/{network}/pools/{token_address}\n"

    # ========== 4. SAUVEGARDE DANS DB AVEC TRACKING ==========
    alert_data = {
        'token_name': pool_data['base_token_name'],
        'token_address': token_address,
        'network': network,

        # Prix et scores
        'price_at_alert': price,
        'score': score,
        'base_score': base_score,
        'momentum_bonus': momentum_bonus,
        'confidence_score': pool_data.get('confidence_score', 0),

        # Métriques
        'volume_24h': pool_data['volume_24h'],
        'volume_6h': pool_data.get('volume_6h'),
        'volume_1h': pool_data.get('volume_1h'),
        'liquidity': pool_data['liquidity'],
        'buys_24h': pool_data.get('buys_24h'),
        'sells_24h': pool_data.get('sells_24h'),
        'buy_ratio': pool_data.get('buys_24h', 0) / pool_data.get('sells_24h', 1),
        'total_txns': pool_data.get('total_txns'),
        'age_hours': pool_data.get('age_hours'),

        # Niveaux de prix calculés
        'entry_price': entry_price,
        'stop_loss_price': stop_loss_price,
        'stop_loss_percent': stop_loss_percent,
        'tp1_price': tp1_price,
        'tp1_percent': tp1_percent,
        'tp2_price': tp2_price,
        'tp2_percent': tp2_percent,
        'tp3_price': tp3_price,
        'tp3_percent': tp3_percent,

        # Message complet
        'alert_message': txt
    }

    # Sauvegarder et démarrer le tracking automatique
    alert_id = tracker.save_alert(alert_data)

    if alert_id > 0:
        print(f"✅ Alerte {alert_id} sauvegardée - Tracking automatique démarré")
    else:
        print(f"⚠️ Erreur sauvegarde alerte")

    # ========== 5. RETOURNER LE MESSAGE ==========
    return txt


# ============================================
# MODIFICATION DANS scan_geckoterminal()
# ============================================

def scan_geckoterminal_modifie():
    """
    Version modifiée de scan_geckoterminal() qui utilise
    le nouveau système avec sécurité + tracking
    """
    # ... (ton code existant pour collecter les pools)

    # Quand tu génères une alerte:
    for opp in opportunities:
        base_token = opp["pool_data"]["base_token_name"]
        pool_addr = opp["pool_data"]["pool_address"]
        alert_key = f"{base_token}_{pool_addr}"

        if check_cooldown(alert_key):
            # UTILISER LA NOUVELLE FONCTION
            alert_msg = generer_alerte_complete_avec_tracking(
                opp["pool_data"],
                opp["score"],
                opp["base_score"],
                opp["momentum_bonus"],
                opp["momentum"],
                opp["multi_pool_data"],
                opp["signals"],
                opp["resistance_data"]
            )

            # Si None, l'alerte a été bloquée pour raisons de sécurité
            if alert_msg is None:
                print(f"⛔ Alerte bloquée pour {base_token} - Sécurité insuffisante")
                continue

            # Envoyer l'alerte Telegram
            if send_telegram(alert_msg):
                print(f"✅ Alerte envoyée: {opp['pool_data']['name']} (Score: {opp['score']})")
                alerts_sent += 1
            else:
                print(f"❌ Échec alerte: {opp['pool_data']['name']}")

            if alerts_sent >= MAX_ALERTS_PER_SCAN:
                print(f"⚠️ Limite {MAX_ALERTS_PER_SCAN} alertes atteinte")
                break

            time.sleep(1)


# ============================================
# COMMANDES UTILES
# ============================================

def afficher_stats():
    """Affiche les statistiques de performance."""
    tracker.print_stats()


def voir_historique_token(token_name):
    """Voir l'historique complet d'un token."""
    history = tracker.get_token_history(token_name)

    print(f"\n{'='*80}")
    print(f"📊 HISTORIQUE - {token_name}")
    print(f"{'='*80}")

    for i, alert in enumerate(history, 1):
        print(f"\n[{i}] Alerte du {alert['timestamp']}")
        print(f"   Prix entrée: ${alert['entry_price']:.8f}")
        print(f"   Score: {alert['score']}")

        if alert.get('roi_at_4h') is not None:
            print(f"   ROI 4h: {alert['roi_at_4h']:+.2f}%")
            print(f"   Qualité: {alert.get('prediction_quality', 'N/A')}")

        # Afficher les trackings
        if alert.get('trackings'):
            print(f"   Trackings:")
            for t in alert['trackings']:
                status = []
                if t['tp3_hit']:
                    status.append("🟢🟢🟢")
                elif t['tp2_hit']:
                    status.append("🟢🟢")
                elif t['tp1_hit']:
                    status.append("🟢")
                if t['sl_hit']:
                    status.append("🔴 SL")

                status_str = " ".join(status) if status else ""
                print(f"     {t['minutes']:4d}min: ${t['price']:.8f} ({t['roi']:+.2f}%) {status_str}")

    print(f"{'='*80}\n")


# ============================================
# EXEMPLE D'UTILISATION COMPLÈTE
# ============================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 EXEMPLE D'INTÉGRATION - Alert Tracker + Security Checker")
    print("="*80 + "\n")

    # Simuler une opportunité détectée
    pool_data_exemple = {
        'name': 'PEPE / USDT',
        'base_token_name': 'PEPE',
        'pool_address': '0x6982508145454Ce325dDbE47a25d4ec3d2311933',
        'network': 'eth',
        'network_display': 'Ethereum',
        'price_usd': 0.00000123,
        'volume_24h': 500000,
        'volume_6h': 200000,
        'volume_1h': 80000,
        'liquidity': 300000,
        'buys_24h': 1200,
        'sells_24h': 800,
        'total_txns': 2000,
        'age_hours': 12,
        'confidence_score': 85
    }

    score = 85
    base_score = 70
    momentum_bonus = 15
    momentum = {'1h': 5.2, '3h': 12.5, '6h': 18.3}
    multi_pool_data = {'is_multi_pool': False}
    signals = ["🔥 Volume spike x2.5", "🟢 Buy pressure forte"]
    resistance_data = {}

    # Générer l'alerte avec sécurité + tracking
    alert_msg = generer_alerte_complete_avec_tracking(
        pool_data_exemple, score, base_score, momentum_bonus,
        momentum, multi_pool_data, signals, resistance_data
    )

    if alert_msg:
        print("\n📨 MESSAGE D'ALERTE GÉNÉRÉ:\n")
        print(alert_msg)
    else:
        print("\n⛔ Alerte bloquée pour raisons de sécurité")

    # Afficher les stats après quelques alertes
    print("\n")
    afficher_stats()

    # Voir l'historique d'un token
    voir_historique_token("PEPE")

    print("\n✅ Exemple terminé")
    print("\n💡 PROCHAINES ÉTAPES:")
    print("1. Implémenter fetch_current_price() dans alert_tracker.py")
    print("2. Configurer les APIs honeypot/LP lock dans security_checker.py")
    print("3. Intégrer dans ton geckoterminal_scanner_v2.py")
    print("4. Tester avec des tokens réels")
    print("5. Analyser les stats après 24-48h\n")