#!/usr/bin/env python3
"""
Analyse approfondie et intelligente des performances du bot
Identifie les patterns de succès et recommandations pour améliorer le win rate
"""
import sqlite3
import sys
from collections import defaultdict
from statistics import mean, median

DB_PATH = "/data/alerts_history.db"

def analyze_advanced_patterns():
    print("=" * 100)
    print("ANALYSE APPROFONDIE DES PATTERNS DE SUCCÈS")
    print("=" * 100)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer toutes les données nécessaires
    cursor.execute("""
        SELECT
            a.id,
            a.network,
            a.token_name,
            a.score,
            a.base_score,
            a.momentum_bonus,
            a.confidence_score,
            a.entry_price,
            a.tp1_price,
            a.tp2_price,
            a.tp3_price,
            a.volume_24h,
            a.volume_6h,
            a.volume_1h,
            a.liquidity,
            a.buys_24h,
            a.sells_24h,
            a.buy_ratio,
            a.total_txns,
            a.age_hours,
            a.volume_acceleration_1h_vs_6h,
            a.volume_acceleration_6h_vs_24h,
            a.velocite_pump,
            a.type_pump,
            COALESCE(MAX(pt.highest_price), a.entry_price) as highest_price
        FROM alerts a
        LEFT JOIN price_tracking pt ON a.id = pt.alert_id
        GROUP BY a.id
    """)

    alerts = cursor.fetchall()
    print(f"\n Total alertes analysées: {len(alerts):,}\n")

    # Organisation par réseau
    by_network = defaultdict(list)
    winners = []
    losers = []

    for alert in alerts:
        (id, network, token_name, score, base_score, momentum_bonus, confidence_score,
         entry_price, tp1_price, tp2_price, tp3_price,
         volume_24h, volume_6h, volume_1h, liquidity,
         buys_24h, sells_24h, buy_ratio, total_txns, age_hours,
         vol_accel_1h_6h, vol_accel_6h_24h, velocite_pump, type_pump,
         highest_price) = alert

        # Calculer si TP1 atteint
        tp1_hit = highest_price >= tp1_price * 0.995 if tp1_price and highest_price else False

        alert_data = {
            'id': id,
            'network': network,
            'token_name': token_name,
            'score': score or 0,
            'base_score': base_score or 0,
            'momentum_bonus': momentum_bonus or 0,
            'confidence_score': confidence_score or 0,
            'entry_price': entry_price or 0,
            'tp1_price': tp1_price or 0,
            'tp2_price': tp2_price or 0,
            'tp3_price': tp3_price or 0,
            'volume_24h': volume_24h or 0,
            'volume_6h': volume_6h or 0,
            'volume_1h': volume_1h or 0,
            'liquidity': liquidity or 0,
            'buys_24h': buys_24h or 0,
            'sells_24h': sells_24h or 0,
            'buy_ratio': buy_ratio or 0,
            'total_txns': total_txns or 0,
            'age_hours': age_hours or 0,
            'vol_accel_1h_6h': vol_accel_1h_6h or 0,
            'vol_accel_6h_24h': vol_accel_6h_24h or 0,
            'velocite_pump': velocite_pump or 0,
            'type_pump': type_pump or 'UNKNOWN',
            'highest_price': highest_price or 0,
            'tp1_hit': tp1_hit,
            'roi': ((highest_price / entry_price - 1) * 100) if entry_price and highest_price else 0
        }

        by_network[network].append(alert_data)

        if tp1_hit:
            winners.append(alert_data)
        else:
            losers.append(alert_data)

    print("=" * 100)
    print("1. ANALYSE PAR SCORE")
    print("=" * 100)

    # Analyse par tranches de score
    score_ranges = [(0, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 101)]

    print(f"\n{'Score Range':<15} {'Total':>8} {'Winners':>8} {'Win Rate':>10} {'Avg ROI':>10}")
    print("-" * 100)

    for min_score, max_score in score_ranges:
        range_alerts = [a for a in alerts if min_score <= (a[3] or 0) < max_score]
        range_winners = [a for a in range_alerts if a[24] >= a[8] * 0.995 if a[8] and a[24]]

        total = len(range_alerts)
        winners_count = len(range_winners)
        win_rate = (winners_count / total * 100) if total > 0 else 0
        avg_roi = mean([((a[24] / a[7] - 1) * 100) for a in range_alerts if a[7] and a[24]]) if range_alerts else 0

        print(f"{min_score}-{max_score-1:<12} {total:8} {winners_count:8} {win_rate:9.1f}% {avg_roi:9.1f}%")

    print("\n" + "=" * 100)
    print("2. ANALYSE PAR TYPE DE PUMP")
    print("=" * 100)

    pump_types = defaultdict(lambda: {'total': 0, 'winners': 0, 'rois': []})

    for alert in winners + losers:
        pump_type = alert['type_pump']
        pump_types[pump_type]['total'] += 1
        if alert['tp1_hit']:
            pump_types[pump_type]['winners'] += 1
        pump_types[pump_type]['rois'].append(alert['roi'])

    print(f"\n{'Type Pump':<20} {'Total':>8} {'Winners':>8} {'Win Rate':>10} {'Avg ROI':>10}")
    print("-" * 100)

    for pump_type in sorted(pump_types.keys()):
        data = pump_types[pump_type]
        win_rate = (data['winners'] / data['total'] * 100) if data['total'] > 0 else 0
        avg_roi = mean(data['rois']) if data['rois'] else 0
        print(f"{pump_type:<20} {data['total']:8} {data['winners']:8} {win_rate:9.1f}% {avg_roi:9.1f}%")

    print("\n" + "=" * 100)
    print("3. ANALYSE PAR ÂGE DU TOKEN")
    print("=" * 100)

    age_ranges = [(0, 1), (1, 6), (6, 24), (24, 72), (72, 168), (168, 999999)]
    age_labels = ["<1h", "1-6h", "6-24h", "1-3d", "3-7d", ">7d"]

    print(f"\n{'Age Range':<15} {'Total':>8} {'Winners':>8} {'Win Rate':>10} {'Avg ROI':>10}")
    print("-" * 100)

    for (min_age, max_age), label in zip(age_ranges, age_labels):
        age_alerts = [a for a in winners + losers if min_age <= a['age_hours'] < max_age]
        age_winners = [a for a in age_alerts if a['tp1_hit']]

        total = len(age_alerts)
        winners_count = len(age_winners)
        win_rate = (winners_count / total * 100) if total > 0 else 0
        avg_roi = mean([a['roi'] for a in age_alerts]) if age_alerts else 0

        print(f"{label:<15} {total:8} {winners_count:8} {win_rate:9.1f}% {avg_roi:9.1f}%")

    print("\n" + "=" * 100)
    print("4. ANALYSE PAR BUY RATIO")
    print("=" * 100)

    buy_ratio_ranges = [(0, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)]

    print(f"\n{'Buy Ratio':<15} {'Total':>8} {'Winners':>8} {'Win Rate':>10} {'Avg ROI':>10}")
    print("-" * 100)

    for min_ratio, max_ratio in buy_ratio_ranges:
        ratio_alerts = [a for a in winners + losers if min_ratio <= a['buy_ratio'] < max_ratio]
        ratio_winners = [a for a in ratio_alerts if a['tp1_hit']]

        total = len(ratio_alerts)
        winners_count = len(ratio_winners)
        win_rate = (winners_count / total * 100) if total > 0 else 0
        avg_roi = mean([a['roi'] for a in ratio_alerts]) if ratio_alerts else 0

        print(f"{min_ratio:.1f}-{max_ratio:.1f:<9} {total:8} {winners_count:8} {win_rate:9.1f}% {avg_roi:9.1f}%")

    print("\n" + "=" * 100)
    print("5. ANALYSE PAR VÉLOCITÉ DE PUMP")
    print("=" * 100)

    velocity_ranges = [(0, 50), (50, 100), (100, 200), (200, 500), (500, 1000), (1000, 999999)]

    print(f"\n{'Velocity':<15} {'Total':>8} {'Winners':>8} {'Win Rate':>10} {'Avg ROI':>10}")
    print("-" * 100)

    for min_vel, max_vel in velocity_ranges:
        vel_alerts = [a for a in winners + losers if min_vel <= a['velocite_pump'] < max_vel]
        vel_winners = [a for a in vel_alerts if a['tp1_hit']]

        total = len(vel_alerts)
        winners_count = len(vel_winners)
        win_rate = (winners_count / total * 100) if total > 0 else 0
        avg_roi = mean([a['roi'] for a in vel_alerts]) if vel_alerts else 0

        label = f"{min_vel}-{max_vel}" if max_vel < 999999 else f">{min_vel}"
        print(f"{label:<15} {total:8} {winners_count:8} {win_rate:9.1f}% {avg_roi:9.1f}%")

    print("\n" + "=" * 100)
    print("6. COMPARAISON WINNERS vs LOSERS - MÉTRIQUES MOYENNES")
    print("=" * 100)

    if winners and losers:
        print(f"\n{'Métrique':<30} {'Winners (Avg)':>20} {'Losers (Avg)':>20} {'Différence':>15}")
        print("-" * 100)

        metrics = [
            ('Score', 'score'),
            ('Base Score', 'base_score'),
            ('Momentum Bonus', 'momentum_bonus'),
            ('Confidence Score', 'confidence_score'),
            ('Liquidity ($)', 'liquidity'),
            ('Volume 24h ($)', 'volume_24h'),
            ('Volume 1h ($)', 'volume_1h'),
            ('Total Txns', 'total_txns'),
            ('Buy Ratio', 'buy_ratio'),
            ('Age (hours)', 'age_hours'),
            ('Vol Accel 1h/6h (%)', 'vol_accel_1h_6h'),
            ('Vol Accel 6h/24h (%)', 'vol_accel_6h_24h'),
            ('Vélocité Pump', 'velocite_pump')
        ]

        for label, key in metrics:
            winner_avg = mean([a[key] for a in winners if a[key] is not None])
            loser_avg = mean([a[key] for a in losers if a[key] is not None])
            diff = winner_avg - loser_avg
            diff_pct = (diff / loser_avg * 100) if loser_avg != 0 else 0

            print(f"{label:<30} {winner_avg:>20,.2f} {loser_avg:>20,.2f} {diff_pct:>14,.1f}%")

    print("\n" + "=" * 100)
    print("7. ANALYSE PAR RÉSEAU - DÉTAILS")
    print("=" * 100)

    for network in sorted(by_network.keys()):
        network_alerts = by_network[network]
        network_winners = [a for a in network_alerts if a['tp1_hit']]

        if not network_alerts:
            continue

        print(f"\n--- {network.upper()} ---")
        print(f"Total: {len(network_alerts)} | Winners: {len(network_winners)} | Win Rate: {len(network_winners)/len(network_alerts)*100:.1f}%")

        if network_winners:
            print(f"\nWinners - Moyennes:")
            print(f"  Score: {mean([a['score'] for a in network_winners]):.1f}")
            print(f"  Liquidity: ${mean([a['liquidity'] for a in network_winners]):,.0f}")
            print(f"  Volume 24h: ${mean([a['volume_24h'] for a in network_winners]):,.0f}")
            print(f"  Buy Ratio: {mean([a['buy_ratio'] for a in network_winners]):.2f}")
            print(f"  Age: {mean([a['age_hours'] for a in network_winners]):.1f}h")
            print(f"  ROI Moyen: {mean([a['roi'] for a in network_winners]):.1f}%")

    print("\n" + "=" * 100)
    print("8. RECOMMANDATIONS SMART POUR AMÉLIORER WIN RATE")
    print("=" * 100)

    print("\nBasé sur l'analyse des patterns de succès:\n")

    # Recommandation 1: Score minimum
    score_70_plus = [a for a in winners + losers if a['score'] >= 70]
    score_70_winners = [a for a in score_70_plus if a['tp1_hit']]
    if score_70_plus:
        wr_70 = len(score_70_winners) / len(score_70_plus) * 100
        print(f"1. SCORE MINIMUM")
        print(f"   Alertes avec score >= 70: Win rate = {wr_70:.1f}%")
        if wr_70 > 30:
            print(f"   Recommandation: Augmenter score minimum à 70+ pour tous les réseaux")
        print()

    # Recommandation 2: Buy Ratio optimal
    high_buy_ratio = [a for a in winners + losers if a['buy_ratio'] >= 0.6]
    high_buy_winners = [a for a in high_buy_ratio if a['tp1_hit']]
    if high_buy_ratio:
        wr_buy = len(high_buy_winners) / len(high_buy_ratio) * 100
        print(f"2. BUY RATIO OPTIMAL")
        print(f"   Alertes avec buy_ratio >= 0.6: Win rate = {wr_buy:.1f}%")
        if wr_buy > 35:
            print(f"   Recommandation: Ajouter filtre buy_ratio minimum à 0.6")
        print()

    # Recommandation 3: Âge optimal
    young_tokens = [a for a in winners + losers if a['age_hours'] <= 24]
    young_winners = [a for a in young_tokens if a['tp1_hit']]
    if young_tokens:
        wr_young = len(young_winners) / len(young_tokens) * 100
        print(f"3. ÂGE DU TOKEN")
        print(f"   Tokens <= 24h: Win rate = {wr_young:.1f}%")
        if wr_young > 30:
            print(f"   Recommandation: Privilégier les tokens jeunes (<24h)")
        print()

    # Recommandation 4: Type de pump
    if pump_types:
        best_pump_type = max(pump_types.items(),
                            key=lambda x: x[1]['winners']/x[1]['total'] if x[1]['total'] > 10 else 0)
        if best_pump_type[1]['total'] > 10:
            wr_pump = best_pump_type[1]['winners'] / best_pump_type[1]['total'] * 100
            print(f"4. TYPE DE PUMP OPTIMAL")
            print(f"   Meilleur type: {best_pump_type[0]} - Win rate = {wr_pump:.1f}%")
            print(f"   Recommandation: Privilégier les pumps de type '{best_pump_type[0]}'")
            print()

    # Recommandation 5: Seuils par réseau
    print(f"5. SEUILS OPTIMAUX PAR RÉSEAU")
    for network in ['arbitrum', 'base']:
        network_alerts = by_network.get(network, [])
        if not network_alerts:
            continue

        network_winners = [a for a in network_alerts if a['tp1_hit']]

        if network_winners:
            avg_liq_winners = mean([a['liquidity'] for a in network_winners])
            avg_vol_winners = mean([a['volume_24h'] for a in network_winners])
            avg_txns_winners = mean([a['total_txns'] for a in network_winners])

            print(f"\n   {network.upper()} - Moyennes des WINNERS:")
            print(f"     Liquidity: ${avg_liq_winners:,.0f}")
            print(f"     Volume 24h: ${avg_vol_winners:,.0f}")
            print(f"     Txns: {avg_txns_winners:.0f}")
            print(f"     Recommandation: Utiliser ces valeurs comme nouveaux seuils minimum")

    print("\n" + "=" * 100)
    print("ANALYSE TERMINÉE")
    print("=" * 100)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DB_PATH = sys.argv[1]

    analyze_advanced_patterns()
