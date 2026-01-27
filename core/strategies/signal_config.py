"""
Signal Config - Configuration partagée pour les stratégies de trading

Contient:
- Configuration SL/TP par réseau
- Position sizing par qualité de signal
- Fonctions utilitaires de configuration
"""

from typing import Dict, Optional


# ============================================
# CONFIGURATION SL/TP PAR RÉSEAU
# ============================================

NETWORK_SLTP_CONFIG = {
    'solana': {
        'stop_loss_percent': -12,  # -12% (était -10%)
        'tp1_percent': 7,          # +7% (était +5%)
        'tp2_percent': 12,         # +12% (était +10%)
        'tp3_percent': 20,         # +20% (était +15%)
        'timeout_hours': 12,       # Sortir après 12h sans mouvement
    },
    'eth': {
        'stop_loss_percent': -15,  # -15% (était -10%) - gas fees + volatilité
        'tp1_percent': 8,          # +8% (était +5%) - couvrir gas
        'tp2_percent': 15,         # +15% (était +10%)
        'tp3_percent': 25,         # +25% (était +15%)
        'timeout_hours': 6,        # Plus court sur ETH
    },
}

# Configuration par défaut pour les réseaux non optimisés
DEFAULT_SLTP_CONFIG = {
    'stop_loss_percent': -10,
    'tp1_percent': 5,
    'tp2_percent': 10,
    'tp3_percent': 15,
    'timeout_hours': 24,
}


# ============================================
# POSITION SIZING PAR QUALITÉ DE SIGNAL
# ============================================

SIGNAL_POSITION_SIZE = {
    'A++': 1.25,  # 125% - Zone Optimale (WR ~85%+)
    'A+': 1.0,    # 100%
    'A': 0.75,    # 75%
    'B': 0.50,    # 50%
    None: 0.0,    # 0% - NO_SIGNAL
}


# ============================================
# FONCTIONS D'ACCÈS À LA CONFIGURATION
# ============================================

def get_sltp_config(network: str) -> Dict:
    """
    Retourne la configuration SL/TP optimisée pour un réseau.

    Args:
        network: Nom du réseau

    Returns:
        Dict avec stop_loss_percent, tp1_percent, tp2_percent, tp3_percent, timeout_hours
    """
    network = network.lower()

    if network in NETWORK_SLTP_CONFIG:
        return NETWORK_SLTP_CONFIG[network].copy()

    return DEFAULT_SLTP_CONFIG.copy()


def calculate_sltp_prices(entry_price: float, network: str) -> Dict:
    """
    Calcule les prix SL/TP basés sur la configuration réseau.

    Args:
        entry_price: Prix d'entrée
        network: Nom du réseau

    Returns:
        Dict avec stop_loss_price, tp1_price, tp2_price, tp3_price
    """
    if entry_price <= 0:
        return {}

    config = get_sltp_config(network)

    return {
        'stop_loss_price': entry_price * (1 + config['stop_loss_percent'] / 100),
        'tp1_price': entry_price * (1 + config['tp1_percent'] / 100),
        'tp2_price': entry_price * (1 + config['tp2_percent'] / 100),
        'tp3_price': entry_price * (1 + config['tp3_percent'] / 100),
        'stop_loss_percent': config['stop_loss_percent'],
        'tp1_percent': config['tp1_percent'],
        'tp2_percent': config['tp2_percent'],
        'tp3_percent': config['tp3_percent'],
        'timeout_hours': config['timeout_hours'],
    }


def get_position_size(signal: Optional[str], base_amount: float) -> float:
    """
    Retourne le montant à investir selon le signal.

    Args:
        signal: Qualité du signal ('A+', 'A', 'B', None)
        base_amount: Montant de base à investir

    Returns:
        Montant ajusté selon le signal
    """
    multiplier = SIGNAL_POSITION_SIZE.get(signal, 0.0)
    return base_amount * multiplier


def get_position_size_percent(signal: Optional[str]) -> int:
    """
    Retourne le pourcentage de position selon le signal.

    Args:
        signal: Qualité du signal ('A+', 'A', 'B', None)

    Returns:
        Pourcentage (0-100)
    """
    multiplier = SIGNAL_POSITION_SIZE.get(signal, 0.0)
    return int(multiplier * 100)


# ============================================
# CONSTANTES POUR DOCUMENTATION
# ============================================

SIGNAL_DESCRIPTIONS = {
    'A++': {
        'name': 'SIGNAL_A++ (Zone Optimale)',
        'description': 'Zone Optimale Railway data - Execution prioritaire',
        'expected_wr_solana': '85%+',
        'expected_wr_eth': '83%+',
        'position_size': '125%',
        'criteria_solana': 'Vol1-5M + Liq<200K + Age<6h',
        'criteria_eth': 'Vol50-100K + Liq<100K + Age<6h',
    },
    'A+': {
        'name': 'SIGNAL_A+ (Premium)',
        'description': 'Conditions optimales - Execution immediate',
        'expected_wr_solana': '73.8%',
        'expected_wr_eth': '72.3%',
        'position_size': '100%',
    },
    'A': {
        'name': 'SIGNAL_A (Fort)',
        'description': 'Signal fort - Execution recommandee',
        'expected_wr_solana': '65%',
        'expected_wr_eth': '60%',
        'position_size': '75%',
    },
    'B': {
        'name': 'SIGNAL_B (Correct)',
        'description': 'Signal correct - Execution avec prudence',
        'expected_wr_solana': '55%',
        'expected_wr_eth': '51%',
        'position_size': '50%',
    },
    None: {
        'name': 'NO_SIGNAL',
        'description': 'Pas de signal - Ignorer',
        'expected_wr_solana': 'N/A',
        'expected_wr_eth': 'N/A',
        'position_size': '0%',
    },
}
