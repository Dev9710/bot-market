#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Démonstration du nouveau format d'alerte sans lancer le bot."""

import sys
import io

# Fix encodage Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Exemple de données d'anomalies (simulées)
exemple_anomalies = [
    {
        "symbol": "BTC",
        "name": "Bitcoin",
        "coingecko_id": "bitcoin",
        "prix": 98765.432,
        "vol1m": 12345678,
        "ratio": 8.3,
        "mc": 1234567890000,
        "pct24": 5.67,
        "pct_from_low": 12.3,
        "h_l_ratio": 1.15
    },
    {
        "symbol": "USDT",
        "name": "Tether",
        "coingecko_id": "tether",
        "prix": 1.0005,
        "vol1m": 45678900,
        "ratio": 6.2,
        "mc": 98765432100,
        "pct24": 0.12,
        "pct_from_low": 0.3,
        "h_l_ratio": 1.01
    },
    {
        "symbol": "ETH",
        "name": "Ethereum",
        "coingecko_id": "ethereum",
        "prix": 3456.78,
        "vol1m": 8765432,
        "ratio": 7.1,
        "mc": 456789123000,
        "pct24": 3.45,
        "pct_from_low": 8.9,
        "h_l_ratio": 1.12
    }
]

# Simuler les infos de plateformes
exemple_platforms = {
    "bitcoin": {
        "exchanges": ["Binance", "Coinbase", "KuCoin"],
        "blockchains": []
    },
    "tether": {
        "exchanges": ["Binance", "KuCoin", "OKX"],
        "blockchains": ["Ethereum", "Tron", "Avalanche"]
    },
    "ethereum": {
        "exchanges": ["Binance", "Coinbase", "Kraken"],
        "blockchains": []
    }
}


def format_demo_alert(top):
    """Format l'alerte comme dans le vrai bot."""
    txt = "🌍 *Top activités crypto détectées*\n"
    txt += "_(Volume anormal — explications adaptées débutants)_\n\n"

    for i, t in enumerate(top, start=1):
        platforms = exemple_platforms.get(t['coingecko_id'], {"exchanges": [], "blockchains": []})

        # Formater les exchanges
        exchanges_txt = ""
        if platforms["exchanges"]:
            exchanges_list = ", ".join(platforms["exchanges"][:3])
            exchanges_txt = f"🏪 Exchanges : `{exchanges_list}`\n"

        # Formater les blockchains
        blockchains_txt = ""
        if platforms["blockchains"]:
            blockchains_list = ", ".join(platforms["blockchains"])
            blockchains_txt = f"⛓️ Blockchains : `{blockchains_list}`\n"
        elif not platforms["exchanges"]:
            blockchains_txt = f"⛓️ Natif (blockchain propre)\n"
        elif platforms["exchanges"] and not platforms["blockchains"]:
            blockchains_txt = f"⛓️ Natif (blockchain propre)\n"

        txt += (
            f"*#{i} — {t['symbol']} ({t['name']})*\n"
            f"💰 Prix : `{t['prix']:.6f} $`\n"
            f"📈 Volume 1m estimé : `{t['vol1m']:,.0f} $`\n"
            f"🔥 Multiplicateur : `x{t['ratio']:.1f}`\n"
            f"🏦 Market Cap : `{t['mc']:,.0f} $`\n"
            f"📊 Variation 24h : `{t['pct24']:.2f}%`\n"
            f"📉 Depuis le bas 24h : `{t['pct_from_low']:.1f}%`\n"
            f"🧱 Ratio Haut/Bas : `{t['h_l_ratio']:.2f}`\n"
            f"{exchanges_txt}"
            f"{blockchains_txt}"
            f"_→ Mouvement inhabituel détecté. Les traders s'intéressent à ce token._\n\n"
        )

    return txt


if __name__ == "__main__":
    print("=" * 80)
    print("📱 DÉMONSTRATION DU NOUVEAU FORMAT D'ALERTE TELEGRAM")
    print("=" * 80)
    print("\nCe message serait envoyé sur Telegram :\n")
    print("-" * 80)

    alerte = format_demo_alert(exemple_anomalies)
    print(alerte)

    print("-" * 80)
    print("\n✅ Nouvelles informations ajoutées :")
    print("   1. Nom complet du token : BTC (Bitcoin)")
    print("   2. Exchanges où il est listé : Binance, Coinbase, KuCoin")
    print("   3. Blockchains supportées : Ethereum, Tron, etc.")
    print("\n📊 Ces infos aident l'utilisateur à :")
    print("   - Identifier rapidement le token")
    print("   - Savoir où le trader")
    print("   - Comprendre s'il est multi-chain")
    print("\n" + "=" * 80)
