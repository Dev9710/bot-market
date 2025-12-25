#!/usr/bin/env python3
"""
ULTIMATE EXPERT ANALYZER - 40 ans d'expérience crypto traduit en code
Analyses multi-dimensionnelles pour maximiser le win rate sur tous les réseaux
"""
import sqlite3
import sys
from collections import defaultdict
from statistics import mean, median, stdev
from datetime import datetime

DB_PATH = "/data/alerts_history.db"

def expert_analysis():
    print("=" * 120)
    print("ULTIMATE EXPERT ANALYZER - ANALYSE EXHAUSTIVE PRO")
    print("=" * 120)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupération COMPLÈTE avec toutes les colonnes critiques
    cursor.execute("""
        SELECT
            a.id, a.network, a.token_name, a.token_address,
            a.score, a.base_score, a.momentum_bonus, a.confidence_score,
            a.entry_price, a.tp1_price, a.tp2_price, a.tp3_price, a.stop_loss_price,
            a.volume_24h, a.volume_6h, a.volume_1h,
            a.liquidity, a.buys_24h, a.sells_24h, a.buy_ratio, a.total_txns,
            a.age_hours, a.volume_acceleration_1h_vs_6h, a.volume_acceleration_6h_vs_24h,
            a.velocite_pump, a.type_pump, a.created_at,
            a.tp1_percent, a.tp2_percent, a.tp3_percent,
            COALESCE(MAX(pt.highest_price), a.entry_price) as highest_price,
            COALESCE(MIN(pt.lowest_price), a.entry_price) as lowest_price
        FROM alerts a
        LEFT JOIN price_tracking pt ON a.id = pt.alert_id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    """)

    alerts_raw = cursor.fetchall()
    print(f"\n[INIT] Chargement: {len(alerts_raw):,} alertes\n")

    # Organisation avancée
    alerts = []
    winners_tp1, winners_tp2, winners_tp3 = [], [], []
    losers = []
    by_network = defaultdict(list)
    by_token = defaultdict(list)
    by_hour = defaultdict(list)
    by_day = defaultdict(list)

    for raw in alerts_raw:
        if not raw[8] or not raw[9] or not raw[30]:  # Skip si données manquantes
            continue

        entry, tp1, tp2, tp3, sl = raw[8], raw[9], raw[10], raw[11], raw[12]
        highest, lowest = raw[30], raw[31]

        max_roi = ((highest / entry - 1) * 100) if entry else 0
        max_dd = ((lowest / entry - 1) * 100) if entry and lowest else 0

        tp1_hit = highest >= tp1 * 0.995
        tp2_hit = highest >= tp2 * 0.995 if tp2 else False
        tp3_hit = highest >= tp3 * 0.995 if tp3 else False
        sl_hit = lowest <= sl * 1.005 if sl else False

        # Ratios avancés
        vol_ratio_1h_24h = (raw[15] / raw[13]) if raw[13] and raw[13] > 0 else 0
        vol_ratio_6h_24h = (raw[14] / raw[13]) if raw[13] and raw[13] > 0 else 0
        liq_to_vol_ratio = (raw[16] / raw[13]) if raw[13] and raw[13] > 0 else 0
        txns_per_vol = (raw[20] / raw[13]) if raw[13] and raw[13] > 0 else 0

        # Timestamp analysis
        try:
            dt = datetime.fromisoformat(raw[26].replace('Z', '+00:00'))
            hour = dt.hour
            day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        except:
            hour = 0
            day_of_week = 0

        alert = {
            'id': raw[0], 'network': raw[1], 'token_name': raw[2], 'token_address': raw[3],
            'score': raw[4] or 0, 'base_score': raw[5] or 0, 'momentum_bonus': raw[6] or 0,
            'confidence_score': raw[7] or 0,
            'entry_price': entry, 'tp1_price': tp1, 'tp2_price': tp2 or 0, 'tp3_price': tp3 or 0,
            'stop_loss_price': sl or 0,
            'volume_24h': raw[13] or 0, 'volume_6h': raw[14] or 0, 'volume_1h': raw[15] or 0,
            'liquidity': raw[16] or 0, 'buys_24h': raw[17] or 0, 'sells_24h': raw[18] or 0,
            'buy_ratio': raw[19] or 0, 'total_txns': raw[20] or 0, 'age_hours': raw[21] or 0,
            'vol_accel_1h_6h': raw[22] or 0, 'vol_accel_6h_24h': raw[23] or 0,
            'velocite_pump': raw[24] or 0, 'type_pump': raw[25] or 'UNKNOWN',
            'created_at': raw[26], 'tp1_percent': raw[27] or 0, 'tp2_percent': raw[28] or 0,
            'tp3_percent': raw[29] or 0,
            'highest_price': highest, 'lowest_price': lowest,
            'max_roi': max_roi, 'max_dd': max_dd,
            'tp1_hit': tp1_hit, 'tp2_hit': tp2_hit, 'tp3_hit': tp3_hit, 'sl_hit': sl_hit,
            'vol_ratio_1h_24h': vol_ratio_1h_24h, 'vol_ratio_6h_24h': vol_ratio_6h_24h,
            'liq_to_vol_ratio': liq_to_vol_ratio, 'txns_per_vol': txns_per_vol,
            'hour': hour, 'day_of_week': day_of_week,
            'risk_reward': (max_roi / abs(max_dd)) if max_dd != 0 else 0,
        }

        alerts.append(alert)
        if tp1_hit: winners_tp1.append(alert)
        if tp2_hit: winners_tp2.append(alert)
        if tp3_hit: winners_tp3.append(alert)
        if not tp1_hit: losers.append(alert)

        by_network[raw[1]].append(alert)
        by_token[raw[3]].append(alert)
        by_hour[hour].append(alert)
        by_day[day_of_week].append(alert)

    total = len(alerts)
    print(f"Winners TP1: {len(winners_tp1)} ({len(winners_tp1)/total*100:.1f}%)")
    print(f"Winners TP2: {len(winners_tp2)} ({len(winners_tp2)/total*100:.1f}%)")
    print(f"Winners TP3: {len(winners_tp3)} ({len(winners_tp3)/total*100:.1f}%)")
    print(f"Losers: {len(losers)} ({len(losers)/total*100:.1f}%)")

    # ========== ANALYSE 1: TEMPORAL PATTERNS ==========
    print("\n" + "=" * 120)
    print("[1/15] ANALYSE TEMPORELLE - BEST TIME TO TRADE")
    print("=" * 120)

    print(f"\n{'Heure (UTC)':<15} {'Total':>10} {'TP1 Wins':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    for hour in sorted(by_hour.keys()):
        hour_alerts = by_hour[hour]
        hour_winners = [a for a in hour_alerts if a['tp1_hit']]
        wr = (len(hour_winners) / len(hour_alerts) * 100) if hour_alerts else 0
        avg_roi = mean([w['max_roi'] for w in hour_winners]) if hour_winners else 0

        if len(hour_alerts) >= 10:
            marker = "  <<<" if wr > 25 else ""
            print(f"{hour:02d}:00{'':<10} {len(hour_alerts):>10} {len(hour_winners):>10} {wr:>11.1f}% {avg_roi:>11.1f}%{marker}")

    print(f"\n{'Jour Semaine':<15} {'Total':>10} {'TP1 Wins':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    for day_idx in range(7):
        day_alerts = by_day[day_idx]
        day_winners = [a for a in day_alerts if a['tp1_hit']]
        wr = (len(day_winners) / len(day_alerts) * 100) if day_alerts else 0
        avg_roi = mean([w['max_roi'] for w in day_winners]) if day_winners else 0

        if len(day_alerts) >= 10:
            marker = "  <<<" if wr > 22 else ""
            print(f"{days[day_idx]:<15} {len(day_alerts):>10} {len(day_winners):>10} {wr:>11.1f}% {avg_roi:>11.1f}%{marker}")

    # ========== ANALYSE 2: LIQUIDITY SWEET SPOT ==========
    print("\n" + "=" * 120)
    print("[2/15] LIQUIDITY SWEET SPOT - ZONE OPTIMALE PAR RÉSEAU")
    print("=" * 120)

    liq_ranges = [
        (0, 50000), (50000, 100000), (100000, 200000), (200000, 500000),
        (500000, 1000000), (1000000, 5000000), (5000000, 999999999)
    ]

    for network in sorted(by_network.keys()):
        network_alerts = by_network[network]
        if len(network_alerts) < 20:
            continue

        print(f"\n{network.upper()}:")
        print(f"{'Liquidity Range':<25} {'Total':>10} {'TP1 Wins':>10} {'Win Rate':>12} {'Avg ROI':>12}")
        print("-" * 120)

        for min_liq, max_liq in liq_ranges:
            liq_alerts = [a for a in network_alerts if min_liq <= a['liquidity'] < max_liq]
            liq_winners = [a for a in liq_alerts if a['tp1_hit']]

            if len(liq_alerts) >= 5:
                wr = (len(liq_winners) / len(liq_alerts) * 100)
                avg_roi = mean([w['max_roi'] for w in liq_winners]) if liq_winners else 0

                liq_label = f"${min_liq//1000}K-${max_liq//1000}K" if max_liq < 999999999 else f">${min_liq//1000}K"
                marker = "  <<<< SWEET SPOT" if wr > 30 else ""
                print(f"{liq_label:<25} {len(liq_alerts):>10} {len(liq_winners):>10} {wr:>11.1f}% {avg_roi:>11.1f}%{marker}")

    # ========== ANALYSE 3: VOLUME VELOCITY CORRELATION ==========
    print("\n" + "=" * 120)
    print("[3/15] VOLUME VELOCITY - ACCÉLÉRATION CRITIQUE")
    print("=" * 120)

    print(f"\n{'Vol 1h/24h Ratio':<20} {'Total':>10} {'TP1 Wins':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    vol_ratio_ranges = [
        (0, 0.01, "0-1%"), (0.01, 0.05, "1-5%"), (0.05, 0.1, "5-10%"),
        (0.1, 0.2, "10-20%"), (0.2, 0.5, "20-50%"), (0.5, 1.0, "50-100%"), (1.0, 999, ">100%")
    ]

    for min_r, max_r, label in vol_ratio_ranges:
        ratio_alerts = [a for a in alerts if min_r <= a['vol_ratio_1h_24h'] < max_r]
        ratio_winners = [a for a in ratio_alerts if a['tp1_hit']]

        if len(ratio_alerts) >= 10:
            wr = (len(ratio_winners) / len(ratio_alerts) * 100)
            avg_roi = mean([w['max_roi'] for w in ratio_winners]) if ratio_winners else 0
            marker = "  <<<< MOMENTUM!" if wr > 25 else ""
            print(f"{label:<20} {len(ratio_alerts):>10} {len(ratio_winners):>10} {wr:>11.1f}% {avg_roi:>11.1f}%{marker}")

    # ========== ANALYSE 4: AGE SWEET SPOT DÉTAILLÉ ==========
    print("\n" + "=" * 120)
    print("[4/15] AGE ANALYSIS - CYCLE DE VIE DU TOKEN")
    print("=" * 120)

    age_ranges = [
        (0, 0.5, "<30min"), (0.5, 1, "30min-1h"), (1, 3, "1-3h"), (3, 6, "3-6h"),
        (6, 12, "6-12h"), (12, 24, "12-24h"), (24, 48, "1-2d"),
        (48, 72, "2-3d"), (72, 168, "3-7d"), (168, 999999, ">7d")
    ]

    print(f"\n{'Age Range':<15} {'Total':>10} {'TP1 Wins':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    for min_age, max_age, label in age_ranges:
        age_alerts = [a for a in alerts if min_age <= a['age_hours'] < max_age]
        age_winners = [a for a in age_alerts if a['tp1_hit']]

        if len(age_alerts) >= 10:
            wr = (len(age_winners) / len(age_alerts) * 100)
            avg_roi = mean([w['max_roi'] for w in age_winners]) if age_winners else 0
            marker = "  <<<< PRIME TIME" if wr > 25 else ""
            print(f"{label:<15} {len(age_alerts):>10} {len(age_winners):>10} {wr:>11.1f}% {avg_roi:>11.1f}%{marker}")

    # ========== ANALYSE 5: RISK/REWARD RATIO ==========
    print("\n" + "=" * 120)
    print("[5/15] RISK/REWARD ANALYSIS - MEILLEUR R:R")
    print("=" * 120)

    rr_ranges = [(0, 0.5), (0.5, 1), (1, 2), (2, 5), (5, 10), (10, 999999)]

    print(f"\n{'Risk:Reward':<15} {'Total':>10} {'TP1 Wins':>10} {'Win Rate':>12} {'Avg ROI':>12}")
    print("-" * 120)

    for min_rr, max_rr in rr_ranges:
        rr_alerts = [a for a in winners_tp1 if min_rr <= abs(a['risk_reward']) < max_rr]
        avg_roi = mean([w['max_roi'] for w in rr_alerts]) if rr_alerts else 0

        if len(rr_alerts) >= 5:
            rr_label = f"{min_rr:.1f}-{max_rr:.1f}" if max_rr < 999999 else f">{min_rr:.0f}"
            print(f"{rr_label:<15} {len(rr_alerts):>10} {len(rr_alerts):>10} {'100.0':>11}% {avg_roi:>11.1f}%")

    # ========== ANALYSE 6: CORRELATION MATRIX ==========
    print("\n" + "=" * 120)
    print("[6/15] CORRELATION WINNERS vs LOSERS - FACTEURS DÉTERMINANTS")
    print("=" * 120)

    metrics = [
        ('Score', 'score'), ('Momentum Bonus', 'momentum_bonus'),
        ('Liquidity', 'liquidity'), ('Volume 24h', 'volume_24h'),
        ('Volume 1h', 'volume_1h'), ('Vol Ratio 1h/24h', 'vol_ratio_1h_24h'),
        ('Total Txns', 'total_txns'), ('Txns/Vol', 'txns_per_vol'),
        ('Age (hours)', 'age_hours'), ('Vélocité', 'velocite_pump'),
        ('Liq/Vol Ratio', 'liq_to_vol_ratio'),
    ]

    print(f"\n{'Métrique':<25} {'Win Avg':>15} {'Los Avg':>15} {'Diff %':>12} {'Impact':>10}")
    print("-" * 120)

    for label, key in metrics:
        w_vals = [w[key] for w in winners_tp1 if w[key] is not None and w[key] != 0]
        l_vals = [l[key] for l in losers if l[key] is not None and l[key] != 0]

        if w_vals and l_vals:
            w_avg = mean(w_vals)
            l_avg = mean(l_vals)
            diff = ((w_avg - l_avg) / l_avg * 100) if l_avg != 0 else 0

            if abs(diff) > 100:
                impact = "CRITICAL"
            elif abs(diff) > 50:
                impact = "HIGH"
            elif abs(diff) > 20:
                impact = "MEDIUM"
            else:
                impact = "LOW"

            print(f"{label:<25} {w_avg:>15,.2f} {l_avg:>15,.2f} {diff:>11.1f}% {impact:>10}")

    # ========== ANALYSE 7: SCORE BREAKDOWN ==========
    print("\n" + "=" * 120)
    print("[7/15] SCORE DECOMPOSITION - BASE vs MOMENTUM vs CONFIDENCE")
    print("=" * 120)

    print(f"\n{'Component':<20} {'Win Avg':>12} {'Los Avg':>12} {'Correlation':>15}")
    print("-" * 120)

    components = [
        ('Base Score', 'base_score'),
        ('Momentum Bonus', 'momentum_bonus'),
        ('Confidence', 'confidence_score'),
        ('SCORE TOTAL', 'score'),
    ]

    for label, key in components:
        w_avg = mean([w[key] for w in winners_tp1 if w[key]])
        l_avg = mean([l[key] for l in losers if l[key]])
        correlation = "POSITIVE" if w_avg > l_avg else "NEGATIVE"

        print(f"{label:<20} {w_avg:>12.1f} {l_avg:>12.1f} {correlation:>15}")

    # ========== ANALYSE 8: COMBO 3D (Score + Type + Vélocité) ==========
    print("\n" + "=" * 120)
    print("[8/15] COMBOS 3D - Score + Type Pump + Vélocité")
    print("=" * 120)

    score_ranges = [(50, 70), (70, 80), (80, 90), (90, 101)]
    pump_types = ['RAPIDE', 'TRES_RAPIDE', 'PARABOLIQUE']
    vel_ranges = [(0, 5), (5, 20), (20, 50), (50, 999999)]

    best_combos = []

    for score_min, score_max in score_ranges:
        for pump_type in pump_types:
            for vel_min, vel_max in vel_ranges:
                combo_alerts = [a for a in alerts
                              if score_min <= a['score'] < score_max
                              and a['type_pump'] == pump_type
                              and vel_min <= a['velocite_pump'] < vel_max]
                combo_winners = [a for a in combo_alerts if a['tp1_hit']]

                if len(combo_alerts) >= 5:
                    wr = (len(combo_winners) / len(combo_alerts) * 100)
                    avg_roi = mean([w['max_roi'] for w in combo_winners]) if combo_winners else 0

                    if wr > 35:  # Seulement les bons
                        vel_label = f"Vel {vel_min}-{vel_max}" if vel_max < 999999 else f"Vel >{vel_min}"
                        best_combos.append({
                            'combo': f"Score {score_min}-{score_max} + {pump_type} + {vel_label}",
                            'total': len(combo_alerts),
                            'winners': len(combo_winners),
                            'wr': wr,
                            'roi': avg_roi
                        })

    best_combos.sort(key=lambda x: x['wr'], reverse=True)

    print(f"\n{'Combo 3D':<70} {'Total':>10} {'Wins':>10} {'WR':>10} {'ROI':>10}")
    print("-" * 120)

    for combo in best_combos[:15]:
        print(f"{combo['combo']:<70} {combo['total']:>10} {combo['winners']:>10} {combo['wr']:>9.1f}% {combo['roi']:>9.1f}%")

    # ========== ANALYSE 9: FAILUREPATTERNS ==========
    print("\n" + "=" * 120)
    print("[9/15] FAILURE PATTERNS - POURQUOI ÇA ÉCHOUE")
    print("=" * 120)

    # Losers qui ont atteint SL
    sl_losers = [l for l in losers if l['sl_hit']]
    print(f"\nLosers ayant touché SL: {len(sl_losers)} ({len(sl_losers)/len(losers)*100:.1f}%)")

    # Analyse des losers par drawdown severity
    severe_dd_losers = [l for l in losers if l['max_dd'] < -20]
    mild_dd_losers = [l for l in losers if -20 <= l['max_dd'] < -10]

    print(f"Losers avec DD > -20%: {len(severe_dd_losers)} ({len(severe_dd_losers)/len(losers)*100:.1f}%)")
    print(f"Losers avec DD -10% à -20%: {len(mild_dd_losers)} ({len(mild_dd_losers)/len(losers)*100:.1f}%)")

    # Caractéristiques communes des losers
    print(f"\nCaractéristiques MOYENNES des LOSERS:")
    print(f"  Score: {mean([l['score'] for l in losers]):.1f}")
    print(f"  Vélocité: {mean([l['velocite_pump'] for l in losers]):.1f}")
    print(f"  Liquidity: ${mean([l['liquidity'] for l in losers]):,.0f}")
    print(f"  Age: {mean([l['age_hours'] for l in losers]):.1f}h")
    print(f"  Max DD: {mean([l['max_dd'] for l in losers]):.1f}%")

    # Type pump des losers
    loser_pumps = defaultdict(int)
    for l in losers:
        loser_pumps[l['type_pump']] += 1

    print(f"\nDistribution Type Pump (Losers):")
    for pump_type, count in sorted(loser_pumps.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pump_type}: {count} ({count/len(losers)*100:.1f}%)")

    # ========== ANALYSE 10: OUTLIERS - MEGA GAINS ==========
    print("\n" + "=" * 120)
    print("[10/15] OUTLIERS ANALYSIS - MEGA GAINS PATTERNS")
    print("=" * 120)

    mega_winners = sorted([w for w in winners_tp1 if w['max_roi'] > 100], key=lambda x: x['max_roi'], reverse=True)

    print(f"\nWinners avec ROI >100%: {len(mega_winners)}")
    print(f"\n{'Token':<40} {'Network':<10} {'ROI':>10} {'Score':>8} {'Type':>15} {'Vel':>8}")
    print("-" * 120)

    for w in mega_winners[:20]:
        print(f"{w['token_name'][:39]:<40} {w['network'][:9]:<10} {w['max_roi']:>9.1f}% {w['score']:>8} {w['type_pump']:>15} {w['velocite_pump']:>8.1f}")

    # Caractéristiques communes mega gains
    if mega_winners:
        print(f"\nCaractéristiques MEGA GAINS (ROI >100%):")
        print(f"  Score moyen: {mean([w['score'] for w in mega_winners]):.1f}")
        print(f"  Vélocité moyenne: {mean([w['velocite_pump'] for w in mega_winners]):.1f}")
        print(f"  Age moyen: {mean([w['age_hours'] for w in mega_winners]):.1f}h")

        mega_pumps = defaultdict(int)
        for w in mega_winners:
            mega_pumps[w['type_pump']] += 1
        best_mega_pump = max(mega_pumps.items(), key=lambda x: x[1])
        print(f"  Type pump dominant: {best_mega_pump[0]} ({best_mega_pump[1]}/{len(mega_winners)})")

    # ========== ANALYSE 11: NETWORK-SPECIFIC THRESHOLDS ==========
    print("\n" + "=" * 120)
    print("[11/15] SEUILS OPTIMAUX DYNAMIQUES PAR RÉSEAU")
    print("=" * 120)

    for network in sorted(by_network.keys()):
        network_alerts = by_network[network]
        network_winners = [a for a in network_alerts if a['tp1_hit']]

        if len(network_winners) < 10:
            continue

        print(f"\n{network.upper()} - Seuils Recommandés:")
        print("-" * 120)

        # Percentiles multiples
        percentiles = [10, 25, 50, 75, 90]
        metrics_to_analyze = ['liquidity', 'volume_24h', 'total_txns', 'score', 'velocite_pump']

        for metric in metrics_to_analyze:
            values = sorted([w[metric] for w in network_winners if w[metric]])
            if not values:
                continue

            print(f"\n  {metric.upper()}:")
            for p in percentiles:
                idx = int(len(values) * p / 100)
                val = values[min(idx, len(values)-1)]
                label = "CONSERVATEUR" if p == 10 else "ÉQUILIBRÉ" if p == 25 else "AGRESSIF" if p >= 75 else "STANDARD"
                print(f"    P{p} ({label:12}): {val:>15,.2f}")

    # ========== ANALYSE 12: WIN STREAKS & PATTERNS ==========
    print("\n" + "=" * 120)
    print("[12/15] WIN STREAKS - SÉRIES GAGNANTES")
    print("=" * 120)

    # Tokens avec plusieurs wins consécutifs
    token_sequences = {}
    for addr, token_alerts in by_token.items():
        if len(token_alerts) < 3:
            continue

        sorted_alerts = sorted(token_alerts, key=lambda x: x['created_at'])
        streak = 0
        max_streak = 0

        for alert in sorted_alerts:
            if alert['tp1_hit']:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0

        if max_streak >= 3:
            wins = len([a for a in token_alerts if a['tp1_hit']])
            token_sequences[addr] = {
                'name': token_alerts[0]['token_name'],
                'max_streak': max_streak,
                'total_wins': wins,
                'total_alerts': len(token_alerts)
            }

    if token_sequences:
        print(f"\nTokens avec win streak >= 3:")
        print(f"{'Token':<40} {'Max Streak':>12} {'Total Wins':>12} {'Total Alerts':>15}")
        print("-" * 120)

        for addr, data in sorted(token_sequences.items(), key=lambda x: x[1]['max_streak'], reverse=True)[:15]:
            print(f"{data['name'][:39]:<40} {data['max_streak']:>12} {data['total_wins']:>12} {data['total_alerts']:>15}")

    # ========== ANALYSE 13: RÉSUMÉ EXÉCUTIF ==========
    print("\n" + "=" * 120)
    print("[13/15] RÉSUMÉ EXÉCUTIF - TOP INSIGHTS")
    print("=" * 120)

    print(f"\n1. WIN RATE GLOBAL: {len(winners_tp1)/len(alerts)*100:.1f}%")

    # Meilleur réseau
    network_stats = []
    for net, alerts_net in by_network.items():
        winners_net = [a for a in alerts_net if a['tp1_hit']]
        if len(alerts_net) >= 20:
            wr = len(winners_net) / len(alerts_net) * 100
            roi = mean([w['max_roi'] for w in winners_net]) if winners_net else 0
            network_stats.append((net, wr, roi))

    network_stats.sort(key=lambda x: x[1], reverse=True)
    if network_stats:
        print(f"\n2. MEILLEUR RÉSEAU: {network_stats[0][0].upper()}")
        print(f"   Win Rate: {network_stats[0][1]:.1f}% | ROI Moyen: {network_stats[0][2]:.1f}%")

    # Meilleure heure
    hour_stats = []
    for hour, hour_alerts in by_hour.items():
        hour_winners = [a for a in hour_alerts if a['tp1_hit']]
        if len(hour_alerts) >= 20:
            wr = len(hour_winners) / len(hour_alerts) * 100
            hour_stats.append((hour, wr))

    hour_stats.sort(key=lambda x: x[1], reverse=True)
    if hour_stats:
        print(f"\n3. MEILLEURE HEURE: {hour_stats[0][0]:02d}:00 UTC")
        print(f"   Win Rate: {hour_stats[0][1]:.1f}%")

    # Mega gains count
    print(f"\n4. MEGA GAINS (>100% ROI): {len(mega_winners)} alertes")
    if mega_winners:
        print(f"   ROI Maximum: {max([w['max_roi'] for w in mega_winners]):.1f}%")

    # Best combo
    if best_combos:
        print(f"\n5. MEILLEUR COMBO 3D:")
        print(f"   {best_combos[0]['combo']}")
        print(f"   Win Rate: {best_combos[0]['wr']:.1f}% | ROI: {best_combos[0]['roi']:.1f}%")

    print("\n" + "=" * 120)
    print("[14/15] PLAN D'ACTION RECOMMANDÉ")
    print("=" * 120)

    print("\n**MODIFICATIONS IMMÉDIATES:**")

    # Réseaux à ajuster
    print("\n1. AJUSTER SEUILS:")
    for net, wr, roi in network_stats:
        if wr < 15:
            print(f"   - {net.upper()}: Win Rate {wr:.1f}% TROP BAS → Augmenter seuils drastiquement")

    # Filtres à ajouter
    print("\n2. AJOUTER FILTRES:")
    if hour_stats:
        best_hours = [h for h, wr in hour_stats if wr > 25]
        if best_hours:
            print(f"   - Privilégier heures: {', '.join([f'{h:02d}:00' for h in best_hours[:5]])}")

    print("\n3. PATTERNS HAUTE CONFIANCE:")
    if best_combos:
        for combo in best_combos[:3]:
            if combo['wr'] > 50:
                print(f"   - {combo['combo']}: {combo['wr']:.1f}% WR")

    print("\n4. TOKENS WATCHLIST:")
    watchlist_tokens = [data['name'] for addr, data in sorted(token_sequences.items(), key=lambda x: x[1]['max_streak'], reverse=True)[:5]]
    if watchlist_tokens:
        print(f"   - Suivre: {', '.join(watchlist_tokens)}")

    print("\n" + "=" * 120)
    print("[15/15] ANALYSE TERMINÉE")
    print("=" * 120)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DB_PATH = sys.argv[1]

    expert_analysis()
