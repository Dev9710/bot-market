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
    """Recupere volume 1min reel."""
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": "1m", "limit": 60}

    try:
        r = requests.get(url, params=params, timeout=10)
        klines = r.json()

        if not isinstance(klines, list) or len(klines) < 2:
            return None

        latest = klines[-1]
        close_price = float(latest[4])
        latest_volume_token = float(latest[5])
        latest_volume_usd = latest_volume_token * close_price

        total_volume_usd = 0
        for kline in klines[:-1]:
            volume_token = float(kline[5])
            close = float(kline[4])
            total_volume_usd += volume_token * close

        avg_volume_1min = total_volume_usd / len(klines[:-1]) if len(klines) > 1 else 1
        ratio = latest_volume_usd / avg_volume_1min if avg_volume_1min > 0 else 0

        return {
            'symbol': symbol,
            'current_1min_volume': latest_volume_usd,
            'avg_1h_volume': avg_volume_1min,
            'ratio': ratio,
            'price': close_price
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

    # Determiner nombre de decimales (2 pour prix > $1, sinon plus)
    if price >= 1:
        prix_fmt = f"${price:.2f}"
    elif price >= 0.01:
        prix_fmt = f"${price:.4f}"
    else:
        prix_fmt = f"${price:.6f}"

    txt = f"\n🔥 *{symbol}*"
    if token_name != symbol:
        txt += f" ({token_name})"
    txt += f"\n━━━━━━━━━━━━━━━━\n"
    txt += f"💰 Prix: {prix_fmt}\n"
    txt += f"📊 Vol 1min: ${vol_1min/1000:.0f}K (+{vol_increase_pct:.0f}% vs moy 1h)\n"
    txt += f"📈 Ratio: x{ratio:.1f}\n"

    if oi and oi['open_interest_usd'] > 0:
        txt += f"💼 OI: ${oi['open_interest_usd']/1_000_000:.1f}M (positions futures)\n"

    txt += f"\n🔍 *QUE SE PASSE-T-IL?*\n\n"

    # Section volume detaillee
    txt += f"💵 INJECTION DE VOLUME x{ratio:.1f}!\n"
    txt += f"   ↳ Volume normal: ${vol_avg/1000:.0f}K/min\n"
    txt += f"   ↳ Volume actuel: ${vol_1min/1000:.0f}K/min\n"
    txt += f"   ↳ Difference: +${vol_diff/1000:.0f}K en 1 minute!\n"
    txt += f"   ↳ Quelqu'un vient d'acheter MASSIVEMENT\n\n"

    # Explication importance volume
    txt += f"📊 POURQUOI LE VOLUME COMPTE?\n"
    txt += f"   • Volume eleve = Gros acheteurs entrent\n"
    if ratio >= 10:
        txt += f"   • Spike x{ratio:.0f} = Info privilegiee possible\n"
        txt += f"   • Pas un achat retail normal\n"
        txt += f"   • Probable: Institution, whale, ou insider\n\n"
    elif ratio >= 5:
        txt += f"   • Spike x{ratio:.1f} = Activite anormale\n"
        txt += f"   • Acheteurs importants actifs\n\n"

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
# BOUCLE PRINCIPALE
# =========================

def boucle():
    """Boucle principale du bot."""
    state = charger_json(STATE_FILE, {"last_alerts": {}, "last_scan": None})

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
            anomalies = scanner(cfg)

            if anomalies:
                alert_key = "binance_alerts"

                if alert_key not in state["last_alerts"] or secondes_depuis(state["last_alerts"][alert_key]) >= cfg['alert_cooldown_seconds']:

                    sorted_anomalies = sorted(anomalies, key=lambda x: x['volume_data']['ratio'], reverse=True)[:cfg['max_alerts_per_scan']]

                    msg = "Top activites crypto detectees\n(Volume temps reel Binance)\n"

                    for i, anomaly in enumerate(sorted_anomalies, 1):
                        msg += f"\n#{i} " + generer_analyse(anomaly)

                    msg += f"\n\nScan effectue : {datetime.now().strftime('%H:%M:%S')}"

                    tg(msg)
                    state["last_alerts"][alert_key] = datetime.utcnow().isoformat()
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
