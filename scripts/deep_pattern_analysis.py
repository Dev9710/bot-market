#!/usr/bin/env python3
"""
Analyse approfondie des patterns gagnants.
Objectif: Identifier les combinaisons optimales pour maximiser le winrate.
"""

import json
from pathlib import Path
from collections import defaultdict
from itertools import product

EXPORT_FILE = Path(__file__).parent.parent / "alerts_railway_export.json"


def load_alerts():
    # Essayer UTF-16-LE d'abord (format Windows commun)
    encodings = ['utf-16-le', 'utf-16', 'utf-8']

    for encoding in encodings:
        try:
            with open(EXPORT_FILE, 'r', encoding=encoding) as f:
                content = f.read()

            # Nettoyer caracteres nuls et espaces parasites
            if '\x00' in content:
                content = content.replace('\x00', '')

            # Trouver le debut du JSON
            json_start = content.find('{')
            if json_start > 0:
                content = content[json_start:]

            # Parser
            data = json.loads(content)
            print(f"Fichier charge avec encoding: {encoding}")
            return data.get('alerts', [])
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            continue

    raise ValueError(f"Impossible de charger {EXPORT_FILE}")


def prepare_alerts(alerts):
    """Prepare alerts with calculated fields."""
    valid = []
    for alert in alerts:
        price_at = alert.get('price_at_alert') or alert.get('entry_price')
        price_after = alert.get('price_1h_after')

        if not price_at or not price_after:
            continue

        try:
            pct = (float(price_after) - float(price_at)) / float(price_at) * 100
            alert['_pct'] = pct
            alert['_win'] = pct >= 5
            alert['_loss'] = pct <= -10
            valid.append(alert)
        except:
            pass

    return valid


def analyze_combinations(alerts, network):
    """Analyze all parameter combinations to find optimal zones."""
    print(f"\n{'='*60}")
    print(f"ANALYSE COMBINATOIRE - {network.upper()}")
    print(f"{'='*60}")

    network_alerts = [a for a in alerts if a.get('network') == network]
    if len(network_alerts) < 50:
        print(f"Pas assez de donnees ({len(network_alerts)} alertes)")
        return

    print(f"Alertes analysables: {len(network_alerts)}")

    # Define ranges for each parameter
    if network == 'solana':
        vol_ranges = [
            (0, 100_000, "Vol<100K"),
            (100_000, 500_000, "Vol100-500K"),
            (500_000, 1_000_000, "Vol500K-1M"),
            (1_000_000, 5_000_000, "Vol1-5M"),
            (5_000_000, float('inf'), "Vol>5M"),
        ]
        liq_ranges = [
            (0, 100_000, "Liq<100K"),
            (100_000, 200_000, "Liq100-200K"),
            (200_000, 500_000, "Liq200-500K"),
            (500_000, float('inf'), "Liq>500K"),
        ]
    else:  # ETH
        vol_ranges = [
            (0, 50_000, "Vol<50K"),
            (50_000, 100_000, "Vol50-100K"),
            (100_000, 500_000, "Vol100-500K"),
            (500_000, float('inf'), "Vol>500K"),
        ]
        liq_ranges = [
            (0, 30_000, "Liq<30K"),
            (30_000, 50_000, "Liq30-50K"),
            (50_000, 100_000, "Liq50-100K"),
            (100_000, float('inf'), "Liq>100K"),
        ]

    age_ranges = [
        (0, 6, "Age<6h"),
        (6, 12, "Age6-12h"),
        (12, 24, "Age12-24h"),
        (24, float('inf'), "Age>24h"),
    ]

    ratio_ranges = [
        (0, 1.0, "Ratio<1"),
        (1.0, 1.2, "Ratio1-1.2"),
        (1.2, 1.5, "Ratio1.2-1.5"),
        (1.5, float('inf'), "Ratio>1.5"),
    ]

    # Find best single-parameter filters
    print("\n--- MEILLEURS FILTRES SIMPLES ---")
    results = []

    for ranges, param, getter in [
        (vol_ranges, "volume", lambda a: a.get('volume_24h', 0) or 0),
        (liq_ranges, "liquidite", lambda a: a.get('liquidity', 0) or 0),
        (age_ranges, "age", lambda a: a.get('age_hours', 0) or 0),
        (ratio_ranges, "buy_ratio", lambda a: a.get('buy_ratio', 0) or 0),
    ]:
        for vmin, vmax, label in ranges:
            subset = [a for a in network_alerts if vmin <= getter(a) < vmax]
            if len(subset) >= 20:
                wins = sum(1 for a in subset if a['_win'])
                losses = sum(1 for a in subset if a['_loss'])
                decided = wins + losses
                if decided > 0:
                    wr = wins / decided * 100
                    results.append((wr, len(subset), decided, label, param))

    results.sort(reverse=True)
    for wr, total, decided, label, param in results[:15]:
        marker = " ***" if wr >= 65 else " **" if wr >= 55 else ""
        print(f"  {label} ({param}): {total} alertes, {decided} decided | WR: {wr:.1f}%{marker}")

    # Find best combinations (2 parameters)
    print("\n--- MEILLEURES COMBINAISONS (2 params) ---")
    combos = []

    for (v_min, v_max, v_label) in vol_ranges:
        for (l_min, l_max, l_label) in liq_ranges:
            subset = [a for a in network_alerts
                     if v_min <= (a.get('volume_24h') or 0) < v_max
                     and l_min <= (a.get('liquidity') or 0) < l_max]
            if len(subset) >= 15:
                wins = sum(1 for a in subset if a['_win'])
                losses = sum(1 for a in subset if a['_loss'])
                decided = wins + losses
                if decided >= 10:
                    wr = wins / decided * 100
                    combos.append((wr, len(subset), decided, f"{v_label} + {l_label}"))

    for (v_min, v_max, v_label) in vol_ranges:
        for (a_min, a_max, a_label) in age_ranges:
            subset = [a for a in network_alerts
                     if v_min <= (a.get('volume_24h') or 0) < v_max
                     and a_min <= (a.get('age_hours') or 0) < a_max]
            if len(subset) >= 15:
                wins = sum(1 for a in subset if a['_win'])
                losses = sum(1 for a in subset if a['_loss'])
                decided = wins + losses
                if decided >= 10:
                    wr = wins / decided * 100
                    combos.append((wr, len(subset), decided, f"{v_label} + {a_label}"))

    for (r_min, r_max, r_label) in ratio_ranges:
        for (a_min, a_max, a_label) in age_ranges:
            subset = [a for a in network_alerts
                     if r_min <= (a.get('buy_ratio') or 0) < r_max
                     and a_min <= (a.get('age_hours') or 0) < a_max]
            if len(subset) >= 15:
                wins = sum(1 for a in subset if a['_win'])
                losses = sum(1 for a in subset if a['_loss'])
                decided = wins + losses
                if decided >= 10:
                    wr = wins / decided * 100
                    combos.append((wr, len(subset), decided, f"{r_label} + {a_label}"))

    combos.sort(reverse=True)
    for wr, total, decided, label in combos[:15]:
        marker = " ***" if wr >= 70 else " **" if wr >= 60 else ""
        print(f"  {label}: {total} alertes, {decided} decided | WR: {wr:.1f}%{marker}")

    # Find best 3-parameter combinations
    print("\n--- MEILLEURES COMBINAISONS (3 params) ---")
    combos3 = []

    for (v_min, v_max, v_label) in vol_ranges:
        for (l_min, l_max, l_label) in liq_ranges:
            for (a_min, a_max, a_label) in age_ranges:
                subset = [a for a in network_alerts
                         if v_min <= (a.get('volume_24h') or 0) < v_max
                         and l_min <= (a.get('liquidity') or 0) < l_max
                         and a_min <= (a.get('age_hours') or 0) < a_max]
                if len(subset) >= 10:
                    wins = sum(1 for a in subset if a['_win'])
                    losses = sum(1 for a in subset if a['_loss'])
                    decided = wins + losses
                    if decided >= 5:
                        wr = wins / decided * 100
                        combos3.append((wr, len(subset), decided, wins, losses, f"{v_label} + {l_label} + {a_label}"))

    combos3.sort(reverse=True)
    for wr, total, decided, wins, losses, label in combos3[:20]:
        marker = " ***" if wr >= 75 else " **" if wr >= 65 else ""
        print(f"  {label}: {total} alertes | WR: {wr:.1f}% ({wins}W/{losses}L){marker}")


def analyze_type_pump_velocity(alerts, network):
    """Analyze type_pump and velocite_pump impact."""
    print(f"\n{'='*60}")
    print(f"ANALYSE TYPE_PUMP & VELOCITE - {network.upper()}")
    print(f"{'='*60}")

    network_alerts = [a for a in alerts if a.get('network') == network]

    # Par type_pump
    by_type = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    for alert in network_alerts:
        type_pump = alert.get('type_pump', 'UNKNOWN')
        by_type[type_pump]['total'] += 1
        if alert['_win']:
            by_type[type_pump]['wins'] += 1
        elif alert['_loss']:
            by_type[type_pump]['losses'] += 1

    print("\nPar TYPE_PUMP:")
    for t, stats in sorted(by_type.items(), key=lambda x: -(x[1]['wins'] + x[1]['losses'])):
        decided = stats['wins'] + stats['losses']
        if decided >= 5:
            wr = stats['wins'] / decided * 100
            print(f"  {t}: {stats['total']} alertes | WR: {wr:.1f}% ({stats['wins']}W/{stats['losses']}L)")

    # Par velocite ranges
    print("\nPar VELOCITE_PUMP:")
    vel_ranges = [
        (-float('inf'), -20, "vel<-20 (dump)"),
        (-20, -5, "vel-20 to -5"),
        (-5, 5, "vel-5 to +5 (stable)"),
        (5, 20, "vel+5 to +20"),
        (20, float('inf'), "vel>+20 (moon)"),
    ]

    for vmin, vmax, label in vel_ranges:
        subset = [a for a in network_alerts
                 if (a.get('velocite_pump') is not None)
                 and vmin <= a.get('velocite_pump') < vmax]
        if len(subset) >= 10:
            wins = sum(1 for a in subset if a['_win'])
            losses = sum(1 for a in subset if a['_loss'])
            decided = wins + losses
            if decided >= 5:
                wr = wins / decided * 100
                marker = " ***" if wr >= 65 else " **" if wr >= 55 else ""
                print(f"  {label}: {len(subset)} alertes | WR: {wr:.1f}%{marker}")


def analyze_concentration_risk(alerts, network):
    """Analyze concentration risk impact."""
    print(f"\n{'='*60}")
    print(f"ANALYSE CONCENTRATION_RISK - {network.upper()}")
    print(f"{'='*60}")

    network_alerts = [a for a in alerts if a.get('network') == network]

    # Extract concentration_risk from alert_message if not direct field
    by_risk = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})

    for alert in network_alerts:
        msg = alert.get('alert_message', '')
        if 'concentration : HIGH' in msg or 'concentration: HIGH' in msg:
            risk = 'HIGH'
        elif 'concentration : MEDIUM' in msg or 'concentration: MEDIUM' in msg:
            risk = 'MEDIUM'
        elif 'concentration : LOW' in msg or 'concentration: LOW' in msg:
            risk = 'LOW'
        else:
            risk = 'UNKNOWN'

        by_risk[risk]['total'] += 1
        if alert['_win']:
            by_risk[risk]['wins'] += 1
        elif alert['_loss']:
            by_risk[risk]['losses'] += 1

    print("\nPar CONCENTRATION_RISK:")
    for r, stats in sorted(by_risk.items()):
        decided = stats['wins'] + stats['losses']
        if decided >= 5:
            wr = stats['wins'] / decided * 100
            print(f"  {r}: {stats['total']} alertes | WR: {wr:.1f}% ({stats['wins']}W/{stats['losses']}L)")


def generate_recommendations(alerts):
    """Generate specific recommendations based on analysis."""
    print("\n" + "=" * 60)
    print("RECOMMANDATIONS SPECIFIQUES D'AMELIORATION")
    print("=" * 60)

    for network in ['solana', 'eth']:
        network_alerts = [a for a in alerts if a.get('network') == network]
        if not network_alerts:
            continue

        wins = sum(1 for a in network_alerts if a['_win'])
        losses = sum(1 for a in network_alerts if a['_loss'])
        decided = wins + losses
        current_wr = (wins / decided * 100) if decided > 0 else 0

        print(f"\n{'='*40}")
        print(f"{network.upper()} - WR ACTUEL: {current_wr:.1f}%")
        print(f"{'='*40}")

        if network == 'solana':
            print("""
PROBLEME: WR a 49.8% = NON RENTABLE

PATTERNS IDENTIFIES:
1. Age < 6h: WR 62.9% (+13% vs moyenne)
2. Volume < 500K: WR ~63% (+13%)
3. Buy ratio > 2.0: WR 50% (neutre)

FILTRES A IMPLEMENTER:
- EXCLURE Age > 24h (WR 27.9%)
- EXCLURE Volume > 5M (WR 29.1%)
- PRIORISER Age < 6h + Volume < 1M

NOUVEAU SIGNAL A++:
  Vol < 500K + Age < 6h = Zone Optimale Estimee ~70%+ WR
""")
        else:  # ETH
            print("""
OK: WR a 60.8% = RENTABLE

PATTERNS IDENTIFIES:
1. Volume < 100K: WR 63.1%
2. Liquidite < 50K: WR 56%
3. Buy ratio 1.5-2.0: WR 58.7%
4. Age < 6h: WR 53.2%

FILTRES A IMPLEMENTER:
- EXCLURE Age > 48h (WR 8.6%!)
- EXCLURE buy_ratio < 1.0 (WR 0%!)
- PRIORISER Vol < 100K + Liq < 50K

NOUVEAU SIGNAL A++:
  Vol < 100K + Liq < 50K + Age < 12h = ~65%+ WR estime
""")


def main():
    print("=" * 60)
    print("ANALYSE APPROFONDIE DES PATTERNS")
    print("=" * 60)

    alerts = load_alerts()
    valid_alerts = prepare_alerts(alerts)

    print(f"Alertes avec resultat: {len(valid_alerts)}")

    for network in ['solana', 'eth']:
        analyze_combinations(valid_alerts, network)
        analyze_type_pump_velocity(valid_alerts, network)
        analyze_concentration_risk(valid_alerts, network)

    generate_recommendations(valid_alerts)


if __name__ == "__main__":
    main()
