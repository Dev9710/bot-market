"""Test si les filtres Arbitrum fonctionnent"""

# Simuler les constantes
MIN_LIQUIDITY_USD = 100000
MIN_VOLUME_24H_USD = 50000
MIN_TXNS_24H = 100

ARBITRUM_THRESHOLDS = {
    'min_liquidity': 2000,
    'min_volume': 400,
    'min_txns': 10,
}

# Test avec pool Arbitrum fictif
pool_data_arb = {
    "network": "arbitrum",
    "liquidity": 5000,  # $5K - devrait passer avec seuils Arbitrum
    "volume_24h": 800,   # $800 - devrait passer
    "total_txns": 15,    # 15 txns - devrait passer
    "age_hours": 24
}

# Test avec pool Solana fictif
pool_data_sol = {
    "network": "solana",
    "liquidity": 5000,  # $5K - devrait ECHOUER avec seuils globaux
    "volume_24h": 800,
    "total_txns": 15,
    "age_hours": 24
}

def is_valid_opportunity(pool_data, score=50):
    """Version simplifiée de la fonction."""
    network = pool_data.get("network", "")

    if network == "arbitrum":
        min_liq = ARBITRUM_THRESHOLDS['min_liquidity']
        min_vol = ARBITRUM_THRESHOLDS['min_volume']
        min_txns = ARBITRUM_THRESHOLDS['min_txns']
    else:
        min_liq = MIN_LIQUIDITY_USD
        min_vol = MIN_VOLUME_24H_USD
        min_txns = MIN_TXNS_24H

    print(f"Reseau: {network}")
    print(f"Seuils appliques: Liq={min_liq}, Vol={min_vol}, Txns={min_txns}")
    print(f"Valeurs pool: Liq={pool_data['liquidity']}, Vol={pool_data['volume_24h']}, Txns={pool_data['total_txns']}")

    if pool_data["liquidity"] < min_liq:
        return False, f"Liquidite trop faible: ${pool_data['liquidity']:,.0f}"

    if pool_data["volume_24h"] < min_vol:
        return False, f"Volume trop faible: ${pool_data['volume_24h']:,.0f}"

    if pool_data["total_txns"] < min_txns:
        return False, f"Pas assez de txns: {pool_data['total_txns']}"

    return True, "OK"

print("=== TEST ARBITRUM ===")
valid, reason = is_valid_opportunity(pool_data_arb)
print(f"Resultat: {'VALIDE' if valid else 'REJETE'} - {reason}\n")

print("=== TEST SOLANA ===")
valid, reason = is_valid_opportunity(pool_data_sol)
print(f"Resultat: {'VALIDE' if valid else 'REJETE'} - {reason}\n")

print("Le filtre fonctionne correctement si:")
print("- Arbitrum est VALIDE")
print("- Solana est REJETE")
