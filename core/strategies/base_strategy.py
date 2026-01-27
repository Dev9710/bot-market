"""
Base Strategy - Classe abstraite pour les stratégies de trading

Définit l'interface commune pour toutes les stratégies par blockchain.
Chaque stratégie doit implémenter:
- should_exclude() : Filtres d'exclusion
- get_signal_quality() : Qualité du signal (A+, A, B, None)
- calculate_score() : Score ajusté avec bonus/malus
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from .signal_config import (
    get_sltp_config,
    calculate_sltp_prices,
    get_position_size_percent,
)


class BaseStrategy(ABC):
    """
    Classe abstraite définissant l'interface d'une stratégie de trading.

    Chaque blockchain a sa propre implémentation avec:
    - Ses filtres d'exclusion
    - Ses critères de signal quality
    - Ses bonus/malus de scoring
    """

    # À définir dans les sous-classes
    NETWORK_NAME: str = ""

    # ============================================
    # MÉTHODES ABSTRAITES (à implémenter)
    # ============================================

    @abstractmethod
    def should_exclude(self, alert: Dict) -> Tuple[bool, str]:
        """
        Vérifie si l'alerte doit être exclue.

        Args:
            alert: Données de l'alerte

        Returns:
            (should_exclude, reason)
        """
        pass

    @abstractmethod
    def get_signal_quality(self, alert: Dict) -> Optional[str]:
        """
        Détermine la qualité du signal.

        Args:
            alert: Données de l'alerte

        Returns:
            'A+' : Signal premium
            'A'  : Signal fort
            'B'  : Signal correct
            None : NO_SIGNAL - ignorer
        """
        pass

    @abstractmethod
    def calculate_score(self, alert: Dict, base_score: int) -> int:
        """
        Calcule le score ajusté avec bonus/malus.

        Args:
            alert: Données de l'alerte
            base_score: Score de base

        Returns:
            Score ajusté (0-100)
        """
        pass

    # ============================================
    # MÉTHODES UTILITAIRES (communes)
    # ============================================

    def _get_hour(self, alert: Dict) -> int:
        """Extrait l'heure UTC de l'alerte."""
        ts = alert.get('timestamp') or alert.get('created_at') or '12:00'
        try:
            return int(str(ts)[11:13])
        except (ValueError, IndexError):
            return 12

    def _safe_get(self, alert: Dict, key: str, default=0):
        """Récupère une valeur avec gestion des None."""
        value = alert.get(key)
        return value if value is not None else default

    # ============================================
    # MÉTHODES COMPLÈTES (utilisent les abstraites)
    # ============================================

    def get_signal_with_exclusion(self, alert: Dict) -> Optional[str]:
        """
        Détermine le signal en vérifiant d'abord les exclusions.

        Args:
            alert: Données de l'alerte

        Returns:
            'A+', 'A', 'B', ou None
        """
        # Vérifier exclusions d'abord
        excluded, reason = self.should_exclude(alert)
        if excluded:
            return None

        return self.get_signal_quality(alert)

    def get_adjusted_score(self, alert: Dict) -> int:
        """
        Calcule le score ajusté complet.

        Args:
            alert: Données de l'alerte

        Returns:
            Score ajusté (0-100)
        """
        base_score = alert.get('base_score', alert.get('score', 50))
        score = self.calculate_score(alert, base_score)
        return max(0, min(100, score))

    def analyze(self, alert: Dict) -> Dict:
        """
        Analyse complète d'une alerte avec cette stratégie.

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
            - network: str
        """
        network = self.NETWORK_NAME

        # Vérifier exclusions
        is_excluded, exclusion_reason = self.should_exclude(alert)

        # Obtenir signal quality
        signal_quality = None if is_excluded else self.get_signal_quality(alert)

        # Calculer score ajusté
        adjusted_score = self.get_adjusted_score(alert)

        # Position size
        position_size_percent = get_position_size_percent(signal_quality)

        # SL/TP config
        entry_price = alert.get('price_usd', alert.get('entry_price', 0))
        sltp_config = calculate_sltp_prices(entry_price, network) if entry_price else {}

        # Recommandation
        recommendation = self._get_recommendation(
            signal_quality, is_excluded, exclusion_reason
        )

        return {
            'signal_quality': signal_quality,
            'is_excluded': is_excluded,
            'exclusion_reason': exclusion_reason,
            'adjusted_score': adjusted_score,
            'position_size_percent': position_size_percent,
            'sltp_config': sltp_config,
            'recommendation': recommendation,
            'network': network.upper(),
        }

    def _get_recommendation(
        self,
        signal_quality: Optional[str],
        is_excluded: bool,
        exclusion_reason: str
    ) -> str:
        """Génère la recommandation basée sur l'analyse."""
        if is_excluded:
            return f"EVITER - {exclusion_reason}"

        if signal_quality == 'A+':
            return "SIGNAL_A+ - Executer immediatement (100%)"
        elif signal_quality == 'A':
            return "SIGNAL_A - Executer (75%)"
        elif signal_quality == 'B':
            return "SIGNAL_B - Executer avec prudence (50%)"
        else:
            return "NO_SIGNAL - Ignorer"

    def format_message(self, alert: Dict, analysis: Dict = None) -> str:
        """
        Formate un message pour afficher l'analyse du signal.

        Args:
            alert: Données de l'alerte
            analysis: Résultat de analyze (optionnel)

        Returns:
            Message formaté
        """
        if analysis is None:
            analysis = self.analyze(alert)

        signal = analysis['signal_quality']
        network = analysis['network']

        # Indicateur selon signal
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
