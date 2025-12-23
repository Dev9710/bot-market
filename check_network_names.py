"""Verifier les noms de reseaux exacts dans pool_data"""
import requests
import time

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

print("=== VERIFICATION NOMS RESEAUX ===\n")

networks_to_test = ['arbitrum', 'solana', 'eth', 'bsc', 'base']

for network_id in networks_to_test:
    url = f"{GECKOTERMINAL_API}/networks/{network_id}/new_pools"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            pools = data.get('data', [])

            if pools:
                # Prendre le premier pool
                first_pool = pools[0]

                # Extraire le network ID
                relationships = first_pool.get('relationships', {})
                network_data = relationships.get('network', {}).get('data', {})
                network_type = network_data.get('type')
                network_returned_id = network_data.get('id')

                attrs = first_pool.get('attributes', {})
                pool_name = attrs.get('name', 'N/A')

                print(f"Reseau API: {network_id}")
                print(f"  Pool exemple: {pool_name}")
                print(f"  Network ID retourne: {network_returned_id}")
                print(f"  Network type: {network_type}")
                print()

        time.sleep(1)

    except Exception as e:
        print(f"Erreur {network_id}: {e}\n")

print("\n=== CONCLUSION ===")
print("Si network_returned_id differe de 'arbitrum', c'est le probleme!")
print("Le code devra utiliser le bon identifiant.")
