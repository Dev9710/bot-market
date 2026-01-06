"""
Script de diagnostic pour comprendre pourquoi reserve_in_usd est souvent manquant
"""

import requests
import json
from datetime import datetime

def test_api_endpoints():
    """Teste les 3 endpoints GeckoTerminal pour voir les différences"""

    base_url = "https://api.geckoterminal.com/api/v2"
    network = "eth"

    print("="*80)
    print("TEST: Comparaison des endpoints GeckoTerminal")
    print("="*80)
    print()

    # Test 1: Trending pools
    print("1. TRENDING POOLS")
    print("-" * 80)
    url_trending = f"{base_url}/networks/{network}/trending_pools"
    response = requests.get(url_trending, headers={"Accept": "application/json"}, timeout=15)

    if response.status_code == 200:
        data = response.json()
        pools = data.get("data", [])

        print(f"Total trending pools: {len(pools)}")

        # Analyser les 5 premiers
        has_reserve = 0
        missing_reserve = 0

        for i, pool in enumerate(pools[:5]):
            attrs = pool.get("attributes", {})
            name = attrs.get("name", "N/A")
            reserve = attrs.get("reserve_in_usd")
            fdv = attrs.get("fdv_usd")

            if reserve not in [None, "", "null"]:
                has_reserve += 1
                print(f"  [{i+1}] {name[:30]:<30} | reserve_in_usd: ${float(reserve):,.2f}")
            else:
                missing_reserve += 1
                print(f"  [{i+1}] {name[:30]:<30} | reserve_in_usd: MISSING (fdv: {fdv})")

        print(f"\nRésumé: {has_reserve} avec reserve_in_usd, {missing_reserve} sans")
    else:
        print(f"Erreur: {response.status_code}")

    print()

    # Test 2: New pools
    print("2. NEW POOLS")
    print("-" * 80)
    url_new = f"{base_url}/networks/{network}/new_pools"
    response = requests.get(url_new, headers={"Accept": "application/json"}, timeout=15)

    if response.status_code == 200:
        data = response.json()
        pools = data.get("data", [])

        print(f"Total new pools: {len(pools)}")

        # Analyser les 5 premiers
        has_reserve = 0
        missing_reserve = 0

        for i, pool in enumerate(pools[:5]):
            attrs = pool.get("attributes", {})
            name = attrs.get("name", "N/A")
            reserve = attrs.get("reserve_in_usd")
            fdv = attrs.get("fdv_usd")
            created = attrs.get("pool_created_at", "N/A")

            if reserve not in [None, "", "null"]:
                has_reserve += 1
                print(f"  [{i+1}] {name[:30]:<30} | reserve_in_usd: ${float(reserve):,.2f} | created: {created}")
            else:
                missing_reserve += 1
                print(f"  [{i+1}] {name[:30]:<30} | reserve_in_usd: MISSING (fdv: {fdv}) | created: {created}")

        print(f"\nRésumé: {has_reserve} avec reserve_in_usd, {missing_reserve} sans")
    else:
        print(f"Erreur: {response.status_code}")

    print()

    # Test 3: Pool spécifique par adresse
    print("3. POOL PAR ADRESSE (test avec un trending pool)")
    print("-" * 80)

    # Prendre l'adresse du premier trending pool
    response = requests.get(url_trending, headers={"Accept": "application/json"}, timeout=15)
    if response.status_code == 200:
        data = response.json()
        pools = data.get("data", [])
        if pools:
            first_pool = pools[0]
            pool_address = first_pool.get("attributes", {}).get("address")
            pool_name = first_pool.get("attributes", {}).get("name")

            url_specific = f"{base_url}/networks/{network}/pools/{pool_address}"
            response = requests.get(url_specific, headers={"Accept": "application/json"}, timeout=15)

            if response.status_code == 200:
                data = response.json()
                pool_data = data.get("data", {})
                attrs = pool_data.get("attributes", {})

                reserve = attrs.get("reserve_in_usd")
                fdv = attrs.get("fdv_usd")

                print(f"Pool: {pool_name}")
                print(f"Address: {pool_address}")
                if reserve not in [None, "", "null"]:
                    print(f"reserve_in_usd: ${float(reserve):,.2f}")
                else:
                    print(f"reserve_in_usd: MISSING (fdv: {fdv})")

                # Afficher tous les champs disponibles
                print(f"\nTous les champs disponibles dans attributes:")
                for key in sorted(attrs.keys()):
                    print(f"  - {key}")
            else:
                print(f"Erreur: {response.status_code}")

    print()
    print("="*80)
    print("CONCLUSION")
    print("="*80)
    print()
    print("Si reserve_in_usd est systématiquement MISSING pour certains pools:")
    print("1. C'est une limitation de l'API GeckoTerminal")
    print("2. Ces pools n'ont pas encore de données de liquidité disponibles")
    print("3. Il faut utiliser les fallbacks (FDV, Market Cap, Volume)")
    print()
    print("Si reserve_in_usd est présent partout:")
    print("1. Le problème vient du parsing dans notre code")
    print("2. Il faut vérifier la fonction parse_pool_data()")

if __name__ == "__main__":
    test_api_endpoints()
