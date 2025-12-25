#!/usr/bin/env python3
"""
ULTIMATE PATTERN ANALYZER - Analyse exhaustive de 3000+ alertes
Trouve les patterns gagnants systématiques et stratégies optimales par réseau
"""
import sqlite3
import sys
from collections import defaultdict
from statistics import mean, median, stdev
from datetime import datetime, timedelta

DB_PATH = "/data/alerts_history.db"

def ultimate_analysis():
    print("=" * 120)
    print("ULTIMATE PATTERN ANALYZER - ANALYSE EXHAUSTIVE")
    print("=" * 120)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ========== 1. RÉCUPÉRATION DONNÉES COMPLÈTES ==========
    print("\n[1/10] Récupération des données...")

    cursor.execute("""
        SELECT
            a.id,
            a.network,
            a.token_name,
            a.token_address,
            a.score,
            a.base_score,
            a.momentum_bonus,
            a.confidence_score,
            a.entry_price,
            a.tp1_price,
            a.tp2_price,
            a.tp3_price,
            a.stop_loss_price,
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
            a.created_at,
            a.tp1_percent,
            a.tp2_percent,
            a.tp3_percent,
            a.stop_loss_percent
        FROM alerts a
        ORDER BY a.created_at DESC
    """)

    alerts = cursor.fetchall()
    print(f"   Total alertes: {len(alerts):,}")

    # ========== 2. RÉCUPÉRATION TRACKING TEMPOREL ==========
    print("\n[2/10] Analyse temporelle des performances...")

    timing_data = {}
    for alert in alerts:
        alert_id = alert[0]

        cursor.execute("""
            SELECT
                minutes_after_alert,
                price,
                roi_percent,
                tp1_hit,
                tp2_hit,
                tp3_hit,
                sl_hit,
                highest_price,
                lowest_price
            FROM price_tracking
            WHERE alert_id = ?
            ORDER BY minutes_after_alert ASC
        """, (alert_id,))

        tracking = cursor.fetchall()

        if tracking:
            # Analyser timing des TP
            tp1_time = None
            tp2_time = None
            tp3_time = None
            sl_time = None
            max_price = max([t[7] for t in tracking if t[7]]) if any(t[7] for t in tracking) else alert[8]
            min_price = min([t[8] for t in tracking if t[8]]) if any(t[8] for t in tracking) else alert[8]

            for t in tracking:
                minutes, price, roi, tp1, tp2, tp3, sl, hp, lp = t
                if tp1 and tp1_time is None:
                    tp1_time = minutes
                if tp2 and tp2_time is None:
                    tp2_time = minutes
                if tp3 and tp3_time is None:
                    tp3_time = minutes
                if sl and sl_time is None:
                    sl_time = minutes

            timing_data[alert_id] = {
                'tp1_time': tp1_time,
                'tp2_time': tp2_time,
                'tp3_time': tp3_time,
                'sl_time': sl_time,
                'max_price': max_price,
                'min_price': min_price,
                'max_roi': ((max_price / alert[8] - 1) * 100) if alert[8] and max_price else 0,
                'max_drawdown': ((min_price / alert[8] - 1) * 100) if alert[8] and min_price else 0,
                'tracking_count': len(tracking)
            }

    # ========== 3. ORGANISATION PAR CATÉGORIES ==========
    print("\n[3/10] Catégorisation des alertes...")

    winners_tp1 = []
    winners_tp2 = []
    winners_tp3 = []
    losers = []
    by_network = defaultdict(list)
    by_token = defaultdict(list)

    for alert in alerts:
        alert_id = alert[0]
        timing = timing_data.get(alert_id, {})

        alert_dict = {
            'id': alert_id,
            'network': alert[1],
            'token_name': alert[2],
            'token_address': alert[3],
            'score': alert[4] or 0,
            'base_score': alert[5] or 0,
            'momentum_bonus': alert[6] or 0,
            'confidence_score': alert[7] or 0,
            'entry_price': alert[8] or 0,
            'tp1_price': alert[9] or 0,
            'tp2_price': alert[10] or 0,
            'tp3_price': alert[11] or 0,
            'stop_loss_price': alert[12] or 0,
            'volume_24h': alert[13] or 0,
            'volume_6h': alert[14] or 0,
            'volume_1h': alert[15] or 0,
            'liquidity': alert[16] or 0,
            'buys_24h': alert[17] or 0,
            'sells_24h': alert[18] or 0,
            'buy_ratio': alert[19] or 0,
            'total_txns': alert[20] or 0,
            'age_hours': alert[21] or 0,
            'vol_accel_1h_6h': alert[22] or 0,
            'vol_accel_6h_24h': alert[23] or 0,
            'velocite_pump': alert[24] or 0,
            'type_pump': alert[25] or 'UNKNOWN',
            'created_at': alert[26],
            'tp1_percent': alert[27] or 0,
            'tp2_percent': alert[28] or 0,
            'tp3_percent': alert[29] or 0,
            'stop_loss_percent': alert[30] or 0,
            'tp1_time': timing.get('tp1_time'),
            'tp2_time': timing.get('tp2_time'),
            'tp3_time': timing.get('tp3_time'),
            'sl_time': timing.get('sl_time'),
            'max_price': timing.get('max_price', alert[8]),
            'min_price': timing.get('min_price', alert[8]),
            'max_roi': timing.get('max_roi', 0),
            'max_drawdown': timing.get('max_drawdown', 0),
        }

        # Catégorisation
        if alert_dict['tp1_time'] is not None:
            winners_tp1.append(alert_dict)
        if alert_dict['tp2_time'] is not None:
            winners_tp2.append(alert_dict)
        if alert_dict['tp3_time'] is not None:
            winners_tp3.append(alert_dict)
        if alert_dict['tp1_time'] is None:
            losers.append(alert_dict)

        by_network[alert[1]].append(alert_dict)
        by_token[alert[3]].append(alert_dict)

    print(f"   Winners TP1: {len(winners_tp1)}")
    print(f"   Winners TP2: {len(winners_tp2)}")
    print(f"   Winners TP3: {len(winners_tp3)}")
    print(f"   Losers: {len(losers)}")

    # ========== 4. ANALYSE TIMING DÉTAILLÉE ==========
    print("\n" + "=" * 120)
    print("SECTION 1: ANALYSE TIMING - QUAND LES TP SONT ATTEINTS")
    print("=" * 120)

    timing_ranges = [
        (0, 5, "<5min"),
        (5, 15, "5-15min"),
        (15, 30, "15-30min"),
        (30, 60, "30-60min"),
        (60, 180, "1-3h"),
        (180, 360, "3-6h"),
        (360, 1440, "6-24h"),
        (1440, 4320, "1-3d"),
        (4320, 999999, ">3d")
    ]

    print(f"\n{'Timeframe':<15} {'TP1 Count':>12} {'TP2 Count':>12} {'TP3 Count':>12} {'% TP1':>10}")
    print("-" * 120)

    for min_t, max_t, label in timing_ranges:
        tp1_count = len([w for w in winners_tp1 if w['tp1_time'] and min_t <= w['tp1_time'] < max_t])
        tp2_count = len([w for w in winners_tp2 if w['tp2_time'] and min_t <= w['tp2_time'] < max_t])
        tp3_count = len([w for w in winners_tp3 if w['tp3_time'] and min_t <= w['tp3_time'] < max_t])
        pct = (tp1_count / len(winners_tp1) * 100) if winners_tp1 else 0

        print(f"{label:<15} {tp1_count:>12} {tp2_count:>12} {tp3_count:>12} {pct:>9.1f}%")

    # Timing moyen par réseau
    print(f"\n{'Réseau':<15} {'Avg TP1 Time':>15} {'Avg TP2 Time':>15} {'Avg TP3 Time':>15}")
    print("-" * 120)

    for network in sorted(by_network.keys()):
        network_tp1 = [w for w in winners_tp1 if w['network'] == network and w['tp1_time']]
        network_tp2 = [w for w in winners_tp2 if w['network'] == network and w['tp2_time']]
        network_tp3 = [w for w in winners_tp3 if w['network'] == network and w['tp3_time']]

        avg_tp1 = mean([w['tp1_time'] for w in network_tp1]) if network_tp1 else 0
        avg_tp2 = mean([w['tp2_time'] for w in network_tp2]) if network_tp2 else 0
        avg_tp3 = mean([w['tp3_time'] for w in network_tp3]) if network_tp3 else 0

        print(f"{network.upper():<15} {avg_tp1:>12.0f}min {avg_tp2:>12.0f}min {avg_tp3:>12.0f}min")

    # ========== 5. ANALYSE DRAWDOWN ==========
    print("\n" + "=" * 120)
    print("SECTION 2: ANALYSE DRAWDOWN - RISQUE AVANT PROFIT")
    print("=" * 120)

    dd_ranges = [
        (0, -5, "0 à -5%"),
        (-5, -10, "-5 à -10%"),
        (-10, -15, "-10 à -15%"),
        (-15, -20, "-15 à -20%"),
        (-20, -30, "-20 à -30%"),
        (-30, -100, "> -30%")
    ]

    print(f"\n{'Drawdown Range':<20} {'TP1 Winners':>15} {'Losers':>15} {'Win Rate':>12}")
    print("-" * 120)

    for max_dd, min_dd, label in dd_ranges:
        tp1_in_range = [w for w in winners_tp1 if min_dd <= w['max_drawdown'] < max_dd]
        losers_in_range = [l for l in losers if min_dd <= l['max_drawdown'] < max_dd]
        total = len(tp1_in_range) + len(losers_in_range)
        wr = (len(tp1_in_range) / total * 100) if total > 0 else 0

        print(f"{label:<20} {len(tp1_in_range):>15} {len(losers_in_range):>15} {wr:>11.1f}%")

    # Winners qui n'ont JAMAIS touché SL
    no_sl_winners = [w for w in winners_tp1 if w['max_drawdown'] > w['stop_loss_percent']]
    print(f"\nWinners TP1 qui n'ont JAMAIS touché SL: {len(no_sl_winners)} ({len(no_sl_winners)/len(winners_tp1)*100:.1f}%)")

    # Winners qui ont touché SL puis récupéré
    sl_then_tp = [w for w in winners_tp1 if w['max_drawdown'] <= w['stop_loss_percent']]
    print(f"Winners TP1 qui ont touché SL puis récupéré: {len(sl_then_tp)} ({len(sl_then_tp)/len(winners_tp1)*100:.1f}%)")

    # ========== 6. PATTERNS GAGNANTS - COMBINAISONS ==========
    print("\n" + "=" * 120)
    print("SECTION 3: PATTERNS GAGNANTS - COMBINAISONS DE VARIABLES")
    print("=" * 120)

    # Combinaison Score + Type Pump
    print(f"\n{'Combo Score + Type Pump':<40} {'Total':>10} {'TP1':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    score_ranges_combo = [(50, 70, "50-70"), (70, 80, "70-80"), (80, 90, "80-90"), (90, 101, "90-100")]
    pump_types_combo = ['RAPIDE', 'TRES_RAPIDE', 'PARABOLIQUE', 'LENT']

    combos = []
    for score_min, score_max, score_label in score_ranges_combo:
        for pump_type in pump_types_combo:
            combo_alerts = [a for a in winners_tp1 + losers
                          if score_min <= a['score'] < score_max and a['type_pump'] == pump_type]
            combo_winners = [a for a in combo_alerts if a['tp1_time'] is not None]

            if len(combo_alerts) >= 5:  # Minimum 5 alertes pour être significatif
                wr = (len(combo_winners) / len(combo_alerts) * 100) if combo_alerts else 0
                avg_roi = mean([w['max_roi'] for w in combo_winners]) if combo_winners else 0

                combos.append({
                    'label': f"Score {score_label} + {pump_type}",
                    'total': len(combo_alerts),
                    'winners': len(combo_winners),
                    'win_rate': wr,
                    'avg_roi': avg_roi
                })

    # Trier par win rate
    combos.sort(key=lambda x: x['win_rate'], reverse=True)

    for combo in combos[:15]:  # Top 15
        print(f"{combo['label']:<40} {combo['total']:>10} {combo['winners']:>10} {combo['win_rate']:>11.1f}% {combo['avg_roi']:>11.1f}%")

    # Combinaison Score + Vélocité
    print(f"\n{'Combo Score + Vélocité':<40} {'Total':>10} {'TP1':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    vel_ranges = [(0, 50, "0-50"), (50, 100, "50-100"), (100, 200, "100-200"), (200, 999999, ">200")]

    vel_combos = []
    for score_min, score_max, score_label in score_ranges_combo:
        for vel_min, vel_max, vel_label in vel_ranges:
            combo_alerts = [a for a in winners_tp1 + losers
                          if score_min <= a['score'] < score_max
                          and vel_min <= a['velocite_pump'] < vel_max]
            combo_winners = [a for a in combo_alerts if a['tp1_time'] is not None]

            if len(combo_alerts) >= 5:
                wr = (len(combo_winners) / len(combo_alerts) * 100) if combo_alerts else 0
                avg_roi = mean([w['max_roi'] for w in combo_winners]) if combo_winners else 0

                vel_combos.append({
                    'label': f"Score {score_label} + Vel {vel_label}",
                    'total': len(combo_alerts),
                    'winners': len(combo_winners),
                    'win_rate': wr,
                    'avg_roi': avg_roi
                })

    vel_combos.sort(key=lambda x: x['win_rate'], reverse=True)

    for combo in vel_combos[:15]:
        print(f"{combo['label']:<40} {combo['total']:>10} {combo['winners']:>10} {combo['win_rate']:>11.1f}% {combo['avg_roi']:>11.1f}%")

    # ========== 7. TOKENS MULTIPLES ALERTES ==========
    print("\n" + "=" * 120)
    print("SECTION 4: TOKENS AVEC MULTIPLES ALERTES - PATTERN DE RE-PUMP")
    print("=" * 120)

    multi_alert_tokens = {addr: alerts for addr, alerts in by_token.items() if len(alerts) > 1}

    print(f"\nTokens avec >1 alerte: {len(multi_alert_tokens)}")
    print(f"\n{'Token':<50} {'Alerts':>8} {'TP1 Hits':>10} {'Win Rate':>12} {'Best ROI':>12}")
    print("-" * 120)

    token_stats = []
    for addr, token_alerts in multi_alert_tokens.items():
        tp1_hits = len([a for a in token_alerts if a['tp1_time'] is not None])
        wr = (tp1_hits / len(token_alerts) * 100) if token_alerts else 0
        best_roi = max([a['max_roi'] for a in token_alerts])

        token_stats.append({
            'name': token_alerts[0]['token_name'],
            'count': len(token_alerts),
            'tp1_hits': tp1_hits,
            'win_rate': wr,
            'best_roi': best_roi
        })

    token_stats.sort(key=lambda x: x['win_rate'], reverse=True)

    for t in token_stats[:20]:
        print(f"{t['name']:<50} {t['count']:>8} {t['tp1_hits']:>10} {t['win_rate']:>11.1f}% {t['best_roi']:>11.1f}%")

    # ========== 8. STRATÉGIE OPTIMALE PAR RÉSEAU ==========
    print("\n" + "=" * 120)
    print("SECTION 5: STRATÉGIE OPTIMALE PAR RÉSEAU")
    print("=" * 120)

    for network in sorted(by_network.keys()):
        network_alerts = by_network[network]
        network_winners = [a for a in network_alerts if a['tp1_time'] is not None]

        if not network_winners:
            continue

        print(f"\n{'='*50} {network.upper()} {'='*50}")
        print(f"Total alertes: {len(network_alerts)} | Winners TP1: {len(network_winners)} | Win Rate: {len(network_winners)/len(network_alerts)*100:.1f}%")

        # Meilleur timing d'entrée
        fast_winners = [w for w in network_winners if w['tp1_time'] and w['tp1_time'] < 60]
        print(f"\nTP1 atteint en <1h: {len(fast_winners)} ({len(fast_winners)/len(network_winners)*100:.1f}% des winners)")

        # Caractéristiques moyennes des winners
        print(f"\nCaractéristiques WINNERS moyens:")
        print(f"  Score moyen: {mean([w['score'] for w in network_winners]):.1f}")
        print(f"  Liquidity moyenne: ${mean([w['liquidity'] for w in network_winners]):,.0f}")
        print(f"  Volume 24h moyen: ${mean([w['volume_24h'] for w in network_winners]):,.0f}")
        print(f"  Volume 1h moyen: ${mean([w['volume_1h'] for w in network_winners]):,.0f}")
        print(f"  Txns moyen: {mean([w['total_txns'] for w in network_winners]):.0f}")
        print(f"  Age moyen: {mean([w['age_hours'] for w in network_winners]):.1f}h")
        print(f"  Vélocité moyenne: {mean([w['velocite_pump'] for w in network_winners]):.1f}")
        print(f"  ROI moyen: {mean([w['max_roi'] for w in network_winners]):.1f}%")
        print(f"  Drawdown moyen: {mean([w['max_drawdown'] for w in network_winners]):.1f}%")
        print(f"  Temps moyen vers TP1: {mean([w['tp1_time'] for w in network_winners if w['tp1_time']]):.0f}min")

        # Type de pump dominant
        pump_types_dist = defaultdict(int)
        for w in network_winners:
            pump_types_dist[w['type_pump']] += 1
        best_pump = max(pump_types_dist.items(), key=lambda x: x[1]) if pump_types_dist else ('N/A', 0)
        print(f"  Type pump dominant: {best_pump[0]} ({best_pump[1]} occurrences)")

        # Seuils optimaux recommandés
        print(f"\nSEUILS OPTIMAUX RECOMMANDÉS:")
        liq_p25 = sorted([w['liquidity'] for w in network_winners])[len(network_winners)//4]
        vol_p25 = sorted([w['volume_24h'] for w in network_winners])[len(network_winners)//4]
        txns_p25 = sorted([w['total_txns'] for w in network_winners])[len(network_winners)//4]
        score_p25 = sorted([w['score'] for w in network_winners])[len(network_winners)//4]
        vel_p25 = sorted([w['velocite_pump'] for w in network_winners])[len(network_winners)//4]

        print(f"  Liquidity min (25th percentile): ${liq_p25:,.0f}")
        print(f"  Volume 24h min (25th percentile): ${vol_p25:,.0f}")
        print(f"  Txns min (25th percentile): {txns_p25:.0f}")
        print(f"  Score min (25th percentile): {score_p25:.0f}")
        print(f"  Vélocité min (25th percentile): {vel_p25:.0f}")
        print(f"  Type pump préféré: {best_pump[0]}")

    # ========== 9. PATTERN "QUASI-SYSTÉMATIQUE" ==========
    print("\n" + "=" * 120)
    print("SECTION 6: PATTERNS QUASI-SYSTÉMATIQUES (>70% WIN RATE)")
    print("=" * 120)

    print("\nRecherche de patterns avec win rate >70%...")

    high_wr_patterns = []

    # Test combinaisons multiples
    for network in by_network.keys():
        for score_min, score_max, score_label in score_ranges_combo:
            for pump_type in pump_types_combo:
                for vel_min, vel_max, vel_label in vel_ranges:
                    pattern_alerts = [a for a in winners_tp1 + losers
                                    if a['network'] == network
                                    and score_min <= a['score'] < score_max
                                    and a['type_pump'] == pump_type
                                    and vel_min <= a['velocite_pump'] < vel_max]

                    pattern_winners = [a for a in pattern_alerts if a['tp1_time'] is not None]

                    if len(pattern_alerts) >= 10:  # Minimum 10 pour être fiable
                        wr = (len(pattern_winners) / len(pattern_alerts) * 100)

                        if wr >= 70:
                            avg_roi = mean([w['max_roi'] for w in pattern_winners]) if pattern_winners else 0
                            avg_time = mean([w['tp1_time'] for w in pattern_winners if w['tp1_time']]) if pattern_winners else 0

                            high_wr_patterns.append({
                                'pattern': f"{network.upper()} | Score {score_label} | {pump_type} | Vel {vel_label}",
                                'total': len(pattern_alerts),
                                'winners': len(pattern_winners),
                                'win_rate': wr,
                                'avg_roi': avg_roi,
                                'avg_time': avg_time
                            })

    if high_wr_patterns:
        high_wr_patterns.sort(key=lambda x: x['win_rate'], reverse=True)

        print(f"\n{'Pattern':<80} {'Total':>8} {'Winners':>10} {'Win Rate':>12} {'Avg ROI':>12} {'Avg Time':>12}")
        print("-" * 120)

        for p in high_wr_patterns[:20]:
            print(f"{p['pattern']:<80} {p['total']:>8} {p['winners']:>10} {p['win_rate']:>11.1f}% {p['avg_roi']:>11.1f}% {p['avg_time']:>9.0f}min")
    else:
        print("\nAucun pattern avec >70% win rate trouvé (critère peut-être trop strict)")

    # ========== 10. RÉSUMÉ EXÉCUTIF & RECOMMANDATIONS ==========
    print("\n" + "=" * 120)
    print("SECTION 7: RÉSUMÉ EXÉCUTIF & PLAN D'ACTION")
    print("=" * 120)

    print("\n1. TIMING OPTIMAL:")
    fast_tp1_pct = len([w for w in winners_tp1 if w['tp1_time'] and w['tp1_time'] < 60]) / len(winners_tp1) * 100
    print(f"   - {fast_tp1_pct:.1f}% des TP1 atteints en <1h")
    print(f"   - Recommandation: Utiliser stop-loss temps (exit si pas TP1 en 2-3h)")

    print("\n2. DRAWDOWN:")
    safe_winners_pct = len([w for w in winners_tp1 if w['max_drawdown'] > -10]) / len(winners_tp1) * 100
    print(f"   - {safe_winners_pct:.1f}% des winners n'ont jamais fait >-10% drawdown")
    print(f"   - Recommandation: Stop-loss à -12% pour éviter faux signaux")

    print("\n3. MEILLEURE COMBINAISON:")
    if combos:
        best_combo = combos[0]
        print(f"   - {best_combo['label']}: {best_combo['win_rate']:.1f}% win rate")
        print(f"   - ROI moyen: {best_combo['avg_roi']:.1f}%")

    print("\n4. PATTERNS HAUTE CONFIANCE (>70% WR):")
    if high_wr_patterns:
        print(f"   - {len(high_wr_patterns)} patterns identifiés")
        print(f"   - Meilleur: {high_wr_patterns[0]['pattern']}")
        print(f"     Win rate: {high_wr_patterns[0]['win_rate']:.1f}% | ROI moyen: {high_wr_patterns[0]['avg_roi']:.1f}%")

    print("\n5. RÉSEAU LE PLUS PERFORMANT:")
    network_perfs = []
    for network, alerts in by_network.items():
        winners = [a for a in alerts if a['tp1_time'] is not None]
        if alerts:
            wr = len(winners) / len(alerts) * 100
            avg_roi = mean([w['max_roi'] for w in winners]) if winners else 0
            network_perfs.append((network, wr, avg_roi, len(alerts)))

    network_perfs.sort(key=lambda x: x[1], reverse=True)
    if network_perfs:
        best_net = network_perfs[0]
        print(f"   - {best_net[0].upper()}: {best_net[1]:.1f}% win rate | {best_net[2]:.1f}% ROI moyen | {best_net[3]} alertes")

    print("\n" + "=" * 120)
    print("ANALYSE TERMINÉE")
    print("=" * 120)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DB_PATH = sys.argv[1]

    ultimate_analysis()
