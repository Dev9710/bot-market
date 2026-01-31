"""
ETH Strategy - Stratégie de trading optimisée pour Ethereum

Basé sur l'analyse Railway de 49,092 alertes (30 janvier 2026)
Win Rate: 60.8% -> 80%+ avec filtres data-driven v2

SIGNAL_A++ (Zone Optimale 80-92% WR):
- vol_accel_1h_vs_6h < 0.2 (91.7% WR!)
- vol_accel_1h_vs_6h 0.2-0.5 (80.0% WR)
- decision_tp SECURISER_HOLD (73.3% WR)
- decision_tp NOUVEAUX_NIVEAUX (70.6% WR)
- Vol 50-100K + Liq 50-100K + Age < 6h (83.3% WR)

SIGNAL_A+ (65-72% WR):
- volume_1h 25-50K (69.0% WR)
- vol_accel_6h_vs_24h 0.5-1.0 (68.4% WR)

Exclusions data-driven v2:
- concentration_risk MEDIUM (23.1% WR!)
- buy_ratio < 1.0 (0% WR)
- Heures 13h-15h (< 25% WR)
- decision_tp ENTRER (47.8% WR)
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
    # CONSTANTES SPÉCIFIQUES ETH (Railway data v2 - 30/01/2026)
    # ============================================

    # Heures défavorables (Railway: < 25% WR)
    BAD_HOURS = [13, 14, 15, 21, 22]

    # Bonnes heures (Railway: 70%+ WR)
    GOOD_HOURS = [1, 2, 3, 4, 7, 8, 16, 19]

    # Heures premium (Railway: 80%+ WR)
    PREMIUM_HOURS = [4, 7, 19]  # 04h=87.8%, 07h=79.5%, 19h=100%

    # Jours optimaux (Railway: 70%+ WR)
    GOOD_DAYS = ['Saturday', 'Sunday']

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

    # decision_tp_tracking premium (Railway: 70%+ WR)
    PREMIUM_TP_DECISIONS = ['SECURISER_HOLD', 'NOUVEAUX_NIVEAUX']

    # decision_tp_tracking à éviter (Railway: < 50% WR)
    AVOID_TP_DECISIONS = ['ENTRER']

    # ============================================
    # FILTRES D'EXCLUSION
    # ============================================

    def should_exclude(self, alert: Dict) -> Tuple[bool, str]:
        """
        Vérifie si une alerte ETH doit être exclue.
        Filtres basés sur analyse Railway 30/01/2026 (1,240 alertes).

        Returns:
            (should_exclude, reason)
        """
        vol = self._safe_get(alert, 'volume_24h', 0)
        liquidity = self._safe_get(alert, 'liquidity', 0)
        age = self._safe_get(alert, 'age_hours', 0)
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        hour = self._get_hour(alert)
        decision_tp = self._safe_get(alert, 'decision_tp_tracking', '')

        # Extraction concentration_risk depuis le message
        concentration_risk = self._extract_concentration_risk(alert)

        # [CRITIQUE] concentration_risk MEDIUM = 23.1% WR!
        if concentration_risk in self.DANGEROUS_CONCENTRATION:
            return True, f"Concentration risk dangereux: {concentration_risk} (WR 23%)"

        # [CRITIQUE] buy_ratio < 1.0 = 0% WR!
        if buy_ratio < self.MIN_BUY_RATIO:
            return True, f"Buy ratio trop faible ({buy_ratio:.2f} < 1.0)"

        # [NOUVEAU v2] Heures critiques 13h-15h (< 25% WR)
        if hour in [13, 14, 15]:
            return True, f"Heure critique ({hour}h UTC - WR < 25%)"

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
        Basé sur analyse Railway 30/01/2026 (1,240 alertes analysables).

        Returns:
            'A++': 80-92% WR - Zone Optimale
            'A+' : 65-72% WR - Conditions favorables
            'A'  : 60% WR - Vol<100K + conditions favorables
            'B'  : 51% WR - conditions basiques
            None : NO_SIGNAL
        """
        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        liquidity = self._safe_get(alert, 'liquidity', float('inf'))
        age = self._safe_get(alert, 'age_hours', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        vol_accel_1h = self._safe_get(alert, 'volume_acceleration_1h_vs_6h', 1)
        vol_accel_6h = self._safe_get(alert, 'volume_acceleration_6h_vs_24h', 1)
        volume_1h = self._safe_get(alert, 'volume_1h', 0)
        decision_tp = self._safe_get(alert, 'decision_tp_tracking', '')
        is_first_alert = self._safe_get(alert, 'is_alerte_suivante', 1) == 0
        hour = self._get_hour(alert)

        # ============================================
        # SIGNAL_A++ : Zone Optimale (80-92% WR)
        # ============================================

        # [NOUVEAU v2] vol_accel_1h_vs_6h < 0.2 = 91.7% WR (acheter le dip!)
        if vol_accel_1h < 0.2 and age < 12:
            return 'A++'

        # [NOUVEAU v2] vol_accel_1h_vs_6h 0.2-0.5 = 80.0% WR
        if 0.2 <= vol_accel_1h < 0.5 and age < 12:
            return 'A++'

        # [NOUVEAU v2] decision_tp SECURISER_HOLD = 73.3% WR
        if decision_tp == 'SECURISER_HOLD':
            return 'A++'

        # [NOUVEAU v2] decision_tp NOUVEAUX_NIVEAUX = 70.6% WR
        if decision_tp == 'NOUVEAUX_NIVEAUX':
            return 'A++'

        # [NOUVEAU v2] Heures premium (87.8% WR à 04h, 79.5% à 07h)
        if hour in self.PREMIUM_HOURS and age < 12:
            return 'A++'

        # Railway original: Vol50-100K + Liq50-100K + Age<6h = 83.3% WR
        if (self.OPTIMAL_VOLUME_MIN <= vol < self.OPTIMAL_VOLUME_MAX
            and 50_000 <= liquidity < 100_000
            and age < 6):
            return 'A++'

        # ============================================
        # SIGNAL_A+ : (65-72% WR)
        # ============================================

        # [NOUVEAU v2] volume_1h 25-50K = 69.0% WR
        if 25_000 <= volume_1h < 50_000 and age < 12:
            return 'A+'

        # [NOUVEAU v2] vol_accel_6h_vs_24h 0.5-1.0 = 68.4% WR
        if 0.5 <= vol_accel_6h < 1.0 and age < 12:
            return 'A+'

        # [NOUVEAU v2] Première alerte sur token = 62.7% WR
        if is_first_alert and buy_ratio >= 1.2:
            return 'A+'

        # Railway original: Vol50-100K + Liq30-50K + Age<6h = 72.3% WR
        if (self.OPTIMAL_VOLUME_MIN <= vol < self.OPTIMAL_VOLUME_MAX
            and self.OPTIMAL_LIQ_MIN <= liquidity < 50_000
            and age < 6):
            return 'A+'

        # ============================================
        # SIGNAL_A : Vol optimal + Age jeune (60% WR)
        # ============================================
        if vol < self.OPTIMAL_VOLUME_MAX and age < 6:
            return 'A'

        # ============================================
        # SIGNAL_B : Vol acceptable (51% WR)
        # ============================================
        if vol < self.OPTIMAL_VOLUME_MAX and buy_ratio >= 1.5:
            return 'B'

        return None

    # ============================================
    # SCORING
    # ============================================

    def calculate_score(self, alert: Dict, base_score: int) -> int:
        """
        Calcule les bonus/malus de score pour ETH.
        Basé sur analyse Railway 30/01/2026 (1,240 alertes).

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
        vol_accel_1h = self._safe_get(alert, 'volume_acceleration_1h_vs_6h', 1)
        vol_accel_6h = self._safe_get(alert, 'volume_acceleration_6h_vs_24h', 1)
        volume_1h = self._safe_get(alert, 'volume_1h', 0)
        decision_tp = self._safe_get(alert, 'decision_tp_tracking', '')
        is_first_alert = self._safe_get(alert, 'is_alerte_suivante', 1) == 0
        total_txns = self._safe_get(alert, 'total_txns', float('inf'))

        concentration_risk = self._extract_concentration_risk(alert)

        # Obtenir le jour de la semaine
        day_of_week = self._get_day_of_week(alert)

        # === BONUS (Railway data v2) ===

        # [NOUVEAU v2] vol_accel_1h_vs_6h < 0.5 = 80-92% WR (acheter le dip!)
        if vol_accel_1h < 0.2:
            score += 30
        elif vol_accel_1h < 0.5:
            score += 20

        # [NOUVEAU v2] decision_tp premium = 70%+ WR
        if decision_tp in self.PREMIUM_TP_DECISIONS:
            score += 20

        # [NOUVEAU v2] volume_1h 25-50K = 69.0% WR
        if 25_000 <= volume_1h < 50_000:
            score += 15
        elif 50_000 <= volume_1h < 100_000:
            score += 10

        # [NOUVEAU v2] vol_accel_6h_vs_24h 0.5-1.0 = 68.4% WR
        if 0.5 <= vol_accel_6h < 1.0:
            score += 15

        # [NOUVEAU v2] Première alerte = 62.7% WR
        if is_first_alert:
            score += 10

        # [NOUVEAU v2] total_txns < 500 = 57.5% WR
        if total_txns < 500:
            score += 10

        # [NOUVEAU v2] Heures premium (87.8% WR à 04h)
        if hour in self.PREMIUM_HOURS:
            score += 20
        elif hour in self.GOOD_HOURS:
            score += 10

        # [NOUVEAU v2] Samedi/Dimanche = 70-76% WR
        if day_of_week in self.GOOD_DAYS:
            score += 15

        # Volume optimal 50-100K = 75.5% WR
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

        # === MALUS (Railway data v2) ===

        # [CRITIQUE] concentration_risk MEDIUM = 23.1% WR
        if concentration_risk in self.DANGEROUS_CONCENTRATION:
            score -= 30

        # buy_ratio < 1.0 = 0% WR
        if buy_ratio < 1.0:
            score -= 40

        # [NOUVEAU v2] Heures critiques 13h-15h (< 25% WR)
        if hour in [13, 14, 15]:
            score -= 35
        elif hour in self.BAD_HOURS:
            score -= 20

        # [NOUVEAU v2] decision_tp ENTRER = 47.8% WR
        if decision_tp in self.AVOID_TP_DECISIONS:
            score -= 15

        # Volume trop élevé
        if vol > 150_000:
            score -= 15

        # Token trop vieux
        if age > 24:
            score -= 25

        return score

    def _get_day_of_week(self, alert: Dict) -> str:
        """Extrait le jour de la semaine depuis timestamp."""
        from datetime import datetime
        timestamp = self._safe_get(alert, 'timestamp', '') or self._safe_get(alert, 'created_at', '')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.strptime(timestamp[:19], '%Y-%m-%d %H:%M:%S')
                else:
                    dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%A')
            except:
                pass
        return ''
