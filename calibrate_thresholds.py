"""
Calibration des seuils optimaux pour eviter spam tout en capturant opportunites
A executer avec: railway run python calibrate_thresholds.py
"""
import requests
import time
from collections import defaultdict

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

print("=== CALIBRATION DES SEUILS ===\n")
print("Analyse des 100 derniers new pools par reseau...\n")

# Reseaux a analyser
networks = ['solana', 'arbitrum', 'eth', 'bsc', 'base']

results = {}

for network in networks:
    print(f"Analyse {network.upper()}...")

    url = f"{GECKOTERMINAL_API}/networks/{network}/new_pools"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            pools = data.get('data', [])

            # Collecte des metriques
            liquidities = []
            volumes = []
            txns_counts = []

            for pool in pools[:100]:
                attrs = pool.get('attributes', {})

                liq = float(attrs.get('reserve_in_usd', 0) or 0)
                vol = float(attrs.get('volume_usd', {}).get('h24', 0) or 0)
                txns_24h = attrs.get('transactions', {}).get('h24', {})
                total_txns = txns_24h.get('buys', 0) + txns_24h.get('sells', 0)

                liquidities.append(liq)
                volumes.append(vol)
                txns_counts.append(total_txns)

            # Statistiques
            if liquidities:
                liquidities.sort(reverse=True)
                volumes.sort(reverse=True)
                txns_counts.sort(reverse=True)

                results[network] = {
                    'total_pools': len(liquidities),
                    'liq_top10': liquidities[9] if len(liquidities) > 9 else 0,
                    'liq_top20': liquidities[19] if len(liquidities) > 19 else 0,
                    'liq_top30': liquidities[29] if len(liquidities) > 29 else 0,
                    'vol_top10': volumes[9] if len(volumes) > 9 else 0,
                    'vol_top20': volumes[19] if len(volumes) > 19 else 0,
                    'vol_top30': volumes[29] if len(volumes) > 29 else 0,
                    'txn_top10': txns_counts[9] if len(txns_counts) > 9 else 0,
                    'txn_top20': txns_counts[19] if len(txns_counts) > 19 else 0,
                    'txn_top30': txns_counts[29] if len(txns_counts) > 29 else 0,
                }

                print(f"  OK - {len(liquidities)} pools analyses")
        else:
            print(f"  Erreur API: {response.status_code}")

        time.sleep(1)  # Rate limiting

    except Exception as e:
        print(f"  Erreur: {e}")

# Affichage des resultats
print("\n" + "="*80)
print("RESULTATS - Seuils pour capturer TOP 10/20/30 pools par reseau")
print("="*80)

print("\nLIQUIDITE (USD):")
print(f"{'Reseau':<12} {'Top 10':<15} {'Top 20':<15} {'Top 30':<15}")
print("-" * 60)
for network, data in results.items():
    print(f"{network.upper():<12} ${data['liq_top10']:>13,.0f} ${data['liq_top20']:>13,.0f} ${data['liq_top30']:>13,.0f}")

print("\nVOLUME 24H (USD):")
print(f"{'Reseau':<12} {'Top 10':<15} {'Top 20':<15} {'Top 30':<15}")
print("-" * 60)
for network, data in results.items():
    print(f"{network.upper():<12} ${data['vol_top10']:>13,.0f} ${data['vol_top20']:>13,.0f} ${data['vol_top30']:>13,.0f}")

print("\nTRANSACTIONS 24H:")
print(f"{'Reseau':<12} {'Top 10':<15} {'Top 20':<15} {'Top 30':<15}")
print("-" * 60)
for network, data in results.items():
    print(f"{network.upper():<12} {data['txn_top10']:>14,} {data['txn_top20']:>14,} {data['txn_top30']:>14,}")

# Recommandations
print("\n" + "="*80)
print("RECOMMANDATIONS")
print("="*80)

# Calculer moyennes pour Top 20 (equilibre qualite/quantite)
avg_liq_top20 = sum(d['liq_top20'] for d in results.values()) / len(results)
avg_vol_top20 = sum(d['vol_top20'] for d in results.values()) / len(results)
avg_txn_top20 = sum(d['txn_top20'] for d in results.values()) / len(results)

print("\nObjectif: Capturer TOP 20 pools par reseau (equilibre qualite/volume)")
print(f"\nSeuils suggeres (moyennes multi-reseaux):")
print(f"  MIN_LIQUIDITY_USD = {int(avg_liq_top20):,}  # ${int(avg_liq_top20):,}")
print(f"  MIN_VOLUME_24H_USD = {int(avg_vol_top20):,}  # ${int(avg_vol_top20):,}")
print(f"  MIN_TXNS_24H = {int(avg_txn_top20)}  # {int(avg_txn_top20)} transactions")

print(f"\nAlternative CONSERVATRICE (TOP 10 - moins d'alertes, meilleure qualite):")
avg_liq_top10 = sum(d['liq_top10'] for d in results.values()) / len(results)
avg_vol_top10 = sum(d['vol_top10'] for d in results.values()) / len(results)
avg_txn_top10 = sum(d['txn_top10'] for d in results.values()) / len(results)
print(f"  MIN_LIQUIDITY_USD = {int(avg_liq_top10):,}")
print(f"  MIN_VOLUME_24H_USD = {int(avg_vol_top10):,}")
print(f"  MIN_TXNS_24H = {int(avg_txn_top10)}")

print(f"\nAlternative AGGRESSIVE (TOP 30 - plus d'alertes, plus de bruit):")
avg_liq_top30 = sum(d['liq_top30'] for d in results.values()) / len(results)
avg_vol_top30 = sum(d['vol_top30'] for d in results.values()) / len(results)
avg_txn_top30 = sum(d['txn_top30'] for d in results.values()) / len(results)
print(f"  MIN_LIQUIDITY_USD = {int(avg_liq_top30):,}")
print(f"  MIN_VOLUME_24H_USD = {int(avg_vol_top30):,}")
print(f"  MIN_TXNS_24H = {int(avg_txn_top30)}")

# Estimation nombre d'alertes par jour
print("\n" + "="*80)
print("ESTIMATION ALERTES PAR JOUR (5 reseaux, scan toutes les 5 min = 288 scans/jour)")
print("="*80)
scan_per_day = 288  # 24h * 60min / 5min
pools_per_scan_top20 = 20 * len(networks)  # Top 20 par reseau
pools_per_scan_top10 = 10 * len(networks)
pools_per_scan_top30 = 30 * len(networks)

print(f"\nTOP 10 (conservateur): ~{pools_per_scan_top10 * 2} alertes/jour")
print(f"TOP 20 (equilibre):    ~{pools_per_scan_top20 * 2} alertes/jour")
print(f"TOP 30 (agressif):     ~{pools_per_scan_top30 * 2} alertes/jour")

print("\n=== FIN CALIBRATION ===")
