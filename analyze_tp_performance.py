#!/usr/bin/env python3
"""
Analyse de performance par blockchain basee sur les TP atteints.
Determine quelle blockchain est la plus rentable.

Usage:
    python analyze_tp_performance.py alerts_railway_export_utf8.json
"""

import sys
import json
from pathlib import Path
from collections import defaultdict
import statistics

def analyze_tp_performance(json_file: str):
    """Analyse des TP atteints par blockchain."""

    print(f"\n{'='*100}")
    print(f"   ANALYSE PERFORMANCE PAR BLOCKCHAIN - TP ATTEINTS")
    print(f"{'='*100}\n")

    # Charger données
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    alerts = data.get('alerts', [])
    total = len(alerts)

    print(f"Total alertes analysees: {total}\n")

    # ========================================================================
    # SECTION 1: ANALYSE GLOBALE DES TP
    # ========================================================================
    print(f"{'='*100}")
    print("SECTION 1: ANALYSE GLOBALE DES TP ATTEINTS")
    print("-" * 100)

    # Vérifier si nous avons des données de tracking
    has_tracking_data = False
    sample_alert = alerts[0] if alerts else {}

    # Chercher les clés de tracking possibles
    tracking_keys = ['tp1_was_hit', 'tp2_was_hit', 'tp3_was_hit', 'sl_was_hit',
                     'max_roi_percent', 'roi_at_24h', 'was_coherent']

    for key in tracking_keys:
        if key in sample_alert:
            has_tracking_data = True
            break

    if not has_tracking_data:
        print("\nATTENTION: Pas de donnees de tracking trouvees dans l'export.")
        print("Les alertes semblent ne pas avoir ete trackees apres emission.")
        print("\nAnalyse basee sur les metriques disponibles au moment de l'alerte:")
        print("- Prix d'entree vs TP cibles")
        print("- Ratios risque/recompense")
        print("- Metriques de qualite (score, velocite, etc.)\n")

    # Collecter stats par réseau
    network_stats = defaultdict(lambda: {
        'total_alerts': 0,
        'entry_prices': [],
        'tp1_targets': [],
        'tp2_targets': [],
        'tp3_targets': [],
        'sl_targets': [],
        'tp1_percents': [],
        'tp2_percents': [],
        'tp3_percents': [],
        'sl_percents': [],
        'scores': [],
        'velocites': [],
        'liquidites': [],
        'ages': [],
        'type_pumps': defaultdict(int),
        # Si données de tracking disponibles
        'tp1_hit': 0,
        'tp2_hit': 0,
        'tp3_hit': 0,
        'sl_hit': 0,
        'no_tp_hit': 0,
        'max_rois': [],
    })

    for alert in alerts:
        network = alert.get('network', 'unknown')
        network_stats[network]['total_alerts'] += 1

        # Prix et targets
        if alert.get('entry_price'):
            network_stats[network]['entry_prices'].append(alert['entry_price'])
        if alert.get('tp1_price'):
            network_stats[network]['tp1_targets'].append(alert['tp1_price'])
        if alert.get('tp2_price'):
            network_stats[network]['tp2_targets'].append(alert['tp2_price'])
        if alert.get('tp3_price'):
            network_stats[network]['tp3_targets'].append(alert['tp3_price'])
        if alert.get('stop_loss_price'):
            network_stats[network]['sl_targets'].append(alert['stop_loss_price'])

        # Pourcentages
        if alert.get('tp1_percent'):
            network_stats[network]['tp1_percents'].append(alert['tp1_percent'])
        if alert.get('tp2_percent'):
            network_stats[network]['tp2_percents'].append(alert['tp2_percent'])
        if alert.get('tp3_percent'):
            network_stats[network]['tp3_percents'].append(alert['tp3_percent'])
        if alert.get('stop_loss_percent'):
            network_stats[network]['sl_percents'].append(abs(alert['stop_loss_percent']))

        # Métriques qualité
        if alert.get('score'):
            network_stats[network]['scores'].append(alert['score'])
        if alert.get('velocite_pump') is not None:
            network_stats[network]['velocites'].append(alert['velocite_pump'])
        if alert.get('liquidity'):
            network_stats[network]['liquidites'].append(alert['liquidity'])
        if alert.get('age_hours') is not None:
            network_stats[network]['ages'].append(alert['age_hours'])

        # Type pump
        type_pump = alert.get('type_pump', 'unknown')
        network_stats[network]['type_pumps'][type_pump] += 1

        # Données de tracking si disponibles
        if alert.get('tp1_was_hit'):
            network_stats[network]['tp1_hit'] += 1
        if alert.get('tp2_was_hit'):
            network_stats[network]['tp2_hit'] += 1
        if alert.get('tp3_was_hit'):
            network_stats[network]['tp3_hit'] += 1
        if alert.get('sl_was_hit'):
            network_stats[network]['sl_hit'] += 1
        if alert.get('max_roi_percent') is not None:
            network_stats[network]['max_rois'].append(alert['max_roi_percent'])

        # Compter celles qui n'ont atteint aucun TP (si données tracking)
        if has_tracking_data:
            if not any([alert.get('tp1_was_hit'), alert.get('tp2_was_hit'),
                       alert.get('tp3_was_hit')]):
                network_stats[network]['no_tp_hit'] += 1

    # ========================================================================
    # SECTION 2: COMPARAISON PAR BLOCKCHAIN
    # ========================================================================
    print(f"\n{'='*100}")
    print("SECTION 2: PERFORMANCE PAR BLOCKCHAIN")
    print("-" * 100)

    print(f"\n{'Blockchain':<12} | {'Alertes':>8} | {'% Total':>8} | {'Score Moy':>10} | "
          f"{'Vel Moy':>10} | {'Liq Moyenne':>15}")
    print(f"{'-'*12}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*15}")

    # Trier par nombre d'alertes
    sorted_networks = sorted(network_stats.items(),
                            key=lambda x: x[1]['total_alerts'],
                            reverse=True)

    for network, stats in sorted_networks:
        count = stats['total_alerts']
        pct = count / total * 100
        avg_score = statistics.mean(stats['scores']) if stats['scores'] else 0
        avg_vel = statistics.mean(stats['velocites']) if stats['velocites'] else 0
        avg_liq = statistics.mean(stats['liquidites']) if stats['liquidites'] else 0

        print(f"{network:<12} | {count:8d} | {pct:7.2f}% | {avg_score:10.2f} | "
              f"{avg_vel:10.2f} | ${avg_liq:14,.0f}")

    # ========================================================================
    # SECTION 3: ANALYSE DES TARGETS PAR BLOCKCHAIN
    # ========================================================================
    print(f"\n{'='*100}")
    print("SECTION 3: OBJECTIFS DE PROFIT PAR BLOCKCHAIN")
    print("-" * 100)

    for network, stats in sorted_networks:
        print(f"\n{network.upper()} - {stats['total_alerts']} alertes:")
        print(f"  {'-'*90}")

        if stats['tp1_percents']:
            avg_tp1 = statistics.mean(stats['tp1_percents'])
            med_tp1 = statistics.median(stats['tp1_percents'])
            print(f"  TP1 moyen:  {avg_tp1:6.2f}% (mediane: {med_tp1:6.2f}%)")

        if stats['tp2_percents']:
            avg_tp2 = statistics.mean(stats['tp2_percents'])
            med_tp2 = statistics.median(stats['tp2_percents'])
            print(f"  TP2 moyen:  {avg_tp2:6.2f}% (mediane: {med_tp2:6.2f}%)")

        if stats['tp3_percents']:
            avg_tp3 = statistics.mean(stats['tp3_percents'])
            med_tp3 = statistics.median(stats['tp3_percents'])
            print(f"  TP3 moyen:  {avg_tp3:6.2f}% (mediane: {med_tp3:6.2f}%)")

        if stats['sl_percents']:
            avg_sl = statistics.mean(stats['sl_percents'])
            med_sl = statistics.median(stats['sl_percents'])
            print(f"  SL moyen:   {avg_sl:6.2f}% (mediane: {med_sl:6.2f}%)")

        # Ratio risque/recompense
        if stats['tp1_percents'] and stats['sl_percents']:
            rr_tp1 = statistics.mean(stats['tp1_percents']) / statistics.mean(stats['sl_percents'])
            rr_tp2 = statistics.mean(stats['tp2_percents']) / statistics.mean(stats['sl_percents']) if stats['tp2_percents'] else 0
            rr_tp3 = statistics.mean(stats['tp3_percents']) / statistics.mean(stats['sl_percents']) if stats['tp3_percents'] else 0
            print(f"  Ratio R/R:  TP1={rr_tp1:.2f}x | TP2={rr_tp2:.2f}x | TP3={rr_tp3:.2f}x")

    # ========================================================================
    # SECTION 4: TAUX DE RÉUSSITE (SI DONNÉES TRACKING)
    # ========================================================================
    if has_tracking_data:
        print(f"\n{'='*100}")
        print("SECTION 4: TAUX DE REUSSITE PAR BLOCKCHAIN")
        print("-" * 100)

        print(f"\n{'Blockchain':<12} | {'Total':>7} | {'TP1 Hit':>8} | {'TP2 Hit':>8} | "
              f"{'TP3 Hit':>8} | {'SL Hit':>7} | {'Aucun TP':>9}")
        print(f"{'-'*12}-+-{'-'*7}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*7}-+-{'-'*9}")

        for network, stats in sorted_networks:
            total_net = stats['total_alerts']
            tp1_hit = stats['tp1_hit']
            tp2_hit = stats['tp2_hit']
            tp3_hit = stats['tp3_hit']
            sl_hit = stats['sl_hit']
            no_tp = stats['no_tp_hit']

            print(f"{network:<12} | {total_net:7d} | "
                  f"{tp1_hit:4d} ({tp1_hit/total_net*100:4.1f}%) | "
                  f"{tp2_hit:4d} ({tp2_hit/total_net*100:4.1f}%) | "
                  f"{tp3_hit:4d} ({tp3_hit/total_net*100:4.1f}%) | "
                  f"{sl_hit:3d} ({sl_hit/total_net*100:4.1f}%) | "
                  f"{no_tp:4d} ({no_tp/total_net*100:4.1f}%)")

        # Win rate global
        print(f"\n{'Blockchain':<12} | {'Win Rate':>10} | {'ROI Moyen Max':>15} | {'Meilleur ROI':>13}")
        print(f"{'-'*12}-+-{'-'*10}-+-{'-'*15}-+-{'-'*13}")

        for network, stats in sorted_networks:
            total_net = stats['total_alerts']
            any_tp_hit = stats['tp1_hit'] + stats['tp2_hit'] + stats['tp3_hit']
            win_rate = (any_tp_hit / total_net * 100) if total_net > 0 else 0

            avg_max_roi = statistics.mean(stats['max_rois']) if stats['max_rois'] else 0
            best_roi = max(stats['max_rois']) if stats['max_rois'] else 0

            print(f"{network:<12} | {win_rate:9.2f}% | {avg_max_roi:14.2f}% | {best_roi:12.2f}%")

    # ========================================================================
    # SECTION 5: ANALYSE PAR TYPE DE PUMP ET BLOCKCHAIN
    # ========================================================================
    print(f"\n{'='*100}")
    print("SECTION 5: DISTRIBUTION DES TYPES DE PUMP PAR BLOCKCHAIN")
    print("-" * 100)

    for network, stats in sorted_networks:
        print(f"\n{network.upper()}:")
        total_net = stats['total_alerts']

        # Trier par fréquence
        sorted_pumps = sorted(stats['type_pumps'].items(),
                             key=lambda x: x[1],
                             reverse=True)

        for pump_type, count in sorted_pumps:
            pct = count / total_net * 100
            print(f"  {pump_type:<15}: {count:4d} ({pct:5.2f}%)")

    # ========================================================================
    # SECTION 6: BLOCKCHAIN LA PLUS RENTABLE - SYNTHÈSE
    # ========================================================================
    print(f"\n{'='*100}")
    print("SECTION 6: CLASSEMENT DES BLOCKCHAINS - SYNTHESE")
    print("-" * 100)

    # Calculer un score composite pour chaque blockchain
    blockchain_scores = []

    for network, stats in network_stats.items():
        if stats['total_alerts'] == 0:
            continue

        # Métriques de qualité
        avg_score = statistics.mean(stats['scores']) if stats['scores'] else 0
        avg_vel = statistics.mean(stats['velocites']) if stats['velocites'] else 0
        avg_liq = statistics.mean(stats['liquidites']) if stats['liquidites'] else 0

        # Normaliser liquidité (log scale)
        liq_score = min(avg_liq / 100000, 10)  # Max 10 points

        # Métriques de performance (si tracking disponible)
        if has_tracking_data and stats['total_alerts'] > 0:
            win_rate = ((stats['tp1_hit'] + stats['tp2_hit'] + stats['tp3_hit'])
                       / stats['total_alerts'] * 100)
            avg_max_roi = statistics.mean(stats['max_rois']) if stats['max_rois'] else 0
        else:
            # Estimer basé sur qualité
            win_rate = avg_score * 0.5  # Proxy
            avg_max_roi = avg_vel * 0.5  # Proxy

        # Score composite (pondéré)
        composite_score = (
            avg_score * 0.3 +           # 30% score qualité
            min(avg_vel, 50) * 0.2 +    # 20% vélocité (max 50)
            liq_score * 0.1 +           # 10% liquidité
            win_rate * 0.4              # 40% win rate
        )

        blockchain_scores.append({
            'network': network,
            'composite_score': composite_score,
            'avg_score': avg_score,
            'avg_vel': avg_vel,
            'avg_liq': avg_liq,
            'win_rate': win_rate,
            'avg_max_roi': avg_max_roi,
            'total_alerts': stats['total_alerts'],
        })

    # Trier par score composite
    blockchain_scores.sort(key=lambda x: x['composite_score'], reverse=True)

    print(f"\nClassement (Score composite = qualite + performance):\n")
    print(f"{'Rang':<5} | {'Blockchain':<12} | {'Score':>8} | {'Qualite':>8} | "
          f"{'Velocite':>10} | {'Win Rate':>9} | {'Alertes':>8}")
    print(f"{'-'*5}-+-{'-'*12}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*9}-+-{'-'*8}")

    for i, bc in enumerate(blockchain_scores, 1):
        medal = ['', '', ''][i-1] if i <= 3 else ' '
        print(f"{i:<4}{medal} | {bc['network']:<12} | {bc['composite_score']:8.2f} | "
              f"{bc['avg_score']:8.2f} | {bc['avg_vel']:10.2f} | "
              f"{bc['win_rate']:8.2f}% | {bc['total_alerts']:8d}")

    # ========================================================================
    # SECTION 7: RECOMMANDATIONS
    # ========================================================================
    print(f"\n{'='*100}")
    print("SECTION 7: RECOMMANDATIONS STRATEGIQUES PAR BLOCKCHAIN")
    print("-" * 100)

    best = blockchain_scores[0] if blockchain_scores else None
    worst = blockchain_scores[-1] if blockchain_scores else None

    if best:
        print(f"\nBLOCKCHAIN LA PLUS RENTABLE: {best['network'].upper()}")
        print(f"  Score composite: {best['composite_score']:.2f}")
        print(f"  Score qualite:   {best['avg_score']:.2f}")
        print(f"  Velocite moy:    {best['avg_vel']:.2f}")
        print(f"  Win rate:        {best['win_rate']:.2f}%")
        print(f"  Liquidite moy:   ${best['avg_liq']:,.0f}")
        print(f"  Nombre alertes:  {best['total_alerts']}")

    if worst:
        print(f"\nBLOCKCHAIN LA MOINS PERFORMANTE: {worst['network'].upper()}")
        print(f"  Score composite: {worst['composite_score']:.2f}")
        print(f"  Score qualite:   {worst['avg_score']:.2f}")
        print(f"  Win rate:        {worst['win_rate']:.2f}%")
        print(f"  => RECOMMENDATION: Filtrer agressivement ou eviter")

    # Recommandations par rang
    print(f"\nRECOMMANDATIONS PAR RANG:")
    for i, bc in enumerate(blockchain_scores, 1):
        if i == 1:
            rec = "FOCUS PRINCIPAL - Qualite maximale"
        elif i == 2:
            rec = "EXCELLENT CHOIX - Bon equilibre"
        elif i == 3:
            rec = "BON POTENTIEL - A surveiller"
        elif i == 4:
            rec = "ACCEPTABLE - Filtrage necessaire"
        else:
            rec = "EVITER ou filtrage tres agressif"

        print(f"  {i}. {bc['network'].upper():<12}: {rec}")

    # Analyse des forces/faiblesses
    print(f"\nFORCES/FAIBLESSES PAR BLOCKCHAIN:")
    for bc in blockchain_scores:
        net = bc['network'].upper()
        strengths = []
        weaknesses = []

        if bc['avg_score'] > 80:
            strengths.append("Score eleve")
        elif bc['avg_score'] < 70:
            weaknesses.append("Score faible")

        if bc['avg_vel'] > 20:
            strengths.append("Velocite forte")
        elif bc['avg_vel'] < 5:
            weaknesses.append("Velocite faible")

        if bc['avg_liq'] > 500000:
            strengths.append("Liquidite excellente")
        elif bc['avg_liq'] < 100000:
            weaknesses.append("Liquidite faible")

        if bc['win_rate'] > 40:
            strengths.append("Win rate eleve")
        elif bc['win_rate'] < 25:
            weaknesses.append("Win rate faible")

        print(f"\n  {net}:")
        if strengths:
            print(f"    Forces:     {', '.join(strengths)}")
        if weaknesses:
            print(f"    Faiblesses: {', '.join(weaknesses)}")

    print(f"\n{'='*100}")
    print("ANALYSE TERMINEE")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_tp_performance.py alerts_railway_export_utf8.json")
        sys.exit(1)

    json_file = sys.argv[1]

    if not Path(json_file).exists():
        print(f"Erreur: Fichier non trouve: {json_file}")
        sys.exit(1)

    analyze_tp_performance(json_file)
