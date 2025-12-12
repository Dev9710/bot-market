#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DexScreener Scanner - Detecte nouveaux tokens DEX (Ethereum, Polygon, Base, Solana)
Comme DONICA dans ton exemple: tokens crees recemment qui pump
"""

import sys
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Fix encodage pour emojis (Windows)
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (ValueError, AttributeError):
            pass

# Configuration
DEXSCREENER_BASE = "https://api.dexscreener.com/latest/dex"

# Cache
CACHE = {}
CACHE_DURATION = 300  # 5 minutes

def get_trending_tokens(chain: str = "ethereum", min_liquidity: float = 50000, max_age_hours: int = 48) -> List[Dict]:
    """
    Recupere les tokens NOUVEAUX et ACTIFS sur une blockchain.

    Args:
        chain: ethereum, polygon, base, arbitrum, solana, etc.
        min_liquidity: Liquidite minimum (evite rug pulls)
        max_age_hours: Age maximum du token en heures

    Returns:
        Liste de tokens avec metrics
    """
    cache_key = f"trending_{chain}"
    now = time.time()

    if cache_key in CACHE and (now - CACHE[cache_key]['time']) < CACHE_DURATION:
        return CACHE[cache_key]['data']

    # DexScreener - Top pairs par volume
    url = f"{DEXSCREENER_BASE}/tokens"

    try:
        # On va chercher les top gainers des dernieres 24h
        boosted_url = f"{DEXSCREENER_BASE}/search?q={chain}"

        # Alternative: Utiliser l'endpoint pairs
        pairs_url = f"{DEXSCREENER_BASE}/pairs/{chain}"

        # Pour l'instant utilisons un endpoint simple
        # DexScreener a des endpoints publics mais limites
        # On va utiliser leur endpoint "latest" qui donne les derniers pairs

        print(f"⚠️ DexScreener API necessite une approche differente...")
        print(f"Utilisons search par blockchain: {chain}")

        # Pour tester, simulons des donnees
        # En production, il faut utiliser leur vrai API
        tokens = []

        # TODO: Implementer vraie logique DexScreener
        # Pour l'instant retournons liste vide

        CACHE[cache_key] = {'data': tokens, 'time': now}
        return tokens

    except Exception as e:
        print(f"Erreur DexScreener: {e}")
        return []


def get_token_details(pair_address: str, chain: str = "ethereum") -> Optional[Dict]:
    """
    Recupere details complets d'un token via son adresse de pair.

    Returns:
        {
            'symbol': 'TOKEN',
            'name': 'Token Name',
            'price_usd': 0.0001,
            'volume_1h': 50000,
            'volume_24h': 1200000,
            'liquidity_usd': 350000,
            'price_change_1h': 45.2,
            'price_change_24h': 120.5,
            'transactions_1h': 450,
            'holders': 1200,  # Si disponible
            'age_hours': 3,
            'chain': 'ethereum'
        }
    """
    url = f"{DEXSCREENER_BASE}/pairs/{chain}/{pair_address}"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        if 'pair' not in data:
            return None

        pair = data['pair']

        # Extraire infos critiques
        token_details = {
            'symbol': pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
            'name': pair.get('baseToken', {}).get('name', 'Unknown Token'),
            'price_usd': float(pair.get('priceUsd', 0)),
            'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
            'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
            'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
            'transactions_24h': int(pair.get('txns', {}).get('h24', {}).get('buys', 0)) + int(pair.get('txns', {}).get('h24', {}).get('sells', 0)),
            'chain': chain,
            'pair_address': pair_address,
            'dex': pair.get('dexId', 'unknown')
        }

        return token_details

    except Exception as e:
        print(f"Erreur details token: {e}")
        return None


def detect_new_pumps(
    chains: List[str] = ["ethereum", "polygon", "base"],
    min_volume_1h: float = 100000,
    min_liquidity: float = 50000,
    min_price_change: float = 50.0,
    max_age_hours: int = 48
) -> List[Dict]:
    """
    Detecte nouveaux tokens qui pump comme DONICA.

    Criteres:
    - Token recent (< 48h)
    - Volume eleve (> $100K/h)
    - Liquidite safe (> $50K)
    - Prix monte fort (> +50%)

    Returns:
        Liste de tokens detectes
    """
    print(f"\n{'='*80}")
    print(f"🔍 DEXSCREENER SCAN - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")

    all_pumps = []

    for chain in chains:
        print(f"\n📊 Scan {chain}...")

        # NOTE: DexScreener API publique est limitee
        # Pour une implementation complete, il faudrait:
        # 1. Utiliser leur API payante
        # 2. Ou scraper leur site web
        # 3. Ou utiliser des endpoints alternatifs

        print(f"⚠️ DexScreener implementation requires paid API or alternative approach")
        print(f"   Free endpoints are very limited")

    print(f"\n✅ Scan termine: {len(all_pumps)} pumps detectes")

    return all_pumps


def generer_alerte_dex(token: Dict) -> str:
    """
    Genere alerte CONCISE pour nouveau token DEX.

    Format similaire a Binance mais adapte aux nouveaux tokens.
    """
    symbol = token.get('symbol', 'UNKNOWN')
    price = token.get('price_usd', 0)
    vol_24h = token.get('volume_24h', 0)
    liq = token.get('liquidity_usd', 0)
    pct_24h = token.get('price_change_24h', 0)
    age = token.get('age_hours', 0)
    chain = token.get('chain', 'unknown')
    txns = token.get('transactions_24h', 0)

    txt = f"\n🆕 *{symbol}* ({chain.upper()})\n"
    txt += f"💰 Prix: ${price:.8f}\n"
    txt += f"📊 Vol 24h: ${vol_24h/1000:.0f}K\n"
    txt += f"💧 Liquidite: ${liq/1000:.0f}K\n"
    txt += f"📈 +{pct_24h:.0f}% (24h)\n"
    txt += f"⏰ Age: {age:.0f}h\n"
    txt += f"🔄 Txns: {txns}\n"

    txt += f"\n🔍 *ANALYSE:*\n"

    if age < 6:
        txt += f"🆕 TOKEN TRES RECENT ({age:.0f}h)!\n"

    if pct_24h > 100:
        txt += f"🚀 PUMP MASSIF +{pct_24h:.0f}%!\n"

    if liq < 50000:
        txt += f"⚠️ FAIBLE LIQUIDITE - RISQUE RUG PULL!\n"
    elif liq > 500000:
        txt += f"✅ Liquidite safe (${liq/1000:.0f}K)\n"

    if txns > 1000:
        txt += f"🔥 FOMO! {txns} transactions\n"

    txt += f"\n⚡ *ACTION:*\n"

    if liq < 50000:
        txt += f"❌ NE PAS ACHETER - Risque rug pull!\n"
    elif pct_24h > 100 and age < 12:
        txt += f"⚠️ PUMP recent - Probable dump imminent\n❌ Trop risque pour entrer maintenant\n"
    elif pct_24h > 50 and liq > 200000:
        txt += f"👀 Surveiller de pres\n💰 Si stabil ise: acheter PETIT montant\n"
    else:
        txt += f"🔎 Token a surveiller\n"

    return txt


if __name__ == "__main__":
    print("="*80)
    print("🚀 DEXSCREENER SCANNER - Nouveaux Tokens DEX")
    print("="*80)
    print()
    print("⚠️ NOTE IMPORTANTE:")
    print("DexScreener API publique est tres limitee.")
    print("Pour implementation complete, il faut:")
    print("  1. API payante DexScreener")
    print("  2. Ou Defined.fi API (alternative gratuite)")
    print("  3. Ou GeckoTerminal API (CoinGecko pour DEX)")
    print()
    print("Pour l'instant, ce scanner est un TEMPLATE.")
    print("="*80)

    # Test avec donnees exemple (comme DONICA)
    test_token = {
        'symbol': 'DONICA',
        'name': 'Donica Token',
        'price_usd': 0.000120,
        'volume_24h': 2000000,
        'liquidity_usd': 500000,
        'price_change_24h': 395.5,
        'transactions_24h': 1200,
        'age_hours': 2,
        'chain': 'ethereum'
    }

    print("\n📊 EXEMPLE D'ALERTE (token comme DONICA):")
    alerte = generer_alerte_dex(test_token)
    print(alerte)
