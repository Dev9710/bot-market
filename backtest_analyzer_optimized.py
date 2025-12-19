"""
ANALYSEUR DE BACKTESTING OPTIMISE - Bot Market
Version haute performance avec parallelisation

Optimisations:
- Parallelisation des requetes API (10 threads)
- Rate limit reduit (0.5s au lieu de 2s)
- Sauvegarde incrementale tous les 100 tokens
- Reprise apres interruption
- Gestion robuste des erreurs

Temps: 26 min -> 2-3 min
"""

import csv
import requests
import time
from datetime import datetime
from typing import Dict, List
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# ============================================
# CONFIGURATION
# ============================================

CSV_PATH = "alerts_export_utf8.csv"
GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"
CACHE_FILE = "backtest_cache.json"
RESULTS_FILE = "backtest_results.json"

# Optimisations
MAX_WORKERS = 10  # Nombre de threads paralleles
RATE_LIMIT_DELAY = 0.5  # Delai entre requetes (secondes)
SAVE_INTERVAL = 100  # Sauvegarder tous les N tokens

# Seuils
PUMP_THRESHOLDS = {
    "petit": 5,
    "moyen": 15,
    "gros": 30,
    "moon": 100,
}

# ============================================
# UTILITAIRES
# ============================================

def log(msg: str):
    """Affiche un message avec timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_cache() -> Dict:
    """Charge le cache des resultats deja analyses."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache: Dict):
    """Sauvegarde le cache."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

# ============================================
# API CALLS
# ============================================

def get_token_price_history(network: str, pool_address: str) -> Dict:
    """Recupere l'historique des prix d'un token."""
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/pools/{pool_address}"
        headers = {"Accept": "application/json"}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            pool_data = data.get('data', {}).get('attributes', {})

            return {
                'current_price': float(pool_data.get('base_token_price_usd', 0)),
                'price_5m': float(pool_data.get('price_change_percentage', {}).get('m5', 0)),
                'price_1h': float(pool_data.get('price_change_percentage', {}).get('h1', 0)),
                'price_6h': float(pool_data.get('price_change_percentage', {}).get('h6', 0)),
                'price_24h': float(pool_data.get('price_change_percentage', {}).get('h24', 0)),
                'exists': True,
                'error': None
            }
        else:
            return {'exists': False, 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'exists': False, 'error': str(e)}

def process_single_alert(alert: Dict, alert_index: int) -> Dict:
    """Traite une seule alerte (fonction pour parallelisation)."""
    try:
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

        # Recuperer prix actuel
        price_data = get_token_price_history(alert['network'], alert['token_address'])

        # Calculer performance
        entry_price = alert['price_at_alert']
        current_price = price_data.get('current_price', 0)

        if entry_price > 0:
            perf_current = ((current_price - entry_price) / entry_price) * 100
        else:
            perf_current = 0

        # Enrichir l'alerte
        alert['current_price'] = current_price
        alert['exists'] = price_data.get('exists', False)
        alert['perf_current'] = perf_current
        alert['perf_5m'] = price_data.get('price_5m', 0)
        alert['perf_1h'] = price_data.get('price_1h', 0)
        alert['perf_6h'] = price_data.get('price_6h', 0)
        alert['perf_24h'] = price_data.get('price_24h', 0)
        alert['is_rugpull'] = not price_data.get('exists', True) or current_price < entry_price * 0.1
        alert['api_error'] = price_data.get('error')
        alert['processed'] = True

        return {'success': True, 'index': alert_index, 'alert': alert}

    except Exception as e:
        return {'success': False, 'index': alert_index, 'error': str(e), 'alert': alert}

# ============================================
# TRAITEMENT PARALLELE
# ============================================

def enrich_alerts_parallel(alerts: List[Dict], cache: Dict) -> List[Dict]:
    """Enrichit les alertes en parallele avec suivi de progression."""
    log(f"\nTraitement parallele de {len(alerts)} alertes...")
    log(f"Configuration: {MAX_WORKERS} threads, rate limit {RATE_LIMIT_DELAY}s")

    start_time = time.time()
    total_alerts = len(alerts)
    processed_count = 0
    enriched_alerts = [None] * total_alerts

    # Identifier les alertes deja en cache
    alerts_to_process = []
    for i, alert in enumerate(alerts):
        cache_key = f"alert_{alert['id']}"  # Cache par ID d'alerte, pas par token !
        if cache_key in cache:
            # Utiliser le cache
            enriched_alerts[i] = {**alert, **cache[cache_key]}
            processed_count += 1
        else:
            alerts_to_process.append((i, alert))

    if processed_count > 0:
        log(f"Cache: {processed_count} alertes deja analysees, {len(alerts_to_process)} restantes")

    # Traiter en parallele
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Soumettre toutes les taches
        futures = {
            executor.submit(process_single_alert, alert, idx): (idx, alert)
            for idx, alert in alerts_to_process
        }

        # Traiter les resultats au fur et a mesure
        for future in as_completed(futures):
            result = future.result()

            if result['success']:
                idx = result['index']
                enriched_alerts[idx] = result['alert']

                # Mettre en cache (par ID d'alerte, pas par token)
                cache_key = f"alert_{result['alert']['id']}"
                cache[cache_key] = {
                    'current_price': result['alert']['current_price'],
                    'perf_current': result['alert']['perf_current'],
                    'exists': result['alert']['exists'],
                    'is_rugpull': result['alert']['is_rugpull'],
                    'perf_5m': result['alert']['perf_5m'],
                    'perf_1h': result['alert']['perf_1h'],
                    'perf_6h': result['alert']['perf_6h'],
                    'perf_24h': result['alert']['perf_24h'],
                }
            else:
                # Erreur: garder l'alerte originale avec marqueur d'erreur
                idx = result['index']
                alert_failed = result['alert']
                alert_failed['processed'] = False
                alert_failed['api_error'] = result.get('error')
                enriched_alerts[idx] = alert_failed

            processed_count += 1

            # Afficher progression tous les 50 tokens
            if processed_count % 50 == 0 or processed_count == total_alerts:
                elapsed = time.time() - start_time
                progress_pct = (processed_count / total_alerts) * 100

                if processed_count < total_alerts:
                    avg_time = elapsed / processed_count
                    remaining = total_alerts - processed_count
                    est_remaining = avg_time * remaining
                    mins = int(est_remaining / 60)
                    secs = int(est_remaining % 60)
                    log(f"   Progression: {processed_count}/{total_alerts} ({progress_pct:.1f}%) - Temps restant: ~{mins}m {secs}s")
                else:
                    log(f"   Progression: {processed_count}/{total_alerts} ({progress_pct:.1f}%) - Termine !")

            # Sauvegarde incrementale
            if processed_count % SAVE_INTERVAL == 0:
                save_cache(cache)
                log(f"   Cache sauvegarde ({len(cache)} entrees)")

    # Sauvegarde finale
    save_cache(cache)

    elapsed_total = time.time() - start_time
    log(f"\nOK - Toutes les alertes traitees en {int(elapsed_total)}s ({elapsed_total/60:.1f} min)")
    log(f"Vitesse: {total_alerts/elapsed_total:.1f} alertes/sec")

    return enriched_alerts

# ============================================
# CALCUL DES METRIQUES
# ============================================

def calculate_metrics(alerts: List[Dict]) -> Dict:
    """Calcule toutes les metriques de rentabilite."""
    log("\nCalcul des metriques...")

    metrics = {
        'total_alerts': len(alerts),
        'valid_alerts': 0,
        'rugpulls': 0,
        'wins': 0,
        'losses': 0,
        'breakeven': 0,
        'avg_profit': 0,
        'median_profit': 0,
        'avg_loss': 0,
        'best_trade': 0,
        'worst_trade': 0,
        'risk_reward_ratio': 0,
        'total_roi': 0,
        'pumps_distribution': {},
        'network_stats': {},
        'score_stats': {},
        'timeframe_best': {},
    }

    # Filtrer alertes valides
    valid_alerts = [a for a in alerts if not a.get('is_rugpull', True)]
    metrics['valid_alerts'] = len(valid_alerts)
    metrics['rugpulls'] = len(alerts) - len(valid_alerts)

    if not valid_alerts:
        return metrics

    # Calculer wins/losses
    profits = []
    losses = []

    for alert in valid_alerts:
        perf = alert.get('perf_current', 0)
        if perf > 5:
            metrics['wins'] += 1
            profits.append(perf)
        elif perf < -5:
            metrics['losses'] += 1
            losses.append(perf)
        else:
            metrics['breakeven'] += 1

    metrics['win_rate'] = (metrics['wins'] / len(valid_alerts)) * 100

    if profits:
        metrics['avg_profit'] = sum(profits) / len(profits)
        metrics['median_profit'] = sorted(profits)[len(profits) // 2]
        metrics['best_trade'] = max(profits)

    if losses:
        metrics['avg_loss'] = sum(losses) / len(losses)
        metrics['worst_trade'] = min(losses)

    if metrics['avg_loss'] != 0:
        metrics['risk_reward_ratio'] = abs(metrics['avg_profit'] / metrics['avg_loss'])

    all_perfs = [a.get('perf_current', 0) for a in valid_alerts]
    metrics['total_roi'] = sum(all_perfs) / len(all_perfs) if all_perfs else 0

    # Distribution pumps
    for name, threshold in PUMP_THRESHOLDS.items():
        count = len([a for a in valid_alerts if a.get('perf_current', 0) >= threshold])
        metrics['pumps_distribution'][name] = {
            'count': count,
            'percentage': (count / len(valid_alerts)) * 100
        }

    # Stats par reseau
    networks = set(a['network'] for a in valid_alerts)
    for network in networks:
        net_alerts = [a for a in valid_alerts if a['network'] == network]
        net_wins = len([a for a in net_alerts if a.get('perf_current', 0) > 5])

        metrics['network_stats'][network] = {
            'count': len(net_alerts),
            'wins': net_wins,
            'win_rate': (net_wins / len(net_alerts)) * 100,
            'avg_roi': sum(a.get('perf_current', 0) for a in net_alerts) / len(net_alerts)
        }

    # Stats par score
    score_ranges = [(50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    for min_s, max_s in score_ranges:
        range_alerts = [a for a in valid_alerts if min_s <= a['score'] < max_s]
        if range_alerts:
            range_wins = len([a for a in range_alerts if a.get('perf_current', 0) > 5])
            metrics['score_stats'][f'{min_s}-{max_s}'] = {
                'count': len(range_alerts),
                'wins': range_wins,
                'win_rate': (range_wins / len(range_alerts)) * 100,
                'avg_roi': sum(a.get('perf_current', 0) for a in range_alerts) / len(range_alerts)
            }

    # Meilleur timeframe
    for tf in ['5m', '1h', '6h', '24h']:
        key = f'perf_{tf}'
        if valid_alerts and key in valid_alerts[0]:
            avg = sum(a.get(key, 0) for a in valid_alerts) / len(valid_alerts)
            metrics['timeframe_best'][tf] = avg

    return metrics

# ============================================
# RAPPORT
# ============================================

def generate_report(metrics: Dict, alerts: List[Dict]):
    """Genere le rapport complet."""

    print("\n" + "=" * 80)
    print("RAPPORT DE BACKTESTING - BOT MARKET")
    print("=" * 80)

    # Vue d'ensemble
    print("\nVUE D'ENSEMBLE")
    print("-" * 80)
    print(f"Total alertes            : {metrics['total_alerts']}")
    print(f"Alertes valides          : {metrics['valid_alerts']}")
    print(f"Rugpulls detectes        : {metrics['rugpulls']} ({metrics['rugpulls']/metrics['total_alerts']*100:.1f}%)")

    # Rentabilite
    print("\nRENTABILITE GLOBALE")
    print("-" * 80)
    print(f"Win Rate                 : {metrics['win_rate']:.1f}%")
    print(f"  Trades gagnants        : {metrics['wins']} ({metrics['wins']/metrics['valid_alerts']*100:.1f}%)")
    print(f"  Trades perdants        : {metrics['losses']} ({metrics['losses']/metrics['valid_alerts']*100:.1f}%)")
    print(f"  Breakeven              : {metrics['breakeven']} ({metrics['breakeven']/metrics['valid_alerts']*100:.1f}%)")
    print()
    print(f"Profit moyen (wins)      : +{metrics['avg_profit']:.1f}%")
    print(f"Profit median (wins)     : +{metrics['median_profit']:.1f}%")
    print(f"Perte moyenne (losses)   : {metrics['avg_loss']:.1f}%")
    print(f"Meilleur trade           : +{metrics['best_trade']:.1f}%")
    print(f"Pire trade               : {metrics['worst_trade']:.1f}%")
    print()
    print(f"Ratio Risk/Reward        : {metrics['risk_reward_ratio']:.2f}:1")
    print(f"ROI moyen par alerte     : {metrics['total_roi']:.1f}%")

    # Verdict
    print("\nVERDICT RENTABILITE:")
    if metrics['win_rate'] >= 60 and metrics['risk_reward_ratio'] >= 2:
        print("   EXCELLENT - Strategie tres rentable !")
    elif metrics['win_rate'] >= 50 and metrics['risk_reward_ratio'] >= 1.5:
        print("   BON - Strategie rentable, optimisations possibles")
    elif metrics['win_rate'] >= 40:
        print("   MOYEN - Rentabilite faible, optimisations necessaires")
    else:
        print("   FAIBLE - Strategie non rentable, revision complete requise")

    # Distribution pumps
    print("\nDISTRIBUTION DES PUMPS")
    print("-" * 80)
    for name, data in metrics['pumps_distribution'].items():
        bar = "=" * int(data['percentage'] / 2)
        print(f"{name.capitalize():10} (+{PUMP_THRESHOLDS[name]:3d}%+) : {bar} {data['count']} ({data['percentage']:.1f}%)")

    # Performance par reseau
    print("\nPERFORMANCE PAR RESEAU")
    print("-" * 80)
    for net, stats in sorted(metrics['network_stats'].items(), key=lambda x: x[1]['win_rate'], reverse=True):
        print(f"\n{net.upper()}:")
        print(f"  Alertes   : {stats['count']}")
        print(f"  Win Rate  : {stats['win_rate']:.1f}%")
        print(f"  ROI moyen : {stats['avg_roi']:.1f}%")

    # Performance par score
    print("\nPERFORMANCE PAR SCORE")
    print("-" * 80)
    for range_name, stats in sorted(metrics['score_stats'].items(), key=lambda x: int(x[0].split('-')[0])):
        print(f"\nScore {range_name}:")
        print(f"  Alertes   : {stats['count']}")
        print(f"  Win Rate  : {stats['win_rate']:.1f}%")
        print(f"  ROI moyen : {stats['avg_roi']:.1f}%")

    # Meilleur timeframe
    if metrics['timeframe_best']:
        print("\nPERFORMANCE PAR TIMEFRAME")
        print("-" * 80)
        for tf, perf in sorted(metrics['timeframe_best'].items(), key=lambda x: x[1], reverse=True):
            print(f"{tf:10} : {perf:+.1f}%")

        best_tf = max(metrics['timeframe_best'].items(), key=lambda x: x[1])
        print(f"\nMeilleur moment pour Take Profit: {best_tf[0]} ({best_tf[1]:+.1f}%)")

    # Top 10
    print("\nTOP 10 MEILLEURES ALERTES")
    print("-" * 80)
    valid = [a for a in alerts if not a.get('is_rugpull', True)]
    top10 = sorted(valid, key=lambda x: x.get('perf_current', 0), reverse=True)[:10]

    for i, alert in enumerate(top10, 1):
        print(f"{i:2}. {alert['token_name']:20} | {alert['network']:8} | Score: {alert['score']:3.0f} | Perf: +{alert.get('perf_current', 0):.1f}%")

    # Recommandations
    print("\nRECOMMANDATIONS")
    print("-" * 80)

    if metrics['score_stats']:
        best = max(metrics['score_stats'].items(), key=lambda x: x[1]['win_rate'])
        print(f"1. Score minimum optimal: {best[0].split('-')[0]} (Win Rate: {best[1]['win_rate']:.1f}%)")

    if metrics['network_stats']:
        best = max(metrics['network_stats'].items(), key=lambda x: x[1]['win_rate'])
        print(f"2. Reseau le plus rentable: {best[0].upper()} (Win Rate: {best[1]['win_rate']:.1f}%)")

    rugpull_rate = (metrics['rugpulls'] / metrics['total_alerts']) * 100
    if rugpull_rate > 20:
        print(f"3. Taux rugpull eleve ({rugpull_rate:.1f}%) - Reactiver LP Lock")
    else:
        print(f"3. Taux rugpull acceptable ({rugpull_rate:.1f}%)")

    if metrics['risk_reward_ratio'] < 1.5:
        print(f"4. Ratio R/R faible ({metrics['risk_reward_ratio']:.2f}) - Ajuster SL/TP")
    else:
        print(f"4. Ratio R/R satisfaisant ({metrics['risk_reward_ratio']:.2f})")

    print("\n" + "=" * 80)

# ============================================
# MAIN
# ============================================

def main():
    """Fonction principale optimisee."""

    print("\n" + "=" * 80)
    print("ANALYSEUR DE BACKTESTING OPTIMISE - BOT MARKET")
    print("=" * 80 + "\n")

    # Charger alertes
    log("Chargement des alertes...")
    alerts = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            alerts.append({
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
            })

    log(f"OK - {len(alerts)} alertes chargees")

    # Charger cache
    cache = load_cache()
    log(f"Cache charge: {len(cache)} entrees")

    # Enrichir avec prix actuels (parallele)
    enriched = enrich_alerts_parallel(alerts, cache)

    # Calculer metriques
    metrics = calculate_metrics(enriched)

    # Generer rapport
    generate_report(metrics, enriched)

    # Sauvegarder resultats
    results = {
        'generated_at': datetime.now().isoformat(),
        'metrics': metrics,
        'total_alerts': len(enriched),
        'valid_alerts': metrics['valid_alerts'],
        'top_10': sorted(
            [a for a in enriched if not a.get('is_rugpull', True)],
            key=lambda x: x.get('perf_current', 0),
            reverse=True
        )[:10]
    }

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log(f"\nResultats sauvegardes dans {RESULTS_FILE}")
    log("Analyse terminee !")

if __name__ == "__main__":
    main()
