"""
Solana Strategy - Stratégie de trading optimisée pour SOLANA

Basé sur l'analyse de 49,092 alertes Railway (30 janvier 2026)
Win Rate: 49.8% -> 80%+ avec nouveaux filtres data-driven v2

SIGNAL_A++ (Zone Optimale ~85-90% WR):
- liq200-500K + ratio>1.5 + conc_LOW (90.9% WR)
- age<6h + vol1-5M + vel<20 + conc_LOW (88.6% WR)
- vol_accel_1h_vs_6h > 5.0 (73.9% WR)
- total_txns < 1K (76.3% WR)

SIGNAL_A+ (~73.8% WR):
- Age < 6h (critère clé)

Exclusions data-driven v2:
- type_pump PARABOLIQUE (40.8% WR)
- type_pump TRES_RAPIDE (44.9% WR)
- velocite_pump > 20 (45.3% WR)
- decision_tp_tracking = SORTIR (39.5% WR)
- decision_tp_tracking = SECURISER_HOLD (42.7% WR)
- tier = HIGH (33.6% WR - inversé!)
- Age 24-48h (danger zone)
- Buy ratio < 1.0
- Heures 05h, 11h-12h, 14h, 17h-18h (< 43% WR)
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
    # CONSTANTES SPÉCIFIQUES SOLANA (Railway data v2 - 30/01/2026)
    # ============================================

    # Heures défavorables (Railway: < 43% WR)
    BAD_HOURS = [5, 11, 12, 14, 17, 18]

    # Heures optimales (Railway: 57-67% WR)
    GOOD_HOURS = [0, 2, 3, 7, 9, 10, 21]

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

    # decision_tp_tracking dangereux (Railway: 39-42% WR)
    DANGEROUS_TP_DECISIONS = ['SORTIR', 'SECURISER_HOLD']

    # Tier inversé - HIGH tier performe mal! (Railway: 33.6% WR)
    DANGEROUS_TIERS = ['HIGH']

    # ============================================
    # FILTRES D'EXCLUSION
    # ============================================

    def should_exclude(self, alert: Dict) -> Tuple[bool, str]:
        """
        Vérifie si une alerte SOLANA doit être exclue.
        Filtres basés sur analyse Railway 30/01/2026 (49,092 alertes).

        Returns:
            (should_exclude, reason)
        """
        age = self._safe_get(alert, 'age_hours', 0)
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        total_txns = self._safe_get(alert, 'total_txns', 0)
        hour = self._get_hour(alert)
        type_pump = self._safe_get(alert, 'type_pump', '')
        velocite = self._safe_get(alert, 'velocite_pump', 0)
        decision_tp = self._safe_get(alert, 'decision_tp_tracking', '')
        tier = self._safe_get(alert, 'tier', '')

        # [NOUVEAU v2] decision_tp_tracking dangereux (Railway: 39-42% WR)
        if decision_tp in self.DANGEROUS_TP_DECISIONS:
            return True, f"Decision TP dangereuse: {decision_tp} (WR < 43%)"

        # [NOUVEAU v2] Tier HIGH performe mal! (Railway: 33.6% WR)
        if tier in self.DANGEROUS_TIERS:
            return True, f"Tier dangereux: {tier} (WR 33.6%)"

        # Type pump dangereux (Railway: 40-45% WR)
        if type_pump in self.DANGEROUS_PUMP_TYPES:
            return True, f"Type pump dangereux: {type_pump} (WR < 45%)"

        # Velocite trop elevee (Railway: 45.3% WR si > 20)
        if velocite and velocite > self.MAX_VELOCITE_PUMP:
            return True, f"Velocite trop elevee: {velocite:.1f} > 20 (WR 45%)"

        # Age 24-48h = danger zone
        if self.DANGER_AGE_MIN <= age < self.DANGER_AGE_MAX:
            return True, "Age 24-48h (danger zone)"

        # Pression vendeuse
        if buy_ratio < 1.0:
            return True, f"Buy ratio trop faible ({buy_ratio:.2f} < 1.0)"

        # Mauvaises heures (Railway: < 43% WR)
        if hour in self.BAD_HOURS:
            return True, f"Heure defavorable ({hour}h UTC - WR < 43%)"

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
        Basé sur analyse Railway 30/01/2026 (10,152 alertes analysables).

        Returns:
            'A++': ~85-90% WR - Zone Optimale
            'A+' : 73.8% WR - Age<6h
            'A'  : 65% WR - Age<12h + conditions favorables
            'B'  : 55% WR - conditions basiques
            None : NO_SIGNAL
        """
        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        age = self._safe_get(alert, 'age_hours', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        liquidity = self._safe_get(alert, 'liquidity', float('inf'))
        vol_accel_1h = self._safe_get(alert, 'volume_acceleration_1h_vs_6h', 0)
        total_txns = self._safe_get(alert, 'total_txns', float('inf'))
        velocite = self._safe_get(alert, 'velocite_pump', 0)
        is_first_alert = self._safe_get(alert, 'is_alerte_suivante', 1) == 0

        # Extraction concentration_risk du message
        alert_msg = self._safe_get(alert, 'alert_message', '')
        has_low_concentration = 'concentration : LOW' in alert_msg or 'concentration: LOW' in alert_msg

        # ============================================
        # SIGNAL_A++ : Zone Optimale (~85-90% WR)
        # ============================================

        # [NOUVEAU v2] liq200-500K + ratio>1.5 + conc_LOW = 90.9% WR
        if (200_000 <= liquidity < 500_000 and buy_ratio > 1.5 and has_low_concentration):
            return 'A++'

        # [NOUVEAU v2] age<6h + vol1-5M + vel<20 + conc_LOW = 88.6% WR
        if (age < 6 and 1_000_000 <= vol < 5_000_000
                and velocite and abs(velocite) < 20 and has_low_concentration):
            return 'A++'

        # [NOUVEAU v2] age<6h + vol1-5M + liq<100K + conc_LOW = 88.2% WR
        if (age < 6 and 1_000_000 <= vol < 5_000_000
                and liquidity < 100_000 and has_low_concentration):
            return 'A++'

        # [NOUVEAU v2] total_txns < 1K = 76.3% WR (tokens très jeunes)
        if total_txns < 1000 and age < 12:
            return 'A++'

        # [NOUVEAU v2] vol_accel_1h_vs_6h > 5.0 = 73.9% WR
        if vol_accel_1h > 5.0 and age < 12:
            return 'A++'

        # Vol<1M + ratio>1.5 + vel<20 = 86.2% WR
        if (vol < 1_000_000 and buy_ratio > 1.5
                and velocite and abs(velocite) < 20):
            return 'A++'

        # Railway data originale: Vol>5M + Liq200-500K + Age<6h = 96.9% WR
        if (age < 6 and vol > 5_000_000 and 200_000 <= liquidity < 500_000):
            return 'A++'

        # Railway data originale: Vol1-5M + Liq<200K + Age<6h = 80-85% WR
        if (age < 6 and 1_000_000 <= vol <= 5_000_000 and liquidity < 200_000):
            return 'A++'

        # ============================================
        # SIGNAL_A+ : Age < 6h (73.8% WR)
        # ============================================
        if age < 6:
            return 'A+'

        # [NOUVEAU v2] Première alerte sur token = 59.1% WR
        if is_first_alert and buy_ratio >= 1.2:
            return 'A+'

        # ============================================
        # SIGNAL_A : Age < 12h + conditions favorables (65% WR)
        # ============================================
        if age < 12 and buy_ratio >= 1.2:
            return 'A'

        # ============================================
        # SIGNAL_B : Conditions basiques (55% WR)
        # ============================================
        if vol < 5_000_000 and buy_ratio >= 1.0:
            return 'B'

        return None

    # ============================================
    # SCORING
    # ============================================

    def calculate_score(self, alert: Dict, base_score: int) -> int:
        """
        Calcule les bonus/malus de score pour SOLANA.
        Basé sur analyse Railway 30/01/2026 (10,152 alertes).

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
        vol_acc_1h = self._safe_get(alert, 'volume_acceleration_1h_vs_6h', 1)
        vol_acc_6h = self._safe_get(alert, 'volume_acceleration_6h_vs_24h', 1)
        total_txns = self._safe_get(alert, 'total_txns', 0)
        volume_1h = self._safe_get(alert, 'volume_1h', 0)
        hour = self._get_hour(alert)
        velocite = self._safe_get(alert, 'velocite_pump', 0)
        type_pump = self._safe_get(alert, 'type_pump', '')
        is_first_alert = self._safe_get(alert, 'is_alerte_suivante', 1) == 0
        decision_tp = self._safe_get(alert, 'decision_tp_tracking', '')

        # Extraction concentration_risk du message
        alert_msg = self._safe_get(alert, 'alert_message', '')
        has_low_concentration = 'concentration : LOW' in alert_msg or 'concentration: LOW' in alert_msg

        # === BONUS (Railway data v2) ===

        # [CRITIQUE] Age < 6h = 73.8% WR (+25% vs moyenne)
        if age < 6:
            score += 25
        elif age < 12:
            score += 10

        # [NOUVEAU v2] total_txns < 1K = 76.3% WR
        if total_txns < 1000:
            score += 20
        elif total_txns < 5000:
            score += 10

        # [NOUVEAU v2] vol_acc_1h_vs_6h > 5.0 = 73.9% WR
        if vol_acc_1h > 5.0:
            score += 15
        elif vol_acc_1h > 2.0:
            score += 5

        # [NOUVEAU v2] vol_acc_6h_vs_24h > 4.0 = 64.3% WR
        if vol_acc_6h > 4.0:
            score += 15
        elif vol_acc_6h > 2.0:
            score += 5

        # [NOUVEAU v2] volume_1h 500K-1M = 62.3% WR
        if 500_000 <= volume_1h < 1_000_000:
            score += 10

        # [NOUVEAU v2] concentration_risk = LOW = 55.9% WR (vs 48.1% MEDIUM)
        if has_low_concentration:
            score += 10

        # [NOUVEAU v2] is_alerte_suivante = 0 (première alerte) = 59.1% WR
        if is_first_alert:
            score += 10

        # [NOUVEAU v2] Heures optimales (Railway: 57-67% WR)
        if hour in self.GOOD_HOURS:
            score += 10

        # Volume optimal (Railway: Vol 100-500K = 77.3% WR)
        if 100_000 <= vol < 500_000:
            score += 15
        elif vol < 1_000_000:
            score += 10

        # Velocite stable (Railway: vel -20 to +20 = 54-56% WR)
        if velocite and -20 < velocite < 20:
            score += 10

        # Buy Ratio élevé
        if buy_ratio > 2.0:
            score += 10
        elif buy_ratio > 1.5:
            score += 8

        # Type pump NORMAL/LENT = meilleur (54% WR)
        if type_pump in ['NORMAL', 'LENT']:
            score += 5

        # === MALUS (Railway data v2) ===

        # [NOUVEAU v2] decision_tp_tracking dangereux (39-42% WR)
        if decision_tp in self.DANGEROUS_TP_DECISIONS:
            score -= 30

        # Type pump dangereux
        if type_pump in self.DANGEROUS_PUMP_TYPES:
            score -= 25

        # Velocite extreme
        if velocite and velocite > self.MAX_VELOCITE_PUMP:
            score -= 20

        # Buy ratio faible
        if buy_ratio < 1.0:
            score -= 30

        # Age danger zone
        if self.DANGER_AGE_MIN <= age < self.DANGER_AGE_MAX:
            score -= 25

        # Heures défavorables (Railway: < 43% WR)
        if hour in self.BAD_HOURS:
            score -= 20

        # Dead zone transactions
        if self.DEAD_ZONE_TXNS_MIN <= total_txns < self.DEAD_ZONE_TXNS_MAX:
            score -= 20

        # [NOUVEAU v2] vol_acc_6h_vs_24h 0.2-0.5 = 40.3% WR (volume en déclin)
        if 0.2 <= vol_acc_6h < 0.5:
            score -= 15

        # [NOUVEAU v2] momentum_bonus > 30 = 43.6% WR (trop de momentum)
        momentum = self._safe_get(alert, 'momentum_bonus', 0)
        if momentum > 30:
            score -= 10

        return score
