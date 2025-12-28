"""
Test V3.1 VOLUME ÉLEVÉ - Objectif ~10 alertes/jour

Stratégie: Assouplir significativement pour atteindre volume cible
"""

import json
import sys
from collections import defaultdict

# V3.1 VOLUME ÉLEVÉ - Objectif 10/jour (avec Arbitrum)
V3_1_HIGH_VOLUME = {
    'MIN_TOKEN_AGE': 0.0,
    'EMBRYONIC_MAX': 3.0,
    'MIN_VELOCITE_DEFAULT': 3.0,
    'DANGER_AGE_MIN': 12.0,
    'DANGER_AGE_MAX': 24.0,
    'OPTIMAL_AGE_MIN': 48.0,
    'OPTIMAL_AGE_MAX': 72.0,
    'NETWORKS': ['eth', 'bsc', 'base', 'solana', 'arbitrum'],  # Arbitrum réactivé
    'NETWORK_FILTERS': {
        'eth': {'min_score': 75, 'min_velocity': 3},
        'base': {'min_score': 80, 'min_velocity': 6},
        'bsc': {'min_score': 75, 'min_velocity': 5},
        'solana': {'min_score': 70, 'min_velocity': 3},
        'arbitrum': {'min_score': 85, 'min_velocity': 8},  # TRÈS strict pour Arbitrum
    },
    'LIQUIDITY': {
        'eth': (50000, 800000),
        'base': (200000, 3000000),
        'bsc': (300000, 8000000),
        'solana': (50000, 400000),
        'arbitrum': (100000, 500000),  # Strict pour Arbitrum
    }
}

# V3.1 STRICTE (référence)
V3_1_STRICT = {
    'MIN_TOKEN_AGE': 0.0,
    'MIN_VELOCITE_DEFAULT': 10.0,
    'DANGER_AGE_MIN': 12.0,
    'DANGER_AGE_MAX': 24.0,
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

REJECTED_PUMP_TYPES = ["LENT", "STAGNANT", "STABLE"]

def passes_filters(alert, config):
    """Teste si alerte passe les filtres."""
    network = alert.get('network', '').lower()
    score = alert.get('score', 0)
    velocite = alert.get('velocite_pump', 0)
    type_pump = alert.get('type_pump', '')
    age = alert.get('age_hours', 0)
    liq = alert.get('liquidity', 0)

    if network not in config['NETWORKS']:
        return False, "Réseau désactivé"

    network_filter = config['NETWORK_FILTERS'].get(network, {})
    min_score = network_filter.get('min_score', 85)
    if score < min_score:
        return False, f"Score {score} < {min_score}"

    min_velocity = network_filter.get('min_velocity', config['MIN_VELOCITE_DEFAULT'])
    if velocite < min_velocity:
        return False, f"Vélocité {velocite:.1f} < {min_velocity}"

    if type_pump in REJECTED_PUMP_TYPES:
        return False, f"Type {type_pump}"

    if config['DANGER_AGE_MIN'] <= age <= config['DANGER_AGE_MAX']:
        return False, f"Zone danger"

    liq_range = config['LIQUIDITY'].get(network)
    if liq_range:
        min_liq, max_liq = liq_range
        if liq < min_liq or liq > max_liq:
            return False, f"Liquidité"

    return True, "OK"

def calc_stats(alerts):
    if not alerts:
        return {}
    scores = [a['score'] for a in alerts if 'score' in a]
    vels = [a['velocite_pump'] for a in alerts if 'velocite_pump' in a]
    liqs = [a['liquidity'] for a in alerts if 'liquidity' in a]
    return {
        'count': len(alerts),
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'avg_vel': sum(vels) / len(vels) if vels else 0,
        'avg_liq': sum(liqs) / len(liqs) if liqs else 0,
    }

def analyze(json_file):
    print(f"\n{'='*80}")
    print(f"   TEST V3.1 VOLUME ELEVE - Objectif 10 alertes/jour")
    print(f"{'='*80}\n")

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    alerts = data.get('alerts', [])
    total = len(alerts)
    # Estimer durée: 4252 alertes V2 sur ~3 mois = 90 jours
    days_total = 90

    print(f"Total alertes Railway: {total} (~{days_total} jours estimes)\n")

    # Tester configs
    strict_passed = [a for a in alerts if passes_filters(a, V3_1_STRICT)[0]]
    high_volume_passed = [a for a in alerts if passes_filters(a, V3_1_HIGH_VOLUME)[0]]

    strict_stats = calc_stats(strict_passed)
    hv_stats = calc_stats(high_volume_passed)

    # Affichage
    print(f"{'='*80}")
    print(f"COMPARAISON")
    print(f"{'='*80}\n")

    print(f"V3.1 STRICTE:")
    print(f"  Alertes total:       {strict_stats['count']:4d} / {total}")
    print(f"  Alertes/jour:        {strict_stats['count']/days_total:.1f}")
    print(f"  Score moyen:         {strict_stats['avg_score']:.1f}")
    print(f"  Velocite moy:        {strict_stats['avg_vel']:.1f}")
    print(f"  Liquidite moy:       ${strict_stats['avg_liq']:,.0f}")

    print(f"\nV3.1 VOLUME ELEVE:")
    print(f"  Alertes total:       {hv_stats['count']:4d} / {total}")
    print(f"  Alertes/jour:        {hv_stats['count']/days_total:.1f} <<< OBJECTIF: 10/jour")
    print(f"  Score moyen:         {hv_stats['avg_score']:.1f}")
    print(f"  Velocite moy:        {hv_stats['avg_vel']:.1f}")
    print(f"  Liquidite moy:       ${hv_stats['avg_liq']:,.0f}")

    diff_count = hv_stats['count'] - strict_stats['count']
    diff_score = hv_stats['avg_score'] - strict_stats['avg_score']
    diff_vel = hv_stats['avg_vel'] - strict_stats['avg_vel']

    print(f"\nDIFFERENCE:")
    print(f"  Alertes:             {diff_count:+4d} ({diff_count/strict_stats['count']*100:+.0f}%)")
    print(f"  Alertes/jour:        {diff_count/days_total:+.1f}")
    print(f"  Score moyen:         {diff_score:+.1f} points")
    print(f"  Velocite moy:        {diff_vel:+.1f}")

    # Par réseau
    print(f"\n{'='*80}")
    print(f"REPARTITION PAR RESEAU (Volume Elevé)")
    print(f"{'='*80}\n")

    by_network = defaultdict(list)
    for alert in high_volume_passed:
        by_network[alert.get('network', 'unknown')].append(alert)

    print(f"{'Reseau':<10} | {'Alertes':>8} | {'Score':>6} | {'Vel':>7} | {'Liq':>12}")
    print(f"{'-'*10}+{'-'*10}+{'-'*8}+{'-'*9}+{'-'*14}")

    for network in ['eth', 'base', 'bsc', 'solana', 'arbitrum']:
        if network in by_network:
            stats = calc_stats(by_network[network])
            count = stats['count']
            per_day = count / days_total
            print(f"{network.upper():<10} | {count:4d} ({per_day:.1f}/j) | "
                  f"{stats['avg_score']:6.1f} | {stats['avg_vel']:7.1f} | "
                  f"${stats['avg_liq']:>11,.0f}")

    # Distribution qualité
    print(f"\n{'='*80}")
    print(f"DISTRIBUTION QUALITE")
    print(f"{'='*80}\n")

    ranges = {'95-100': 0, '90-94': 0, '85-89': 0, '80-84': 0, '75-79': 0, '<75': 0}
    for alert in high_volume_passed:
        score = alert.get('score', 0)
        if score >= 95: ranges['95-100'] += 1
        elif score >= 90: ranges['90-94'] += 1
        elif score >= 85: ranges['85-89'] += 1
        elif score >= 80: ranges['80-84'] += 1
        elif score >= 75: ranges['75-79'] += 1
        else: ranges['<75'] += 1

    for r, count in ranges.items():
        pct = count / hv_stats['count'] * 100 if hv_stats['count'] else 0
        bar = '#' * int(pct / 2)
        print(f"  Score {r:7s}: {count:4d} ({pct:5.1f}%) {bar}")

    # Analyse critique
    print(f"\n{'='*80}")
    print(f"ANALYSE CRITIQUE")
    print(f"{'='*80}\n")

    excellent = ranges['95-100']
    good = ranges['90-94'] + ranges['95-100']
    acceptable = good + ranges['85-89']
    risky = ranges['75-79'] + ranges['<75']

    pct_excellent = excellent / hv_stats['count'] * 100 if hv_stats['count'] else 0
    pct_good = good / hv_stats['count'] * 100 if hv_stats['count'] else 0
    pct_risky = risky / hv_stats['count'] * 100 if hv_stats['count'] else 0

    print(f"Qualite des {hv_stats['count']} alertes:")
    print(f"  Score 95+:           {excellent:4d} ({pct_excellent:.1f}%) - EXCELLENT")
    print(f"  Score 90+:           {good:4d} ({pct_good:.1f}%) - BON")
    print(f"  Score 85+:           {acceptable:4d} ({acceptable/hv_stats['count']*100:.1f}%) - ACCEPTABLE")
    print(f"  Score <80:           {risky:4d} ({pct_risky:.1f}%) - RISQUE")

    # Win rate estimé
    wr_excellent = 0.60  # 60% WR pour score 95+
    wr_good = 0.50       # 50% WR pour score 90-94
    wr_acceptable = 0.40 # 40% WR pour score 85-89
    wr_risky = 0.30      # 30% WR pour score <85

    avg_score = hv_stats['avg_score']
    if avg_score >= 90:
        wr_estimate_min = 45
        wr_estimate_max = 58
    elif avg_score >= 85:
        wr_estimate_min = 38
        wr_estimate_max = 50
    elif avg_score >= 80:
        wr_estimate_min = 32
        wr_estimate_max = 45
    else:
        wr_estimate_min = 25
        wr_estimate_max = 38

    print(f"\nWin Rate Estime (score moyen {avg_score:.1f}):")
    print(f"  Fourchette:          {wr_estimate_min}-{wr_estimate_max}%")

    # ROI projection
    alertes_per_month = hv_stats['count'] * 30 / days_total
    wr_mid = (wr_estimate_min + wr_estimate_max) / 2 / 100

    wins = alertes_per_month * wr_mid
    losses = alertes_per_month * (1 - wr_mid)
    roi = (wins * 0.15) - (losses * 0.10)  # +15% gains, -10% pertes

    print(f"\nProjection ROI mensuel:")
    print(f"  Alertes/mois:        ~{alertes_per_month:.0f}")
    print(f"  Win rate moyen:      {wr_mid*100:.0f}%")
    print(f"  Wins:                ~{wins:.0f}")
    print(f"  Losses:              ~{losses:.0f}")
    print(f"  ROI net:             {roi:+.1f}% / mois")

    # Recommandation
    print(f"\n{'='*80}")
    print(f"RECOMMANDATION")
    print(f"{'='*80}\n")

    if hv_stats['count'] / days_total >= 9:
        print(f"  [OK] Objectif 10/jour atteint ({hv_stats['count']/days_total:.1f}/jour)")
    else:
        print(f"  [!] Objectif 10/jour NON atteint ({hv_stats['count']/days_total:.1f}/jour)")

    if avg_score >= 88:
        print(f"  [OK] Qualite EXCELLENTE (score {avg_score:.1f})")
        print(f"\n  => DEPLOIEMENT RECOMMANDE")
    elif avg_score >= 85:
        print(f"  [~] Qualite BONNE (score {avg_score:.1f})")
        print(f"  [!] Degradation moderee vs stricte (-{abs(diff_score):.1f} points)")
        print(f"\n  => DEPLOIEMENT ACCEPTABLE si besoin volume")
    elif avg_score >= 80:
        print(f"  [!] Qualite MOYENNE (score {avg_score:.1f})")
        print(f"  [!] Degradation importante (-{abs(diff_score):.1f} points)")
        print(f"  [!] {pct_risky:.1f}% alertes score <80 (risque)")
        print(f"\n  => DEPLOIEMENT RISQUE - Tester avec capital limite")
    else:
        print(f"  [X] Qualite FAIBLE (score {avg_score:.1f})")
        print(f"  [X] Degradation critique (-{abs(diff_score):.1f} points)")
        print(f"\n  => DEPLOIEMENT NON RECOMMANDE")

    print(f"\n  Compromis volume/qualite:")
    if roi > 5:
        print(f"  [OK] ROI {roi:+.1f}%/mois acceptable (>{5}%)")
    else:
        print(f"  [!] ROI {roi:+.1f}%/mois faible (<{5}%)")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_v3_1_high_volume.py alerts_railway_export_utf8.json")
        sys.exit(1)

    analyze(sys.argv[1])
