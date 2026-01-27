"""
ETH Strategy - Stratégie de trading optimisée pour Ethereum

Basé sur l'analyse Railway de 43,328 alertes (27 janvier 2026)
Win Rate: 60.8% -> 80%+ avec filtres data-driven

SIGNAL_A++ (Zone Optimale 83.3% WR):
- Vol 50-100K + Liq 50-100K + Age < 6h

SIGNAL_A+ (72.3% WR):
- Vol 50-100K + Liq 30-50K + Age < 6h

Exclusions data-driven:
- concentration_risk MEDIUM (23.1% WR!)
- buy_ratio < 1.0 (0% WR)
- Age > 24h
"""

from typing import Dict, Optional, Tuple

from .base_strategy import BaseStrategy


class EthStrategy(BaseStrategy):
    """
    Stratégie optimisée pour Ethereum (Railway data 27/01/2026).

    Performance backtest (595 alertes analysées):
    - SIGNAL_A++ : 83.3% WR (Vol50-100K + Liq50-100K + Age<6h)
    - SIGNAL_A+  : 72.3% WR (Vol50-100K + Liq30-50K + Age<6h)
    - SIGNAL_A   : 60% WR (Vol<100K + conditions favorables)
    - SIGNAL_B   : 51% WR (conditions basiques)
    """

    NETWORK_NAME = "eth"

    # ============================================
    # CONSTANTES SPÉCIFIQUES ETH (Railway data)
    # ============================================

    # Heures défavorables
    BAD_HOURS = [10, 11, 12, 13, 14, 22, 23]

    # Bonnes heures
    GOOD_HOURS = [0, 1, 2, 3, 4, 6, 7, 8]

    # Seuils de volume (Railway: Vol 50-100K = 75.5% WR)
    MAX_VOLUME_EXCLUDE = 200_000
    OPTIMAL_VOLUME_MIN = 50_000
    OPTIMAL_VOLUME_MAX = 100_000

    # Seuils de liquidité (Railway: Liq 30-50K = 66% WR)
    MAX_LIQUIDITY = 100_000
    OPTIMAL_LIQ_MIN = 30_000
    OPTIMAL_LIQ_MAX = 100_000

    # Age maximum
    MAX_AGE_HOURS = 24

    # Buy ratio minimum (Railway: ratio < 1.0 = 0% WR!)
    MIN_BUY_RATIO = 1.0

    # Concentration risk dangereux (Railway: MEDIUM = 23.1% WR)
    DANGEROUS_CONCENTRATION = ['MEDIUM']

    # ============================================
    # FILTRES D'EXCLUSION
    # ============================================

    def should_exclude(self, alert: Dict) -> Tuple[bool, str]:
        """
        Vérifie si une alerte ETH doit être exclue.
        Filtres basés sur analyse Railway 27/01/2026.

        Returns:
            (should_exclude, reason)
        """
        vol = self._safe_get(alert, 'volume_24h', 0)
        liquidity = self._safe_get(alert, 'liquidity', 0)
        age = self._safe_get(alert, 'age_hours', 0)
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        hour = self._get_hour(alert)

        # [NOUVEAU] Extraction concentration_risk depuis le message
        concentration_risk = self._extract_concentration_risk(alert)

        # [CRITIQUE] concentration_risk MEDIUM = 23.1% WR!
        if concentration_risk in self.DANGEROUS_CONCENTRATION:
            return True, f"Concentration risk dangereux: {concentration_risk} (WR 23%)"

        # [CRITIQUE] buy_ratio < 1.0 = 0% WR!
        if buy_ratio < self.MIN_BUY_RATIO:
            return True, f"Buy ratio trop faible ({buy_ratio:.2f} < 1.0)"

        # Volume trop élevé
        if vol > self.MAX_VOLUME_EXCLUDE:
            return True, f"Volume trop eleve (${vol:,.0f} > $200K)"

        # Liquidité trop élevée
        if liquidity > self.MAX_LIQUIDITY:
            return True, f"Liquidite trop elevee (${liquidity:,.0f} > $100K)"

        # Token trop vieux
        if age > self.MAX_AGE_HOURS:
            return True, f"Token trop vieux ({age:.1f}h > 24h)"

        # Mauvaises heures
        if hour in self.BAD_HOURS:
            return True, f"Heure defavorable ({hour}h UTC)"

        return False, ""

    def _extract_concentration_risk(self, alert: Dict) -> str:
        """Extrait concentration_risk depuis alert_message."""
        msg = self._safe_get(alert, 'alert_message', '')
        if 'concentration : HIGH' in msg or 'concentration: HIGH' in msg:
            return 'HIGH'
        elif 'concentration : MEDIUM' in msg or 'concentration: MEDIUM' in msg:
            return 'MEDIUM'
        elif 'concentration : LOW' in msg or 'concentration: LOW' in msg:
            return 'LOW'
        return 'UNKNOWN'

    # ============================================
    # SIGNAL QUALITY
    # ============================================

    def get_signal_quality(self, alert: Dict) -> Optional[str]:
        """
        Détermine la qualité du signal pour ETH.
        Basé sur analyse Railway 27/01/2026 (595 alertes).

        Returns:
            'A++': 83.3% WR - Vol50-100K + Liq50-100K + Age<6h
            'A+' : 72.3% WR - Vol50-100K + Liq30-50K + Age<6h
            'A'  : 60% WR - Vol<100K + conditions favorables
            'B'  : 51% WR - conditions basiques
            None : NO_SIGNAL
        """
        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        liquidity = self._safe_get(alert, 'liquidity', float('inf'))
        age = self._safe_get(alert, 'age_hours', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)

        # SIGNAL_A++ : Zone Optimale (83.3% WR)
        # Railway: Vol50-100K + Liq50-100K + Age<6h = 83.3% WR
        if (self.OPTIMAL_VOLUME_MIN <= vol < self.OPTIMAL_VOLUME_MAX
            and 50_000 <= liquidity < 100_000
            and age < 6):
            return 'A++'

        # SIGNAL_A+ : (72.3% WR)
        # Railway: Vol50-100K + Liq30-50K + Age<6h = 72.3% WR
        if (self.OPTIMAL_VOLUME_MIN <= vol < self.OPTIMAL_VOLUME_MAX
            and self.OPTIMAL_LIQ_MIN <= liquidity < 50_000
            and age < 6):
            return 'A+'

        # SIGNAL_A : Vol optimal + Age jeune (60% WR)
        if vol < self.OPTIMAL_VOLUME_MAX and age < 6:
            return 'A'

        # SIGNAL_B : Vol acceptable (51% WR)
        if vol < self.OPTIMAL_VOLUME_MAX and buy_ratio >= 1.5:
            return 'B'

        return None

    # ============================================
    # SCORING
    # ============================================

    def calculate_score(self, alert: Dict, base_score: int) -> int:
        """
        Calcule les bonus/malus de score pour ETH.
        Basé sur analyse Railway 27/01/2026.

        Args:
            alert: Données de l'alerte
            base_score: Score de base

        Returns:
            Score ajusté
        """
        score = base_score

        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        liquidity = self._safe_get(alert, 'liquidity', float('inf'))
        age = self._safe_get(alert, 'age_hours', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        hour = self._get_hour(alert)

        concentration_risk = self._extract_concentration_risk(alert)

        # === BONUS (Railway data) ===

        # [CRITIQUE] Volume optimal 50-100K = 75.5% WR
        if self.OPTIMAL_VOLUME_MIN <= vol < self.OPTIMAL_VOLUME_MAX:
            score += 20
        elif vol < 50_000:
            score += 10

        # Liquidité optimale 30-50K = 66% WR
        if self.OPTIMAL_LIQ_MIN <= liquidity < 50_000:
            score += 15
        elif liquidity < self.OPTIMAL_LIQ_MAX:
            score += 5

        # Age < 6h = 60.5% WR
        if age < 6:
            score += 15

        # Buy Ratio > 1.5 = 61.7% WR
        if buy_ratio > 2.0:
            score += 10
        elif buy_ratio > 1.5:
            score += 5

        # Concentration LOW = 61.7% WR
        if concentration_risk == 'LOW':
            score += 10

        # Bonnes heures
        if hour in [1, 2, 3]:
            score += 5

        # === MALUS (Railway data) ===

        # [CRITIQUE] concentration_risk MEDIUM = 23.1% WR
        if concentration_risk in self.DANGEROUS_CONCENTRATION:
            score -= 30

        # buy_ratio < 1.0 = 0% WR
        if buy_ratio < 1.0:
            score -= 40

        # Volume trop élevé
        if vol > 150_000:
            score -= 15

        # Mauvaises heures
        if hour in [10, 11, 12, 13, 14]:
            score -= 20
        elif hour in [22, 23]:
            score -= 15

        # Token trop vieux
        if age > 24:
            score -= 25

        return score
