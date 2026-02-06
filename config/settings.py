"""
Configuration centralisée du Scanner V3

Toutes les variables de configuration du scanner sont ici.
Permet de modifier les seuils sans toucher au code métier.
"""

import os

# ============================================
# CONFIGURATION API & TELEGRAM
# ============================================

# Charger variables d'environnement depuis .env.v3 (si disponible)
try:
    from dotenv import load_dotenv
    # Charger .env.v3 en priorité, sinon .env par défaut
    env_v3_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.v3')
    if os.path.exists(env_v3_path):
        load_dotenv(env_v3_path)
    else:
        load_dotenv()
except ImportError:
    pass  # Utiliser variables système si dotenv pas disponible

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

# Configuration Telegram V3 (peut être différente de V2 si .env.v3 utilisé)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ============================================
# RÉSEAUX BLOCKCHAIN
# ============================================

# Réseaux à surveiller - V3.1: ARBITRUM DÉSACTIVÉ (4.4% quality rate)
# V3.2: Ajout Polygon et Avalanche pour augmenter volume d'opportunités
# Polygon: Très actif memecoins, frais bas
# Avalanche: Écosystème DeFi mature, bonne qualité
NETWORKS = ["eth", "bsc", "base", "solana", "polygon_pos", "avax"]  # V3.2: +Polygon +Avalanche

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

# ============================================
# FONCTION DE CONSTRUCTION DES SEUILS
# ============================================

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
# CONFIGURATION DASHBOARD (MODE ACTIF)
# ============================================
# V4.0 OPTIMIZED - Based on 51,924 alerts backtest analysis
# Key findings:
# - Dynamic TPs (Vel×K) = +15.18%/trade vs Fixed TPs = +5.36%/trade (3x better)
# - 30% of losses had reached +5% before SL hit (missed wins)
# - 77% of wins touched -8% before winning (SL too aggressive)

# Configuration DASHBOARD V4.0 - OPTIMIZED THRESHOLDS
DASHBOARD_CONFIG = {
    'MIN_VELOCITE_PUMP': 5.0,
    'NETWORK_SCORE_FILTERS': {
        # V4.0: Optimized per network based on backtest data
        'eth': {'min_score': 90, 'min_velocity': 30, 'min_buy_ratio': 1.0},      # V4.0: vel 5→30 (30+ = 85%+ WR)
        'base': {'min_score': 85, 'min_velocity': 30, 'min_buy_ratio': 1.0},     # V4.0: vel 7→30 (30+ = optimal)
        'bsc': {'min_score': 95, 'min_velocity': 5, 'min_buy_ratio': 1.0},       # BSC: OK as-is
        'solana': {'min_score': 100, 'min_velocity': 5, 'min_buy_ratio': 1.0},   # V4.0: 95→100 (score 100 only)
        'arbitrum': {'min_score': 98, 'min_velocity': 5, 'min_buy_ratio': 1.0},  # Filter strict
        'polygon_pos': {'min_score': 70, 'min_velocity': 5, 'min_buy_ratio': 1.0},
        'avax': {'min_score': 72, 'min_velocity': 5, 'min_buy_ratio': 1.0},
    },
    'LIQUIDITY': {
        # V4.0: Optimized per network based on win rate analysis
        'eth': (30000, 75000),          # V4.0: <$75K optimal for ETH (higher WR on small pools)
        'base': (100000, 10000000),     # BASE: OK as-is
        'bsc': (20000, 50000000),       # BSC: OK as-is
        'solana': (200000, 2000000),    # V4.0: min 30K→200K ($200K+ = higher WR)
        'polygon_pos': (20000, 3000000),
        'avax': (30000, 5000000),
    }
}

# Appliquer la configuration
MIN_VELOCITE_PUMP = DASHBOARD_CONFIG['MIN_VELOCITE_PUMP']
NETWORK_SCORE_FILTERS = DASHBOARD_CONFIG['NETWORK_SCORE_FILTERS']
NETWORK_THRESHOLDS = build_network_thresholds(DASHBOARD_CONFIG)

# ============================================
# FILTRES V3 - Backtest Phase 2
# ============================================

OPTIMAL_VELOCITE_PUMP = 30.0     # Bonus si > 30
EXPLOSIVE_VELOCITE_PUMP = 50.0   # Bonus supplémentaire si > 50

# Filtre TYPE PUMP (73% des losers sont "LENT")
ALLOWED_PUMP_TYPES = ["RAPIDE", "TRES_RAPIDE", "PARABOLIQUE"]  # Rejeter LENT, STAGNANT
REJECTED_PUMP_TYPES = ["LENT", "STAGNANT", "STABLE"]

# Filtre ÂGE TOKEN - V4.0 NETWORK-SPECIFIC DANGER ZONES
# Based on 51,924 alerts backtest analysis per network:
# - SOLANA: Age 24-96h = high loss rate (avoid)
# - ETH: Age 6-12h = danger zone (avoid)
# - BASE: Age 96h+ = degraded performance (avoid)
MIN_TOKEN_AGE_HOURS = 0.0        # Accept embryonic tokens
EMBRYONIC_AGE_MAX_HOURS = 3.0    # Zone embryonic: 0-3h (QI 182.83)
OPTIMAL_TOKEN_AGE_MIN_HOURS = 48.0   # Zone mature: 48-72h (WR 36.1%)
OPTIMAL_TOKEN_AGE_MAX_HOURS = 72.0
MAX_TOKEN_AGE_HOURS = 168.0      # Max 7 jours

# V4.0: Network-specific age danger zones (hours)
NETWORK_AGE_DANGER_ZONES = {
    'solana': (24, 96),      # Avoid 24-96h for Solana
    'eth': (6, 12),          # Avoid 6-12h for ETH
    'base': (96, 168),       # Avoid 96h+ for BASE
    'bsc': None,             # No specific danger zone
    'polygon_pos': None,
    'avax': None,
}

# Legacy constants (kept for compatibility)
DANGER_ZONE_AGE_MIN = 12.0
DANGER_ZONE_AGE_MAX = 24.0

# Watchlist automatique (tokens "Money Printer")
# snowball/SOL: 100% WR sur 81 alertes!
# RTX/USDT: 100% WR sur 20 alertes
# TTD/USDT: 77.8% WR sur 45 alertes
# FIREBALL/SOL: 77.4% WR sur 31 alertes
WATCHLIST_TOKENS = [
    "snowball", "RTX", "TTD", "FIREBALL",
    # Ajouter d'autres tokens avec historique exceptionnel
]

# ============================================
# SEUILS GLOBAUX
# ============================================

# Seuils globaux (hérités, conservés pour compatibilité)
VOLUME_LIQUIDITY_RATIO = 0.5    # Vol24h/Liquidité > 50%

# Seuils pour signaux avancés
TRADERS_SPIKE_THRESHOLD = 0.5   # +50% traders
BUY_RATIO_THRESHOLD = 0.8       # 80% buy ratio
BUY_RATIO_CHANGE_THRESHOLD = 0.15  # +15% variation
ACCELERATION_THRESHOLD = 0.05   # +5% en 1h
VOLUME_SPIKE_THRESHOLD = 0.5    # +50% volume

# ============================================
# V4.1: DYNAMIC TP/SL + VOL/LIQ OPTIMIZATION
# ============================================
# Based on 51,924 alerts deep analysis:
# - Fixed TPs (+5/+10/+15%): +5.36%/trade avg, 64.5% WR
# - Dynamic TPs (Vel×K): +15.18%/trade avg, 53.5% WR (3x better!)
#
# V4.1 NEW DISCOVERIES:
# - Vol/Liq 2.0-5.0 = 33.4% WR (vs 24% baseline) = +9% improvement!
# - SOLANA + Vol/Liq 2.0-5.0 = 51.7% WR (HUGE!)
# - Hour 06:00-14:00 UTC = worst performance (17-22% WR)
# - Thursday = best day (30.3% WR), Wednesday/Friday = worst (21.2%)

# Dynamic TP multipliers (TP = velocite_pump × K)
TP_MULTIPLIERS = {
    'TP1': 0.3,   # Conservative: Velocite × 0.3 (captures quick gains)
    'TP2': 0.6,   # Moderate: Velocite × 0.6 (balanced)
    'TP3': 1.2,   # Aggressive: Velocite × 1.2 (lets winners run)
}

# Stop Loss - V4.0: Widened from -10% to -12%
STOP_LOSS_PERCENT = -12.0

# Minimum TP values (floor to avoid micro-targets)
MIN_TP1_PERCENT = 3.0
MIN_TP2_PERCENT = 6.0
MIN_TP3_PERCENT = 12.0

# Maximum TP values (ceiling for sanity check)
MAX_TP1_PERCENT = 15.0
MAX_TP2_PERCENT = 30.0
MAX_TP3_PERCENT = 60.0

# Minimum buy ratio filter
MIN_BUY_RATIO = 1.0

# ============================================
# V4.1: VOL/LIQ RATIO OPTIMIZATION (NEW!)
# ============================================
# CRITICAL DISCOVERY: Vol/Liq ratio is a major predictor of success
# - Vol/Liq 2.0-5.0 = 33.4% WR (best overall)
# - SOLANA + Vol/Liq 2.0-5.0 = 51.7% WR (exceptional!)
# - BASE + Vol/Liq 20+ = 42.5% WR
# - BSC + Vol/Liq 1.0-2.0 = 37.1% WR

NETWORK_VOL_LIQ_RANGES = {
    'solana': (2.0, 5.0),     # 51.7% WR - BEST!
    'eth': (5.0, None),       # 34.7% WR with Vol/Liq 20+, but 5+ is safer
    'base': (10.0, None),     # 42.5% WR with Vol/Liq 20+
    'bsc': (1.0, 3.0),        # 37.1% WR in 1.0-2.0 range
    'polygon_pos': (2.0, 10.0),
    'avax': (2.0, 10.0),
}

# ============================================
# V4.1: TIME-BASED FILTERING (NEW!)
# ============================================
# Analysis shows significant WR variation by hour (UTC):
# - GOOD hours (>26% WR): 00-05, 16-17, 20-22
# - BAD hours (<22% WR): 06-14, 19

# Hours to AVOID (UTC) - Win rate consistently < 22%
DANGER_HOURS_UTC = [6, 7, 8, 9, 10, 11, 12, 13, 14, 19]

# Best hours (UTC) - Win rate > 27%
OPTIMAL_HOURS_UTC = [0, 1, 2, 3, 4, 16, 17, 20, 21]

# Day of week filtering (0=Monday, 6=Sunday)
# Thursday (3) = 30.3% WR (BEST)
# Wednesday (2) and Friday (4) = 21.2% WR (WORST)
BEST_DAYS = [3]  # Thursday
AVOID_DAYS = [2, 4]  # Wednesday, Friday

# Enable/disable time filtering (set False for backtesting)
ENABLE_TIME_FILTERING = True

def calculate_dynamic_tps(velocite_pump: float) -> dict:
    """
    Calculate dynamic Take Profit levels based on velocite_pump.

    V4.0 Formula: TP = velocite_pump × K
    Where K = 0.3 (TP1), 0.6 (TP2), 1.2 (TP3)

    Example: velocite_pump = 25
    - TP1 = 25 × 0.3 = 7.5%
    - TP2 = 25 × 0.6 = 15%
    - TP3 = 25 × 1.2 = 30%

    Args:
        velocite_pump: Token's price acceleration (%)

    Returns:
        dict with TP1, TP2, TP3 percentages
    """
    # Calculate raw TPs
    tp1_raw = velocite_pump * TP_MULTIPLIERS['TP1']
    tp2_raw = velocite_pump * TP_MULTIPLIERS['TP2']
    tp3_raw = velocite_pump * TP_MULTIPLIERS['TP3']

    # Apply floor (minimum values)
    tp1 = max(tp1_raw, MIN_TP1_PERCENT)
    tp2 = max(tp2_raw, MIN_TP2_PERCENT)
    tp3 = max(tp3_raw, MIN_TP3_PERCENT)

    # Apply ceiling (maximum values)
    tp1 = min(tp1, MAX_TP1_PERCENT)
    tp2 = min(tp2, MAX_TP2_PERCENT)
    tp3 = min(tp3, MAX_TP3_PERCENT)

    return {
        'TP1': round(tp1, 1),
        'TP2': round(tp2, 1),
        'TP3': round(tp3, 1),
        'SL': STOP_LOSS_PERCENT,
        'velocite_used': velocite_pump,
        'formula': 'DYNAMIC_V4'
    }

def is_in_age_danger_zone(network: str, age_hours: float) -> bool:
    """
    Check if token age is in the network-specific danger zone.

    V4.0: Each network has different problematic age ranges:
    - SOLANA: 24-96h (high loss rate)
    - ETH: 6-12h (danger zone)
    - BASE: 96h+ (degraded performance)

    Args:
        network: Network identifier (solana, eth, base, etc.)
        age_hours: Token age in hours

    Returns:
        True if in danger zone, False otherwise
    """
    danger_zone = NETWORK_AGE_DANGER_ZONES.get(network.lower())
    if danger_zone is None:
        return False

    min_age, max_age = danger_zone
    return min_age <= age_hours <= max_age

def calculate_vol_liq_ratio(volume_24h: float, liquidity: float) -> float:
    """Calculate Volume/Liquidity ratio."""
    if liquidity > 0:
        return volume_24h / liquidity
    return 0.0

def is_optimal_vol_liq(network: str, vol_liq_ratio: float) -> tuple:
    """
    V4.1: Check if Vol/Liq ratio is in optimal range for this network.

    Returns:
        tuple: (is_optimal: bool, reason: str or None)
    """
    network_lower = network.lower()
    bounds = NETWORK_VOL_LIQ_RANGES.get(network_lower)

    if bounds is None:
        return True, None  # No filter for this network

    min_ratio, max_ratio = bounds

    if vol_liq_ratio < min_ratio:
        return False, f"Vol/Liq {vol_liq_ratio:.1f} < {min_ratio}"

    if max_ratio is not None and vol_liq_ratio > max_ratio:
        return False, f"Vol/Liq {vol_liq_ratio:.1f} > {max_ratio}"

    return True, None

def is_optimal_time(hour_utc: int = None, day_of_week: int = None) -> tuple:
    """
    V4.1: Check if current time is optimal for trading.

    Args:
        hour_utc: Hour in UTC (0-23). If None, uses current time.
        day_of_week: Day (0=Monday, 6=Sunday). If None, uses current time.

    Returns:
        tuple: (is_optimal: bool, reason: str or None)
    """
    if not ENABLE_TIME_FILTERING:
        return True, None

    from datetime import datetime, timezone

    if hour_utc is None or day_of_week is None:
        now = datetime.now(timezone.utc)
        hour_utc = now.hour if hour_utc is None else hour_utc
        day_of_week = now.weekday() if day_of_week is None else day_of_week

    # Check danger hours
    if hour_utc in DANGER_HOURS_UTC:
        return False, f"Hour {hour_utc}:00 UTC in danger zone"

    # Check avoid days (optional - less strict)
    # if day_of_week in AVOID_DAYS:
    #     return False, f"Day {day_of_week} is historically weak"

    return True, None

def passes_v4_filters(network: str, score: float, velocite: float,
                      buy_ratio: float, liquidity: float, age_hours: float,
                      volume_24h: float = None, hour_utc: int = None) -> tuple:
    """
    V4.1 Comprehensive filter check for a potential alert.

    Returns:
        tuple: (passes: bool, rejection_reason: str or None)
    """
    network_lower = network.lower()
    filters = NETWORK_SCORE_FILTERS.get(network_lower, {})

    # Check score
    min_score = filters.get('min_score', 70)
    if score < min_score:
        return False, f"Score {score} < {min_score}"

    # Check velocity
    min_velocity = filters.get('min_velocity', 5)
    if velocite < min_velocity:
        return False, f"Velocite {velocite} < {min_velocity}"

    # Check buy ratio (V4.0)
    min_buy_ratio = filters.get('min_buy_ratio', MIN_BUY_RATIO)
    if buy_ratio < min_buy_ratio:
        return False, f"Buy ratio {buy_ratio} < {min_buy_ratio}"

    # Check age danger zone (V4.0)
    if is_in_age_danger_zone(network_lower, age_hours):
        danger = NETWORK_AGE_DANGER_ZONES.get(network_lower)
        return False, f"Age {age_hours}h in danger zone {danger[0]}-{danger[1]}h"

    # Check liquidity bounds
    liq_bounds = DASHBOARD_CONFIG['LIQUIDITY'].get(network_lower)
    if liq_bounds:
        min_liq, max_liq = liq_bounds
        if liquidity < min_liq:
            return False, f"Liquidity ${liquidity:,.0f} < ${min_liq:,.0f}"
        if liquidity > max_liq:
            return False, f"Liquidity ${liquidity:,.0f} > ${max_liq:,.0f}"

    # V4.1: Check Vol/Liq ratio (CRITICAL for win rate!)
    if volume_24h is not None and liquidity > 0:
        vol_liq = calculate_vol_liq_ratio(volume_24h, liquidity)
        is_good, reason = is_optimal_vol_liq(network_lower, vol_liq)
        if not is_good:
            return False, reason

    # V4.1: Check time filtering
    if hour_utc is not None:
        is_good_time, reason = is_optimal_time(hour_utc)
        if not is_good_time:
            return False, reason

    return True, None

def get_alert_quality_score(network: str, score: float, velocite: float,
                            buy_ratio: float, vol_liq_ratio: float,
                            hour_utc: int = None) -> dict:
    """
    V4.1: Calculate a quality score for an alert based on all factors.

    Returns dict with:
    - quality_score: 0-100 (higher = better)
    - tier: 'GOLDEN', 'SILVER', 'BRONZE', 'STANDARD'
    - factors: dict of individual factor scores
    """
    factors = {}

    # Score factor (0-25 points)
    if score >= 100:
        factors['score'] = 25
    elif score >= 95:
        factors['score'] = 20
    elif score >= 90:
        factors['score'] = 15
    else:
        factors['score'] = 10

    # Velocite factor (0-25 points)
    if velocite >= 50:
        factors['velocite'] = 25
    elif velocite >= 30:
        factors['velocite'] = 20
    elif velocite >= 20:
        factors['velocite'] = 15
    else:
        factors['velocite'] = 10

    # Vol/Liq factor (0-30 points) - MOST IMPORTANT
    network_lower = network.lower()
    bounds = NETWORK_VOL_LIQ_RANGES.get(network_lower)
    if bounds:
        min_r, max_r = bounds
        if min_r <= vol_liq_ratio <= (max_r or 100):
            factors['vol_liq'] = 30  # In optimal range
        elif vol_liq_ratio >= min_r * 0.8:
            factors['vol_liq'] = 20  # Close to optimal
        else:
            factors['vol_liq'] = 10
    else:
        factors['vol_liq'] = 20  # No specific range

    # Time factor (0-20 points)
    if hour_utc is not None:
        if hour_utc in OPTIMAL_HOURS_UTC:
            factors['time'] = 20
        elif hour_utc not in DANGER_HOURS_UTC:
            factors['time'] = 15
        else:
            factors['time'] = 5
    else:
        factors['time'] = 15

    total = sum(factors.values())

    # Determine tier
    if total >= 90:
        tier = 'GOLDEN'
    elif total >= 75:
        tier = 'SILVER'
    elif total >= 60:
        tier = 'BRONZE'
    else:
        tier = 'STANDARD'

    return {
        'quality_score': total,
        'tier': tier,
        'factors': factors
    }

# ============================================
# COOLDOWNS ET LIMITES
# ============================================

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
