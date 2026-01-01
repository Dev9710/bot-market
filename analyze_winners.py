#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse des patterns de tokens gagnants par blockchain
Extrait les top 10 performers par réseau et identifie les patterns communs
"""
import sqlite3
import os
import sys
from collections import defaultdict
import json

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

print(f"📊 Using database: {DB_PATH}\n")

def analyze_token_performance(conn, network=None):
    """
    Analyse les tokens avec alertes multiples (indicateur de performance)
    Les tokens qui déclenchent plusieurs alertes ont généralement performé
    """

    query = """
        SELECT
            token_address,
            token_name,
            network,
            COUNT(*) as alert_count,
            MIN(created_at) as first_alert,
            MAX(created_at) as last_alert,
            AVG(score) as avg_score,
            MAX(score) as max_score,
            MIN(score) as min_score,
            AVG(liquidity) as avg_liquidity,
            MAX(liquidity) as max_liquidity,
            AVG(volume_24h) as avg_volume,
            MAX(volume_24h) as max_volume,
            MIN(age_hours) as min_age,
            AVG(base_score) as avg_base_score,
            AVG(momentum_bonus) as avg_momentum,
            AVG(confidence_score) as avg_confidence,
            AVG(volume_acceleration_1h_vs_6h) as avg_acceleration
        FROM alerts
        {}
        GROUP BY token_address
        HAVING alert_count >= 2
        ORDER BY alert_count DESC, max_score DESC
        LIMIT 10
    """.format("WHERE network = ?" if network else "")

    params = [network] if network else []
    cursor = conn.execute(query, params)

    return cursor.fetchall()

def extract_patterns(tokens):
    """Extrait les patterns communs des top performers"""

    patterns = {
        'score_range': [],
        'liquidity_range': [],
        'volume_range': [],
        'age_at_first_alert': [],
        'alert_frequency': [],
        'score_evolution': [],
        'liquidity_evolution': [],
        'common_traits': defaultdict(int)
    }

    for token in tokens:
        alert_count = token['alert_count']
        avg_score = token['avg_score']
        max_score = token['max_score']
        min_score = token['min_score']
        avg_liq = token['avg_liquidity']
        max_liq = token['max_liquidity']
        min_age = token['min_age']

        # Score patterns
        patterns['score_range'].append({
            'avg': avg_score,
            'max': max_score,
            'min': min_score,
            'progression': max_score - min_score
        })

        # Liquidity patterns
        if avg_liq and max_liq:
            patterns['liquidity_range'].append({
                'avg': avg_liq,
                'max': max_liq,
                'growth': (max_liq / avg_liq * 100) if avg_liq > 0 else 0
            })

        # Age at first detection
        patterns['age_at_first_alert'].append(min_age)

        # Alert frequency (nombre d'alertes)
        patterns['alert_frequency'].append(alert_count)

        # Categorize common traits
        if avg_score >= 95:
            patterns['common_traits']['ULTRA_HIGH_score'] += 1
        elif avg_score >= 85:
            patterns['common_traits']['HIGH_score'] += 1

        if avg_liq and avg_liq > 100000:
            patterns['common_traits']['high_liquidity_100k+'] += 1
        elif avg_liq and avg_liq > 50000:
            patterns['common_traits']['medium_liquidity_50k+'] += 1

        if min_age and min_age < 0.083:  # <5min
            patterns['common_traits']['ultra_fresh'] += 1
        elif min_age and min_age < 0.5:  # <30min
            patterns['common_traits']['very_fresh'] += 1

        if alert_count >= 5:
            patterns['common_traits']['multiple_alerts_5+'] += 1
        elif alert_count >= 3:
            patterns['common_traits']['multiple_alerts_3+'] += 1

    return patterns

def print_analysis(network, tokens, patterns):
    """Affiche l'analyse formatée"""

    print(f"\n{'='*80}")
    print(f"🎯 ANALYSE: {network.upper() if network else 'ALL NETWORKS'}")
    print(f"{'='*80}\n")

    if not tokens:
        print("❌ Aucun token avec performances multiples trouvé\n")
        return

    # Top performers
    print(f"📈 TOP {len(tokens)} PERFORMERS (Multiple Alerts = Performance Confirmée):\n")
    for i, token in enumerate(tokens, 1):
        token_name = token['token_name'].split('/')[0] if token['token_name'] else 'Unknown'
        print(f"  {i}. {token_name[:20]:20} | "
              f"Alerts: ×{token['alert_count']:2} | "
              f"Score: {token['min_score']:.0f}→{token['max_score']:.0f} (avg:{token['avg_score']:.1f}) | "
              f"Liq: ${token['avg_liquidity']/1000:.0f}K | "
              f"Age: {token['min_age']*60:.0f}min")

    print(f"\n{'─'*80}\n")

    # Pattern Analysis
    print("🔍 PATTERNS IDENTIFIÉS:\n")

    # Score patterns
    if patterns['score_range']:
        avg_scores = [p['avg'] for p in patterns['score_range']]
        avg_progression = [p['progression'] for p in patterns['score_range']]
        print(f"  📊 SCORE:")
        print(f"     • Score moyen au lancement: {sum(avg_scores)/len(avg_scores):.1f}")
        print(f"     • Progression moyenne: +{sum(avg_progression)/len(avg_progression):.1f} points")
        print(f"     • Range: {min(s['min'] for s in patterns['score_range']):.0f} - {max(s['max'] for s in patterns['score_range']):.0f}")

    # Liquidity patterns
    if patterns['liquidity_range']:
        avg_liq = [p['avg'] for p in patterns['liquidity_range']]
        avg_growth = [p['growth'] for p in patterns['liquidity_range'] if p['growth'] > 0]
        print(f"\n  💰 LIQUIDITÉ:")
        print(f"     • Liquidité moyenne: ${sum(avg_liq)/len(avg_liq)/1000:.0f}K")
        if avg_growth:
            print(f"     • Croissance moyenne: +{sum(avg_growth)/len(avg_growth):.0f}%")

    # Age patterns
    if patterns['age_at_first_alert']:
        avg_age_min = sum(patterns['age_at_first_alert'])/len(patterns['age_at_first_alert']) * 60
        print(f"\n  ⏰ ÂGE À LA DÉTECTION:")
        print(f"     • Âge moyen au 1er signal: {avg_age_min:.0f} minutes")
        under_5min = sum(1 for age in patterns['age_at_first_alert'] if age < 0.083)
        under_30min = sum(1 for age in patterns['age_at_first_alert'] if age < 0.5)
        print(f"     • <5min: {under_5min}/{len(patterns['age_at_first_alert'])} ({under_5min/len(patterns['age_at_first_alert'])*100:.0f}%)")
        print(f"     • <30min: {under_30min}/{len(patterns['age_at_first_alert'])} ({under_30min/len(patterns['age_at_first_alert'])*100:.0f}%)")

    # Alert frequency
    if patterns['alert_frequency']:
        avg_alerts = sum(patterns['alert_frequency'])/len(patterns['alert_frequency'])
        print(f"\n  🔔 FRÉQUENCE ALERTES:")
        print(f"     • Nombre moyen d'alertes: {avg_alerts:.1f}")
        print(f"     • Max: {max(patterns['alert_frequency'])}")

    # Common traits
    print(f"\n  ✅ TRAITS COMMUNS (sur {len(tokens)} tokens):")
    total = len(tokens)
    for trait, count in sorted(patterns['common_traits'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count/total)*100
        print(f"     • {trait.replace('_', ' ').title()}: {count}/{total} ({percentage:.0f}%)")

    print(f"\n{'─'*80}\n")

def generate_strategy(all_patterns):
    """Génère une stratégie basée sur les patterns réels"""

    print(f"\n{'='*80}")
    print("🎯 STRATÉGIE RECOMMANDÉE BASÉE SUR VOS DONNÉES RÉELLES")
    print(f"{'='*80}\n")

    print("✅ CRITÈRES D'ENTRY (validés par vos top performers):\n")

    # Aggregate patterns across networks
    all_scores = []
    all_liq = []
    all_ages = []
    all_traits = defaultdict(int)

    for network, patterns in all_patterns.items():
        all_scores.extend([s['avg'] for s in patterns['score_range']])
        all_liq.extend([l['avg'] for l in patterns['liquidity_range']])
        all_ages.extend(patterns['age_at_first_alert'])
        for trait, count in patterns['common_traits'].items():
            all_traits[trait] += count

    if all_scores:
        min_score = min(all_scores)
        avg_score = sum(all_scores)/len(all_scores)
        print(f"  1️⃣  SCORE: ≥{min_score:.0f} (idéal: ≥{avg_score:.0f})")

    if all_liq:
        avg_liq_val = sum(all_liq)/len(all_liq)
        print(f"  2️⃣  LIQUIDITÉ: ≥${avg_liq_val/1000:.0f}K")

    if all_ages:
        avg_age_min = (sum(all_ages)/len(all_ages)) * 60
        fresh_ratio = sum(1 for a in all_ages if a < 0.5) / len(all_ages) * 100
        print(f"  3️⃣  ÂGE: <30 minutes ({fresh_ratio:.0f}% des winners)")
        print(f"            Âge moyen optimal: {avg_age_min:.0f}min")

    print(f"\n  4️⃣  ALERTES MULTIPLES:")
    print(f"      • Si ×2+ alertes ET score en hausse = FORT signal bullish")
    print(f"      • Pattern répétitif = token en momentum")

    print(f"\n  5️⃣  ÉVOLUTION:")
    print(f"      • Surveiller croissance liquidité (bon signe)")
    print(f"      • Score qui monte = momentum confirmé")

    print("\n📝 RÈGLES DE TRADING:\n")
    print("  ✓ Entre uniquement si TOUS les critères ci-dessus sont validés")
    print("  ✓ Si alerte multiple (×2+): augmente position size de 50%")
    print("  ✓ Si score monte entre alertes: signal très bullish")
    print("  ✓ Si liquidity baisse: EXIT immédiat (rug warning)")
    print("  ✓ Toujours sortir 50% à TP1 (+20-30%)")

    print(f"\n{'─'*80}\n")

def main():
    """Main analysis function"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    networks = ['eth', 'base', 'bsc', 'solana', 'polygon_pos', 'avax']

    all_patterns = {}

    # Analyze each network
    for network in networks:
        tokens = analyze_token_performance(conn, network)
        if tokens:
            patterns = extract_patterns(tokens)
            all_patterns[network] = patterns
            print_analysis(network, tokens, patterns)

    # Global analysis
    print("\n" + "="*80)
    print("🌍 ANALYSE GLOBALE (TOUS RÉSEAUX)")
    print("="*80)

    all_tokens = analyze_token_performance(conn)
    if all_tokens:
        global_patterns = extract_patterns(all_tokens)
        print_analysis(None, all_tokens, global_patterns)

    # Generate strategy
    if all_patterns:
        generate_strategy(all_patterns)

    conn.close()

    print("\n✅ Analyse terminée!\n")

if __name__ == "__main__":
    main()
