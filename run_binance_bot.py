#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanceur principal du bot Binance - Sans problèmes d'encodage
Version simplifiée tout-en-un
"""

import os
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# =========================
# CONFIGURATION
# =========================

load_dotenv()

BINANCE_BASE = "https://api.binance.com"
BINANCE_FUTURES = "https://fapi.binance.com"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

STATE_FILE = "monitor_state_binance.json"
CONFIG_FILE = "config_binance.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("binance-bot")

# Cache
CACHE = {}

# =========================
# FONCTIONS UTILITAIRES
# =========================

def charger_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def secondes_depuis(iso):
    try:
        return (datetime.utcnow() - datetime.fromisoformat(iso)).total_seconds()
    except:
        return 10**9

def tg(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram non configure")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        logger.info("Alerte Telegram envoyee")
    except Exception as e:
        logger.error(f"Erreur Telegram: {e}")

# =========================
# API BINANCE
# =========================

def get_top_pairs(max_pairs=150):
    """Recupere top pairs par volume 24h."""
    ticker_url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
    try:
        r = requests.get(ticker_url, timeout=10)
        r.raise_for_status()
        tickers = r.json()

        # Verifier que c'est bien une liste
        if not isinstance(tickers, list):
            logger.error(f"Reponse API invalide: {tickers}")
            return []

        usdt_tickers = [
            t for t in tickers
            if isinstance(t, dict) and t.get('symbol', '').endswith('USDT') and float(t.get('quoteVolume', 0)) > 1000000
        ]

        usdt_tickers.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        return [t['symbol'] for t in usdt_tickers[:max_pairs]]
    except Exception as e:
        logger.error(f"Erreur recuperation pairs: {e}")
        return []

def get_klines_volume(symbol):
    """Recupere volume 1min reel avec variations de prix + momentum."""
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": "1m", "limit": 60}

    try:
        r = requests.get(url, params=params, timeout=10)
        klines = r.json()

        if not isinstance(klines, list) or len(klines) < 4:
            return None

        latest = klines[-1]
        close_price = float(latest[4])
        open_price = float(latest[1])
        latest_volume_token = float(latest[5])
        latest_volume_usd = latest_volume_token * close_price

        # Prix il y a 1h (pour variation 1h)
        hour_ago_price = float(klines[0][4])
        price_change_1h = ((close_price - hour_ago_price) / hour_ago_price * 100) if hour_ago_price > 0 else 0

        # Nombre de trades (approximation via nombre de klines avec volume)
        trades_count = sum(1 for k in klines if float(k[5]) > 0)

        total_volume_usd = 0
        for kline in klines[:-1]:
            volume_token = float(kline[5])
            close = float(kline[4])
            total_volume_usd += volume_token * close

        avg_volume_1min = total_volume_usd / len(klines[:-1]) if len(klines) > 1 else 1
        ratio = latest_volume_usd / avg_volume_1min if avg_volume_1min > 0 else 0

        # Variation du volume
        volume_change_pct = ((latest_volume_usd - avg_volume_1min) / avg_volume_1min * 100) if avg_volume_1min > 0 else 0

        # MOMENTUM DETECTION: Comparer t-0, t-1, t-2 pour voir si accelere/decelere
        # t-0 = derniere minute (latest)
        # t-1 = avant-derniere minute
        # t-2 = 2 minutes avant
        vol_t0 = latest_volume_usd

        if len(klines) >= 2:
            kline_t1 = klines[-2]
            vol_t1 = float(kline_t1[5]) * float(kline_t1[4])
        else:
            vol_t1 = 0

        if len(klines) >= 3:
            kline_t2 = klines[-3]
            vol_t2 = float(kline_t2[5]) * float(kline_t2[4])
        else:
            vol_t2 = 0

        # Calculer le momentum
        momentum = "neutre"
        if vol_t0 > vol_t1 and vol_t1 > vol_t2 and vol_t2 > 0:
            momentum = "acceleration"  # Volume augmente progressivement = BON SIGNE
        elif vol_t0 < vol_t1 and vol_t1 < vol_t2:
            momentum = "deceleration"  # Volume diminue = SIGNAL FAIBLIT
        elif vol_t0 > vol_t1 and vol_t1 < vol_t2:
            momentum = "reprise"  # Volume remonte apres baisse = POSSIBLE REBOND

        return {
            'symbol': symbol,
            'current_1min_volume': latest_volume_usd,
            'avg_1h_volume': avg_volume_1min,
            'ratio': ratio,
            'price': close_price,
            'price_change_1h': price_change_1h,
            'volume_change_pct': volume_change_pct,
            'trades_count_1h': trades_count,
            'momentum': momentum,
            'vol_t0': vol_t0,
            'vol_t1': vol_t1,
            'vol_t2': vol_t2
        }
    except:
        return None

def get_liquidations(symbol):
    """Recupere liquidations 5min."""
    url = f"{BINANCE_FUTURES}/fapi/v1/allForceOrders"
    params = {"symbol": symbol, "limit": 100}

    try:
        r = requests.get(url, params=params, timeout=10)
        orders = r.json()

        if not isinstance(orders, list):
            return None

        now = time.time() * 1000
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

            if order.get('side') == 'SELL':
                long_liq += value
            else:
                short_liq += value
            count += 1

        return {
            'total_liquidated_usd': long_liq + short_liq,
            'long_liquidated': long_liq,
            'short_liquidated': short_liq,
            'count': count
        }
    except:
        return None

def get_open_interest(symbol):
    """Recupere Open Interest."""
    try:
        r = requests.get(f"{BINANCE_FUTURES}/fapi/v1/openInterest", params={"symbol": symbol}, timeout=10)
        data = r.json()

        price_r = requests.get(f"{BINANCE_FUTURES}/fapi/v1/ticker/price", params={"symbol": symbol}, timeout=10)
        price = float(price_r.json().get('price', 0))

        oi_amount = float(data.get('openInterest', 0))
        return {'open_interest_usd': oi_amount * price}
    except:
        return None

def get_token_info(symbol):
    """Recupere info token (nom complet)."""
    # Dict statique des noms complets (peut etre etendu)
    token_names = {
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'BNB': 'Binance Coin',
        'SOL': 'Solana',
        'XRP': 'Ripple',
        'ADA': 'Cardano',
        'DOGE': 'Dogecoin',
        'AVAX': 'Avalanche',
        'SHIB': 'Shiba Inu',
        'DOT': 'Polkadot',
        'MATIC': 'Polygon',
        'LTC': 'Litecoin',
        'BCH': 'Bitcoin Cash',
        'UNI': 'Uniswap',
        'LINK': 'Chainlink',
        'XLM': 'Stellar',
        'ATOM': 'Cosmos',
        'FIL': 'Filecoin',
        'ENA': 'Ethena',
        'DASH': 'Dash',
        'XMR': 'Monero',
        'ZEC': 'Zcash',
        'AIXBT': 'AIXBT',
        'FDUSD': 'First Digital USD'
    }

    # Essayer de recuperer depuis API Binance
    try:
        r = requests.get(f"{BINANCE_BASE}/api/v3/exchangeInfo", timeout=10)
        data = r.json()
        for s in data.get('symbols', []):
            if s['symbol'] == symbol:
                base = s['baseAsset']
                return token_names.get(base, base)
    except:
        pass

    # Fallback sur dict statique
    base_symbol = symbol.replace('USDT', '')
    return token_names.get(base_symbol, base_symbol)

# =========================
# SCORE DE CONFIANCE
# =========================

def calculer_score_confiance(anomaly):
    """
    Calcule un score de confiance 0-100 pour evaluer la qualite du signal.
    Score eleve = signal fiable, forte probabilite de profit.
    """
    v = anomaly['volume_data']
    liq = anomaly.get('liquidations')
    oi = anomaly.get('open_interest')

    score = 0
    details = []

    # 1. VOLUME SPIKE (30 points max)
    ratio = v['ratio']
    volume_change = v.get('volume_change_pct', 0)

    if ratio >= 10 and volume_change >= 300:
        score += 30
        details.append("Volume exceptionnel (x10+)")
    elif ratio >= 7 and volume_change >= 200:
        score += 25
        details.append("Volume tres fort (x7+)")
    elif ratio >= 5 and volume_change >= 100:
        score += 20
        details.append("Volume fort (x5+)")
    elif ratio >= 3:
        score += 12
        details.append("Volume correct (x3+)")

    # 2. MOMENTUM VOLUME (15 points max)
    momentum = v.get('momentum', 'neutre')

    if momentum == "acceleration":
        score += 15
        details.append("Acceleration volume (t-2 < t-1 < t-0)")
    elif momentum == "reprise":
        score += 8
        details.append("Reprise apres baisse")
    elif momentum == "deceleration":
        score -= 10
        details.append("Volume decelere (mauvais signe)")

    # 3. MOMENTUM PRIX (20 points max)
    price_change = v.get('price_change_1h', 0)

    if price_change > 5 and volume_change > 200:
        score += 20
        details.append("Prix + Volume synchronises")
    elif price_change > 3 and volume_change > 100:
        score += 15
        details.append("Bon momentum")
    elif price_change > 1:
        score += 10
        details.append("Momentum positif")
    elif price_change < -2:
        score -= 10
        details.append("Prix baisse malgre volume")

    # 4. LIQUIDATIONS (25 points max)
    if liq and liq['total_liquidated_usd'] > 0:
        total_liq = liq['total_liquidated_usd']
        short_liq = liq['short_liquidated']
        long_liq = liq['long_liquidated']

        if short_liq > long_liq * 3 and total_liq > 1_000_000:
            score += 25
            details.append("Short Squeeze massif!")
        elif short_liq > long_liq * 2 and total_liq > 500_000:
            score += 18
            details.append("Short Squeeze confirme")
        elif long_liq > short_liq * 3:
            score -= 15
            details.append("Long Squeeze (baisse)")

    # 5. VOLUME ABSOLU (20 points max)
    vol_1min = v['current_1min_volume']

    if vol_1min >= 500_000:
        score += 20
        details.append("Gros volume absolu")
    elif vol_1min >= 200_000:
        score += 15
        details.append("Volume solide")
    elif vol_1min >= 100_000:
        score += 10
        details.append("Volume correct")

    # Limiter entre 0 et 100
    score = max(0, min(100, score))

    return score, details

# =========================
# ANALYSE PEDAGOGIQUE
# =========================

def generer_analyse(anomaly):
    """Genere analyse PEDAGOGIQUE avec emojis."""
    v = anomaly['volume_data']
    liq = anomaly.get('liquidations')
    oi = anomaly.get('open_interest')

    symbol = anomaly['symbol']
    full_symbol = symbol + 'USDT'  # Pour API calls
    token_name = get_token_info(full_symbol)

    price = v['price']
    vol_1min = v['current_1min_volume']
    vol_avg = v['avg_1h_volume']
    ratio = v['ratio']
    vol_increase_pct = ((vol_1min - vol_avg) / vol_avg * 100) if vol_avg > 0 else 0
    vol_diff = vol_1min - vol_avg

    # CALCULER LE SCORE DE CONFIANCE
    score, score_details = calculer_score_confiance(anomaly)

    # Determiner nombre de decimales (2 pour prix > $1, sinon plus)
    if price >= 1:
        prix_fmt = f"${price:.2f}"
    elif price >= 0.01:
        prix_fmt = f"${price:.4f}"
    else:
        prix_fmt = f"${price:.6f}"

    # Recuperer nouvelles metriques
    price_change_1h = v.get('price_change_1h', 0)
    volume_change_pct = v.get('volume_change_pct', 0)
    trades_count = v.get('trades_count_1h', 0)

    # HEADER AVEC SCORE
    txt = f"\n🔥 *{symbol}*"
    if token_name != symbol:
        txt += f" ({token_name})"
    txt += f"\n━━━━━━━━━━━━━━━━\n"

    # AFFICHER LE SCORE DE CONFIANCE
    if score >= 80:
        txt += f"🎯 *SCORE: {score}/100* ⭐⭐⭐ EXCELLENT\n"
        txt += f"   💡 Signal TRES fiable - Forte probabilite profit\n\n"
    elif score >= 60:
        txt += f"🎯 *SCORE: {score}/100* ⭐⭐ BON\n"
        txt += f"   💡 Signal fiable - Bonne opportunite\n\n"
    elif score >= 40:
        txt += f"🎯 *SCORE: {score}/100* ⭐ MOYEN\n"
        txt += f"   ⚠️ Signal correct mais prudence\n\n"
    else:
        txt += f"🎯 *SCORE: {score}/100* ⚠️ FAIBLE\n"
        txt += f"   ❌ Signal peu fiable - A eviter\n\n"

    txt += f"📋 Raisons du score:\n"
    for detail in score_details[:3]:  # Top 3 raisons
        txt += f"   • {detail}\n"
    txt += f"\n"
    txt += f"💰 Prix: {prix_fmt} ({price_change_1h:+.1f}% 1h)\n"
    txt += f"📊 Vol 1min: ${vol_1min/1000:.0f}K ({volume_change_pct:+.0f}%)\n"
    txt += f"📈 Ratio: x{ratio:.1f}\n"

    if trades_count > 0:
        txt += f"🔄 Trades 1h: ~{trades_count}\n"

    if oi and oi['open_interest_usd'] > 0:
        txt += f"💼 OI: ${oi['open_interest_usd']/1_000_000:.1f}M\n"

    txt += f"\n🔍 *ANALYSE:*\n"

    # Analyse du volume
    if volume_change_pct >= 300:
        txt += f"🔥 Volume EXPLOSIF +{volume_change_pct:.0f}%!\n"
    elif volume_change_pct >= 100:
        txt += f"📈 Forte hausse volume +{volume_change_pct:.0f}%\n"
    elif volume_change_pct >= 50:
        txt += f"📊 Hausse volume significative +{volume_change_pct:.0f}%\n"

    # Analyse du prix
    if price_change_1h >= 3:
        txt += f"🚀 Prix en hausse forte +{price_change_1h:.1f}% (1h)\n"
    elif price_change_1h >= 1:
        txt += f"📈 Prix monte +{price_change_1h:.1f}% (1h)\n"
    elif price_change_1h <= -3:
        txt += f"📉 Prix en baisse forte {price_change_1h:.1f}% (1h)\n"
    elif price_change_1h <= -1:
        txt += f"📉 Prix baisse {price_change_1h:.1f}% (1h)\n"
    else:
        txt += f"⚖️ Prix stable ({price_change_1h:+.1f}% 1h)\n"

    # Analyse du ratio (spike)
    if ratio >= 10:
        txt += f"⚠️ Spike EXTREME x{ratio:.0f} = Probable whale/institution\n"
    elif ratio >= 5:
        txt += f"📊 Activite anormale detectee (x{ratio:.1f})\n"

    # Analyse du momentum
    momentum = v.get('momentum', 'neutre')
    if momentum == "acceleration":
        txt += f"🚀 MOMENTUM: Acceleration detectee!\n"
        txt += f"   💡 Volume augmente progressivement (t-2 < t-1 < t-0)\n"
        txt += f"   ✅ Signal se RENFORCE = BON SIGNE\n"
    elif momentum == "reprise":
        txt += f"🔄 MOMENTUM: Reprise apres baisse\n"
        txt += f"   💡 Volume remonte apres une pause\n"
        txt += f"   ⚠️ Possible rebond - A surveiller\n"
    elif momentum == "deceleration":
        txt += f"📉 MOMENTUM: Deceleration detectee\n"
        txt += f"   💡 Volume diminue progressivement\n"
        txt += f"   ❌ Signal s'affaiblit - PRUDENCE!\n"

    txt += f"\n"

    # Liquidations
    if liq and liq['total_liquidated_usd'] > 0:
        total_liq = liq['total_liquidated_usd']
        long_liq = liq['long_liquidated']
        short_liq = liq['short_liquidated']

        txt += f"⚡ LIQUIDATIONS (5 dernieres minutes):\n"
        txt += f"   📉 Shorts liquides: ${short_liq/1000:.0f}K ({short_liq/total_liq*100:.0f}%)\n"
        txt += f"   📈 Longs liquides: ${long_liq/1000:.0f}K ({long_liq/total_liq*100:.0f}%)\n\n"

        # Explication pedagogique Short/Long Squeeze
        if short_liq > long_liq * 3:
            txt += f"🔥 SITUATION: Short Squeeze!\n\n"
            txt += f"   📚 C'EST QUOI?\n"
            txt += f"   • Des traders avaient parie sur la BAISSE (short)\n"
            txt += f"   • Le prix a MONTE au lieu de baisser\n"
            txt += f"   • Leurs positions fermees de FORCE\n"
            txt += f"   • Pour fermer un short = ACHETER le token\n"
            txt += f"   • ${short_liq/1000:.0f}K de shorts obliges d'ACHETER\n\n"
            txt += f"   💡 CONSEQUENCE:\n"
            txt += f"   • Ces achats forces font monter le prix ENCORE PLUS\n"
            txt += f"   • Effet BOULE DE NEIGE!\n"
            txt += f"   • Court terme (30min-2h): Prix continue monter\n\n"

        elif long_liq > short_liq * 3:
            txt += f"🔴 SITUATION: Long Squeeze!\n\n"
            txt += f"   📚 C'EST QUOI?\n"
            txt += f"   • Des traders avaient parie sur la HAUSSE (long)\n"
            txt += f"   • Le prix a BAISSE au lieu de monter\n"
            txt += f"   • Leurs positions fermees de FORCE\n"
            txt += f"   • Pour fermer un long = VENDRE le token\n"
            txt += f"   • ${long_liq/1000:.0f}K de longs obliges de VENDRE\n\n"
            txt += f"   💡 CONSEQUENCE:\n"
            txt += f"   • Ces ventes forcees font baisser le prix ENCORE PLUS\n"
            txt += f"   • Effet DOMINO!\n"
            txt += f"   • Court terme: Prix continue baisser\n\n"

    txt += f"⚡ *ACTION SUGGEREE:*\n"

    # Calculer stop loss et targets (toujours!)
    stop_loss = price * 0.97
    target1 = price * 1.05
    target2 = price * 1.10

    # Determiner format prix pour stop/targets
    if price >= 1:
        sl_fmt = f"${stop_loss:.2f}"
        t1_fmt = f"${target1:.2f}"
        t2_fmt = f"${target2:.2f}"
    elif price >= 0.01:
        sl_fmt = f"${stop_loss:.4f}"
        t1_fmt = f"${target1:.4f}"
        t2_fmt = f"${target2:.4f}"
    else:
        sl_fmt = f"${stop_loss:.6f}"
        t1_fmt = f"${target1:.6f}"
        t2_fmt = f"${target2:.6f}"

    # Recommandations
    if liq and liq['total_liquidated_usd'] > 0:
        total_liq = liq['total_liquidated_usd']
        long_liq = liq['long_liquidated']
        short_liq = liq['short_liquidated']

        if short_liq > long_liq * 3 and total_liq > 1_000_000:
            txt += f"✅ ACHETER position courte (30min-2h)\n"
            txt += f"   💡 Short Squeeze = Prix va monter\n"
            txt += f"🎯 Entree: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"
            txt += f"⚠️ RISQUE ELEVE! Reste vigilant!\n"
        elif long_liq > short_liq * 3 and total_liq > 1_000_000:
            txt += f"❌ NE PAS ACHETER (baisse en cours)\n"
            txt += f"   💡 Long Squeeze = Prix va baisser\n"
            txt += f"⏰ Attends 1-2h que ca se stabilise\n"
        else:
            # Liquidations equilibrees
            txt += f"👀 SURVEILLER de pres\n"
            txt += f"🎯 Entree possible: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"
    else:
        # Pas de liquidations
        if ratio >= 10:
            txt += f"👀 SURVEILLER de pres:\n"
            txt += f"🔎 Cherche news Twitter/Reddit\n"
            txt += f"📊 Surveille 10-20min evolution\n\n"
            txt += f"💰 Si tu achetes:\n"
            txt += f"🎯 Entree: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"
        else:
            txt += f"👀 Surveille evolution\n\n"
            txt += f"💰 Si tu achetes:\n"
            txt += f"🎯 Entree: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"

    txt += f"\n📍 Binance: https://binance.com/en/trade/{full_symbol}\n"

    return txt

# =========================
# SCANNER
# =========================

def scanner(cfg):
    """Scan Binance et retourne anomalies."""
    logger.info("Debut du scan...")

    pairs = get_top_pairs(cfg['max_pairs_to_scan'])
    if not pairs:
        return []

    logger.info(f"Analyse de {len(pairs)} pairs...")

    anomalies = []
    scanned = 0

    for symbol in pairs:
        vol_data = get_klines_volume(symbol)

        if not vol_data:
            continue

        scanned += 1

        if vol_data['current_1min_volume'] < cfg['min_volume_usd']:
            continue

        if vol_data['ratio'] >= cfg['volume_threshold']:
            anomaly = {
                'symbol': symbol.replace('USDT', ''),
                'volume_data': vol_data,
                'liquidations': get_liquidations(symbol),
                'open_interest': get_open_interest(symbol),
                'detection_time': datetime.now()
            }

            anomalies.append(anomaly)
            logger.info(f"Anomalie detectee: {symbol} (x{vol_data['ratio']:.1f})")

        if scanned % 50 == 0:
            time.sleep(0.5)

    logger.info(f"Scan termine: {scanned} pairs analyses, {len(anomalies)} anomalies")
    return anomalies

# =========================
# PERFORMANCE TRACKING
# =========================

def verifier_performance(alert_history_with_price):
    """
    Verifie les performances des alertes passees.
    Retourne le win rate et stats utiles.
    """
    if not alert_history_with_price:
        return None

    wins = 0
    losses = 0
    total = 0

    for symbol, alerts in alert_history_with_price.items():
        for alert in alerts:
            if 'outcome' in alert:
                total += 1
                if alert['outcome'] == 'win':
                    wins += 1
                elif alert['outcome'] == 'loss':
                    losses += 1

    if total == 0:
        return None

    win_rate = (wins / total * 100) if total > 0 else 0

    return {
        'total_alerts': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate
    }

def evaluer_alertes_passees(alert_history):
    """
    Evalue les alertes passees (il y a 1h+) pour calculer le win rate.
    Une alerte = 'win' si prix a monte de 3%+ dans l'heure suivante.
    """
    now = datetime.utcnow()
    evaluated = 0

    for symbol, alerts in alert_history.items():
        for alert in alerts:
            # Si l'alerte n'a pas encore de outcome et date d'il y a 1h+
            if 'outcome' not in alert and 'price' in alert and 'timestamp' in alert:
                alert_time = datetime.fromisoformat(alert['timestamp'])
                hours_elapsed = (now - alert_time).total_seconds() / 3600

                # Si alerte date d'au moins 1h, on peut evaluer
                if hours_elapsed >= 1:
                    try:
                        # Recuperer le prix actuel
                        r = requests.get(f"{BINANCE_BASE}/api/v3/ticker/price", params={"symbol": symbol}, timeout=10)
                        current_price = float(r.json().get('price', 0))

                        if current_price > 0:
                            entry_price = alert['price']
                            change_pct = ((current_price - entry_price) / entry_price * 100)

                            # Critere: +3% = win
                            alert['outcome'] = 'win' if change_pct >= 3 else 'loss'
                            alert['profit_pct'] = change_pct
                            evaluated += 1
                    except:
                        pass

    if evaluated > 0:
        logger.info(f"Evalues {evaluated} alertes passees")

    return alert_history

# =========================
# FILTRE ANTI-MANIPULATION
# =========================

def nettoyer_historique(alert_history):
    """Nettoie l'historique des alertes > 7 jours."""
    now = datetime.utcnow()
    cleaned = {}

    for symbol, alerts in alert_history.items():
        # Garder seulement les alertes des 7 derniers jours
        recent_alerts = []
        for a in alerts:
            # Nouveau format: dict avec timestamp
            if isinstance(a, dict) and 'timestamp' in a:
                if (now - datetime.fromisoformat(a['timestamp'])).days <= 7:
                    recent_alerts.append(a)
            # Ancien format: simple string ISO timestamp (backward compatibility)
            elif isinstance(a, str):
                if (now - datetime.fromisoformat(a)).days <= 7:
                    recent_alerts.append(a)

        if recent_alerts:
            cleaned[symbol] = recent_alerts

    return cleaned

def est_manipule(symbol, alert_history, max_alerts=3):
    """
    Verifie si un token est probablement manipule.
    Critere: >3 alertes dans les 7 derniers jours = suspect.
    """
    if symbol not in alert_history:
        return False

    # Compter les alertes recentes
    count = len(alert_history[symbol])

    if count > max_alerts:
        logger.warning(f"Token {symbol} filtre: {count} alertes en 7j (manipulation suspectee)")
        return True

    return False

# =========================
# BOUCLE PRINCIPALE
# =========================

def boucle():
    """Boucle principale du bot."""
    state = charger_json(STATE_FILE, {
        "last_alerts": {},
        "last_scan": None,
        "alert_history": {}  # Nouveau: track alert count par symbol
    })

    cfg = charger_json(CONFIG_FILE, {
        "scan_interval_seconds": 120,
        "alert_cooldown_seconds": 600,
        "volume_threshold": 5.0,
        "min_volume_usd": 50000,
        "max_pairs_to_scan": 150,
        "max_alerts_per_scan": 3
    })

    if not Path(CONFIG_FILE).exists():
        save_json(CONFIG_FILE, cfg)

    tg(f"Bot Binance demarre !\nVolume threshold: {cfg['volume_threshold']}x\nScan: {cfg['scan_interval_seconds']}s")

    while True:
        try:
            # Nettoyer l'historique des alertes anciennes (> 7 jours)
            state["alert_history"] = nettoyer_historique(state.get("alert_history", {}))

            # Evaluer les alertes passees (performance tracking)
            state["alert_history"] = evaluer_alertes_passees(state.get("alert_history", {}))

            # Calculer le win rate actuel
            perf = verifier_performance(state.get("alert_history", {}))
            if perf:
                logger.info(f"Performance: {perf['wins']}/{perf['total_alerts']} wins = {perf['win_rate']:.1f}% win rate")

            anomalies = scanner(cfg)

            if anomalies:
                # FILTRE ANTI-MANIPULATION: Retirer les tokens suspects
                anomalies_filtrees = [
                    a for a in anomalies
                    if not est_manipule(a['symbol'], state["alert_history"], max_alerts=3)
                ]

                if not anomalies_filtrees:
                    logger.info("Toutes les anomalies filtrees (manipulation suspectee)")
                else:
                    alert_key = "binance_alerts"

                    if alert_key not in state["last_alerts"] or secondes_depuis(state["last_alerts"][alert_key]) >= cfg['alert_cooldown_seconds']:

                        sorted_anomalies = sorted(anomalies_filtrees, key=lambda x: x['volume_data']['ratio'], reverse=True)[:cfg['max_alerts_per_scan']]

                        msg = "Top activites crypto detectees\n(Volume temps reel Binance)\n"

                        # Afficher les performances si disponibles
                        if perf and perf['total_alerts'] >= 5:  # Au moins 5 alertes pour stats fiables
                            msg += f"\n📊 *PERFORMANCES BOT:*\n"
                            msg += f"   ✅ Win Rate: {perf['win_rate']:.1f}%\n"
                            msg += f"   📈 Wins: {perf['wins']} | ❌ Losses: {perf['losses']}\n"
                            msg += f"   (Critere: +3% en 1h)\n"

                        for i, anomaly in enumerate(sorted_anomalies, 1):
                            msg += f"\n#{i} " + generer_analyse(anomaly)

                        msg += f"\n\nScan effectue : {datetime.now().strftime('%H:%M:%S')}"

                        tg(msg)
                        state["last_alerts"][alert_key] = datetime.utcnow().isoformat()

                        # Enregistrer les alertes dans l'historique (avec prix pour tracking perf)
                        now = datetime.utcnow().isoformat()
                        for anomaly in sorted_anomalies:
                            symbol = anomaly['symbol']
                            price = anomaly['volume_data']['price']

                            if symbol not in state["alert_history"]:
                                state["alert_history"][symbol] = []

                            # Nouveau format: dict avec timestamp et prix
                            state["alert_history"][symbol].append({
                                'timestamp': now,
                                'price': price
                                # 'outcome' sera ajoute plus tard par evaluer_alertes_passees()
                            })

                        logger.info("Alerte envoyee")
                else:
                    temps_restant = cfg['alert_cooldown_seconds'] - secondes_depuis(state["last_alerts"][alert_key])
                    logger.info(f"Cooldown actif, {temps_restant:.0f}s restantes")

            state["last_scan"] = datetime.utcnow().isoformat()
            save_json(STATE_FILE, state)

            logger.info(f"Prochain scan dans {cfg['scan_interval_seconds']}s\n")
            time.sleep(cfg['scan_interval_seconds'])

        except KeyboardInterrupt:
            logger.info("Arret demande")
            tg("Bot Binance arrete")
            break
        except Exception as e:
            logger.error(f"Erreur: {e}")
            time.sleep(60)

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("="*80)
    print("BOT CRYPTO MONITOR v4.0 - BINANCE SCANNER")
    print("="*80)
    print("\nFonctionnalites:")
    print("  - Detection volume 1min temps reel")
    print("  - Liquidations massives")
    print("  - Open Interest tracking")
    print("  - Analyse pedagogique\n")
    print("Ctrl+C pour arreter")
    print("="*80)
    print()

    try:
        boucle()
    except KeyboardInterrupt:
        print("\nArret du bot.")
