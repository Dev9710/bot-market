#!/usr/bin/env python3
# Crypto Monitor v4.0 – Scanner Binance Temps Réel
# Détection volume 1min réel + liquidations + Open Interest
# Alertes pédagogiques pour débutants

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import modules locaux
from binance_scanner import scan_all_pairs
from binance_alerts import format_binance_alert

# =========================
# INITIALISATION
# =========================

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

STATE_FILE = "monitor_state_binance.json"
CONFIG_FILE = "config_binance.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("binance-scan")

# =========================
# UTILS
# =========================

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


def secondes_depuis(iso):
    try:
        return (datetime.utcnow() - datetime.fromisoformat(iso)).total_seconds()
    except:
        return 10**9

# =========================
# STATE
# =========================

def charger_state():
    st = charger_json(STATE_FILE, None)
    if st is None:
        st = {
            "last_alerts": {},
            "last_scan": None
        }
    return st


def save_state(st):
    save_json(STATE_FILE, st)

# =========================
# TELEGRAM
# =========================

import requests

def tg(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram non configuré")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID,
                  "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        logger.info("✅ Alerte Telegram envoyée")
    except Exception as e:
        logger.error(f"Erreur Telegram: {e}")

# =========================
# ANTI-SPAM
# =========================

def doit_alerter(state, key, cooldown):
    if key not in state["last_alerts"]:
        return True
    return secondes_depuis(state["last_alerts"][key]) >= cooldown


def marquer(state, key):
    state["last_alerts"][key] = datetime.utcnow().isoformat()

# =========================
# BOUCLE PRINCIPALE
# =========================

def boucle():
    state = charger_state()
    cfg = charger_json(CONFIG_FILE, {
        "scan_interval_seconds": 120,  # 2 minutes par défaut
        "alert_cooldown_seconds": 600,  # 10 minutes entre alertes
        "volume_threshold": 5.0,  # x5 volume
        "min_volume_usd": 50000,  # $50K minimum
        "max_pairs_to_scan": 150,  # Top 150 tokens
        "max_alerts_per_scan": 3  # Max 3 alertes à la fois
    })

    # Sauvegarder config par défaut si inexistante
    if not Path(CONFIG_FILE).exists():
        save_json(CONFIG_FILE, cfg)
        logger.info(f"✅ Configuration créée: {CONFIG_FILE}")

    tg("🚀 *Bot Binance démarré !*\n\n"
       "Détection volume temps réel activée:\n"
       f"• Volume threshold: {cfg['volume_threshold']}x\n"
       f"• Scan interval: {cfg['scan_interval_seconds']}s\n"
       f"• Cooldown alertes: {cfg['alert_cooldown_seconds']}s\n\n"
       "Je te préviendrai des mouvements anormaux sur Binance!")

    while True:
        try:
            logger.info("🔍 Début du scan Binance...")

            # Scanner Binance
            anomalies = scan_all_pairs(
                volume_threshold=cfg['volume_threshold'],
                min_volume_usd=cfg['min_volume_usd'],
                max_pairs=cfg['max_pairs_to_scan']
            )

            if anomalies:
                logger.info(f"🎯 {len(anomalies)} anomalies détectées")

                # Vérifier cooldown
                alert_key = "binance_alerts"
                if doit_alerter(state, alert_key, cfg['alert_cooldown_seconds']):
                    # Formater et envoyer alerte
                    alert_text = format_binance_alert(
                        anomalies,
                        max_alerts=cfg['max_alerts_per_scan']
                    )

                    if alert_text:
                        tg(alert_text)
                        marquer(state, alert_key)
                        logger.info("✅ Alerte envoyée")
                else:
                    temps_restant = cfg['alert_cooldown_seconds'] - secondes_depuis(state["last_alerts"][alert_key])
                    logger.info(f"⏳ Cooldown actif, {temps_restant:.0f}s restantes")
            else:
                logger.info("✓ Aucune anomalie détectée")

            # Sauvegarder état
            state["last_scan"] = datetime.utcnow().isoformat()
            save_state(state)

            # Attendre avant prochain scan
            logger.info(f"⏰ Prochain scan dans {cfg['scan_interval_seconds']}s\n")
            time.sleep(cfg['scan_interval_seconds'])

        except KeyboardInterrupt:
            logger.info("🛑 Arrêt demandé par l'utilisateur")
            tg("🛑 Bot Binance arrêté manuellement.")
            break

        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle principale: {e}")
            time.sleep(60)  # Attendre 1 min avant de réessayer

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("="*80)
    print("🚀 BOT CRYPTO MONITOR v4.0 - BINANCE SCANNER")
    print("="*80)
    print()
    print("Fonctionnalités:")
    print("  ✅ Détection volume 1min temps réel (Binance klines)")
    print("  ✅ Liquidations massives (Binance Futures)")
    print("  ✅ Open Interest tracking")
    print("  ✅ Long/Short ratio")
    print("  ✅ Analyse pédagogique pour débutants")
    print()
    print("Appuyez sur Ctrl+C pour arrêter")
    print("="*80)
    print()

    try:
        boucle()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du bot.")
