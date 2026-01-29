"""
Core package - Logique métier principale du scanner

Modules:
- alerts.py : Gestion des alertes
- filters.py : Filtres de tokens
- scoring.py : Système de scoring V3/V4
- signals.py : Analyse des signaux
- scanner_steps.py : Étapes du scanner
- strategy_validator.py : Validation des stratégies
- signal_strategy.py : Facade stratégies SIGNAL

Sous-packages:
- strategies/ : Stratégies optimisées par blockchain (ETH, SOLANA)
"""

from core.scoring import (
    calculate_base_score,
    calculate_momentum_bonus,
    calculate_final_score,
    calculate_final_score_v4,
    calculate_confidence_tier,
    calculate_confidence_score,
    analyze_whale_activity,
)

from core.signal_strategy import (
    get_signal_quality,
    should_exclude,
    analyze_signal,
    get_strategy,
    is_strategy_available,
)

__all__ = [
    # Scoring
    'calculate_base_score',
    'calculate_momentum_bonus',
    'calculate_final_score',
    'calculate_final_score_v4',
    'calculate_confidence_tier',
    'calculate_confidence_score',
    'analyze_whale_activity',
    # Signal Strategy
    'get_signal_quality',
    'should_exclude',
    'analyze_signal',
    'get_strategy',
    'is_strategy_available',
]
