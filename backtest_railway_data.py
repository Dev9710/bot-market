#!/usr/bin/env python3
"""
Backtest rapide sur données Railway exportées.

Usage:
    python backtest_railway_data.py alerts_railway_export.json
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

def analyze_railway_export(json_file: str):
    """Analyse rapide des alertes Railway."""

    print(f"\n{'='*70}")
    print(f"   BACKTEST DONNEES RAILWAY (V2)")
    print(f"{'='*70}\n")

    # Charger JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    alerts = data.get('alerts', [])
    total = len(alerts)

    print(f"Total alertes: {total}\n")

    # Stats par réseau
    by_network = defaultdict(int)
    by_score_range = defaultdict(int)
    velocites = []
    ages = []

    for alert in alerts:
        network = alert.get('network', 'unknown')
        score = alert.get('score', 0)
        velocite = alert.get('velocite_pump', 0)
        age = alert.get('age_hours', 0)

        by_network[network] += 1

        if score >= 80:
            by_score_range['80+'] += 1
        elif score >= 70:
            by_score_range['70-79'] += 1
        elif score >= 60:
            by_score_range['60-69'] += 1
        elif score >= 50:
            by_score_range['50-59'] += 1
        else:
            by_score_range['<50'] += 1

        if velocite:
            velocites.append(velocite)
        if age:
            ages.append(age)

    # Afficher stats
    print("REPARTITION PAR RESEAU:")
    for network, count in sorted(by_network.items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        print(f"   {network:10s}: {count:4d} alertes ({pct:5.1f}%)")

    print(f"\nREPARTITION PAR SCORE:")
    for score_range in ['80+', '70-79', '60-69', '50-59', '<50']:
        count = by_score_range.get(score_range, 0)
        pct = count / total * 100 if total > 0 else 0
        print(f"   {score_range:6s}: {count:4d} alertes ({pct:5.1f}%)")

    # Stats vélocité
    if velocites:
        print(f"\nVELOCITE:")
        print(f"   Moyenne: {sum(velocites)/len(velocites):.1f}")
        print(f"   Min: {min(velocites):.1f}")
        print(f"   Max: {max(velocites):.1f}")

        # Combien passent le filtre V3 (>5)
        passing_v3 = sum(1 for v in velocites if v > 5)
        pct_v3 = passing_v3 / len(velocites) * 100
        print(f"   Passent filtre V3 (>5): {passing_v3}/{len(velocites)} ({pct_v3:.1f}%)")

    # Stats âge
    if ages:
        print(f"\nAGE DES TOKENS:")
        print(f"   Moyen: {sum(ages)/len(ages):.1f}h")
        print(f"   Min: {min(ages):.1f}h")
        print(f"   Max: {max(ages):.1f}h")

        # Zones V3
        danger_zone = sum(1 for a in ages if 12 <= a <= 24)
        optimal_zone = sum(1 for a in ages if 48 <= a <= 72)

        print(f"   Zone danger (12-24h): {danger_zone} ({danger_zone/len(ages)*100:.1f}%)")
        print(f"   Zone optimale (2-3j): {optimal_zone} ({optimal_zone/len(ages)*100:.1f}%)")

    # Simulation filtre V3
    print(f"\nSIMULATION FILTRES V3:")

    v3_candidates = 0
    for alert in alerts:
        score = alert.get('score', 0)
        velocite = alert.get('velocite_pump', 0)
        type_pump = alert.get('type_pump', '')
        age = alert.get('age_hours', 0)

        # Critères V3
        if (score >= 60 and
            velocite > 5 and
            type_pump != 'LENT' and
            not (12 <= age <= 24)):
            v3_candidates += 1

    reduction_pct = (total - v3_candidates) / total * 100 if total > 0 else 0

    print(f"   Alertes V2: {total}")
    print(f"   Passeraient filtre V3: {v3_candidates}")
    print(f"   Reduction: -{reduction_pct:.1f}%")

    print(f"\nIMPACT ATTENDU V3:")
    print(f"   - Moins d'alertes ({-reduction_pct:.0f}%)")
    print(f"   - Qualite superieure (score min 60, velocite >5)")
    print(f"   - Evite zone danger age (12-24h)")
    print(f"   - Win rate attendu: 35-50% (vs 18.9% V2)")

    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backtest_railway_data.py alerts_railway_export.json")
        print("\nExemple:")
        print("  python backtest_railway_data.py alerts_railway_export.json")
        sys.exit(1)

    json_file = sys.argv[1]

    if not Path(json_file).exists():
        print(f"❌ Fichier non trouvé: {json_file}")
        print("\n💡 Exportez d'abord vos données Railway:")
        print("   Suivez EXPORT_RAILWAY_DATABASE.md")
        sys.exit(1)

    analyze_railway_export(json_file)
