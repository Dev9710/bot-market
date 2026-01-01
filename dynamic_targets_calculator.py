#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCULATEUR DYNAMIQUE DE TARGETS (TP1/TP2/TP3/SL/TS)
Recalcule les targets à chaque nouvelle alerte en fonction de l'évolution réelle
"""
import sys
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def calculate_dynamic_targets(alert, previous_alerts=None, current_price=None):
    """
    Calcule les targets dynamiques (TP1/TP2/TP3/SL/TS) optimaux
    basés sur:
    - Les patterns identifiés (gains moyens par réseau)
    - L'évolution du token (alertes multiples)
    - Les conditions actuelles (liquidité, volume, momentum)

    Args:
        alert: Dict contenant les données de l'alerte actuelle
        previous_alerts: List des alertes précédentes pour ce token (optionnel)
        current_price: Prix actuel si différent du prix d'alerte (optionnel)

    Returns:
        dict: {
            'entry_price': float,
            'tp1': {'price': float, 'percent': float, 'exit_amount': float},
            'tp2': {'price': float, 'percent': float, 'exit_amount': float},
            'tp3': {'price': float, 'percent': float, 'exit_amount': float},
            'stop_loss': {'price': float, 'percent': float},
            'trail_stop': {'percent': float, 'activation': str},
            'position_size': float (0-1),
            'reasoning': str,
            'risk_level': str
        }
    """

    # Extract data
    network = alert.get('network', '').lower()
    entry_price = current_price or alert.get('entry_price') or alert.get('price_at_alert', 0)
    liquidity = alert.get('liquidity', 0) or 0
    volume_24h = alert.get('volume_24h', 0) or 0
    score = alert.get('score', 0) or 0
    age_hours = alert.get('age_hours', 0) or 0
    accel = alert.get('volume_acceleration_1h_vs_6h', 0) or 0
    alert_count = alert.get('alert_count', 1) or 1

    # Analyze previous alerts if available
    has_history = previous_alerts and len(previous_alerts) > 1
    price_trend = None
    liquidity_trend = None
    volume_trend = None

    if has_history:
        # Sort by date
        sorted_alerts = sorted(previous_alerts, key=lambda x: x.get('created_at', ''))

        # Price trend
        prev_price = sorted_alerts[-2].get('entry_price', 0)
        if prev_price > 0 and entry_price > 0:
            price_change = ((entry_price - prev_price) / prev_price) * 100
            price_trend = 'hausse' if price_change > 2 else ('stable' if price_change > -2 else 'baisse')

        # Liquidity trend
        prev_liq = sorted_alerts[-2].get('liquidity', 0)
        if prev_liq > 0 and liquidity > 0:
            liq_change = ((liquidity - prev_liq) / prev_liq) * 100
            liquidity_trend = 'hausse' if liq_change > 5 else ('stable' if liq_change > -5 else 'baisse')

        # Volume trend
        prev_vol = sorted_alerts[-2].get('volume_24h', 0)
        if prev_vol > 0 and volume_24h > 0:
            vol_change = ((volume_24h - prev_vol) / prev_vol) * 100
            volume_trend = 'hausse' if vol_change > 10 else ('stable' if vol_change > -10 else 'baisse')

    # ================================================================
    # STEP 1: BASE TARGETS (selon réseau et patterns identifiés)
    # ================================================================

    # Gains moyens identifiés par réseau
    network_gains = {
        'eth': {'avg': 59.1, 'top': 1233, 'tp1_base': 15, 'tp2_base': 40, 'tp3_base': 80},
        'bsc': {'avg': 27.0, 'top': 70, 'tp1_base': 10, 'tp2_base': 25, 'tp3_base': 50},
        'base': {'avg': 16.5, 'top': 254, 'tp1_base': 8, 'tp2_base': 18, 'tp3_base': 35},
        'solana': {'avg': 13.3, 'top': 59, 'tp1_base': 7, 'tp2_base': 15, 'tp3_base': 30},
        'arbitrum': {'avg': 13.2, 'top': 23, 'tp1_base': 5, 'tp2_base': 12, 'tp3_base': 20}
    }

    base_config = network_gains.get(network, network_gains['solana'])

    tp1_pct = base_config['tp1_base']
    tp2_pct = base_config['tp2_base']
    tp3_pct = base_config['tp3_base']
    sl_pct = -10  # Standard -10%

    # ================================================================
    # STEP 2: AJUSTEMENTS SELON CONDITIONS ACTUELLES
    # ================================================================

    multiplier = 1.0
    reasoning_parts = []

    # 2.1 Score (qualité du signal)
    if score >= 95:
        multiplier *= 1.3
        reasoning_parts.append("Score ULTRA_HIGH (≥95): Targets +30%")
    elif score >= 85:
        multiplier *= 1.2
        reasoning_parts.append("Score HIGH (≥85): Targets +20%")
    elif score >= 75:
        multiplier *= 1.1
        reasoning_parts.append("Score MEDIUM (≥75): Targets +10%")
    elif score < 60:
        multiplier *= 0.8
        reasoning_parts.append("Score faible (<60): Targets -20% (prudence)")

    # 2.2 Liquidité (sécurité)
    if network == 'solana':
        if liquidity >= 200_000:
            multiplier *= 1.15
            reasoning_parts.append("Liquidité >200K (élevée pour SOL): Targets +15%")
        elif liquidity < 100_000:
            multiplier *= 0.9
            sl_pct = -8  # Stop plus serré si liq faible
            reasoning_parts.append("Liquidité <100K (risque): Targets -10%, SL -8%")
    else:
        if liquidity >= 500_000:
            multiplier *= 1.2
            reasoning_parts.append("Liquidité >500K (excellente): Targets +20%")
        elif liquidity < 100_000:
            multiplier *= 0.85
            sl_pct = -8
            reasoning_parts.append("Liquidité <100K (risque): Targets -15%, SL -8%")

    # 2.3 Volume (momentum)
    vol_liq_ratio = (volume_24h / liquidity * 100) if liquidity > 0 else 0
    if vol_liq_ratio > 500:
        multiplier *= 1.25
        reasoning_parts.append(f"Vol/Liq {vol_liq_ratio:.0f}% (fort momentum): Targets +25%")
    elif vol_liq_ratio > 200:
        multiplier *= 1.1
        reasoning_parts.append(f"Vol/Liq {vol_liq_ratio:.0f}% (bon momentum): Targets +10%")
    elif vol_liq_ratio < 50:
        multiplier *= 0.9
        reasoning_parts.append(f"Vol/Liq {vol_liq_ratio:.0f}% (faible): Targets -10%")

    # 2.4 Accélération
    if accel >= 6:
        multiplier *= 1.2
        reasoning_parts.append("Accélération ≥6x (explosive): Targets +20%")
    elif accel >= 4:
        multiplier *= 1.1
        reasoning_parts.append("Accélération ≥4x (forte): Targets +10%")
    elif accel < 1:
        multiplier *= 0.95
        reasoning_parts.append("Accélération <1x (décélération): Targets -5%")

    # 2.5 Freshness
    age_minutes = age_hours * 60
    if age_minutes < 5:
        multiplier *= 1.15
        reasoning_parts.append("ULTRA-FRESH (<5min): Targets +15%")
    elif age_minutes < 30:
        multiplier *= 1.05
        reasoning_parts.append("FRESH (<30min): Targets +5%")
    elif age_hours > 6:
        multiplier *= 0.9
        reasoning_parts.append("Age >6h (mature): Targets -10%")

    # ================================================================
    # STEP 3: AJUSTEMENTS SELON ÉVOLUTION (alertes multiples)
    # ================================================================

    if has_history and alert_count >= 2:

        # 3.1 Prix en hausse = bullish
        if price_trend == 'hausse':
            multiplier *= 1.3
            reasoning_parts.append(f"Prix en HAUSSE entre alertes: Targets +30% 🚀")
        elif price_trend == 'stable':
            multiplier *= 1.1
            reasoning_parts.append("Prix STABLE: Targets +10%")
        elif price_trend == 'baisse':
            multiplier *= 0.85
            sl_pct = -7  # Stop plus serré
            reasoning_parts.append("Prix en BAISSE: Targets -15%, SL -7% ⚠️")

        # 3.2 Liquidité en hausse = sécurité
        if liquidity_trend == 'hausse':
            multiplier *= 1.2
            reasoning_parts.append("Liquidité en HAUSSE: Targets +20% ✅")
        elif liquidity_trend == 'baisse':
            multiplier *= 0.8
            sl_pct = -7
            reasoning_parts.append("Liquidité en BAISSE: Targets -20%, SL -7% 🚨")

        # 3.3 Volume en hausse = momentum
        if volume_trend == 'hausse':
            multiplier *= 1.15
            reasoning_parts.append("Volume en HAUSSE: Targets +15%")
        elif volume_trend == 'baisse':
            multiplier *= 0.9
            reasoning_parts.append("Volume en BAISSE: Targets -10%")

        # 3.4 Nombre d'alertes = performance confirmée
        if alert_count >= 10:
            multiplier *= 1.4
            reasoning_parts.append(f"×{alert_count} ALERTES (champion): Targets +40% 🔥🔥🔥")
        elif alert_count >= 5:
            multiplier *= 1.25
            reasoning_parts.append(f"×{alert_count} ALERTES (winner): Targets +25% 🔥🔥")
        elif alert_count >= 2:
            multiplier *= 1.15
            reasoning_parts.append(f"×{alert_count} ALERTES (confirmé): Targets +15% 🔥")

    # ================================================================
    # STEP 4: CALCUL FINAL DES TARGETS
    # ================================================================

    tp1_pct_final = tp1_pct * multiplier
    tp2_pct_final = tp2_pct * multiplier
    tp3_pct_final = tp3_pct * multiplier

    # Cap les targets (sécurité)
    tp1_pct_final = min(tp1_pct_final, 50)
    tp2_pct_final = min(tp2_pct_final, 150)
    tp3_pct_final = min(tp3_pct_final, 300)

    # Prix des targets
    tp1_price = entry_price * (1 + tp1_pct_final / 100)
    tp2_price = entry_price * (1 + tp2_pct_final / 100)
    tp3_price = entry_price * (1 + tp3_pct_final / 100)
    sl_price = entry_price * (1 + sl_pct / 100)

    # ================================================================
    # STEP 5: POSITION SIZING DYNAMIQUE
    # ================================================================

    position_size = 0.05  # Base 5%

    # Augmenter selon qualité signal
    if score >= 95:
        position_size = 0.10  # 10% si ULTRA_HIGH
    elif score >= 85:
        position_size = 0.07  # 7% si HIGH

    # Augmenter si alertes multiples
    if alert_count >= 5:
        position_size = min(0.10, position_size * 1.5)
    elif alert_count >= 2:
        position_size = min(0.10, position_size * 1.2)

    # Réduire si conditions dégradées
    if liquidity_trend == 'baisse' or price_trend == 'baisse':
        position_size *= 0.7

    # Cap à 10% max
    position_size = min(0.10, position_size)

    # ================================================================
    # STEP 6: RÉPARTITION EXITS (TP1/TP2/TP3)
    # ================================================================

    # Distribution standard
    tp1_exit = 0.50  # 50% à TP1
    tp2_exit = 0.30  # 30% à TP2
    tp3_exit = 0.20  # 20% à TP3

    # Ajuster si très bullish (alertes multiples + hausse)
    if alert_count >= 5 and price_trend == 'hausse':
        tp1_exit = 0.30  # Garder plus longtemps
        tp2_exit = 0.40
        tp3_exit = 0.30
        reasoning_parts.append("Token très bullish: Hold plus longtemps (30/40/30)")

    # Ajuster si conditions dégradées
    if liquidity_trend == 'baisse' or volume_trend == 'baisse':
        tp1_exit = 0.70  # Sortir plus vite
        tp2_exit = 0.20
        tp3_exit = 0.10
        reasoning_parts.append("Conditions dégradées: Exit rapide (70/20/10)")

    # ================================================================
    # STEP 7: TRAIL STOP
    # ================================================================

    # Trail stop activation
    ts_activation = "Après TP1 atteint"
    ts_percent = -5  # -5% standard

    # Trail plus serré si conditions risquées
    if liquidity < 100_000 or liquidity_trend == 'baisse':
        ts_percent = -3
        reasoning_parts.append("Trail Stop serré (-3%) vu risque liquidité")

    # Trail plus large si très bullish
    if alert_count >= 5 and price_trend == 'hausse' and liquidity_trend == 'hausse':
        ts_percent = -7
        ts_activation = "Après TP2 atteint"
        reasoning_parts.append("Trail Stop large (-7%) laissant respirer le pump")

    # ================================================================
    # STEP 8: RISK LEVEL
    # ================================================================

    risk_score = 0

    # Facteurs positifs
    if score >= 85: risk_score += 2
    if liquidity >= 200_000: risk_score += 2
    if accel >= 5: risk_score += 1
    if alert_count >= 2: risk_score += 2
    if price_trend == 'hausse': risk_score += 2
    if liquidity_trend == 'hausse': risk_score += 2

    # Facteurs négatifs
    if liquidity < 100_000: risk_score -= 3
    if liquidity_trend == 'baisse': risk_score -= 3
    if price_trend == 'baisse': risk_score -= 2
    if score < 70: risk_score -= 2

    if risk_score >= 7:
        risk_level = "🟢 FAIBLE (Excellent setup)"
    elif risk_score >= 4:
        risk_level = "🟡 MOYEN (Bon setup)"
    elif risk_score >= 0:
        risk_level = "🟠 ÉLEVÉ (Prudence)"
    else:
        risk_level = "🔴 TRÈS ÉLEVÉ (Déconseillé)"

    # ================================================================
    # RETURN FINAL
    # ================================================================

    return {
        'entry_price': entry_price,
        'tp1': {
            'price': tp1_price,
            'percent': tp1_pct_final,
            'exit_amount': tp1_exit * 100
        },
        'tp2': {
            'price': tp2_price,
            'percent': tp2_pct_final,
            'exit_amount': tp2_exit * 100
        },
        'tp3': {
            'price': tp3_price,
            'percent': tp3_pct_final,
            'exit_amount': tp3_exit * 100
        },
        'stop_loss': {
            'price': sl_price,
            'percent': sl_pct
        },
        'trail_stop': {
            'percent': ts_percent,
            'activation': ts_activation
        },
        'position_size': position_size * 100,  # En pourcentage
        'reasoning': reasoning_parts,
        'risk_level': risk_level,
        'multiplier': multiplier
    }

def print_targets_analysis(targets, alert, token_name="Unknown"):
    """Affiche l'analyse complète des targets"""

    print(f"\n{'='*90}")
    print(f"🎯 TARGETS DYNAMIQUES - {token_name}")
    print(f"{'='*90}\n")

    # Header
    network = alert.get('network', 'unknown').upper()
    score = alert.get('score', 0)
    alert_count = alert.get('alert_count', 1)

    print(f"Réseau: {network} | Score: {score} | Alertes: ×{alert_count}")
    print(f"Entry Price: ${targets['entry_price']:.8f}")

    print(f"\n{'─'*90}")
    print(f"💡 RAISONNEMENT:\n")

    for i, reason in enumerate(targets['reasoning'], 1):
        print(f"   {i}. {reason}")

    print(f"\n   Multiplicateur final: {targets['multiplier']:.2f}x")
    print(f"   Niveau de risque: {targets['risk_level']}")

    print(f"\n{'─'*90}")
    print(f"🎯 TARGETS & EXITS:\n")

    # TP1
    tp1 = targets['tp1']
    print(f"   TP1: ${tp1['price']:.8f} (+{tp1['percent']:.1f}%)")
    print(f"        → Sortir {tp1['exit_amount']:.0f}% de la position")

    # TP2
    tp2 = targets['tp2']
    print(f"\n   TP2: ${tp2['price']:.8f} (+{tp2['percent']:.1f}%)")
    print(f"        → Sortir {tp2['exit_amount']:.0f}% de la position")

    # TP3
    tp3 = targets['tp3']
    print(f"\n   TP3: ${tp3['price']:.8f} (+{tp3['percent']:.1f}%)")
    print(f"        → Sortir {tp3['exit_amount']:.0f}% de la position (reste)")

    print(f"\n{'─'*90}")
    print(f"🛡️  PROTECTION:\n")

    # Stop Loss
    sl = targets['stop_loss']
    print(f"   Stop Loss: ${sl['price']:.8f} ({sl['percent']:.0f}%)")
    print(f"              ⚠️  NON NÉGOCIABLE - Exit immédiat si touché")

    # Trail Stop
    ts = targets['trail_stop']
    print(f"\n   Trail Stop: {ts['percent']:.0f}%")
    print(f"               Activation: {ts['activation']}")

    print(f"\n{'─'*90}")
    print(f"💰 POSITION SIZING:\n")

    print(f"   Taille position recommandée: {targets['position_size']:.1f}% du capital total")

    capital_example = 10000  # Example avec 10K
    position_usd = capital_example * (targets['position_size'] / 100)

    print(f"\n   Exemple avec ${capital_example:,} capital:")
    print(f"   ├─ Position: ${position_usd:,.2f}")
    print(f"   ├─ Exit TP1 ({tp1['exit_amount']:.0f}%): ${position_usd * tp1['exit_amount']/100:,.2f}")
    print(f"   ├─ Exit TP2 ({tp2['exit_amount']:.0f}%): ${position_usd * tp2['exit_amount']/100:,.2f}")
    print(f"   └─ Exit TP3 ({tp3['exit_amount']:.0f}%): ${position_usd * tp3['exit_amount']/100:,.2f}")

    print(f"\n{'─'*90}")
    print(f"📊 RÉSUMÉ RAPIDE:\n")

    print(f"   Entry:  ${targets['entry_price']:.8f}")
    print(f"   SL:     ${sl['price']:.8f} ({sl['percent']:.0f}%)")
    print(f"   TP1:    ${tp1['price']:.8f} (+{tp1['percent']:.1f}%) - Exit {tp1['exit_amount']:.0f}%")
    print(f"   TP2:    ${tp2['price']:.8f} (+{tp2['percent']:.1f}%) - Exit {tp2['exit_amount']:.0f}%")
    print(f"   TP3:    ${tp3['price']:.8f} (+{tp3['percent']:.1f}%) - Exit {tp3['exit_amount']:.0f}%")
    print(f"   Trail:  {ts['percent']:.0f}% après {ts['activation'].lower()}")

    print(f"\n{'='*90}\n")

# ================================================================
# EXAMPLES / TESTS
# ================================================================

if __name__ == "__main__":

    print("🎯 CALCULATEUR DYNAMIQUE DE TARGETS\n")
    print("Basé sur l'analyse de 4252 alertes réelles\n")

    # ================================================================
    # TEST 1: SOLANA PREMIÈRE ALERTE (zone optimale)
    # ================================================================

    print("\n" + "="*90)
    print("TEST 1: SOLANA - PREMIÈRE ALERTE (Zone Optimale)")
    print("="*90)

    sol_first = {
        'network': 'solana',
        'entry_price': 0.00045,
        'liquidity': 180_000,
        'volume_24h': 2_500_000,
        'score': 95,
        'age_hours': 0.05,  # 3 min
        'volume_acceleration_1h_vs_6h': 6.0,
        'alert_count': 1
    }

    targets1 = calculate_dynamic_targets(sol_first)
    print_targets_analysis(targets1, sol_first, "TEST Token (SOL)")

    # ================================================================
    # TEST 2: SOLANA ALERTE MULTIPLE (prix en hausse)
    # ================================================================

    print("\n" + "="*90)
    print("TEST 2: SOLANA - ×5 ALERTES (Prix +15%, Liq +20%)")
    print("="*90)

    sol_multi_prev = [
        {'entry_price': 0.00045, 'liquidity': 180_000, 'volume_24h': 2_500_000, 'created_at': '2025-01-01 10:00:00'},
        {'entry_price': 0.00048, 'liquidity': 190_000, 'volume_24h': 2_800_000, 'created_at': '2025-01-01 10:15:00'},
        {'entry_price': 0.00050, 'liquidity': 200_000, 'volume_24h': 3_000_000, 'created_at': '2025-01-01 10:30:00'},
        {'entry_price': 0.00051, 'liquidity': 210_000, 'volume_24h': 3_200_000, 'created_at': '2025-01-01 10:45:00'}
    ]

    sol_multi_current = {
        'network': 'solana',
        'entry_price': 0.00052,  # +15% depuis première alerte
        'liquidity': 216_000,     # +20%
        'volume_24h': 3_500_000,  # +40%
        'score': 98,
        'age_hours': 0.75,  # 45 min
        'volume_acceleration_1h_vs_6h': 6.0,
        'alert_count': 5,
        'created_at': '2025-01-01 11:00:00'
    }

    targets2 = calculate_dynamic_targets(sol_multi_current, sol_multi_prev)
    print_targets_analysis(targets2, sol_multi_current, "WINNER Token (SOL) - ×5 alertes")

    # ================================================================
    # TEST 3: ETH GROS GAINS (conditions excellentes)
    # ================================================================

    print("\n" + "="*90)
    print("TEST 3: ETH - GROS GAINS POTENTIEL")
    print("="*90)

    eth_big = {
        'network': 'eth',
        'entry_price': 0.000125,
        'liquidity': 400_000,
        'volume_24h': 800_000,
        'score': 100,
        'age_hours': 2,
        'volume_acceleration_1h_vs_6h': 5.5,
        'alert_count': 2
    }

    targets3 = calculate_dynamic_targets(eth_big)
    print_targets_analysis(targets3, eth_big, "MOONSHOT Token (ETH)")

    # ================================================================
    # TEST 4: CONDITIONS DÉGRADÉES (liquidité baisse)
    # ================================================================

    print("\n" + "="*90)
    print("TEST 4: CONDITIONS DÉGRADÉES (Liquidité -25%, Prix -5%)")
    print("="*90)

    degraded_prev = [
        {'entry_price': 0.00080, 'liquidity': 200_000, 'volume_24h': 500_000, 'created_at': '2025-01-01 10:00:00'},
        {'entry_price': 0.00078, 'liquidity': 180_000, 'volume_24h': 450_000, 'created_at': '2025-01-01 10:20:00'}
    ]

    degraded_current = {
        'network': 'bsc',
        'entry_price': 0.00076,  # -5% depuis première
        'liquidity': 150_000,     # -25% 🚨
        'volume_24h': 400_000,    # -20%
        'score': 75,
        'age_hours': 0.5,
        'volume_acceleration_1h_vs_6h': 0.8,
        'alert_count': 3,
        'created_at': '2025-01-01 10:40:00'
    }

    targets4 = calculate_dynamic_targets(degraded_current, degraded_prev)
    print_targets_analysis(targets4, degraded_current, "RISKY Token (BSC)")

    print("\n" + "="*90)
    print("✅ TESTS TERMINÉS")
    print("="*90)
    print("\nUtilisation:")
    print("  from dynamic_targets_calculator import calculate_dynamic_targets")
    print("  targets = calculate_dynamic_targets(alert, previous_alerts)")
    print("\n")
