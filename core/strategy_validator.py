"""
Strategy Validator - Validation des stratégies réseau pour canal VIP

Vérifie si une alerte remplit TOUS les critères de la stratégie réseau
et envoie une notification au canal Telegram VIP si validée.
"""

from typing import Dict, Optional, List, Tuple
from utils.helpers import log


# STRATÉGIES PAR RÉSEAU (identiques au frontend token_details.html)
NETWORK_STRATEGIES = {
    'solana': {
        'min_score': 95,
        'min_velocity': 5,
        'min_liq': 30000,
        'max_liq': 2000000,
        'min_volume': 30000,
        'min_age': 1,
        'max_age': 48,
        'min_buy_ratio': 0.55,
        'bonus_score': 98,
        'rules': [
            {'name': 'Score', 'target': '≥ 95 (STRICT!)', 'check': lambda a: a.get('score', 0) >= 95},
            {'name': 'Liquidité', 'target': '$30K-$2M', 'check': lambda a: 30000 <= a.get('liquidity', 0) <= 2000000},
            {'name': 'Volume 24h', 'target': '≥ $30K', 'check': lambda a: a.get('volume_24h', 0) >= 30000},
            {'name': 'Vélocité', 'target': '≥ 5x', 'check': lambda a: a.get('velocite_pump', 0) >= 5},
            {'name': 'Buy Ratio', 'target': '≥ 55%', 'check': lambda a: a.get('buy_ratio', 0) >= 0.55},
            {'name': 'Age', 'target': '1-48h', 'check': lambda a: 1 <= a.get('age_hours', 0) <= 48},
            {'name': 'BONUS', 'target': 'Score 98-100', 'check': lambda a: a.get('score', 0) >= 98, 'bonus': True}
        ]
    },
    'eth': {
        'min_score': 90,
        'min_velocity': 3,
        'min_liq': 50000,
        'max_liq': 5000000,
        'min_volume': 50000,
        'min_age': 2,
        'max_age': 72,
        'min_buy_ratio': 0.50,
        'bonus_score': 95,
        'rules': [
            {'name': 'Score', 'target': '≥ 90', 'check': lambda a: a.get('score', 0) >= 90},
            {'name': 'Liquidité', 'target': '$50K-$5M', 'check': lambda a: 50000 <= a.get('liquidity', 0) <= 5000000},
            {'name': 'Volume 24h', 'target': '≥ $50K', 'check': lambda a: a.get('volume_24h', 0) >= 50000},
            {'name': 'Vélocité', 'target': '≥ 3x', 'check': lambda a: a.get('velocite_pump', 0) >= 3},
            {'name': 'Buy Ratio', 'target': '≥ 50%', 'check': lambda a: a.get('buy_ratio', 0) >= 0.50},
            {'name': 'Age', 'target': '2-72h', 'check': lambda a: 2 <= a.get('age_hours', 0) <= 72},
            {'name': 'BONUS', 'target': 'Score 95-100', 'check': lambda a: a.get('score', 0) >= 95, 'bonus': True}
        ]
    },
    'bsc': {
        'min_score': 88,
        'min_velocity': 4,
        'min_liq': 20000,
        'max_liq': 1000000,
        'min_volume': 20000,
        'min_age': 1,
        'max_age': 48,
        'min_buy_ratio': 0.52,
        'bonus_score': 93,
        'rules': [
            {'name': 'Score', 'target': '≥ 88', 'check': lambda a: a.get('score', 0) >= 88},
            {'name': 'Liquidité', 'target': '$20K-$1M', 'check': lambda a: 20000 <= a.get('liquidity', 0) <= 1000000},
            {'name': 'Volume 24h', 'target': '≥ $20K', 'check': lambda a: a.get('volume_24h', 0) >= 20000},
            {'name': 'Vélocité', 'target': '≥ 4x', 'check': lambda a: a.get('velocite_pump', 0) >= 4},
            {'name': 'Buy Ratio', 'target': '≥ 52%', 'check': lambda a: a.get('buy_ratio', 0) >= 0.52},
            {'name': 'Age', 'target': '1-48h', 'check': lambda a: 1 <= a.get('age_hours', 0) <= 48},
            {'name': 'BONUS', 'target': 'Score 93-100', 'check': lambda a: a.get('score', 0) >= 93, 'bonus': True}
        ]
    },
    'base': {
        'min_score': 90,
        'min_velocity': 3,
        'min_liq': 30000,
        'max_liq': 2000000,
        'min_volume': 30000,
        'min_age': 1,
        'max_age': 48,
        'min_buy_ratio': 0.50,
        'bonus_score': 95,
        'rules': [
            {'name': 'Score', 'target': '≥ 90', 'check': lambda a: a.get('score', 0) >= 90},
            {'name': 'Liquidité', 'target': '$30K-$2M', 'check': lambda a: 30000 <= a.get('liquidity', 0) <= 2000000},
            {'name': 'Volume 24h', 'target': '≥ $30K', 'check': lambda a: a.get('volume_24h', 0) >= 30000},
            {'name': 'Vélocité', 'target': '≥ 3x', 'check': lambda a: a.get('velocite_pump', 0) >= 3},
            {'name': 'Buy Ratio', 'target': '≥ 50%', 'check': lambda a: a.get('buy_ratio', 0) >= 0.50},
            {'name': 'Age', 'target': '1-48h', 'check': lambda a: 1 <= a.get('age_hours', 0) <= 48},
            {'name': 'BONUS', 'target': 'Score 95-100', 'check': lambda a: a.get('score', 0) >= 95, 'bonus': True}
        ]
    },
    'arbitrum': {
        'min_score': 88,
        'min_velocity': 3,
        'min_liq': 40000,
        'max_liq': 3000000,
        'min_volume': 40000,
        'min_age': 2,
        'max_age': 72,
        'min_buy_ratio': 0.50,
        'bonus_score': 93,
        'rules': [
            {'name': 'Score', 'target': '≥ 88', 'check': lambda a: a.get('score', 0) >= 88},
            {'name': 'Liquidité', 'target': '$40K-$3M', 'check': lambda a: 40000 <= a.get('liquidity', 0) <= 3000000},
            {'name': 'Volume 24h', 'target': '≥ $40K', 'check': lambda a: a.get('volume_24h', 0) >= 40000},
            {'name': 'Vélocité', 'target': '≥ 3x', 'check': lambda a: a.get('velocite_pump', 0) >= 3},
            {'name': 'Buy Ratio', 'target': '≥ 50%', 'check': lambda a: a.get('buy_ratio', 0) >= 0.50},
            {'name': 'Age', 'target': '2-72h', 'check': lambda a: 2 <= a.get('age_hours', 0) <= 72},
            {'name': 'BONUS', 'target': 'Score 93-100', 'check': lambda a: a.get('score', 0) >= 93, 'bonus': True}
        ]
    },
    'polygon_pos': {
        'min_score': 85,
        'min_velocity': 3,
        'min_liq': 15000,
        'max_liq': 800000,
        'min_volume': 15000,
        'min_age': 1,
        'max_age': 48,
        'min_buy_ratio': 0.50,
        'bonus_score': 90,
        'rules': [
            {'name': 'Score', 'target': '≥ 85', 'check': lambda a: a.get('score', 0) >= 85},
            {'name': 'Liquidité', 'target': '$15K-$800K', 'check': lambda a: 15000 <= a.get('liquidity', 0) <= 800000},
            {'name': 'Volume 24h', 'target': '≥ $15K', 'check': lambda a: a.get('volume_24h', 0) >= 15000},
            {'name': 'Vélocité', 'target': '≥ 3x', 'check': lambda a: a.get('velocite_pump', 0) >= 3},
            {'name': 'Buy Ratio', 'target': '≥ 50%', 'check': lambda a: a.get('buy_ratio', 0) >= 0.50},
            {'name': 'Age', 'target': '1-48h', 'check': lambda a: 1 <= a.get('age_hours', 0) <= 48},
            {'name': 'BONUS', 'target': 'Score 90-100', 'check': lambda a: a.get('score', 0) >= 90, 'bonus': True}
        ]
    },
    'avax': {
        'min_score': 88,
        'min_velocity': 3,
        'min_liq': 25000,
        'max_liq': 1500000,
        'min_volume': 25000,
        'min_age': 1,
        'max_age': 48,
        'min_buy_ratio': 0.50,
        'bonus_score': 93,
        'rules': [
            {'name': 'Score', 'target': '≥ 88', 'check': lambda a: a.get('score', 0) >= 88},
            {'name': 'Liquidité', 'target': '$25K-$1.5M', 'check': lambda a: 25000 <= a.get('liquidity', 0) <= 1500000},
            {'name': 'Volume 24h', 'target': '≥ $25K', 'check': lambda a: a.get('volume_24h', 0) >= 25000},
            {'name': 'Vélocité', 'target': '≥ 3x', 'check': lambda a: a.get('velocite_pump', 0) >= 3},
            {'name': 'Buy Ratio', 'target': '≥ 50%', 'check': lambda a: a.get('buy_ratio', 0) >= 0.50},
            {'name': 'Age', 'target': '1-48h', 'check': lambda a: 1 <= a.get('age_hours', 0) <= 48},
            {'name': 'BONUS', 'target': 'Score 93-100', 'check': lambda a: a.get('score', 0) >= 93, 'bonus': True}
        ]
    }
}


def validate_strategy(alert_data: Dict) -> Tuple[bool, bool, int, int, List[str]]:
    """
    Valide si une alerte remplit TOUS les critères de sa stratégie réseau.

    Args:
        alert_data: Données complètes de l'alerte

    Returns:
        Tuple (is_ready_to_trade, has_bonus, passed_count, total_count, failed_rules)
        - is_ready_to_trade: True si TOUS les critères obligatoires sont remplis
        - has_bonus: True si le bonus est activé
        - passed_count: Nombre de critères validés
        - total_count: Nombre total de critères obligatoires
        - failed_rules: Liste des règles non validées
    """
    network = alert_data.get('network', '').lower()
    strategy = NETWORK_STRATEGIES.get(network, NETWORK_STRATEGIES.get('eth'))

    if not strategy:
        log(f"   ⚠️ Stratégie inconnue pour réseau: {network}")
        return False, False, 0, 0, []

    # Séparer les règles critiques et bonus
    critical_rules = [r for r in strategy['rules'] if not r.get('bonus', False)]
    bonus_rules = [r for r in strategy['rules'] if r.get('bonus', False)]

    # Valider les règles critiques
    passed_count = 0
    failed_rules = []

    for rule in critical_rules:
        try:
            if rule['check'](alert_data):
                passed_count += 1
            else:
                failed_rules.append(rule['name'])
        except Exception as e:
            log(f"   ⚠️ Erreur validation règle {rule['name']}: {e}")
            failed_rules.append(rule['name'])

    total_count = len(critical_rules)
    is_ready_to_trade = (passed_count == total_count)

    # Vérifier le bonus
    has_bonus = False
    if bonus_rules:
        try:
            has_bonus = all(rule['check'](alert_data) for rule in bonus_rules)
        except Exception as e:
            log(f"   ⚠️ Erreur validation bonus: {e}")

    return is_ready_to_trade, has_bonus, passed_count, total_count, failed_rules


def format_vip_message(alert_data: Dict, alert_id: int, has_bonus: bool) -> str:
    """
    Formate un message VIP pour le canal Telegram dédié.

    Args:
        alert_data: Données complètes de l'alerte
        alert_id: ID de l'alerte en DB
        has_bonus: True si le bonus est activé

    Returns:
        Message formaté prêt à envoyer
    """
    network = alert_data.get('network', '').upper()
    token_name = alert_data.get('token_name', 'UNKNOWN')
    score = alert_data.get('score', 0)

    # Titre selon bonus
    if has_bonus:
        title = "🚀 PRIORITÉ MAXIMALE - BONUS ACTIVÉ!"
    else:
        title = "✅ READY TO TRADE"

    # Récupérer les valeurs
    liquidity = alert_data.get('liquidity', 0)
    volume_24h = alert_data.get('volume_24h', 0)
    velocite_pump = alert_data.get('velocite_pump', 0)
    buy_ratio = alert_data.get('buy_ratio', 0)
    age_hours = alert_data.get('age_hours', 0)

    entry_price = alert_data.get('entry_price', 0)
    tp1_price = alert_data.get('tp1_price', 0)
    tp2_price = alert_data.get('tp2_price', 0)
    tp3_price = alert_data.get('tp3_price', 0)
    sl_price = alert_data.get('stop_loss_price', 0)

    # Récupérer la stratégie réseau
    network_key = alert_data.get('network', '').lower()
    strategy = NETWORK_STRATEGIES.get(network_key, NETWORK_STRATEGIES.get('eth'))

    # Construire la checklist validée
    critical_rules = [r for r in strategy['rules'] if not r.get('bonus', False)]
    checklist_lines = []

    for rule in critical_rules:
        name = rule['name']
        target = rule['target']

        # Formater la valeur actuelle
        if name == 'Score':
            current = f"{score}/100"
        elif name == 'Liquidité':
            current = f"${liquidity:,.0f}"
        elif name == 'Volume 24h':
            current = f"${volume_24h:,.0f}"
        elif name == 'Vélocité':
            current = f"{velocite_pump:.1f}x"
        elif name == 'Buy Ratio':
            current = f"{buy_ratio * 100:.0f}%"
        elif name == 'Age':
            current = f"{age_hours:.1f}h"
        else:
            current = "N/A"

        checklist_lines.append(f"✅ {name} {target} → {current}")

    # Ajouter le bonus si activé
    if has_bonus:
        bonus_rule = next((r for r in strategy['rules'] if r.get('bonus', False)), None)
        if bonus_rule:
            checklist_lines.append(f"🚀 {bonus_rule['name']} {bonus_rule['target']} ACTIVÉ")

    checklist = "\n".join(checklist_lines)

    # Construire le message
    message = f"""
{title}

{token_name} • {network}
Score: {score}/100 ⭐

✅ STRATÉGIE VALIDÉE ({len(critical_rules)}/{len(critical_rules)})
━━━━━━━━━━━━━━━━━━━━━
{checklist}

📊 ENTRY: ${entry_price:.10f}
🎯 TP1: ${tp1_price:.10f} (+5%)
🎯 TP2: ${tp2_price:.10f} (+10%)
🎯 TP3: ${tp3_price:.10f} (+15%)
🛡️ SL: ${sl_price:.10f} (-10%)

👉 <a href="https://bot-market-production.up.railway.app/bot-market/token_details.html?id={alert_id}">Voir Dashboard</a>
""".strip()

    return message


def check_and_send_vip_alert(alert_data: Dict, alert_id: int, telegram_sender) -> bool:
    """
    Vérifie si une alerte est prête au trade et envoie une notification VIP.

    Args:
        alert_data: Données complètes de l'alerte
        alert_id: ID de l'alerte en DB
        telegram_sender: Fonction d'envoi Telegram (send_telegram)

    Returns:
        True si notification VIP envoyée, False sinon
    """
    try:
        # Valider la stratégie
        is_ready, has_bonus, passed, total, failed = validate_strategy(alert_data)

        network = alert_data.get('network', 'UNKNOWN').upper()
        token_name = alert_data.get('token_name', 'UNKNOWN')

        if is_ready:
            status = "🚀 PRIORITÉ MAXIMALE - BONUS ACTIVÉ" if has_bonus else "✅ READY TO TRADE"
            log(f"   {status}: {token_name} ({network}) - {passed}/{total} critères validés")

            # Formater le message VIP
            vip_message = format_vip_message(alert_data, alert_id, has_bonus)

            # Envoyer au canal VIP
            vip_chat_id = "-1003393653837"  # Canal Botscp v3
            success = telegram_sender(vip_message, chat_id=vip_chat_id, parse_mode='HTML')

            if success:
                log(f"   📢 Notification VIP envoyée au canal {vip_chat_id}")
                return True
            else:
                log(f"   ⚠️ Échec envoi notification VIP")
                return False
        else:
            log(f"   ⏸️ Conditions non remplies: {token_name} ({network}) - {passed}/{total} critères ({', '.join(failed)} manquants)")
            return False

    except Exception as e:
        log(f"   ⚠️ Erreur validation stratégie VIP: {e}")
        return False
