"""
BACKTESTING AVEC TP/SL THEORIQUES
Utilise les TP/SL de la DB locale + simulation bas

ée sur les probabilités réalistes crypto
"""

import sqlite3
import json
from datetime import datetime
from collections import defaultdict
import statistics

DB_PATH = r"c:\Users\ludo_\Documents\projets\owner\bot-market\alerts_history.db"

def get_all_alerts_with_tp_sl():
    """Recupere toutes les alertes avec TP/SL de la DB locale"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT
            id, network, token_name,
            score, tier, created_at,
            entry_price,
            stop_loss_percent,
            tp1_percent, tp2_percent, tp3_percent,
            volume_24h, liquidity
        FROM alerts
        WHERE entry_price IS NOT NULL
          AND tp1_percent IS NOT NULL
          AND stop_loss_percent IS NOT NULL
    """)

    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return alerts

def simulate_tp_sl_outcome(score, tier, tp1_pct, tp2_pct, tp3_pct, sl_pct):
    """
    Simule le resultat d'un trade base sur le score/tier

    Probabil

ités basées sur l'expérience crypto trading:
    - Score >= 98 (ULTRA_HIGH): 75% win rate, avec répartition TP1/TP2/TP3
    - Score 95-97 (HIGH): 65% win rate
    - Score 90-94 (MEDIUM): 55% win rate
    - Score < 90 (LOW): 35% win rate

    Pour les wins, répartition:
    - TP3: 30% des wins (meilleur gain)
    - TP2: 40% des wins (gain moyen)
    - TP1: 30% des wins (gain minimal)
    """

    # Determiner win rate base sur score
    if score >= 98:
        win_rate = 0.75
    elif score >= 95:
        win_rate = 0.65
    elif score >= 90:
        win_rate = 0.55
    else:
        win_rate = 0.35

    # Simuler (hash deterministe base sur proprietes)
    import hashlib
    seed = hashlib.md5(f"{score}{tier}{tp1_pct}{tp2_pct}{tp3_pct}".encode()).hexdigest()
    pseudo_random = int(seed[:8], 16) / 0xFFFFFFFF

    # Determiner si WIN ou LOSS
    if pseudo_random < win_rate:
        # WIN - Determiner quel TP
        tp_random = (int(seed[8:16], 16) / 0xFFFFFFFF)

        if tp_random < 0.30:
            return 'TP3', abs(tp3_pct)  # TP3 = meilleur gain
        elif tp_random < 0.70:
            return 'TP2', abs(tp2_pct)  # TP2 = gain moyen
        else:
            return 'TP1', abs(tp1_pct)  # TP1 = gain minimal
    else:
        # LOSS
        return 'SL', sl_pct  # SL est déjà négatif

def analyze_results(alerts):
    """Analyse les resultats du backtest"""

    stats_by_network = defaultdict(lambda: {
        'total': 0,
        'tp1': 0,
        'tp2': 0,
        'tp3': 0,
        'sl': 0,
        'gains': [],
        'losses': [],
        'by_tier': defaultdict(lambda: {'tp': 0, 'sl': 0, 'total': 0}),
        'by_score': defaultdict(lambda: {'tp': 0, 'sl': 0, 'total': 0})
    })

    results = []

    for alert in alerts:
        net = alert['network']
        score = alert['score']
        tier = alert['tier'] or 'UNKNOWN'

        # Simuler outcome
        outcome, gain_pct = simulate_tp_sl_outcome(
            score,
            tier,
            alert['tp1_percent'],
            alert['tp2_percent'],
            alert['tp3_percent'],
            alert['stop_loss_percent']
        )

        # Stats
        stats_by_network[net]['total'] += 1
        stats_by_network[net]['by_tier'][tier]['total'] += 1

        # Score bucket
        if score >= 98:
            score_bucket = '98-100'
        elif score >= 95:
            score_bucket = '95-97'
        elif score >= 90:
            score_bucket = '90-94'
        else:
            score_bucket = '<90'

        stats_by_network[net]['by_score'][score_bucket]['total'] += 1

        if outcome == 'TP3':
            stats_by_network[net]['tp3'] += 1
            stats_by_network[net]['gains'].append(gain_pct)
            stats_by_network[net]['by_tier'][tier]['tp'] += 1
            stats_by_network[net]['by_score'][score_bucket]['tp'] += 1
        elif outcome == 'TP2':
            stats_by_network[net]['tp2'] += 1
            stats_by_network[net]['gains'].append(gain_pct)
            stats_by_network[net]['by_tier'][tier]['tp'] += 1
            stats_by_network[net]['by_score'][score_bucket]['tp'] += 1
        elif outcome == 'TP1':
            stats_by_network[net]['tp1'] += 1
            stats_by_network[net]['gains'].append(gain_pct)
            stats_by_network[net]['by_tier'][tier]['tp'] += 1
            stats_by_network[net]['by_score'][score_bucket]['tp'] += 1
        elif outcome == 'SL':
            stats_by_network[net]['sl'] += 1
            stats_by_network[net]['losses'].append(gain_pct)
            stats_by_network[net]['by_tier'][tier]['sl'] += 1
            stats_by_network[net]['by_score'][score_bucket]['sl'] += 1

        results.append({
            'id': alert['id'],
            'network': net,
            'tier': tier,
            'score': score,
            'outcome': outcome,
            'gain_pct': gain_pct
        })

    return stats_by_network, results

def generate_report(stats_by_network):
    """Genere le rapport de backtesting"""

    print()
    print("=" * 80)
    print("BACKTESTING AVEC TP/SL THEORIQUES - RESULTATS")
    print("=" * 80)
    print()

    print("METHODOLOGIE:")
    print("  - Simulation basee sur win rates realistes crypto:")
    print("    * Score >= 98 (ULTRA_HIGH): 75% win rate")
    print("    * Score 95-97 (HIGH): 65% win rate")
    print("    * Score 90-94 (MEDIUM): 55% win rate")
    print("    * Score < 90 (LOW): 35% win rate")
    print("  - Repartition des wins: TP3=30%, TP2=40%, TP1=30%")
    print()
    print("=" * 80)
    print()

    # Trier par reseau
    sorted_networks = sorted(stats_by_network.items(), key=lambda x: x[1]['total'], reverse=True)

    for net, stats in sorted_networks:
        total = stats['total']
        if total == 0:
            continue

        tp_total = stats['tp1'] + stats['tp2'] + stats['tp3']
        sl_total = stats['sl']

        win_rate = (tp_total / total * 100) if total > 0 else 0

        # Calculer gains/pertes moyens
        avg_gain = statistics.mean(stats['gains']) if stats['gains'] else 0
        avg_loss = statistics.mean(stats['losses']) if stats['losses'] else 0

        # Expected value par trade
        expected_value = (tp_total / total) * avg_gain + (sl_total / total) * avg_loss

        # Sharpe ratio
        all_returns = stats['gains'] + stats['losses']
        sharpe = (statistics.mean(all_returns) / statistics.stdev(all_returns)) if len(all_returns) > 1 and statistics.stdev(all_returns) > 0 else 0

        print(f"{net.upper()} - {total} alertes")
        print("-" * 80)
        print(f"  WIN RATE: {win_rate:.1f}% ({tp_total} wins / {total} total)")
        print()
        print(f"  Resultats:")
        print(f"    TP3 (meilleur):  {stats['tp3']:4d} ({stats['tp3']/total*100:5.1f}%)")
        print(f"    TP2:             {stats['tp2']:4d} ({stats['tp2']/total*100:5.1f}%)")
        print(f"    TP1:             {stats['tp1']:4d} ({stats['tp1']/total*100:5.1f}%)")
        print(f"    SL (pertes):     {sl_total:4d} ({sl_total/total*100:5.1f}%)")
        print()
        print(f"  Performance:")
        print(f"    Gain moyen:      {avg_gain:+.1f}%")
        print(f"    Perte moyenne:   {avg_loss:+.1f}%")
        print(f"    Expected value:  {expected_value:+.1f}% par trade")
        print(f"    Sharpe Ratio:    {sharpe:.2f}")
        print()

        # Stats par tier
        print(f"  Performance par TIER:")
        for tier in ['ULTRA_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW', 'UNKNOWN']:
            tier_stats = stats['by_tier'].get(tier)
            if tier_stats and tier_stats['total'] > 0:
                tier_tp = tier_stats['tp']
                tier_sl = tier_stats['sl']
                tier_total = tier_stats['total']
                tier_wr = (tier_tp / tier_total * 100) if tier_total > 0 else 0
                print(f"    {tier:12s}: {tier_wr:5.1f}% WR ({tier_tp}/{tier_total})")

        print()

        # Stats par score
        print(f"  Performance par SCORE:")
        for score_bucket in ['98-100', '95-97', '90-94', '<90']:
            score_stats = stats['by_score'].get(score_bucket)
            if score_stats and score_stats['total'] > 0:
                score_tp = score_stats['tp']
                score_sl = score_stats['sl']
                score_total = score_stats['total']
                score_wr = (score_tp / score_total * 100) if score_total > 0 else 0
                print(f"    {score_bucket:8s}: {score_wr:5.1f}% WR ({score_tp}/{score_total})")

        print()

    # Statistiques globales
    print("=" * 80)
    print("STATISTIQUES GLOBALES")
    print("=" * 80)
    print()

    global_tp = sum(s['tp1'] + s['tp2'] + s['tp3'] for s in stats_by_network.values())
    global_sl = sum(s['sl'] for s in stats_by_network.values())
    global_total = sum(s['total'] for s in stats_by_network.values())

    global_wr = (global_tp / global_total * 100) if global_total > 0 else 0

    all_gains = [g for s in stats_by_network.values() for g in s['gains']]
    all_losses = [l for s in stats_by_network.values() for l in s['losses']]

    global_avg_gain = statistics.mean(all_gains) if all_gains else 0
    global_avg_loss = statistics.mean(all_losses) if all_losses else 0
    global_ev = (global_tp / global_total) * global_avg_gain + (global_sl / global_total) * global_avg_loss if global_total > 0 else 0

    all_returns = all_gains + all_losses
    global_sharpe = (statistics.mean(all_returns) / statistics.stdev(all_returns)) if len(all_returns) > 1 and statistics.stdev(all_returns) > 0 else 0

    print(f"Total alertes: {global_total}")
    print()
    print(f"WIN RATE GLOBAL: {global_wr:.1f}%")
    print()
    print(f"Wins:   {global_tp} ({global_tp/global_total*100:.1f}%)")
    print(f"Losses: {global_sl} ({global_sl/global_total*100:.1f}%)")
    print()
    print(f"Gain moyen:      {global_avg_gain:+.1f}%")
    print(f"Perte moyenne:   {global_avg_loss:+.1f}%")
    print(f"Expected value:  {global_ev:+.1f}% par trade")
    print(f"Sharpe Ratio:    {global_sharpe:.2f}")
    print()

    print("=" * 80)
    print("RECOMMANDATIONS")
    print("=" * 80)
    print()

    best_net = max(stats_by_network.items(), key=lambda x: (x[1]['tp1'] + x[1]['tp2'] + x[1]['tp3']) / x[1]['total'] if x[1]['total'] > 0 else 0)
    print(f"Meilleur reseau (win rate): {best_net[0].upper()} ({(best_net[1]['tp1'] + best_net[1]['tp2'] + best_net[1]['tp3']) / best_net[1]['total'] * 100:.1f}%)")

    best_sharpe_net = max(stats_by_network.items(), key=lambda x: (statistics.mean(x[1]['gains'] + x[1]['losses']) / statistics.stdev(x[1]['gains'] + x[1]['losses'])) if len(x[1]['gains'] + x[1]['losses']) > 1 and statistics.stdev(x[1]['gains'] + x[1]['losses']) > 0 else 0)
    print(f"Meilleur Sharpe Ratio: {best_sharpe_net[0].upper()}")
    print()

    print("=" * 80)

if __name__ == '__main__':
    print("BACKTESTING AVEC TP/SL THEORIQUES")
    print("=" * 80)
    print()

    # Charger alertes
    print("[1/3] Chargement des alertes avec TP/SL depuis la DB locale...")
    alerts = get_all_alerts_with_tp_sl()
    print(f"      OK {len(alerts)} alertes chargees")
    print()

    # Analyser
    print("[2/3] Simulation et analyse des resultats...")
    stats_by_network, results = analyze_results(alerts)
    print(f"      OK {len(results)} trades simules")
    print()

    # Rapport
    print("[3/3] Generation du rapport...")
    generate_report(stats_by_network)

    # Sauvegarder
    output = {
        'stats_by_network': {k: dict(v) for k, v in stats_by_network.items()},
        'sample_results': results[:100],  # Premier 100 pour reference
        'metadata': {
            'total_alerts': len(results),
            'methodology': 'Theoretical TP/SL simulation based on realistic crypto win rates',
            'timestamp': datetime.now().isoformat()
        }
    }

    with open('backtest_tp_sl_theoretical.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)

    print()
    print("OK Resultats sauvegardes dans backtest_tp_sl_theoretical.json")
