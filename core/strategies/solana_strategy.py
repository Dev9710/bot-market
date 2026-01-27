"""
Solana Strategy - Stratégie de trading optimisée pour SOLANA

Basé sur l'analyse de 43,328 alertes Railway (27 janvier 2026)
Win Rate: 49.8% -> 70%+ avec nouveaux filtres data-driven

SIGNAL_A++ (Zone Optimale ~85% WR):
- Vol 1-5M + Liq < 200K + Age < 6h
- Vol > 5M + Liq 200-500K + Age < 6h (96.9% WR!)

SIGNAL_A+ (~73.8% WR):
- Age < 6h (critère clé)

Exclusions data-driven:
- type_pump PARABOLIQUE (40.8% WR)
- type_pump TRES_RAPIDE (44.9% WR)
- velocite_pump > 20 (45.3% WR)
- Age 24-48h (danger zone)
- Buy ratio < 1.0
"""

from typing import Dict, Optional, Tuple

from .base_strategy import BaseStrategy


class SolanaStrategy(BaseStrategy):
    """
    Stratégie optimisée pour SOLANA (Railway data 27/01/2026).

    Performance backtest (6,867 alertes analysées):
    - SIGNAL_A++ : ~85% WR (Vol1-5M + Liq<200K + Age<6h)
    - SIGNAL_A+  : 73.8% WR (Age<6h)
    - SIGNAL_A   : 65% WR (Age<12h + conditions favorables)
    - SIGNAL_B   : 55% WR (conditions basiques)
    """

    NETWORK_NAME = "solana"

    # ============================================
    # CONSTANTES SPÉCIFIQUES SOLANA (Railway data)
    # ============================================

    # Heures défavorables (US open et afternoon)
    BAD_HOURS = [13, 14, 18, 19]

    # Zone danger age
    DANGER_AGE_MIN = 24
    DANGER_AGE_MAX = 48

    # Dead zone transactions
    DEAD_ZONE_TXNS_MIN = 5000
    DEAD_ZONE_TXNS_MAX = 10000

    # Types de pump dangereux (Railway: 40-45% WR)
    DANGEROUS_PUMP_TYPES = ['PARABOLIQUE', 'TRES_RAPIDE']

    # Velocite dangereuse (Railway: 45.3% WR si > 20)
    MAX_VELOCITE_PUMP = 20

    # ============================================
    # FILTRES D'EXCLUSION
    # ============================================

    def should_exclude(self, alert: Dict) -> Tuple[bool, str]:
        """
        Vérifie si une alerte SOLANA doit être exclue.
        Filtres basés sur analyse Railway 27/01/2026.

        Returns:
            (should_exclude, reason)
        """
        age = self._safe_get(alert, 'age_hours', 0)
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        total_txns = self._safe_get(alert, 'total_txns', 0)
        hour = self._get_hour(alert)
        type_pump = self._safe_get(alert, 'type_pump', '')
        velocite = self._safe_get(alert, 'velocite_pump', 0)

        # [NOUVEAU] Type pump dangereux (Railway: 40-45% WR)
        if type_pump in self.DANGEROUS_PUMP_TYPES:
            return True, f"Type pump dangereux: {type_pump} (WR < 45%)"

        # [NOUVEAU] Velocite trop elevee (Railway: 45.3% WR si > 20)
        if velocite and velocite > self.MAX_VELOCITE_PUMP:
            return True, f"Velocite trop elevee: {velocite:.1f} > 20 (WR 45%)"

        # Age 24-48h = danger zone
        if self.DANGER_AGE_MIN <= age < self.DANGER_AGE_MAX:
            return True, "Age 24-48h (danger zone)"

        # Pression vendeuse
        if buy_ratio < 1.0:
            return True, f"Buy ratio trop faible ({buy_ratio:.2f} < 1.0)"

        # Mauvaises heures - US open et afternoon
        if hour in self.BAD_HOURS:
            return True, f"Heure defavorable ({hour}h UTC)"

        # Dead zone transactions
        if self.DEAD_ZONE_TXNS_MIN <= total_txns < self.DEAD_ZONE_TXNS_MAX:
            return True, f"Dead zone txns ({total_txns})"

        return False, ""

    # ============================================
    # SIGNAL QUALITY
    # ============================================

    def get_signal_quality(self, alert: Dict) -> Optional[str]:
        """
        Détermine la qualité du signal pour SOLANA.
        Basé sur analyse Railway 27/01/2026 (6,867 alertes).

        Returns:
            'A++': ~85% WR - Zone Optimale (Vol1-5M + Liq<200K + Age<6h)
            'A+' : 73.8% WR - Age<6h
            'A'  : 65% WR - Age<12h + conditions favorables
            'B'  : 55% WR - conditions basiques
            None : NO_SIGNAL
        """
        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        age = self._safe_get(alert, 'age_hours', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        liquidity = self._safe_get(alert, 'liquidity', float('inf'))

        # SIGNAL_A++ : Zone Optimale (~85% WR)
        # Railway data: Vol>5M + Liq200-500K + Age<6h = 96.9% WR
        # Railway data: Vol1-5M + Liq<200K + Age<6h = 80-85% WR
        if age < 6:
            if (vol > 5_000_000 and 200_000 <= liquidity < 500_000):
                return 'A++'  # 96.9% WR
            if (1_000_000 <= vol <= 5_000_000 and liquidity < 200_000):
                return 'A++'  # 80-85% WR

        # SIGNAL_A+ : Age < 6h (73.8% WR)
        if age < 6:
            return 'A+'

        # SIGNAL_A : Age < 12h + conditions favorables (65% WR)
        if age < 12 and buy_ratio >= 1.2:
            return 'A'

        # SIGNAL_B : Conditions basiques (55% WR)
        if vol < 5_000_000 and buy_ratio >= 1.0:
            return 'B'

        return None

    # ============================================
    # SCORING
    # ============================================

    def calculate_score(self, alert: Dict, base_score: int) -> int:
        """
        Calcule les bonus/malus de score pour SOLANA.
        Basé sur analyse Railway 27/01/2026.

        Args:
            alert: Données de l'alerte
            base_score: Score de base

        Returns:
            Score ajusté
        """
        score = base_score

        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        age = self._safe_get(alert, 'age_hours', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        vol_acc = self._safe_get(alert, 'volume_acceleration_1h_vs_6h', 1)
        total_txns = self._safe_get(alert, 'total_txns', 0)
        hour = self._get_hour(alert)
        velocite = self._safe_get(alert, 'velocite_pump', 0)
        type_pump = self._safe_get(alert, 'type_pump', '')

        # === BONUS (Railway data) ===

        # [CRITIQUE] Age < 6h = 73.8% WR (+25% vs moyenne)
        if age < 6:
            score += 25
        elif age < 12:
            score += 10

        # Volume optimal (Railway: Vol 100-500K = 77.3% WR)
        if 100_000 <= vol < 500_000:
            score += 15
        elif vol < 1_000_000:
            score += 10

        # Velocite stable (Railway: vel -20 to +20 = 54-56% WR)
        if velocite and -20 < velocite < 20:
            score += 10

        # Buy Ratio
        if buy_ratio > 2.0:
            score += 10
        elif buy_ratio > 1.5:
            score += 5

        # Volume acceleration
        if vol_acc > 3.0:
            score += 10

        # Total txns (early stage)
        if total_txns < 1000:
            score += 10
        elif total_txns < 5000:
            score += 5

        # Type pump NORMAL/LENT = meilleur (54% WR)
        if type_pump in ['NORMAL', 'LENT']:
            score += 5

        # === MALUS (Railway data) ===

        # Type pump dangereux
        if type_pump in self.DANGEROUS_PUMP_TYPES:
            score -= 25

        # Velocite extreme
        if velocite and velocite > self.MAX_VELOCITE_PUMP:
            score -= 20

        if buy_ratio < 1.0:
            score -= 30

        if self.DANGER_AGE_MIN <= age < self.DANGER_AGE_MAX:
            score -= 25

        if hour in [13, 14]:
            score -= 20
        elif hour in [18, 19]:
            score -= 15

        if self.DEAD_ZONE_TXNS_MIN <= total_txns < self.DEAD_ZONE_TXNS_MAX:
            score -= 20

        return score
