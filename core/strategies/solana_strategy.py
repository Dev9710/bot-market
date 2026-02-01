"""
Solana Strategy - Détection Market Cap + Volume + Whale Tracking

STRATEGIE v3.1 - 01/02/2026:
Bot de détection basé sur le MARKET CAP pour memecoins Solana.
Entrée à bas MC + validation whale → Sortie à MC cible pour sécuriser profits.

LOGIQUE D'ENTREE:
1. NIVEAU MC: Entrer à un market cap favorable (pas trop élevé)
   - MC < $500K = Zone early (risqué mais gros potentiel)
   - MC $500K-2M = Zone optimale (bon ratio risk/reward)
   - MC > $5M = Zone tardive (moins de potentiel)

2. TRIGGER: Accélération du volume
   - volume_acceleration_1h_vs_6h > 2.0 = momentum croissant
   - volume_acceleration_6h_vs_24h > 1.5 = tendance confirmée

3. CONFIRMATION: Whale activity (multi-wallet buying)
   - whale_score > 0 = accumulation détectée
   - DISTRIBUTED_BUYING pattern = signal fort

LOGIQUE DE SORTIE (PROFIT):
- Basée sur le multiplicateur de MC depuis l'entrée
- TP1: MC x2 (exit 50% position)
- TP2: MC x3 (exit 30% position)
- TP3: MC x5 (exit 20% restant)
- Trailing stop serré (-5%) pour sécuriser profits

SIGNAL_A++ (Entrée forte):
- MC favorable + Volume accel > 3.0 + whale bullish

SIGNAL_A+ (Entrée modérée):
- MC correct + Volume accel > 2.0

EXCLUSIONS (protection anti-rug):
- MC trop élevé (> $10M = late stage)
- type_pump PARABOLIQUE (dump imminent)
- velocite_pump > 20 (surchauffe)
- Buy ratio < 1.0 (pression vendeuse)
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
    # CONSTANTES MARKET CAP - STRATEGIE v3.1
    # ============================================

    # Zones d'entrée basées sur le Market Cap
    MC_EARLY_MAX = 500_000       # < $500K = Zone early (risqué, gros potentiel)
    MC_OPTIMAL_MIN = 500_000    # $500K-2M = Zone optimale
    MC_OPTIMAL_MAX = 2_000_000
    MC_LATE_MIN = 5_000_000     # > $5M = Zone tardive
    MC_EXCLUDE = 10_000_000     # > $10M = Exclure (late stage, peu de potentiel)

    # Multiplicateurs de sortie (par rapport au MC d'entrée)
    MC_TP1_MULTIPLIER = 2.0     # TP1 = MC x2 (exit 50%)
    MC_TP2_MULTIPLIER = 3.0     # TP2 = MC x3 (exit 30%)
    MC_TP3_MULTIPLIER = 5.0     # TP3 = MC x5 (exit 20%)

    # ============================================
    # CONSTANTES VOLUME & WHALE
    # ============================================

    # Seuils d'accélération volume (trigger principal)
    VOL_ACCEL_STRONG = 3.0      # Accélération forte
    VOL_ACCEL_MODERATE = 2.0    # Accélération modérée
    VOL_ACCEL_MIN = 1.5         # Minimum pour entrée

    # Seuils whale score (confirmation)
    WHALE_SCORE_STRONG = 10     # Forte accumulation
    WHALE_SCORE_POSITIVE = 0    # Accumulation détectée

    # ============================================
    # CONSTANTES AUTRES
    # ============================================

    # Heures défavorables (Railway: < 43% WR)
    BAD_HOURS = [5, 11, 12, 14, 17, 18]

    # Heures optimales (Railway: 57-67% WR)
    GOOD_HOURS = [0, 2, 3, 7, 9, 10, 21]

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
        Stratégie v3.1: Basée sur Market Cap + Volume + Whale.

        Returns:
            (should_exclude, reason)
        """
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        total_txns = self._safe_get(alert, 'total_txns', 0)
        hour = self._get_hour(alert)
        type_pump = self._safe_get(alert, 'type_pump', '')
        velocite = self._safe_get(alert, 'velocite_pump', 0)
        decision_tp = self._safe_get(alert, 'decision_tp_tracking', '')
        tier = self._safe_get(alert, 'tier', '')

        # === MARKET CAP FILTER (v3.1) ===
        market_cap = self._safe_get(alert, 'market_cap_usd', 0)
        fdv = self._safe_get(alert, 'fdv_usd', 0)
        mc = market_cap if market_cap > 0 else fdv  # Utiliser FDV si MC non dispo

        # [v3.1] Exclure si MC trop élevé (late stage, peu de potentiel)
        if mc > self.MC_EXCLUDE:
            return True, f"MC trop eleve: ${mc/1_000_000:.1f}M > ${self.MC_EXCLUDE/1_000_000:.0f}M (late stage)"

        # === AUTRES FILTRES ===

        # decision_tp_tracking dangereux (signal de fin)
        if decision_tp in self.DANGEROUS_TP_DECISIONS:
            return True, f"Decision TP dangereuse: {decision_tp} (WR < 43%)"

        # Tier HIGH performe mal
        if tier in self.DANGEROUS_TIERS:
            return True, f"Tier dangereux: {tier} (WR 33.6%)"

        # Type pump dangereux (dump imminent)
        if type_pump in self.DANGEROUS_PUMP_TYPES:
            return True, f"Type pump dangereux: {type_pump} (WR < 45%)"

        # Velocite trop elevee (surchauffe)
        if velocite and velocite > self.MAX_VELOCITE_PUMP:
            return True, f"Velocite trop elevee: {velocite:.1f} > 20 (WR 45%)"

        # Pression vendeuse
        if buy_ratio < 1.0:
            return True, f"Buy ratio trop faible ({buy_ratio:.2f} < 1.0)"

        # Mauvaises heures
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
        Stratégie v3.1: Market Cap + Volume Accel + Whale Confirmation.

        LOGIQUE:
        1. ZONE MC: Vérifier le niveau de market cap (early/optimal/late)
        2. TRIGGER: Accélération du volume (vol_accel_1h > 2.0)
        3. CONFIRMATION: Whale activity (whale_score > 0)
        4. A++ = MC favorable + Volume accel + Whale

        Returns:
            'A++': MC optimal + Volume accel forte + whale bullish
            'A+' : MC correct + Volume accel modérée
            'A'  : Volume croissant + conditions favorables
            'B'  : Conditions basiques
            None : NO_SIGNAL
        """
        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        liquidity = self._safe_get(alert, 'liquidity', float('inf'))
        velocite = self._safe_get(alert, 'velocite_pump', 0)
        is_first_alert = self._safe_get(alert, 'is_alerte_suivante', 1) == 0

        # === MARKET CAP (v3.1) ===
        market_cap = self._safe_get(alert, 'market_cap_usd', 0)
        fdv = self._safe_get(alert, 'fdv_usd', 0)
        mc = market_cap if market_cap > 0 else fdv

        # Déterminer la zone MC
        mc_early = mc < self.MC_EARLY_MAX if mc > 0 else False
        mc_optimal = self.MC_OPTIMAL_MIN <= mc < self.MC_OPTIMAL_MAX if mc > 0 else False
        mc_late = mc >= self.MC_LATE_MIN if mc > 0 else False
        mc_favorable = mc_early or mc_optimal  # Early ou Optimal = favorable

        # === TRIGGER PRINCIPAL: Accélération du volume ===
        vol_accel_1h = self._safe_get(alert, 'volume_acceleration_1h_vs_6h', 0)
        vol_accel_6h = self._safe_get(alert, 'volume_acceleration_6h_vs_24h', 0)

        # === CONFIRMATION: Whale activity ===
        whale_score = self._safe_get(alert, 'whale_score', 0)
        whale_pattern = self._safe_get(alert, 'whale_pattern', '')

        # Extraction concentration_risk du message
        alert_msg = self._safe_get(alert, 'alert_message', '')
        has_low_concentration = 'concentration : LOW' in alert_msg or 'concentration: LOW' in alert_msg
        is_distributed_buying = whale_pattern == 'DISTRIBUTED_BUYING' or whale_score > self.WHALE_SCORE_POSITIVE
        is_strong_whale = whale_score >= self.WHALE_SCORE_STRONG

        # ============================================
        # SIGNAL_A++ : MC Favorable + Volume Accel Forte + Whale
        # ============================================

        # [v3.1 BEST] MC optimal + Volume accel forte + whale confirmation
        if mc_optimal and vol_accel_1h > self.VOL_ACCEL_STRONG and is_distributed_buying:
            return 'A++'

        # [v3.1] MC early/optimal + Volume accel extreme (> 5x)
        if mc_favorable and vol_accel_1h > 5.0:
            return 'A++'

        # [v3.1] MC favorable + Volume accel forte + whale forte
        if mc_favorable and vol_accel_1h > self.VOL_ACCEL_STRONG and is_strong_whale:
            return 'A++'

        # [v3.1] MC favorable + Double accélération (1h ET 6h)
        if mc_favorable and vol_accel_1h > self.VOL_ACCEL_MODERATE and vol_accel_6h > self.VOL_ACCEL_MODERATE:
            return 'A++'

        # [v3.1] Volume accel extreme même sans MC data
        if vol_accel_1h > 5.0 and is_distributed_buying:
            return 'A++'

        # [BACKUP] Volume accel + concentration LOW
        if vol_accel_1h > 2.5 and has_low_concentration:
            return 'A++'

        # [BACKUP] High liquidity + buy pressure + low concentration
        if (200_000 <= liquidity < 500_000 and buy_ratio > 1.5 and has_low_concentration):
            return 'A++'

        # ============================================
        # SIGNAL_A+ : MC Correct + Volume Accel Modérée
        # ============================================

        # [v3.1] MC favorable + Volume accel modérée
        if mc_favorable and vol_accel_1h > self.VOL_ACCEL_MODERATE:
            return 'A+'

        # [v3.1] Volume accel modérée + whale positive
        if vol_accel_1h > self.VOL_ACCEL_MODERATE and is_distributed_buying:
            return 'A+'

        # [v3.1] Volume accel + whale positive (même sans MC)
        if vol_accel_1h > self.VOL_ACCEL_MIN and whale_score > 0:
            return 'A+'

        # [v3.1] Tendance 6h positive + buy pressure
        if vol_accel_6h > self.VOL_ACCEL_MODERATE and buy_ratio > 1.3:
            return 'A+'

        # Première alerte sur token = signal frais
        if is_first_alert and buy_ratio >= 1.3 and not mc_late:
            return 'A+'

        # ============================================
        # SIGNAL_A : Volume croissant + conditions favorables
        # ============================================
        if vol_accel_1h > 1.2 and buy_ratio >= 1.2:
            return 'A'

        if vol_accel_6h > 1.5 and buy_ratio >= 1.2:
            return 'A'

        # ============================================
        # SIGNAL_B : Conditions basiques
        # ============================================
        if vol < 5_000_000 and buy_ratio >= 1.0 and vol_accel_1h > 1.0:
            return 'B'

        return None

    # ============================================
    # SCORING
    # ============================================

    def calculate_mc_exit_targets(self, entry_mc: float) -> Dict:
        """
        Calcule les niveaux de sortie basés sur le Market Cap.
        Utilisé pour sécuriser les profits sur les memecoins.

        Args:
            entry_mc: Market cap au moment de l'entrée

        Returns:
            Dict avec MC targets pour TP1, TP2, TP3
        """
        return {
            'entry_mc': entry_mc,
            'tp1_mc': entry_mc * self.MC_TP1_MULTIPLIER,   # x2
            'tp1_multiplier': self.MC_TP1_MULTIPLIER,
            'tp1_exit_pct': 50,  # Sortir 50% de la position
            'tp2_mc': entry_mc * self.MC_TP2_MULTIPLIER,   # x3
            'tp2_multiplier': self.MC_TP2_MULTIPLIER,
            'tp2_exit_pct': 30,  # Sortir 30%
            'tp3_mc': entry_mc * self.MC_TP3_MULTIPLIER,   # x5
            'tp3_multiplier': self.MC_TP3_MULTIPLIER,
            'tp3_exit_pct': 20,  # Sortir 20% restant
        }

    def calculate_score(self, alert: Dict, base_score: int) -> int:
        """
        Calcule les bonus/malus de score pour SOLANA.
        Stratégie v3.1: Market Cap + Volume Accel + Whale.

        Args:
            alert: Données de l'alerte
            base_score: Score de base

        Returns:
            Score ajusté
        """
        score = base_score

        vol = self._safe_get(alert, 'volume_24h', float('inf'))
        buy_ratio = self._safe_get(alert, 'buy_ratio', 0)
        hour = self._get_hour(alert)
        velocite = self._safe_get(alert, 'velocite_pump', 0)
        type_pump = self._safe_get(alert, 'type_pump', '')
        is_first_alert = self._safe_get(alert, 'is_alerte_suivante', 1) == 0
        decision_tp = self._safe_get(alert, 'decision_tp_tracking', '')
        total_txns = self._safe_get(alert, 'total_txns', 0)

        # === MARKET CAP (v3.1) ===
        market_cap = self._safe_get(alert, 'market_cap_usd', 0)
        fdv = self._safe_get(alert, 'fdv_usd', 0)
        mc = market_cap if market_cap > 0 else fdv

        # === TRIGGER PRINCIPAL: Accélération volume ===
        vol_acc_1h = self._safe_get(alert, 'volume_acceleration_1h_vs_6h', 1)
        vol_acc_6h = self._safe_get(alert, 'volume_acceleration_6h_vs_24h', 1)

        # === CONFIRMATION: Whale activity ===
        whale_score = self._safe_get(alert, 'whale_score', 0)

        # Extraction concentration_risk du message
        alert_msg = self._safe_get(alert, 'alert_message', '')
        has_low_concentration = 'concentration : LOW' in alert_msg or 'concentration: LOW' in alert_msg

        # === BONUS PRIORITAIRES (Volume Acceleration) ===

        # [v3 CRITIQUE] Volume acceleration 1h - TRIGGER PRINCIPAL
        if vol_acc_1h > 5.0:
            score += 35  # Accélération extrême
        elif vol_acc_1h > 3.0:
            score += 25  # Accélération forte
        elif vol_acc_1h > 2.0:
            score += 15  # Accélération modérée
        elif vol_acc_1h > 1.5:
            score += 8   # Légère accélération

        # [v3 CRITIQUE] Volume acceleration 6h - CONFIRMATION TENDANCE
        if vol_acc_6h > 4.0:
            score += 20  # Tendance très forte
        elif vol_acc_6h > 2.0:
            score += 12  # Tendance confirmée
        elif vol_acc_6h > 1.5:
            score += 5   # Tendance positive

        # [v3] Double accélération = bonus supplémentaire
        if vol_acc_1h > 2.0 and vol_acc_6h > 2.0:
            score += 15  # Momentum confirmé sur 2 timeframes

        # === BONUS CONFIRMATION (Whale Activity) ===

        # [v3] Whale score positif = accumulation distribuée
        if whale_score > 10:
            score += 20  # Forte accumulation whale
        elif whale_score > 0:
            score += 10  # Accumulation modérée

        # [v3] Concentration LOW = moins de risque manipulation
        if has_low_concentration:
            score += 10

        # === BONUS MARKET CAP (v3.1) ===

        if mc > 0:  # Si MC disponible
            # [v3.1] Zone optimale = meilleur ratio risk/reward
            if self.MC_OPTIMAL_MIN <= mc < self.MC_OPTIMAL_MAX:
                score += 20  # $500K-2M = zone idéale
            # [v3.1] Zone early = gros potentiel mais risqué
            elif mc < self.MC_EARLY_MAX:
                score += 15  # < $500K = early stage
            # [v3.1] Zone tardive = moins de potentiel
            elif mc >= self.MC_LATE_MIN:
                score -= 15  # > $5M = late stage

        # === AUTRES BONUS ===

        # Première alerte sur token = signal frais
        if is_first_alert:
            score += 10

        # Buy Ratio élevé = pression acheteuse
        if buy_ratio > 2.0:
            score += 10
        elif buy_ratio > 1.5:
            score += 5

        # Volume optimal (pas trop gros)
        if 100_000 <= vol < 500_000:
            score += 10
        elif vol < 1_000_000:
            score += 5

        # Velocite stable (pas de pump extreme)
        if velocite and -20 < velocite < 20:
            score += 5

        # Type pump NORMAL/LENT
        if type_pump in ['NORMAL', 'LENT']:
            score += 5

        # Heures optimales
        if hour in self.GOOD_HOURS:
            score += 5

        # === MALUS (Protection Anti-Rug) ===

        # [v3 CRITIQUE] Volume en déclin = danger
        if vol_acc_1h < 0.5:
            score -= 30  # Volume s'effondre
        elif vol_acc_1h < 0.8:
            score -= 15  # Volume décline

        # [v3] Volume 6h en déclin
        if 0.2 <= vol_acc_6h < 0.5:
            score -= 20  # Tendance baissière confirmée

        # [v3] Whale score négatif = manipulation/dump
        if whale_score < -15:
            score -= 30  # Whale dump détecté
        elif whale_score < -5:
            score -= 15  # Pression vendeuse whale

        # decision_tp_tracking dangereux (signal de fin)
        if decision_tp in self.DANGEROUS_TP_DECISIONS:
            score -= 25

        # Type pump dangereux (dump imminent)
        if type_pump in self.DANGEROUS_PUMP_TYPES:
            score -= 25

        # Velocite extreme (surchauffe)
        if velocite and velocite > self.MAX_VELOCITE_PUMP:
            score -= 20

        # Buy ratio faible (pression vendeuse)
        if buy_ratio < 1.0:
            score -= 25

        # Heures défavorables
        if hour in self.BAD_HOURS:
            score -= 15

        # Dead zone transactions
        if self.DEAD_ZONE_TXNS_MIN <= total_txns < self.DEAD_ZONE_TXNS_MAX:
            score -= 15

        return score
