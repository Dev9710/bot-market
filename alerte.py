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
# FORMATTAGE ALERTES
# =========================


def format_global_alert(top):
    txt = "🌍 *Top activités crypto détectées*\n"
    txt += "_(Volume anormal — explications adaptées débutants)_\n\n"

    for i, t in enumerate(top, start=1):
        txt += (
            f"*#{i} — {t['symbol']}*\n"
            f"💰 Prix : `{t['prix']:.6f} $`\n"
            f"📈 Volume 1m estimé : `{t['vol1m']:,.0f} $`\n"
            f"🔥 Multiplicateur : `x{t['ratio']:.1f}`\n"
            f"🏦 Market Cap : `{t['mc']:,.0f} $`\n"
            f"📊 Variation 24h : `{t['pct24']:.2f}%`\n"
            f"📉 Depuis le bas 24h : `{t['pct_from_low']:.1f}%`\n"
            f"🧱 Ratio Haut/Bas : `{t['h_l_ratio']:.2f}`\n"
            f"_→ Cela indique qu’un mouvement inhabituel apparaît sur ce token. Les traders commencent à s’y intéresser._\n\n"
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
