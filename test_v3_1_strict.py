"""
Test V3.1 STRICTE - Configuration ultra-rentable (2.7 alertes/jour)
"""

import json
import sys
from collections import defaultdict

# V3.1 STRICTE - Ultra-rentable (2.7/jour)
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
    network = alert.get('network', '').lower()
    score = alert.get('score', 0)
    velocite = alert.get('velocite_pump', 0)
    type_pump = alert.get('type_pump', '')
    age = alert.get('age_hours', 0)
    liq = alert.get('liquidity', 0)

    if network not in config['NETWORKS']:
        return False

    network_filter = config['NETWORK_FILTERS'].get(network, {})
    min_score = network_filter.get('min_score', 85)
    if score < min_score:
        return False

    min_velocity = network_filter.get('min_velocity', config['MIN_VELOCITE_DEFAULT'])
    if velocite < min_velocity:
        return False

    if type_pump in REJECTED_PUMP_TYPES:
        return False

    if config['DANGER_AGE_MIN'] <= age <= config['DANGER_AGE_MAX']:
        return False

    liq_range = config['LIQUIDITY'].get(network)
    if liq_range:
        min_liq, max_liq = liq_range
        if liq < min_liq or liq > max_liq:
            return False

    return True

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

def main(json_file):
    print(f"\n{'='*80}")
    print(f"   TEST V3.1 STRICTE - Configuration ultra-rentable")
    print(f"{'='*80}\n")

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    alerts = data.get('alerts', [])
    total = len(alerts)
    days_total = 90

    passed = [a for a in alerts if passes_filters(a, V3_1_STRICT)]
    stats = calc_stats(passed)

    print(f"Total alertes Railway: {total}")
    print(f"Periode estimee:       ~{days_total} jours\n")

    print(f"{'='*80}")
    print(f"RESULTATS V3.1 STRICTE")
    print(f"{'='*80}\n")

    per_day = stats['count'] / days_total
    print(f"  Alertes total:       {stats['count']:4d} / {total} ({stats['count']/total*100:.1f}%)")
    print(f"  Alertes/jour:        {per_day:.1f} <<< OBJECTIF: ~2.7/jour")
    print(f"  Score moyen:         {stats['avg_score']:.1f}")
    print(f"  Velocite moy:        {stats['avg_vel']:.1f}")
    print(f"  Liquidite moy:       ${stats['avg_liq']:,.0f}")

    # Par réseau
    print(f"\n{'='*80}")
    print(f"REPARTITION PAR RESEAU")
    print(f"{'='*80}\n")

    by_network = defaultdict(list)
    for alert in passed:
        by_network[alert.get('network', 'unknown')].append(alert)

    print(f"{'Reseau':<10} | {'Alertes':>8} | {'/jour':>6} | {'Score':>6} | {'Vel':>7}")
    print(f"{'-'*10}+{'-'*10}+{'-'*8}+{'-'*8}+{'-'*9}")

    for network in ['eth', 'base', 'bsc', 'solana']:
        if network in by_network:
            net_stats = calc_stats(by_network[network])
            count = net_stats['count']
            print(f"{network.upper():<10} | {count:8d} | {count/days_total:6.1f} | "
                  f"{net_stats['avg_score']:6.1f} | {net_stats['avg_vel']:7.1f}")

    # Distribution qualité
    print(f"\n{'='*80}")
    print(f"DISTRIBUTION QUALITE")
    print(f"{'='*80}\n")

    ranges = {'95-100': 0, '90-94': 0, '85-89': 0, '80-84': 0, '75-79': 0, '<75': 0}
    for alert in passed:
        score = alert.get('score', 0)
        if score >= 95: ranges['95-100'] += 1
        elif score >= 90: ranges['90-94'] += 1
        elif score >= 85: ranges['85-89'] += 1
        elif score >= 80: ranges['80-84'] += 1
        elif score >= 75: ranges['75-79'] += 1
        else: ranges['<75'] += 1

    for r, count in ranges.items():
        pct = count / stats['count'] * 100 if stats['count'] else 0
        bar = '#' * int(pct / 2)
        print(f"  Score {r:7s}: {count:4d} ({pct:5.1f}%) {bar}")

    # Win rate et ROI
    print(f"\n{'='*80}")
    print(f"PROJECTIONS PERFORMANCE")
    print(f"{'='*80}\n")

    excellent = ranges['95-100']
    good = ranges['90-94'] + ranges['95-100']
    risky = ranges['75-79'] + ranges['<75']

    print(f"Qualite:")
    print(f"  Score 95+:           {excellent:4d} ({excellent/stats['count']*100:.1f}%)")
    print(f"  Score 90+:           {good:4d} ({good/stats['count']*100:.1f}%)")
    print(f"  Score <80:           {risky:4d} ({risky/stats['count']*100:.1f}%)")

    avg_score = stats['avg_score']
    if avg_score >= 95:
        wr_min, wr_max = 55, 70
    elif avg_score >= 90:
        wr_min, wr_max = 45, 58
    elif avg_score >= 87:
        wr_min, wr_max = 40, 52
    elif avg_score >= 85:
        wr_min, wr_max = 38, 50
    else:
        wr_min, wr_max = 32, 45

    print(f"\nWin Rate estime:       {wr_min}-{wr_max}%")

    alertes_per_month = stats['count'] * 30 / days_total
    wr_mid = (wr_min + wr_max) / 2 / 100
    wins = alertes_per_month * wr_mid
    losses = alertes_per_month * (1 - wr_mid)
    roi = (wins * 0.15) - (losses * 0.10)

    print(f"\nROI mensuel projete:")
    print(f"  Alertes/mois:        ~{alertes_per_month:.0f}")
    print(f"  Wins:                ~{wins:.0f}")
    print(f"  Losses:              ~{losses:.0f}")
    print(f"  ROI net:             {roi:+.1f}%")

    # Recommandation
    print(f"\n{'='*80}")
    print(f"VALIDATION")
    print(f"{'='*80}\n")

    if 2.5 <= per_day <= 3.0:
        print(f"  [OK] Objectif 2.7/jour atteint ({per_day:.1f}/jour)")
    elif per_day < 2.5:
        print(f"  [!] Sous objectif ({per_day:.1f}/jour < 2.7/jour)")
    else:
        print(f"  [+] Au-dessus objectif ({per_day:.1f}/jour > 2.7/jour)")

    if avg_score >= 95:
        print(f"  [OK] Qualite EXCELLENTE (score {avg_score:.1f})")
    elif avg_score >= 92:
        print(f"  [OK] Qualite TRES BONNE (score {avg_score:.1f})")
    elif avg_score >= 89:
        print(f"  [~] Qualite BONNE (score {avg_score:.1f})")
    else:
        print(f"  [!] Qualite moyenne (score {avg_score:.1f})")

    if roi >= 10:
        print(f"  [OK] ROI excellent ({roi:+.1f}%/mois >= 10%)")
    elif roi >= 7:
        print(f"  [OK] ROI bon ({roi:+.1f}%/mois >= 7%)")
    elif roi >= 4:
        print(f"  [~] ROI acceptable ({roi:+.1f}%/mois >= 4%)")
    else:
        print(f"  [!] ROI faible ({roi:+.1f}%/mois < 4%)")

    if 2.5 <= per_day <= 3.0 and avg_score >= 95 and roi >= 10:
        print(f"\n  => CONFIGURATION VALIDEE - Ultra-rentable!")
        print(f"     Mode ideal pour: capital limite, trading conservateur, WR >60% requis")
    elif per_day >= 2.0 and avg_score >= 92:
        print(f"\n  => CONFIGURATION ACCEPTABLE")
    else:
        print(f"\n  => CONFIGURATION A AJUSTER")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_v3_1_strict.py alerts_railway_export_utf8.json")
        sys.exit(1)

    main(sys.argv[1])
