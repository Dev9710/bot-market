#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO-SCORING des signaux de trading
Score chaque nouvelle alerte de 0-100 basé sur les patterns identifiés
"""
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def calculate_signal_score(alert):
    """
    Calcule un score de signal de 0-100 pour une alerte
    Basé sur les patterns identifiés dans l'analyse

    Returns:
        tuple: (score, breakdown, recommendation)
    """

    score = 0
    breakdown = []

    # Extract data
    network = alert.get('network', '').lower()
    volume_24h = alert.get('volume_24h', 0) or 0
    liquidity = alert.get('liquidity', 0) or 0
    base_score = alert.get('score', 0) or 0
    age_hours = alert.get('age_hours', 0) or 0
    age_minutes = age_hours * 60
    accel = alert.get('volume_acceleration_1h_vs_6h', 0) or 0
    alert_count = alert.get('alert_count', 1) or 1

    # 1. RÉSEAU (25 points max)
    network_scores = {
        'solana': 25,  # Champion absolu
        'base': 20,    # Haute qualité
        'eth': 18,     # Gros gains
        'bsc': 15,     # Bon
        'arbitrum': 12 # Correct
    }
    network_score = network_scores.get(network, 10)
    score += network_score
    breakdown.append(f"Réseau {network.upper()}: +{network_score}")

    # 2. ZONE DE VOLUME OPTIMALE (20 points max)
    volume_score = 0
    if network == 'solana':
        if 1_000_000 <= volume_24h <= 5_000_000:
            volume_score = 20  # Zone optimale identifiée
            breakdown.append(f"Volume OPTIMAL (1M-5M): +20")
        elif volume_24h > 5_000_000:
            volume_score = 15
            breakdown.append(f"Volume >5M: +15")
        elif 100_000 <= volume_24h < 1_000_000:
            volume_score = 10
            breakdown.append(f"Volume 100K-1M: +10")
    elif network == 'base':
        if 100_000 <= volume_24h <= 500_000:
            volume_score = 20
            breakdown.append(f"Volume OPTIMAL (100K-500K): +20")
        elif 500_000 < volume_24h <= 1_000_000:
            volume_score = 15
            breakdown.append(f"Volume 500K-1M: +15")
    elif network == 'eth':
        if 200_000 <= volume_24h <= 500_000:
            volume_score = 20
            breakdown.append(f"Volume OPTIMAL (200K-500K): +20")
        elif volume_24h > 500_000:
            volume_score = 15
            breakdown.append(f"Volume >500K: +15")
    else:
        if volume_24h >= 100_000:
            volume_score = 15
            breakdown.append(f"Volume ≥100K: +15")

    score += volume_score

    # 3. LIQUIDITÉ (15 points max)
    liq_score = 0
    if network == 'solana':
        if liquidity < 200_000:
            liq_score = 15  # Zone optimale
            breakdown.append(f"Liquidité <200K (optimal): +15")
        elif 200_000 <= liquidity < 500_000:
            liq_score = 10
            breakdown.append(f"Liquidité 200K-500K: +10")
    elif network in ['base', 'bsc', 'eth']:
        if 100_000 <= liquidity <= 500_000:
            liq_score = 15
            breakdown.append(f"Liquidité 100K-500K (optimal): +15")
        elif 500_000 < liquidity <= 2_000_000:
            liq_score = 12
            breakdown.append(f"Liquidité 500K-2M: +12")
        elif liquidity > 2_000_000:
            liq_score = 10
            breakdown.append(f"Liquidité >2M: +10")
    else:
        if liquidity >= 100_000:
            liq_score = 12
            breakdown.append(f"Liquidité ≥100K: +12")

    score += liq_score

    # 4. FRESHNESS (15 points max)
    fresh_score = 0
    if age_minutes < 5:
        fresh_score = 15  # ULTRA-FRESH
        breakdown.append(f"ULTRA-FRESH (<5min): +15 🔥")
    elif age_minutes < 30:
        fresh_score = 12
        breakdown.append(f"FRESH (<30min): +12")
    elif age_hours < 1:
        fresh_score = 8
        breakdown.append(f"Récent (<1h): +8")
    elif age_hours < 6:
        fresh_score = 5
        breakdown.append(f"Actif (<6h): +5")

    score += fresh_score

    # 5. SCORE DE BASE (10 points max)
    if base_score >= 95:
        base_pts = 10
        breakdown.append(f"Score ULTRA_HIGH (≥95): +10")
    elif base_score >= 85:
        base_pts = 8
        breakdown.append(f"Score HIGH (≥85): +8")
    elif base_score >= 75:
        base_pts = 6
        breakdown.append(f"Score MEDIUM (≥75): +6")
    elif base_score >= 60:
        base_pts = 4
        breakdown.append(f"Score acceptable (≥60): +4")
    else:
        base_pts = 0
        breakdown.append(f"Score faible (<60): +0")

    score += base_pts

    # 6. ACCÉLÉRATION (10 points max)
    accel_score = 0
    if accel >= 6:
        accel_score = 10
        breakdown.append(f"Accélération ≥6x: +10 🚀")
    elif accel >= 5:
        accel_score = 8
        breakdown.append(f"Accélération ≥5x: +8")
    elif accel >= 2:
        accel_score = 5
        breakdown.append(f"Accélération ≥2x: +5")
    elif accel >= 1:
        accel_score = 3
        breakdown.append(f"Accélération normale: +3")

    score += accel_score

    # 7. ALERTES MULTIPLES (BONUS 15 points)
    multi_score = 0
    if alert_count >= 10:
        multi_score = 15
        breakdown.append(f"ALERTES MULTIPLES (×{alert_count}): +15 🔥🔥🔥")
    elif alert_count >= 5:
        multi_score = 12
        breakdown.append(f"Alertes multiples (×{alert_count}): +12 🔥🔥")
    elif alert_count >= 2:
        multi_score = 8
        breakdown.append(f"Alertes multiples (×{alert_count}): +8 🔥")

    score += multi_score

    # TOTAL MAX = 110 points (normalisé à 100)
    score = min(100, score)

    # Recommandation
    if score >= 85:
        action = "🟢 STRONG BUY"
        position = "10% capital (MAX)"
        confidence = "95%+"
    elif score >= 70:
        action = "🟢 BUY"
        position = "7% capital"
        confidence = "85%+"
    elif score >= 55:
        action = "🟡 CONSIDER"
        position = "5% capital"
        confidence = "70%+"
    elif score >= 40:
        action = "🟡 WATCH"
        position = "3% capital (prudent)"
        confidence = "50%+"
    else:
        action = "🔴 SKIP"
        position = "0% - Ne pas trader"
        confidence = "<50%"

    recommendation = {
        'action': action,
        'position': position,
        'confidence': confidence,
        'score': score
    }

    return score, breakdown, recommendation

def print_signal_analysis(alert):
    """Affiche l'analyse complète d'un signal"""

    score, breakdown, rec = calculate_signal_score(alert)

    print(f"\n{'='*80}")
    print(f"🎯 ANALYSE DE SIGNAL")
    print(f"{'='*80}\n")

    # Token Info
    token_name = alert.get('token_name', 'Unknown').split('/')[0]
    network = alert.get('network', 'unknown').upper()

    print(f"Token: {token_name}")
    print(f"Réseau: {network}")
    print(f"Pool: {alert.get('token_address', 'N/A')[:20]}...")

    print(f"\n{'─'*80}")
    print(f"📊 DÉTAILS DU SCORING:\n")

    for line in breakdown:
        print(f"   {line}")

    print(f"\n{'─'*80}")
    print(f"🎯 SCORE FINAL: {score}/100\n")

    print(f"{'─'*80}")
    print(f"💡 RECOMMANDATION:\n")
    print(f"   Action:     {rec['action']}")
    print(f"   Position:   {rec['position']}")
    print(f"   Confiance:  {rec['confidence']}")

    print(f"\n{'─'*80}")

    # Additional context
    if score >= 85:
        print(f"\n✅ EXCELLENT SIGNAL!")
        print(f"   • Entry immédiat recommandé")
        print(f"   • Stop loss: -10%")
        print(f"   • TP1: +5% (sortir 50%)")
        print(f"   • Probabilité succès: {rec['confidence']}")
    elif score >= 70:
        print(f"\n✅ BON SIGNAL")
        print(f"   • Entry recommandé")
        print(f"   • Suivre checklist standard")
        print(f"   • Surveiller évolution")
    elif score >= 55:
        print(f"\n🟡 SIGNAL MOYEN")
        print(f"   • Entry possible mais prudent")
        print(f"   • Réduire position size")
        print(f"   • Stop loss strict")
    else:
        print(f"\n⚠️  SIGNAL FAIBLE")
        print(f"   • Éviter ce trade")
        print(f"   • Attendre meilleur signal")

    print(f"\n{'='*80}\n")

    return score, rec

# Example usage
if __name__ == "__main__":

    print("📊 AUTO-SCORING DES SIGNAUX DE TRADING\n")
    print("Basé sur l'analyse de 4252 alertes réelles\n")

    # Test avec différents profils

    # Profile 1: SOLANA OPTIMAL
    print("\n" + "="*80)
    print("TEST 1: SOLANA ZONE OPTIMALE")
    print("="*80)

    solana_optimal = {
        'network': 'solana',
        'token_name': 'TEST / SOL',
        'token_address': '0x123...',
        'volume_24h': 2_500_000,  # 2.5M (dans zone 1M-5M)
        'liquidity': 180_000,      # <200K optimal
        'score': 95,               # ULTRA_HIGH
        'age_hours': 0.05,         # 3 minutes
        'volume_acceleration_1h_vs_6h': 6.0,
        'alert_count': 1
    }

    print_signal_analysis(solana_optimal)

    # Profile 2: SOLANA AVEC ALERTES MULTIPLES
    print("\n" + "="*80)
    print("TEST 2: SOLANA AVEC ALERTES MULTIPLES")
    print("="*80)

    solana_multi = {
        'network': 'solana',
        'token_name': 'WINNER / SOL',
        'token_address': '0x456...',
        'volume_24h': 3_000_000,
        'liquidity': 150_000,
        'score': 85,
        'age_hours': 0.08,  # 5 minutes
        'volume_acceleration_1h_vs_6h': 6.0,
        'alert_count': 5  # MULTIPLE ALERTS 🔥
    }

    print_signal_analysis(solana_multi)

    # Profile 3: ETH GROS GAINS
    print("\n" + "="*80)
    print("TEST 3: ETH ZONE GROS GAINS")
    print("="*80)

    eth_big = {
        'network': 'eth',
        'token_name': 'MOONSHOT / WETH',
        'token_address': '0x789...',
        'volume_24h': 400_000,
        'liquidity': 300_000,
        'score': 100,
        'age_hours': 2,  # 2h (plus mature)
        'volume_acceleration_1h_vs_6h': 5.0,
        'alert_count': 2
    }

    print_signal_analysis(eth_big)

    # Profile 4: BASE HAUTE QUALITÉ
    print("\n" + "="*80)
    print("TEST 4: BASE HAUTE QUALITÉ")
    print("="*80)

    base_quality = {
        'network': 'base',
        'token_name': 'SOLID / WETH',
        'token_address': '0xabc...',
        'volume_24h': 300_000,
        'liquidity': 250_000,
        'score': 95,
        'age_hours': 0.3,  # 18 minutes
        'volume_acceleration_1h_vs_6h': 6.0,
        'alert_count': 1
    }

    print_signal_analysis(base_quality)

    # Profile 5: SIGNAL FAIBLE (à éviter)
    print("\n" + "="*80)
    print("TEST 5: SIGNAL FAIBLE (À ÉVITER)")
    print("="*80)

    weak_signal = {
        'network': 'bsc',
        'token_name': 'WEAK / BNB',
        'token_address': '0xdef...',
        'volume_24h': 50_000,      # Volume trop faible
        'liquidity': 30_000,        # Liquidité faible
        'score': 65,                # Score moyen
        'age_hours': 12,            # Trop vieux
        'volume_acceleration_1h_vs_6h': 0.5,  # Pas d'accélération
        'alert_count': 1
    }

    print_signal_analysis(weak_signal)

    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80)
    print("\nUtilisation:")
    print("  from auto_score_signal import calculate_signal_score")
    print("  score, breakdown, rec = calculate_signal_score(alert)")
    print("\n")
