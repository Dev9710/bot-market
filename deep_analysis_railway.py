#!/usr/bin/env python3
"""
Analyse approfondie des 4252 alertes Railway.
Detection de patterns gagnants, correlations cachees, insights.
Sans biais V3 - analyse pure des donnees.

Usage:
    python deep_analysis_railway.py alerts_railway_export_utf8.json
"""

import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import statistics

def deep_analysis(json_file: str):
    """Analyse approfondie multi-dimensionnelle."""

    print(f"\n{'='*90}")
    print(f"   ANALYSE APPROFONDIE RAILWAY - 4252 ALERTES")
    print(f"   Detection de patterns, correlations, insights cachés")
    print(f"{'='*90}\n")

    # Charger données
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    alerts = data.get('alerts', [])
    total = len(alerts)

    print(f"Dataset: {total} alertes analysees\n")

    # ========================================================================
    # SECTION 1: DISTRIBUTION MULTI-DIMENSIONNELLE
    # ========================================================================
    print(f"{'='*90}")
    print("SECTION 1: PROFIL MULTI-DIMENSIONNEL DES ALERTES")
    print("-" * 90)

    # Collecte des métriques
    metrics = {
        'scores': [],
        'velocites': [],
        'ages': [],
        'liquidites': [],
        'volumes_24h': [],
        'volumes_6h': [],
        'volumes_1h': [],
        'buy_ratios': [],
        'total_txns': [],
    }

    for alert in alerts:
        if alert.get('score') is not None:
            metrics['scores'].append(alert['score'])
        if alert.get('velocite_pump') is not None:
            metrics['velocites'].append(alert['velocite_pump'])
        if alert.get('age_hours') is not None:
            metrics['ages'].append(alert['age_hours'])
        if alert.get('liquidity') is not None:
            metrics['liquidites'].append(alert['liquidity'])
        if alert.get('volume_24h') is not None:
            metrics['volumes_24h'].append(alert['volume_24h'])
        if alert.get('volume_6h') is not None:
            metrics['volumes_6h'].append(alert['volume_6h'])
        if alert.get('volume_1h') is not None:
            metrics['volumes_1h'].append(alert['volume_1h'])
        if alert.get('buy_ratio') is not None:
            metrics['buy_ratios'].append(alert['buy_ratio'])
        if alert.get('total_txns') is not None:
            metrics['total_txns'].append(alert['total_txns'])

    # Statistiques descriptives complètes
    def stats_desc(data, name, decimals=2):
        if not data:
            return
        print(f"\n{name}:")
        print(f"  Count:      {len(data)}")
        print(f"  Moyenne:    {statistics.mean(data):.{decimals}f}")
        print(f"  Mediane:    {statistics.median(data):.{decimals}f}")
        print(f"  Std Dev:    {statistics.stdev(data) if len(data) > 1 else 0:.{decimals}f}")
        print(f"  Min:        {min(data):.{decimals}f}")
        print(f"  Q1 (25%):   {statistics.quantiles(data, n=4)[0]:.{decimals}f}")
        print(f"  Q2 (50%):   {statistics.quantiles(data, n=4)[1]:.{decimals}f}")
        print(f"  Q3 (75%):   {statistics.quantiles(data, n=4)[2]:.{decimals}f}")
        print(f"  Max:        {max(data):.{decimals}f}")

    stats_desc(metrics['scores'], "SCORE (0-100)", 1)
    stats_desc(metrics['velocites'], "VELOCITE PUMP", 2)
    stats_desc(metrics['ages'], "AGE TOKEN (heures)", 1)
    stats_desc(metrics['liquidites'], "LIQUIDITE ($)", 0)
    stats_desc(metrics['buy_ratios'], "BUY RATIO (0-1)", 3)

    # ========================================================================
    # SECTION 2: PATTERNS PAR RÉSEAU - ANALYSE FINE
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 2: PATTERNS PAR RESEAU - CARACTERISTIQUES DISTINCTES")
    print("-" * 90)

    network_profiles = defaultdict(lambda: {
        'count': 0,
        'scores': [],
        'velocites': [],
        'ages': [],
        'liquidites': [],
        'buy_ratios': [],
        'type_pumps': defaultdict(int),
    })

    for alert in alerts:
        net = alert.get('network', 'unknown')
        network_profiles[net]['count'] += 1

        if alert.get('score') is not None:
            network_profiles[net]['scores'].append(alert['score'])
        if alert.get('velocite_pump') is not None:
            network_profiles[net]['velocites'].append(alert['velocite_pump'])
        if alert.get('age_hours') is not None:
            network_profiles[net]['ages'].append(alert['age_hours'])
        if alert.get('liquidity') is not None:
            network_profiles[net]['liquidites'].append(alert['liquidity'])
        if alert.get('buy_ratio') is not None:
            network_profiles[net]['buy_ratios'].append(alert['buy_ratio'])

        type_pump = alert.get('type_pump', 'unknown')
        network_profiles[net]['type_pumps'][type_pump] += 1

    for network in sorted(network_profiles.keys()):
        prof = network_profiles[network]
        print(f"\n{network.upper()} ({prof['count']} alertes - {prof['count']/total*100:.1f}%):")
        print(f"  {'-'*80}")

        if prof['scores']:
            avg_score = statistics.mean(prof['scores'])
            print(f"  Score moyen:        {avg_score:.1f}")

        if prof['velocites']:
            avg_vel = statistics.mean(prof['velocites'])
            med_vel = statistics.median(prof['velocites'])
            high_vel = sum(1 for v in prof['velocites'] if v > 10)
            print(f"  Velocite moyenne:   {avg_vel:.2f} (mediane: {med_vel:.2f})")
            print(f"  Velocite >10:       {high_vel}/{len(prof['velocites'])} ({high_vel/len(prof['velocites'])*100:.1f}%)")

        if prof['ages']:
            avg_age = statistics.mean(prof['ages'])
            print(f"  Age moyen:          {avg_age:.1f}h")

        if prof['liquidites']:
            avg_liq = statistics.mean(prof['liquidites'])
            print(f"  Liquidite moyenne:  ${avg_liq:,.0f}")

        if prof['buy_ratios']:
            avg_buy = statistics.mean(prof['buy_ratios'])
            print(f"  Buy ratio moyen:    {avg_buy:.3f}")

        # Type pump dominant
        if prof['type_pumps']:
            dominant = max(prof['type_pumps'].items(), key=lambda x: x[1])
            print(f"  Type pump dominant: {dominant[0]} ({dominant[1]}/{prof['count']} = {dominant[1]/prof['count']*100:.1f}%)")

    # ========================================================================
    # SECTION 3: ZONES D'AGE - PATTERNS DÉTAILLÉS
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 3: ANALYSE PAR ZONE D'AGE - RECHERCHE DE SWEET SPOTS")
    print("-" * 90)

    age_zones = {
        '0-6h (nouveau-ne)': (0, 6),
        '6-12h (tres jeune)': (6, 12),
        '12-18h (jeune)': (12, 18),
        '18-24h (1 jour)': (18, 24),
        '24-36h (1.5 jour)': (24, 36),
        '36-48h (2 jours)': (36, 48),
        '48-60h (2.5 jours)': (48, 60),
        '60-72h (3 jours)': (60, 72),
        '72-96h (3-4 jours)': (72, 96),
        '>96h (mature)': (96, 999),
    }

    age_analysis = {}
    for zone_name, (min_age, max_age) in age_zones.items():
        zone_alerts = [a for a in alerts
                       if a.get('age_hours') is not None
                       and min_age <= a.get('age_hours') < max_age]

        if zone_alerts:
            age_analysis[zone_name] = {
                'count': len(zone_alerts),
                'avg_score': statistics.mean([a['score'] for a in zone_alerts if a.get('score')]),
                'avg_velocite': statistics.mean([a['velocite_pump'] for a in zone_alerts if a.get('velocite_pump')]),
                'avg_liquidity': statistics.mean([a['liquidity'] for a in zone_alerts if a.get('liquidity')]),
            }

    print(f"\n{'Zone Age':<25} | {'Count':>6} | {'% Total':>7} | {'Score':>6} | {'Velocite':>9} | {'Liquidite':>12}")
    print(f"{'-'*25}-+-{'-'*6}-+-{'-'*7}-+-{'-'*6}-+-{'-'*9}-+-{'-'*12}")

    for zone_name in age_zones.keys():
        if zone_name in age_analysis:
            analysis = age_analysis[zone_name]
            pct = analysis['count'] / total * 100
            print(f"{zone_name:<25} | {analysis['count']:6d} | {pct:6.1f}% | "
                  f"{analysis['avg_score']:6.1f} | {analysis['avg_velocite']:9.2f} | "
                  f"${analysis['avg_liquidity']:11,.0f}")

    # ========================================================================
    # SECTION 4: ANALYSE VELOCITE - SEGMENTATION FINE
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 4: SEGMENTATION PAR VELOCITE - IDENTIFICATION DES WINNERS")
    print("-" * 90)

    vel_zones = {
        'Negatif (<0)': lambda v: v < 0,
        'Stagnant (0-1)': lambda v: 0 <= v < 1,
        'Lent (1-3)': lambda v: 1 <= v < 3,
        'Modere (3-5)': lambda v: 3 <= v < 5,
        'Actif (5-10)': lambda v: 5 <= v < 10,
        'Rapide (10-20)': lambda v: 10 <= v < 20,
        'Tres rapide (20-50)': lambda v: 20 <= v < 50,
        'Explosif (50-100)': lambda v: 50 <= v < 100,
        'Parabolique (>100)': lambda v: v >= 100,
    }

    vel_analysis = {}
    for zone_name, condition in vel_zones.items():
        zone_alerts = [a for a in alerts
                       if a.get('velocite_pump') is not None
                       and condition(a.get('velocite_pump'))]

        if zone_alerts:
            vel_analysis[zone_name] = {
                'count': len(zone_alerts),
                'avg_score': statistics.mean([a['score'] for a in zone_alerts if a.get('score')]),
                'avg_age': statistics.mean([a['age_hours'] for a in zone_alerts if a.get('age_hours')]),
                'avg_liquidity': statistics.mean([a['liquidity'] for a in zone_alerts if a.get('liquidity')]),
            }

    print(f"\n{'Zone Velocite':<25} | {'Count':>6} | {'% Total':>7} | {'Score':>6} | {'Age (h)':>8} | {'Liquidite':>12}")
    print(f"{'-'*25}-+-{'-'*6}-+-{'-'*7}-+-{'-'*6}-+-{'-'*8}-+-{'-'*12}")

    for zone_name in vel_zones.keys():
        if zone_name in vel_analysis:
            analysis = vel_analysis[zone_name]
            pct = analysis['count'] / total * 100
            print(f"{zone_name:<25} | {analysis['count']:6d} | {pct:6.1f}% | "
                  f"{analysis['avg_score']:6.1f} | {analysis['avg_age']:8.1f} | "
                  f"${analysis['avg_liquidity']:11,.0f}")

    # ========================================================================
    # SECTION 5: CROISEMENT SCORE × VELOCITE × AGE (3D)
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 5: ANALYSE TRIDIMENSIONNELLE - SCORE × VELOCITE × AGE")
    print("-" * 90)

    # Définir des buckets
    score_buckets = [(80, 100, '80+'), (70, 79, '70-79'), (60, 69, '60-69'), (0, 59, '<60')]
    vel_buckets = [(10, 9999, 'Vel>10'), (5, 10, 'Vel 5-10'), (0, 5, 'Vel<5')]
    age_buckets = [(0, 24, 'Age<24h'), (24, 48, 'Age 24-48h'), (48, 999, 'Age>48h')]

    # Matrice 3D
    matrix_3d = defaultdict(int)

    for alert in alerts:
        score = alert.get('score', 0)
        vel = alert.get('velocite_pump')
        age = alert.get('age_hours')

        if vel is None or age is None:
            continue

        # Trouver buckets
        score_label = next((label for min_s, max_s, label in score_buckets if min_s <= score <= max_s), None)
        vel_label = next((label for min_v, max_v, label in vel_buckets if min_v <= vel < max_v), None)
        age_label = next((label for min_a, max_a, label in age_buckets if min_a <= age < max_a), None)

        if score_label and vel_label and age_label:
            key = (score_label, vel_label, age_label)
            matrix_3d[key] += 1

    print(f"\nDistribution 3D (Top 20 combinaisons):")
    print(f"{'Score':<8} | {'Velocite':<12} | {'Age':<13} | {'Count':>6} | {'% Total':>7}")
    print(f"{'-'*8}-+-{'-'*12}-+-{'-'*13}-+-{'-'*6}-+-{'-'*7}")

    sorted_combos = sorted(matrix_3d.items(), key=lambda x: x[1], reverse=True)[:20]
    for (score_l, vel_l, age_l), count in sorted_combos:
        pct = count / total * 100
        print(f"{score_l:<8} | {vel_l:<12} | {age_l:<13} | {count:6d} | {pct:6.2f}%")

    # ========================================================================
    # SECTION 6: ANALYSE LIQUIDITÉ - ZONES OPTIMALES
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 6: ANALYSE LIQUIDITE - SWEET SPOTS PAR RESEAU")
    print("-" * 90)

    liq_by_network = defaultdict(list)
    for alert in alerts:
        if alert.get('liquidity'):
            net = alert.get('network', 'unknown')
            liq_by_network[net].append(alert['liquidity'])

    print(f"\n{'Reseau':<12} | {'Count':>6} | {'Moyenne':>12} | {'Mediane':>12} | {'Q1':>12} | {'Q3':>12}")
    print(f"{'-'*12}-+-{'-'*6}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}")

    for network in sorted(liq_by_network.keys()):
        liqs = liq_by_network[network]
        avg = statistics.mean(liqs)
        med = statistics.median(liqs)
        q1 = statistics.quantiles(liqs, n=4)[0]
        q3 = statistics.quantiles(liqs, n=4)[2]
        print(f"{network:<12} | {len(liqs):6d} | ${avg:11,.0f} | ${med:11,.0f} | ${q1:11,.0f} | ${q3:11,.0f}")

    # ========================================================================
    # SECTION 7: TYPE PUMP - ANALYSE COMPARATIVE
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 7: ANALYSE PAR TYPE DE PUMP - CARACTERISTIQUES")
    print("-" * 90)

    pump_profiles = defaultdict(lambda: {
        'count': 0,
        'scores': [],
        'velocites': [],
        'ages': [],
        'liquidites': [],
    })

    for alert in alerts:
        ptype = alert.get('type_pump', 'unknown')
        pump_profiles[ptype]['count'] += 1

        if alert.get('score') is not None:
            pump_profiles[ptype]['scores'].append(alert['score'])
        if alert.get('velocite_pump') is not None:
            pump_profiles[ptype]['velocites'].append(alert['velocite_pump'])
        if alert.get('age_hours') is not None:
            pump_profiles[ptype]['ages'].append(alert['age_hours'])
        if alert.get('liquidity') is not None:
            pump_profiles[ptype]['liquidites'].append(alert['liquidity'])

    print(f"\n{'Type Pump':<15} | {'Count':>6} | {'%':>6} | {'Score':>6} | {'Velocite':>9} | {'Age (h)':>8} | {'Liquidite':>12}")
    print(f"{'-'*15}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*9}-+-{'-'*8}-+-{'-'*12}")

    for ptype in sorted(pump_profiles.keys(), key=lambda x: pump_profiles[x]['count'], reverse=True):
        prof = pump_profiles[ptype]
        pct = prof['count'] / total * 100
        avg_score = statistics.mean(prof['scores']) if prof['scores'] else 0
        avg_vel = statistics.mean(prof['velocites']) if prof['velocites'] else 0
        avg_age = statistics.mean(prof['ages']) if prof['ages'] else 0
        avg_liq = statistics.mean(prof['liquidites']) if prof['liquidites'] else 0

        print(f"{ptype:<15} | {prof['count']:6d} | {pct:5.1f}% | {avg_score:6.1f} | "
              f"{avg_vel:9.2f} | {avg_age:8.1f} | ${avg_liq:11,.0f}")

    # ========================================================================
    # SECTION 8: BUY RATIO - CORRELATION AVEC PERFORMANCE
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 8: ANALYSE BUY RATIO - SENTIMENT DU MARCHE")
    print("-" * 90)

    buy_ratio_zones = {
        'Bearish (<0.45)': lambda r: r < 0.45,
        'Faible (0.45-0.50)': lambda r: 0.45 <= r < 0.50,
        'Neutre (0.50-0.55)': lambda r: 0.50 <= r < 0.55,
        'Positif (0.55-0.60)': lambda r: 0.55 <= r < 0.60,
        'Bullish (0.60-0.70)': lambda r: 0.60 <= r < 0.70,
        'Tres bullish (>0.70)': lambda r: r >= 0.70,
    }

    buy_ratio_analysis = {}
    for zone_name, condition in buy_ratio_zones.items():
        zone_alerts = [a for a in alerts
                       if a.get('buy_ratio') is not None
                       and condition(a.get('buy_ratio'))]

        if zone_alerts:
            buy_ratio_analysis[zone_name] = {
                'count': len(zone_alerts),
                'avg_score': statistics.mean([a['score'] for a in zone_alerts if a.get('score')]),
                'avg_velocite': statistics.mean([a['velocite_pump'] for a in zone_alerts if a.get('velocite_pump')]),
                'avg_liquidity': statistics.mean([a['liquidity'] for a in zone_alerts if a.get('liquidity')]),
            }

    print(f"\n{'Zone Buy Ratio':<22} | {'Count':>6} | {'%':>6} | {'Score':>6} | {'Velocite':>9} | {'Liquidite':>12}")
    print(f"{'-'*22}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*9}-+-{'-'*12}")

    for zone_name in buy_ratio_zones.keys():
        if zone_name in buy_ratio_analysis:
            analysis = buy_ratio_analysis[zone_name]
            pct = analysis['count'] / total * 100
            print(f"{zone_name:<22} | {analysis['count']:6d} | {pct:5.1f}% | "
                  f"{analysis['avg_score']:6.1f} | {analysis['avg_velocite']:9.2f} | "
                  f"${analysis['avg_liquidity']:11,.0f}")

    # ========================================================================
    # SECTION 9: PATTERNS GAGNANTS - DETECTION
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 9: DETECTION DE PATTERNS GAGNANTS POTENTIELS")
    print("-" * 90)

    # Pattern 1: Score élevé + Velocite forte + Age optimal
    pattern_1 = [a for a in alerts
                 if a.get('score', 0) >= 75
                 and a.get('velocite_pump', 0) > 10
                 and 24 <= a.get('age_hours', 0) <= 72]

    # Pattern 2: Buy ratio élevé + Liquidité forte
    pattern_2 = [a for a in alerts
                 if a.get('buy_ratio', 0) > 0.60
                 and a.get('liquidity', 0) > 50000]

    # Pattern 3: Ethereum/Solana + Velocite explosive
    pattern_3 = [a for a in alerts
                 if a.get('network') in ['eth', 'solana']
                 and a.get('velocite_pump', 0) > 20]

    # Pattern 4: Score très élevé seul
    pattern_4 = [a for a in alerts if a.get('score', 0) >= 85]

    # Pattern 5: Jeune + Rapide + Bullish
    pattern_5 = [a for a in alerts
                 if a.get('age_hours', 999) < 12
                 and a.get('velocite_pump', 0) > 15
                 and a.get('buy_ratio', 0) > 0.65]

    # Pattern 6: Mature + Stable + Liquide
    pattern_6 = [a for a in alerts
                 if a.get('age_hours', 0) > 48
                 and a.get('velocite_pump', 0) > 5
                 and a.get('liquidity', 0) > 100000]

    print(f"\nPatterns identifies:")
    print(f"\n1. PATTERN 'GOLDEN' (Score>=75 + Vel>10 + Age 24-72h):")
    print(f"   Count: {len(pattern_1)} ({len(pattern_1)/total*100:.2f}%)")
    if pattern_1:
        avg_score_p1 = statistics.mean([a['score'] for a in pattern_1])
        avg_vel_p1 = statistics.mean([a['velocite_pump'] for a in pattern_1])
        print(f"   Score moyen: {avg_score_p1:.1f}")
        print(f"   Velocite moyenne: {avg_vel_p1:.1f}")

    print(f"\n2. PATTERN 'BULLISH MOMENTUM' (Buy ratio>0.60 + Liq>50k):")
    print(f"   Count: {len(pattern_2)} ({len(pattern_2)/total*100:.2f}%)")
    if pattern_2:
        avg_liq_p2 = statistics.mean([a['liquidity'] for a in pattern_2])
        print(f"   Liquidite moyenne: ${avg_liq_p2:,.0f}")

    print(f"\n3. PATTERN 'EXPLOSIVE MAJORS' (ETH/SOL + Vel>20):")
    print(f"   Count: {len(pattern_3)} ({len(pattern_3)/total*100:.2f}%)")
    if pattern_3:
        by_net_p3 = defaultdict(int)
        for a in pattern_3:
            by_net_p3[a.get('network')] += 1
        print(f"   Distribution: {dict(by_net_p3)}")

    print(f"\n4. PATTERN 'HIGH CONFIDENCE' (Score>=85):")
    print(f"   Count: {len(pattern_4)} ({len(pattern_4)/total*100:.2f}%)")
    if pattern_4:
        avg_vel_p4 = statistics.mean([a.get('velocite_pump', 0) for a in pattern_4])
        print(f"   Velocite moyenne: {avg_vel_p4:.1f}")

    print(f"\n5. PATTERN 'EARLY ROCKET' (Age<12h + Vel>15 + Buy ratio>0.65):")
    print(f"   Count: {len(pattern_5)} ({len(pattern_5)/total*100:.2f}%)")
    if pattern_5:
        avg_age_p5 = statistics.mean([a['age_hours'] for a in pattern_5])
        print(f"   Age moyen: {avg_age_p5:.1f}h")

    print(f"\n6. PATTERN 'STABLE GROWTH' (Age>48h + Vel>5 + Liq>100k):")
    print(f"   Count: {len(pattern_6)} ({len(pattern_6)/total*100:.2f}%)")
    if pattern_6:
        avg_age_p6 = statistics.mean([a['age_hours'] for a in pattern_6])
        print(f"   Age moyen: {avg_age_p6:.1f}h")

    # ========================================================================
    # SECTION 10: INSIGHTS & CONCLUSIONS
    # ========================================================================
    print(f"\n{'='*90}")
    print("SECTION 10: INSIGHTS & PATTERNS CACHES DETECTES")
    print("-" * 90)

    insights = []

    # Insight 1: Meilleur réseau
    best_network = max(network_profiles.items(),
                      key=lambda x: statistics.mean(x[1]['scores']) if x[1]['scores'] else 0)
    insights.append(f"Reseau avec meilleur score moyen: {best_network[0].upper()} "
                   f"({statistics.mean(best_network[1]['scores']):.1f})")

    # Insight 2: Zone age optimale
    best_age_zone = max(age_analysis.items(), key=lambda x: x[1]['avg_score'])
    insights.append(f"Zone d'age avec meilleur score: {best_age_zone[0]} "
                   f"(score moyen: {best_age_zone[1]['avg_score']:.1f})")

    # Insight 3: Zone velocite optimale
    best_vel_zone = max(vel_analysis.items(), key=lambda x: x[1]['avg_score'])
    insights.append(f"Zone velocite avec meilleur score: {best_vel_zone[0]} "
                   f"(score moyen: {best_vel_zone[1]['avg_score']:.1f})")

    # Insight 4: Type pump performant
    best_pump = max(pump_profiles.items(),
                   key=lambda x: statistics.mean(x[1]['scores']) if x[1]['scores'] else 0)
    insights.append(f"Type pump avec meilleur score: {best_pump[0]} "
                   f"({statistics.mean(best_pump[1]['scores']):.1f})")

    # Insight 5: Correlation buy ratio
    best_buy_zone = max(buy_ratio_analysis.items(), key=lambda x: x[1]['avg_score'])
    insights.append(f"Buy ratio optimal: {best_buy_zone[0]} "
                   f"(score moyen: {best_buy_zone[1]['avg_score']:.1f})")

    # Insight 6: Pattern le plus rare et potentiellement précieux
    patterns_counts = [
        ("GOLDEN", len(pattern_1)),
        ("BULLISH MOMENTUM", len(pattern_2)),
        ("EXPLOSIVE MAJORS", len(pattern_3)),
        ("HIGH CONFIDENCE", len(pattern_4)),
        ("EARLY ROCKET", len(pattern_5)),
        ("STABLE GROWTH", len(pattern_6)),
    ]
    rarest = min(patterns_counts, key=lambda x: x[1] if x[1] > 0 else 99999)
    insights.append(f"Pattern le plus selectif: {rarest[0]} ({rarest[1]} alertes = {rarest[1]/total*100:.2f}%)")

    print("\nINSIGHTS CLES:")
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")

    # Recommandations stratégiques
    print(f"\nRECOMMANDATIONS STRATEGIQUES BASEES SUR LES DONNEES:")
    print(f"\n1. FOCUS RESEAU:")
    top_3_networks = sorted(network_profiles.items(),
                           key=lambda x: statistics.mean(x[1]['scores']) if x[1]['scores'] else 0,
                           reverse=True)[:3]
    for net, prof in top_3_networks:
        avg_sc = statistics.mean(prof['scores']) if prof['scores'] else 0
        print(f"   - {net.upper()}: score moyen {avg_sc:.1f}")

    print(f"\n2. FENETRE TEMPORELLE OPTIMALE:")
    top_age_zones = sorted(age_analysis.items(), key=lambda x: x[1]['avg_score'], reverse=True)[:3]
    for zone, analysis in top_age_zones:
        print(f"   - {zone}: score {analysis['avg_score']:.1f}, velocite {analysis['avg_velocite']:.2f}")

    print(f"\n3. SEUILS DE VELOCITE:")
    vel_high_score = [z for z, a in vel_analysis.items() if a['avg_score'] > 80]
    if vel_high_score:
        print(f"   - Zones avec score moyen >80: {', '.join(vel_high_score)}")

    print(f"\n4. PATTERNS A PRIVILEGIER:")
    valuable_patterns = [(name, count) for name, count in patterns_counts if 10 <= count <= 200]
    if valuable_patterns:
        for name, count in valuable_patterns:
            print(f"   - {name}: {count} alertes (selectif mais pas trop rare)")

    print(f"\n{'='*90}")
    print("ANALYSE APPROFONDIE TERMINEE")
    print(f"{'='*90}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deep_analysis_railway.py alerts_railway_export_utf8.json")
        sys.exit(1)

    json_file = sys.argv[1]

    if not Path(json_file).exists():
        print(f"Erreur: Fichier non trouve: {json_file}")
        sys.exit(1)

    deep_analysis(json_file)
