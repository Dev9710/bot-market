#!/usr/bin/env python3
"""
Backtest à partir du fichier CSV exporté
Usage: python backtest_from_csv.py alerts_data.csv
"""
import csv
import sys
from collections import defaultdict

# Seuils configurés
NETWORK_THRESHOLDS = {
    "solana": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "bsc": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "eth": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "base": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "arbitrum": {"min_liquidity": 2000, "min_volume": 400, "min_txns": 10},
    "avax": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "polygon_pos": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
}

def analyze_from_csv(csv_path):
    """Analyse les données depuis le CSV"""
    print("=" * 80)
    print("📊 BACKTESTING - COMPARAISON RÉSEAUX")
    print("=" * 80)

    # Lire le CSV
    alerts = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            alerts.append(row)

    total_alerts = len(alerts)
    print(f"\n✅ Total alertes analysées: {total_alerts:,}")

    # Grouper par réseau
    by_network = defaultdict(list)
    for alert in alerts:
        by_network[alert['network']].append(alert)

    # Répartition par réseau
    print(f"\n📡 RÉPARTITION PAR RÉSEAU:")
    for network in sorted(by_network.keys(), key=lambda n: len(by_network[n]), reverse=True):
        count = len(by_network[network])
        pct = (count / total_alerts * 100) if total_alerts > 0 else 0
        thresholds = NETWORK_THRESHOLDS.get(network, {})
        liq = thresholds.get("min_liquidity", 0) / 1000
        vol = thresholds.get("min_volume", 0) / 1000
        txns = thresholds.get("min_txns", 0)
        print(f"   {network.upper():15} {count:5} alertes ({pct:5.1f}%) - Seuils: ${liq:.0f}K/${vol:.0f}K/{txns}txns")

    # Analyse TP HIT par réseau
    print(f"\n🎯 ANALYSE TP HIT PAR RÉSEAU:")
    print(f"{'Réseau':<15} {'Alertes':>8} {'TP1':>8} {'TP2':>8} {'TP3':>8} {'Win%':>8} {'Score Moy':>10}")
    print("-" * 80)

    results = {}
    for network, network_alerts in sorted(by_network.items(), key=lambda x: len(x[1]), reverse=True):
        # Filtrer ceux qui ont des TP valides
        valid_alerts = [a for a in network_alerts
                       if float(a.get('tp1_price', 0) or 0) > 0
                       and float(a.get('prix_max_atteint', 0) or 0) > 0]

        if not valid_alerts:
            continue

        total = len(valid_alerts)
        tp1_hits = 0
        tp2_hits = 0
        tp3_hits = 0
        total_score = 0

        for alert in valid_alerts:
            prix_max = float(alert.get('prix_max_atteint', 0) or 0)
            tp1 = float(alert.get('tp1_price', 0) or 0)
            tp2 = float(alert.get('tp2_price', 0) or 0)
            tp3 = float(alert.get('tp3_price', 0) or 0)
            score = int(alert.get('score', 0) or 0)

            total_score += score

            if prix_max >= tp1 * 0.995:  # Tolérance 0.5%
                tp1_hits += 1
            if prix_max >= tp2 * 0.995:
                tp2_hits += 1
            if prix_max >= tp3 * 0.995:
                tp3_hits += 1

        win_rate = (tp1_hits / total * 100) if total > 0 else 0
        avg_score = total_score / total if total > 0 else 0

        results[network] = {
            'total': total,
            'tp1': tp1_hits,
            'tp2': tp2_hits,
            'tp3': tp3_hits,
            'win_rate': win_rate,
            'avg_score': avg_score
        }

        print(f"{network.upper():<15} {total:8} {tp1_hits:8} {tp2_hits:8} {tp3_hits:8} {win_rate:7.1f}% {avg_score:9.1f}")

    # Comparaison Arbitrum vs Autres
    print(f"\n" + "=" * 80)
    print("🔬 COMPARAISON DÉTAILLÉE: ARBITRUM vs AUTRES RÉSEAUX")
    print("=" * 80)

    if 'arbitrum' in results:
        arb = results['arbitrum']
        print(f"\n📊 ARBITRUM (Seuils: $2K / $400 / 10txns):")
        print(f"   Alertes: {arb['total']}")
        print(f"   TP1 Hit: {arb['tp1']} ({arb['tp1']/arb['total']*100:.1f}%)")
        print(f"   TP2 Hit: {arb['tp2']} ({arb['tp2']/arb['total']*100:.1f}%)")
        print(f"   TP3 Hit: {arb['tp3']} ({arb['tp3']/arb['total']*100:.1f}%)")
        print(f"   Win Rate: {arb['win_rate']:.1f}%")
        print(f"   Score Moyen: {arb['avg_score']:.1f}/100")

    # Moyenne des réseaux stricts
    strict_networks = ['solana', 'bsc', 'eth', 'base']
    strict_stats = {'total': 0, 'tp1': 0, 'tp2': 0, 'tp3': 0}

    for net in strict_networks:
        if net in results:
            strict_stats['total'] += results[net]['total']
            strict_stats['tp1'] += results[net]['tp1']
            strict_stats['tp2'] += results[net]['tp2']
            strict_stats['tp3'] += results[net]['tp3']

    if strict_stats['total'] > 0:
        strict_win_rate = (strict_stats['tp1'] / strict_stats['total'] * 100)
        print(f"\n📊 RÉSEAUX STRICTS COMBINÉS (Seuils: $100K / $50K / 100txns):")
        print(f"   Réseaux: Solana, BSC, ETH, Base")
        print(f"   Alertes: {strict_stats['total']}")
        print(f"   TP1 Hit: {strict_stats['tp1']} ({strict_stats['tp1']/strict_stats['total']*100:.1f}%)")
        print(f"   Win Rate: {strict_win_rate:.1f}%")

        if 'arbitrum' in results:
            diff = arb['win_rate'] - strict_win_rate
            print(f"\n🔬 COMPARAISON:")
            print(f"   Arbitrum Win Rate: {arb['win_rate']:.1f}%")
            print(f"   Stricts Win Rate:  {strict_win_rate:.1f}%")
            print(f"   Différence:        {diff:+.1f}%")

            if diff > 0:
                print(f"   ✅ Arbitrum MEILLEUR de {abs(diff):.1f}%!")
            elif diff < -5:
                print(f"   ⚠️ Arbitrum MOINS BON de {abs(diff):.1f}% - Seuils trop bas?")
            else:
                print(f"   ✅ Performances SIMILAIRES - Seuils valides!")

    # Recommandations
    print(f"\n" + "=" * 80)
    print("💡 RECOMMANDATIONS")
    print("=" * 80)

    if 'arbitrum' in results and strict_stats['total'] > 0:
        arb_wr = arb['win_rate']
        strict_wr = strict_win_rate

        if arb_wr >= strict_wr - 5:
            print(f"\n✅ SEUILS ARBITRUM VALIDÉS!")
            print(f"   Win rate {arb_wr:.1f}% comparable aux réseaux stricts ({strict_wr:.1f}%)")
            print(f"   Recommandation: GARDER les seuils Arbitrum actuels")
            print(f"   → $2K liquidity / $400 volume / 10 txns")
        elif arb_wr < strict_wr - 10:
            print(f"\n⚠️ SEUILS ARBITRUM À AJUSTER")
            print(f"   Win rate {arb_wr:.1f}% significativement inférieur ({strict_wr:.1f}%)")
            print(f"   Recommandation: AUGMENTER les seuils Arbitrum")
            print(f"   → Tester: $5K liquidity / $1K volume / 20 txns")
        else:
            print(f"\n✅ SEUILS ARBITRUM ACCEPTABLES")
            print(f"   Win rate {arb_wr:.1f}% légèrement inférieur ({strict_wr:.1f}%)")
            print(f"   Recommandation: MONITORER encore 1-2 jours puis décider")

    print(f"\n" + "=" * 80)
    print(f"✅ Analyse terminée - {total_alerts:,} alertes analysées")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backtest_from_csv.py alerts_data.csv")
        sys.exit(1)

    analyze_from_csv(sys.argv[1])