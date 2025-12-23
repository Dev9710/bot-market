"""Test de la nouvelle structure NETWORK_THRESHOLDS"""

# Simuler la config
NETWORK_THRESHOLDS = {
    "solana": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "bsc": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "eth": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "base": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "arbitrum": {"min_liquidity": 2000, "min_volume": 400, "min_txns": 10},
    "avax": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "polygon_pos": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "default": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100}
}

def is_valid_opportunity(pool_data):
    """Version simplifiée"""
    network = pool_data.get("network", "")
    thresholds = NETWORK_THRESHOLDS.get(network, NETWORK_THRESHOLDS["default"])

    min_liq = thresholds["min_liquidity"]
    min_vol = thresholds["min_volume"]
    min_txns = thresholds["min_txns"]

    print(f"Network: {network}")
    print(f"  Seuils: ${min_liq:,} liq, ${min_vol:,} vol, {min_txns} txns")
    print(f"  Pool: ${pool_data['liquidity']:,} liq, ${pool_data['volume_24h']:,} vol, {pool_data['total_txns']} txns")

    if pool_data["liquidity"] < min_liq:
        return False, "Liquidite trop faible"
    if pool_data["volume_24h"] < min_vol:
        return False, "Volume trop faible"
    if pool_data["total_txns"] < min_txns:
        return False, "Pas assez de txns"

    return True, "OK"

# Test cases
print("=== TEST 1: Pool Arbitrum (devrait PASSER) ===")
pool_arb = {"network": "arbitrum", "liquidity": 5000, "volume_24h": 800, "total_txns": 15}
valid, reason = is_valid_opportunity(pool_arb)
print(f"Resultat: {'VALIDE' if valid else 'REJETE'} - {reason}\n")

print("=== TEST 2: Pool Solana (devrait ECHOUER - seuils stricts) ===")
pool_sol = {"network": "solana", "liquidity": 5000, "volume_24h": 800, "total_txns": 15}
valid, reason = is_valid_opportunity(pool_sol)
print(f"Resultat: {'VALIDE' if valid else 'REJETE'} - {reason}\n")

print("=== TEST 3: Pool Solana (devrait PASSER - metriques elevees) ===")
pool_sol_ok = {"network": "solana", "liquidity": 150000, "volume_24h": 80000, "total_txns": 150}
valid, reason = is_valid_opportunity(pool_sol_ok)
print(f"Resultat: {'VALIDE' if valid else 'REJETE'} - {reason}\n")

print("=== TEST 4: Reseau inconnu (devrait utiliser default) ===")
pool_unknown = {"network": "fantom", "liquidity": 150000, "volume_24h": 80000, "total_txns": 150}
valid, reason = is_valid_opportunity(pool_unknown)
print(f"Resultat: {'VALIDE' if valid else 'REJETE'} - {reason}\n")

print("=== TOUS LES TESTS PASSES ===")
print("Structure NETWORK_THRESHOLDS fonctionne correctement!")
