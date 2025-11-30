"""
GeckoTerminal Scanner - Detection tokens DEX (nouvelles opportunites)
Detecte les nouveaux tokens avec volume eleve et liquidite suffisante
API Gratuite: 30 calls/min
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# UTF-8 pour emojis Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (ValueError, AttributeError):
            pass

# Configuration
GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7868518759:AAFxEXGz0DgMPYVKILJOEb5kNDwPy3N5W5c")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7994790177")

# Reseaux a surveiller (ordre de priorite)
NETWORKS = [
    "eth",        # Ethereum
    "bsc",        # Binance Smart Chain
    "polygon",    # Polygon
    "arbitrum",   # Arbitrum
    "base",       # Base
    "solana",     # Solana
]

# Seuils de detection
MIN_LIQUIDITY_USD = 50000      # Liquidite min (eviter rug pull)
MIN_VOLUME_24H_USD = 100000    # Volume 24h min
MIN_TXNS_24H = 100             # Nb transactions min
MAX_TOKEN_AGE_HOURS = 72       # Max 3 jours (nouveaux tokens)
VOLUME_LIQUIDITY_RATIO = 0.5   # Vol24h/Liquidite > 50% = actif

# Cooldown alertes
alert_cooldown = {}
COOLDOWN_SECONDS = 1800  # 30 min entre alertes meme token

# Logs
def log(msg: str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def send_telegram(message: str) -> bool:
    """Envoie alerte Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        log(f"❌ Erreur Telegram: {e}")
        return False

def get_trending_pools(network: str, page: int = 1) -> Optional[List[Dict]]:
    """Recupere pools trending sur un reseau."""
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/trending_pools"
        params = {"page": page}
        headers = {"Accept": "application/json"}

        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 429:
            log(f"⚠️ Rate limit atteint, pause 60s...")
            time.sleep(60)
            return None

        if response.status_code != 200:
            log(f"⚠️ Erreur {network}: {response.status_code}")
            return None

        data = response.json()
        return data.get("data", [])

    except Exception as e:
        log(f"❌ Erreur get_trending_pools {network}: {e}")
        return None

def get_new_pools(network: str, page: int = 1) -> Optional[List[Dict]]:
    """Recupere nouveaux pools sur un reseau."""
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/new_pools"
        params = {"page": page}
        headers = {"Accept": "application/json"}

        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 429:
            log(f"⚠️ Rate limit atteint, pause 60s...")
            time.sleep(60)
            return None

        if response.status_code != 200:
            return None

        data = response.json()
        return data.get("data", [])

    except Exception as e:
        log(f"❌ Erreur get_new_pools {network}: {e}")
        return None

def parse_pool_data(pool: Dict) -> Optional[Dict]:
    """Parse donnees pool GeckoTerminal."""
    try:
        attrs = pool.get("attributes", {})

        # Infos de base
        name = attrs.get("name", "Unknown")
        base_token = attrs.get("base_token_price_usd")
        price_usd = float(base_token) if base_token else 0

        # Volume et liquidite
        volume_24h = float(attrs.get("volume_usd", {}).get("h24", 0))
        liquidity = float(attrs.get("reserve_in_usd", 0))

        # Transactions
        txns_24h = attrs.get("transactions", {}).get("h24", {})
        buys = txns_24h.get("buys", 0)
        sells = txns_24h.get("sells", 0)
        total_txns = buys + sells

        # Variation prix
        price_change_24h = float(attrs.get("price_change_percentage", {}).get("h24", 0))

        # Age du pool
        pool_created = attrs.get("pool_created_at")
        if pool_created:
            created_dt = datetime.fromisoformat(pool_created.replace('Z', '+00:00'))
            age_hours = (datetime.now().astimezone() - created_dt).total_seconds() / 3600
        else:
            age_hours = 999999  # Inconnu = tres vieux

        # Reseau et adresse
        network = pool.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
        pool_address = attrs.get("address", "")

        return {
            "name": name,
            "price_usd": price_usd,
            "volume_24h": volume_24h,
            "liquidity": liquidity,
            "total_txns": total_txns,
            "buys": buys,
            "sells": sells,
            "price_change_24h": price_change_24h,
            "age_hours": age_hours,
            "network": network,
            "pool_address": pool_address,
        }

    except Exception as e:
        log(f"⚠️ Erreur parse pool: {e}")
        return None

def is_valid_opportunity(pool_data: Dict) -> tuple[bool, str]:
    """Verifie si pool est une opportunite valide."""

    # Check liquidite min (anti rug pull)
    if pool_data["liquidity"] < MIN_LIQUIDITY_USD:
        return False, f"❌ Liquidite trop faible: ${pool_data['liquidity']:,.0f}"

    # Check volume min
    if pool_data["volume_24h"] < MIN_VOLUME_24H_USD:
        return False, f"⚠️ Volume trop faible: ${pool_data['volume_24h']:,.0f}"

    # Check transactions min
    if pool_data["total_txns"] < MIN_TXNS_24H:
        return False, f"⚠️ Pas assez de txns: {pool_data['total_txns']}"

    # Check age (nouveaux tokens uniquement)
    if pool_data["age_hours"] > MAX_TOKEN_AGE_HOURS:
        return False, f"⏳ Token trop ancien: {pool_data['age_hours']:.0f}h"

    # Check ratio volume/liquidite (activite)
    ratio = pool_data["volume_24h"] / pool_data["liquidity"] if pool_data["liquidity"] > 0 else 0
    if ratio < VOLUME_LIQUIDITY_RATIO:
        return False, f"📉 Ratio Vol/Liq trop faible: {ratio:.1%}"

    # Detecter pump & dump potentiel
    buy_sell_ratio = pool_data["buys"] / pool_data["sells"] if pool_data["sells"] > 0 else 999
    if buy_sell_ratio > 5:
        return False, f"🚨 Trop de achats vs ventes (pump?): {buy_sell_ratio:.1f}"

    if buy_sell_ratio < 0.2:
        return False, f"📉 Trop de ventes vs achats (dump?): {buy_sell_ratio:.1f}"

    return True, "✅ Opportunite valide"

def generer_alerte_dex(pool_data: Dict) -> str:
    """Genere alerte CONCISE avec emojis (meme format que Binance)."""

    name = pool_data["name"]
    price = pool_data["price_usd"]
    vol_24h = pool_data["volume_24h"]
    liq = pool_data["liquidity"]
    pct_24h = pool_data["price_change_24h"]
    age = pool_data["age_hours"]
    txns = pool_data["total_txns"]
    buys = pool_data["buys"]
    sells = pool_data["sells"]
    network = pool_data["network"].upper()
    ratio_vol_liq = vol_24h / liq if liq > 0 else 0

    # Alerte concise
    txt = f"\n🆕 *NOUVEAU TOKEN DEX*\n"
    txt += f"━━━━━━━━━━━━━━━━\n"
    txt += f"💎 {name}\n"
    txt += f"🌐 Reseau: {network}\n"
    txt += f"💰 Prix: ${price:.8f}\n"
    txt += f"📊 Vol 24h: ${vol_24h/1000:.0f}K\n"
    txt += f"💧 Liquidite: ${liq/1000:.0f}K\n"
    txt += f"📈 Variation: {pct_24h:+.1f}%\n"
    txt += f"⏰ Age: {age:.0f}h\n"
    txt += f"🔄 Txns: {txns} (A:{buys} V:{sells})\n"
    txt += f"📊 Vol/Liq: {ratio_vol_liq:.1%}\n\n"

    txt += f"🔍 *ANALYSE:*\n"

    # Analyse liquidite
    if liq >= 200000:
        txt += f"✅ Liquidite solide (${liq/1000:.0f}K)\n"
    elif liq >= 100000:
        txt += f"⚠️ Liquidite moyenne (${liq/1000:.0f}K)\n"
    else:
        txt += f"⚠️ Liquidite faible - PRUDENCE!\n"

    # Analyse activite
    if ratio_vol_liq >= 1.0:
        txt += f"🔥 TRES actif! (Vol={ratio_vol_liq:.0%} Liq)\n"
    elif ratio_vol_liq >= 0.5:
        txt += f"📈 Bonne activite (Vol={ratio_vol_liq:.0%} Liq)\n"

    # Analyse achats/ventes
    buy_sell_ratio = buys / sells if sells > 0 else 999
    if buy_sell_ratio > 2:
        txt += f"🟢 Plus d'achats! ({buys}A vs {sells}V)\n"
    elif buy_sell_ratio < 0.5:
        txt += f"🔴 Plus de ventes! ({buys}A vs {sells}V)\n"
    else:
        txt += f"⚖️ Equilibre achats/ventes\n"

    # Analyse age
    if age < 24:
        txt += f"🆕 NOUVEAU! (Cree il y a {age:.0f}h)\n"
    elif age < 48:
        txt += f"⏰ Recent ({age:.0f}h)\n"

    # Analyse prix
    if pct_24h > 50:
        txt += f"🚀 PUMP violent +{pct_24h:.0f}%!\n"
    elif pct_24h > 20:
        txt += f"📈 Hausse forte +{pct_24h:.0f}%\n"
    elif pct_24h < -20:
        txt += f"📉 Baisse forte {pct_24h:.0f}%\n"

    txt += f"\n⚡ *ACTION:*\n"

    # Recommandation
    if liq >= 200000 and ratio_vol_liq >= 1.0 and 0.5 <= buy_sell_ratio <= 2:
        txt += f"✅ OPPORTUNITE potentielle\n"
        txt += f"🎯 Entree: petit montant test\n"
        txt += f"⚠️ Stop: -15% / Target: +30-50%\n"
    elif liq >= 100000:
        txt += f"👀 Surveille evolution\n"
        txt += f"⚠️ Liquidite moyenne - petit risque\n"
    else:
        txt += f"❌ EVITER - Liquidite trop faible!\n"
        txt += f"🚨 Risque RUG PULL eleve!\n"

    txt += f"\n🔗 https://geckoterminal.com/{network}/pools/{pool_data['pool_address']}\n"

    return txt

def check_cooldown(pool_name: str) -> bool:
    """Verifie si alerte en cooldown."""
    now = time.time()
    if pool_name in alert_cooldown:
        elapsed = now - alert_cooldown[pool_name]
        if elapsed < COOLDOWN_SECONDS:
            return False
    alert_cooldown[pool_name] = now
    return True

def scan_geckoterminal():
    """Scan GeckoTerminal pour nouveaux tokens."""

    log("=" * 80)
    log("🦎 GECKOTERMINAL SCANNER - Detection Nouveaux Tokens DEX")
    log("=" * 80)

    opportunities = []

    for network in NETWORKS:
        log(f"\n🔍 Scan reseau: {network.upper()}")

        # Recuperer trending pools (plus actifs)
        trending = get_trending_pools(network)

        if trending:
            log(f"   📊 {len(trending)} pools trending trouves")

            for pool in trending:
                pool_data = parse_pool_data(pool)

                if pool_data:
                    is_valid, reason = is_valid_opportunity(pool_data)

                    if is_valid:
                        log(f"   ✅ Opportunite: {pool_data['name']}")
                        opportunities.append(pool_data)
                    else:
                        log(f"   ⏭️  {pool_data['name']}: {reason}")

        # Pause pour rate limit (30 calls/min = 1 call/2s)
        time.sleep(2)

        # Recuperer nouveaux pools
        new_pools = get_new_pools(network)

        if new_pools:
            log(f"   🆕 {len(new_pools)} nouveaux pools trouves")

            for pool in new_pools:
                pool_data = parse_pool_data(pool)

                if pool_data:
                    # Filtrer uniquement les tres nouveaux (<72h)
                    if pool_data["age_hours"] <= MAX_TOKEN_AGE_HOURS:
                        is_valid, reason = is_valid_opportunity(pool_data)

                        if is_valid:
                            log(f"   ✅ Opportunite: {pool_data['name']}")
                            opportunities.append(pool_data)
                        else:
                            log(f"   ⏭️  {pool_data['name']}: {reason}")

        # Pause pour rate limit
        time.sleep(2)

    # Envoyer alertes
    log(f"\n📊 TOTAL: {len(opportunities)} opportunites detectees")

    alerts_sent = 0
    for opp in opportunities:
        if check_cooldown(opp["name"]):
            alert_msg = generer_alerte_dex(opp)

            if send_telegram(alert_msg):
                log(f"✅ Alerte envoyee: {opp['name']}")
                alerts_sent += 1
            else:
                log(f"❌ Echec alerte: {opp['name']}")

            # Limiter a 3 alertes max par scan
            if alerts_sent >= 3:
                log("⚠️ Limite 3 alertes atteinte")
                break

            time.sleep(1)  # Pause entre alertes

    log(f"\n✅ Scan termine: {alerts_sent} alertes envoyees")
    log("=" * 80)

def main():
    """Boucle principale."""
    log("🚀 Demarrage GeckoTerminal Scanner...")
    log(f"📡 Reseaux surveilles: {', '.join([n.upper() for n in NETWORKS])}")
    log(f"💧 Liquidite min: ${MIN_LIQUIDITY_USD:,}")
    log(f"📊 Volume 24h min: ${MIN_VOLUME_24H_USD:,}")
    log(f"⏰ Age max: {MAX_TOKEN_AGE_HOURS}h")
    log(f"🔄 Scan tous les 5 minutes (rate limit: 30 calls/min)")

    while True:
        try:
            scan_geckoterminal()

            # Attendre 5 minutes avant prochain scan
            log("\n💤 Pause 5 min avant prochain scan...\n")
            time.sleep(300)

        except KeyboardInterrupt:
            log("\n⏹️  Arret du scanner")
            break

        except Exception as e:
            log(f"❌ Erreur: {e}")
            log("⏳ Pause 60s avant retry...")
            time.sleep(60)

if __name__ == "__main__":
    main()
