# -*- coding: utf-8 -*-
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)

print("TEST LP LOCK - Version Simple")
print("="*60)

# Import et test
import requests
import time

def test_goplus_api(token_address, network):
    """Test direct de l'API GoPlusLabs"""
    chain_id_map = {
        'eth': '1',
        'bsc': '56',
    }

    chain_id = chain_id_map.get(network)
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}"
    params = {'contract_addresses': token_address.lower()}

    print(f"\nTest: {token_address[:10]}... sur {network}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            token_data = data.get('result', {}).get(token_address.lower(), {})

            if token_data:
                lp_holders = token_data.get('lp_holders', [])
                print(f"LP Holders trouvés: {len(lp_holders)}")

                for holder in lp_holders[:3]:  # Afficher les 3 premiers
                    print(f"  - Address: {holder.get('address', 'N/A')[:10]}...")
                    print(f"    Percent: {float(holder.get('percent', 0)) * 100:.2f}%")
                    print(f"    Is Locked: {holder.get('is_locked', '0')}")
            else:
                print("Aucune donnée token trouvée")
        else:
            print(f"Erreur API: {response.status_code}")
    except Exception as e:
        print(f"Erreur: {e}")

# Tests
print("\n" + "="*60)
print("Test 1: PEPE (ETH)")
print("="*60)
test_goplus_api("0x6982508145454Ce325dDbE47a25d4ec3d2311933", "eth")

time.sleep(2)

print("\n" + "="*60)
print("Test 2: CAKE (BSC)")
print("="*60)
test_goplus_api("0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "bsc")

print("\n" + "="*60)
print("TESTS TERMINES")
print("="*60)