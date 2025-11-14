#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de la fonction get_token_platforms pour vérifier les infos de listing."""

import sys
import io
import requests

# Fix encodage Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

def get_token_platforms(coingecko_id):
    """Récupère les plateformes (exchanges + blockchains) depuis CoinGecko."""
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/{coingecko_id}",
            params={"localization": "false", "tickers": "true", "community_data": "false", "developer_data": "false"},
            timeout=10
        )
        data = r.json()

        # Récupérer les exchanges (top 5)
        exchanges = []
        if "tickers" in data and isinstance(data["tickers"], list):
            seen_exchanges = set()
            for ticker in data["tickers"][:20]:
                exchange_name = ticker.get("market", {}).get("name", "")
                if exchange_name and exchange_name not in seen_exchanges:
                    seen_exchanges.add(exchange_name)
                    exchanges.append(exchange_name)
                if len(exchanges) >= 5:
                    break

        # Récupérer les blockchains
        blockchains = []
        if "platforms" in data and isinstance(data["platforms"], dict):
            for platform_key in data["platforms"].keys():
                platform_name = platform_key.replace("-", " ").title()
                blockchains.append(platform_name)

        return {
            "exchanges": exchanges[:5],
            "blockchains": blockchains[:3],
            "name": data.get("name", "Unknown")
        }
    except Exception as e:
        print(f"Erreur: {e}")
        return {"exchanges": [], "blockchains": [], "name": "Unknown"}


if __name__ == "__main__":
    # Test sur quelques tokens populaires
    test_tokens = [
        ("bitcoin", "BTC"),
        ("ethereum", "ETH"),
        ("ripple", "XRP"),
        ("tether", "USDT"),
        ("uniswap", "UNI"),
        ("chainlink", "LINK"),
    ]

    print("🧪 Test des informations de listing\n")
    print("=" * 80)

    for token_id, symbol in test_tokens:
        print(f"\n📊 {symbol} ({token_id})")
        print("-" * 80)

        platforms = get_token_platforms(token_id)

        print(f"Nom complet : {platforms['name']}")

        if platforms["exchanges"]:
            print(f"🏪 Exchanges   : {', '.join(platforms['exchanges'][:3])}")
        else:
            print(f"🏪 Exchanges   : Aucun détecté")

        if platforms["blockchains"]:
            print(f"⛓️  Blockchains : {', '.join(platforms['blockchains'])}")
        else:
            print(f"⛓️  Blockchains : Natif (blockchain propre)")

    print("\n" + "=" * 80)
    print("✅ Test terminé !")
