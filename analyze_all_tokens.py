#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse complète de TOUS les tokens détectés
Trouve les patterns des meilleurs scores par blockchain
"""
import sqlite3
import os
import sys
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Find the database
DB_PATH = os.getenv("DB_PATH")
if not DB_PATH:
    if os.path.exists("alerts_tracker.db"):
        DB_PATH = "alerts_tracker.db"
    elif os.path.exists("alerts_history.db"):
        DB_PATH = "alerts_history.db"
    else:
        print("❌ ERROR: Database not found!")
        exit(1)

print(f"📊 Analyse des tokens détectés\n")
print(f"Database: {DB_PATH}\n")

def get_top_tokens(conn, network=None, limit=15):
    """Récupère les top tokens par score pour un réseau"""

    query = """
        SELECT
            token_name,
            token_address,
            network,
            score,
            base_score,
            momentum_bonus,
            confidence_score,
            liquidity,
            volume_24h,
            volume_6h,
            volume_1h,
            age_hours,
            buy_ratio,
            volume_acceleration_1h_vs_6h,
            entry_price,
            tp1_percent,
            tp2_percent,
            tp3_percent,
            created_at
        FROM alerts
        {}
        ORDER BY score DESC, liquidity DESC
        LIMIT ?
    """.format("WHERE network = ?" if network else "")

    params = [network, limit] if network else [limit]
    cursor = conn.execute(query, params)

    return cursor.fetchall()

def analyze_patterns(tokens, network_name):
    """Analyse les patterns communs des top scorers"""

    print(f"\n{'='*100}")
    print(f"🎯 ANALYSE: {network_name.upper()}")
    print(f"{'='*100}\n")

    if not tokens:
        print("❌ Aucun token trouvé\n")
        return None

    print(f"📊 TOP {len(tokens)} TOKENS (par score):\n")
    print(f"{'#':<3} {'Token':<25} {'Score':<7} {'Tier':<12} {'Liq':<12} {'Vol 24h':<12} {'Age':<10} {'Accel':<8}")
    print("─" * 100)

    patterns = {
        'score_distribution': defaultdict(int),
        'liquidity_range': [],
        'volume_range': [],
        'age_distribution': [],
        'momentum_distribution': [],
        'acceleration_distribution': [],
        'buy_ratio_distribution': [],
        'tp_targets': {'tp1': [], 'tp2': [], 'tp3': []}
    }

    for i, token in enumerate(tokens, 1):
        # Determine tier
        score = token['score']
        if score >= 95:
            tier = 'ULTRA_HIGH'
        elif score >= 85:
            tier = 'HIGH'
        elif score >= 75:
            tier = 'MEDIUM'
        else:
            tier = 'LOW'

        patterns['score_distribution'][tier] += 1

        token_name = token['token_name'].split('/')[0] if token['token_name'] else 'Unknown'
        liq = token['liquidity'] or 0
        vol = token['volume_24h'] or 0
        age_min = (token['age_hours'] or 0) * 60
        accel = token['volume_acceleration_1h_vs_6h'] or 0

        # Print token
        print(f"{i:<3} {token_name[:24]:<25} "
              f"{score:<7} "
              f"{tier:<12} "
              f"${liq/1000:>7.0f}K   "
              f"${vol/1000:>7.0f}K   "
              f"{age_min:>6.0f}min "
              f"{accel:>6.1f}x")

        # Collect patterns
        patterns['liquidity_range'].append(liq)
        patterns['volume_range'].append(vol)
        patterns['age_distribution'].append(age_min)

        if token['momentum_bonus']:
            patterns['momentum_distribution'].append(token['momentum_bonus'])

        if accel:
            patterns['acceleration_distribution'].append(accel)

        if token['buy_ratio']:
            patterns['buy_ratio_distribution'].append(token['buy_ratio'])

        if token['tp1_percent']:
            patterns['tp_targets']['tp1'].append(token['tp1_percent'])
        if token['tp2_percent']:
            patterns['tp_targets']['tp2'].append(token['tp2_percent'])
        if token['tp3_percent']:
            patterns['tp_targets']['tp3'].append(token['tp3_percent'])

    print("\n" + "─" * 100)

    # Statistical Analysis
    print(f"\n🔍 PATTERNS IDENTIFIÉS:\n")

    # Score distribution
    print(f"  📊 DISTRIBUTION DES TIERS:")
    total = len(tokens)
    for tier in ['ULTRA_HIGH', 'HIGH', 'MEDIUM', 'LOW']:
        count = patterns['score_distribution'][tier]
        pct = (count/total)*100 if total > 0 else 0
        print(f"     • {tier:12}: {count}/{total} ({pct:.0f}%)")

    # Liquidity
    if patterns['liquidity_range']:
        liq_sorted = sorted([l for l in patterns['liquidity_range'] if l > 0])
        if liq_sorted:
            print(f"\n  💰 LIQUIDITÉ:")
            print(f"     • Moyenne: ${sum(liq_sorted)/len(liq_sorted)/1000:.0f}K")
            print(f"     • Médiane: ${liq_sorted[len(liq_sorted)//2]/1000:.0f}K")
            print(f"     • Min: ${min(liq_sorted)/1000:.0f}K")
            print(f"     • Max: ${max(liq_sorted)/1000:.0f}K")
            # Sweet spot analysis
            over_50k = sum(1 for l in liq_sorted if l >= 50000)
            over_100k = sum(1 for l in liq_sorted if l >= 100000)
            print(f"     • ≥$50K: {over_50k}/{len(liq_sorted)} ({over_50k/len(liq_sorted)*100:.0f}%)")
            print(f"     • ≥$100K: {over_100k}/{len(liq_sorted)} ({over_100k/len(liq_sorted)*100:.0f}%)")

    # Volume
    if patterns['volume_range']:
        vol_sorted = sorted([v for v in patterns['volume_range'] if v > 0])
        if vol_sorted:
            print(f"\n  📈 VOLUME 24H:")
            print(f"     • Moyenne: ${sum(vol_sorted)/len(vol_sorted)/1000:.0f}K")
            print(f"     • Médiane: ${vol_sorted[len(vol_sorted)//2]/1000:.0f}K")
            over_100k = sum(1 for v in vol_sorted if v >= 100000)
            print(f"     • ≥$100K: {over_100k}/{len(vol_sorted)} ({over_100k/len(vol_sorted)*100:.0f}%)")

    # Age
    if patterns['age_distribution']:
        age_sorted = sorted([a for a in patterns['age_distribution'] if a >= 0])
        print(f"\n  ⏰ ÂGE À LA DÉTECTION:")
        print(f"     • Moyenne: {sum(age_sorted)/len(age_sorted):.0f} minutes")
        print(f"     • Médiane: {age_sorted[len(age_sorted)//2]:.0f} minutes")
        under_5 = sum(1 for a in age_sorted if a < 5)
        under_30 = sum(1 for a in age_sorted if a < 30)
        under_60 = sum(1 for a in age_sorted if a < 60)
        print(f"     • <5min:  {under_5}/{len(age_sorted)} ({under_5/len(age_sorted)*100:.0f}%)")
        print(f"     • <30min: {under_30}/{len(age_sorted)} ({under_30/len(age_sorted)*100:.0f}%)")
        print(f"     • <1h:    {under_60}/{len(age_sorted)} ({under_60/len(age_sorted)*100:.0f}%)")

    # Momentum
    if patterns['momentum_distribution']:
        mom_sorted = sorted(patterns['momentum_distribution'])
        print(f"\n  🚀 MOMENTUM BONUS:")
        print(f"     • Moyenne: +{sum(mom_sorted)/len(mom_sorted):.1f} points")
        print(f"     • Max: +{max(mom_sorted):.0f} points")

    # Acceleration
    if patterns['acceleration_distribution']:
        accel_sorted = sorted([a for a in patterns['acceleration_distribution'] if a > 0])
        if accel_sorted:
            print(f"\n  ⚡ ACCÉLÉRATION VOLUME (1h vs 6h):")
            print(f"     • Moyenne: {sum(accel_sorted)/len(accel_sorted):.1f}x")
            print(f"     • Médiane: {accel_sorted[len(accel_sorted)//2]:.1f}x")
            over_2x = sum(1 for a in accel_sorted if a >= 2)
            over_5x = sum(1 for a in accel_sorted if a >= 5)
            print(f"     • ≥2x: {over_2x}/{len(accel_sorted)} ({over_2x/len(accel_sorted)*100:.0f}%)")
            print(f"     • ≥5x: {over_5x}/{len(accel_sorted)} ({over_5x/len(accel_sorted)*100:.0f}%)")

    # Buy Ratio
    if patterns['buy_ratio_distribution']:
        buy_sorted = sorted(patterns['buy_ratio_distribution'])
        print(f"\n  ✅ BUY RATIO:")
        print(f"     • Moyenne: {sum(buy_sorted)/len(buy_sorted):.1%}")
        print(f"     • Médiane: {buy_sorted[len(buy_sorted)//2]:.1%}")

    # TP Targets
    print(f"\n  🎯 TARGETS RECOMMANDÉS:")
    if patterns['tp_targets']['tp1']:
        avg_tp1 = sum(patterns['tp_targets']['tp1'])/len(patterns['tp_targets']['tp1'])
        print(f"     • TP1: +{avg_tp1:.0f}%")
    if patterns['tp_targets']['tp2']:
        avg_tp2 = sum(patterns['tp_targets']['tp2'])/len(patterns['tp_targets']['tp2'])
        print(f"     • TP2: +{avg_tp2:.0f}%")
    if patterns['tp_targets']['tp3']:
        avg_tp3 = sum(patterns['tp_targets']['tp3'])/len(patterns['tp_targets']['tp3'])
        print(f"     • TP3: +{avg_tp3:.0f}%")

    return patterns

def generate_trading_rules(all_patterns):
    """Génère des règles de trading basées sur les patterns réels"""

    print(f"\n\n{'='*100}")
    print("🎯 STRATÉGIE DE TRADING OPTIMALE (Basée sur vos données réelles)")
    print(f"{'='*100}\n")

    # Aggregate stats
    all_liq = []
    all_vol = []
    all_ages = []
    all_scores = []
    tier_dist = defaultdict(int)

    for network, patterns in all_patterns.items():
        if patterns:
            all_liq.extend(patterns['liquidity_range'])
            all_vol.extend(patterns['volume_range'])
            all_ages.extend(patterns['age_distribution'])
            for tier, count in patterns['score_distribution'].items():
                tier_dist[tier] += count

    # Filter out zeros
    all_liq = [l for l in all_liq if l > 0]
    all_vol = [v for v in all_vol if v > 0]
    all_ages = [a for a in all_ages if a >= 0]

    print("✅ RÈGLES D'ENTRY (Niveau de confiance par blockchain):\n")

    print("  📋 CHECKLIST PRÉ-TRADE:\n")

    if all_liq:
        median_liq = sorted(all_liq)[len(all_liq)//2]
        p75_liq = sorted(all_liq)[int(len(all_liq)*0.75)]
        print(f"     1. LIQUIDITÉ:")
        print(f"        • Minimum absolu: >${median_liq/1000:.0f}K (médiane)")
        print(f"        • Recommandé: >${p75_liq/1000:.0f}K (top 25%)")

    if all_vol:
        median_vol = sorted(all_vol)[len(all_vol)//2]
        print(f"\n     2. VOLUME 24H:")
        print(f"        • Minimum: >${median_vol/1000:.0f}K (médiane)")

    total_tokens = sum(tier_dist.values())
    ultra_high_pct = (tier_dist['ULTRA_HIGH']/total_tokens)*100 if total_tokens > 0 else 0
    high_pct = (tier_dist['HIGH']/total_tokens)*100 if total_tokens > 0 else 0

    print(f"\n     3. SCORE:")
    print(f"        • ULTRA_HIGH (≥95): {ultra_high_pct:.0f}% des détections ⭐⭐⭐")
    print(f"        • HIGH (≥85): {high_pct:.0f}% des détections ⭐⭐")
    print(f"        → Privilégier uniquement ULTRA_HIGH & HIGH")

    if all_ages:
        median_age = sorted(all_ages)[len(all_ages)//2]
        under_30 = sum(1 for a in all_ages if a < 30)
        fresh_pct = (under_30/len(all_ages))*100
        print(f"\n     4. FRESHNESS (ÂGE):")
        print(f"        • {fresh_pct:.0f}% des tokens détectés à <30min")
        print(f"        • Médiane: {median_age:.0f} minutes")
        print(f"        → Agir rapidement sur les <30min signals")

    print(f"\n\n  💡 STRATÉGIES PAR BLOCKCHAIN:\n")

    for network, patterns in all_patterns.items():
        if not patterns:
            continue

        liq_data = [l for l in patterns['liquidity_range'] if l > 0]
        age_data = [a for a in patterns['age_distribution'] if a >= 0]

        if liq_data and age_data:
            med_liq = sorted(liq_data)[len(liq_data)//2]
            med_age = sorted(age_data)[len(age_data)//2]
            ultra_high = patterns['score_distribution']['ULTRA_HIGH']
            total = sum(patterns['score_distribution'].values())
            quality_pct = (ultra_high/total)*100 if total > 0 else 0

            print(f"     {network.upper():10} → Liq médiane: ${med_liq/1000:>6.0f}K | Âge médian: {med_age:>4.0f}min | ULTRA_HIGH: {quality_pct:.0f}%")

    print(f"\n\n  🎲 GESTION DU RISQUE:\n")
    print(f"     • Position size max: 3-5% du capital par trade")
    print(f"     • Stop loss: -10% strict (non négociable)")
    print(f"     • Take profit partiel (50%) à TP1")
    print(f"     • Trail stop sur le reste après TP1")
    print(f"     • Maximum 3-5 positions ouvertes simultanément")

    print(f"\n  ⚡ SIGNAUX D'ACTION:\n")
    print(f"     🟢 ENTRY si:")
    print(f"        - Score ≥90 (ULTRA_HIGH ou HIGH top)")
    print(f"        - Liquidity > médiane réseau")
    print(f"        - Age <30min (privilégier <5min)")
    print(f"        - Volume croissant (si accel >2x = bonus)")
    print(f"\n     🔴 EXIT immédiat si:")
    print(f"        - Liquidity baisse de >20%")
    print(f"        - Volume s'effondre")
    print(f"        - Stop loss touché (-10%)")
    print(f"\n     🟡 EXIT partiel si:")
    print(f"        - TP1 atteint (+20-30%)")
    print(f"        - 6h écoulées sans nouveau momentum")

    print(f"\n{'─'*100}\n")

def main():
    """Main analysis"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get total stats
    cursor = conn.execute("SELECT COUNT(*) as total, COUNT(DISTINCT network) as networks FROM alerts")
    stats = cursor.fetchone()
    print(f"📈 Total alertes: {stats['total']}")
    print(f"🌍 Réseaux actifs: {stats['networks']}\n")

    networks = ['eth', 'base', 'bsc', 'solana', 'polygon_pos', 'avax']

    all_patterns = {}

    # Analyze each network
    for network in networks:
        tokens = get_top_tokens(conn, network, limit=15)
        if tokens:
            patterns = analyze_patterns(tokens, network)
            all_patterns[network] = patterns

    # Global analysis
    print(f"\n\n{'='*100}")
    print("🌍 ANALYSE GLOBALE (TOP 20 TOUS RÉSEAUX)")
    print(f"{'='*100}")

    all_tokens = get_top_tokens(conn, network=None, limit=20)
    if all_tokens:
        global_patterns = analyze_patterns(all_tokens, "GLOBAL")
        all_patterns['GLOBAL'] = global_patterns

    # Generate trading rules
    generate_trading_rules(all_patterns)

    conn.close()

    print("\n✅ Analyse terminée!\n")

if __name__ == "__main__":
    main()
