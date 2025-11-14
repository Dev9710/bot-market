#!/usr/bin/env python3
# Crypto Monitor – Scan Global Unifié
# Détection précoce d’activité, volume anormal, whales, prix et métriques clés.
# Optimisé pour débutants, alertes Telegram simples et parlantes.

import os
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# =========================
# INITIALISATION
# =========================

load_dotenv()

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
ETHERSCAN_V2 = "https://api.etherscan.io/v2/api"

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CMC_API_KEY = os.getenv("CMC_API_KEY", "")

STATE_FILE = "monitor_state.json"
CONFIG_FILE = "config_tokens.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("global-scan")

# =========================
# OUTILS
# =========================


def maintenant():
    return datetime.utcnow()


def secondes_depuis(iso):
    try:
        return (maintenant() - datetime.fromisoformat(iso)).total_seconds()
    except:
        return 10**9


def charger_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        with p.open("r") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# STATE
# =========================


def charger_state():
    st = charger_json(STATE_FILE, None)
    if st is None:
        st = {
            "global_volume": {},
            "last_alerts": {},
            "global_last_run": None
        }
    return st


def save_state(st):
    save_json(STATE_FILE, st)

# =========================
# TELEGRAM
# =========================


def tg(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID,
                  "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except:
        pass

# =========================
# ANTI-SPAM
# =========================


def doit_alerter(state, key, cooldown):
    if key not in state["last_alerts"]:
        return True
    return secondes_depuis(state["last_alerts"][key]) >= cooldown


def marquer(state, key):
    state["last_alerts"][key] = maintenant().isoformat()

# =========================
# SCAN GLOBAL
# =========================


def scan_global(state, cfg):
    gcfg = cfg.get("global_volume_scan", {})
    if not gcfg.get("enabled", False):
        return []

    interval = gcfg.get("interval_seconds", 60)
    min_vol24 = gcfg.get("min_vol24_usd", 100000)
    ratio_thr = gcfg.get("ratio_threshold", 5.0)
    min_price = gcfg.get("min_price_usd", 0.0001)

    last_run = state["global_last_run"]
    if last_run and secondes_depuis(last_run) < interval:
        return []

    logger.info("🌍 Scan global (CoinGecko)…")

    anomalies = []

    try:
        for page in range(1, 5):  # ~1000 coins
            r = requests.get(
                f"{COINGECKO_BASE}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": page
                },
                timeout=20
            )

            markets = r.json()
            if not isinstance(markets, list):
                continue

            for c in markets:

                # SÉCURISATION MAX : aucun float ne peut être None
                idcg = c.get("id")
                if not idcg:
                    continue

                symbol = (c.get("symbol") or "???").upper()
                name = c.get("name") or "Unknown"
                prix = float(c.get("current_price") or 0)
                vol24 = float(c.get("total_volume") or 0)
                mc = float(c.get("market_cap") or 0)

                high24 = float(c.get("high_24h") or 0)
                low24 = float(c.get("low_24h") or 0)
                pct24 = float(c.get("price_change_percentage_24h") or 0)

                # Filtre qualité
                if prix < min_price or vol24 < min_vol24:
                    continue

                # Calculs protégés
                avg1m = vol24 / 1440 if vol24 > 0 else 0
                h_l_ratio = (high24 / low24) if low24 > 0 else 0
                pct_from_low = ((prix - low24) / low24 *
                                100) if low24 > 0 else 0
                pct_from_high = ((prix - high24) / high24 *
                                 100) if high24 > 0 else 0

                # Récup dernier état
                gstate = state["global_volume"].setdefault(idcg, {})
                last_vol24 = float(gstate.get("vol24", 0))
                last_ts = gstate.get("ts")

                vol1m_est = 0
                if last_ts:
                    dt = secondes_depuis(last_ts)
                    dt = max(dt, 1)  # évite division 0
                    delta = max(vol24 - last_vol24, 0)
                    vol1m_est = delta / (dt / 60)

                # Mise à jour
                gstate["vol24"] = vol24
                gstate["ts"] = maintenant().isoformat()

                if avg1m <= 0 or vol1m_est <= 0:
                    continue

                ratio = vol1m_est / avg1m

                if ratio >= ratio_thr:
                    anomalies.append({
                        "symbol": symbol,
                        "name": name,
                        "coingecko_id": idcg,
                        "prix": prix,
                        "mc": mc,
                        "pct24": pct24,
                        "vol1m": vol1m_est,
                        "vol24": vol24,
                        "ratio": ratio,
                        "h_l_ratio": h_l_ratio,
                        "pct_from_low": pct_from_low,
                        "pct_from_high": pct_from_high
                    })

    except Exception as e:
        logger.warning(f"Erreur scan global : {e}")

    state["global_last_run"] = maintenant().isoformat()

    return sorted(anomalies, key=lambda x: x["ratio"], reverse=True)

# =========================
# BINANCE FUTURES API
# =========================

# Cache pour positions long/short
LONGSHORT_CACHE = {}


def get_binance_longshort_ratio(symbol):
    """
    Récupère le ratio long/short depuis Binance Futures API (GRATUIT).

    Args:
        symbol: Symbole du token (ex: "BTCUSDT")

    Returns:
        dict avec ratio, pourcentages et interprétation ou None si erreur
    """
    # Vérifier le cache d'abord (5 minutes de validité)
    cache_key = f"{symbol}_{int(time.time() / 300)}"  # Change toutes les 5 min
    if cache_key in LONGSHORT_CACHE:
        return LONGSHORT_CACHE[cache_key]

    try:
        url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
        params = {
            "symbol": symbol,
            "period": "5m",
            "limit": 1
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if isinstance(data, list) and len(data) > 0:
            latest = data[0]
            ratio = float(latest['longShortRatio'])
            long_pct = ratio / (1 + ratio)
            short_pct = 1 - long_pct

            # Interprétation intelligente
            if long_pct >= 0.65:
                interpretation = f"⚠️ MAJORITÉ EN LONG ({long_pct*100:.1f}%)"
                risk = "Risque de liquidations si baisse soudaine"
                action = "Stop-loss recommandé"
            elif short_pct >= 0.65:
                interpretation = f"⚠️ MAJORITÉ EN SHORT ({short_pct*100:.1f}%)"
                risk = "Risque de short squeeze si hausse"
                action = "Opportunité d'achat si squeeze confirmé"
            else:
                interpretation = f"✓ ÉQUILIBRÉ (L:{long_pct*100:.1f}% S:{short_pct*100:.1f}%)"
                risk = "Bataille indécise"
                action = "Attendre signal clair"

            result = {
                'longShortRatio': ratio,
                'longPct': long_pct,
                'shortPct': short_pct,
                'interpretation': interpretation,
                'risk': risk,
                'action': action
            }

            # Sauvegarder dans le cache
            LONGSHORT_CACHE[cache_key] = result
            return result

    except Exception as e:
        logger.warning(f"Erreur Binance API pour {symbol}: {e}")

    return None


# =========================
# RÉCUPÉRATION INFOS LISTING
# =========================

# Cache pour éviter de récupérer les mêmes infos plusieurs fois
PLATFORMS_CACHE = {}


def get_token_platforms(coingecko_id):
    """Récupère les plateformes (exchanges + blockchains) depuis CoinGecko."""
    # Vérifier le cache d'abord
    if coingecko_id in PLATFORMS_CACHE:
        return PLATFORMS_CACHE[coingecko_id]

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
            for ticker in data["tickers"][:20]:  # Limiter pour éviter trop d'appels
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
                # Convertir les clés techniques en noms lisibles
                platform_name = platform_key.replace("-", " ").title()
                blockchains.append(platform_name)

        result = {
            "exchanges": exchanges[:5],  # Top 5 exchanges
            "blockchains": blockchains[:3]  # Top 3 blockchains
        }

        # Sauvegarder dans le cache
        PLATFORMS_CACHE[coingecko_id] = result
        return result

    except Exception as e:
        logger.warning(f"Erreur récupération platforms pour {coingecko_id}: {e}")
        result = {"exchanges": [], "blockchains": []}
        PLATFORMS_CACHE[coingecko_id] = result
        return result


# =========================
# GÉNÉRATION DESCRIPTIONS INTELLIGENTES
# =========================


def generate_smart_analysis(t, longshort_data=None):
    """
    Génère une analyse intelligente et contextuelle pour un token.

    Args:
        t: Dictionnaire avec les données du token
        longshort_data: Données Binance long/short (optionnel)

    Returns:
        str: Description formatée avec analyse et recommandations
    """
    ratio = t['ratio']
    pct24 = t['pct24']
    pct_from_low = t['pct_from_low']
    h_l_ratio = t['h_l_ratio']
    vol1m = t['vol1m']
    vol24 = t['vol24']

    # Calcul volume moyen
    avg1m = vol24 / 1440

    # Construction de l'analyse
    txt = "\n🚨 *POURQUOI CETTE ALERTE ?*\n"

    # 1. Volume
    txt += f"✓ Volume x{ratio:.1f} supérieur à la moyenne ({vol1m:,.0f}$/min vs {avg1m:,.0f}$/min)\n"

    # 2. Prix (hausse/baisse/stable)
    if pct24 > 2:
        txt += f"✓ Prix en hausse : +{pct24:.2f}% sur 24h, +{pct_from_low:.1f}% depuis le plus bas\n"
    elif pct24 < -2:
        txt += f"⚠️ Prix en baisse : {pct24:.2f}% sur 24h, à {pct_from_low:.1f}% du plus bas\n"
    else:
        txt += f"✓ Prix stable : {pct24:+.2f}% sur 24h avec faible variation\n"

    # 3. Volatilité
    volatility_pct = (h_l_ratio - 1) * 100
    if volatility_pct > 10:
        txt += f"✓ Volatilité élevée : {volatility_pct:.1f}% d'écart haut/bas\n"
    else:
        txt += f"✓ Volatilité modérée : {volatility_pct:.1f}% d'écart haut/bas\n"

    # 4. Positions long/short (si disponible)
    if longshort_data:
        txt += f"✓ Positions : {longshort_data['interpretation']}\n"

    # INTERPRÉTATION
    txt += "\n💡 *CE QUE ÇA SIGNIFIE :*\n"

    # Déterminer le scénario
    if ratio >= 10 and pct24 > 20:
        # PUMP massif
        txt += f"🔥 *PUMP DÉTECTÉ !* Volume x{ratio:.1f} + Prix +{pct24:.1f}% = FOMO massif.\n"
        txt += "Des acheteurs entrent en panique, probablement après une annonce.\n"
        txt += "⚠️ DANGER : Ce qui monte vite redescend vite !\n"

    elif pct24 > 3 and pct_from_low > 10:
        # Accumulation forte (hausse)
        txt += f"Gros acheteurs entrent massivement. Prix monte avec volume élevé\n"
        txt += "= Signal d'accumulation forte. Momentum haussier confirmé.\n"
        if longshort_data and longshort_data['longPct'] > 0.60:
            txt += f"⚠️ Attention : {longshort_data['longPct']*100:.0f}% en long, risque si correction.\n"

    elif pct24 < -3 and pct_from_low < 10:
        # Capitulation (baisse)
        txt += f"Gros vendeurs liquident leurs positions massivement.\n"
        txt += "Volume élevé + Prix en baisse = Capitulation possible.\n"
        txt += "⚠️ Pression vendeuse importante, proche du support critique.\n"
        if longshort_data and longshort_data['shortPct'] > 0.60:
            txt += f"⚠️ {longshort_data['shortPct']*100:.0f}% en short, risque de short squeeze si rebond.\n"

    elif abs(pct24) < 2 and ratio > 5:
        # Volume élevé + prix stable (accumulation silencieuse)
        txt += f"Volume anormalement élevé mais prix stable = Accumulation silencieuse.\n"
        txt += "Les gros joueurs se positionnent avant un mouvement futur.\n"

    else:
        # Cas général
        txt += f"Activité inhabituelle détectée. Volume x{ratio:.1f} au-dessus de la normale.\n"
        txt += "Les traders s'intéressent fortement à ce token en ce moment.\n"

    # RECOMMANDATION
    txt += "\n⚠️ *QUE FAIRE :*\n"

    if ratio >= 10 and pct24 > 20:
        # PUMP - NE PAS ACHETER
        txt += "❌ NE PAS ACHETER maintenant (risque de dump imminent) !\n"
        txt += "✓ Si vous détenez : Prenez vos profits progressivement\n"
        txt += "✓ Si vous n'en avez pas : Attendre une correction avant d'entrer\n"

    elif pct24 > 3 and pct_from_low > 10:
        # Signal d'achat potentiel
        txt += "✓ Surveiller les prochaines minutes\n"
        txt += "✓ Si volume reste élevé + prix continue de monter = Signal d'achat\n"
        if longshort_data:
            txt += f"✓ {longshort_data['action']}\n"

    elif pct24 < -3 and pct_from_low < 5:
        # Signal de vente
        txt += "⚠️ ATTENTION - Signal de vente potentiel\n"
        txt += "✓ Si vous détenez ce token : Surveillez le support\n"
        txt += "✓ Si cassure du plus bas 24h : Vente recommandée\n"

    else:
        # Attendre
        txt += "✓ Surveiller l'évolution des prochaines minutes\n"
        txt += "✓ Attendre confirmation avant d'entrer en position\n"
        if longshort_data:
            txt += f"✓ {longshort_data['action']}\n"

    return txt


# =========================
# FORMATTAGE ALERTES
# =========================


def format_global_alert(top):
    txt = "🌍 *Top activités crypto détectées*\n"
    txt += "_(Volume anormal — Analyse détaillée)_\n\n"

    for i, t in enumerate(top, start=1):
        # Récupérer les plateformes de listing
        platforms = get_token_platforms(t['coingecko_id'])

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
        elif not platforms["exchanges"]:  # Si pas de blockchain ni exchange détecté
            blockchains_txt = f"⛓️ Natif (blockchain propre)\n"

        # Essayer de récupérer les positions long/short (Binance)
        # Convertir le symbol en format Binance (ex: BTC -> BTCUSDT)
        binance_symbol = f"{t['symbol']}USDT"
        longshort_data = get_binance_longshort_ratio(binance_symbol)

        # Section positions (si disponible)
        positions_txt = ""
        if longshort_data:
            positions_txt = (
                f"\n📊 *POSITIONS (Binance Futures) :*\n"
                f"🟢 LONGS : {longshort_data['longPct']*100:.1f}%  |  "
                f"🔴 SHORTS : {longshort_data['shortPct']*100:.1f}%\n"
                f"{longshort_data['interpretation']}\n"
            )

        # Générer l'analyse intelligente
        analysis = generate_smart_analysis(t, longshort_data)

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
            f"{positions_txt}"
            f"{analysis}\n"
            f"{'─'*40}\n\n"
        )

    return txt

# =========================
# BOUCLE PRINCIPALE
# =========================


def boucle():
    state = charger_state()
    cfg = charger_json(CONFIG_FILE, {})

    tg("🚀 *Bot global démarré !*\nJe te préviendrai des mouvements anormaux dans tout l'écosystème.")

    cooldown = cfg.get("alert_cooldown_seconds", 300)

    while True:
        anomalies = scan_global(state, cfg)

        if anomalies:
            top = anomalies[:10]
            alert_key = "global_top"

            if doit_alerter(state, alert_key, cooldown):
                tg(format_global_alert(top))
                marquer(state, alert_key)

        save_state(state)
        time.sleep(1 * 60)  # ⏳ scan toutes les 15 minutes

# =========================
# MAIN
# =========================


if __name__ == "__main__":
    try:
        boucle()
    except KeyboardInterrupt:
        tg("🛑 Bot arrêté manuellement.")
        print("STOP.")
