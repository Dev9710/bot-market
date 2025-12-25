#!/usr/bin/env python3
"""
ULTIMATE SIMPLE ANALYZER - Version simplifiée utilisant highest_price
Analyse exhaustive sans dépendre des booleans de price_tracking
"""
import sqlite3
import sys
from collections import defaultdict
from statistics import mean, median

DB_PATH = "/data/alerts_history.db"

def simple_ultimate_analysis():
    print("=" * 120)
    print("ULTIMATE SIMPLE ANALYZER - ANALYSE EXHAUSTIVE DES PATTERNS")
    print("=" * 120)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupération avec JOIN pour avoir highest_price
    cursor.execute("""
        SELECT
            a.id,
            a.network,
            a.token_name,
            a.token_address,
            a.score,
            a.base_score,
            a.momentum_bonus,
            a.entry_price,
            a.tp1_price,
            a.tp2_price,
            a.tp3_price,
            a.stop_loss_price,
            a.volume_24h,
            a.volume_1h,
            a.liquidity,
            a.total_txns,
            a.age_hours,
            a.velocite_pump,
            a.type_pump,
            a.created_at,
            COALESCE(MAX(pt.highest_price), a.entry_price) as highest_price,
            COALESCE(MIN(pt.lowest_price), a.entry_price) as lowest_price
        FROM alerts a
        LEFT JOIN price_tracking pt ON a.id = pt.alert_id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    """)

    alerts = cursor.fetchall()
    print(f"\n[1/7] Total alertes analysées: {len(alerts):,}\n")

    # Organisation
    winners_tp1 = []
    winners_tp2 = []
    winners_tp3 = []
    losers = []
    by_network = defaultdict(list)
    by_token = defaultdict(list)

    for alert in alerts:
        (id, network, token_name, token_address, score, base_score, momentum_bonus,
         entry_price, tp1_price, tp2_price, tp3_price, stop_loss_price,
         volume_24h, volume_1h, liquidity, total_txns, age_hours,
         velocite_pump, type_pump, created_at, highest_price, lowest_price) = alert

        # Skip si données manquantes
        if not entry_price or not tp1_price or not highest_price:
            continue

        # Calculer ROI et drawdown
        max_roi = ((highest_price / entry_price - 1) * 100) if entry_price else 0
        max_dd = ((lowest_price / entry_price - 1) * 100) if entry_price and lowest_price else 0

        # Déterminer si TP atteints
        tp1_hit = highest_price >= tp1_price * 0.995
        tp2_hit = highest_price >= tp2_price * 0.995 if tp2_price else False
        tp3_hit = highest_price >= tp3_price * 0.995 if tp3_price else False

        alert_dict = {
            'id': id,
            'network': network,
            'token_name': token_name,
            'token_address': token_address,
            'score': score or 0,
            'base_score': base_score or 0,
            'momentum_bonus': momentum_bonus or 0,
            'entry_price': entry_price,
            'tp1_price': tp1_price,
            'tp2_price': tp2_price or 0,
            'tp3_price': tp3_price or 0,
            'stop_loss_price': stop_loss_price or 0,
            'volume_24h': volume_24h or 0,
            'volume_1h': volume_1h or 0,
            'liquidity': liquidity or 0,
            'total_txns': total_txns or 0,
            'age_hours': age_hours or 0,
            'velocite_pump': velocite_pump or 0,
            'type_pump': type_pump or 'UNKNOWN',
            'highest_price': highest_price,
            'lowest_price': lowest_price,
            'max_roi': max_roi,
            'max_dd': max_dd,
            'tp1_hit': tp1_hit,
            'tp2_hit': tp2_hit,
            'tp3_hit': tp3_hit,
        }

        if tp1_hit:
            winners_tp1.append(alert_dict)
        if tp2_hit:
            winners_tp2.append(alert_dict)
        if tp3_hit:
            winners_tp3.append(alert_dict)
        if not tp1_hit:
            losers.append(alert_dict)

        by_network[network].append(alert_dict)
        by_token[token_address].append(alert_dict)

    print(f"Winners TP1: {len(winners_tp1)} ({len(winners_tp1)/(len(winners_tp1)+len(losers))*100:.1f}%)")
    print(f"Winners TP2: {len(winners_tp2)} ({len(winners_tp2)/(len(winners_tp1)+len(losers))*100:.1f}%)")
    print(f"Winners TP3: {len(winners_tp3)} ({len(winners_tp3)/(len(winners_tp1)+len(losers))*100:.1f}%)")
    print(f"Losers: {len(losers)} ({len(losers)/(len(winners_tp1)+len(losers))*100:.1f}%)")

    # ========== SECTION 1: DRAWDOWN ANALYSIS ==========
    print("\n" + "=" * 120)
    print("[2/7] ANALYSE DRAWDOWN - RISQUE RÉEL")
    print("=" * 120)

    dd_ranges = [(0, -5), (-5, -10), (-10, -15), (-15, -20), (-20, -30), (-30, -100)]

    print(f"\n{'Drawdown':<15} {'TP1 Winners':>15} {'Losers':>15} {'Total':>10} {'Win Rate':>12}")
    print("-" * 120)

    for max_dd, min_dd in dd_ranges:
        w_in_range = [w for w in winners_tp1 if min_dd <= w['max_dd'] < max_dd]
        l_in_range = [l for l in losers if min_dd <= l['max_dd'] < max_dd]
        total = len(w_in_range) + len(l_in_range)
        wr = (len(w_in_range) / total * 100) if total > 0 else 0

        print(f"{max_dd} à {min_dd}%{'':<5} {len(w_in_range):>15} {len(l_in_range):>15} {total:>10} {wr:>11.1f}%")

    # Winners sans drawdown significatif
    safe_winners = [w for w in winners_tp1 if w['max_dd'] > -10]
    print(f"\nWinners TP1 avec drawdown <10%: {len(safe_winners)} ({len(safe_winners)/len(winners_tp1)*100:.1f}%)")

    # ========== SECTION 2: PATTERNS COMBINÉS ==========
    print("\n" + "=" * 120)
    print("[3/7] PATTERNS GAGNANTS - COMBINAISONS OPTIMALES")
    print("=" * 120)

    score_ranges = [(50, 70), (70, 80), (80, 90), (90, 101)]
    pump_types = ['RAPIDE', 'TRES_RAPIDE', 'PARABOLIQUE', 'LENT', 'NORMAL']

    combos = []
    for score_min, score_max in score_ranges:
        for pump_type in pump_types:
            combo_alerts = [a for a in winners_tp1 + losers
                          if score_min <= a['score'] < score_max and a['type_pump'] == pump_type]
            combo_winners = [a for a in combo_alerts if a['tp1_hit']]

            if len(combo_alerts) >= 10:
                wr = (len(combo_winners) / len(combo_alerts) * 100)
                avg_roi = mean([w['max_roi'] for w in combo_winners]) if combo_winners else 0

                combos.append({
                    'label': f"Score {score_min}-{score_max} + {pump_type}",
                    'total': len(combo_alerts),
                    'winners': len(combo_winners),
                    'win_rate': wr,
                    'avg_roi': avg_roi
                })

    combos.sort(key=lambda x: x['win_rate'], reverse=True)

    print(f"\n{'Combinaison':<40} {'Total':>10} {'Winners':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    for combo in combos[:20]:
        print(f"{combo['label']:<40} {combo['total']:>10} {combo['winners']:>10} {combo['win_rate']:>11.1f}% {combo['avg_roi']:>11.1f}%")

    # ========== SECTION 3: TOKENS RÉCURRENTS ==========
    print("\n" + "=" * 120)
    print("[4/7] TOKENS AVEC MULTIPLES ALERTES")
    print("=" * 120)

    multi_tokens = {addr: alerts for addr, alerts in by_token.items() if len(alerts) > 1}

    token_stats = []
    for addr, token_alerts in multi_tokens.items():
        tp1_count = len([a for a in token_alerts if a['tp1_hit']])
        wr = (tp1_count / len(token_alerts) * 100)
        best_roi = max([a['max_roi'] for a in token_alerts])

        if len(token_alerts) >= 3:  # Au moins 3 alertes
            token_stats.append({
                'name': token_alerts[0]['token_name'],
                'count': len(token_alerts),
                'tp1_hits': tp1_count,
                'win_rate': wr,
                'best_roi': best_roi
            })

    token_stats.sort(key=lambda x: x['win_rate'], reverse=True)

    print(f"\n{'Token':<50} {'Alertes':>10} {'TP1 Hits':>10} {'Win Rate':>12} {'Best ROI':>12}")
    print("-" * 120)

    for t in token_stats[:20]:
        print(f"{t['name']:<50} {t['count']:>10} {t['tp1_hits']:>10} {t['win_rate']:>11.1f}% {t['best_roi']:>11.1f}%")

    # ========== SECTION 4: ANALYSE PAR RÉSEAU ==========
    print("\n" + "=" * 120)
    print("[5/7] STRATÉGIE OPTIMALE PAR RÉSEAU")
    print("=" * 120)

    for network in sorted(by_network.keys()):
        alerts_net = by_network[network]
        winners_net = [a for a in alerts_net if a['tp1_hit']]

        if not winners_net:
            continue

        print(f"\n{network.upper()} - {len(alerts_net)} alertes | {len(winners_net)} winners | {len(winners_net)/len(alerts_net)*100:.1f}% WR")
        print("-" * 120)

        print(f"Caractéristiques MOYENNES des WINNERS:")
        print(f"  Score: {mean([w['score'] for w in winners_net]):.1f}")
        print(f"  Liquidity: ${mean([w['liquidity'] for w in winners_net]):,.0f}")
        print(f"  Volume 24h: ${mean([w['volume_24h'] for w in winners_net]):,.0f}")
        print(f"  Volume 1h: ${mean([w['volume_1h'] for w in winners_net]):,.0f}")
        print(f"  Txns: {mean([w['total_txns'] for w in winners_net]):.0f}")
        print(f"  Age: {mean([w['age_hours'] for w in winners_net]):.1f}h")
        print(f"  Vélocité: {mean([w['velocite_pump'] for w in winners_net]):.1f}")
        print(f"  ROI moyen: {mean([w['max_roi'] for w in winners_net]):.1f}%")
        print(f"  Drawdown moyen: {mean([w['max_dd'] for w in winners_net]):.1f}%")

        # Type pump dominant
        pump_dist = defaultdict(int)
        for w in winners_net:
            pump_dist[w['type_pump']] += 1
        best_pump = max(pump_dist.items(), key=lambda x: x[1]) if pump_dist else ('N/A', 0)
        print(f"  Type pump dominant: {best_pump[0]} ({best_pump[1]}/{len(winners_net)})")

        # Seuils recommandés (25e percentile)
        if len(winners_net) >= 4:
            liq_p25 = sorted([w['liquidity'] for w in winners_net])[len(winners_net)//4]
            vol_p25 = sorted([w['volume_24h'] for w in winners_net])[len(winners_net)//4]
            txns_p25 = sorted([w['total_txns'] for w in winners_net])[len(winners_net)//4]

            print(f"\nSEUILS RECOMMANDÉS (25th percentile):")
            print(f"  Liquidity min: ${liq_p25:,.0f}")
            print(f"  Volume 24h min: ${vol_p25:,.0f}")
            print(f"  Txns min: {txns_p25:.0f}")

    # ========== SECTION 5: PATTERNS HAUTE CONFIANCE ==========
    print("\n" + "=" * 120)
    print("[6/7] PATTERNS HAUTE CONFIANCE (Win Rate >60%)")
    print("=" * 120)

    high_wr_patterns = []

    for network in by_network.keys():
        for score_min, score_max in score_ranges:
            for pump_type in pump_types:
                pattern_alerts = [a for a in winners_tp1 + losers
                                if a['network'] == network
                                and score_min <= a['score'] < score_max
                                and a['type_pump'] == pump_type]

                pattern_winners = [a for a in pattern_alerts if a['tp1_hit']]

                if len(pattern_alerts) >= 10:
                    wr = (len(pattern_winners) / len(pattern_alerts) * 100)

                    if wr >= 60:
                        avg_roi = mean([w['max_roi'] for w in pattern_winners]) if pattern_winners else 0

                        high_wr_patterns.append({
                            'pattern': f"{network.upper()} | Score {score_min}-{score_max} | {pump_type}",
                            'total': len(pattern_alerts),
                            'winners': len(pattern_winners),
                            'win_rate': wr,
                            'avg_roi': avg_roi
                        })

    if high_wr_patterns:
        high_wr_patterns.sort(key=lambda x: x['win_rate'], reverse=True)

        print(f"\n{'Pattern':<60} {'Total':>10} {'Winners':>10} {'Win Rate':>12} {'Avg ROI':>12}")
        print("-" * 120)

        for p in high_wr_patterns[:15]:
            print(f"{p['pattern']:<60} {p['total']:>10} {p['winners']:>10} {p['win_rate']:>11.1f}% {p['avg_roi']:>11.1f}%")
    else:
        print("\nAucun pattern avec >60% win rate trouvé (ajuster critère si nécessaire)")

    # ========== SECTION 6: COMPARAISON WINNERS VS LOSERS ==========
    print("\n" + "=" * 120)
    print("[7/7] COMPARAISON WINNERS vs LOSERS - DIFFÉRENCES CLÉS")
    print("=" * 120)

    metrics = [
        ('Score', 'score'),
        ('Liquidity', 'liquidity'),
        ('Volume 24h', 'volume_24h'),
        ('Volume 1h', 'volume_1h'),
        ('Total Txns', 'total_txns'),
        ('Age (hours)', 'age_hours'),
        ('Vélocité Pump', 'velocite_pump'),
    ]

    print(f"\n{'Métrique':<20} {'Winners (Avg)':>20} {'Losers (Avg)':>20} {'Différence':>15}")
    print("-" * 120)

    for label, key in metrics:
        w_avg = mean([w[key] for w in winners_tp1 if w[key] is not None])
        l_avg = mean([l[key] for l in losers if l[key] is not None])
        diff_pct = ((w_avg - l_avg) / l_avg * 100) if l_avg != 0 else 0

        print(f"{label:<20} {w_avg:>20,.2f} {l_avg:>20,.2f} {diff_pct:>14.1f}%")

    # ========== RÉSUMÉ EXÉCUTIF ==========
    print("\n" + "=" * 120)
    print("RÉSUMÉ EXÉCUTIF")
    print("=" * 120)

    print(f"\n1. WIN RATE GLOBAL: {len(winners_tp1)/(len(winners_tp1)+len(losers))*100:.1f}%")

    print(f"\n2. MEILLEURE COMBINAISON:")
    if combos:
        best = combos[0]
        print(f"   {best['label']}: {best['win_rate']:.1f}% WR | {best['avg_roi']:.1f}% ROI")

    print(f"\n3. PATTERNS HAUTE CONFIANCE:")
    if high_wr_patterns:
        print(f"   {len(high_wr_patterns)} patterns avec >60% WR trouvés")
        best_pattern = high_wr_patterns[0]
        print(f"   Meilleur: {best_pattern['pattern']}")
        print(f"   Win Rate: {best_pattern['win_rate']:.1f}% | ROI: {best_pattern['avg_roi']:.1f}%")

    print(f"\n4. RÉSEAU LE PLUS PERFORMANT:")
    network_perfs = []
    for net, alerts in by_network.items():
        winners = [a for a in alerts if a['tp1_hit']]
        if alerts:
            wr = len(winners) / len(alerts) * 100
            avg_roi = mean([w['max_roi'] for w in winners]) if winners else 0
            network_perfs.append((net, wr, avg_roi))

    network_perfs.sort(key=lambda x: x[1], reverse=True)
    if network_perfs:
        best_net = network_perfs[0]
        print(f"   {best_net[0].upper()}: {best_net[1]:.1f}% WR | {best_net[2]:.1f}% ROI")

    print("\n" + "=" * 120)
    print("ANALYSE TERMINÉE")
    print("=" * 120)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DB_PATH = sys.argv[1]

    simple_ultimate_analysis()
