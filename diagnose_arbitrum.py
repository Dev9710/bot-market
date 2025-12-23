"""
Diagnostic Arbitrum - Pourquoi aucune alerte ?
À exécuter avec: railway run python diagnose_arbitrum.py
"""
import requests
import time

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

print("=== DIAGNOSTIC ARBITRUM ===\n")

# Test 1: Vérifier si l'API retourne des pools Arbitrum
print("1. TEST API - Trending pools Arbitrum")
print("-" * 50)

try:
    url = f"{GECKOTERMINAL_API}/networks/arbitrum/trending_pools"
    response = requests.get(url, timeout=10)

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        pools = data.get('data', [])
        print(f"[OK] Pools retournes: {len(pools)}")

        if pools:
            print("\n📊 Top 5 pools Arbitrum:")
            for i, pool in enumerate(pools[:5], 1):
                attrs = pool.get('attributes', {})
                name = attrs.get('name', 'N/A')
                volume_24h = attrs.get('volume_usd', {}).get('h24', 0)
                liquidity = attrs.get('reserve_in_usd', 0)
                txns_24h = attrs.get('transactions', {}).get('h24', {})
                buys = txns_24h.get('buys', 0)
                sells = txns_24h.get('sells', 0)

                print(f"\n{i}. {name}")
                print(f"   Volume 24h: ${volume_24h:,.0f}")
                print(f"   Liquidité: ${liquidity:,.0f}")
                print(f"   Txns 24h: {buys + sells} (B:{buys} / S:{sells})")

                # Tester contre les seuils du bot
                MIN_LIQUIDITY = 100000
                MIN_VOLUME = 50000
                MIN_TXNS = 100

                passes = []
                if liquidity >= MIN_LIQUIDITY:
                    passes.append("✅ Liquidité OK")
                else:
                    passes.append(f"❌ Liquidité trop faible (min ${MIN_LIQUIDITY:,})")

                if volume_24h >= MIN_VOLUME:
                    passes.append("✅ Volume OK")
                else:
                    passes.append(f"❌ Volume trop faible (min ${MIN_VOLUME:,})")

                total_txns = buys + sells
                if total_txns >= MIN_TXNS:
                    passes.append("✅ Txns OK")
                else:
                    passes.append(f"❌ Txns trop faibles (min {MIN_TXNS})")

                print(f"   Filtres bot: {' | '.join(passes)}")
        else:
            print("❌ Aucun pool retourné par l'API")
    else:
        print(f"❌ Erreur API: {response.status_code}")
        print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ Erreur: {e}")

# Test 2: Vérifier les new pools
print("\n\n2. TEST API - New pools Arbitrum")
print("-" * 50)

try:
    url = f"{GECKOTERMINAL_API}/networks/arbitrum/new_pools"
    response = requests.get(url, timeout=10)

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        pools = data.get('data', [])
        print(f"✅ New pools retournés: {len(pools)}")

        if pools:
            print("\n📊 5 premiers new pools:")
            eligible_count = 0

            for pool in pools[:10]:
                attrs = pool.get('attributes', {})
                name = attrs.get('name', 'N/A')
                volume_24h = attrs.get('volume_usd', {}).get('h24', 0)
                liquidity = attrs.get('reserve_in_usd', 0)
                txns_24h = attrs.get('transactions', {}).get('h24', {})
                buys = txns_24h.get('buys', 0)
                sells = txns_24h.get('sells', 0)
                total_txns = buys + sells

                # Tester éligibilité
                MIN_LIQUIDITY = 100000
                MIN_VOLUME = 50000
                MIN_TXNS = 100

                eligible = (liquidity >= MIN_LIQUIDITY and
                           volume_24h >= MIN_VOLUME and
                           total_txns >= MIN_TXNS)

                if eligible:
                    eligible_count += 1
                    print(f"\n✅ ÉLIGIBLE: {name}")
                    print(f"   Volume: ${volume_24h:,.0f} | Liq: ${liquidity:,.0f} | Txns: {total_txns}")

            print(f"\n📊 Résumé: {eligible_count}/10 pools éligibles selon critères bot")

            if eligible_count == 0:
                print("\n⚠️ PROBLÈME IDENTIFIÉ: Aucun pool Arbitrum ne passe les filtres!")
                print("   Solutions possibles:")
                print("   - Réduire MIN_LIQUIDITY_USD (actuellement 100K)")
                print("   - Réduire MIN_VOLUME_24H_USD (actuellement 50K)")
                print("   - Réduire MIN_TXNS_24H (actuellement 100)")
    else:
        print(f"❌ Erreur API: {response.status_code}")

except Exception as e:
    print(f"❌ Erreur: {e}")

# Test 3: Comparer avec Solana (qui marche)
print("\n\n3. COMPARAISON - Solana vs Arbitrum")
print("-" * 50)

for network in ['solana', 'arbitrum']:
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/new_pools"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            pools = data.get('data', [])

            eligible = 0
            for pool in pools[:50]:
                attrs = pool.get('attributes', {})
                volume_24h = attrs.get('volume_usd', {}).get('h24', 0)
                liquidity = attrs.get('reserve_in_usd', 0)
                txns = attrs.get('transactions', {}).get('h24', {})
                total_txns = txns.get('buys', 0) + txns.get('sells', 0)

                if liquidity >= 100000 and volume_24h >= 50000 and total_txns >= 100:
                    eligible += 1

            print(f"{network.upper()}: {eligible}/50 pools éligibles")

        time.sleep(1)  # Rate limiting

    except Exception as e:
        print(f"{network.upper()}: Erreur - {e}")

print("\n=== FIN DIAGNOSTIC ===")
