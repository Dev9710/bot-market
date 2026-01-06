"""
Test complet d'un scan pour voir où reserve_in_usd est perdu
"""

import sys
sys.path.insert(0, '.')

from utils.api_client import get_trending_pools, get_new_pools, parse_pool_data

def test_full_scan():
    network = "eth"
    liquidity_stats = {}

    print("="*80)
    print("TEST: Scan complet ETH avec tracking liquidité")
    print("="*80)
    print()

    # Test trending pools
    print("1. TRENDING POOLS")
    print("-" * 80)
    trending = get_trending_pools(network)

    if trending:
        all_pools_data = []
        for i, pool in enumerate(trending[:5]):  # Premiers 5 seulement
            pool_data = parse_pool_data(pool, network, liquidity_stats)
            if pool_data:
                all_pools_data.append(pool_data)
                name = pool_data.get('name', 'N/A')
                liq = pool_data.get('liquidity', 0)
                print(f"  [{i+1}] {name[:40]:<40} | Liquidité: ${liq:,.2f}")

        print(f"\nTotal parsed: {len(all_pools_data)}")
    print()

    # Test new pools
    print("2. NEW POOLS")
    print("-" * 80)
    new_pools = get_new_pools(network)

    if new_pools:
        all_pools_data = []
        for i, pool in enumerate(new_pools[:10]):  # Premiers 10
            pool_data = parse_pool_data(pool, network, liquidity_stats)
            if pool_data:
                all_pools_data.append(pool_data)
                name = pool_data.get('name', 'N/A')
                liq = pool_data.get('liquidity', 0)
                print(f"  [{i+1}] {name[:40]:<40} | Liquidité: ${liq:,.2f}")

        print(f"\nTotal parsed: {len(all_pools_data)}")
    print()

    # Afficher les stats de liquidité
    print("3. STATISTIQUES DE LIQUIDITÉ")
    print("-" * 80)
    total = sum(liquidity_stats.values())
    print(f"Total pools: {total}")
    for source, count in sorted(liquidity_stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {source:<25} : {count:4d} pools ({pct:5.1f}%)")

    print()
    if liquidity_stats.get('reserve_in_usd', 0) == total:
        print("✅ EXCELLENT: 100% des pools ont reserve_in_usd!")
    elif liquidity_stats.get('reserve_in_usd', 0) >= total * 0.9:
        print("✅ BON: >90% des pools ont reserve_in_usd")
    else:
        print(f"⚠️ ATTENTION: Seulement {liquidity_stats.get('reserve_in_usd', 0)} / {total} pools avec reserve_in_usd")
        print()
        print("Cela peut être normal si:")
        print("- Les pools sont très récents (< 1 minute)")
        print("- L'API GeckoTerminal n'a pas encore les données")
        print("- Il y a un bug dans parse_pool_data()")

if __name__ == "__main__":
    test_full_scan()
