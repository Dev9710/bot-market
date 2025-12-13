"""
GeckoTerminal Scanner V2 - Detection tokens DEX avec analyse avancée
Nouvelles fonctionnalités:
- Multi-pool correlation (même token sur plusieurs pools)
- Momentum multi-timeframe (1h, 3h, 6h, 24h)
- Traders spike detection
- Buy/Sell pressure evolution
- Scoring dynamique avec bonus momentum
- Alertes ACCELERATION
- Résistance/Support detection
- Alertes reformatées ultra-complètes
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# UTF-8 pour emojis Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (ValueError, AttributeError):
            pass

# ============================================
# CONFIGURATION
# ============================================
GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Réseaux à surveiller
NETWORKS = ["eth", "bsc", "arbitrum", "base", "solana"]

# Seuils de détection
MIN_LIQUIDITY_USD = 200000      # Liquidité min (sécurité)
MIN_VOLUME_24H_USD = 100000     # Volume 24h min
MIN_TXNS_24H = 100              # Nb transactions min
MAX_TOKEN_AGE_HOURS = 72        # Max 3 jours
VOLUME_LIQUIDITY_RATIO = 0.5    # Vol24h/Liquidité > 50%

# Seuils pour signaux avancés
TRADERS_SPIKE_THRESHOLD = 0.5   # +50% traders
BUY_RATIO_THRESHOLD = 0.8       # 80% buy ratio
BUY_RATIO_CHANGE_THRESHOLD = 0.15  # +15% variation
ACCELERATION_THRESHOLD = 0.05   # +5% en 1h
VOLUME_SPIKE_THRESHOLD = 0.5    # +50% volume

# Cooldown et limites
COOLDOWN_SECONDS = 1800
MAX_ALERTS_PER_SCAN = 5

# ============================================
# CACHE SIMPLIFIÉ
# ============================================
# On garde seulement buy_ratio history (pas fourni par API)
buy_ratio_history = defaultdict(lambda: defaultdict(list))

# Multi-pool tracking
token_pools = defaultdict(list)  # [base_token] = [pool_data, pool_data, ...]
alert_cooldown = {}

# ============================================
# UTILITAIRES
# ============================================
# Mapping des networks pour affichage lisible
NETWORK_NAMES = {
    "eth": "Ethereum",
    "bsc": "BSC (Binance Smart Chain)",
    "arbitrum": "Arbitrum",
    "base": "Base",
    "solana": "Solana",
    "polygon": "Polygon",
    "avalanche": "Avalanche",
    "optimism": "Optimism",
    "fantom": "Fantom",
}

def get_network_display_name(network_id: str) -> str:
    """Convertit ID network en nom lisible."""
    return NETWORK_NAMES.get(network_id.lower(), network_id.upper())

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

def extract_base_token(pool_name: str) -> str:
    """Extrait le nom du base token depuis le nom du pool."""
    # Ex: "LAVA / USDT 0.01%" -> "LAVA"
    if "/" in pool_name:
        return pool_name.split("/")[0].strip()
    return pool_name.strip()

def check_cooldown(alert_key: str) -> bool:
    """Vérifie si alerte en cooldown."""
    now = time.time()
    if alert_key in alert_cooldown:
        elapsed = now - alert_cooldown[alert_key]
        if elapsed < COOLDOWN_SECONDS:
            return False
    alert_cooldown[alert_key] = now
    return True

# ============================================
# API CALLS
# ============================================
def get_trending_pools(network: str, page: int = 1) -> Optional[List[Dict]]:
    """Récupère pools trending sur un réseau."""
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
    """Récupère nouveaux pools sur un réseau."""
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

# ============================================
# PARSING & ENRICHISSEMENT
# ============================================
def parse_pool_data(pool: Dict, network: str = "unknown") -> Optional[Dict]:
    """Parse données pool GeckoTerminal avec enrichissements."""
    try:
        attrs = pool.get("attributes", {})

        # Infos de base
        name = attrs.get("name", "Unknown")
        base_token_name = extract_base_token(name)
        base_token_price = attrs.get("base_token_price_usd")
        price_usd = float(base_token_price) if base_token_price else 0

        # Volume et liquidité (protéger contre None)
        volume_usd_data = attrs.get("volume_usd", {}) or {}
        volume_24h = float(volume_usd_data.get("h24") or 0)
        volume_6h = float(volume_usd_data.get("h6") or 0)
        volume_1h = float(volume_usd_data.get("h1") or 0)
        liquidity = float(attrs.get("reserve_in_usd") or 0)

        # Transactions (protéger contre None)
        transactions_data = attrs.get("transactions", {}) or {}
        txns_24h = transactions_data.get("h24", {}) or {}
        txns_6h = transactions_data.get("h6", {}) or {}
        txns_1h = transactions_data.get("h1", {}) or {}

        buys_24h = txns_24h.get("buys", 0)
        sells_24h = txns_24h.get("sells", 0)
        buys_6h = txns_6h.get("buys", 0)
        sells_6h = txns_6h.get("sells", 0)
        buys_1h = txns_1h.get("buys", 0)
        sells_1h = txns_1h.get("sells", 0)

        total_txns = buys_24h + sells_24h

        # Variations prix (multi-timeframe depuis API) - Protéger contre None
        price_changes = attrs.get("price_change_percentage", {}) or {}
        price_change_24h = float(price_changes.get("h24") or 0)
        price_change_6h = float(price_changes.get("h6") or 0)
        price_change_1h = float(price_changes.get("h1") or 0)

        # Age du pool
        pool_created = attrs.get("pool_created_at")
        if pool_created:
            created_dt = datetime.fromisoformat(pool_created.replace('Z', '+00:00'))
            age_hours = (datetime.now().astimezone() - created_dt).total_seconds() / 3600
        else:
            age_hours = 999999

        # Réseau et adresse - Utiliser le paramètre network passé directement
        # On garde le network passé en paramètre (fourni lors de l'appel de l'API)
        # Si ce n'était pas fourni, on essaie de l'extraire des relationships
        if network == "unknown":
            relationships = pool.get("relationships", {}) or {}
            network_data = relationships.get("network", {}) or {}
            network_inner = network_data.get("data", {}) or {}
            network = network_inner.get("id", "unknown")

            # Si network toujours unknown, essayer de l'extraire du type
            if network == "unknown":
                pool_type = pool.get("type", "")
                # Format peut être "pool" ou "network-name-pool"
                if "-" in pool_type:
                    network = pool_type.split("-")[0]

        pool_address = attrs.get("address", "")

        # FDV et Market Cap (protéger contre None)
        fdv_usd = float(attrs.get("fdv_usd") or 0)
        market_cap_usd = float(attrs.get("market_cap_usd") or 0)

        return {
            "name": name,
            "base_token_name": base_token_name,
            "price_usd": price_usd,
            "volume_24h": volume_24h,
            "volume_6h": volume_6h,
            "volume_1h": volume_1h,
            "liquidity": liquidity,
            "total_txns": total_txns,
            "buys_24h": buys_24h,
            "sells_24h": sells_24h,
            "buys_6h": buys_6h,
            "sells_6h": sells_6h,
            "buys_1h": buys_1h,
            "sells_1h": sells_1h,
            "price_change_24h": price_change_24h,
            "price_change_6h": price_change_6h,
            "price_change_1h": price_change_1h,
            "age_hours": age_hours,
            "network": network,
            "pool_address": pool_address,
            "fdv_usd": fdv_usd,
            "market_cap_usd": market_cap_usd,
        }
    except Exception as e:
        log(f"⚠️ Erreur parse pool: {e}")
        return None

# ============================================
# HISTORIQUE BUY RATIO (SIMPLIFIÉ)
# ============================================
def update_buy_ratio_history(pool_data: Dict):
    """Met à jour seulement l'historique buy ratio (pas fourni par API)."""
    base_token = pool_data["base_token_name"]
    pool_addr = pool_data["pool_address"]
    now = time.time()

    # Buy ratio 24h
    buy_ratio = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0
    buy_ratio_history[base_token][pool_addr].append((now, buy_ratio))

    # Nettoyer historique (garder 2h seulement - on a besoin que de 1h)
    cutoff = now - 7200  # 2h
    buy_ratio_history[base_token][pool_addr] = [
        (t, v) for t, v in buy_ratio_history[base_token][pool_addr] if t > cutoff
    ]

def get_buy_ratio_change(base_token: str, pool_addr: str) -> Optional[float]:
    """Calcule variation buy ratio sur 1h."""
    hist = buy_ratio_history[base_token][pool_addr]

    if not hist or len(hist) < 2:
        return None

    now = time.time()
    one_hour_ago = now - 3600  # 1h

    # Trouver valeur la plus proche d'il y a 1h
    past_values = [v for t, v in hist if t < one_hour_ago]
    if not past_values:
        return None

    past = past_values[-1]  # Plus récente valeur avant 1h
    current = hist[-1][1]

    if past == 0:
        return None

    return ((current - past) / past) * 100

def get_price_momentum_from_api(pool_data: Dict) -> Dict[str, Optional[float]]:
    """
    SIMPLIFIÉ: Utilise directement les données de l'API au lieu de recalculer.
    GeckoTerminal fournit déjà price_change_1h, price_change_6h !
    """
    return {
        "1h": pool_data.get("price_change_1h"),
        "3h": None,  # Pas fourni par API, on estime
        "6h": pool_data.get("price_change_6h"),
    }

def find_resistance_simple(pool_data: Dict) -> Dict:
    """
    SIMPLIFIÉ: Résistance basée sur prix actuel et variation.
    Pour une vraie résistance, il faudrait un historique long-terme.
    """
    # Résistance simple = prix actuel + 10% (estimation conservative)
    current_price = pool_data["price_usd"]

    # Si prix en hausse forte (>20% sur 24h), résistance proche
    if pool_data["price_change_24h"] > 20:
        resistance = current_price * 1.05  # +5% seulement
    else:
        resistance = current_price * 1.10  # +10%

    resistance_dist_pct = ((resistance - current_price) / current_price) * 100

    return {
        "resistance": resistance,
        "support": None,  # Pas calculé pour simplifier
        "resistance_dist_pct": resistance_dist_pct,
    }

# ============================================
# MULTI-POOL CORRELATION
# ============================================
def group_pools_by_token(all_pools: List[Dict]) -> Dict[str, List[Dict]]:
    """Regroupe pools par base token."""
    grouped = defaultdict(list)
    for pool in all_pools:
        base_token = pool["base_token_name"]
        grouped[base_token].append(pool)
    return grouped

def analyze_multi_pool(pools: List[Dict]) -> Dict:
    """Analyse activité cross-pool d'un token."""
    if len(pools) <= 1:
        return {"is_multi_pool": False}

    total_volume = sum(p["volume_24h"] for p in pools)
    total_liquidity = sum(p["liquidity"] for p in pools)

    # Identifier pool dominant
    pools_sorted = sorted(pools, key=lambda x: x["volume_24h"], reverse=True)
    dominant_pool = pools_sorted[0]

    # Type de pool dominant (USDT, WETH, etc)
    dominant_pair = dominant_pool["name"].split("/")[1].strip().split()[0] if "/" in dominant_pool["name"] else "Unknown"

    # Vol/Liq par pool
    pool_activities = []
    for p in pools:
        vol_liq = (p["volume_24h"] / p["liquidity"] * 100) if p["liquidity"] > 0 else 0
        pair_name = p["name"].split("/")[1].strip().split()[0] if "/" in p["name"] else "Unknown"
        pool_activities.append({
            "pair": pair_name,
            "vol_liq_pct": vol_liq,
            "volume": p["volume_24h"],
        })

    # Signal bullish si WETH > USDT
    is_bullish = False
    weth_activity = next((p for p in pool_activities if "WETH" in p["pair"] or "ETH" in p["pair"]), None)
    usdt_activity = next((p for p in pool_activities if "USDT" in p["pair"] or "USDC" in p["pair"]), None)

    if weth_activity and usdt_activity:
        if weth_activity["vol_liq_pct"] > usdt_activity["vol_liq_pct"]:
            is_bullish = True

    return {
        "is_multi_pool": True,
        "num_pools": len(pools),
        "total_volume": total_volume,
        "total_liquidity": total_liquidity,
        "dominant_pair": dominant_pair,
        "pool_activities": pool_activities,
        "is_weth_dominant": is_bullish,
    }

# ============================================
# SCORING DYNAMIQUE
# ============================================
def calculate_base_score(pool_data: Dict) -> int:
    """
    Score de base DYNAMIQUE (fondamentaux) avec pénalités.
    Corrigé pour ALMANAK: score ne doit plus monter pendant une chute.
    """
    score = 0

    # Liquidité (max 30 points)
    liq = pool_data["liquidity"]
    if liq >= 1000000:
        score += 30
    elif liq >= 500000:
        score += 25
    elif liq >= 200000:
        score += 20
    elif liq >= 100000:
        score += 15
    elif liq >= 50000:
        score += 10

    # Volume (max 20 points)
    vol = pool_data["volume_24h"]
    if vol >= 1000000:
        score += 20
    elif vol >= 500000:
        score += 15
    elif vol >= 200000:
        score += 10
    elif vol >= 100000:
        score += 5

    # Age (max 20 points)
    age = pool_data["age_hours"]
    if 24 <= age <= 72:
        score += 20  # Sweet spot
    elif age < 24:
        score += 10  # Très récent (risqué)
    elif 72 < age <= 168:
        score += 10  # Une semaine

    # Vol/Liq ratio (max 15 points)
    vol_liq = (vol / liq) if liq > 0 else 0
    if 0.5 <= vol_liq <= 1.5:
        score += 15  # Sweet spot
    elif 0.3 <= vol_liq < 0.5 or 1.5 < vol_liq <= 2.0:
        score += 10
    elif vol_liq > 2.0:
        score += 5  # Trop actif (pump?)

    # Buy/Sell balance (max 15 points)
    buy_ratio = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0
    if 0.6 <= buy_ratio <= 1.4:
        score += 15  # Équilibré
    elif 0.4 <= buy_ratio < 0.6 or 1.4 < buy_ratio <= 2.0:
        score += 10
    elif buy_ratio < 0.4 or buy_ratio > 2.0:
        score += 5  # Déséquilibré

    # === NOUVELLES PÉNALITÉS DYNAMIQUES (Correction ALMANAK) ===

    # PÉNALITÉ 1: Tendance baissière 24h (CRITIQUE)
    price_change_24h = pool_data.get("price_change_24h", 0)
    if price_change_24h < -40:
        score -= 35  # Crash massif (-45% comme ALMANAK)
    elif price_change_24h < -30:
        score -= 25  # Chute sévère
    elif price_change_24h < -20:
        score -= 15  # Chute importante
    elif price_change_24h < -10:
        score -= 8   # Baisse modérée

    # PÉNALITÉ 2: Pression vendeuse massive 24h (CRITIQUE)
    total_txns_24h = pool_data["buys_24h"] + pool_data["sells_24h"]
    if total_txns_24h > 0:
        sell_pressure_24h = pool_data["sells_24h"] / total_txns_24h
        if sell_pressure_24h > 0.70:  # >70% ventes (cas ALMANAK: 63-68%)
            score -= 25
        elif sell_pressure_24h > 0.65:  # >65% ventes
            score -= 20
        elif sell_pressure_24h > 0.60:  # >60% ventes
            score -= 12

    # PÉNALITÉ 3: Liquidité en chute (risque rug pull)
    # Note: Nécessiterait historique liquidité, simulé via Vol/Liq ratio anormal
    if vol_liq > 3.0:  # Activité excessive = possiblement liquidité qui fond
        score -= 10

    return max(score, 0)  # Ne jamais descendre sous 0

def calculate_momentum_bonus(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> int:
    """
    Bonus momentum INTELLIGENT (dynamique actuelle).
    Corrigé pour ALMANAK: distingue bon spike (accumulation) vs mauvais spike (panic sell).
    """
    bonus = 0

    # === Prix 1h (max 15 points) ===
    price_1h = momentum.get("1h", 0)
    price_6h = pool_data.get("price_change_6h", 0)
    price_24h = pool_data.get("price_change_24h", 0)

    if price_1h >= 10:
        bonus += 15
    elif price_1h >= 5:
        bonus += 10
    elif price_1h >= 2:
        bonus += 5

    # === DÉTECTION DEAD CAT BOUNCE (Correction ALMANAK) ===
    # Rebond 1h positif MAIS tendance 24h très négative = piège
    if price_1h > 0 and price_24h < -20:
        # Dead cat bounce détecté
        if price_1h < 10:  # Petit rebond sur grosse chute
            bonus -= 10  # PÉNALITÉ au lieu de bonus!
        # Si rebond >10%, on garde le bonus mais on avertira dans les signaux

    # === Volume Spike: BON ou MAUVAIS? ===
    txn_1h = pool_data["buys_1h"] + pool_data["sells_1h"]
    txn_24h = pool_data["total_txns"]

    if txn_24h > 0:
        txn_1h_normalized = txn_1h * 24  # Normaliser sur 24h
        has_volume_spike = txn_1h_normalized > txn_24h * 1.5  # +50% activité

        if has_volume_spike:
            # Spike + Prix hausse = BON (accumulation)
            if price_1h > 3:
                bonus += 10
            # Spike + Prix stable/léger hausse = NEUTRE
            elif price_1h > 0:
                bonus += 5
            # Spike + Prix chute = MAUVAIS (panic sell)
            elif price_1h < -5:
                bonus -= 10  # PÉNALITÉ pour panic sell
            # Spike + Prix léger baisse = vigilance
            else:
                bonus += 0  # Pas de bonus ni pénalité
        elif txn_1h_normalized > txn_24h * 1.2:
            # Activité modérée
            if price_1h > 0:
                bonus += 5

    # === Buy Pressure 1h (max 10 points) ===
    buy_ratio_1h = pool_data["buys_1h"] / pool_data["sells_1h"] if pool_data["sells_1h"] > 0 else 1.0
    buy_ratio_24h = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0

    # Buy ratio 1h DOIT être comparé au ratio 24h
    if buy_ratio_1h >= 1.2:  # Forte dominance acheteurs
        bonus += 10
    elif buy_ratio_1h >= 1.0:  # Léger avantage acheteurs
        bonus += 8
    elif buy_ratio_1h >= 0.8:  # Équilibre
        bonus += 5
    elif buy_ratio_1h < 0.5 and buy_ratio_24h < 0.5:
        # Vendeurs dominent 1h ET 24h = très mauvais
        bonus -= 5

    # === Multi-pool (max 10 points) ===
    if multi_pool_data.get("is_multi_pool"):
        bonus += 5
        if multi_pool_data.get("is_weth_dominant"):
            bonus += 5

    # === CORRECTION CONTEXTE GLOBAL ===
    # Si price_24h très négatif, limiter le momentum bonus max
    if price_24h < -30:
        bonus = min(bonus, 10)  # Max 10 points si token en crash
    elif price_24h < -20:
        bonus = min(bonus, 15)  # Max 15 points si token en chute

    return max(min(bonus, 30), -20)  # Max +30, Min -20

def calculate_final_score(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> Tuple[int, int, int]:
    """Score final = base + momentum."""
    base = calculate_base_score(pool_data)
    momentum_bonus = calculate_momentum_bonus(pool_data, momentum, multi_pool_data)
    final = max(min(base + momentum_bonus, 100), 0)  # Entre 0 et 100
    return final, base, momentum_bonus

def calculate_confidence_score(pool_data: Dict) -> int:
    """
    Calcule niveau de confiance dans les données (0-100%).
    Corrigé pour ALMANAK: ajout indicateur fiabilité.
    """
    confidence = 100

    # Réduire confiance si données incomplètes
    if pool_data.get("network", "").lower() == "unknown":
        confidence -= 20  # Données réseau manquantes

    # Réduire confiance si liquidité faible = données moins stables
    liq = pool_data.get("liquidity", 0)
    if liq < 200000:
        confidence -= 20  # Liquidité trop faible
    elif liq < 300000:
        confidence -= 10  # Liquidité moyenne-faible

    # Réduire confiance si trop récent = historique limité
    age = pool_data.get("age_hours", 999)
    if age < 6:
        confidence -= 20  # Moins de 6h = très peu d'historique
    elif age < 12:
        confidence -= 10  # Moins de 12h = historique limité

    # Réduire confiance si volume très faible
    vol = pool_data.get("volume_24h", 0)
    if vol < 100000:
        confidence -= 15  # Volume faible = données peu significatives

    # Réduire confiance si transactions trop peu nombreuses
    txns = pool_data.get("total_txns", 0)
    if txns < 200:
        confidence -= 10  # Peu de transactions = données peu représentatives

    return max(confidence, 0)

# ============================================
# DÉTECTION SIGNAUX
# ============================================
def detect_signals(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> List[str]:
    """
    Détecte tous les signaux importants.
    Corrigé pour ALMANAK: ajoute warnings pour dead cat bounce et panic sell.
    """
    signals = []

    price_1h = momentum.get("1h", 0)
    price_6h = pool_data.get("price_change_6h", 0)
    price_24h = pool_data.get("price_change_24h", 0)

    buy_ratio_1h = pool_data["buys_1h"] / pool_data["sells_1h"] if pool_data["sells_1h"] > 0 else 1.0
    buy_ratio_24h = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0

    # === DEAD CAT BOUNCE WARNING (NOUVEAU - Correction ALMANAK) ===
    if price_1h > 0 and price_24h < -20:
        if price_1h < 10:
            signals.append(f"⚠️ DEAD CAT BOUNCE: Rebond +{price_1h:.1f}% sur tendance baissière {price_24h:.1f}%")
        else:
            signals.append(f"⚠️ REVERSAL FRAGILE: Rebond fort (+{price_1h:.1f}%) mais tendance 24h négative ({price_24h:.1f}%)")

    # ACCELERATION (seulement si pas dead cat bounce)
    elif price_1h >= 5:
        signals.append(f"🚀 ACCELERATION: +{price_1h:.1f}% en 1h")

    # REVERSAL (uniquement si contexte positif)
    if price_24h < -10 and price_1h > 3 and price_6h > 0:
        # Reversal confirmé si 6h aussi positif
        signals.append(f"📈 REVERSAL CONFIRMÉ: Hausse 1h/6h malgré {price_24h:.1f}% 24h")
    elif price_24h < -10 and price_1h > 5:
        # Reversal possible mais non confirmé
        signals.append(f"📈 REVERSAL: Hausse malgré {price_24h:.1f}% 24h (confirmation nécessaire)")

    # === VOLUME SPIKE: QUALIFIÉ (NOUVEAU) ===
    vol_1h_normalized = pool_data["volume_1h"] * 24
    if vol_1h_normalized > pool_data["volume_24h"] * 1.5:
        spike_pct = ((vol_1h_normalized / pool_data["volume_24h"]) - 1) * 100

        # Qualifier le spike
        if price_1h > 3:
            signals.append(f"📊 VOLUME SPIKE BULLISH: +{spike_pct:.0f}% activité + prix hausse")
        elif price_1h < -5:
            signals.append(f"🚨 VOLUME SPIKE BEARISH: +{spike_pct:.0f}% activité = panic sell détecté")
        else:
            signals.append(f"📊 VOLUME SPIKE: +{spike_pct:.0f}% activité vs moyenne")

    # === BUY PRESSURE (AMÉLIORÉ) ===
    if buy_ratio_1h > buy_ratio_24h * 1.2 and buy_ratio_1h >= 0.8:
        signals.append(f"🟢 BUY PRESSURE: Ratio 1h ({buy_ratio_1h:.2f}) > 24h ({buy_ratio_24h:.2f})")
    elif buy_ratio_1h < buy_ratio_24h * 0.8 and buy_ratio_24h < 0.5:
        # SELL PRESSURE warning (NOUVEAU)
        signals.append(f"🔴 SELL PRESSURE: Vendeurs intensifient (1h: {buy_ratio_1h:.2f}, 24h: {buy_ratio_24h:.2f})")

    # MULTI-POOL
    if multi_pool_data.get("is_multi_pool"):
        signals.append(f"🌐 MULTI-POOL: {multi_pool_data['num_pools']} pools actifs")
        if multi_pool_data.get("is_weth_dominant"):
            signals.append(f"⚡ WETH pool dominant = Smart money")

    # === BOTTOM CONFIRMÉ (AMÉLIORÉ - plus strict) ===
    # Bottom = prix bas + acheteurs reviennent + pression change
    if price_24h < -15 and price_1h > 0 and buy_ratio_1h > buy_ratio_24h * 1.3 and buy_ratio_1h > 0.9:
        signals.append(f"✅ BOTTOM CONFIRMÉ: Acheteurs reviennent massivement")
    elif price_24h < -10 and price_1h > 3 and price_6h > 0:
        signals.append(f"✅ Bottom potentiel: Reversal multi-timeframe")

    return signals

# ============================================
# VALIDATION OPPORTUNITÉ
# ============================================
def is_valid_opportunity(pool_data: Dict, score: int) -> Tuple[bool, str]:
    """Vérifie si pool est une opportunité valide."""

    # Check liquidité min
    if pool_data["liquidity"] < MIN_LIQUIDITY_USD:
        return False, f"❌ Liquidité trop faible: ${pool_data['liquidity']:,.0f}"

    # Check volume min
    if pool_data["volume_24h"] < MIN_VOLUME_24H_USD:
        return False, f"⚠️ Volume trop faible: ${pool_data['volume_24h']:,.0f}"

    # Check transactions min
    if pool_data["total_txns"] < MIN_TXNS_24H:
        return False, f"⚠️ Pas assez de txns: {pool_data['total_txns']}"

    # Check age
    if pool_data["age_hours"] > MAX_TOKEN_AGE_HOURS:
        return False, f"⏳ Token trop ancien: {pool_data['age_hours']:.0f}h"

    # Check score minimum
    if score < 55:
        return False, f"📉 Score trop faible: {score}/100"

    # Check ratio volume/liquidité
    ratio = pool_data["volume_24h"] / pool_data["liquidity"] if pool_data["liquidity"] > 0 else 0
    if ratio < VOLUME_LIQUIDITY_RATIO:
        return False, f"📉 Ratio Vol/Liq trop faible: {ratio:.1%}"

    # Check pump & dump potentiel
    buy_sell_ratio = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 999
    if buy_sell_ratio > 5:
        return False, f"🚨 Trop d'achats vs ventes (pump?): {buy_sell_ratio:.1f}"
    if buy_sell_ratio < 0.2:
        return False, f"📉 Trop de ventes vs achats (dump?): {buy_sell_ratio:.1f}"

    return True, "✅ Opportunité valide"

# ============================================
# GÉNÉRATION ALERTE COMPLÈTE
# ============================================
def generer_alerte_complete(pool_data: Dict, score: int, base_score: int, momentum_bonus: int,
                            momentum: Dict, multi_pool_data: Dict, signals: List[str],
                            resistance_data: Dict) -> str:
    """Génère alerte ultra-complète avec toutes les données."""

    name = pool_data["name"]
    base_token = pool_data["base_token_name"]
    price = pool_data["price_usd"]
    vol_24h = pool_data["volume_24h"]
    vol_6h = pool_data["volume_6h"]
    vol_1h = pool_data["volume_1h"]
    liq = pool_data["liquidity"]
    pct_24h = pool_data["price_change_24h"]
    pct_6h = pool_data["price_change_6h"]
    pct_1h = pool_data["price_change_1h"]
    age = pool_data["age_hours"]
    txns = pool_data["total_txns"]
    buys = pool_data["buys_24h"]
    sells = pool_data["sells_24h"]
    buys_1h = pool_data["buys_1h"]
    sells_1h = pool_data["sells_1h"]
    network_id = pool_data["network"]  # ID original pour le lien
    network_display = get_network_display_name(network_id)  # Nom lisible pour affichage
    ratio_vol_liq = (vol_24h / liq * 100) if liq > 0 else 0
    buy_ratio_24h = buys / sells if sells > 0 else 1.0
    buy_ratio_1h = buys_1h / sells_1h if sells_1h > 0 else 1.0

    # Emojis score
    if score >= 80:
        score_emoji = "⭐️⭐️⭐️⭐️"
        score_label = "EXCELLENT"
    elif score >= 70:
        score_emoji = "⭐️⭐️⭐️"
        score_label = "TRÈS BON"
    elif score >= 60:
        score_emoji = "⭐️⭐️"
        score_label = "BON"
    elif score >= 50:
        score_emoji = "⭐️"
        score_label = "MOYEN"
    else:
        score_emoji = ""
        score_label = "FAIBLE"

    # ========== CONSTRUCTION ALERTE ==========
    txt = f"\n🆕 *NOUVEAU TOKEN DEX*\n"
    txt += f"━━━━━━━━━━━━━━━━\n"
    txt += f"💎 {name}\n"
    txt += f"⛓️ Blockchain: {network_display}\n\n"

    # SCORE + CONFIANCE (NOUVEAU)
    confidence = calculate_confidence_score(pool_data)
    txt += f"🎯 *SCORE: {score}/100 {score_emoji} {score_label}*\n"
    txt += f"   Base: {base_score} | Momentum: {momentum_bonus:+d}\n"
    txt += f"📊 Confiance: {confidence}% (fiabilité données)\n\n"

    # PRIX & MOMENTUM
    txt += f"━━━ PRIX & MOMENTUM ━━━\n"
    txt += f"💰 Prix: ${price:.8f}\n"

    # Multi-timeframe
    txt += f"📊 "
    txt += f"24h: {pct_24h:+.1f}% "
    if pct_6h != 0:
        txt += f"| 6h: {pct_6h:+.1f}% "
    if pct_1h != 0:
        emoji_1h = "🚀" if pct_1h > 5 else ("🟢" if pct_1h > 0 else "🔴")
        txt += f"| 1h: {pct_1h:+.1f}% {emoji_1h}"
    txt += "\n"

    # Momentum calculé (historique)
    if any(momentum.values()):
        txt += f"📈 Momentum: "
        parts = []
        if momentum.get("1h") is not None:
            parts.append(f"1h {momentum['1h']:+.1f}%")
        if momentum.get("3h") is not None:
            parts.append(f"3h {momentum['3h']:+.1f}%")
        if momentum.get("6h") is not None:
            parts.append(f"6h {momentum['6h']:+.1f}%")
        txt += " | ".join(parts) + "\n"

    # Résistance
    if resistance_data.get("resistance"):
        txt += f"🎯 Résistance: ${resistance_data['resistance']:.8f} "
        txt += f"(+{resistance_data['resistance_dist_pct']:.1f}%)\n"

    txt += "\n"

    # ACTIVITÉ
    txt += f"━━━ ACTIVITÉ ━━━\n"
    txt += f"📊 Vol 24h: ${vol_24h/1000:.0f}K\n"

    # Volume spike ?
    if vol_1h > 0:
        vol_1h_normalized = vol_1h * 24
        if vol_1h_normalized > vol_24h * 1.3:
            spike = ((vol_1h_normalized / vol_24h) - 1) * 100
            txt += f"⚡ Vol 1h: ${vol_1h/1000:.0f}K (x{vol_1h_normalized/vol_24h:.1f} activité!) 🔥\n"
        else:
            txt += f"📉 Vol 1h: ${vol_1h/1000:.0f}K\n"

    txt += f"💧 Liquidité: ${liq/1000:.0f}K\n"

    # Transactions 24h - Format explicite avec estimation traders (NOUVEAU)
    txt += f"🔄 Transactions 24h: {txns}\n"
    # Estimation traders: moyenne 2-3 tx par trader
    traders_estimate = int(txns / 2.5)  # Estimation conservative
    txt += f"👥 Traders estimés: ~{traders_estimate} (basé sur txns)\n"
    buys_pct = (buys / txns * 100) if txns > 0 else 0
    sells_pct = (sells / txns * 100) if txns > 0 else 0
    txt += f"   🟢 ACHATS: {buys} ({buys_pct:.0f}%)\n"
    txt += f"   🔴 VENTES: {sells} ({sells_pct:.0f}%)\n"

    # Pression dominante
    if buy_ratio_24h >= 1.0:
        txt += f"   ⚖️ Pression: ACHETEURS dominent (ratio {buy_ratio_24h:.2f})\n"
    elif buy_ratio_24h >= 0.8:
        txt += f"   ⚖️ Pression: ÉQUILIBRÉE (ratio {buy_ratio_24h:.2f})\n"
    else:
        txt += f"   ⚖️ Pression: VENDEURS dominent (ratio {buy_ratio_24h:.2f})\n"

    # Pression 1h (si différente)
    if buys_1h > 0 and sells_1h > 0 and abs(buy_ratio_1h - buy_ratio_24h) > 0.1:
        txt += f"\n📊 Pression 1h:\n"
        buys_1h_pct = (buys_1h / (buys_1h + sells_1h) * 100)
        sells_1h_pct = (sells_1h / (buys_1h + sells_1h) * 100)
        txt += f"   🟢 ACHATS: {buys_1h} ({buys_1h_pct:.0f}%)"

        if buy_ratio_1h > buy_ratio_24h:
            txt += f" ⬆️\n"
        else:
            txt += f" ⬇️\n"

        txt += f"   🔴 VENTES: {sells_1h} ({sells_1h_pct:.0f}%)"

        if buy_ratio_1h > buy_ratio_24h:
            txt += f" ⬇️\n"
        else:
            txt += f" ⬆️\n"

        if buy_ratio_1h > buy_ratio_24h and buy_ratio_1h >= 0.8:
            txt += f"   ✅ ACHETEURS prennent le contrôle !\n"
        elif buy_ratio_1h < buy_ratio_24h and buy_ratio_1h < 0.7:
            txt += f"   ⚠️ VENDEURS prennent le contrôle !\n"

    txt += f"\n⚡ Vol/Liq: {ratio_vol_liq:.0f}%\n"
    txt += f"⏰ Age: {age:.0f}h\n\n"

    # MULTI-POOL (si applicable)
    if multi_pool_data.get("is_multi_pool"):
        txt += f"━━━ MULTI-POOL ━━━\n"
        txt += f"🌐 Pools actifs: {multi_pool_data['num_pools']}\n"
        txt += f"📊 Volume total: ${multi_pool_data['total_volume']/1000:.0f}K\n"
        txt += f"💧 Liquidité totale: ${multi_pool_data['total_liquidity']/1000:.0f}K\n"

        # Détail pools
        for activity in multi_pool_data['pool_activities']:
            txt += f"   • {activity['pair']}: {activity['vol_liq_pct']:.0f}% Vol/Liq\n"

        if multi_pool_data.get("is_weth_dominant"):
            txt += f"⚡ WETH pool dominant = Smart money 🚀\n"
        txt += "\n"

    # SIGNAUX
    if signals:
        txt += f"━━━ SIGNAUX DÉTECTÉS ━━━\n"
        for signal in signals:
            txt += f"{signal}\n"
        txt += "\n"

    # ACTION RECOMMANDÉE
    txt += f"━━━ ACTION RECOMMANDÉE ━━━\n"

    # Entry zone
    entry_low = price * 0.98
    entry_high = price * 1.02
    txt += f"⚡ Entry: ${entry_low:.8f} - ${entry_high:.8f}\n"

    # Stop loss
    stop_loss = price * 0.90
    txt += f"🛑 Stop loss: ${stop_loss:.8f} (-10%)\n"

    # Take profits
    tp1 = price * 1.05
    tp2 = price * 1.10
    tp3 = price * 1.15
    txt += f"🎯 TP1 (50%): ${tp1:.8f} (+5%)\n"
    txt += f"🎯 TP2 (30%): ${tp2:.8f} (+10%)\n"
    txt += f"🎯 TP3 (20%): ${tp3:.8f} (+15%)\n"
    txt += f"🔄 Trail stop: -5% après TP1\n\n"

    # RISQUES
    txt += f"━━━ RISQUES ━━━\n"
    if age < 24:
        txt += f"⚠️ Très jeune ({age:.0f}h) - Volatilité élevée\n"
    elif age > 72:
        txt += f"⚠️ Age: {age:.0f}h (exit window passée?)\n"

    if pct_24h < -15:
        txt += f"⚠️ Variation 24h négative ({pct_24h:.1f}%) - Risque re-dump\n"

    if liq >= 500000:
        txt += f"✅ Liquidité solide (${liq/1000:.0f}K) - Faible risque rug\n"
    elif liq >= 200000:
        txt += f"⚠️ Liquidité moyenne (${liq/1000:.0f}K) - Prudence\n"
    else:
        txt += f"🚨 Liquidité faible (${liq/1000:.0f}K) - Risque élevé\n"

    txt += f"\n🔗 https://geckoterminal.com/{network_id.lower()}/pools/{pool_data['pool_address']}\n"

    return txt

# ============================================
# SCAN PRINCIPAL
# ============================================
def scan_geckoterminal():
    """Scan GeckoTerminal avec analyse avancée."""

    log("=" * 80)
    log("🦎 GECKOTERMINAL SCANNER V2 - Analyse Avancée")
    log("=" * 80)

    all_pools = []

    # Collecter tous les pools
    for network in NETWORKS:
        log(f"\n🔍 Scan réseau: {network.upper()}")

        # Trending pools
        trending = get_trending_pools(network)
        if trending:
            log(f"   📊 {len(trending)} pools trending trouvés")
            for pool in trending:
                pool_data = parse_pool_data(pool, network)  # Passer le network en paramètre
                if pool_data and pool_data["age_hours"] <= MAX_TOKEN_AGE_HOURS:
                    all_pools.append(pool_data)

        time.sleep(2)

        # New pools
        new_pools = get_new_pools(network)
        if new_pools:
            log(f"   🆕 {len(new_pools)} nouveaux pools trouvés")
            for pool in new_pools:
                pool_data = parse_pool_data(pool, network)  # Passer le network en paramètre
                if pool_data and pool_data["age_hours"] <= MAX_TOKEN_AGE_HOURS:
                    all_pools.append(pool_data)

        time.sleep(2)

    log(f"\n📊 Total pools collectés: {len(all_pools)}")

    # Mettre à jour historique (seulement buy ratio)
    for pool_data in all_pools:
        update_buy_ratio_history(pool_data)

    # Grouper par token
    grouped = group_pools_by_token(all_pools)

    log(f"🔗 Tokens uniques détectés: {len(grouped)}")

    # Analyser chaque token
    opportunities = []

    for base_token, pools in grouped.items():
        # Multi-pool analysis
        multi_pool_data = analyze_multi_pool(pools)

        # Analyser chaque pool
        for pool_data in pools:
            # Momentum - SIMPLIFIÉ: depuis API directement
            momentum = get_price_momentum_from_api(pool_data)

            # Résistance - SIMPLIFIÉ: calcul basique
            resistance_data = find_resistance_simple(pool_data)

            # Score
            score, base_score, momentum_bonus = calculate_final_score(pool_data, momentum, multi_pool_data)

            # Validation
            is_valid, reason = is_valid_opportunity(pool_data, score)

            if is_valid:
                # Détecter signaux
                signals = detect_signals(pool_data, momentum, multi_pool_data)

                opportunities.append({
                    "pool_data": pool_data,
                    "score": score,
                    "base_score": base_score,
                    "momentum_bonus": momentum_bonus,
                    "momentum": momentum,
                    "multi_pool_data": multi_pool_data,
                    "signals": signals,
                    "resistance_data": resistance_data,
                })

                log(f"   ✅ Opportunité: {pool_data['name']} (Score: {score})")
            else:
                log(f"   ⏭️  {pool_data['name']}: {reason}")

    # Trier par score
    opportunities.sort(key=lambda x: x["score"], reverse=True)

    log(f"\n📊 TOTAL: {len(opportunities)} opportunités détectées")

    # Envoyer alertes
    alerts_sent = 0
    for opp in opportunities:
        base_token = opp["pool_data"]["base_token_name"]
        pool_addr = opp["pool_data"]["pool_address"]
        alert_key = f"{base_token}_{pool_addr}"

        if check_cooldown(alert_key):
            alert_msg = generer_alerte_complete(
                opp["pool_data"],
                opp["score"],
                opp["base_score"],
                opp["momentum_bonus"],
                opp["momentum"],
                opp["multi_pool_data"],
                opp["signals"],
                opp["resistance_data"]
            )

            if send_telegram(alert_msg):
                log(f"✅ Alerte envoyée: {opp['pool_data']['name']} (Score: {opp['score']})")
                alerts_sent += 1
            else:
                log(f"❌ Échec alerte: {opp['pool_data']['name']}")

            if alerts_sent >= MAX_ALERTS_PER_SCAN:
                log(f"⚠️ Limite {MAX_ALERTS_PER_SCAN} alertes atteinte")
                break

            time.sleep(1)

    log(f"\n✅ Scan terminé: {alerts_sent} alertes envoyées")
    log("=" * 80)

# ============================================
# MAIN
# ============================================
def main():
    """Boucle principale."""
    log("🚀 Démarrage GeckoTerminal Scanner V2...")
    log(f"📡 Réseaux surveillés: {', '.join([n.upper() for n in NETWORKS])}")
    log(f"💧 Liquidité min: ${MIN_LIQUIDITY_USD:,}")
    log(f"📊 Volume 24h min: ${MIN_VOLUME_24H_USD:,}")
    log(f"⏰ Age max: {MAX_TOKEN_AGE_HOURS}h")
    log(f"🔄 Scan toutes les 5 minutes")
    log(f"🎯 Max {MAX_ALERTS_PER_SCAN} alertes par scan")

    while True:
        try:
            scan_geckoterminal()

            log("\n💤 Pause 5 min avant prochain scan...\n")
            time.sleep(300)

        except KeyboardInterrupt:
            log("\n⏹️  Arrêt du scanner")
            break

        except Exception as e:
            log(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            log("⏳ Pause 60s avant retry...")
            time.sleep(60)

if __name__ == "__main__":
    main()
