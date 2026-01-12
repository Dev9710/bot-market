"""
Scanner Steps - Sous-fonctions du scanner principal

Décomposition du scan_geckoterminal() en étapes logiques:
- collect_pools_from_networks(): Collecte des pools depuis l'API
- update_price_max_for_tracked_tokens(): Mise à jour des prix max en DB
- analyze_and_filter_tokens(): Analyse et filtrage des opportunités
- process_and_send_alerts(): Traitement et envoi des alertes
- track_active_alerts(): Suivi des alertes actives
- report_liquidity_stats(): Rapport des statistiques de liquidité
"""

import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from config.settings import (
    NETWORKS,
    MAX_TOKEN_AGE_HOURS,
    MAX_ALERTS_PER_SCAN,
    NETWORK_SCORE_FILTERS,
    ENABLE_ACTIVE_TRACKING,
    ACTIVE_TRACKING_MAX_AGE_HOURS,
    ACTIVE_TRACKING_UPDATE_COOLDOWN_MINUTES,
)
from utils.helpers import log
from utils.api_client import get_trending_pools, get_new_pools, get_pool_by_address, parse_pool_data
from utils.telegram import send_telegram
from data.cache import update_buy_ratio_history
from core.signals import get_price_momentum_from_api, find_resistance_simple, group_pools_by_token, analyze_multi_pool, detect_signals
from core.scoring import calculate_final_score, calculate_confidence_tier
from core.filters import check_watchlist_token, is_valid_opportunity
from core.alerts import should_send_alert, generer_alerte_complete
from core.strategy_validator import check_and_send_vip_alert


def collect_pools_from_networks(liquidity_stats: Dict) -> List[Dict]:
    """
    Collecte tous les pools depuis tous les réseaux configurés.

    Args:
        liquidity_stats: Dictionnaire pour tracker les sources de liquidité

    Returns:
        Liste de tous les pools collectés avec leurs données
    """
    all_pools = []

    for network in NETWORKS:
        log(f"\n🔍 Scan réseau: {network.upper()}")

        # Trending pools - 1 page seulement (20 pools)
        trending = get_trending_pools(network)
        if trending:
            for pool in trending:
                pool_data = parse_pool_data(pool, network, liquidity_stats)
                if pool_data and pool_data["age_hours"] <= MAX_TOKEN_AGE_HOURS:
                    all_pools.append(pool_data)
            log(f"   📊 {len(trending)} pools trending trouvés")

        time.sleep(2)

        # New pools - 1 page seulement (20 pools)
        new_pools = get_new_pools(network)
        if new_pools:
            for pool in new_pools:
                pool_data = parse_pool_data(pool, network, liquidity_stats)
                if pool_data and pool_data["age_hours"] <= MAX_TOKEN_AGE_HOURS:
                    all_pools.append(pool_data)
            log(f"   🆕 {len(new_pools)} nouveaux pools trouvés")

        time.sleep(2)

    log(f"\n📊 Total pools collectés: {len(all_pools)}")
    return all_pools


def update_price_max_for_tracked_tokens(all_pools: List[Dict], alert_tracker) -> None:
    """
    Met à jour le prix MAX en temps réel pour TOUS les tokens trackés.
    CRITIQUE pour backtesting: capture les pics de prix entre chaque scan.

    Args:
        all_pools: Liste de tous les pools collectés
        alert_tracker: Instance AlertTracker pour mise à jour DB
    """
    if alert_tracker is None:
        return

    for pool_data in all_pools:
        token_address = pool_data.get('token_address')
        current_price = pool_data.get('price', 0)

        if token_address and current_price > 0:
            # Vérifier si ce token a une alerte active
            previous_alert = alert_tracker.get_last_alert_for_token(token_address)
            if previous_alert:
                alert_id = previous_alert.get('id')
                # Mettre à jour le prix MAX en DB
                alert_tracker.update_price_max_realtime(alert_id, current_price)


def analyze_and_filter_tokens(
    all_pools: List[Dict],
    security_checker
) -> Tuple[List[Dict], int]:
    """
    Analyse tous les tokens, calcule les scores et filtre les opportunités.

    Args:
        all_pools: Liste de tous les pools collectés
        security_checker: Instance SecurityChecker pour validation sécurité

    Returns:
        (opportunités, tokens_rejected)
        - opportunités: Liste des opportunités validées
        - tokens_rejected: Nombre de tokens rejetés
    """
    # Grouper par token
    grouped = group_pools_by_token(all_pools)
    log(f"🔗 Tokens uniques détectés: {len(grouped)}")

    opportunities = []
    tokens_rejected = 0

    for base_token, pools in grouped.items():
        # Multi-pool analysis
        multi_pool_data = analyze_multi_pool(pools)

        # Analyser chaque pool
        for pool_data in pools:
            # Momentum - SIMPLIFIÉ: depuis API directement
            momentum = get_price_momentum_from_api(pool_data)

            # Résistance - SIMPLIFIÉ: calcul basique
            resistance_data = find_resistance_simple(pool_data)

            # Score (avec analyse whale)
            score, base_score, momentum_bonus, whale_analysis = calculate_final_score(
                pool_data, momentum, multi_pool_data
            )

            # NOUVEAU: Rejeter immédiatement si WHALE DUMP détecté
            if whale_analysis['pattern'] == 'WHALE_SELLING':
                log(f"   🚨 {pool_data['name']}: WHALE DUMP détecté - REJETÉ")
                tokens_rejected += 1
                continue

            # FILTRE SCORE PAR RÉSEAU (maintenant que le score est calculé!)
            network = pool_data.get('network', '').lower()
            min_score_required = NETWORK_SCORE_FILTERS.get(network, {}).get('min_score', 85)

            # Token watchlist: bypass filtre score
            if not check_watchlist_token(pool_data) and score < min_score_required:
                log(f"   ⏭️  {pool_data['name']}: [V3 REJECT] Score insuffisant: {score} < {min_score_required} ({network.upper()})")
                tokens_rejected += 1
                continue

            # Validation sécurité
            token_address = pool_data["pool_address"]
            network = pool_data["network"]

            log(f"\n🔒 Vérification sécurité: {pool_data['name']}")
            security_result = security_checker.check_token_security(token_address, network)

            # Vérifier si le token passe les critères de sécurité
            should_send, reason = security_checker.should_send_alert(
                security_result, min_security_score=50
            )

            if not should_send:
                log(f"⛔ Token rejeté: {reason}")
                log(f"   Score sécurité: {security_result['security_score']}/100")
                log(f"   Niveau risque: {security_result['risk_level']}")
                tokens_rejected += 1
                continue

            log(f"✅ Sécurité validée (Score: {security_result['security_score']}/100)")

            # Validation opportunité (filtres V3 + validation classique)
            is_valid, reason = is_valid_opportunity(pool_data, score)

            if not is_valid:
                log(f"   ⏭️  {pool_data['name']}: {reason}")
                continue

            # Détecter signaux
            signals = detect_signals(pool_data, momentum, multi_pool_data)

            # Ajouter signaux whale aux signaux existants
            if whale_analysis['signals']:
                signals.extend(whale_analysis['signals'])

            opportunities.append({
                "pool_data": pool_data,
                "score": score,
                "base_score": base_score,
                "momentum_bonus": momentum_bonus,
                "whale_analysis": whale_analysis,
                "momentum": momentum,
                "multi_pool_data": multi_pool_data,
                "signals": signals,
                "resistance_data": resistance_data,
                "security_result": security_result,  # Ajouter pour process_and_send_alerts
            })

            log(f"   ✅ Opportunité: {pool_data['name']} (Score: {score})")

    # Trier par score
    opportunities.sort(key=lambda x: x["score"], reverse=True)

    log(f"\n📊 TOTAL: {len(opportunities)} opportunités détectées")

    return opportunities, tokens_rejected


def process_and_send_alerts(
    opportunities: List[Dict],
    alert_tracker,
    security_checker
) -> Tuple[int, int]:
    """
    Traite les opportunités et envoie les alertes Telegram.

    Args:
        opportunities: Liste des opportunités validées
        alert_tracker: Instance AlertTracker pour sauvegarde DB
        security_checker: Instance SecurityChecker pour infos sécurité

    Returns:
        (alerts_sent, tokens_rejected)
    """
    alerts_sent = 0
    tokens_rejected = 0

    for opp in opportunities:
        base_token = opp["pool_data"]["base_token_name"]
        pool_addr = opp["pool_data"]["pool_address"]
        alert_key = f"{base_token}_{pool_addr}"

        # Utiliser pool_address comme token_address
        token_address = opp["pool_data"]["pool_address"]
        network = opp["pool_data"]["network"]

        # Vérifier si c'est la première alerte pour ce token
        is_first_alert = not alert_tracker.token_already_alerted(token_address)

        # Générer le message d'alerte (pour récupérer regle5_data)
        alert_msg, regle5_data = generer_alerte_complete(
            opp["pool_data"],
            opp["score"],
            opp["base_score"],
            opp["momentum_bonus"],
            opp["momentum"],
            opp["multi_pool_data"],
            opp["signals"],
            opp["resistance_data"],
            opp.get("whale_analysis"),
            is_first_alert,
            alert_tracker
        )

        # NOUVEAU: Vérifier si on doit envoyer l'alerte (FIX BUG #1 - SPAM)
        price = opp["pool_data"].get("price_usd", 0)
        should_send_now, send_reason = should_send_alert(
            token_address, price, alert_tracker, regle5_data
        )

        if not should_send_now:
            log(f"⏸️ Alerte bloquée (anti-spam): {opp['pool_data']['name']}")
            log(f"   Raison: {send_reason}")
            continue

        # Ajouter les infos de sécurité à l'alerte
        security_result = opp.get("security_result", {})
        security_info = security_checker.format_security_warning(security_result)
        alert_msg = alert_msg + "\n" + security_info

        if send_telegram(alert_msg):
            log(f"✅ Alerte envoyée: {opp['pool_data']['name']} (Score: {opp['score']})")

            # SAUVEGARDE EN BASE DE DONNÉES + TRACKING AUTO
            try:
                # Préparer les données pour la DB
                price = opp["pool_data"].get("price_usd", 0)
                entry_price = price
                stop_loss_price = price * 0.90  # -10%
                tp1_price = price * 1.05  # +5%
                tp2_price = price * 1.10  # +10%
                tp3_price = price * 1.15  # +15%

                # Calculate tier for confidence level (CRITICAL for dashboard display)
                tier = calculate_confidence_tier(opp["pool_data"])

                alert_data = {
                    'token_name': opp["pool_data"]["name"],
                    'token_address': token_address,
                    'network': network,
                    'price_at_alert': price,
                    'score': opp["score"],
                    'tier': tier,  # CRITICAL: Added for dashboard filtering
                    'base_score': opp["base_score"],
                    'momentum_bonus': opp["momentum_bonus"],
                    'confidence_score': security_result.get('security_score', 0),
                    'volume_24h': opp["pool_data"].get("volume_24h", 0),
                    'volume_6h': opp["pool_data"].get("volume_6h", 0),
                    'volume_1h': opp["pool_data"].get("volume_1h", 0),
                    'liquidity': opp["pool_data"].get("liquidity", 0),
                    'buys_24h': opp["pool_data"].get("buys_24h", 0),
                    'sells_24h': opp["pool_data"].get("sells_24h", 0),
                    'buy_ratio': opp["pool_data"].get("buy_ratio", 0),
                    'total_txns': opp["pool_data"].get("total_txns", 0),
                    'age_hours': opp["pool_data"].get("age_hours", 0),
                    'volume_acceleration_1h_vs_6h': opp["pool_data"].get("volume_acceleration_1h_vs_6h", 0),
                    'volume_acceleration_6h_vs_24h': opp["pool_data"].get("volume_acceleration_6h_vs_24h", 0),
                    'entry_price': entry_price,
                    'stop_loss_price': stop_loss_price,
                    'stop_loss_percent': -10,
                    'tp1_price': tp1_price,
                    'tp1_percent': 5,
                    'tp2_price': tp2_price,
                    'tp2_percent': 10,
                    'tp3_price': tp3_price,
                    'tp3_percent': 15,
                    'alert_message': alert_msg,
                    # RÈGLE 5: Données de vélocité du pump
                    'velocite_pump': regle5_data['velocite_pump'],
                    'type_pump': regle5_data['type_pump'],
                    'decision_tp_tracking': regle5_data['decision_tp_tracking'],
                    'temps_depuis_alerte_precedente': regle5_data['temps_depuis_alerte_precedente'],
                    'is_alerte_suivante': regle5_data['is_alerte_suivante']
                }

                alert_id = alert_tracker.save_alert(alert_data)
                if alert_id > 0:
                    log(f"   💾 Sauvegardé en DB (ID: {alert_id}) - Tracking auto démarré")

                    # VALIDATION STRATÉGIE VIP: Vérifier si prête au trade
                    try:
                        check_and_send_vip_alert(alert_data, alert_id, send_telegram)
                    except Exception as vip_error:
                        log(f"   ⚠️ Erreur validation VIP: {vip_error}")
                else:
                    log(f"   ⚠️ Échec sauvegarde DB (token déjà existant?)")

            except Exception as e:
                log(f"   ⚠️ Erreur sauvegarde DB: {e}")

            alerts_sent += 1
        else:
            log(f"❌ Échec alerte: {opp['pool_data']['name']}")

        if alerts_sent >= MAX_ALERTS_PER_SCAN:
            log(f"⚠️ Limite {MAX_ALERTS_PER_SCAN} alertes atteinte")
            break

        time.sleep(1)

    return alerts_sent, tokens_rejected


def track_active_alerts(alert_tracker) -> int:
    """
    Tracking actif des alertes existantes pour détecter TP/SL.

    Args:
        alert_tracker: Instance AlertTracker

    Returns:
        Nombre de mises à jour envoyées
    """
    if not ENABLE_ACTIVE_TRACKING or alert_tracker is None:
        return 0

    log(f"\n📡 TRACKING ACTIF: Vérification des pools alertés...")

    active_alerts = alert_tracker.get_active_alerts(max_age_hours=ACTIVE_TRACKING_MAX_AGE_HOURS)
    log(f"   🔍 {len(active_alerts)} alertes actives à tracker (< {ACTIVE_TRACKING_MAX_AGE_HOURS}h)")

    updates_sent = 0
    for alert in active_alerts:
        try:
            alert_id = alert['id']
            token_name = alert['token_name']
            pool_address = alert['token_address']
            network = alert['network']
            created_at_str = alert['created_at']

            # Vérifier cooldown (éviter spam)
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
            minutes_elapsed = (now - created_at).total_seconds() / 60

            # Vérifier si dernière mise à jour était il y a moins de COOLDOWN minutes
            if minutes_elapsed < ACTIVE_TRACKING_UPDATE_COOLDOWN_MINUTES:
                continue  # Trop récent, skip

            # Récupérer données actuelles du pool
            pool_data = get_pool_by_address(network, pool_address)

            if not pool_data or not isinstance(pool_data, dict):
                # Pool plus disponible (delisted, erreur API, etc.)
                log(f"   ⚠️ Pool data invalide pour {token_name}: {type(pool_data)}")
                continue

            current_price = pool_data.get('price_usd', 0)

            if current_price <= 0:
                continue

            # Mettre à jour le prix MAX en temps réel
            alert_tracker.update_price_max_realtime(alert_id, current_price)

            # Vérifier si on doit envoyer une mise à jour Telegram
            should_send_now, reason = should_send_alert(
                pool_address, current_price, alert_tracker, None
            )

            if should_send_now:
                log(f"   🔄 Mise à jour: {token_name} - {reason}")

                # Récupérer momentum et multi-pool (optionnel pour mises à jour)
                momentum = get_price_momentum_from_api(pool_data)
                multi_pool_data = {}  # Optionnel pour updates

                # Calculer score et whale analysis
                score, base_score, momentum_bonus, whale_analysis = calculate_final_score(
                    pool_data, momentum, multi_pool_data
                )

                # Générer message d'alerte (is_first_alert = False)
                try:
                    alert_msg, regle5_data = generer_alerte_complete(
                        pool_data, score, base_score, momentum_bonus, momentum,
                        multi_pool_data, [], None, whale_analysis,
                        is_first_alert=False,  # C'est une mise à jour
                        tracker=alert_tracker
                    )
                except Exception as gen_error:
                    log(f"   ❌ Erreur génération alerte pour {token_name}: {gen_error}")
                    import traceback
                    log(f"   Traceback: {traceback.format_exc()}")
                    continue  # Skip cette alerte

                # Envoyer via Telegram
                success = send_telegram(alert_msg)

                if success:
                    updates_sent += 1
                    log(f"   ✅ Mise à jour envoyée pour {token_name}")

                    # Limiter le nombre de mises à jour par scan
                    if updates_sent >= 5:  # Max 5 mises à jour par scan
                        log(f"   ⚠️ Limite 5 mises à jour atteinte")
                        break
                else:
                    log(f"   ❌ Échec envoi mise à jour: {token_name}")

                time.sleep(1)  # Pause entre mises à jour

        except Exception as e:
            log(f"   ❌ Erreur tracking {alert.get('token_name', 'unknown')}: {e}")

    log(f"   📊 Tracking terminé: {updates_sent} mises à jour envoyées")

    return updates_sent


def report_liquidity_stats(liquidity_stats: Dict) -> None:
    """
    Affiche les statistiques des sources de liquidité.

    Args:
        liquidity_stats: Dictionnaire des compteurs par source
    """
    log(f"\n📊 STATISTIQUES SOURCES DE LIQUIDITÉ:")
    log(f"   Total pools analysés: {sum(liquidity_stats.values())}")

    total_pools = sum(liquidity_stats.values())
    if total_pools > 0:
        real_reserve = liquidity_stats.get('reserve_in_usd', 0)
        fdv_estimate = liquidity_stats.get('fdv_usd(10%)', 0)
        mcap_estimate = liquidity_stats.get('market_cap(15%)', 0)
        vol_estimate = liquidity_stats.get('volume_24h(x5)', 0)
        none_liq = liquidity_stats.get('none', 0)

        # Calculer pourcentages
        real_pct = (real_reserve / total_pools) * 100
        fdv_pct = (fdv_estimate / total_pools) * 100
        mcap_pct = (mcap_estimate / total_pools) * 100
        vol_pct = (vol_estimate / total_pools) * 100
        none_pct = (none_liq / total_pools) * 100

        log(f"   ✅ reserve_in_usd (REAL):      {real_reserve:4d} pools ({real_pct:5.1f}%)")

        if fdv_estimate + mcap_estimate + vol_estimate + none_liq > 0:
            log(f"   ⚠️  ESTIMATIONS (FALLBACK):")
            if fdv_estimate > 0:
                log(f"      • fdv_usd (10%):           {fdv_estimate:4d} pools ({fdv_pct:5.1f}%)")
            if mcap_estimate > 0:
                log(f"      • market_cap (15%):        {mcap_estimate:4d} pools ({mcap_pct:5.1f}%)")
            if vol_estimate > 0:
                log(f"      • volume_24h (x5):         {vol_estimate:4d} pools ({vol_pct:5.1f}%)")
            if none_liq > 0:
                log(f"      • none (LIQ=0):            {none_liq:4d} pools ({none_pct:5.1f}%)")

        # Résumé qualité des données
        if real_pct >= 90:
            log(f"   🎯 EXCELLENT: {real_pct:.1f}% de données réelles")
        elif real_pct >= 70:
            log(f"   ✅ BON: {real_pct:.1f}% de données réelles")
        elif real_pct >= 50:
            log(f"   ⚠️  MOYEN: Seulement {real_pct:.1f}% de données réelles")
        else:
            log(f"   🚨 CRITIQUE: Seulement {real_pct:.1f}% de données réelles!")
