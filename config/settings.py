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
# Objectif: 8-10 alertes/jour | Score 91.4 | WR 45-58% | ROI +4-7%/mois

# Configuration DASHBOARD (8-10 alertes/jour) - V3.3: Thresholds reduced for better coverage
DASHBOARD_CONFIG = {
    'MIN_VELOCITE_PUMP': 5.0,
    'NETWORK_SCORE_FILTERS': {
        'eth': {'min_score': 70, 'min_velocity': 5},      # V3.3: Reduced 78→70 for more ETH alerts
        'base': {'min_score': 75, 'min_velocity': 7},     # V3.3: Reduced 82→75
        'bsc': {'min_score': 72, 'min_velocity': 5},      # V3.3: Reduced 80→72 for more BSC alerts
        'solana': {'min_score': 68, 'min_velocity': 5},   # V3.3: Reduced 72→68 (already performing)
        'polygon_pos': {'min_score': 70, 'min_velocity': 5},  # V3.3: Reduced 75→70
        'avax': {'min_score': 72, 'min_velocity': 5},     # V3.3: Reduced 80→72
    },
    'LIQUIDITY': {
        'eth': (30000, 600000),         # V3.4: Reduced 80K→30K to catch early pools
        'base': (100000, 2500000),      # V3.4: Reduced 250K→100K
        'bsc': (20000, 6000000),        # V3.4: Reduced 400K→20K (NEW pools have only $4K-$20K!)
        'solana': (30000, 300000),      # V3.4: Reduced 80K→30K for consistency
        'polygon_pos': (20000, 500000), # V3.4: Reduced 50K→20K
        'avax': (30000, 800000),        # V3.4: Reduced 100K→30K
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
