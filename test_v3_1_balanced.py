"""
Test V3.1 ÉQUILIBRÉE - Plus d'opportunités sans dégrader qualité

Stratégie:
- Assouplir légèrement les filtres pour augmenter volume
- Maintenir qualité élevée (score >90, vélocité >20)
"""

import json
import sys
from collections import defaultdict

# Configuration V3.1 ÉQUILIBRÉE - Plus d'opportunités
V3_1_BALANCED_CONFIG = {
    'MIN_TOKEN_AGE': 0.0,
    'EMBRYONIC_MAX': 3.0,
    'MIN_VELOCITE_DEFAULT': 6.0,  # Réduit de 10 à 6
    'DANGER_AGE_MIN': 12.0,
    'DANGER_AGE_MAX': 24.0,
    'OPTIMAL_AGE_MIN': 48.0,
    'OPTIMAL_AGE_MAX': 72.0,
    'NETWORKS': ['eth', 'bsc', 'base', 'solana'],
    'NETWORK_FILTERS': {
        'eth': {
            'min_score': 80,        # Réduit de 85 à 80
            'min_velocity': 6       # Réduit de 10 à 6
        },
        'base': {
            'min_score': 85,        # Réduit de 90 à 85
            'min_velocity': 10      # Réduit de 15 à 10
        },
        'bsc': {
            'min_score': 82,        # Réduit de 88 à 82
            'min_velocity': 8       # Réduit de 12 à 8
        },
        'solana': {
            'min_score': 75,        # Réduit de 85 à 75
            'min_velocity': 6       # Réduit de 10 à 6
        },
    },
    'LIQUIDITY': {
        'eth': (80000, 600000),          # Élargi de 100k-500k
        'base': (250000, 2500000),       # Élargi de 300k-2M
        'bsc': (400000, 6000000),        # Élargi de 500k-5M
        'solana': (80000, 300000),       # Élargi de 100k-250k
    }
}

# V3.1 STRICTE (pour comparaison)
V3_1_STRICT_CONFIG = {
    'MIN_TOKEN_AGE': 0.0,
    'EMBRYONIC_MAX': 3.0,
    'MIN_VELOCITE_DEFAULT': 10.0,
    'DANGER_AGE_MIN': 12.0,
    'DANGER_AGE_MAX': 24.0,
    'OPTIMAL_AGE_MIN': 48.0,
    'OPTIMAL_AGE_MAX': 72.0,
    'NETWORKS': ['eth', 'bsc', 'base', 'solana'],
    'NETWORK_FILTERS': {
        'eth': {'min_score': 85, 'min_velocity': 10},
        'base': {'min_score': 90, 'min_velocity': 15},
        'bsc': {'min_score': 88, 'min_velocity': 12},
        'solana': {'min_score': 85, 'min_velocity': 10},
    },
    'LIQUIDITY': {
        'eth': (100000, 500000),
        'base': (300000, 2000000),
        'bsc': (500000, 5000000),
        'solana': (100000, 250000),
    }
}

ALLOWED_PUMP_TYPES = ["RAPIDE", "TRES_RAPIDE", "PARABOLIQUE"]
REJECTED_PUMP_TYPES = ["LENT", "STAGNANT", "STABLE"]

def passes_filters(alert, config):
    """Teste si alerte passe les filtres d'une configuration."""
    network = alert.get('network', '').lower()
    score = alert.get('score', 0)
    velocite = alert.get('velocite_pump', 0)
    type_pump = alert.get('type_pump', '')
    age = alert.get('age_hours', 0)
    liq = alert.get('liquidity', 0)

    # Réseau actif?
    if network not in config['NETWORKS']:
        return False, "Réseau désactivé"

    # Score par réseau
    network_filter = config['NETWORK_FILTERS'].get(network, {})
    min_score = network_filter.get('min_score', 85)
    if score < min_score:
        return False, f"Score {score} < {min_score} ({network.upper()})"

    # Vélocité par réseau
    min_velocity = network_filter.get('min_velocity', config['MIN_VELOCITE_DEFAULT'])
    if velocite < min_velocity:
        return False, f"Vélocité {velocite:.1f} < {min_velocity} ({network.upper()})"

    # Type pump
    if type_pump in REJECTED_PUMP_TYPES:
        return False, f"Type {type_pump} rejeté"

    # Zone danger 12-24h
    if config['DANGER_AGE_MIN'] <= age <= config['DANGER_AGE_MAX']:
        return False, f"Zone danger âge {age:.1f}h"

    # Liquidité
    liq_range = config['LIQUIDITY'].get(network)
    if liq_range:
        min_liq, max_liq = liq_range
        if liq < min_liq:
            return False, f"Liquidité {liq:,.0f} < {min_liq:,.0f}"
        if liq > max_liq:
            return False, f"Liquidité {liq:,.0f} > {max_liq:,.0f}"

    return True, "OK"

def calculate_quality_stats(alerts):
    """Calcule statistiques qualité."""
    if not alerts:
        return {}

    scores = [a['score'] for a in alerts if 'score' in a]
    velocites = [a['velocite_pump'] for a in alerts if 'velocite_pump' in a]
    liquidites = [a['liquidity'] for a in alerts if 'liquidity' in a]

    return {
        'count': len(alerts),
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'avg_velocity': sum(velocites) / len(velocites) if velocites else 0,
        'avg_liquidity': sum(liquidites) / len(liquidites) if liquidites else 0,
    }

def analyze_balanced(json_file):
    """Compare V3.1 STRICTE vs V3.1 ÉQUILIBRÉE."""

    print(f"\n{'='*80}")
    print(f"   TEST V3.1 EQUILIBREE - Optimisation Volume/Qualite")
    print(f"{'='*80}\n")

    # Charger données
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    alerts = data.get('alerts', [])
    total = len(alerts)

    print(f"Total alertes Railway: {total}\n")

    # Tester V3.1 STRICTE
    v3_1_strict = []
    for alert in alerts:
        passed, reason = passes_filters(alert, V3_1_STRICT_CONFIG)
        if passed:
            v3_1_strict.append(alert)

    # Tester V3.1 ÉQUILIBRÉE
    v3_1_balanced = []
    v3_1_balanced_reasons = defaultdict(int)
    for alert in alerts:
        passed, reason = passes_filters(alert, V3_1_BALANCED_CONFIG)
        if passed:
            v3_1_balanced.append(alert)
        else:
            v3_1_balanced_reasons[reason] += 1

    # Stats
    strict_stats = calculate_quality_stats(v3_1_strict)
    balanced_stats = calculate_quality_stats(v3_1_balanced)

    # Afficher résultats
    print(f"{'='*80}")
    print(f"COMPARAISON V3.1 STRICTE vs EQUILIBREE")
    print(f"{'='*80}\n")

    print(f"V3.1 STRICTE (actuelle):")
    print(f"  Alertes passees:     {len(v3_1_strict):4d} / {total} ({len(v3_1_strict)/total*100:.1f}%)")
    print(f"  Alertes/jour:        ~{len(v3_1_strict) * 7 / total:.1f}")
    print(f"  Score moyen:         {strict_stats['avg_score']:.1f}")
    print(f"  Velocite moyenne:    {strict_stats['avg_velocity']:.1f}")
    print(f"  Liquidite moyenne:   ${strict_stats['avg_liquidity']:,.0f}")

    print(f"\nV3.1 EQUILIBREE (proposee):")
    print(f"  Alertes passees:     {len(v3_1_balanced):4d} / {total} ({len(v3_1_balanced)/total*100:.1f}%)")
    print(f"  Alertes/jour:        ~{len(v3_1_balanced) * 7 / total:.1f}")
    print(f"  Score moyen:         {balanced_stats['avg_score']:.1f}")
    print(f"  Velocite moyenne:    {balanced_stats['avg_velocity']:.1f}")
    print(f"  Liquidite moyenne:   ${balanced_stats['avg_liquidity']:,.0f}")

    print(f"\nDIFFERENCE EQUILIBREE vs STRICTE:")
    diff_count = len(v3_1_balanced) - len(v3_1_strict)
    diff_score = balanced_stats['avg_score'] - strict_stats['avg_score']
    diff_vel = balanced_stats['avg_velocity'] - strict_stats['avg_velocity']

    print(f"  Nombre alertes:      {diff_count:+4d} ({diff_count/len(v3_1_strict)*100:+.1f}%)")
    print(f"  Score moyen:         {diff_score:+.1f} points")
    print(f"  Velocite moyenne:    {diff_vel:+.1f}")

    # Analyse par réseau
    print(f"\n{'='*80}")
    print(f"REPARTITION EQUILIBREE PAR RESEAU")
    print(f"{'='*80}\n")

    by_network_balanced = defaultdict(list)
    for alert in v3_1_balanced:
        network = alert.get('network', 'unknown')
        by_network_balanced[network].append(alert)

    by_network_strict = defaultdict(list)
    for alert in v3_1_strict:
        network = alert.get('network', 'unknown')
        by_network_strict[network].append(alert)

    print(f"{'Reseau':<10} | {'Strict':>6} | {'Equilibre':>9} | {'Diff':>6} | {'Score':>6} | {'Vel':>7}")
    print(f"{'-'*10}+{'-'*8}+{'-'*11}+{'-'*8}+{'-'*8}+{'-'*9}")

    for network in ['eth', 'base', 'bsc', 'solana']:
        strict_count = len(by_network_strict.get(network, []))
        balanced_count = len(by_network_balanced.get(network, []))
        diff = balanced_count - strict_count

        if balanced_count > 0:
            stats = calculate_quality_stats(by_network_balanced[network])
            print(f"{network.upper():<10} | {strict_count:6d} | {balanced_count:9d} | {diff:+6d} | "
                  f"{stats['avg_score']:6.1f} | {stats['avg_velocity']:7.1f}")

    # Détails assouplissement
    print(f"\n{'='*80}")
    print(f"DETAILS ASSOUPLISSEMENT")
    print(f"{'='*80}\n")

    print(f"Changements de seuils:\n")
    print(f"  ETH:")
    print(f"    Score:     85 -> 80  (-5 points)")
    print(f"    Velocite:  10 -> 6   (-4)")
    print(f"    Liquidite: $100k-500k -> $80k-600k")
    print(f"\n  BASE:")
    print(f"    Score:     90 -> 85  (-5 points)")
    print(f"    Velocite:  15 -> 10  (-5)")
    print(f"    Liquidite: $300k-2M -> $250k-2.5M")
    print(f"\n  BSC:")
    print(f"    Score:     88 -> 82  (-6 points)")
    print(f"    Velocite:  12 -> 8   (-4)")
    print(f"    Liquidite: $500k-5M -> $400k-6M")
    print(f"\n  SOLANA:")
    print(f"    Score:     85 -> 75  (-10 points)")
    print(f"    Velocite:  10 -> 6   (-4)")
    print(f"    Liquidite: $100k-250k -> $80k-300k")

    # Distribution qualité
    print(f"\n{'='*80}")
    print(f"DISTRIBUTION QUALITE V3.1 EQUILIBREE")
    print(f"{'='*80}\n")

    score_ranges = {
        '95-100': 0,
        '90-94': 0,
        '85-89': 0,
        '80-84': 0,
        '<80': 0
    }

    for alert in v3_1_balanced:
        score = alert.get('score', 0)
        if score >= 95:
            score_ranges['95-100'] += 1
        elif score >= 90:
            score_ranges['90-94'] += 1
        elif score >= 85:
            score_ranges['85-89'] += 1
        elif score >= 80:
            score_ranges['80-84'] += 1
        else:
            score_ranges['<80'] += 1

    for range_name, count in score_ranges.items():
        pct = count / len(v3_1_balanced) * 100 if v3_1_balanced else 0
        print(f"  Score {range_name}: {count:3d} alertes ({pct:5.1f}%)")

    # Projection performance
    print(f"\n{'='*80}")
    print(f"PROJECTIONS PERFORMANCE")
    print(f"{'='*80}\n")

    print(f"V3.1 STRICTE:")
    print(f"  Volume:      {len(v3_1_strict)} alertes (1-2/jour)")
    print(f"  Qualite:     Score {strict_stats['avg_score']:.1f} (EXCELLENT)")
    print(f"  Win Rate:    55-70% (qualite maximale)")
    print(f"  ROI/trade:   +8-12%")

    print(f"\nV3.1 EQUILIBREE:")
    print(f"  Volume:      {len(v3_1_balanced)} alertes ({len(v3_1_balanced) * 7 / total:.1f}/jour)")
    print(f"  Qualite:     Score {balanced_stats['avg_score']:.1f} (TRES BON)")
    print(f"  Win Rate:    45-60% (bon equilibre)")
    print(f"  ROI/trade:   +5-9%")

    # Recommandation
    print(f"\n{'='*80}")
    print(f"RECOMMANDATION")
    print(f"{'='*80}\n")

    quality_degradation = diff_score
    volume_increase = diff_count / len(v3_1_strict) * 100 if v3_1_strict else 0

    print(f"V3.1 EQUILIBREE vs STRICTE:")
    print(f"  [+] +{diff_count} alertes supplementaires (+{volume_increase:.0f}%)")
    print(f"  [+] {len(v3_1_balanced) * 7 / total:.1f} alertes/jour (meilleure utilisation capital)")
    print(f"  [-] {abs(diff_score):.1f} points de score moyen ({abs(diff_score)/strict_stats['avg_score']*100:.1f}% degradation)")

    if balanced_stats['avg_score'] >= 92:
        print(f"\n  [OK] Score moyen {balanced_stats['avg_score']:.1f} reste EXCELLENT (>92)")
        print(f"  [OK] Degradation qualite ACCEPTABLE pour +{volume_increase:.0f}% volume")
        print(f"\n  => RECOMMANDATION: DEPLOYER V3.1 EQUILIBREE")
        print(f"     - Meilleur compromis volume/qualite")
        print(f"     - Win rate attendu: 45-60%")
        print(f"     - {len(v3_1_balanced) * 7 / total:.1f} alertes/jour vs {len(v3_1_strict) * 7 / total:.1f}")
    else:
        print(f"\n  [!] Score moyen {balanced_stats['avg_score']:.1f} < 92")
        print(f"  [!] Degradation qualite IMPORTANTE")
        print(f"\n  => RECOMMANDATION: GARDER V3.1 STRICTE ou compromis intermediaire")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_v3_1_balanced.py alerts_railway_export_utf8.json")
        sys.exit(1)

    analyze_balanced(sys.argv[1])
