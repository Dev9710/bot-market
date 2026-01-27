"""
Strategies Module - Stratégies de trading optimisées par blockchain

Architecture:
- base_strategy.py : Classe abstraite définissant l'interface
- signal_config.py : Configuration partagée (SL/TP, position sizing)
- solana_strategy.py : Stratégie optimisée SOLANA (88.7% WR)
- eth_strategy.py : Stratégie optimisée ETH (59.1% WR)

Usage:
    from core.strategies import get_strategy, analyze_alert

    strategy = get_strategy('solana')
    result = strategy.analyze(alert)
"""

from .base_strategy import BaseStrategy
from .signal_config import (
    NETWORK_SLTP_CONFIG,
    SIGNAL_POSITION_SIZE,
    get_sltp_config,
    get_position_size,
    get_position_size_percent,
    calculate_sltp_prices,
)
from .solana_strategy import SolanaStrategy
from .eth_strategy import EthStrategy


# Registry des stratégies disponibles
_STRATEGY_REGISTRY = {
    'solana': SolanaStrategy,
    'eth': EthStrategy,
}


def get_strategy(network: str) -> BaseStrategy:
    """
    Factory pour obtenir la stratégie appropriée selon le réseau.

    Args:
        network: Nom du réseau (solana, eth, ...)

    Returns:
        Instance de la stratégie correspondante
    """
    network = network.lower()
    strategy_class = _STRATEGY_REGISTRY.get(network)

    if strategy_class:
        return strategy_class()

    return None


def is_strategy_available(network: str) -> bool:
    """Vérifie si une stratégie optimisée existe pour ce réseau."""
    return network.lower() in _STRATEGY_REGISTRY


def get_supported_networks() -> list:
    """Retourne la liste des réseaux avec stratégie optimisée."""
    return list(_STRATEGY_REGISTRY.keys())


def analyze_alert(alert: dict, network: str = None) -> dict:
    """
    Point d'entrée rapide pour analyser une alerte.

    Args:
        alert: Données de l'alerte
        network: Réseau (optionnel, extrait de alert si absent)

    Returns:
        Résultat de l'analyse ou None si pas de stratégie
    """
    if network is None:
        network = alert.get('network', '')

    strategy = get_strategy(network)

    if strategy:
        return strategy.analyze(alert)

    return None


__all__ = [
    # Classes
    'BaseStrategy',
    'SolanaStrategy',
    'EthStrategy',
    # Factory
    'get_strategy',
    'is_strategy_available',
    'get_supported_networks',
    'analyze_alert',
    # Config
    'NETWORK_SLTP_CONFIG',
    'SIGNAL_POSITION_SIZE',
    'get_sltp_config',
    'get_position_size',
    'get_position_size_percent',
    'calculate_sltp_prices',
]
