#!/usr/bin/env python3
"""
Analyse complete des statistiques Railway.
- Statistiques globales
- Winrate par blockchain
- Patterns gagnants (volume/liquidite)
- Recommandations d'amelioration
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Chemin vers le fichier export
EXPORT_FILE = Path(__file__).parent.parent / "alerts_railway_export.json"


def load_alerts():
    """Charge les alertes depuis le fichier JSON."""
    if not EXPORT_FILE.exists():
        print(f"ERREUR: Fichier non trouve: {EXPORT_FILE}")
        sys.exit(1)

    print(f"Chargement de {EXPORT_FILE}...")

    # Lire le fichier (peut etre en UTF-16)
    try:
        with open(EXPORT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(EXPORT_FILE, 'r', encoding='utf-16') as f:
            content = f.read()

    # Nettoyer le contenu si necessaire (enlever prefixe de log)
    if content.startswith('Connexion') or '\x00' in content:
        # Fichier UTF-16 avec espaces
        content = content.replace('\x00', '')
        # Trouver le debut du JSON
        json_start = content.find('{')
        if json_start > 0:
            content = content[json_start:]

    data = json.loads(content)
    return data.get('alerts', [])


def analyze_completeness(alerts):
    """Analyse la completude des alertes pour le backtest."""
    print("\n" + "=" * 60)
    print("ANALYSE DE COMPLETUDE DES ALERTES")
    print("=" * 60)

    total = len(alerts)

    # Compteurs
    with_price_after = 0
    with_max_price = 0
    with_result = 0
    complete_for_backtest = 0

    # Champs requis pour backtest
    required_fields = ['price_at_alert', 'price_1h_after', 'price_max_1h', 'network']

    for alert in alerts:
        if alert.get('price_1h_after') is not None:
            with_price_after += 1
        if alert.get('price_max_1h') is not None:
            with_max_price += 1
        if alert.get('result') is not None:
            with_result += 1

        # Verifier si complete pour backtest
        if all(alert.get(f) is not None for f in required_fields):
            complete_for_backtest += 1

    print(f"\nTotal alertes: {total:,}")
    print(f"Avec price_1h_after: {with_price_after:,} ({100*with_price_after/total:.1f}%)")
    print(f"Avec price_max_1h: {with_max_price:,} ({100*with_max_price/total:.1f}%)")
    print(f"Avec result: {with_result:,} ({100*with_result/total:.1f}%)")
    print(f"\nCompletes pour backtest: {complete_for_backtest:,} ({100*complete_for_backtest/total:.1f}%)")

    # Recommandation
    if complete_for_backtest >= 1000:
        print(f"\n[OK] Suffisant pour backtest fiable (>= 1000 alertes completes)")
    elif complete_for_backtest >= 500:
        print(f"\n[WARNING] Backtest possible mais limite (500-1000 alertes)")
    else:
        print(f"\n[ERROR] Insuffisant pour backtest fiable (< 500 alertes)")

    return complete_for_backtest


def analyze_winrate_by_network(alerts):
    """Analyse le winrate detaille par blockchain."""
    print("\n" + "=" * 60)
    print("ANALYSE WINRATE PAR BLOCKCHAIN")
    print("=" * 60)

    # Grouper par network
    by_network = defaultdict(list)
    for alert in alerts:
        network = alert.get('network', 'unknown')
        by_network[network].append(alert)

    results = {}

    for network, network_alerts in by_network.items():
        print(f"\n{'='*40}")
        print(f"BLOCKCHAIN: {network.upper()}")
        print(f"{'='*40}")

        total = len(network_alerts)

        # Alertes avec resultat
        with_result = [a for a in network_alerts if a.get('price_1h_after') is not None or a.get('result') is not None]

        if not with_result:
            print(f"Total: {total} | Avec resultat: 0 (pas de donnees)")
            continue

        # Calculer les wins (TP1 atteint = +5%)
        wins = 0
        losses = 0
        neutral = 0

        # Par tier/signal
        by_tier = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})

        for alert in with_result:
            price_at = alert.get('price_at_alert') or alert.get('entry_price')
            price_after = alert.get('price_1h_after')
            price_max = alert.get('price_max_1h')
            tier = alert.get('tier', 'UNKNOWN')
            signal = alert.get('signal_quality', tier)

            if not price_at:
                continue

            # Utiliser price_max si disponible, sinon price_after
            final_price = price_max or price_after
            if final_price is None:
                continue

            try:
                pct_change = (float(final_price) - float(price_at)) / float(price_at) * 100
            except (ValueError, ZeroDivisionError):
                continue

            by_tier[signal]['total'] += 1

            # Win si >= +5% (TP1)
            if pct_change >= 5:
                wins += 1
                by_tier[signal]['wins'] += 1
            elif pct_change <= -10:  # SL touche
                losses += 1
                by_tier[signal]['losses'] += 1
            else:
                neutral += 1

        total_decided = wins + losses
        winrate = (wins / total_decided * 100) if total_decided > 0 else 0

        print(f"Total: {total:,}")
        print(f"Avec resultat exploitable: {len(with_result):,}")
        print(f"Wins (>=+5%): {wins} | Losses (<=-10%): {losses} | Neutre: {neutral}")
        print(f"\nWINRATE GLOBAL: {winrate:.1f}%")

        # Par tier
        print(f"\nPar Signal/Tier:")
        for tier, stats in sorted(by_tier.items()):
            tier_total = stats['total']
            tier_wins = stats['wins']
            tier_losses = stats['losses']
            tier_decided = tier_wins + tier_losses
            tier_wr = (tier_wins / tier_decided * 100) if tier_decided > 0 else 0
            print(f"  {tier}: {tier_total} alertes | WR: {tier_wr:.1f}% ({tier_wins}W/{tier_losses}L)")

        results[network] = {
            'total': total,
            'with_result': len(with_result),
            'wins': wins,
            'losses': losses,
            'winrate': winrate,
            'by_tier': dict(by_tier)
        }

    return results


def find_winning_patterns(alerts):
    """Identifie les patterns gagnants par volume et liquidite."""
    print("\n" + "=" * 60)
    print("RECHERCHE DE PATTERNS GAGNANTS")
    print("=" * 60)

    # Filtrer alertes avec resultats
    valid_alerts = []
    for alert in alerts:
        price_at = alert.get('price_at_alert') or alert.get('entry_price')
        price_max = alert.get('price_max_1h') or alert.get('price_1h_after')

        if price_at and price_max:
            try:
                pct = (float(price_max) - float(price_at)) / float(price_at) * 100
                alert['_pct_change'] = pct
                alert['_is_win'] = pct >= 5
                valid_alerts.append(alert)
            except:
                pass

    if not valid_alerts:
        print("Pas assez de donnees valides")
        return

    # Par network
    for network in ['solana', 'eth']:
        network_alerts = [a for a in valid_alerts if a.get('network') == network]
        if not network_alerts:
            continue

        print(f"\n{'='*40}")
        print(f"{network.upper()} - PATTERNS GAGNANTS")
        print(f"{'='*40}")

        # Analyser par tranches de volume
        volume_ranges = [
            (0, 100_000, "0-100K"),
            (100_000, 500_000, "100K-500K"),
            (500_000, 1_000_000, "500K-1M"),
            (1_000_000, 5_000_000, "1M-5M"),
            (5_000_000, 10_000_000, "5M-10M"),
            (10_000_000, float('inf'), "10M+")
        ]

        print("\nPar VOLUME 24h:")
        for vmin, vmax, label in volume_ranges:
            subset = [a for a in network_alerts
                     if vmin <= (a.get('volume_24h') or 0) < vmax]
            if len(subset) >= 10:
                wins = sum(1 for a in subset if a['_is_win'])
                wr = wins / len(subset) * 100
                marker = " ***" if wr >= 70 else " **" if wr >= 60 else ""
                print(f"  {label}: {len(subset)} alertes | WR: {wr:.1f}%{marker}")

        # Analyser par tranches de liquidite
        liq_ranges = [
            (0, 50_000, "0-50K"),
            (50_000, 100_000, "50K-100K"),
            (100_000, 200_000, "100K-200K"),
            (200_000, 500_000, "200K-500K"),
            (500_000, 1_000_000, "500K-1M"),
            (1_000_000, float('inf'), "1M+")
        ]

        print("\nPar LIQUIDITE:")
        for lmin, lmax, label in liq_ranges:
            subset = [a for a in network_alerts
                     if lmin <= (a.get('liquidity') or 0) < lmax]
            if len(subset) >= 10:
                wins = sum(1 for a in subset if a['_is_win'])
                wr = wins / len(subset) * 100
                marker = " ***" if wr >= 70 else " **" if wr >= 60 else ""
                print(f"  {label}: {len(subset)} alertes | WR: {wr:.1f}%{marker}")

        # Zones combinees
        print("\nZONES OPTIMALES (Volume + Liquidite):")
        zones = [
            # (vol_min, vol_max, liq_min, liq_max, label)
            (1_000_000, 5_000_000, 0, 200_000, "Vol 1M-5M + Liq <200K"),
            (500_000, 2_000_000, 50_000, 150_000, "Vol 500K-2M + Liq 50K-150K"),
            (100_000, 1_000_000, 0, 100_000, "Vol 100K-1M + Liq <100K"),
            (0, 500_000, 0, 50_000, "Vol <500K + Liq <50K"),
        ]

        for vol_min, vol_max, liq_min, liq_max, label in zones:
            subset = [a for a in network_alerts
                     if vol_min <= (a.get('volume_24h') or 0) < vol_max
                     and liq_min <= (a.get('liquidity') or 0) < liq_max]
            if len(subset) >= 5:
                wins = sum(1 for a in subset if a['_is_win'])
                wr = wins / len(subset) * 100
                marker = " ***" if wr >= 75 else " **" if wr >= 65 else ""
                print(f"  {label}: {len(subset)} alertes | WR: {wr:.1f}%{marker}")

        # Par buy_ratio
        print("\nPar BUY RATIO:")
        ratio_ranges = [
            (0, 1.0, "<1.0 (vendeurs)"),
            (1.0, 1.2, "1.0-1.2 (equilibre)"),
            (1.2, 1.5, "1.2-1.5 (acheteurs)"),
            (1.5, 2.0, "1.5-2.0 (forte pression)"),
            (2.0, float('inf'), ">2.0 (tres forte)")
        ]

        for rmin, rmax, label in ratio_ranges:
            subset = [a for a in network_alerts
                     if rmin <= (a.get('buy_ratio') or 0) < rmax]
            if len(subset) >= 10:
                wins = sum(1 for a in subset if a['_is_win'])
                wr = wins / len(subset) * 100
                marker = " ***" if wr >= 70 else " **" if wr >= 60 else ""
                print(f"  {label}: {len(subset)} alertes | WR: {wr:.1f}%{marker}")

        # Par age
        print("\nPar AGE (heures):")
        age_ranges = [
            (0, 6, "0-6h (tres jeune)"),
            (6, 12, "6-12h"),
            (12, 24, "12-24h"),
            (24, 48, "24-48h"),
            (48, float('inf'), ">48h")
        ]

        for amin, amax, label in age_ranges:
            subset = [a for a in network_alerts
                     if amin <= (a.get('age_hours') or 0) < amax]
            if len(subset) >= 10:
                wins = sum(1 for a in subset if a['_is_win'])
                wr = wins / len(subset) * 100
                marker = " ***" if wr >= 70 else " **" if wr >= 60 else ""
                print(f"  {label}: {len(subset)} alertes | WR: {wr:.1f}%{marker}")


def analyze_by_score_and_tier(alerts):
    """Analyse par score et tier."""
    print("\n" + "=" * 60)
    print("ANALYSE PAR SCORE ET TIER")
    print("=" * 60)

    valid_alerts = []
    for alert in alerts:
        price_at = alert.get('price_at_alert') or alert.get('entry_price')
        price_max = alert.get('price_max_1h') or alert.get('price_1h_after')

        if price_at and price_max:
            try:
                pct = (float(price_max) - float(price_at)) / float(price_at) * 100
                alert['_pct_change'] = pct
                alert['_is_win'] = pct >= 5
                valid_alerts.append(alert)
            except:
                pass

    for network in ['solana', 'eth']:
        network_alerts = [a for a in valid_alerts if a.get('network') == network]
        if not network_alerts:
            continue

        print(f"\n{network.upper()}:")

        # Par score
        score_ranges = [
            (90, 101, "90-100"),
            (80, 90, "80-89"),
            (70, 80, "70-79"),
            (60, 70, "60-69"),
            (0, 60, "<60")
        ]

        print("  Par SCORE:")
        for smin, smax, label in score_ranges:
            subset = [a for a in network_alerts
                     if smin <= (a.get('score') or 0) < smax]
            if len(subset) >= 5:
                wins = sum(1 for a in subset if a['_is_win'])
                wr = wins / len(subset) * 100
                print(f"    Score {label}: {len(subset)} | WR: {wr:.1f}%")

        # Par tier actuel
        tiers = {}
        for alert in network_alerts:
            tier = alert.get('tier', 'UNKNOWN')
            if tier not in tiers:
                tiers[tier] = {'total': 0, 'wins': 0}
            tiers[tier]['total'] += 1
            if alert['_is_win']:
                tiers[tier]['wins'] += 1

        print("  Par TIER:")
        for tier, stats in sorted(tiers.items()):
            if stats['total'] >= 5:
                wr = stats['wins'] / stats['total'] * 100
                print(f"    {tier}: {stats['total']} | WR: {wr:.1f}%")


def main():
    print("=" * 60)
    print("ANALYSE COMPLETE BASE RAILWAY")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    alerts = load_alerts()
    print(f"\nTotal alertes chargees: {len(alerts):,}")

    # 1. Completude
    complete_count = analyze_completeness(alerts)

    # 2. Winrate par blockchain
    results = analyze_winrate_by_network(alerts)

    # 3. Patterns gagnants
    find_winning_patterns(alerts)

    # 4. Par score et tier
    analyze_by_score_and_tier(alerts)

    # Resume final
    print("\n" + "=" * 60)
    print("RESUME ET RECOMMANDATIONS")
    print("=" * 60)

    print("\nDonnees suffisantes pour backtest:", "OUI" if complete_count >= 500 else "NON")

    for network, data in results.items():
        wr = data.get('winrate', 0)
        status = "RENTABLE" if wr >= 50 else "A AMELIORER"
        print(f"\n{network.upper()}: WR {wr:.1f}% - {status}")


if __name__ == "__main__":
    main()