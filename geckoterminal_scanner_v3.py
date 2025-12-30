"""
GeckoTerminal Scanner V3 - OPTIMISÉ avec enseignements Backtest Phase 2
Améliorations basées sur analyse de 3,261 alertes historiques:

NOUVEAUTÉS V3 (Win Rate attendu: 35-50% vs 18.9% actuel):
✅ Arbitrum DÉSACTIVÉ (4.9% WR catastrophique)
✅ Base optimisé (seuils augmentés: $300K liq, $1M vol)
✅ Filtre vélocité minimum >5 (Facteur #1: +133% impact)
✅ Filtre type pump (rejeter LENT: 73% des échecs)
✅ Filtre âge token optimisé (favoriser 2-3 jours: 36.1% WR)
✅ Système de TIERS (HIGH/MEDIUM/LOW confidence)
✅ Liquidité optimale par réseau
✅ Watchlist automatique (snowball, RTX, TTD, FIREBALL)
✅ Scoring dynamique amélioré

Fonctionnalités V2 conservées:
- Multi-pool correlation
- Momentum multi-timeframe
- Traders spike detection
- Buy/Sell pressure evolution
- Alertes ACCELERATION
- Résistance/Support detection
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Système de sécurité et tracking
from security_checker import SecurityChecker
from alert_tracker import AlertTracker

# UTF-8 pour emojis Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (ValueError, AttributeError):
            pass

# ============================================
# CONFIGURATION V3 - CANAL TELEGRAM SÉPARÉ
# ============================================

# Charger variables d'environnement depuis .env.v3 (si disponible)
try:
    from dotenv import load_dotenv
    # Charger .env.v3 en priorité, sinon .env par défaut
    env_v3_path = os.path.join(os.path.dirname(__file__), '.env.v3')
    if os.path.exists(env_v3_path):
        load_dotenv(env_v3_path)
        print("🔧 V3: Configuration chargée depuis .env.v3")
    else:
        load_dotenv()
        print("⚠️ V3: .env.v3 non trouvé, utilisation .env par défaut")
except ImportError:
    print("⚠️ V3: python-dotenv non installé, variables système utilisées")

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

# Configuration Telegram V3 (peut être différente de V2 si .env.v3 utilisé)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Afficher configuration au démarrage
if TELEGRAM_CHAT_ID and TELEGRAM_BOT_TOKEN:
    print(f"✅ V3 Telegram configuré: Chat ID = {TELEGRAM_CHAT_ID}")
    print(f"   Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
else:
    print(f"⚠️ WARNING: Telegram NON configuré!")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ OK' if TELEGRAM_BOT_TOKEN else '❌ MANQUANT'}")
    print(f"   TELEGRAM_CHAT_ID: {'✅ OK' if TELEGRAM_CHAT_ID else '❌ MANQUANT'}")

# Réseaux à surveiller - V3.1: ARBITRUM DÉSACTIVÉ (4.4% quality rate)
# V3.2: Ajout Polygon et Avalanche pour augmenter volume d'opportunités
# Polygon: Très actif memecoins, frais bas
# Avalanche: Écosystème DeFi mature, bonne qualité
NETWORKS = ["eth", "bsc", "base", "solana", "polygon_pos", "avax"]  # V3.2: +Polygon +Avalanche

# ============================================
# SEUILS PAR RÉSEAU - Configuration centralisée
# ============================================

# Fonction pour construire NETWORK_THRESHOLDS selon le mode actif
def build_network_thresholds(mode_config):
    """Construit NETWORK_THRESHOLDS avec limites de liquidité du mode actif."""
    liq = mode_config['LIQUIDITY']
    return {
        "solana": {
            "min_liquidity": liq['solana'][0],
            "max_liquidity": liq['solana'][1],
            "min_volume": 50000,
            "min_txns": 100
        },
        "bsc": {
            "min_liquidity": liq['bsc'][0],
            "max_liquidity": liq['bsc'][1],
            "min_volume": 100000,
            "min_txns": 100
        },
        "eth": {
            "min_liquidity": liq['eth'][0],
            "max_liquidity": liq['eth'][1],
            "min_volume": 50000,
            "min_txns": 100
        },
        "base": {
            "min_liquidity": liq['base'][0],
            "max_liquidity": liq['base'][1],
            "min_volume": 1000000,
            "min_txns": 150
        },
        "arbitrum": {
            "min_liquidity": 100000,
            "max_liquidity": 1000000,
            "min_volume": 50000,
            "min_txns": 100
        },
        "avax": {
            "min_liquidity": liq.get('avax', (100000, 800000))[0],
            "max_liquidity": liq.get('avax', (100000, 800000))[1],
            "min_volume": 50000,
            "min_txns": 100
        },
        "polygon_pos": {
            "min_liquidity": liq.get('polygon_pos', (50000, 500000))[0],
            "max_liquidity": liq.get('polygon_pos', (50000, 500000))[1],
            "min_volume": 30000,  # Plus bas car frais très bas sur Polygon
            "min_txns": 80
        },
        "default": {
            "min_liquidity": 100000,
            "min_volume": 50000,
            "min_txns": 100
        }
    }

# ============================================
# V3.1: CONFIGURATION ULTRA_RENTABLE - Qualité maximale (2.7 alertes/jour)
# ============================================
# Objectif: 2.7 alertes/jour | Score 95.9 | WR 55-70% | ROI +10-15%/mois
# Basé sur analyse de 4252 alertes Railway

print("=" * 80)
print("V3.2 DASHBOARD - POLYGON + AVALANCHE - 2025-12-30 23:00")
print("Objectif: 8-10 alertes/jour | Score 91.4 | WR 45-58% | ROI +4-7%/mois")
print("NEW: +Polygon +Avalanche | Fallback FDV/MarketCap liquidity")
print("=" * 80)

# Configuration DASHBOARD (5 alertes/jour)
DASHBOARD_CONFIG = {
    'MIN_VELOCITE_PUMP': 5.0,
    'NETWORK_SCORE_FILTERS': {
        'eth': {'min_score': 78, 'min_velocity': 5},
        'base': {'min_score': 82, 'min_velocity': 8},
        'bsc': {'min_score': 80, 'min_velocity': 6},
        'solana': {'min_score': 72, 'min_velocity': 5},
        'polygon_pos': {'min_score': 75, 'min_velocity': 5},  # V3.2: Moins strict car frais bas
        'avax': {'min_score': 80, 'min_velocity': 6},  # V3.2: Similar à BSC
    },
    'LIQUIDITY': {
        'eth': (80000, 600000),
        'base': (250000, 2500000),
        'bsc': (400000, 6000000),
        'solana': (80000, 300000),
        'polygon_pos': (50000, 500000),  # V3.2: Plus bas car frais très bas
        'avax': (100000, 800000),  # V3.2: Similar à ETH
    }
}

# Appliquer la configuration
MIN_VELOCITE_PUMP = DASHBOARD_CONFIG['MIN_VELOCITE_PUMP']
NETWORK_SCORE_FILTERS = DASHBOARD_CONFIG['NETWORK_SCORE_FILTERS']
NETWORK_THRESHOLDS = build_network_thresholds(DASHBOARD_CONFIG)

# ============================================
# V3: NOUVEAUX FILTRES (Backtest Phase 2)
# ============================================

OPTIMAL_VELOCITE_PUMP = 30.0     # Bonus si > 30
EXPLOSIVE_VELOCITE_PUMP = 50.0   # Bonus supplémentaire si > 50

# Filtre TYPE PUMP (73% des losers sont "LENT")
ALLOWED_PUMP_TYPES = ["RAPIDE", "TRES_RAPIDE", "PARABOLIQUE"]  # Rejeter LENT, STAGNANT
REJECTED_PUMP_TYPES = ["LENT", "STAGNANT", "STABLE"]

# Filtre ÂGE TOKEN - V3.1 STRATÉGIE HYBRIDE
# Analyse 4252 alertes:
# - Zone EMBRYONIC 0-3h: Quality Index 182.83 (MEILLEUR!)
# - Zone DANGER 12-24h: Quality Index 36.87 (PIRE)
# - Zone MATURE 48-72h: Win Rate 36.1% (stable)
# V3.1: Accepter 0-3h (embryonic) + 48-72h (mature), éviter 12-24h
MIN_TOKEN_AGE_HOURS = 0.0        # V3.1: CRITIQUE - Accepter embryonic 0-3h
EMBRYONIC_AGE_MAX_HOURS = 3.0    # Zone embryonic: 0-3h (QI 182.83)
OPTIMAL_TOKEN_AGE_MIN_HOURS = 48.0   # Zone mature: 48-72h (WR 36.1%)
OPTIMAL_TOKEN_AGE_MAX_HOURS = 72.0
MAX_TOKEN_AGE_HOURS = 168.0      # Max 7 jours
DANGER_ZONE_AGE_MIN = 12.0       # Éviter zone danger 12-24h
DANGER_ZONE_AGE_MAX = 24.0       # Quality Index 36.87 (PIRE)

# Watchlist automatique (tokens "Money Printer")
# snowball/SOL: 100% WR sur 81 alertes!
# RTX/USDT: 100% WR sur 20 alertes
# TTD/USDT: 77.8% WR sur 45 alertes
# FIREBALL/SOL: 77.4% WR sur 31 alertes
WATCHLIST_TOKENS = [
    "snowball", "RTX", "TTD", "FIREBALL",
    # Ajouter d'autres tokens avec historique exceptionnel
]

# Seuils globaux (hérités, conservés pour compatibilité)
VOLUME_LIQUIDITY_RATIO = 0.5    # Vol24h/Liquidité > 50%

# Seuils pour signaux avancés
TRADERS_SPIKE_THRESHOLD = 0.5   # +50% traders
BUY_RATIO_THRESHOLD = 0.8       # 80% buy ratio
BUY_RATIO_CHANGE_THRESHOLD = 0.15  # +15% variation
ACCELERATION_THRESHOLD = 0.05   # +5% en 1h
VOLUME_SPIKE_THRESHOLD = 0.5    # +50% volume

# Cooldown et limites
COOLDOWN_SECONDS = 0  # DÉSACTIVÉ pour backtesting - collecte toutes les occurrences
MAX_ALERTS_PER_SCAN = 10  # Augmenté de 5 à 10 pour collecte max

# NOUVEAU: Paramètres de re-alerting intelligent (Bug #1 fix)
MIN_PRICE_CHANGE_PERCENT = 5.0  # Re-alerter si variation ±5% depuis entry
MIN_TIME_HOURS_FOR_REALERT = 4.0  # Re-alerter après 4h même sans changement
ENABLE_SMART_REALERT = False  # DÉSACTIVÉ pour phase backtesting (collecte max de données)

# TRACKING ACTIF: Paramètres pour suivre les pools alertés (BACKTESTING)
ENABLE_ACTIVE_TRACKING = True  # Activer le tracking actif des pools alertés
ACTIVE_TRACKING_MAX_AGE_HOURS = 24  # Suivre les alertes des dernières 24h
ACTIVE_TRACKING_UPDATE_COOLDOWN_MINUTES = 15  # Cooldown 15min entre mises à jour

# ============================================
# CACHE SIMPLIFIÉ
# ============================================
# On garde seulement buy_ratio history (pas fourni par API)
buy_ratio_history = defaultdict(lambda: defaultdict(list))

# Multi-pool tracking
token_pools = defaultdict(list)  # [base_token] = [pool_data, pool_data, ...]
alert_cooldown = {}

# Système de sécurité et tracking (initialisés dans main())
security_checker = None
alert_tracker = None

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
    "polygon_pos": "Polygon",
    "avax": "Avalanche",
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
    """Vérifie si alerte en cooldown (LEGACY - utiliser should_send_alert à la place)."""
    now = time.time()
    if alert_key in alert_cooldown:
        elapsed = now - alert_cooldown[alert_key]
        if elapsed < COOLDOWN_SECONDS:
            return False
    alert_cooldown[alert_key] = now
    return True


def should_send_alert(token_address: str, current_price: float, tracker, regle5_data: Dict = None) -> Tuple[bool, str]:
    """
    Détermine si une alerte doit être envoyée pour un token (FIX BUG #1 - SPAM).

    Logique intelligente:
    - 1ère alerte: TOUJOURS envoyer
    - Alertes suivantes: SEULEMENT si:
        * TP atteint (TP1/TP2/TP3) OU
        * Prix a varié de ±5% depuis entry OU
        * 4h se sont écoulées depuis dernière alerte OU
        * Pump parabolique détecté (vélocité >100%/h)

    Returns:
        (should_send: bool, reason: str)
    """
    # Vérifier si c'est la première alerte pour ce token
    if not tracker.token_already_alerted(token_address):
        return True, "Première alerte pour ce token"

    # Si système intelligent désactivé, toujours envoyer
    if not ENABLE_SMART_REALERT:
        return True, "Smart re-alert désactivé"

    # Récupérer la dernière alerte pour ce token
    previous_alert = tracker.get_last_alert_for_token(token_address)
    if not previous_alert:
        return True, "Pas d'alerte précédente trouvée"

    # 1. Vérifier si un TP a été atteint
    entry_price = previous_alert.get('entry_price', 0)
    tp1_price = previous_alert.get('tp1_price', 0)
    tp2_price = previous_alert.get('tp2_price', 0)
    tp3_price = previous_alert.get('tp3_price', 0)

    # Récupérer le prix MAX atteint (pas seulement le prix actuel)
    alert_id = previous_alert.get('id', 0)
    prix_max_atteint = current_price
    if alert_id > 0:
        prix_max_db = tracker.get_highest_price_for_alert(alert_id)
        if prix_max_db:
            prix_max_atteint = max(prix_max_db, current_price)

    # FIX HARMONISATION: Tolérance 0.5% pour cohérence avec analyser_alerte_suivante()
    TP_TOLERANCE_PERCENT = 0.5

    def tp_reached_with_tolerance(prix: float, tp_target: float) -> bool:
        """Vérifie si TP atteint avec tolérance pour arrondi."""
        if tp_target <= 0:
            return False
        ecart_percent = ((prix - tp_target) / tp_target) * 100
        return ecart_percent >= -TP_TOLERANCE_PERCENT

    if tp_reached_with_tolerance(prix_max_atteint, tp1_price):
        return True, f"TP atteint (prix max: ${prix_max_atteint:.6f} >= TP1: ${tp1_price:.6f})"

    # 2. Vérifier si le prix a varié de ±5% depuis entry
    if entry_price > 0:
        price_change_pct = abs((current_price - entry_price) / entry_price * 100)
        if price_change_pct >= MIN_PRICE_CHANGE_PERCENT:
            return True, f"Variation prix significative: {price_change_pct:.1f}% depuis entry"

    # 3. Vérifier le temps écoulé depuis la dernière alerte
    created_at_str = previous_alert.get('created_at', '')
    if created_at_str:
        try:
            from datetime import datetime
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
            elapsed = (now - created_at).total_seconds() / 3600  # En heures

            if elapsed >= MIN_TIME_HOURS_FOR_REALERT:
                return True, f"Temps écoulé suffisant: {elapsed:.1f}h"
        except Exception as e:
            log(f"⚠️ Erreur parsing date: {e}")

    # 4. Vérifier si pump parabolique (RÈGLE 5)
    if regle5_data and regle5_data.get('type_pump') == 'PARABOLIQUE':
        return True, f"Pump PARABOLIQUE détecté - Alerte SORTIR urgente"

    # Aucune raison de re-alerter → SPAM PREVENTION
    return False, f"Pas de changement significatif (prix: ${current_price:.6f}, entry: ${entry_price:.6f})"

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
        pools = data.get("data", [])

        # DEBUG: Log premier pool brut pour diagnostic
        if pools and page == 1 and not hasattr(get_trending_pools, '_logged_raw'):
            import json as json_lib
            log(f"   [DEBUG-RAW-POOL] Premier trending pool {network}:")
            log(f"      {json_lib.dumps(pools[0], indent=2)[:800]}")  # 800 premiers caractères
            get_trending_pools._logged_raw = True

        return pools
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

def get_pool_by_address(network: str, pool_address: str) -> Optional[Dict]:
    """
    Récupère les données d'un pool spécifique via son adresse.
    Utilisé pour le tracking actif des alertes.

    Args:
        network: Réseau (eth, bsc, solana, etc.)
        pool_address: Adresse du pool

    Returns:
        Dict avec les données du pool, ou None si erreur
    """
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/pools/{pool_address}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 429:
            log(f"⚠️ Rate limit atteint pour pool {pool_address[:8]}...")
            time.sleep(60)
            return None
        if response.status_code != 200:
            log(f"⚠️ Pool {pool_address[:8]} non trouvé (status {response.status_code})")
            return None

        data = response.json()
        pool_data = data.get("data")

        if pool_data:
            return parse_pool_data(pool_data, network)
        return None

    except Exception as e:
        log(f"❌ Erreur get_pool_by_address {pool_address[:8]}: {e}")
        return None

# ============================================
# PARSING & ENRICHISSEMENT
# ============================================
def parse_pool_data(pool: Dict, network: str = "unknown") -> Optional[Dict]:
    """Parse données pool GeckoTerminal avec enrichissements."""
    try:
        attrs = pool.get("attributes", {})

        # DEBUG: Log structure du premier pool pour diagnostiquer
        if not hasattr(parse_pool_data, '_logged_structure'):
            log(f"   [DEBUG-STRUCTURE] Premier pool reçu:")
            log(f"      Pool keys: {list(pool.keys())}")
            log(f"      Attributes keys: {list(attrs.keys())[:10]}")  # Premiers 10 keys
            if 'reserve_in_usd' in attrs:
                log(f"      reserve_in_usd found: {attrs['reserve_in_usd']}")
            else:
                log(f"      reserve_in_usd NOT FOUND in attributes!")
            parse_pool_data._logged_structure = True

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

        # Liquidity - avec fallback sur FDV et Market Cap
        reserve_value = attrs.get("reserve_in_usd")
        liquidity = 0
        liquidity_source = "none"

        # Essayer reserve_in_usd d'abord
        if reserve_value and reserve_value not in [None, "", "0.0", "0"]:
            try:
                liquidity = float(reserve_value)
                if liquidity > 0:
                    liquidity_source = "reserve_in_usd"
            except (ValueError, TypeError):
                liquidity = 0

        # FALLBACK 1: Si reserve_in_usd est 0, essayer fdv_usd (10% du FDV)
        if liquidity == 0:
            fdv_value = attrs.get("fdv_usd")
            if fdv_value and fdv_value not in [None, "", "0.0", "0", "null"]:
                try:
                    fdv = float(fdv_value)
                    if fdv > 0:
                        # Estimer liquidité à 10% du FDV (conservateur)
                        liquidity = fdv * 0.10
                        liquidity_source = "fdv_usd(10%)"
                except (ValueError, TypeError):
                    pass

        # FALLBACK 2: Si toujours 0, essayer market_cap_usd (15% du market cap)
        if liquidity == 0:
            mcap_value = attrs.get("market_cap_usd")
            if mcap_value and mcap_value not in [None, "", "0.0", "0", "null"]:
                try:
                    mcap = float(mcap_value)
                    if mcap > 0:
                        # Estimer liquidité à 15% du market cap
                        liquidity = mcap * 0.15
                        liquidity_source = "market_cap(15%)"
                except (ValueError, TypeError):
                    pass

        # Log pour debug
        if liquidity == 0:
            log(f"   [LIQUIDITY] {name}: FAILED - reserve={reserve_value}, fdv={attrs.get('fdv_usd')}, mcap={attrs.get('market_cap_usd')}")
        elif liquidity_source != "reserve_in_usd":
            log(f"   [LIQUIDITY] {name}: ${liquidity:,.0f} from {liquidity_source}")

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

        # NOUVEAU: Wallets uniques (buyers/sellers) - FEATURE WHALE DETECTION
        buyers_24h = txns_24h.get("buyers", 0)
        sellers_24h = txns_24h.get("sellers", 0)
        buyers_6h = txns_6h.get("buyers", 0)
        sellers_6h = txns_6h.get("sellers", 0)
        buyers_1h = txns_1h.get("buyers", 0)
        sellers_1h = txns_1h.get("sellers", 0)

        total_txns = buys_24h + sells_24h

        # Variations prix (multi-timeframe depuis API) - Protéger contre None
        price_changes = attrs.get("price_change_percentage", {}) or {}
        price_change_24h = float(price_changes.get("h24") or 0)
        price_change_6h = float(price_changes.get("h6") or 0)
        price_change_3h = float(price_changes.get("h3") or 0)
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

        # Calculer l'accélération du volume (NOUVEAU)
        vol_24h_avg = volume_24h / 24 if volume_24h > 0 else 0
        vol_6h_avg = volume_6h / 6 if volume_6h > 0 else 0

        volume_acceleration_1h_vs_6h = (volume_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
        volume_acceleration_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

        # ===== V3: CALCULER VELOCITE ET TYPE PUMP (depuis price_change_1h) =====
        # Utiliser price_change_1h comme proxy de vélocité (% par heure)
        velocite_pump = abs(price_change_1h) if price_change_1h else 0

        # Déterminer type de pump basé sur vélocité
        if velocite_pump > 100:
            type_pump = "PARABOLIQUE"
        elif velocite_pump > 50:
            type_pump = "TRES_RAPIDE"
        elif velocite_pump > 20:
            type_pump = "RAPIDE"
        elif velocite_pump > 5:
            type_pump = "NORMAL"
        else:
            type_pump = "LENT"

        # Ajouter token_name et token_symbol pour watchlist check
        token_name = base_token_name  # Déjà extrait
        token_symbol = base_token_name  # On utilise le nom de base comme symbole

        return {
            "name": name,
            "base_token_name": base_token_name,
            "token_name": token_name,  # V3: Pour watchlist
            "token_symbol": token_symbol,  # V3: Pour watchlist
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
            "buyers_24h": buyers_24h,
            "sellers_24h": sellers_24h,
            "buyers_6h": buyers_6h,
            "sellers_6h": sellers_6h,
            "buyers_1h": buyers_1h,
            "sellers_1h": sellers_1h,
            "price_change_24h": price_change_24h,
            "price_change_6h": price_change_6h,
            "price_change_3h": price_change_3h,
            "price_change_1h": price_change_1h,
            "age_hours": age_hours,
            "network": network,
            "pool_address": pool_address,
            "fdv_usd": fdv_usd,
            "market_cap_usd": market_cap_usd,
            "volume_acceleration_1h_vs_6h": volume_acceleration_1h_vs_6h,
            "volume_acceleration_6h_vs_24h": volume_acceleration_6h_vs_24h,
            "velocite_pump": velocite_pump,  # V3: Pour filtres backtest
            "type_pump": type_pump,  # V3: Pour filtres backtest
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
    GeckoTerminal fournit déjà price_change_1h, price_change_3h, price_change_6h !
    """
    return {
        "1h": pool_data.get("price_change_1h"),
        "3h": pool_data.get("price_change_3h"),
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
    Score de base DYNAMIQUE V3 (fondamentaux) avec pénalités ET bonus backtest.
    Corrigé pour ALMANAK: score ne doit plus monter pendant une chute.
    V3: Ajout bonus réseau, zones optimales liquidité, âge optimal.
    """
    score = 0

    # === BONUS RÉSEAU V3 (max 35 points - nouveau!) ===
    network = pool_data.get("network", "")
    liq = pool_data.get("liquidity", 0)

    # DEBUG: Log si liquidité manquante
    if liq == 0:
        log(f"   [DEBUG] Pool {pool_data.get('name', 'UNK')}: liq=0, vol={pool_data.get('volume_24h', 0)}, age={pool_data.get('age_hours', 0)}")
        return 0  # Score 0 si pas de liquidité

    # ETH et Solana = champions (38.9% WR)
    if network == "eth":
        score += 35
        # BONUS ZONE JACKPOT ETH $100K-$200K (55.6% WR, +6,987% ROI!)
        if 100000 <= liq <= 200000:
            score += 15  # JACKPOT!
    elif network == "solana":
        score += 32
        # BONUS ZONE OPTIMALE Solana $100K-$200K (43.8% WR)
        if 100000 <= liq <= 200000:
            score += 12
    elif network == "bsc":
        score += 25  # 23.4% WR
        # BONUS ZONE OPTIMALE BSC $500K-$5M (36-39% WR)
        if 500000 <= liq <= 5000000:
            score += 10
    elif network == "base":
        score += 15  # 12.8% WR (faible)
    elif network == "polygon_pos":
        score += 20  # V3.2: Nouveau réseau, score modéré (à ajuster)
        # Zone optimale Polygon: frais bas = plus d'activité
        if 50000 <= liq <= 300000:
            score += 10
    elif network == "avax":
        score += 28  # V3.2: Écosystème mature, similar à BSC
        # Zone optimale Avalanche
        if 100000 <= liq <= 500000:
            score += 12
    elif network == "arbitrum":
        score += 5   # 4.9% WR (catastrophique)
    else:
        score += 10  # Réseau inconnu (prudence)

    # Liquidité (max 25 points - réduit car réseau/zones déjà comptés)
    if liq >= 1000000:
        score += 15  # Réduit (gros tokens déjà découverts)
    elif liq >= 500000:
        score += 20
    elif liq >= 200000:
        score += 25  # SWEET SPOT général
    elif liq >= 100000:
        score += 25  # SWEET SPOT général
    elif liq >= 50000:
        score += 15

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

    # === ÂGE V3 OPTIMISÉ (max 25 points - augmenté!) ===
    age = pool_data["age_hours"]
    if 48 <= age <= 72:  # 2-3 JOURS = OPTIMAL (36.1% WR!)
        score += 25  # MAXIMUM
    elif 24 <= age < 48 or 72 < age <= 96:  # Autour de l'optimal
        score += 20
    elif 6 <= age < 24:  # Acceptable
        score += 15
    elif age < 6:
        score += 8   # Très récent (risqué, -34% drawdown)
    elif 96 < age <= 168:
        score += 10  # Une semaine (OK)
    # PÉNALITÉ ZONE DANGER 12-24h (8.6% WR!)
    if 12 <= age <= 24:
        score -= 15  # PIRE timing!

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
    Bonus momentum INTELLIGENT V3 (dynamique actuelle).
    Corrigé pour ALMANAK: distingue bon spike (accumulation) vs mauvais spike (panic sell).
    V3: Ajout bonus vélocité (facteur #1 de succès: +133% impact).
    """
    # VALIDATION: Vérifier que momentum est un dict valide
    if not momentum or not isinstance(momentum, dict):
        log(f"   ⚠️ momentum invalide dans calculate_momentum_bonus: {type(momentum)}")
        return 0  # Pas de bonus si momentum invalide

    bonus = 0

    # === VÉLOCITÉ V3 (max 20 points - NOUVEAU! Facteur #1) ===
    velocite = pool_data.get('velocite_pump', 0)
    if velocite >= 100:  # PARABOLIQUE
        bonus += 20  # MAXIMUM
    elif velocite >= 50:  # TRES_RAPIDE (pattern gagnant!)
        bonus += 18
    elif velocite >= 20:  # RAPIDE
        bonus += 15
    elif velocite >= 10:
        bonus += 10
    elif velocite >= 5:
        bonus += 5
    # < 5 = déjà filtré en amont, mais si passe quand même:
    elif velocite < 5:
        bonus -= 5  # PÉNALITÉ

    # === Prix 1h (max 15 points - réduit car vélocité déjà compté) ===
    price_1h = momentum.get("1h", 0)
    price_6h = pool_data.get("price_change_6h", 0)
    price_24h = pool_data.get("price_change_24h", 0)

    if price_1h >= 10:
        bonus += 10  # Réduit de 15 à 10
    elif price_1h >= 5:
        bonus += 7   # Réduit de 10 à 7
    elif price_1h >= 2:
        bonus += 3   # Réduit de 5 à 3

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

# ============================================
# WHALE ACTIVITY ANALYSIS (NOUVEAU)
# ============================================
def analyze_whale_activity(pool_data: Dict) -> Dict:
    """
    Analyse l'activité des whales via unique buyers/sellers.

    Détecte:
    - Whale manipulation (peu de wallets, beaucoup de txns)
    - Accumulation distribuée (beaucoup de wallets)
    - Sentiment du marché (buyers vs sellers)

    Returns:
        {
            'pattern': str,              # WHALE_MANIPULATION / DISTRIBUTED_BUYING / WHALE_SELLING / NORMAL
            'whale_score': int,          # -20 à +20 (bonus/malus au score)
            'avg_buys_per_buyer': float,
            'avg_sells_per_seller': float,
            'unique_wallet_ratio': float, # buyers / sellers
            'concentration_risk': str,    # LOW / MEDIUM / HIGH
            'signals': list               # Liste des signaux détectés
        }
    """
    signals = []
    whale_score = 0

    # Récupérer les données 1h (plus récent = plus important)
    # HOTFIX: Gérer None explicite de l'API (or 0 = fallback)
    buys_1h = pool_data.get('buys_1h') or 0
    sells_1h = pool_data.get('sells_1h') or 0
    buyers_1h = pool_data.get('buyers_1h') or 0
    sellers_1h = pool_data.get('sellers_1h') or 0

    # Récupérer 24h pour contexte
    buys_24h = pool_data.get('buys_24h') or 0
    buyers_24h = pool_data.get('buyers_24h') or 0
    sellers_24h = pool_data.get('sellers_24h') or 0

    # Calculer moyennes de transactions par wallet unique
    avg_buys_per_buyer = buys_1h / buyers_1h if buyers_1h > 0 else 0
    avg_sells_per_seller = sells_1h / sellers_1h if sellers_1h > 0 else 0

    # Ratio unique wallets
    unique_wallet_ratio = buyers_1h / sellers_1h if sellers_1h > 0 else 1.0

    # === DÉTECTION 1: WHALE MANIPULATION (Achat/Vente) ===

    # FIX BUG #2: Seuils plus réalistes pour détecter whale manipulation
    # avg_buys_per_buyer élevé = concentration whale (même avec beaucoup de buyers)

    # WHALE EXTREME: avg > 15 (whale très concentrée)
    if avg_buys_per_buyer > 15:
        signals.append("🐋🐋 WHALE MANIPULATION EXTRÊME détectée (avg: {:.1f}x buys/buyer)".format(avg_buys_per_buyer))
        whale_score -= 20  # GROS MALUS
        pattern = "WHALE_MANIPULATION"
        concentration_risk = "HIGH"

    # WHALE MODÉRÉE: avg > 10 (concentration significative)
    elif avg_buys_per_buyer > 10:
        signals.append("🐋 WHALE ACCUMULATION détectée (avg: {:.1f}x buys/buyer)".format(avg_buys_per_buyer))
        whale_score -= 15  # MALUS car whale peut dumper
        pattern = "WHALE_MANIPULATION"
        concentration_risk = "HIGH"

    # WHALE SELL EXTREME: avg > 15 sells/seller
    elif avg_sells_per_seller > 15:
        signals.append("🚨🚨 WHALE DUMP EXTRÊME détecté (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 30  # ÉNORME MALUS
        pattern = "WHALE_SELLING"
        concentration_risk = "HIGH"

    # WHALE SELL MODÉRÉE: avg > 10 sells/seller
    elif avg_sells_per_seller > 10:
        signals.append("🚨 WHALE DUMP détecté (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 25  # GROS MALUS car dump imminent
        pattern = "WHALE_SELLING"
        concentration_risk = "HIGH"

    # WHALE SELL FAIBLE: avg > 5 sells/seller (seulement si peu de sellers)
    elif avg_sells_per_seller > 5 and sellers_1h < 50:
        signals.append("⚠️ WHALE SELLING détectée (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 15
        pattern = "WHALE_SELLING"
        concentration_risk = "MEDIUM"

    # === DÉTECTION 2: ACCUMULATION DISTRIBUÉE (BULLISH) ===

    # Beaucoup de buyers uniques + ratio favorable
    elif buyers_1h > sellers_1h * 1.5 and buyers_1h > 15:
        signals.append("✅ ACCUMULATION DISTRIBUÉE (achat par many wallets)")
        whale_score += 15  # BONUS car accumulation saine
        pattern = "DISTRIBUTED_BUYING"
        concentration_risk = "LOW"

    # Buyers > sellers mais modéré
    elif buyers_1h > sellers_1h * 1.2 and buyers_1h > 10:
        signals.append("📈 Sentiment BULLISH (plus de buyers que sellers)")
        whale_score += 10
        pattern = "DISTRIBUTED_BUYING"
        concentration_risk = "LOW"

    # === DÉTECTION 3: DISTRIBUTION ÉQUILIBRÉE ===

    elif 0.8 <= unique_wallet_ratio <= 1.2:
        signals.append("⚖️ Marché équilibré (buyers ≈ sellers)")
        whale_score += 0  # Neutre
        pattern = "NORMAL"
        concentration_risk = "MEDIUM"

    # === DÉTECTION 4: SELLING PRESSURE ===

    elif sellers_1h > buyers_1h * 1.3:
        signals.append("⚠️ SELLING PRESSURE (plus de sellers que buyers)")
        whale_score -= 10  # MALUS
        pattern = "DISTRIBUTED_SELLING"
        concentration_risk = "MEDIUM"

    else:
        pattern = "NORMAL"
        concentration_risk = "MEDIUM"

    # === VÉRIFICATION SUPPLÉMENTAIRE: Activité 24h ===

    # Si buyers_24h faible malgré volume élevé → concentration whale
    if buyers_24h > 0:
        avg_buys_per_buyer_24h = buys_24h / buyers_24h
        if avg_buys_per_buyer_24h > 8:
            signals.append("⚠️ Concentration whale sur 24h (peu de wallets uniques)")
            whale_score -= 8
            concentration_risk = "HIGH"

    return {
        'pattern': pattern,
        'whale_score': whale_score,
        'avg_buys_per_buyer': round(avg_buys_per_buyer, 2),
        'avg_sells_per_seller': round(avg_sells_per_seller, 2),
        'unique_wallet_ratio': round(unique_wallet_ratio, 2),
        'concentration_risk': concentration_risk,
        'signals': signals,
        'buyers_1h': buyers_1h,
        'sellers_1h': sellers_1h
    }

# ============================================
# V3: NOUVELLES FONCTIONS DE FILTRAGE
# Basé sur Backtest Phase 2 (3,261 alertes analysées)
# ============================================

def check_watchlist_token(pool_data: Dict) -> bool:
    """
    Vérifie si le token est dans la watchlist "Money Printer"
    Ces tokens ont montré 77-100% win rate historique

    Returns:
        True si token dans watchlist
    """
    token_name = pool_data.get('token_name', '').lower()
    token_symbol = pool_data.get('token_symbol', '').lower()

    for watch_token in WATCHLIST_TOKENS:
        watch_lower = watch_token.lower()
        if watch_lower in token_name or watch_lower in token_symbol:
            return True

    return False

def filter_by_velocite(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre VÉLOCITÉ - V3.1 avec seuils différenciés par réseau

    Stratégie:
    - ETH/SOLANA: Vélocité min 10 (réseaux performants)
    - BASE: Vélocité min 15 (filtrage agressif, volume élevé)
    - BSC: Vélocité min 12 (modéré)

    Returns:
        (pass_filter, reason)
    """
    velocite = pool_data.get('velocite_pump', 0)
    network = pool_data.get('network', '').lower()

    # Token watchlist: bypass filtre vélocité
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass vélocité"

    # V3.1: Seuil par réseau (si défini), sinon seuil global
    min_velocity = NETWORK_SCORE_FILTERS.get(network, {}).get('min_velocity', MIN_VELOCITE_PUMP)

    # Filtre minimum CRITIQUE
    if velocite < min_velocity:
        return False, f"Vélocité trop faible: {velocite:.1f} < {min_velocity} ({network.upper()})"

    # Bonus si vélocité optimale
    if velocite >= OPTIMAL_VELOCITE_PUMP:
        return True, f"Vélocité EXCELLENTE: {velocite:.1f} (>{OPTIMAL_VELOCITE_PUMP} = pattern gagnant)"

    return True, f"Vélocité OK: {velocite:.1f} (min {network.upper()}: {min_velocity})"

def filter_by_type_pump(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre TYPE PUMP - 73% des losers sont "LENT"

    Returns:
        (pass_filter, reason)
    """
    type_pump = pool_data.get('type_pump', 'UNKNOWN')

    # Token watchlist: bypass filtre type
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass type pump"

    # Rejeter types problématiques
    if type_pump in REJECTED_PUMP_TYPES:
        return False, f"Type pump rejeté: {type_pump} (73% des échecs)"

    # Accepter types performants
    if type_pump in ALLOWED_PUMP_TYPES:
        return True, f"Type pump OK: {type_pump}"

    # Type inconnu: accepter avec warning
    return True, f"Type pump inconnu: {type_pump} (à vérifier)"

def filter_by_age(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre ÂGE TOKEN optimisé
    - Zone optimale: 2-3 jours (36.1% WR, +234% ROI)
    - Zone danger: 12-24h (8.6% WR - PIRE moment)
    - Trop tôt (0-30min): 23.8% WR, -34% drawdown

    Returns:
        (pass_filter, reason)
    """
    age_hours = pool_data.get('age_hours', 0)

    # Token watchlist: bypass filtre âge
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass âge"

    # Trop vieux (7+ jours: 0% WR historique)
    if age_hours > MAX_TOKEN_AGE_HOURS:
        return False, f"Token trop vieux: {age_hours:.1f}h (>7 jours = 0% WR)"

    # Trop jeune (< 3h: risqué, -34% drawdown moyen)
    if age_hours < MIN_TOKEN_AGE_HOURS:
        # Exception: si vélocité exceptionnelle (>50)
        velocite = pool_data.get('velocite_pump', 0)
        if velocite < OPTIMAL_VELOCITE_PUMP:
            return False, f"Token trop jeune: {age_hours:.1f}h (<3h risqué, drawdown -34%)"

    # ZONE DANGER 12-24h (8.6% WR - PIRE timing!)
    if DANGER_ZONE_AGE_MIN <= age_hours <= DANGER_ZONE_AGE_MAX:
        # Rejeter sauf si vélocité exceptionnelle ET score élevé
        velocite = pool_data.get('velocite_pump', 0)
        score = pool_data.get('score', 0)
        if velocite < OPTIMAL_VELOCITE_PUMP or score < 80:
            return False, f"ZONE DANGER âge: {age_hours:.1f}h (12-24h = 8.6% WR!)"

    # ZONE OPTIMALE 2-3 jours (36.1% WR, +234% ROI)
    if OPTIMAL_TOKEN_AGE_MIN_HOURS <= age_hours <= OPTIMAL_TOKEN_AGE_MAX_HOURS:
        return True, f"Âge OPTIMAL: {age_hours:.1f}h (2-3 jours = 36.1% WR!)"

    # V3.1: Zone embryonic 0-3h (Quality Index 182.83 - OPTIMAL!)
    if 0 <= age_hours <= EMBRYONIC_AGE_MAX_HOURS:
        velocite = pool_data.get('velocite_pump', 0)
        if velocite >= 20:  # Embryonic OK si vélocité forte
            return True, f"Âge EMBRYONIC OPTIMAL: {age_hours:.1f}h (QI 182.83!)"
        else:
            return True, f"Âge embryonic: {age_hours:.1f}h (acceptable si vélocité >20)"

    # Autres zones: acceptable
    return True, f"Âge OK: {age_hours:.1f}h"

def filter_by_score_network(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre SCORE par réseau - V3.1 NOUVEAU

    Stratégie différenciée:
    - ETH (77.4% quality): Score min 85 (moins strict, réseau excellent)
    - BASE (59.2% quality): Score min 90 (strict, filtrer volume élevé)
    - BSC (50.2% quality): Score min 88 (modéré)
    - SOLANA (39.2% quality): Score min 85 (moins strict, bon potentiel)

    Returns:
        (pass_filter, reason)
    """
    score = pool_data.get('score', 0)
    network = pool_data.get('network', '').lower()

    # Token watchlist: bypass filtre score
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass score"

    # V3.1: Seuil par réseau (si défini), sinon global 85
    min_score = NETWORK_SCORE_FILTERS.get(network, {}).get('min_score', 85)

    if score < min_score:
        return False, f"Score insuffisant: {score} < {min_score} ({network.upper()})"

    return True, f"Score OK: {score} (min {network.upper()}: {min_score})"

def filter_by_liquidity_range(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre LIQUIDITÉ par réseau (zones optimales)
    - Solana: $100K-$200K optimal (43.8% WR)
    - ETH: $100K-$200K optimal (55.6% WR, +6,987% ROI!)
    - BSC: $500K-$5M optimal (36-39% WR)

    Returns:
        (pass_filter, reason)
    """
    network = pool_data.get('network', 'unknown')
    liquidity = pool_data.get('liquidity', 0)

    # Token watchlist: bypass filtre liquidité
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass liquidité"

    thresholds = NETWORK_THRESHOLDS.get(network, NETWORK_THRESHOLDS.get("default"))

    # Check min
    min_liq = thresholds.get('min_liquidity', 0)
    if liquidity < min_liq:
        return False, f"Liquidité trop faible: ${liquidity:,.0f} < ${min_liq:,.0f}"

    # Check max (si défini)
    max_liq = thresholds.get('max_liquidity')
    if max_liq and liquidity > max_liq:
        return False, f"Liquidité trop élevée: ${liquidity:,.0f} > ${max_liq:,.0f} (tokens gros = déjà découverts)"

    # Zone optimale par réseau
    if network == "solana" and 100000 <= liquidity <= 200000:
        return True, f"Liquidité OPTIMALE Solana: ${liquidity:,.0f} (43.8% WR!)"
    elif network == "eth" and 100000 <= liquidity <= 200000:
        return True, f"Liquidité JACKPOT ETH: ${liquidity:,.0f} (55.6% WR, +6,987% ROI!)"
    elif network == "bsc" and 500000 <= liquidity <= 5000000:
        return True, f"Liquidité OPTIMALE BSC: ${liquidity:,.0f} (36-39% WR)"

    return True, f"Liquidité OK: ${liquidity:,.0f}"

def apply_v3_filters(pool_data: Dict) -> Tuple[bool, List[str]]:
    """
    Applique TOUS les filtres V3 dans l'ordre d'importance
    Retourne (pass_all_filters, reasons_list)
    """
    reasons = []

    # 1. SCORE PAR RÉSEAU (V3.1 - NOUVEAU!)
    pass_score, reason_score = filter_by_score_network(pool_data)
    reasons.append(f"✓ {reason_score}" if pass_score else f"✗ {reason_score}")
    if not pass_score:
        return False, reasons

    # 2. VÉLOCITÉ PAR RÉSEAU (V3.1 - Amélioré avec seuils différenciés)
    pass_vel, reason_vel = filter_by_velocite(pool_data)
    reasons.append(f"✓ {reason_vel}" if pass_vel else f"✗ {reason_vel}")
    if not pass_vel:
        return False, reasons

    # 3. TYPE PUMP (73% des losers sont LENT)
    pass_type, reason_type = filter_by_type_pump(pool_data)
    reasons.append(f"✓ {reason_type}" if pass_type else f"✗ {reason_type}")
    if not pass_type:
        return False, reasons

    # 4. ÂGE TOKEN (V3.1 - Hybride: embryonic 0-3h + mature 48-72h)
    pass_age, reason_age = filter_by_age(pool_data)
    reasons.append(f"✓ {reason_age}" if pass_age else f"✗ {reason_age}")
    if not pass_age:
        return False, reasons

    # 5. LIQUIDITÉ (zones optimales par réseau)
    pass_liq, reason_liq = filter_by_liquidity_range(pool_data)
    reasons.append(f"✓ {reason_liq}" if pass_liq else f"✗ {reason_liq}")
    if not pass_liq:
        return False, reasons

    # Tous les filtres V3.1 passés!
    return True, reasons

def calculate_confidence_tier(pool_data: Dict) -> str:
    """
    Calcule le tier de confiance: HIGH, MEDIUM, ou LOW
    Basé sur patterns gagnants du backtest

    HIGH = 35-50% WR attendu
    MEDIUM = 25-30% WR attendu
    LOW = 15-20% WR attendu
    """
    score = pool_data.get('score', 0)
    velocite = pool_data.get('velocite_pump', 0)
    type_pump = pool_data.get('type_pump', '')
    network = pool_data.get('network', '')
    age_hours = pool_data.get('age_hours', 0)
    liquidity = pool_data.get('liquidity', 0)

    # Token watchlist = AUTO HIGH
    if check_watchlist_token(pool_data):
        return "ULTRA_HIGH"  # 77-100% WR historique!

    # HIGH CONFIDENCE (attendu: 35-50% WR)
    high_conditions = [
        network in ['eth', 'solana'],
        48 <= age_hours <= 72,  # 2-3 jours
        velocite >= OPTIMAL_VELOCITE_PUMP,  # >50
        type_pump in ['PARABOLIQUE', 'TRES_RAPIDE'],
        100000 <= liquidity <= 300000
    ]

    if sum(high_conditions) >= 4:  # 4 sur 5 critères
        return "HIGH"

    # MEDIUM CONFIDENCE (attendu: 25-30% WR)
    medium_conditions = [
        network in ['eth', 'solana', 'bsc'],
        age_hours >= 6,
        velocite >= 10,
        type_pump in ALLOWED_PUMP_TYPES,
        liquidity >= 50000,
        score >= 60
    ]

    if sum(medium_conditions) >= 4:
        return "MEDIUM"

    # LOW CONFIDENCE (attendu: 15-20% WR)
    if velocite >= MIN_VELOCITE_PUMP and type_pump in ALLOWED_PUMP_TYPES:
        return "LOW"

    # Très faible confiance
    return "VERY_LOW"

def calculate_final_score(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> Tuple[int, int, int, Dict]:
    """
    Score final = base + momentum + whale_score.

    Returns:
        (final_score, base_score, momentum_bonus, whale_analysis)
    """
    base = calculate_base_score(pool_data)
    momentum_bonus = calculate_momentum_bonus(pool_data, momentum, multi_pool_data)

    # NOUVEAU: Analyse whale activity
    whale_analysis = analyze_whale_activity(pool_data)
    whale_score = whale_analysis['whale_score']

    # Score final avec whale bonus/malus
    final = base + momentum_bonus + whale_score
    final = max(min(final, 100), 0)  # Entre 0 et 100

    return final, base, momentum_bonus, whale_analysis

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
    # VALIDATION: Vérifier que momentum est un dict valide
    if not momentum or not isinstance(momentum, dict):
        log(f"   ⚠️ momentum invalide dans detect_signals: {type(momentum)}")
        return []  # Pas de signaux si momentum invalide

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
    """
    Vérifie si pool est une opportunité valide.
    V3: Applique TOUS les filtres backtest avant validation classique.
    """

    # ===== V3: APPLIQUER FILTRES BACKTEST EN PRIORITÉ =====
    passes_v3, v3_reasons = apply_v3_filters(pool_data)

    # Stocker les raisons V3 dans pool_data pour affichage ultérieur
    pool_data['v3_filter_reasons'] = v3_reasons

    # Si échec filtres V3, rejeter immédiatement (sauf watchlist)
    if not passes_v3:
        # Concaténer toutes les raisons d'échec
        failed_reasons = [r for r in v3_reasons if r.startswith('✗')]
        if failed_reasons:
            return False, f"[V3 REJECT] {failed_reasons[0].replace('✗ ', '')}"
        return False, "[V3 REJECT] Filtres backtest non satisfaits"

    # ===== VALIDATION CLASSIQUE (si V3 passé) =====

    # Récupérer seuils par réseau (avec fallback sur default)
    network = pool_data.get("network", "")
    thresholds = NETWORK_THRESHOLDS.get(network, NETWORK_THRESHOLDS["default"])

    min_liq = thresholds["min_liquidity"]
    min_vol = thresholds["min_volume"]
    min_txns = thresholds["min_txns"]

    # Check liquidité min (déjà vérifié par V3 mais double sécurité)
    if pool_data["liquidity"] < min_liq:
        return False, f"❌ Liquidité trop faible: ${pool_data['liquidity']:,.0f}"

    # Check volume min
    if pool_data["volume_24h"] < min_vol:
        return False, f"⚠️ Volume trop faible: ${pool_data['volume_24h']:,.0f}"

    # Check transactions min
    if pool_data["total_txns"] < min_txns:
        return False, f"⚠️ Pas assez de txns: {pool_data['total_txns']}"

    # Check age max (déjà vérifié par V3)
    if pool_data["age_hours"] > MAX_TOKEN_AGE_HOURS:
        return False, f"⏳ Token trop ancien: {pool_data['age_hours']:.0f}h"

    # Check score minimum (ASSOUPLI pour backtesting: 55 → 50)
    if score < 50:
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

    return True, "✅ Opportunité valide [V3 APPROVED]"

# ============================================
# ÉVALUATION MARCHÉ POUR DÉCISION D'ENTRÉE
# ============================================
def evaluer_conditions_marche(pool_data: Dict, score: int, momentum: Dict,
                              signal_1h: str = None, signal_6h: str = None) -> tuple:
    """
    Évalue TOUTES les conditions du marché pour décider si afficher ACTION RECOMMANDÉE.

    Returns:
        (bool, str, list): (should_enter, decision_type, reasons)
        - should_enter: True = afficher Entry/SL/TP, False = afficher analyse de sortie
        - decision_type: "BUY", "WAIT", "EXIT"
        - reasons: Liste des raisons qui justifient la décision
    """

    reasons_bullish = []
    reasons_bearish = []
    reasons_neutral = []

    # Extraire les données
    pct_24h = pool_data.get("price_change_24h", 0)
    pct_6h = pool_data.get("price_change_6h", 0)
    pct_1h = pool_data.get("price_change_1h", 0)
    vol_24h = pool_data.get("volume_24h", 0)
    vol_6h = pool_data.get("volume_6h", 0)
    vol_1h = pool_data.get("volume_1h", 0)
    liq = pool_data.get("liquidity", 0)
    buys = pool_data.get("buys_24h", 0)
    sells = pool_data.get("sells_24h", 0)
    buys_1h = pool_data.get("buys_1h", 0)
    sells_1h = pool_data.get("sells_1h", 0)
    age = pool_data.get("age_hours", 0)

    buy_ratio_24h = buys / sells if sells > 0 else 1.0
    buy_ratio_1h = buys_1h / sells_1h if sells_1h > 0 else 1.0

    # ===== 1. ANALYSE DU SCORE =====
    if score >= 80:
        reasons_bullish.append("Score excellent (≥80)")
    elif score >= 70:
        reasons_bullish.append("Score bon (≥70)")
    elif score < 60:
        reasons_bearish.append(f"Score faible ({score})")

    # ===== 2. ANALYSE VOLUME (CRITIQUE) =====
    if vol_24h > 0 and vol_6h > 0 and vol_1h > 0:
        vol_24h_avg = vol_24h / 24
        vol_6h_avg = vol_6h / 6
        ratio_1h_vs_6h = (vol_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
        ratio_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

        # Volume court terme (1h vs 6h)
        if signal_1h == "FORTE_ACCELERATION":
            reasons_bullish.append("Volume 1h en FORTE accélération")
        elif signal_1h == "ACCELERATION":
            reasons_bullish.append("Volume 1h en accélération")
        elif signal_1h == "RALENTISSEMENT":
            reasons_bearish.append("Volume 1h en RALENTISSEMENT")
        elif signal_1h == "FORT_RALENTISSEMENT":
            reasons_bearish.append("Volume 1h en FORT RALENTISSEMENT")

        # Volume moyen terme (6h vs 24h)
        if signal_6h == "PUMP_EN_COURS":
            reasons_bullish.append("Pump confirmé sur 6h")
        elif signal_6h == "HAUSSE_PROGRESSIVE":
            reasons_bullish.append("Hausse progressive")
        elif signal_6h == "BAISSE_TENDANCIELLE":
            reasons_bearish.append("Baisse tendancielle sur 6h")

        # PATTERNS CRITIQUES
        if signal_1h in ["FORTE_ACCELERATION", "ACCELERATION"] and signal_6h == "PUMP_EN_COURS":
            reasons_bullish.append("🎯 PATTERN IDÉAL: Pump actif + accélération")
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"] and signal_6h == "PUMP_EN_COURS":
            reasons_bearish.append("⚠️ PATTERN SORTIE: Essoufflement détecté")
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"]:
            reasons_bearish.append("🔴 PATTERN ÉVITER: Volume en chute")

    # ===== 3. ANALYSE PRIX / MOMENTUM (FIX BUG #4 - Multi-TF Confluence) =====

    # Tendance prix 24h
    if pct_24h >= 20:
        reasons_bullish.append(f"Prix 24h en hausse forte (+{pct_24h:.1f}%)")
    elif pct_24h >= 5:
        reasons_bullish.append(f"Prix 24h en hausse (+{pct_24h:.1f}%)")
    elif pct_24h < -15:
        reasons_bearish.append(f"Prix 24h en baisse ({pct_24h:.1f}%)")

    # NOUVEAU: Multi-Timeframe Confluence (Quick Win #3)
    # Détecter PULLBACK SAIN sur uptrend (buy the dip)
    if pct_24h >= 5 and -8 < pct_1h < 0:
        # Uptrend 24h + pullback léger 1h = BUY THE DIP
        reasons_bullish.append(f"📊 PULLBACK SAIN: +{pct_24h:.1f}% 24h | {pct_1h:.1f}% 1h (buy the dip)")
        reasons_bullish.append("✅ Multi-TF confluence: Opportunité d'entrée sur retracement")
    # Détecter continuation haussière (multi-TF bullish)
    elif pct_24h >= 5 and pct_6h >= 3 and pct_1h >= 2:
        reasons_bullish.append(f"🚀 MULTI-TF BULLISH: Hausse confirmée sur 24h/6h/1h")
    # Tendance prix court terme (si pas de pullback sain)
    elif pct_1h >= 5:
        reasons_bullish.append(f"Momentum 1h positif (+{pct_1h:.1f}%)")
    elif pct_1h <= -10:
        # Seulement considérer bearish si vraiment négatif (-10%)
        reasons_bearish.append(f"Momentum 1h très négatif ({pct_1h:.1f}%)")

    # Analyse de la décélération (CRITIQUE pour sortie)
    # MODIFIÉ: Seulement si AUCUN pullback sain
    if pct_1h > 0 and pct_6h > 0 and not (pct_24h >= 5 and -8 < pct_1h < 0):
        if pct_1h < pct_6h * 0.5:  # 1h fait moins de 50% du 6h = décélération
            reasons_bearish.append("Décélération: momentum 1h < 50% du 6h")

    # ===== 4. ANALYSE PRESSION ACHAT/VENTE =====
    ratio_change = buy_ratio_1h - buy_ratio_24h

    if ratio_change > 0.15:  # Forte augmentation pression acheteuse
        reasons_bullish.append(f"Pression acheteuse en hausse (+{ratio_change:.1%})")
    elif ratio_change < -0.15:  # Forte augmentation pression vendeuse
        reasons_bearish.append(f"Pression vendeuse en hausse ({ratio_change:.1%})")

    if buy_ratio_1h >= 1.3:
        reasons_bullish.append(f"Acheteurs dominent 1h (ratio {buy_ratio_1h:.2f})")
    elif buy_ratio_1h <= 0.7:
        reasons_bearish.append(f"Vendeurs dominent 1h (ratio {buy_ratio_1h:.2f})")

    # ===== 5. ANALYSE LIQUIDITÉ =====
    if liq < 150000:
        reasons_bearish.append(f"Liquidité très faible (${liq/1000:.0f}K) - Risque rug élevé")
    elif liq < 200000:
        reasons_neutral.append(f"Liquidité faible (${liq/1000:.0f}K) - Prudence")
    elif liq >= 500000:
        reasons_bullish.append(f"Liquidité solide (${liq/1000:.0f}K)")

    # ===== 6. ANALYSE ÂGE =====
    if age > 48:
        reasons_neutral.append(f"Token mature ({age:.0f}h) - Exit window peut être passée")
    elif age < 1:
        reasons_neutral.append(f"Token très jeune ({age:.1f}h) - Volatilité extrême")

    # ===== DÉCISION FINALE (FIX BUG #6 - Score 70+ devrait donner BUY) =====
    score_bullish = len(reasons_bullish)
    score_bearish = len(reasons_bearish)

    # Détecter patterns critiques
    has_critical_bullish = any("PATTERN IDÉAL" in r or "FORTE accélération" in r or "MULTI-TF BULLISH" in r or "PULLBACK SAIN" in r for r in reasons_bullish)
    has_critical_bearish = any("PATTERN SORTIE" in r or "PATTERN ÉVITER" in r or "FORT RALENTISSEMENT" in r for r in reasons_bearish)

    # NOUVELLE LOGIQUE:
    # 1. Score 70+ avec multi-TF confluence → BUY
    # 2. Pattern critique bearish → EXIT
    # 3. Pattern critique bullish + score >= 65 → BUY
    # 4. Score bullish dominant → BUY
    # 5. Sinon → WAIT ou EXIT

    if has_critical_bearish:
        # Bearish critique = SORTIR (même si score élevé)
        decision = "EXIT"
        should_enter = False
    elif score >= 75 and score_bullish >= 3 and score_bearish <= 1:
        # Score excellent + plusieurs signaux bullish = BUY
        decision = "BUY"
        should_enter = True
    elif score >= 70 and (has_critical_bullish or score_bullish >= 2) and score_bearish <= 1:
        # Score bon + signaux bullish = BUY
        decision = "BUY"
        should_enter = True
    elif has_critical_bullish and score >= 65 and score_bearish <= 2:
        # Pattern idéal/Multi-TF/Pullback sain + score OK = BUY
        decision = "BUY"
        should_enter = True
    elif score_bullish >= 4 and score_bearish <= 1:
        # Beaucoup de signaux bullish = BUY
        decision = "BUY"
        should_enter = True
    elif score_bearish >= 3 or score < 60:
        # Trop bearish ou score faible = EXIT
        decision = "EXIT"
        should_enter = False
    elif score_bullish >= 2 and score_bearish <= 2:
        # Mitigé = WAIT
        decision = "WAIT"
        should_enter = False
    else:
        # Défaut = EXIT
        decision = "EXIT"
        should_enter = False

    return should_enter, decision, {
        'bullish': reasons_bullish,
        'bearish': reasons_bearish,
        'neutral': reasons_neutral
    }

# ============================================
# ANALYSE ALERTE SUIVANTE (TP TRACKING)
# ============================================
def analyser_alerte_suivante(previous_alert: Dict, current_price: float, pool_data: Dict,
                             score: int, momentum: Dict, signal_1h: str = None,
                             signal_6h: str = None, tracker=None) -> Dict:
    """
    Analyse une alerte suivante sur un token déjà alerté.
    Vérifie si les TP ont été atteints et décide de la stratégie.

    VERSION SIMPLE+ - 5 RÈGLES ESSENTIELLES:
    1. Détection des TP atteints
    2. Vérification du prix (pas trop élevé pour re-entry)
    3. Réévaluation des conditions actuelles
    4. Décision: NOUVEAUX_NIVEAUX / SECURISER_HOLD / SORTIR
    5. Analyse vélocité du pump (protection pump parabolique)

    Args:
        previous_alert: Dernière alerte sur ce token (depuis DB)
        current_price: Prix actuel du token
        pool_data: Données actuelles du pool
        score: Score actuel
        momentum: Momentum actuel
        signal_1h: Signal volume 1h vs 6h
        signal_6h: Signal volume 6h vs 24h

    Returns:
        Dict avec:
            - decision: "NOUVEAUX_NIVEAUX" / "SECURISER_HOLD" / "SORTIR"
            - tp_hit: Liste des TP atteints ["TP1", "TP2", "TP3"]
            - tp_gains: Dict avec les gains réalisés {"TP1": 5.0, ...}
            - prix_trop_eleve: bool
            - conditions_favorables: bool
            - raisons: Liste des raisons de la décision
            - nouveaux_niveaux: Dict (si applicable) avec entry/sl/tp
            - velocite_pump: float (% par heure)
            - type_pump: str (PARABOLIQUE / RAPIDE / NORMAL / LENT)
    """

    # VALIDATION: Vérifier que previous_alert et pool_data sont valides
    if not previous_alert or not isinstance(previous_alert, dict):
        log(f"   ⚠️ previous_alert invalide: {type(previous_alert)}")
        return {
            'decision': 'ERROR',
            'tp_hit': [],
            'tp_gains': {},
            'prix_trop_eleve': False,
            'conditions_favorables': False,
            'raisons': ["Données d'alerte précédente invalides"],
            'nouveaux_niveaux': {},
            'hausse_depuis_alerte': 0,
            'velocite_pump': 0,
            'type_pump': 'UNKNOWN',
            'temps_ecoule_heures': 0
        }

    if not pool_data or not isinstance(pool_data, dict):
        log(f"   ⚠️ pool_data invalide dans analyser_alerte_suivante: {type(pool_data)}")
        return {
            'decision': 'ERROR',
            'tp_hit': [],
            'tp_gains': {},
            'prix_trop_eleve': False,
            'conditions_favorables': False,
            'raisons': ["Données de pool invalides"],
            'nouveaux_niveaux': {},
            'hausse_depuis_alerte': 0,
            'velocite_pump': 0,
            'type_pump': 'UNKNOWN',
            'temps_ecoule_heures': 0
        }

    if not momentum or not isinstance(momentum, dict):
        log(f"   ⚠️ momentum invalide dans analyser_alerte_suivante: {type(momentum)}")
        return {
            'decision': 'ERROR',
            'tp_hit': [],
            'tp_gains': {},
            'prix_trop_eleve': False,
            'conditions_favorables': False,
            'raisons': ["Données de momentum invalides"],
            'nouveaux_niveaux': {},
            'hausse_depuis_alerte': 0,
            'velocite_pump': 0,
            'type_pump': 'UNKNOWN',
            'temps_ecoule_heures': 0
        }

    # RÈGLE 1: Détection des TP atteints
    # IMPORTANT: On vérifie si les TP ont été atteints DANS LE PASSÉ (pas juste le prix actuel)
    tp_hit = []
    tp_gains = {}

    tp1_price = previous_alert.get('tp1_price', 0)
    tp2_price = previous_alert.get('tp2_price', 0)
    tp3_price = previous_alert.get('tp3_price', 0)
    entry_price = previous_alert.get('entry_price', previous_alert.get('price_at_alert', 0))

    # Récupérer le prix MAX atteint depuis l'alerte précédente (depuis price_tracking)
    # Si pas de tracking disponible, utiliser le prix actuel comme fallback
    alert_id = previous_alert.get('id', 0)
    prix_max_atteint = current_price  # Fallback par défaut

    # Si le tracker est disponible, récupérer le VRAI prix MAX depuis la DB
    if tracker is not None and alert_id > 0:
        prix_max_db = tracker.get_highest_price_for_alert(alert_id)
        if prix_max_db is not None:
            # Comparer avec le prix actuel et prendre le max
            prix_max_atteint = max(prix_max_db, current_price)
            # Note: On prend le max car le prix actuel peut être > que le dernier tracking

    # FIX HARMONISATION: Tolérance 0.5% pour éviter problèmes d'arrondi
    # Exemple: TP1=$0.1575, prix=$0.1574 → considéré comme atteint (écart 0.06%)
    TP_TOLERANCE_PERCENT = 0.5  # 0.5% de tolérance

    def tp_reached(prix: float, tp_target: float) -> bool:
        """Vérifie si TP atteint avec tolérance pour arrondi."""
        if tp_target <= 0:
            return False
        ecart_percent = ((prix - tp_target) / tp_target) * 100
        # TP atteint si prix >= TP - 0.5%
        return ecart_percent >= -TP_TOLERANCE_PERCENT

    # DEBUG: Log pour comprendre détection TP
    if alert_id > 0:
        log(f"   🔍 DEBUG TP: prix_max={prix_max_atteint:.8f}, tp1={tp1_price:.8f}, tp2={tp2_price:.8f}, tp3={tp3_price:.8f}")

    # Vérification des TP basée sur le prix MAX atteint (historique + actuel)
    # AVEC TOLÉRANCE pour éviter problèmes d'arrondi
    if tp_reached(prix_max_atteint, tp3_price):
        tp_hit.extend(["TP1", "TP2", "TP3"])
        tp_gains["TP1"] = ((tp1_price - entry_price) / entry_price) * 100
        tp_gains["TP2"] = ((tp2_price - entry_price) / entry_price) * 100
        tp_gains["TP3"] = ((tp3_price - entry_price) / entry_price) * 100
    elif tp_reached(prix_max_atteint, tp2_price):
        tp_hit.extend(["TP1", "TP2"])
        tp_gains["TP1"] = ((tp1_price - entry_price) / entry_price) * 100
        tp_gains["TP2"] = ((tp2_price - entry_price) / entry_price) * 100
    elif tp_reached(prix_max_atteint, tp1_price):
        tp_hit.append("TP1")
        tp_gains["TP1"] = ((tp1_price - entry_price) / entry_price) * 100

    # RÈGLE 2: Vérifier si le prix est trop élevé pour re-entry (>20% depuis alerte initiale)
    hausse_depuis_alerte = ((current_price - entry_price) / entry_price) * 100
    prix_trop_eleve = hausse_depuis_alerte > 20.0

    # RÈGLE 5: Analyser la vélocité du pump (protection pump parabolique)
    from datetime import datetime

    # Calculer le temps écoulé depuis l'alerte précédente
    try:
        if isinstance(previous_alert.get('created_at'), str):
            created_at = datetime.strptime(previous_alert['created_at'], '%Y-%m-%d %H:%M:%S')
        else:
            created_at = previous_alert.get('created_at')

        temps_ecoule_heures = (datetime.now() - created_at).total_seconds() / 3600
    except:
        # Si erreur de parsing, estimer à 1h par défaut
        temps_ecoule_heures = 1.0

    # Éviter division par zéro
    if temps_ecoule_heures < 0.01:  # Moins de 36 secondes
        temps_ecoule_heures = 0.01

    # Calculer la vélocité: % de hausse par heure
    velocite_pump = hausse_depuis_alerte / temps_ecoule_heures

    # Classifier le type de pump
    pump_parabolique = False
    pump_tres_rapide = False
    type_pump = ""

    if velocite_pump > 100:  # >100% par heure = PARABOLIQUE
        type_pump = "PARABOLIQUE"
        pump_parabolique = True
    elif velocite_pump > 50:  # >50% par heure = TRÈS RAPIDE
        type_pump = "TRES_RAPIDE"
        pump_tres_rapide = True
    elif velocite_pump > 20:  # >20% par heure = RAPIDE
        type_pump = "RAPIDE"
    elif velocite_pump > 5:  # >5% par heure = NORMAL
        type_pump = "NORMAL"
    else:  # ≤5% par heure = LENT (sain)
        type_pump = "LENT"

    # RÈGLE 3: Réévaluer les conditions actuelles du marché
    log(f"   🔍 DEBUG avant evaluer_conditions_marche: pool_data={type(pool_data)}, score={score}, momentum={type(momentum)}, signal_1h={signal_1h}, signal_6h={signal_6h}")
    conditions_favorables, decision_marche, raisons_marche = evaluer_conditions_marche(
        pool_data, score, momentum, signal_1h, signal_6h
    )
    log(f"   🔍 DEBUG après evaluer_conditions_marche: raisons_marche={type(raisons_marche)}")

    # RÈGLE 4: Décision finale
    raisons = []
    decision = ""
    nouveaux_niveaux = {}

    # CAS 1: Aucun TP atteint → Évaluation selon conditions (FIX BUG #3)
    if not tp_hit:
        # Évaluer si c'est toujours une bonne opportunité d'entrée
        if conditions_favorables and score >= 70:
            decision = "ENTRER"
            raisons.append(f"Aucun TP atteint mais conditions excellentes (Score: {score})")
            raisons.append(f"💡 Si pas en position: ENTRER maintenant")
            raisons.append(f"💡 Si déjà en position: MAINTENIR (pas de TP atteint)")
            log(f"   🔍 DEBUG AVANT extend bullish: raisons_marche type={type(raisons_marche)}, bullish type={type(raisons_marche.get('bullish') if isinstance(raisons_marche, dict) else 'N/A')}")
            raisons.extend(raisons_marche['bullish'][:3])
            log(f"   🔍 DEBUG APRÈS extend bullish")
        elif conditions_favorables and score >= 60:
            decision = "ATTENDRE"
            raisons.append(f"Aucun TP atteint, conditions moyennes (Score: {score})")
            raisons.append(f"💡 Si pas en position: ATTENDRE meilleure entrée")
            raisons.append(f"💡 Si déjà en position: MAINTENIR position initiale")
        else:
            decision = "EVITER"
            raisons.append("Aucun TP atteint et conditions défavorables")
            raisons.append(f"💡 Si pas en position: ÉVITER")
            raisons.append(f"💡 Si en position: Considérer SORTIE si SL proche")
            if raisons_marche['bearish']:
                raisons.extend(raisons_marche['bearish'][:2])

    # CAS 2a: PUMP PARABOLIQUE → SORTIR IMMÉDIATEMENT (risque dump violent)
    elif pump_parabolique and tp_hit:
        decision = "SORTIR"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s) (+{hausse_depuis_alerte:.1f}%)")
        raisons.append(f"🚨 PUMP PARABOLIQUE détecté ({velocite_pump:.0f}%/h)")
        raisons.append(f"⚠️ Risque de dump violent - SÉCURISER IMMÉDIATEMENT")
        raisons.append("💰 Prendre les profits maintenant avant le retournement")

    # CAS 2b: TP atteint(s) + prix trop élevé → Ne pas re-rentrer
    elif prix_trop_eleve:
        decision = "SORTIR"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s) (+{hausse_depuis_alerte:.1f}%)")
        raisons.append(f"⚠️ Prix trop élevé pour re-entry (+{hausse_depuis_alerte:.1f}% depuis alerte initiale)")
        raisons.append("💰 Sécuriser les gains déjà réalisés")

    # CAS 3a: PUMP TRÈS RAPIDE + conditions favorables → Nouveaux niveaux TRÈS SERRÉS
    elif pump_tres_rapide and conditions_favorables and tp_hit:
        decision = "NOUVEAUX_NIVEAUX"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s)")
        for tp_name, gain in tp_gains.items():
            raisons.append(f"   {tp_name}: +{gain:.1f}%")
        raisons.append(f"⚡ Pump très rapide ({velocite_pump:.0f}%/h)")
        raisons.append(f"🚀 Conditions encore favorables ({decision_marche})")
        raisons.append("⚠️ SL TRÈS SERRÉ (-3%) car pump rapide")

        # SL TRÈS SERRÉ à 97% pour pump très rapide
        nouveaux_niveaux = {
            'entry_price': current_price,
            'stop_loss_price': current_price * 0.97,  # -3% au lieu de -5%
            'stop_loss_percent': -3.0,
            'tp1_price': current_price * 1.05,
            'tp1_percent': 5.0,
            'tp2_price': current_price * 1.10,
            'tp2_percent': 10.0,
            'tp3_price': current_price * 1.15,
            'tp3_percent': 15.0
        }

    # CAS 3b: TP atteint(s) + conditions favorables → Nouveaux niveaux
    elif conditions_favorables:
        decision = "NOUVEAUX_NIVEAUX"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s)")
        for tp_name, gain in tp_gains.items():
            raisons.append(f"   {tp_name}: +{gain:.1f}%")
        raisons.append(f"🚀 Conditions encore favorables ({decision_marche})")
        raisons.extend(raisons_marche['bullish'][:3])  # Top 3 raisons haussières

        # Afficher type de pump
        if type_pump == "LENT":
            raisons.append(f"✅ Pump sain ({velocite_pump:.1f}%/h) - Progression stable")

        # Calculer NOUVEAUX niveaux depuis le prix actuel
        # SL plus serré à 95% (car déjà en profit)
        nouveaux_niveaux = {
            'entry_price': current_price,
            'stop_loss_price': current_price * 0.95,
            'stop_loss_percent': -5.0,
            'tp1_price': current_price * 1.05,
            'tp1_percent': 5.0,
            'tp2_price': current_price * 1.10,
            'tp2_percent': 10.0,
            'tp3_price': current_price * 1.15,
            'tp3_percent': 15.0
        }

    # CAS 4: TP atteint(s) + conditions neutres/baissières → Sécuriser
    else:
        decision = "SECURISER_HOLD"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s)")
        for tp_name, gain in tp_gains.items():
            raisons.append(f"   {tp_name}: +{gain:.1f}%")
        raisons.append(f"⚠️ Conditions actuelles: {decision_marche}")
        raisons.extend(raisons_marche['bearish'][:2])  # Top 2 raisons baissières
        raisons.append("💡 Trailing stop à -5% recommandé pour sécuriser")

    return {
        'decision': decision,
        'tp_hit': tp_hit,
        'tp_gains': tp_gains,
        'prix_trop_eleve': prix_trop_eleve,
        'conditions_favorables': conditions_favorables,
        'raisons': raisons,
        'nouveaux_niveaux': nouveaux_niveaux,
        'hausse_depuis_alerte': hausse_depuis_alerte,
        'velocite_pump': velocite_pump,
        'type_pump': type_pump,
        'temps_ecoule_heures': temps_ecoule_heures
    }

# ============================================
# GÉNÉRATION ALERTE COMPLÈTE
# ============================================
def format_price(price: float) -> str:
    """
    Formate le prix de manière intelligente et cohérente (FIX HARMONISATION):
    - Prix >= $1: 2 décimales (ex: $1.23)
    - Prix >= $0.01: 4 décimales (ex: $0.1574) - ÉVITE PROBLÈMES ARRONDI TP
    - Prix < $0.01: 8 décimales (ex: $0.00012345)
    """
    if price >= 1.0:
        return f"${price:.2f}"
    elif price >= 0.01:
        # 4 décimales pour précision TP (évite arrondi $0.1574 → $0.16)
        return f"${price:.4f}"
    else:
        # Pour les très petits prix, garder 8 décimales
        return f"${price:.8f}"

def generer_alerte_complete(pool_data: Dict, score: int, base_score: int, momentum_bonus: int,
                            momentum: Dict, multi_pool_data: Dict, signals: List[str],
                            resistance_data: Dict, whale_analysis: Dict = None, is_first_alert: bool = True,
                            tracker: 'AlertTracker' = None) -> tuple:
    """Génère alerte ultra-complète avec toutes les données.

    Args:
        tracker: Instance d'AlertTracker pour accéder à l'historique (optionnel)

    Returns:
        tuple: (message_texte, donnees_regle5_dict)
    """

    # Initialiser les données RÈGLE 5 par défaut
    regle5_data = {
        'velocite_pump': 0,
        'type_pump': 'UNKNOWN',
        'decision_tp_tracking': None,
        'temps_depuis_alerte_precedente': 0,
        'is_alerte_suivante': 0
    }

    name = pool_data["name"]
    base_token = pool_data["base_token_name"]
    price = pool_data["price_usd"]
    vol_24h = pool_data["volume_24h"]
    vol_6h = pool_data["volume_6h"]
    vol_1h = pool_data["volume_1h"]
    liq = pool_data["liquidity"]
    pct_24h = pool_data["price_change_24h"]
    pct_6h = pool_data["price_change_6h"]
    pct_3h = pool_data["price_change_3h"]
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

    # Initialiser les signaux volume (seront définis dans l'analyse volume)
    signal_1h = None
    signal_6h = None

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
    # Titre différent selon s'il s'agit de la première alerte ou d'une mise à jour
    if is_first_alert:
        txt = f"\n🆕 *Nouvelle opportunité sur le token {base_token}*\n"
    else:
        txt = f"\n🔄 *Nouvelle analyse sur le token {base_token}*\n"
    txt += f"━━━━━━━━━━━━━━━━\n"
    txt += f"💎 {name}\n"
    txt += f"⛓️ Blockchain: {network_display}\n\n"

    # SCORE + CONFIANCE (NOUVEAU)
    confidence = calculate_confidence_score(pool_data)
    txt += f"🎯 *SCORE: {score}/100 {score_emoji} {score_label}*\n"
    txt += f"   Base: {base_score} | Momentum: {momentum_bonus:+d}"

    # Afficher whale score si disponible
    if whale_analysis:
        whale_score = whale_analysis['whale_score']
        if whale_score != 0:
            txt += f" | Whale: {whale_score:+d}"

    txt += f"\n📊 Confiance: {confidence}% (fiabilité données)\n"

    # ===== V3: TIER DE CONFIANCE BACKTEST =====
    tier = calculate_confidence_tier(pool_data)
    tier_emojis = {
        "ULTRA_HIGH": "💎💎💎",
        "HIGH": "💎💎",
        "MEDIUM": "💎",
        "LOW": "⚪",
        "VERY_LOW": "⚫"
    }
    tier_labels = {
        "ULTRA_HIGH": "ULTRA HIGH (Watchlist - 77-100% WR historique)",
        "HIGH": "HIGH (35-50% WR attendu)",
        "MEDIUM": "MEDIUM (25-30% WR attendu)",
        "LOW": "LOW (15-20% WR attendu)",
        "VERY_LOW": "VERY LOW (<15% WR attendu)"
    }
    tier_emoji = tier_emojis.get(tier, "⚪")
    tier_label = tier_labels.get(tier, "UNKNOWN")

    txt += f"🎖️ *TIER V3: {tier_emoji} {tier_label}*\n"

    # Afficher les raisons de filtrage V3 (si disponibles)
    v3_reasons = pool_data.get('v3_filter_reasons', [])
    if v3_reasons:
        # Afficher seulement les raisons positives (succès)
        positive_reasons = [r.replace('✓ ', '') for r in v3_reasons if r.startswith('✓')]
        if positive_reasons:
            txt += f"   V3 Checks: {' | '.join(positive_reasons[:3])}\n"  # Max 3 raisons

    txt += "\n"

    # NOUVEAU: Section WHALE ACTIVITY (FIX BUG #5 - Toujours afficher si whale_score != 0)
    if whale_analysis:
        whale_score_val = whale_analysis.get('whale_score', 0)
        pattern = whale_analysis.get('pattern', 'NORMAL')
        signals = whale_analysis.get('signals', [])

        # Afficher si whale_score != 0 OU si pattern != NORMAL OU si signals non vide
        if whale_score_val != 0 or pattern != 'NORMAL' or signals:
            concentration_risk = whale_analysis['concentration_risk']
            buyers_1h = whale_analysis['buyers_1h']
            sellers_1h = whale_analysis['sellers_1h']
            avg_buys = whale_analysis['avg_buys_per_buyer']
            avg_sells = whale_analysis.get('avg_sells_per_seller', 0)

            # Emoji selon pattern
            if pattern == 'WHALE_MANIPULATION':
                pattern_emoji = "🐋"
                pattern_label = "WHALE MANIPULATION"
            elif pattern == 'WHALE_SELLING':
                pattern_emoji = "🚨"
                pattern_label = "WHALE SELLING"
            elif pattern == 'DISTRIBUTED_BUYING':
                pattern_emoji = "✅"
                pattern_label = "ACCUMULATION DISTRIBUÉE"
            elif pattern == 'DISTRIBUTED_SELLING':
                pattern_emoji = "⚠️"
                pattern_label = "SELLING PRESSURE"
            else:
                # Pattern NORMAL mais whale_score != 0 (ex: concentration 24h)
                pattern_emoji = "📊"
                pattern_label = "WHALE ACTIVITY"

            txt += f"\n{pattern_emoji} *{pattern_label}*\n"
            txt += f"   Buyers: {buyers_1h} | Sellers: {sellers_1h}\n"
            txt += f"   Avg buys/buyer: {avg_buys:.1f}x"
            if avg_sells > 0:
                txt += f" | Avg sells/seller: {avg_sells:.1f}x"
            txt += f"\n   Risque concentration: {concentration_risk}\n"

            # Afficher les signaux si disponibles
            if signals:
                txt += f"   Signaux: {', '.join(signals[:2])}\n"

    txt += "\n"

    # ========== ANALYSE TP TRACKING (pour alertes suivantes) ==========
    if not is_first_alert and tracker is not None:
        token_address = pool_data.get("pool_address", "")
        previous_alert = tracker.get_last_alert_for_token(token_address)

        if previous_alert:
            # Pré-calculer les signaux volume pour l'analyse
            vol_24h_avg = vol_24h / 24
            vol_6h_avg = vol_6h / 6 if vol_6h > 0 else 0
            ratio_1h_vs_6h = (vol_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
            ratio_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

            # Déterminer signaux
            if ratio_1h_vs_6h >= 2.0:
                signal_1h = "FORTE_ACCELERATION"
            elif ratio_1h_vs_6h >= 1.5:
                signal_1h = "ACCELERATION"
            elif ratio_1h_vs_6h <= 0.3:
                signal_1h = "FORT_RALENTISSEMENT"
            elif ratio_1h_vs_6h <= 0.5:
                signal_1h = "RALENTISSEMENT"
            else:
                signal_1h = "STABLE"

            if ratio_6h_vs_24h >= 1.8:
                signal_6h = "PUMP_EN_COURS"
            elif ratio_6h_vs_24h >= 1.3:
                signal_6h = "HAUSSE_PROGRESSIVE"
            elif ratio_6h_vs_24h <= 0.7:
                signal_6h = "BAISSE_TENDANCIELLE"
            else:
                signal_6h = "STABLE"

            # Analyser TP tracking (passer le tracker pour vérifier le prix MAX atteint)
            analyse_tp = analyser_alerte_suivante(
                previous_alert, price, pool_data, score, momentum, signal_1h, signal_6h, tracker
            )
            log(f"   🔍 DEBUG RETOUR analyser_alerte_suivante: decision={analyse_tp.get('decision') if analyse_tp else None}, type={type(analyse_tp)}")

            # VALIDATION: Vérifier que analyse_tp est un dict valide
            if not analyse_tp or not isinstance(analyse_tp, dict):
                log(f"   ⚠️ analyse_tp invalide: {type(analyse_tp)}")
                # Ne pas afficher la section TP tracking si erreur
            elif analyse_tp['decision'] == 'ERROR':
                # Vérifier si l'analyse a échoué (decision == 'ERROR')
                log(f"   ⚠️ Analyse TP tracking échouée, skip section suivi")
                # Ne pas afficher la section TP tracking si erreur
            else:
                # Mettre à jour les données RÈGLE 5
                regle5_data = {
                    'velocite_pump': analyse_tp['velocite_pump'],
                    'type_pump': analyse_tp['type_pump'],
                    'decision_tp_tracking': analyse_tp['decision'],
                    'temps_depuis_alerte_precedente': analyse_tp['temps_ecoule_heures'],
                    'is_alerte_suivante': 1
                }

                # Afficher section TP TRACKING
                txt += f"━━━ SUIVI ALERTE PRÉCÉDENTE ━━━\n"
                entry_prev = previous_alert.get('entry_price', previous_alert.get('price_at_alert', 0))
                txt += f"📍 Entry précédente: {format_price(entry_prev)}\n"
                txt += f"💰 Prix actuel: {format_price(price)} ({analyse_tp['hausse_depuis_alerte']:+.1f}%)\n"

                # Afficher vélocité du pump
                temps_h = analyse_tp['temps_ecoule_heures']
                velocite = analyse_tp['velocite_pump']
                type_pump = analyse_tp['type_pump']

                if temps_h < 1:
                    temps_display = f"{temps_h * 60:.0f} min"
                else:
                    temps_display = f"{temps_h:.1f}h"

                # Emoji selon type de pump
                if type_pump == "PARABOLIQUE":
                    pump_emoji = "🚨"
                    pump_label = "PARABOLIQUE (DANGER)"
                elif type_pump == "TRES_RAPIDE":
                    pump_emoji = "⚡"
                    pump_label = "TRÈS RAPIDE"
                elif type_pump == "RAPIDE":
                    pump_emoji = "🔥"
                    pump_label = "RAPIDE"
                elif type_pump == "NORMAL":
                    pump_emoji = "📈"
                    pump_label = "NORMAL"
                else:  # LENT
                    pump_emoji = "✅"
                    pump_label = "SAIN"

                txt += f"⏱️ Temps écoulé: {temps_display} | {pump_emoji} Vélocité: {velocite:.0f}%/h ({pump_label})\n"

                # Afficher Prix MAX atteint (CRITIQUE pour comprendre détection TP)
                if tracker is not None and 'previous_alert' in locals() and previous_alert:
                    alert_id = previous_alert.get('id', 0)
                    prix_max_db = tracker.get_highest_price_for_alert(alert_id) if alert_id > 0 else None
                    prix_max_display = max(prix_max_db or 0, price)

                    if prix_max_display > 0:
                        entry_price_ref = previous_alert.get('entry_price', price)
                        gain_max = ((prix_max_display - entry_price_ref) / entry_price_ref) * 100
                        txt += f"📈 Prix MAX atteint: {format_price(prix_max_display)} (+{gain_max:.1f}%)\n"

                # Afficher TP atteints (basé sur Prix MAX, pas prix actuel)
                if analyse_tp['tp_hit']:
                    txt += f"✅ *TP ATTEINTS:* {', '.join(analyse_tp['tp_hit'])}\n"
                    for tp_name, gain in analyse_tp['tp_gains'].items():
                        txt += f"   {tp_name}: +{gain:.1f}%\n"
                else:
                    txt += f"⏳ Aucun TP atteint pour le moment\n"

                txt += f"\n🎯 *DÉCISION: {analyse_tp['decision']}*\n"

                # Afficher raisons
                for raison in analyse_tp['raisons']:
                    txt += f"{raison}\n"

                txt += "\n"

    # PRIX & MOMENTUM
    txt += f"━━━ PRIX & MOMENTUM ━━━\n"
    txt += f"💰 Prix: {format_price(price)}\n"

    # Multi-timeframe avec analyse de tendance
    txt += f"📊 "
    txt += f"24h: {pct_24h:+.1f}% "
    if pct_6h != 0:
        txt += f"| 6h: {pct_6h:+.1f}% "
    if pct_3h != 0:
        txt += f"| 3h: {pct_3h:+.1f}% "
    if pct_1h != 0:
        emoji_1h = "🚀" if pct_1h > 5 else ("🟢" if pct_1h > 0 else "🔴")
        txt += f"| 1h: {pct_1h:+.1f}% {emoji_1h}"
    txt += "\n"

    # Analyse de la structure de tendance (NOUVEAU)
    if pct_6h != 0 and pct_3h != 0 and pct_1h != 0:
        # Déterminer si accélération haussière ou essoufflement
        if pct_1h > pct_3h > pct_6h and pct_1h > 0:
            txt += f"📈 Tendance: ACCÉLÉRATION HAUSSIÈRE 🔥\n"
        elif pct_6h > pct_3h > pct_1h and pct_6h > 0:
            txt += f"⚠️ Tendance: ESSOUFFLEMENT (sortie proche) 📉\n"
        elif pct_1h < 0 < pct_3h < pct_6h:
            txt += f"🔄 Tendance: REPRISE après correction (bon entry) ✅\n"
        elif pct_1h < pct_3h < pct_6h and pct_1h < 0:
            txt += f"🔴 Tendance: DÉCÉLÉRATION BAISSIÈRE ⚠️\n"

    # Résistance
    if resistance_data and resistance_data.get("resistance"):
        txt += f"🎯 Résistance: {format_price(resistance_data['resistance'])} "
        txt += f"(+{resistance_data['resistance_dist_pct']:.1f}%)\n"

    txt += "\n"

    # ACTIVITÉ
    txt += f"━━━ ACTIVITÉ ━━━\n"
    txt += f"📊 Vol 24h: ${vol_24h/1000:.0f}K\n"

    # Analyse de l'évolution du volume MULTI-NIVEAUX (NOUVEAU)
    if vol_24h > 0 and vol_6h > 0 and vol_1h > 0:
        # Calculer les moyennes horaires
        vol_24h_avg = vol_24h / 24  # Volume moyen par heure sur 24h
        vol_6h_avg = vol_6h / 6     # Volume moyen par heure sur 6h

        # Ratios d'accélération
        ratio_1h_vs_6h = (vol_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
        ratio_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

        # ANALYSE DOUBLE NIVEAU pour détecter les meilleurs setups

        # Niveau 1: Court terme (1h vs 6h)
        if ratio_1h_vs_6h >= 2.0:
            signal_1h = "FORTE_ACCELERATION"
            emoji_1h = "🔥"
            text_1h = f"FORTE ACCÉLÉRATION ({ratio_1h_vs_6h:.1f}x)"
        elif ratio_1h_vs_6h >= 1.5:
            signal_1h = "ACCELERATION"
            emoji_1h = "📈"
            text_1h = f"ACCÉLÉRATION ({ratio_1h_vs_6h:.1f}x)"
        elif ratio_1h_vs_6h <= 0.5:
            signal_1h = "RALENTISSEMENT"
            emoji_1h = "⚠️"
            text_1h = f"RALENTISSEMENT ({ratio_1h_vs_6h:.1f}x)"
        elif ratio_1h_vs_6h <= 0.3:
            signal_1h = "FORT_RALENTISSEMENT"
            emoji_1h = "🔴"
            text_1h = f"FORT RALENTISSEMENT ({ratio_1h_vs_6h:.1f}x)"
        else:
            signal_1h = "STABLE"
            emoji_1h = "➡️"
            text_1h = f"STABLE ({ratio_1h_vs_6h:.1f}x)"

        # Niveau 2: Moyen terme (6h vs 24h)
        if ratio_6h_vs_24h >= 1.8:
            signal_6h = "PUMP_EN_COURS"
            emoji_6h = "🚀"
            text_6h = f"Pump en cours ({ratio_6h_vs_24h:.1f}x)"
        elif ratio_6h_vs_24h >= 1.3:
            signal_6h = "HAUSSE_PROGRESSIVE"
            emoji_6h = "📊"
            text_6h = f"Hausse progressive ({ratio_6h_vs_24h:.1f}x)"
        elif ratio_6h_vs_24h <= 0.7:
            signal_6h = "BAISSE_TENDANCIELLE"
            emoji_6h = "📉"
            text_6h = f"Baisse tendancielle ({ratio_6h_vs_24h:.1f}x)"
        else:
            signal_6h = "STABLE"
            emoji_6h = "➡️"
            text_6h = f"Normal ({ratio_6h_vs_24h:.1f}x)"

        # VERDICT FINAL combinant les deux niveaux
        txt += f"📊 Volume Multi-Timeframe:\n"
        txt += f"   Court terme (1h): {emoji_1h} {text_1h}\n"
        txt += f"   Moyen terme (6h): {emoji_6h} {text_6h}\n"

        # PATTERN GAGNANTS (basé sur backtest)
        if signal_1h in ["FORTE_ACCELERATION", "ACCELERATION"] and signal_6h == "PUMP_EN_COURS":
            txt += f"✅ PATTERN: ENTRÉE IDÉALE - Pump actif + accélération récente 🎯\n"
        elif signal_1h == "FORTE_ACCELERATION" and signal_6h in ["HAUSSE_PROGRESSIVE", "STABLE"]:
            txt += f"✅ PATTERN: BON ENTRY - Nouveau pump qui démarre 🟢\n"
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"] and signal_6h == "PUMP_EN_COURS":
            txt += f"⚠️ PATTERN: SORTIE PROCHE - Volume qui faiblit (essoufflement) 🚪\n"
        elif signal_1h == "STABLE" and signal_6h == "PUMP_EN_COURS":
            txt += f"⏸️ PATTERN: CONSOLIDATION - Pause avant continuation possible\n"
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"]:
            txt += f"🔴 PATTERN: ÉVITER - Volume en chute libre ❌\n"

        # Afficher détails volumes
        txt += f"   Vol: 24h ${vol_24h/1000:.0f}K | 6h ${vol_6h/1000:.0f}K | 1h ${vol_1h/1000:.0f}K\n"

    # Volume spike ?
    elif vol_1h > 0:
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

        # Analyse de la tendance de pression (focus sur l'évolution, pas les absolus)
        ratio_change = buy_ratio_1h - buy_ratio_24h

        if ratio_change > 0.1:  # Pression acheteuse augmente significativement
            txt += f"   ✅ ACHETEURS prennent le contrôle ! (+{ratio_change:.1%})\n"
        elif ratio_change < -0.1:  # Pression vendeuse augmente significativement
            txt += f"   ⚠️ VENDEURS prennent le contrôle ! ({ratio_change:.1%})\n"
        else:  # Pression stable
            if buy_ratio_1h >= 0.75:
                txt += f"   ➡️ Pression ACHETEUSE stable ({buy_ratio_1h:.0%})\n"
            elif buy_ratio_1h <= 0.55:
                txt += f"   ➡️ Pression VENDEUSE stable ({buy_ratio_1h:.0%})\n"
            else:
                txt += f"   ➡️ Équilibre acheteurs/vendeurs ({buy_ratio_1h:.0%})\n"

    txt += f"\n⚡ Vol/Liq: {ratio_vol_liq:.0f}%\n"
    txt += f"⏰ Créé il y a {age:.0f}h\n\n"

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

    # ÉVALUATION DES CONDITIONS MARCHÉ POUR DÉCISION D'ENTRÉE
    should_enter, decision, analysis_reasons = evaluer_conditions_marche(
        pool_data, score, momentum, signal_1h, signal_6h
    )

    # ACTION RECOMMANDÉE - CONDITIONNELLE
    txt += f"━━━ ACTION RECOMMANDÉE ━━━\n"

    # Vérifier si on a une analyse TP avec nouveaux niveaux (alerte suivante)
    show_nouveaux_niveaux = (not is_first_alert and tracker is not None and
                             'analyse_tp' in locals() and
                             analyse_tp['decision'] == "NOUVEAUX_NIVEAUX")

    if show_nouveaux_niveaux:
        # ✅ NOUVEAUX NIVEAUX TP/SL (car TP précédents atteints + conditions favorables)
        txt += f"🚀 NOUVEAUX NIVEAUX - TP précédents atteints !\n\n"

        nouveaux = analyse_tp['nouveaux_niveaux']
        entry_new = nouveaux['entry_price']
        stop_loss_new = nouveaux['stop_loss_price']
        tp1_new = nouveaux['tp1_price']
        tp2_new = nouveaux['tp2_price']
        tp3_new = nouveaux['tp3_price']

        txt += f"⚡ Entry: {format_price(entry_new)} 🎯\n"
        txt += f"📍 Limite entrée: {format_price(entry_new * 1.03)} (max +3%)\n"
        txt += f"🛑 Stop loss: {format_price(stop_loss_new)} (-5%) ⚡ SL SERRÉ\n"
        txt += f"🎯 TP1 (50%): {format_price(tp1_new)} (+5%)\n"
        txt += f"🎯 TP2 (30%): {format_price(tp2_new)} (+10%)\n"
        txt += f"🎯 TP3 (20%): {format_price(tp3_new)} (+15%)\n"
        txt += f"🔄 Trail stop: -5% après TP1\n\n"

        txt += f"💡 NOTE: SL plus serré (-5%) car déjà en profit !\n\n"

    elif should_enter and decision == "BUY":
        # ✅ CONDITIONS FAVORABLES - Afficher Entry/SL/TP
        txt += f"✅ SIGNAL D'ENTRÉE VALIDÉ\n\n"

        # Afficher les raisons bullish
        if analysis_reasons['bullish']:
            txt += f"📈 Signaux haussiers:\n"
            for reason in analysis_reasons['bullish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        # FIX COHÉRENCE TP: Si alerte suivante, utiliser TP de l'alerte ORIGINALE
        if not is_first_alert and tracker is not None and 'previous_alert' in locals() and previous_alert:
            # Utiliser les TP de la première alerte (COHÉRENCE)
            entry_original = previous_alert.get('entry_price', price)
            sl_original = previous_alert.get('stop_loss_price', price * 0.90)
            tp1_original = previous_alert.get('tp1_price', price * 1.05)
            tp2_original = previous_alert.get('tp2_price', price * 1.10)
            tp3_original = previous_alert.get('tp3_price', price * 1.15)

            txt += f"⚡ Entry (alerte initiale): {format_price(entry_original)} 🎯\n"
            txt += f"📍 Limite entrée: {format_price(entry_original * 1.03)} (max +3%)\n"
            txt += f"🛑 Stop loss: {format_price(sl_original)} (-10%)\n"
            txt += f"🎯 TP1 (50%): {format_price(tp1_original)} (+5%)\n"
            txt += f"🎯 TP2 (30%): {format_price(tp2_original)} (+10%)\n"
            txt += f"🎯 TP3 (20%): {format_price(tp3_original)} (+15%)\n"
            txt += f"🔄 Trail stop: -5% après TP1\n\n"
        else:
            # Première alerte: calculer nouveaux TP depuis prix actuel
            price_max_entry = price * 1.03
            txt += f"⚡ Entry: {format_price(price)} 🎯\n"
            txt += f"📍 Limite entrée: {format_price(price_max_entry)} (max +3%)\n"

            # Stop loss
            stop_loss = price * 0.90
            txt += f"🛑 Stop loss: {format_price(stop_loss)} (-10%)\n"

            # Take profits
            tp1 = price * 1.05
            tp2 = price * 1.10
            tp3 = price * 1.15
            txt += f"🎯 TP1 (50%): {format_price(tp1)} (+5%)\n"
            txt += f"🎯 TP2 (30%): {format_price(tp2)} (+10%)\n"
            txt += f"🎯 TP3 (20%): {format_price(tp3)} (+15%)\n"
            txt += f"🔄 Trail stop: -5% après TP1\n\n"

    elif decision == "WAIT":
        # ⏸️ CONDITIONS INCERTAINES - Attendre
        txt += f"⏸️ ATTENDRE - Conditions pas encore idéales\n\n"

        # Afficher les raisons
        if analysis_reasons['bearish']:
            txt += f"⚠️ Signaux négatifs détectés:\n"
            for reason in analysis_reasons['bearish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        if analysis_reasons['bullish']:
            txt += f"✅ Signaux positifs:\n"
            for reason in analysis_reasons['bullish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        txt += f"💡 RECOMMANDATION:\n"
        txt += f"   • Surveiller l'évolution du volume et du prix\n"
        txt += f"   • Attendre confirmation d'une tendance haussière claire\n"
        txt += f"   • Entrer si le volume accélère et la pression acheteuse augmente\n"
        txt += f"   • Risque modéré - Prudence recommandée\n\n"

    else:  # EXIT
        # 🚫 CONDITIONS DÉFAVORABLES - Ne pas entrer / Sortir
        txt += f"🚫 PAS D'ENTRÉE - Sortie ou éviter le marché\n\n"

        # Afficher les raisons bearish
        if analysis_reasons['bearish']:
            txt += f"🔴 Raisons de sortie/éviter:\n"
            for reason in analysis_reasons['bearish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        # Afficher les points positifs s'il y en a
        if analysis_reasons['bullish']:
            txt += f"⚠️ Points positifs (insuffisants):\n"
            for reason in analysis_reasons['bullish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        txt += f"💡 RECOMMANDATION:\n"

        # Déterminer si c'est un pump qui s'essouffle ou un token à éviter
        is_essoufflement = any("SORTIE" in r or "Essoufflement" in r or "Décélération" in r for r in analysis_reasons['bearish'])
        is_volume_problem = any("ÉVITER" in r or "RALENTISSEMENT" in r or "chute" in r for r in analysis_reasons['bearish'])

        if is_essoufflement:
            txt += f"   • ⚠️ SORTIR si vous êtes en position (pump s'essouffle)\n"
            txt += f"   • NE PAS ENTRER - Momentum en décélération\n"
            txt += f"   • Attendre un éventuel rebound seulement si volume se stabilise\n"
            txt += f"   • Risque élevé de correction\n"
        elif is_volume_problem:
            txt += f"   • 🔴 NE PAS ENTRER - Volume en chute\n"
            txt += f"   • Éviter ce token pour le moment\n"
            txt += f"   • Chercher d'autres opportunités avec volume sain\n"
            txt += f"   • Rebound peu probable sans nouvelle impulsion\n"
        else:
            txt += f"   • 🚫 Conditions actuelles défavorables\n"
            txt += f"   • NE PAS ENTRER tant que la situation ne s'améliore pas\n"
            txt += f"   • Surveiller pour un éventuel rebound avec:\n"
            txt += f"     - Reprise du volume\n"
            txt += f"     - Augmentation de la pression acheteuse\n"
            txt += f"     - Momentum redevenant positif\n"

        txt += "\n"

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

    return txt, regle5_data

# ============================================
# SCAN PRINCIPAL
# ============================================
def scan_geckoterminal():
    """Scan GeckoTerminal avec analyse avancée."""

    log("=" * 80)
    log("🦎 GECKOTERMINAL SCANNER V3.1 - ULTRA_RENTABLE")
    log("=" * 80)

    all_pools = []

    # Collecter tous les pools
    for network in NETWORKS:
        log(f"\n🔍 Scan réseau: {network.upper()}")

        # Trending pools - récupérer 3 pages (60 pools au lieu de 20)
        trending_count = 0
        for page in range(1, 4):  # Pages 1, 2, 3
            trending = get_trending_pools(network, page=page)
            if trending:
                trending_count += len(trending)
                for pool in trending:
                    pool_data = parse_pool_data(pool, network)
                    if pool_data and pool_data["age_hours"] <= MAX_TOKEN_AGE_HOURS:
                        all_pools.append(pool_data)
            time.sleep(1)  # Petite pause entre les pages

        if trending_count > 0:
            log(f"   📊 {trending_count} pools trending trouvés (3 pages)")

        time.sleep(2)

        # New pools - récupérer 3 pages (60 pools au lieu de 20)
        new_count = 0
        for page in range(1, 4):  # Pages 1, 2, 3
            new_pools = get_new_pools(network, page=page)
            if new_pools:
                new_count += len(new_pools)
                for pool in new_pools:
                    pool_data = parse_pool_data(pool, network)
                    if pool_data and pool_data["age_hours"] <= MAX_TOKEN_AGE_HOURS:
                        all_pools.append(pool_data)
            time.sleep(1)  # Petite pause entre les pages

        if new_count > 0:
            log(f"   🆕 {new_count} nouveaux pools trouvés (3 pages)")

        time.sleep(2)

    log(f"\n📊 Total pools collectés: {len(all_pools)}")

    # Mettre à jour historique (seulement buy ratio)
    for pool_data in all_pools:
        update_buy_ratio_history(pool_data)

    # NOUVEAU: Mettre à jour le prix MAX en temps réel pour TOUS les tokens trackés
    # CRITIQUE pour backtesting : capture les pics de prix entre chaque scan
    if alert_tracker is not None:
        for pool_data in all_pools:
            token_address = pool_data.get('token_address')
            current_price = pool_data.get('price', 0)

            if token_address and current_price > 0:
                # Vérifier si ce token a une alerte active
                previous_alert = alert_tracker.get_last_alert_for_token(token_address)
                if previous_alert:
                    alert_id = previous_alert.get('id')
                    # Mettre à jour le prix MAX en DB
                    alert_tracker.update_price_max_realtime(alert_id, current_price)

    # Grouper par token
    grouped = group_pools_by_token(all_pools)

    log(f"🔗 Tokens uniques détectés: {len(grouped)}")

    # Analyser chaque token
    opportunities = []
    tokens_rejected = 0  # Initialiser ici pour éviter UnboundLocalError

    for base_token, pools in grouped.items():
        # Multi-pool analysis
        multi_pool_data = analyze_multi_pool(pools)

        # Analyser chaque pool
        for pool_data in pools:
            # Momentum - SIMPLIFIÉ: depuis API directement
            momentum = get_price_momentum_from_api(pool_data)

            # Résistance - SIMPLIFIÉ: calcul basique
            resistance_data = find_resistance_simple(pool_data)

            # Score (avec analyse whale)
            score, base_score, momentum_bonus, whale_analysis = calculate_final_score(pool_data, momentum, multi_pool_data)

            # NOUVEAU: Rejeter immédiatement si WHALE DUMP détecté
            if whale_analysis['pattern'] == 'WHALE_SELLING':
                log(f"   🚨 {pool_data['name']}: WHALE DUMP détecté - REJETÉ")
                tokens_rejected += 1
                continue

            # Validation
            is_valid, reason = is_valid_opportunity(pool_data, score)

            if is_valid:
                # Détecter signaux
                signals = detect_signals(pool_data, momentum, multi_pool_data)

                # Ajouter signaux whale aux signaux existants
                if whale_analysis['signals']:
                    signals.extend(whale_analysis['signals'])

                opportunities.append({
                    "pool_data": pool_data,
                    "score": score,
                    "base_score": base_score,
                    "momentum_bonus": momentum_bonus,
                    "whale_analysis": whale_analysis,  # NOUVEAU
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
    # tokens_rejected déjà initialisé ligne 2078

    for opp in opportunities:
        base_token = opp["pool_data"]["base_token_name"]
        pool_addr = opp["pool_data"]["pool_address"]
        alert_key = f"{base_token}_{pool_addr}"

        # ==========================================
        # VÉRIFICATION DE SÉCURITÉ
        # ==========================================
        # Utiliser pool_address comme token_address (c'est l'adresse du pool/token)
        token_address = opp["pool_data"]["pool_address"]
        network = opp["pool_data"]["network"]

        log(f"\n🔒 Vérification sécurité: {opp['pool_data']['name']}")

        security_result = security_checker.check_token_security(token_address, network)

        # Vérifier si le token passe les critères de sécurité
        should_send, reason = security_checker.should_send_alert(security_result, min_security_score=50)

        if not should_send:
            log(f"⛔ Token rejeté: {reason}")
            log(f"   Score sécurité: {security_result['security_score']}/100")
            log(f"   Niveau risque: {security_result['risk_level']}")
            tokens_rejected += 1
            continue

        log(f"✅ Sécurité validée (Score: {security_result['security_score']}/100)")

        # ==========================================
        # ENVOI DE L'ALERTE (après validation sécurité)
        # ==========================================

        # Vérifier si c'est la première alerte pour ce token
        is_first_alert = not alert_tracker.token_already_alerted(token_address)

        # Générer le message d'alerte (pour récupérer regle5_data)
        alert_msg, regle5_data = generer_alerte_complete(
            opp["pool_data"],
            opp["score"],
            opp["base_score"],
            opp["momentum_bonus"],
            opp["momentum"],
            opp["multi_pool_data"],
            opp["signals"],
            opp["resistance_data"],
            opp.get("whale_analysis"),  # NOUVEAU: Passer analyse whale
            is_first_alert,
            alert_tracker  # Passer le tracker pour l'analyse TP
        )

        # NOUVEAU: Vérifier si on doit envoyer l'alerte (FIX BUG #1 - SPAM)
        price = opp["pool_data"].get("price_usd", 0)
        should_send, send_reason = should_send_alert(token_address, price, alert_tracker, regle5_data)

        if not should_send:
            log(f"⏸️ Alerte bloquée (anti-spam): {opp['pool_data']['name']}")
            log(f"   Raison: {send_reason}")
            continue

        # Legacy cooldown check (pour compatibilité)
        if check_cooldown(alert_key):
            # Ajouter les infos de sécurité à l'alerte
            security_info = security_checker.format_security_warning(security_result)
            alert_msg = alert_msg + "\n" + security_info

            if send_telegram(alert_msg):
                log(f"✅ Alerte envoyée: {opp['pool_data']['name']} (Score: {opp['score']})")

                # ==========================================
                # SAUVEGARDE EN BASE DE DONNÉES + TRACKING AUTO
                # ==========================================
                try:
                    # Préparer les données pour la DB
                    price = opp["pool_data"].get("price_usd", 0)
                    entry_price = price
                    stop_loss_price = price * 0.90  # -10%
                    tp1_price = price * 1.05  # +5%
                    tp2_price = price * 1.10  # +10%
                    tp3_price = price * 1.15  # +15%

                    alert_data = {
                        'token_name': opp["pool_data"]["name"],
                        'token_address': token_address,
                        'network': network,
                        'price_at_alert': price,
                        'score': opp["score"],
                        'base_score': opp["base_score"],
                        'momentum_bonus': opp["momentum_bonus"],
                        'confidence_score': security_result['security_score'],
                        'volume_24h': opp["pool_data"].get("volume_24h", 0),
                        'volume_6h': opp["pool_data"].get("volume_6h", 0),
                        'volume_1h': opp["pool_data"].get("volume_1h", 0),
                        'liquidity': opp["pool_data"].get("liquidity", 0),
                        'buys_24h': opp["pool_data"].get("buys_24h", 0),
                        'sells_24h': opp["pool_data"].get("sells_24h", 0),
                        'buy_ratio': opp["pool_data"].get("buy_ratio", 0),
                        'total_txns': opp["pool_data"].get("total_txns", 0),
                        'age_hours': opp["pool_data"].get("age_hours", 0),
                        'volume_acceleration_1h_vs_6h': opp["pool_data"].get("volume_acceleration_1h_vs_6h", 0),
                        'volume_acceleration_6h_vs_24h': opp["pool_data"].get("volume_acceleration_6h_vs_24h", 0),
                        'entry_price': entry_price,
                        'stop_loss_price': stop_loss_price,
                        'stop_loss_percent': -10,
                        'tp1_price': tp1_price,
                        'tp1_percent': 5,
                        'tp2_price': tp2_price,
                        'tp2_percent': 10,
                        'tp3_price': tp3_price,
                        'tp3_percent': 15,
                        'alert_message': alert_msg,
                        # RÈGLE 5: Données de vélocité du pump
                        'velocite_pump': regle5_data['velocite_pump'],
                        'type_pump': regle5_data['type_pump'],
                        'decision_tp_tracking': regle5_data['decision_tp_tracking'],
                        'temps_depuis_alerte_precedente': regle5_data['temps_depuis_alerte_precedente'],
                        'is_alerte_suivante': regle5_data['is_alerte_suivante']
                    }

                    alert_id = alert_tracker.save_alert(alert_data)
                    if alert_id > 0:
                        log(f"   💾 Sauvegardé en DB (ID: {alert_id}) - Tracking auto démarré")
                    else:
                        log(f"   ⚠️ Échec sauvegarde DB (token déjà existant?)")

                except Exception as e:
                    log(f"   ⚠️ Erreur sauvegarde DB: {e}")

                alerts_sent += 1
            else:
                log(f"❌ Échec alerte: {opp['pool_data']['name']}")

            if alerts_sent >= MAX_ALERTS_PER_SCAN:
                log(f"⚠️ Limite {MAX_ALERTS_PER_SCAN} alertes atteinte")
                break

            time.sleep(1)
        else:
            # Cooldown actif - alerte bloquée (ne devrait jamais arriver avec COOLDOWN_SECONDS = 0)
            log(f"⏰ Alerte bloquée (cooldown actif): {opp['pool_data']['name']}")

    # ==========================================
    # TRACKING ACTIF DES ALERTES (BACKTESTING)
    # ==========================================
    if ENABLE_ACTIVE_TRACKING and alert_tracker is not None:
        log(f"\n📡 TRACKING ACTIF: Vérification des pools alertés...")

        active_alerts = alert_tracker.get_active_alerts(max_age_hours=ACTIVE_TRACKING_MAX_AGE_HOURS)
        log(f"   🔍 {len(active_alerts)} alertes actives à tracker (< {ACTIVE_TRACKING_MAX_AGE_HOURS}h)")

        updates_sent = 0
        for alert in active_alerts:
            try:
                alert_id = alert['id']
                token_name = alert['token_name']
                pool_address = alert['token_address']
                network = alert['network']
                created_at_str = alert['created_at']

                # Vérifier cooldown (éviter spam)
                from datetime import datetime
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
                minutes_elapsed = (now - created_at).total_seconds() / 60

                # Vérifier si dernière mise à jour était il y a moins de COOLDOWN minutes
                # Pour simplifier, on considère que si l'alerte a moins de COOLDOWN minutes, on skip
                if minutes_elapsed < ACTIVE_TRACKING_UPDATE_COOLDOWN_MINUTES:
                    continue  # Trop récent, skip

                # Récupérer données actuelles du pool
                pool_data = get_pool_by_address(network, pool_address)

                if not pool_data or not isinstance(pool_data, dict):
                    # Pool plus disponible (delisted, erreur API, etc.)
                    log(f"   ⚠️ Pool data invalide pour {token_name}: {type(pool_data)}")
                    continue

                current_price = pool_data.get('price_usd', 0)

                if current_price <= 0:
                    continue

                # Mettre à jour le prix MAX en temps réel
                alert_tracker.update_price_max_realtime(alert_id, current_price)

                # Vérifier si on doit envoyer une mise à jour Telegram
                should_send, reason = should_send_alert(pool_address, current_price, alert_tracker, None)

                if should_send:
                    log(f"   🔄 Mise à jour: {token_name} - {reason}")

                    # Récupérer momentum et multi-pool (optionnel pour mises à jour)
                    momentum = get_price_momentum_from_api(pool_data)
                    multi_pool_data = {}  # Optionnel pour updates

                    # Calculer score et whale analysis
                    score, base_score, momentum_bonus, whale_analysis = calculate_final_score(pool_data, momentum, multi_pool_data)

                    # Générer message d'alerte (is_first_alert = False)
                    try:
                        alert_msg, regle5_data = generer_alerte_complete(
                            pool_data, score, base_score, momentum_bonus, momentum,
                            multi_pool_data, [], None, whale_analysis,
                            is_first_alert=False,  # C'est une mise à jour
                            tracker=alert_tracker
                        )
                    except Exception as gen_error:
                        log(f"   ❌ Erreur génération alerte pour {token_name}: {gen_error}")
                        import traceback
                        log(f"   Traceback: {traceback.format_exc()}")
                        continue  # Skip cette alerte

                    # Envoyer via Telegram
                    success = send_telegram(alert_msg)

                    if success:
                        updates_sent += 1
                        log(f"   ✅ Mise à jour envoyée pour {token_name}")

                        # Limiter le nombre de mises à jour par scan
                        if updates_sent >= 5:  # Max 5 mises à jour par scan
                            log(f"   ⚠️ Limite 5 mises à jour atteinte")
                            break
                    else:
                        log(f"   ❌ Échec envoi mise à jour: {token_name}")

                    time.sleep(1)  # Pause entre mises à jour

            except Exception as e:
                log(f"   ❌ Erreur tracking {alert.get('token_name', 'unknown')}: {e}")

        log(f"   📊 Tracking terminé: {updates_sent} mises à jour envoyées")

    log(f"\n✅ Scan terminé: {alerts_sent} alertes envoyées, {tokens_rejected} tokens rejetés (sécurité)")
    log("=" * 80)

# ============================================
# MAIN
# ============================================
def main():
    """Boucle principale."""
    global security_checker, alert_tracker

    log("🚀 Démarrage GeckoTerminal Scanner V3...")
    log(f"📡 Réseaux surveillés: {', '.join([n.upper() for n in NETWORKS])}")
    log(f"📋 Seuils par réseau (liq/vol/txns):")
    log(f"   • Solana/BSC/ETH/Base: $100K / $50K / 100 txns")
    log(f"   • Arbitrum: $2K / $400 / 10 txns")
    log(f"⏰ Age max: {MAX_TOKEN_AGE_HOURS}h")
    log(f"🔄 Scan toutes les 5 minutes")
    log(f"🎯 Max {MAX_ALERTS_PER_SCAN} alertes par scan")

    # Initialiser le système de sécurité et tracking
    log("\n🔒 Initialisation du système de sécurité...")
    security_checker = SecurityChecker()

    # Chemin DB : volume persistant Railway (/data) ou local
    db_path = os.getenv("DB_PATH", "/data/alerts_history.db")
    alert_tracker = AlertTracker(db_path=db_path)
    log(f"💾 Base de données: {db_path}")

    log("✅ Système de sécurité activé")

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

    # Fermer proprement les connexions
    if alert_tracker:
        log("🔒 Fermeture de la base de données...")
        alert_tracker.close()
        log("✅ Base de données fermée")

if __name__ == "__main__":
    main()
