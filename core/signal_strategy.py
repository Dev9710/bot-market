"""
Signal Strategy - Facade pour les stratégies de trading optimisées ETH & SOLANA

Ce module sert de facade pour maintenir la rétro-compatibilité
avec le code existant tout en utilisant la nouvelle architecture modulaire.

Architecture:
    core/strategies/
    ├── __init__.py       # Factory et exports
    ├── base_strategy.py  # Classe abstraite
    ├── signal_config.py  # Configuration SL/TP, position sizing
    ├── solana_strategy.py # Stratégie SOLANA (88.7% WR)
    └── eth_strategy.py   # Stratégie ETH (59.1% WR)

Nomenclature SIGNAL:
- SIGNAL_A+ : Conditions optimales (88.7% WR Solana, 59.1% WR ETH)
- SIGNAL_A  : Signal fort (78% WR Solana, 56.4% WR ETH)
- SIGNAL_B  : Signal correct (62.5% WR Solana, 47% WR ETH)
- None      : NO_SIGNAL - ignorer

Position sizing:
- A+ : 100%
- A  : 75%
- B  : 50%
"""

from typing import Dict, Optional, Tuple

# Import depuis la nouvelle architecture modulaire
from core.strategies import (
    get_strategy,
    is_strategy_available,
    get_supported_networks,
    analyze_alert,
    NETWORK_SLTP_CONFIG,
    SIGNAL_POSITION_SIZE,
    get_sltp_config,
    get_position_size,
    get_position_size_percent,
    calculate_sltp_prices,
)

# Import pour logging
try:
    from utils.helpers import log
except ImportError:
    def log(msg):
        print(msg)


# ============================================
# FONCTIONS DE FACADE (rétro-compatibilité)
# ============================================

def should_exclude_solana(alert: Dict) -> Tuple[bool, str]:
    """
    Vérifie si une alerte SOLANA doit être exclue.
    DEPRECATED: Utiliser get_strategy('solana').should_exclude(alert)
    """
    strategy = get_strategy('solana')
    if strategy:
        return strategy.should_exclude(alert)
    return False, ""


def should_exclude_eth(alert: Dict) -> Tuple[bool, str]:
    """
    Vérifie si une alerte ETH doit être exclue.
    DEPRECATED: Utiliser get_strategy('eth').should_exclude(alert)
    """
    strategy = get_strategy('eth')
    if strategy:
        return strategy.should_exclude(alert)
    return False, ""


def should_exclude(alert: Dict, network: str = None) -> Tuple[bool, str]:
    """
    Point d'entrée principal pour vérifier les exclusions.

    Returns:
        (should_exclude, reason)
    """
    if network is None:
        network = alert.get('network', '').lower()
    else:
        network = network.lower()

    strategy = get_strategy(network)
    if strategy:
        return strategy.should_exclude(alert)

    # Autres réseaux : pas d'exclusion spécifique
    return False, ""


def _get_signal_solana(alert: Dict) -> Optional[str]:
    """
    Détermine la qualité du signal pour SOLANA.
    DEPRECATED: Utiliser get_strategy('solana').get_signal_quality(alert)
    """
    strategy = get_strategy('solana')
    if strategy:
        return strategy.get_signal_quality(alert)
    return None


def _get_signal_eth(alert: Dict) -> Optional[str]:
    """
    Détermine la qualité du signal pour ETH.
    DEPRECATED: Utiliser get_strategy('eth').get_signal_quality(alert)
    """
    strategy = get_strategy('eth')
    if strategy:
        return strategy.get_signal_quality(alert)
    return None


def get_signal_quality(alert: Dict, network: str = None) -> Optional[str]:
    """
    Détermine la qualité du signal pour une alerte.

    Args:
        alert: Données de l'alerte
        network: Réseau (optionnel, extrait de alert si absent)

    Returns:
        'A+' : Signal premium
        'A'  : Signal fort
        'B'  : Signal correct
        None : NO_SIGNAL - ignorer
    """
    if network is None:
        network = alert.get('network', '').lower()
    else:
        network = network.lower()

    # Vérifier exclusions d'abord
    excluded, reason = should_exclude(alert, network)
    if excluded:
        log(f"   EXCLUSION {network.upper()}: {reason}")
        return None

    # Déterminer le signal selon le réseau
    strategy = get_strategy(network)
    if strategy:
        return strategy.get_signal_quality(alert)

    # Autres réseaux : pas de stratégie optimisée
    return None


def _score_solana(alert: Dict, base_score: int) -> int:
    """
    Calcule les bonus/malus de score pour SOLANA.
    DEPRECATED: Utiliser get_strategy('solana').calculate_score(alert, base_score)
    """
    strategy = get_strategy('solana')
    if strategy:
        return strategy.calculate_score(alert, base_score)
    return base_score


def _score_eth(alert: Dict, base_score: int) -> int:
    """
    Calcule les bonus/malus de score pour ETH.
    DEPRECATED: Utiliser get_strategy('eth').calculate_score(alert, base_score)
    """
    strategy = get_strategy('eth')
    if strategy:
        return strategy.calculate_score(alert, base_score)
    return base_score


def calculate_signal_score(alert: Dict, network: str = None) -> int:
    """
    Calcule le score ajusté avec bonus/malus spécifiques au réseau.

    Args:
        alert: Données de l'alerte
        network: Réseau (optionnel)

    Returns:
        Score ajusté (0-100)
    """
    if network is None:
        network = alert.get('network', '').lower()
    else:
        network = network.lower()

    base_score = alert.get('base_score', alert.get('score', 50))

    strategy = get_strategy(network)
    if strategy:
        score = strategy.calculate_score(alert, base_score)
    else:
        score = base_score

    return max(0, min(100, score))


def analyze_signal(alert: Dict) -> Dict:
    """
    Analyse complète d'une alerte avec la stratégie SIGNAL.

    Args:
        alert: Données de l'alerte

    Returns:
        Dict avec:
        - signal_quality: 'A+', 'A', 'B', ou None
        - is_excluded: bool
        - exclusion_reason: str
        - adjusted_score: int
        - position_size_percent: int
        - sltp_config: Dict
        - recommendation: str
    """
    network = alert.get('network', '').lower()

    strategy = get_strategy(network)
    if strategy:
        return strategy.analyze(alert)

    # Fallback pour réseaux non supportés
    entry_price = alert.get('price_usd', alert.get('entry_price', 0))

    return {
        'signal_quality': None,
        'is_excluded': False,
        'exclusion_reason': '',
        'adjusted_score': alert.get('score', 50),
        'position_size_percent': 0,
        'sltp_config': calculate_sltp_prices(entry_price, network) if entry_price else {},
        'recommendation': 'NO_SIGNAL - Reseau non supporte',
        'network': network.upper(),
    }


def format_signal_message(alert: Dict, analysis: Dict = None) -> str:
    """
    Formate un message pour afficher l'analyse du signal.

    Args:
        alert: Données de l'alerte
        analysis: Résultat de analyze_signal (optionnel)

    Returns:
        Message formaté
    """
    if analysis is None:
        analysis = analyze_signal(alert)

    network = analysis.get('network', alert.get('network', '').upper())

    strategy = get_strategy(network.lower())
    if strategy:
        return strategy.format_message(alert, analysis)

    # Fallback formatting
    signal = analysis['signal_quality']

    if signal == 'A+':
        signal_text = "SIGNAL_A+ (Premium)"
    elif signal == 'A':
        signal_text = "SIGNAL_A (Fort)"
    elif signal == 'B':
        signal_text = "SIGNAL_B (Correct)"
    else:
        signal_text = "NO_SIGNAL"

    lines = [
        f"{signal_text} - {network}",
        f"Score ajuste: {analysis['adjusted_score']}/100",
        f"Position: {analysis['position_size_percent']}%",
    ]

    if analysis['is_excluded']:
        lines.append(f"Exclusion: {analysis['exclusion_reason']}")

    if analysis['sltp_config']:
        config = analysis['sltp_config']
        lines.extend([
            f"SL: {config['stop_loss_percent']}% | TP1: +{config['tp1_percent']}% | TP2: +{config['tp2_percent']}% | TP3: +{config['tp3_percent']}%",
            f"Timeout: {config['timeout_hours']}h",
        ])

    lines.append(f"-> {analysis['recommendation']}")

    return "\n".join(lines)


# ============================================
# EXPORTS POUR RETRO-COMPATIBILITE
# ============================================

__all__ = [
    # Config
    'NETWORK_SLTP_CONFIG',
    'SIGNAL_POSITION_SIZE',
    # Exclusion functions
    'should_exclude',
    'should_exclude_solana',
    'should_exclude_eth',
    # Signal quality
    'get_signal_quality',
    # Scoring
    'calculate_signal_score',
    # Position sizing
    'get_position_size',
    'get_position_size_percent',
    # SL/TP
    'get_sltp_config',
    'calculate_sltp_prices',
    # Analysis
    'analyze_signal',
    'format_signal_message',
    # Factory (nouveau)
    'get_strategy',
    'is_strategy_available',
    'get_supported_networks',
    'analyze_alert',
]
