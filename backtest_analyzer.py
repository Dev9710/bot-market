"""
 ANALYSEUR DE BACKTESTING - Bot Market
Analyse complte de la rentabilit et fiabilit des alertes

Mtriques calcules :
- Win Rate global et par catgorie
- ROI moyen, mdian, min, max
- Ratio Risk/Reward
- Performance par rseau, score, timeframe
- Identification des patterns gagnants
- Dtection des rugpulls et honeypots

Usage:
    python backtest_analyzer.py
"""

import csv
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from collections import defaultdict

# ============================================
# CONFIGURATION
# ============================================

CSV_PATH = "alerts_export_utf8.csv"  # Chemin vers le CSV tlcharg depuis Railway
GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

# Timeframes  analyser (en minutes)
TIMEFRAMES = {
    "5min": 5,
    "15min": 15,
    "30min": 30,
    "1h": 60,
    "2h": 120,
    "6h": 360,
    "12h": 720,
    "24h": 1440,
    "48h": 2880,
}

# Seuils de performance
PUMP_THRESHOLDS = {
    "petit": 5,      # +5%
    "moyen": 15,     # +15%
    "gros": 30,      # +30%
    "moon": 100,     # +100%
}

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def log(msg: str):
    """Affiche un message avec timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_token_price_history(network: str, pool_address: str) -> Dict:
    """
    Rcupre l'historique des prix d'un token via GeckoTerminal.

    Returns:
        Dict avec prices  diffrents timeframes
    """
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/pools/{pool_address}"
        headers = {"Accept": "application/json"}

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            pool_data = data.get('data', {}).get('attributes', {})

            return {
                'current_price': float(pool_data.get('base_token_price_usd', 0)),
                'price_5m': float(pool_data.get('price_change_percentage', {}).get('m5', 0)),
                'price_1h': float(pool_data.get('price_change_percentage', {}).get('h1', 0)),
                'price_6h': float(pool_data.get('price_change_percentage', {}).get('h6', 0)),
                'price_24h': float(pool_data.get('price_change_percentage', {}).get('h24', 0)),
                'volume_24h': float(pool_data.get('volume_usd', {}).get('h24', 0)),
                'liquidity': float(pool_data.get('reserve_in_usd', 0)),
                'exists': True
            }
        else:
            return {'exists': False, 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'exists': False, 'error': str(e)}

def calculate_performance(entry_price: float, current_price: float) -> float:
    """Calcule la performance en %."""
    if entry_price == 0:
        return 0
    return ((current_price - entry_price) / entry_price) * 100

# ============================================
# ANALYSE DE LA BASE DE DONNES
# ============================================

def load_alerts_from_csv(csv_path: str) -> List[Dict]:
    """Charge toutes les alertes depuis le CSV."""
    log(f"Chargement des alertes depuis {csv_path}...")

    try:
        alerts = []

        with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig pour enlever le BOM
            reader = csv.DictReader(f)

            for row in reader:
                # Convertir les types
                alert = {
                    'id': int(row['id']),
                    'token_name': row['token_name'],
                    'token_address': row['token_address'],
                    'network': row['network'],
                    'price_at_alert': float(row['price_at_alert']),
                    'score': float(row['score']),
                    'base_score': float(row['base_score']),
                    'momentum_bonus': float(row['momentum_bonus']),
                    'confidence_score': float(row['confidence_score']),
                    'volume_24h': float(row['volume_24h']),
                    'volume_6h': float(row['volume_6h']),
                    'volume_1h': float(row['volume_1h']),
                    'liquidity': float(row['liquidity']),
                    'buys_24h': int(row['buys_24h']),
                    'sells_24h': int(row['sells_24h']),
                    'buy_ratio': float(row['buy_ratio']),
                    'total_txns': int(row['total_txns']),
                    'age_hours': float(row['age_hours']),
                    'created_at': row['created_at']
                }
                alerts.append(alert)

        log(f"OK - {len(alerts)} alertes chargees")
        return alerts

    except Exception as e:
        log(f"ERREUR chargement CSV: {e}")
        return []

def enrich_alerts_with_current_prices(alerts: List[Dict]) -> List[Dict]:
    """
    Enrichit chaque alerte avec les prix actuels et calcule les performances.
    """
    log(f"\n Rcupration des prix actuels pour {len(alerts)} alertes...")
    log("  Cela peut prendre quelques minutes (rate limit API)...")

    enriched_alerts = []
    start_time = time.time()
    total_alerts = len(alerts)

    for i, alert in enumerate(alerts):
        # Afficher progression tous les 50 tokens
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = time.time() - start_time
            progress_pct = ((i + 1) / total_alerts) * 100

            # Estimer temps restant
            if i > 0:
                avg_time_per_alert = elapsed / (i + 1)
                remaining_alerts = total_alerts - (i + 1)
                estimated_remaining = avg_time_per_alert * remaining_alerts

                # Formater temps restant
                remaining_mins = int(estimated_remaining / 60)
                remaining_secs = int(estimated_remaining % 60)

                log(f"   Progression: {i + 1}/{total_alerts} ({progress_pct:.1f}%) - Temps restant: ~{remaining_mins}m {remaining_secs}s")
            else:
                log(f"   Progression: {i + 1}/{total_alerts} ({progress_pct:.1f}%)")

        # Rcuprer les donnes actuelles du token
        price_data = get_token_price_history(alert['network'], alert['token_address'])

        # Calculer les performances
        alert['current_price'] = price_data.get('current_price', 0)
        alert['exists'] = price_data.get('exists', False)
        alert['perf_current'] = calculate_performance(alert['price_at_alert'], alert['current_price'])

        # Estimer les performances  diffrents timeframes bas sur les % de changement
        alert['perf_5m'] = price_data.get('price_5m', 0)
        alert['perf_1h'] = price_data.get('price_1h', 0)
        alert['perf_6h'] = price_data.get('price_6h', 0)
        alert['perf_24h'] = price_data.get('price_24h', 0)

        # Vrifier si le token existe encore (pas de rugpull)
        alert['is_rugpull'] = not price_data.get('exists', True) or alert['current_price'] < alert['price_at_alert'] * 0.1

        enriched_alerts.append(alert)

        # Rate limit: 1 requte toutes les 2 secondes
        time.sleep(2)

    log(f" Toutes les alertes enrichies avec les prix actuels\n")
    return enriched_alerts

# ============================================
# CALCUL DES MTRIQUES DE RENTABILIT
# ============================================

def calculate_profitability_metrics(alerts: List[Dict]) -> Dict:
    """
    Calcule toutes les mtriques de rentabilit.

    Returns:
        Dict avec toutes les mtriques cls
    """
    log(" Calcul des mtriques de rentabilit...\n")

    metrics = {
        'total_alerts': len(alerts),
        'valid_alerts': 0,
        'rugpulls': 0,
        'wins': 0,
        'losses': 0,
        'breakeven': 0,
        'win_rate': 0,
        'avg_profit': 0,
        'avg_loss': 0,
        'median_profit': 0,
        'best_trade': 0,
        'worst_trade': 0,
        'risk_reward_ratio': 0,
        'total_roi': 0,
        'timeframe_best': {},
        'network_stats': {},
        'score_stats': {},
        'pumps_distribution': {},
    }

    # Filtrer les alertes valides (token existe encore)
    valid_alerts = [a for a in alerts if not a['is_rugpull']]
    metrics['valid_alerts'] = len(valid_alerts)
    metrics['rugpulls'] = len(alerts) - len(valid_alerts)

    if not valid_alerts:
        log("  Aucune alerte valide trouve")
        return metrics

    # Calculer wins/losses (bas sur performance actuelle)
    profits = []
    losses = []

    for alert in valid_alerts:
        perf = alert['perf_current']

        if perf > 5:  # Gain > 5%
            metrics['wins'] += 1
            profits.append(perf)
        elif perf < -5:  # Perte > 5%
            metrics['losses'] += 1
            losses.append(perf)
        else:  # Entre -5% et +5%
            metrics['breakeven'] += 1

    # Win Rate
    metrics['win_rate'] = (metrics['wins'] / len(valid_alerts)) * 100 if valid_alerts else 0

    # Profits moyens et mdians
    if profits:
        metrics['avg_profit'] = sum(profits) / len(profits)
        metrics['median_profit'] = sorted(profits)[len(profits) // 2]
        metrics['best_trade'] = max(profits)

    if losses:
        metrics['avg_loss'] = sum(losses) / len(losses)
        metrics['worst_trade'] = min(losses)

    # Risk/Reward Ratio
    if metrics['avg_loss'] != 0:
        metrics['risk_reward_ratio'] = abs(metrics['avg_profit'] / metrics['avg_loss'])

    # ROI total (simulation)
    all_perfs = [a['perf_current'] for a in valid_alerts]
    metrics['total_roi'] = sum(all_perfs) / len(all_perfs) if all_perfs else 0

    # Distribution des pumps
    for threshold_name, threshold_value in PUMP_THRESHOLDS.items():
        count = len([a for a in valid_alerts if a['perf_current'] >= threshold_value])
        metrics['pumps_distribution'][threshold_name] = {
            'count': count,
            'percentage': (count / len(valid_alerts)) * 100
        }

    # Stats par rseau
    networks = set(a['network'] for a in valid_alerts)
    for network in networks:
        network_alerts = [a for a in valid_alerts if a['network'] == network]
        network_wins = len([a for a in network_alerts if a['perf_current'] > 5])

        metrics['network_stats'][network] = {
            'count': len(network_alerts),
            'wins': network_wins,
            'win_rate': (network_wins / len(network_alerts)) * 100 if network_alerts else 0,
            'avg_roi': sum(a['perf_current'] for a in network_alerts) / len(network_alerts)
        }

    # Stats par tranche de score
    score_ranges = [(50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    for min_score, max_score in score_ranges:
        range_alerts = [a for a in valid_alerts if min_score <= a['score'] < max_score]
        if range_alerts:
            range_wins = len([a for a in range_alerts if a['perf_current'] > 5])

            metrics['score_stats'][f'{min_score}-{max_score}'] = {
                'count': len(range_alerts),
                'wins': range_wins,
                'win_rate': (range_wins / len(range_alerts)) * 100,
                'avg_roi': sum(a['perf_current'] for a in range_alerts) / len(range_alerts)
            }

    # Meilleur timeframe pour TP
    for tf_name, tf_minutes in TIMEFRAMES.items():
        if tf_name in ['5min', '1h', '6h', '24h']:  # On a ces donnes de l'API
            perf_key = f'perf_{tf_name.replace("min", "m").replace("h", "h")}'
            if perf_key in valid_alerts[0]:
                avg_perf = sum(a.get(perf_key, 0) for a in valid_alerts) / len(valid_alerts)
                metrics['timeframe_best'][tf_name] = avg_perf

    return metrics

# ============================================
# GNRATION DU RAPPORT
# ============================================

def generate_report(metrics: Dict, alerts: List[Dict]):
    """Gnre un rapport dtaill et visuel."""

    print("\n" + "=" * 80)
    print(" RAPPORT DE BACKTESTING - BOT MARKET")
    print("=" * 80)

    # Section 1: Vue d'ensemble
    print("\n VUE D'ENSEMBLE")
    print("-" * 80)
    print(f"Total alertes collectes    : {metrics['total_alerts']}")
    print(f"Alertes valides             : {metrics['valid_alerts']}")
    print(f"Rugpulls dtects           : {metrics['rugpulls']} ({(metrics['rugpulls']/metrics['total_alerts']*100):.1f}%)")

    # Section 2: Rentabilit
    print("\n RENTABILIT GLOBALE")
    print("-" * 80)
    print(f"Win Rate                    : {metrics['win_rate']:.1f}%")
    print(f"   Trades gagnants        : {metrics['wins']} ({(metrics['wins']/metrics['valid_alerts']*100):.1f}%)")
    print(f"   Trades perdants        : {metrics['losses']} ({(metrics['losses']/metrics['valid_alerts']*100):.1f}%)")
    print(f"   Breakeven              : {metrics['breakeven']} ({(metrics['breakeven']/metrics['valid_alerts']*100):.1f}%)")
    print()
    print(f"Profit moyen (wins)         : +{metrics['avg_profit']:.1f}%")
    print(f"Profit mdian (wins)        : +{metrics['median_profit']:.1f}%")
    print(f"Perte moyenne (losses)      : {metrics['avg_loss']:.1f}%")
    print(f"Meilleur trade              : +{metrics['best_trade']:.1f}%")
    print(f"Pire trade                  : {metrics['worst_trade']:.1f}%")
    print()
    print(f"Ratio Risk/Reward           : {metrics['risk_reward_ratio']:.2f}:1")
    print(f"ROI moyen par alerte        : {metrics['total_roi']:.1f}%")

    # Verdict rentabilit
    print("\n VERDICT RENTABILIT:")
    if metrics['win_rate'] >= 60 and metrics['risk_reward_ratio'] >= 2:
        print("    EXCELLENT - Stratgie trs rentable !")
    elif metrics['win_rate'] >= 50 and metrics['risk_reward_ratio'] >= 1.5:
        print("    BON - Stratgie rentable, optimisations possibles")
    elif metrics['win_rate'] >= 40:
        print("     MOYEN - Rentabilit faible, optimisations ncessaires")
    else:
        print("    FAIBLE - Stratgie non rentable, rvision complte requise")

    # Section 3: Distribution des Pumps
    print("\n DISTRIBUTION DES PUMPS")
    print("-" * 80)
    for pump_name, pump_data in metrics['pumps_distribution'].items():
        bar = "" * int(pump_data['percentage'] / 2)
        print(f"{pump_name.capitalize():10} (+{PUMP_THRESHOLDS[pump_name]}%+) : {bar} {pump_data['count']} ({pump_data['percentage']:.1f}%)")

    # Section 4: Performance par Rseau
    print("\n PERFORMANCE PAR RSEAU")
    print("-" * 80)
    for network, stats in sorted(metrics['network_stats'].items(), key=lambda x: x[1]['win_rate'], reverse=True):
        print(f"\n{network.upper()}:")
        print(f"  Alertes          : {stats['count']}")
        print(f"  Win Rate         : {stats['win_rate']:.1f}%")
        print(f"  ROI moyen        : {stats['avg_roi']:.1f}%")

    # Section 5: Performance par Score
    print("\n PERFORMANCE PAR SCORE")
    print("-" * 80)
    for score_range, stats in sorted(metrics['score_stats'].items(), key=lambda x: int(x[0].split('-')[0])):
        print(f"\nScore {score_range}:")
        print(f"  Alertes          : {stats['count']}")
        print(f"  Win Rate         : {stats['win_rate']:.1f}%")
        print(f"  ROI moyen        : {stats['avg_roi']:.1f}%")

    # Section 6: Meilleur Timeframe pour TP
    if metrics['timeframe_best']:
        print("\n PERFORMANCE PAR TIMEFRAME")
        print("-" * 80)
        for tf, perf in sorted(metrics['timeframe_best'].items(), key=lambda x: x[1], reverse=True):
            print(f"{tf:10} : {perf:+.1f}%")

        best_tf = max(metrics['timeframe_best'].items(), key=lambda x: x[1])
        print(f"\n Meilleur moment pour Take Profit: {best_tf[0]} ({best_tf[1]:+.1f}%)")

    # Section 7: Top 10 Meilleures Alertes
    print("\n TOP 10 MEILLEURES ALERTES")
    print("-" * 80)
    valid_alerts = [a for a in alerts if not a['is_rugpull']]
    top_alerts = sorted(valid_alerts, key=lambda x: x['perf_current'], reverse=True)[:10]

    for i, alert in enumerate(top_alerts, 1):
        print(f"{i:2}. {alert['token_name']:20} | {alert['network']:8} | Score: {alert['score']:3.0f} | Performance: +{alert['perf_current']:.1f}%")

    # Section 8: Recommandations
    print("\n RECOMMANDATIONS D'OPTIMISATION")
    print("-" * 80)

    # Recommandation 1: Score minimum
    if metrics['score_stats']:
        best_score_range = max(metrics['score_stats'].items(), key=lambda x: x[1]['win_rate'])
        print(f"1. Score minimum optimal : {best_score_range[0].split('-')[0]} (Win Rate: {best_score_range[1]['win_rate']:.1f}%)")

    # Recommandation 2: Rseau
    if metrics['network_stats']:
        best_network = max(metrics['network_stats'].items(), key=lambda x: x[1]['win_rate'])
        print(f"2. Rseau le plus rentable : {best_network[0].upper()} (Win Rate: {best_network[1]['win_rate']:.1f}%)")

    # Recommandation 3: Rugpulls
    rugpull_rate = (metrics['rugpulls'] / metrics['total_alerts']) * 100
    if rugpull_rate > 20:
        print(f"3.   Taux de rugpull lev ({rugpull_rate:.1f}%)  Ractiver LP Lock check")
    else:
        print(f"3.  Taux de rugpull acceptable ({rugpull_rate:.1f}%)")

    # Recommandation 4: Risk/Reward
    if metrics['risk_reward_ratio'] < 1.5:
        print(f"4.   Ratio R/R faible ({metrics['risk_reward_ratio']:.2f})  Ajuster Stop Loss et Take Profit")
    else:
        print(f"4.  Ratio R/R satisfaisant ({metrics['risk_reward_ratio']:.2f})")

    print("\n" + "=" * 80)
    print(" Rapport gnr avec succs !")
    print("=" * 80 + "\n")

# ============================================
# SAUVEGARDE DES RSULTATS
# ============================================

def save_results_to_json(alerts: List[Dict], metrics: Dict, filename: str = "backtest_results.json"):
    """Sauvegarde tous les rsultats dans un fichier JSON."""

    results = {
        'generated_at': datetime.now().isoformat(),
        'metrics': metrics,
        'alerts_summary': {
            'total': len(alerts),
            'valid': metrics['valid_alerts'],
            'rugpulls': metrics['rugpulls']
        },
        'top_10_alerts': sorted(
            [a for a in alerts if not a['is_rugpull']],
            key=lambda x: x['perf_current'],
            reverse=True
        )[:10]
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log(f" Rsultats sauvegards dans {filename}")

# ============================================
# MAIN
# ============================================

def main():
    """Fonction principale."""

    print("\n" + "=" * 80)
    print("ANALYSEUR DE BACKTESTING - BOT MARKET")
    print("=" * 80 + "\n")

    # tape 1: Charger les alertes
    alerts = load_alerts_from_csv(CSV_PATH)

    if not alerts:
        log("ERREUR - Aucune alerte trouvee. Verifiez que le fichier CSV existe.")
        return

    # tape 2: Enrichir avec les prix actuels
    alerts = enrich_alerts_with_current_prices(alerts)

    # tape 3: Calculer les mtriques
    metrics = calculate_profitability_metrics(alerts)

    # tape 4: Gnrer le rapport
    generate_report(metrics, alerts)

    # tape 5: Sauvegarder les rsultats
    save_results_to_json(alerts, metrics)

    log("\nOK - Analyse terminee !")

if __name__ == "__main__":
    main()
