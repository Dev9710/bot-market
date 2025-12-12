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
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

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

def parse_pool_data(pool: Dict, network: str = "unknown") -> Optional[Dict]:
    """Parse donnees pool GeckoTerminal."""
    try:
        attrs = pool.get("attributes", {})

        # Infos de base
        name = attrs.get("name", "Unknown")

        # Recuperer le nom complet du token (pas juste la paire)
        base_token_symbol = attrs.get("base_token_symbol", "")
        quote_token_symbol = attrs.get("quote_token_symbol", "")

        # Si on a les symboles, utiliser le base token
        if base_token_symbol:
            token_name = base_token_symbol
        else:
            # Sinon extraire du nom de la paire
            token_name = name.split("/")[0].strip() if "/" in name else name

        base_token = attrs.get("base_token_price_usd")
        price_usd = float(base_token) if base_token else 0

        # Volume et liquidite
        volume_24h = float(attrs.get("volume_usd", {}).get("h24", 0))
        liquidity = float(attrs.get("reserve_in_usd", 0))

        # Transactions et traders
        txns_24h = attrs.get("transactions", {}).get("h24", {})
        buys = txns_24h.get("buys", 0)
        sells = txns_24h.get("sells", 0)
        total_txns = buys + sells

        # Nombre de traders uniques (si disponible)
        traders_24h = txns_24h.get("buyers", 0) + txns_24h.get("sellers", 0)

        # Variation prix
        price_change_24h = float(attrs.get("price_change_percentage", {}).get("h24", 0))

        # Age du pool
        pool_created = attrs.get("pool_created_at")
        if pool_created:
            created_dt = datetime.fromisoformat(pool_created.replace('Z', '+00:00'))
            age_hours = (datetime.now().astimezone() - created_dt).total_seconds() / 3600
        else:
            age_hours = 999999  # Inconnu = tres vieux

        # Adresse du pool
        pool_address = attrs.get("address", "")

        return {
            "name": name,
            "token_name": token_name,
            "price_usd": price_usd,
            "volume_24h": volume_24h,
            "liquidity": liquidity,
            "total_txns": total_txns,
            "buys": buys,
            "sells": sells,
            "traders_24h": traders_24h,
            "price_change_24h": price_change_24h,
            "age_hours": age_hours,
            "network": network,  # Utilise le parametre passe (eth, bsc, etc.)
            "pool_address": pool_address,
        }

    except Exception as e:
        log(f"⚠️ Erreur parse pool: {e}")
        return None

def calculer_score_confiance_dex(pool_data: Dict) -> tuple[int, list]:
    """
    Calcule score de confiance 0-100 pour tokens DEX.
    Adapte des Quick Wins Binance pour le contexte DEX.

    Criteres:
    1. Liquidite (30 pts) - Plus important sur DEX (rug pull risk)
    2. Age du token (25 pts) - Nouveau mais pas trop (sweet spot 12-48h)
    3. Volume/Liquidite ratio (20 pts) - Activite organique
    4. Distribution Buy/Sell (15 pts) - Pas de pump & dump
    5. Adoption (traders) (10 pts) - Vraie communaute
    """
    score = 0
    details = []

    liq = pool_data["liquidity"]
    age = pool_data["age_hours"]
    vol_24h = pool_data["volume_24h"]
    buys = pool_data["buys"]
    sells = pool_data["sells"]
    traders = pool_data.get("traders_24h", 0)
    price_change = pool_data["price_change_24h"]

    # 1. LIQUIDITE (30 points max) - CRITIQUE pour DEX
    if liq >= 1_000_000:
        score += 30
        details.append("Liquidite excellente ($1M+)")
    elif liq >= 500_000:
        score += 25
        details.append("Liquidite tres bonne ($500K+)")
    elif liq >= 200_000:
        score += 20
        details.append("Liquidite correcte ($200K+)")
    elif liq >= 100_000:
        score += 12
        details.append("Liquidite minimale ($100K+)")
    else:
        score += 5
        details.append("Liquidite faible (risque!)")

    # 2. AGE TOKEN (25 points max) - Sweet spot 12-48h
    if 12 <= age <= 48:
        score += 25
        details.append(f"Age IDEAL ({age:.0f}h - pas rug, pas trop tard)")
    elif 6 <= age < 12:
        score += 15
        details.append(f"Tres recent ({age:.0f}h - surveiller)")
    elif age < 6:
        score -= 15
        details.append(f"TROP RECENT ({age:.0f}h - RUG RISK!)")
    elif 48 < age <= 72:
        score += 10
        details.append(f"Recent ({age:.0f}h)")
    else:
        score -= 10
        details.append(f"Trop vieux ({age:.0f}h)")

    # 3. VOLUME/LIQUIDITE RATIO (20 points max)
    vol_liq_ratio = (vol_24h / liq * 100) if liq > 0 else 0

    if 100 <= vol_liq_ratio <= 500:
        score += 20
        details.append(f"Activite organique ({vol_liq_ratio:.0f}%)")
    elif 50 <= vol_liq_ratio < 100:
        score += 15
        details.append(f"Activite correcte ({vol_liq_ratio:.0f}%)")
    elif vol_liq_ratio > 1000:
        score -= 20
        details.append(f"WASH TRADING suspect ({vol_liq_ratio:.0f}%!)")
    elif vol_liq_ratio < 50:
        score += 5
        details.append(f"Activite faible ({vol_liq_ratio:.0f}%)")

    # 4. DISTRIBUTION BUY/SELL (15 points max)
    buy_sell_ratio = buys / sells if sells > 0 else 999

    if 0.7 <= buy_sell_ratio <= 1.5:
        score += 15
        details.append("Equilibre achats/ventes sain")
    elif 0.5 <= buy_sell_ratio < 0.7 or 1.5 < buy_sell_ratio <= 2:
        score += 10
        details.append("Distribution acceptable")
    elif buy_sell_ratio > 3:
        score -= 15
        details.append("PUMP suspect (trop achats!)")
    elif buy_sell_ratio < 0.3:
        score -= 15
        details.append("DUMP en cours (trop ventes!)")

    # 5. ADOPTION (10 points max)
    if traders >= 10_000:
        score += 10
        details.append(f"Forte adoption ({traders/1000:.0f}K traders)")
    elif traders >= 5_000:
        score += 8
        details.append(f"Bonne adoption ({traders/1000:.1f}K traders)")
    elif traders >= 1_000:
        score += 5
        details.append(f"Adoption moyenne ({traders} traders)")

    # BONUS/MALUS: Prix change extremes
    if price_change > 10_000:
        score -= 25
        details.append(f"PUMP DEJA FINI (+{price_change:.0f}% = TOO LATE!)")
    elif price_change > 1_000:
        score -= 15
        details.append(f"Pump violent (+{price_change:.0f}% - risque haut)")

    # Limiter score entre 0 et 100
    score = max(0, min(100, score))

    return score, details

def is_valid_opportunity(pool_data: Dict) -> tuple[bool, str]:
    """
    Verifie si pool est une opportunite valide.
    Utilise score de confiance + filtres basiques.
    """

    # NOUVEAU: Calculer score de confiance
    score, details = calculer_score_confiance_dex(pool_data)
    pool_data['score'] = score  # Stocker pour affichage
    pool_data['score_details'] = details

    # FILTRE PRINCIPAL: Score minimum
    if score < 40:
        return False, f"❌ Score trop faible: {score}/100 ({details[0] if details else 'multiples problemes'})"

    # Check liquidite min (anti rug pull) - Garde pour securite
    if pool_data["liquidity"] < MIN_LIQUIDITY_USD:
        return False, f"❌ Liquidite trop faible: ${pool_data['liquidity']:,.0f}"

    # Check volume min
    if pool_data["volume_24h"] < MIN_VOLUME_24H_USD:
        return False, f"⚠️ Volume trop faible: ${pool_data['volume_24h']:,.0f}"

    # Check transactions min
    if pool_data["total_txns"] < MIN_TXNS_24H:
        return False, f"⚠️ Pas assez de txns: {pool_data['total_txns']}"

    # FILTRE STRICT: Pump deja fini (>10,000%)
    if pool_data["price_change_24h"] > 10_000:
        return False, f"🚨 PUMP DEJA FINI: +{pool_data['price_change_24h']:.0f}% (TOO LATE!)"

    # FILTRE STRICT: Token trop recent (<6h = rug pull risk)
    if pool_data["age_hours"] < 6:
        return False, f"🚨 TROP RECENT: {pool_data['age_hours']:.1f}h (RUG RISK 90%!)"

    # FILTRE STRICT: Wash trading suspect (vol/liq > 1000%)
    vol_liq_ratio = (pool_data["volume_24h"] / pool_data["liquidity"] * 100) if pool_data["liquidity"] > 0 else 0
    if vol_liq_ratio > 1000:
        return False, f"🚨 WASH TRADING: Vol/Liq {vol_liq_ratio:.0f}% (faux volume!)"

    return True, f"✅ Score: {score}/100"

def generer_alerte_dex(pool_data: Dict) -> str:
    """Genere alerte CONCISE avec emojis (meme format que Binance)."""

    name = pool_data["name"]
    token_name = pool_data.get("token_name", name.split("/")[0])
    price = pool_data["price_usd"]
    vol_24h = pool_data["volume_24h"]
    liq = pool_data["liquidity"]
    pct_24h = pool_data["price_change_24h"]
    age = pool_data["age_hours"]
    txns = pool_data["total_txns"]
    buys = pool_data["buys"]
    sells = pool_data["sells"]
    traders = pool_data.get("traders_24h", 0)
    network_id = pool_data["network"]

    # Mapper les IDs de réseau vers des noms lisibles
    network_names = {
        "eth": "Ethereum",
        "bsc": "BSC (Binance Smart Chain)",
        "polygon": "Polygon",
        "arbitrum": "Arbitrum",
        "base": "Base",
        "solana": "Solana",
        "optimism": "Optimism",
        "avalanche": "Avalanche"
    }
    blockchain = network_names.get(network_id, network_id.upper() if network_id != "unknown" else "Non identifié")

    ratio_vol_liq = vol_24h / liq if liq > 0 else 0

    # Calculer variation volume (approximation)
    vol_avg = liq * 0.5  # Estimation volume moyen = 50% liquidite
    vol_change_pct = ((vol_24h - vol_avg) / vol_avg * 100) if vol_avg > 0 else 0

    # Recuperer score et details
    score = pool_data.get('score', 0)
    score_details = pool_data.get('score_details', [])

    # Alerte concise avec SCORE
    txt = f"\n🆕 *NOUVEAU TOKEN DEX*\n"
    txt += f"━━━━━━━━━━━━━━━━\n"
    txt += f"💎 {token_name}\n"
    txt += f"   Paire: {name}\n"
    txt += f"⛓️ Blockchain: {blockchain}\n\n"

    # AFFICHER SCORE DE CONFIANCE
    if score >= 80:
        txt += f"🎯 *SCORE: {score}/100* ⭐⭐⭐ EXCELLENT\n"
        txt += f"   💡 Token tres fiable pour DEX\n\n"
    elif score >= 60:
        txt += f"🎯 *SCORE: {score}/100* ⭐⭐ BON\n"
        txt += f"   💡 Opportunite interessante\n\n"
    elif score >= 40:
        txt += f"🎯 *SCORE: {score}/100* ⭐ MOYEN\n"
        txt += f"   ⚠️ Risque moyen - Prudence\n\n"
    else:
        txt += f"🎯 *SCORE: {score}/100* ⚠️ FAIBLE\n"
        txt += f"   ❌ Risque eleve - A eviter\n\n"

    # Top 3 raisons du score
    if score_details:
        txt += f"📋 Raisons du score:\n"
        for detail in score_details[:3]:
            txt += f"   • {detail}\n"
        txt += f"\n"
    txt += f"💰 Prix: ${price:.8f} ({pct_24h:+.1f}% 24h)\n"
    txt += f"📊 Vol 24h: ${vol_24h/1000:.0f}K ({vol_change_pct:+.0f}%)\n"

    if traders > 0:
        txt += f"👥 Traders: {traders/1000:.1f}K\n"

    txt += f"💧 Liquidite: ${liq/1000:.0f}K\n"
    txt += f"⏰ Age: {age:.0f}h\n"
    txt += f"🔄 Txns: {txns} (A:{buys} V:{sells})\n\n"

    txt += f"🔍 *ANALYSE:*\n"

    # Analyse volume
    if vol_change_pct >= 200:
        txt += f"🔥 Volume EXPLOSIF +{vol_change_pct:.0f}%!\n"
    elif vol_change_pct >= 100:
        txt += f"📈 Forte hausse volume +{vol_change_pct:.0f}%\n"

    # Analyse liquidite
    if liq >= 200000:
        txt += f"✅ Liquidite solide (${liq/1000:.0f}K)\n"
    elif liq >= 100000:
        txt += f"⚠️ Liquidite moyenne (${liq/1000:.0f}K)\n"
    else:
        txt += f"⚠️ Liquidite faible - PRUDENCE!\n"

    # Analyse traders (adoption organique)
    if traders > 0:
        avg_vol_per_trader = vol_24h / traders if traders > 0 else 0
        if traders >= 1000 and avg_vol_per_trader < 500:
            txt += f"✅ Bonne adoption ({traders/1000:.1f}K traders)\n"
        elif traders >= 500:
            txt += f"📊 Adoption moyenne ({traders/1000:.1f}K traders)\n"
        elif traders < 100 and vol_24h > 100000:
            txt += f"⚠️ Peu de traders ({traders}) + gros volume = Whales?\n"

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

    txt += f"\n🔗 https://geckoterminal.com/{network_id}/pools/{pool_data['pool_address']}\n"

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
                pool_data = parse_pool_data(pool, network)  # Passer le network

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
                pool_data = parse_pool_data(pool, network)  # Passer le network

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
