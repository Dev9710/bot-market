"""Diagnostic Arbitrum - Version simple sans emojis"""
import requests
import time

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

print("=== DIAGNOSTIC ARBITRUM ===\n")
print("1. TEST - Trending pools Arbitrum\n")

# Test trending pools
url = f"{GECKOTERMINAL_API}/networks/arbitrum/trending_pools"
response = requests.get(url, timeout=10)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    pools = data.get('data', [])
    print(f"Pools retournes: {len(pools)}\n")

    if pools:
        print("Top 5 pools Arbitrum:")
        for i, pool in enumerate(pools[:5], 1):
            attrs = pool.get('attributes', {})
            name = attrs.get('name', 'N/A')
            volume_24h = float(attrs.get('volume_usd', {}).get('h24', 0) or 0)
            liquidity = float(attrs.get('reserve_in_usd', 0) or 0)
            txns_24h = attrs.get('transactions', {}).get('h24', {})
            buys = txns_24h.get('buys', 0)
            sells = txns_24h.get('sells', 0)

            print(f"\n{i}. {name}")
            print(f"   Volume 24h: ${volume_24h:,.0f}")
            print(f"   Liquidite: ${liquidity:,.0f}")
            print(f"   Txns: {buys + sells} (B:{buys} S:{sells})")

            # Criteres bot
            MIN_LIQ = 100000
            MIN_VOL = 50000
            MIN_TXN = 100

            liq_ok = "OK" if liquidity >= MIN_LIQ else f"FAIL (min ${MIN_LIQ:,})"
            vol_ok = "OK" if volume_24h >= MIN_VOL else f"FAIL (min ${MIN_VOL:,})"
            txn_ok = "OK" if (buys + sells) >= MIN_TXN else f"FAIL (min {MIN_TXN})"

            print(f"   Filtres: Liq[{liq_ok}] Vol[{vol_ok}] Txn[{txn_ok}]")

# Test new pools
print("\n\n2. TEST - New pools Arbitrum\n")

url = f"{GECKOTERMINAL_API}/networks/arbitrum/new_pools"
response = requests.get(url, timeout=10)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    pools = data.get('data', [])
    print(f"New pools: {len(pools)}\n")

    eligible = 0
    for pool in pools[:20]:
        attrs = pool.get('attributes', {})
        name = attrs.get('name', 'N/A')
        volume_24h = float(attrs.get('volume_usd', {}).get('h24', 0) or 0)
        liquidity = float(attrs.get('reserve_in_usd', 0) or 0)
        txns_24h = attrs.get('transactions', {}).get('h24', {})
        buys = txns_24h.get('buys', 0)
        sells = txns_24h.get('sells', 0)
        total_txns = buys + sells

        if liquidity >= 100000 and volume_24h >= 50000 and total_txns >= 100:
            eligible += 1
            print(f"[ELIGIBLE] {name}")
            print(f"  Vol:${volume_24h:,.0f} Liq:${liquidity:,.0f} Txns:{total_txns}\n")

    print(f"Resultat: {eligible}/20 pools eligibles\n")

    if eligible == 0:
        print("PROBLEME: Aucun pool Arbitrum eligible!")
        print("Les criteres sont trop stricts pour Arbitrum")

# Comparaison Solana vs Arbitrum
print("\n3. COMPARAISON Solana vs Arbitrum (top 50 new pools)\n")

for network in ['solana', 'arbitrum']:
    url = f"{GECKOTERMINAL_API}/networks/{network}/new_pools"
    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        data = response.json()
        pools = data.get('data', [])

        eligible = 0
        for pool in pools[:50]:
            attrs = pool.get('attributes', {})
            volume_24h = float(attrs.get('volume_usd', {}).get('h24', 0) or 0)
            liquidity = float(attrs.get('reserve_in_usd', 0) or 0)
            txns = attrs.get('transactions', {}).get('h24', {})
            total_txns = txns.get('buys', 0) + txns.get('sells', 0)

            if liquidity >= 100000 and volume_24h >= 50000 and total_txns >= 100:
                eligible += 1

        print(f"{network.upper()}: {eligible}/50 pools eligibles")

    time.sleep(1)

print("\n=== FIN DIAGNOSTIC ===")
