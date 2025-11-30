#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner Binance - Détection volume temps réel
Détecte les pumps sur tokens établis via volume 1min, liquidations, Open Interest
"""

import sys
import io
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional

# Fix encodage Windows (seulement si pas déjà fait)
if sys.platform == "win32" and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (ValueError, AttributeError):
        pass  # Déjà configuré

# Configuration
BINANCE_BASE = "https://api.binance.com"
BINANCE_FUTURES = "https://fapi.binance.com"

# Cache pour éviter spam API
CACHE = {}
CACHE_DURATION = 60  # 1 minute


def get_all_trading_pairs() -> List[str]:
    """Récupère tous les pairs USDT actifs sur Binance."""
    cache_key = "trading_pairs"
    now = time.time()

    if cache_key in CACHE and (now - CACHE[cache_key]['time']) < 300:  # 5 min cache
        return CACHE[cache_key]['data']

    url = f"{BINANCE_BASE}/api/v3/exchangeInfo"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        # Filtrer seulement les pairs USDT actifs
        pairs = []
        for s in data.get('symbols', []):
            if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT':
                # Exclure les leveraged tokens (UP, DOWN, BULL, BEAR)
                symbol = s['symbol']
                if not any(x in symbol for x in ['UP', 'DOWN', 'BULL', 'BEAR']):
                    pairs.append(symbol)

        CACHE[cache_key] = {'data': pairs, 'time': now}
        print(f"✅ {len(pairs)} pairs USDT récupérés")
        return pairs

    except Exception as e:
        print(f"❌ Erreur récupération pairs: {e}")
        return []


def get_klines_volume(symbol: str, interval: str = "1m", limit: int = 60) -> Dict:
    """
    Récupère les klines (chandelles) pour calculer le volume temps réel.

    Returns:
        {
            'current_1min_volume': Volume de la dernière minute (USD)
            'avg_1h_volume': Volume moyen par minute sur 1h (USD)
            'ratio': Ratio volume actuel / moyenne
            'price': Prix actuel
        }
    """
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        klines = r.json()

        if not isinstance(klines, list) or len(klines) < 2:
            return None

        # Structure kline: [timestamp, open, high, low, close, volume, ...]
        # Volume est en quantité de token, pas en USD

        # Dernière kline (minute actuelle, peut être incomplète)
        latest = klines[-1]
        close_price = float(latest[4])  # Prix de clôture
        latest_volume_token = float(latest[5])  # Volume en tokens
        latest_volume_usd = latest_volume_token * close_price

        # Calculer volume moyen sur les 60 dernières minutes (sauf la dernière incomplète)
        total_volume_usd = 0
        for kline in klines[:-1]:  # Exclure dernière kline incomplète
            volume_token = float(kline[5])
            close = float(kline[4])
            total_volume_usd += volume_token * close

        avg_volume_1min = total_volume_usd / len(klines[:-1]) if len(klines) > 1 else 1

        # Ratio
        ratio = latest_volume_usd / avg_volume_1min if avg_volume_1min > 0 else 0

        return {
            'symbol': symbol,
            'current_1min_volume': latest_volume_usd,
            'avg_1h_volume': avg_volume_1min,
            'ratio': ratio,
            'price': close_price,
            'timestamp': datetime.fromtimestamp(latest[0] / 1000)
        }

    except Exception as e:
        # print(f"⚠️ Erreur klines {symbol}: {e}")
        return None


def get_liquidations(symbol: str, limit: int = 100) -> Dict:
    """
    Récupère les liquidations récentes sur Binance Futures.

    Returns:
        {
            'total_liquidated_usd': Total liquidé (dernières 5 min)
            'long_liquidated': Longs liquidés
            'short_liquidated': Shorts liquidés
            'count': Nombre de liquidations
        }
    """
    url = f"{BINANCE_FUTURES}/fapi/v1/allForceOrders"
    params = {
        "symbol": symbol,
        "limit": limit
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        orders = r.json()

        if not isinstance(orders, list):
            return None

        # Filtrer liquidations des 5 dernières minutes
        now = time.time() * 1000  # ms
        five_min_ago = now - (5 * 60 * 1000)

        long_liq = 0
        short_liq = 0
        count = 0

        for order in orders:
            timestamp = order.get('time', 0)
            if timestamp < five_min_ago:
                continue

            qty = float(order.get('origQty', 0))
            price = float(order.get('price', 0))
            value = qty * price

            side = order.get('side')  # BUY ou SELL
            # Si side = SELL, c'est un long liquidé (forced sell)
            # Si side = BUY, c'est un short liquidé (forced buy)

            if side == 'SELL':
                long_liq += value
            else:
                short_liq += value

            count += 1

        total = long_liq + short_liq

        return {
            'symbol': symbol,
            'total_liquidated_usd': total,
            'long_liquidated': long_liq,
            'short_liquidated': short_liq,
            'count': count
        }

    except Exception as e:
        # Pas d'erreur si le token n'a pas de futures
        return None


def get_open_interest(symbol: str) -> Dict:
    """
    Récupère l'Open Interest sur Binance Futures.

    Returns:
        {
            'open_interest_usd': Open Interest en USD
            'timestamp': Timestamp
        }
    """
    url = f"{BINANCE_FUTURES}/fapi/v1/openInterest"
    params = {"symbol": symbol}

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        # Récupérer prix actuel pour convertir en USD
        price_url = f"{BINANCE_FUTURES}/fapi/v1/ticker/price"
        price_r = requests.get(price_url, params={"symbol": symbol}, timeout=10)
        price_data = price_r.json()
        price = float(price_data.get('price', 0))

        oi_amount = float(data.get('openInterest', 0))
        oi_usd = oi_amount * price

        return {
            'symbol': symbol,
            'open_interest_usd': oi_usd,
            'open_interest_amount': oi_amount,
            'timestamp': datetime.now()
        }

    except Exception as e:
        return None


def get_funding_rate(symbol: str) -> Optional[float]:
    """Récupère le funding rate actuel."""
    url = f"{BINANCE_FUTURES}/fapi/v1/premiumIndex"
    params = {"symbol": symbol}

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        funding_rate = float(data.get('lastFundingRate', 0))
        return funding_rate

    except Exception as e:
        return None


def scan_all_pairs(
    volume_threshold: float = 5.0,
    min_volume_usd: float = 10000,
    liquidation_threshold: float = 1000000,  # $1M
    max_pairs: int = 200  # Limiter pour vitesse
) -> List[Dict]:
    """
    Scanne tous les pairs Binance et retourne les anomalies détectées.

    Args:
        volume_threshold: Ratio minimum (ex: 5.0 = volume x5)
        min_volume_usd: Volume minimum en USD pour filtrer
        liquidation_threshold: Seuil de liquidations pour alerte
        max_pairs: Nombre maximum de pairs à scanner (top par volume)

    Returns:
        Liste de tokens avec anomalies détectées
    """
    print(f"\n{'='*80}")
    print(f"🔍 SCAN BINANCE - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")

    # Récupérer ticker 24h pour filtrer par volume
    ticker_url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
    try:
        r = requests.get(ticker_url, timeout=10)
        tickers = r.json()

        # Filtrer pairs USDT et trier par volume
        usdt_tickers = [
            t for t in tickers
            if t['symbol'].endswith('USDT') and float(t.get('quoteVolume', 0)) > 1000000  # >$1M vol 24h
        ]

        # Trier par volume décroissant
        usdt_tickers.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)

        # Prendre top N
        pairs = [t['symbol'] for t in usdt_tickers[:max_pairs]]

        print(f"✅ Top {len(pairs)} pairs par volume 24h sélectionnés")

    except Exception as e:
        print(f"❌ Erreur récupération tickers: {e}")
        return []

    print(f"📊 Analyse de {len(pairs)} pairs USDT...")

    anomalies = []
    scanned = 0

    for symbol in pairs:
        # Récupérer volume
        volume_data = get_klines_volume(symbol)

        if not volume_data:
            continue

        scanned += 1

        # Filtrer volume minimum
        if volume_data['current_1min_volume'] < min_volume_usd:
            continue

        # Détecter spike de volume
        if volume_data['ratio'] >= volume_threshold:

            # Récupérer métriques supplémentaires
            liquidations = get_liquidations(symbol)
            oi_data = get_open_interest(symbol)
            funding = get_funding_rate(symbol)

            anomaly = {
                'symbol': symbol.replace('USDT', ''),
                'volume_data': volume_data,
                'liquidations': liquidations,
                'open_interest': oi_data,
                'funding_rate': funding,
                'detection_time': datetime.now()
            }

            anomalies.append(anomaly)

            print(f"\n🚨 ANOMALIE DÉTECTÉE: {symbol}")
            print(f"   Volume 1min: ${volume_data['current_1min_volume']:,.0f}")
            print(f"   Ratio: {volume_data['ratio']:.1f}x")

            if liquidations and liquidations['total_liquidated_usd'] > 0:
                print(f"   Liquidations: ${liquidations['total_liquidated_usd']:,.0f}")

        # Petit délai pour éviter rate limit
        if scanned % 50 == 0:
            print(f"   ... {scanned}/{len(pairs)} pairs scannés")
            time.sleep(0.5)

    print(f"\n✅ Scan terminé: {scanned} pairs analysés, {len(anomalies)} anomalies détectées")

    return anomalies


if __name__ == "__main__":
    print("="*80)
    print("🚀 BINANCE SCANNER - Détection Volume Temps Réel")
    print("="*80)

    # Test avec paramètres plus permissifs pour voir des résultats
    anomalies = scan_all_pairs(
        volume_threshold=3.0,  # x3 pour tester
        min_volume_usd=50000,   # $50K minimum
        liquidation_threshold=500000,  # $500K
        max_pairs=100  # Top 100 pour test rapide
    )

    if anomalies:
        print(f"\n{'='*80}")
        print(f"📊 RÉSULTATS DÉTAILLÉS")
        print(f"{'='*80}\n")

        for a in anomalies:
            print(f"🔥 {a['symbol']}")
            print(f"   Prix: ${a['volume_data']['price']:,.4f}")
            print(f"   Volume 1min: ${a['volume_data']['current_1min_volume']:,.0f}")
            print(f"   Volume moyen 1h: ${a['volume_data']['avg_1h_volume']:,.0f}")
            print(f"   Ratio: {a['volume_data']['ratio']:.1f}x")

            if a['liquidations']:
                liq = a['liquidations']
                print(f"   Liquidations (5min): ${liq['total_liquidated_usd']:,.0f}")
                print(f"      Longs: ${liq['long_liquidated']:,.0f}")
                print(f"      Shorts: ${liq['short_liquidated']:,.0f}")

            if a['open_interest']:
                print(f"   Open Interest: ${a['open_interest']['open_interest_usd']:,.0f}")

            if a['funding_rate']:
                print(f"   Funding Rate: {a['funding_rate']*100:.4f}%")

            print()
    else:
        print("\n⚠️ Aucune anomalie détectée avec ces paramètres")
        print("\nCela signifie:")
        print("- Le marché est calme en ce moment")
        print("- Ou les seuils sont trop élevés")
        print("\nEssayez de réduire volume_threshold à 2.0 pour plus de résultats")
