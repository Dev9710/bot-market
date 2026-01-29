"""
Système de Scoring V3 - Calcul de scores et tiers de confiance

Fonctions de scoring basées sur backtest Phase 2:
- Score de base (fondamentaux + bonus réseau)
- Bonus momentum (accélération, patterns)
- Score final (base + momentum + whale)
- Tiers de confiance (HIGH/MEDIUM/LOW)
- Confidence score (fiabilité des données)

V4 (Janvier 2026): Intégration stratégie SIGNAL optimisée ETH/SOLANA
- Signal quality (A+, A, B, None)
- Filtres d'exclusion basés sur backtest 15,922 alertes
- SL/TP optimisés par réseau
"""

from typing import Dict, Tuple, List, Optional
from utils.helpers import log
from config.settings import (
    MIN_VELOCITE_PUMP,
    OPTIMAL_VELOCITE_PUMP,
    EXPLOSIVE_VELOCITE_PUMP,
    ALLOWED_PUMP_TYPES,
    OPTIMAL_TOKEN_AGE_MIN_HOURS,
    OPTIMAL_TOKEN_AGE_MAX_HOURS,
    EMBRYONIC_AGE_MAX_HOURS,
)
from core.filters import check_watchlist_token
from core.signals import analyze_whale_activity

# Import de la nouvelle stratégie SIGNAL (architecture modulaire)
try:
    from core.strategies import (
        get_strategy,
        is_strategy_available,
        get_supported_networks,
        analyze_alert as analyze_signal_alert,
        get_sltp_config,
        calculate_sltp_prices,
        get_position_size_percent,
    )
    from core.signal_strategy import (
        get_signal_quality,
        should_exclude,
        calculate_signal_score,
        analyze_signal,
    )
    SIGNAL_STRATEGY_AVAILABLE = True
except ImportError:
    SIGNAL_STRATEGY_AVAILABLE = False
    log("signal_strategy.py non disponible - utilisation scoring V3 classique")


def calculate_base_score(pool_data: Dict) -> int:
    """
    Score de base DYNAMIQUE V3 (fondamentaux) avec pénalités ET bonus backtest.
    Corrigé pour ALMANAK: score ne doit plus monter pendant une chute.
    V3: Ajout bonus réseau, zones optimales liquidité, âge optimal.
    """
    score = 0

    # === BONUS RÉSEAU V3 (max 35 points - nouveau!) ===
    network = pool_data.get("network", "")
    liq = pool_data.get("liquidity", 0)

    # DEBUG: Log si liquidité manquante
    if liq == 0:
        log(f"   [DEBUG] Pool {pool_data.get('name', 'UNK')}: liq=0, vol={pool_data.get('volume_24h', 0)}, age={pool_data.get('age_hours', 0)}")
        return 0  # Score 0 si pas de liquidité

    # ETH et Solana = champions (38.9% WR)
    if network == "eth":
        score += 35
        # BONUS ZONE JACKPOT ETH $100K-$200K (55.6% WR, +6,987% ROI!)
        if 100000 <= liq <= 200000:
            score += 15  # JACKPOT!
    elif network == "solana":
        score += 32
        # BONUS ZONE OPTIMALE Solana $100K-$200K (43.8% WR)
        if 100000 <= liq <= 200000:
            score += 12
    elif network == "bsc":
        score += 25  # 23.4% WR
        # BONUS ZONE OPTIMALE BSC $500K-$5M (36-39% WR)
        if 500000 <= liq <= 5000000:
            score += 10
    elif network == "base":
        score += 15  # 12.8% WR (faible)
    elif network == "polygon_pos":
        score += 20  # V3.2: Nouveau réseau, score modéré (à ajuster)
        # Zone optimale Polygon: frais bas = plus d'activité
        if 50000 <= liq <= 300000:
            score += 10
    elif network == "avax":
        score += 28  # V3.2: Écosystème mature, similar à BSC
        # Zone optimale Avalanche
        if 100000 <= liq <= 500000:
            score += 12
    elif network == "arbitrum":
        score += 5   # 4.9% WR (catastrophique)
    else:
        score += 10  # Réseau inconnu (prudence)

    # Liquidité (max 25 points - réduit car réseau/zones déjà comptés)
    if liq >= 1000000:
        score += 15  # Réduit (gros tokens déjà découverts)
    elif liq >= 500000:
        score += 20
    elif liq >= 200000:
        score += 25  # SWEET SPOT général
    elif liq >= 100000:
        score += 25  # SWEET SPOT général
    elif liq >= 50000:
        score += 15

    # Volume (max 20 points)
    vol = pool_data["volume_24h"]
    if vol >= 1000000:
        score += 20
    elif vol >= 500000:
        score += 15
    elif vol >= 200000:
        score += 10
    elif vol >= 100000:
        score += 5

    # === ÂGE V3 OPTIMISÉ (max 25 points - augmenté!) ===
    age = pool_data["age_hours"]
    if 48 <= age <= 72:  # 2-3 JOURS = OPTIMAL (36.1% WR!)
        score += 25  # MAXIMUM
    elif 24 <= age < 48 or 72 < age <= 96:  # Autour de l'optimal
        score += 20
    elif 6 <= age < 24:  # Acceptable
        score += 15
    elif age < 6:
        score += 8   # Très récent (risqué, -34% drawdown)
    elif 96 < age <= 168:
        score += 10  # Une semaine (OK)
    # PÉNALITÉ ZONE DANGER 12-24h (8.6% WR!)
    if 12 <= age <= 24:
        score -= 15  # PIRE timing!

    # Vol/Liq ratio (max 15 points)
    vol_liq = (vol / liq) if liq > 0 else 0
    if 0.5 <= vol_liq <= 1.5:
        score += 15  # Sweet spot
    elif 0.3 <= vol_liq < 0.5 or 1.5 < vol_liq <= 2.0:
        score += 10
    elif vol_liq > 2.0:
        # CORRECTION: Si volume très élevé (>2M), un ratio élevé est POSITIF (viralité)
        if vol > 2000000:
            score += 12  # Volume exceptionnel = bon signe malgré ratio élevé
        else:
            score += 5  # Trop actif (pump?)

    # Buy/Sell balance (max 15 points)
    buy_ratio = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0
    if 0.6 <= buy_ratio <= 1.4:
        score += 15  # Équilibré
    elif 0.4 <= buy_ratio < 0.6 or 1.4 < buy_ratio <= 2.0:
        score += 10
    elif buy_ratio < 0.4 or buy_ratio > 2.0:
        score += 5  # Déséquilibré

    # === NOUVELLES PÉNALITÉS DYNAMIQUES (Correction ALMANAK) ===

    # PÉNALITÉ 1: Tendance baissière 24h (CRITIQUE)
    price_change_24h = pool_data.get("price_change_24h", 0)
    if price_change_24h < -40:
        score -= 35  # Crash massif (-45% comme ALMANAK)
    elif price_change_24h < -30:
        score -= 25  # Chute sévère
    elif price_change_24h < -20:
        score -= 15  # Chute importante
    elif price_change_24h < -10:
        score -= 8   # Baisse modérée

    # PÉNALITÉ 2: Pression vendeuse massive 24h (CRITIQUE)
    total_txns_24h = pool_data["buys_24h"] + pool_data["sells_24h"]
    if total_txns_24h > 0:
        sell_pressure_24h = pool_data["sells_24h"] / total_txns_24h
        if sell_pressure_24h > 0.70:  # >70% ventes (cas ALMANAK: 63-68%)
            score -= 25
        elif sell_pressure_24h > 0.65:  # >65% ventes
            score -= 20
        elif sell_pressure_24h > 0.60:  # >60% ventes
            score -= 12

    # PÉNALITÉ 3: Liquidité en chute (risque rug pull)
    # Note: Nécessiterait historique liquidité, simulé via Vol/Liq ratio anormal
    if vol_liq > 3.0:  # Activité excessive = possiblement liquidité qui fond
        score -= 10

    return max(score, 0)  # Ne jamais descendre sous 0

def calculate_momentum_bonus(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> int:
    """
    Bonus momentum INTELLIGENT V3 (dynamique actuelle).
    Corrigé pour ALMANAK: distingue bon spike (accumulation) vs mauvais spike (panic sell).
    V3: Ajout bonus vélocité (facteur #1 de succès: +133% impact).
    """
    # VALIDATION: Vérifier que momentum est un dict valide
    if not momentum or not isinstance(momentum, dict):
        log(f"   ⚠️ momentum invalide dans calculate_momentum_bonus: {type(momentum)}")
        return 0  # Pas de bonus si momentum invalide

    bonus = 0

    # === VÉLOCITÉ V3 (max 20 points - NOUVEAU! Facteur #1) ===
    velocite = pool_data.get('velocite_pump', 0)
    if velocite >= 100:  # PARABOLIQUE
        bonus += 20  # MAXIMUM
    elif velocite >= 50:  # TRES_RAPIDE (pattern gagnant!)
        bonus += 18
    elif velocite >= 20:  # RAPIDE
        bonus += 15
    elif velocite >= 10:
        bonus += 10
    elif velocite >= 5:
        bonus += 5
    # < 5 = déjà filtré en amont, mais si passe quand même:
    elif velocite < 5:
        bonus -= 5  # PÉNALITÉ

    # === Prix 1h (max 15 points - réduit car vélocité déjà compté) ===
    price_1h = momentum.get("1h", 0)
    price_6h = pool_data.get("price_change_6h", 0)
    price_24h = pool_data.get("price_change_24h", 0)

    if price_1h >= 10:
        bonus += 10  # Réduit de 15 à 10
    elif price_1h >= 5:
        bonus += 7   # Réduit de 10 à 7
    elif price_1h >= 2:
        bonus += 3   # Réduit de 5 à 3

    # === DÉTECTION DEAD CAT BOUNCE (Correction ALMANAK) ===
    # Rebond 1h positif MAIS tendance 24h très négative = piège
    if price_1h > 0 and price_24h < -20:
        # Dead cat bounce détecté
        if price_1h < 10:  # Petit rebond sur grosse chute
            bonus -= 10  # PÉNALITÉ au lieu de bonus!
        # Si rebond >10%, on garde le bonus mais on avertira dans les signaux

    # === Volume Spike: BON ou MAUVAIS? ===
    txn_1h = pool_data["buys_1h"] + pool_data["sells_1h"]
    txn_24h = pool_data["total_txns"]

    if txn_24h > 0:
        txn_1h_normalized = txn_1h * 24  # Normaliser sur 24h
        has_volume_spike = txn_1h_normalized > txn_24h * 1.5  # +50% activité

        if has_volume_spike:
            # Spike + Prix hausse = BON (accumulation)
            if price_1h > 3:
                bonus += 10
            # Spike + Prix stable/léger hausse = NEUTRE
            elif price_1h > 0:
                bonus += 5
            # Spike + Prix chute = MAUVAIS (panic sell)
            elif price_1h < -5:
                bonus -= 10  # PÉNALITÉ pour panic sell
            # Spike + Prix léger baisse = vigilance
            else:
                bonus += 0  # Pas de bonus ni pénalité
        elif txn_1h_normalized > txn_24h * 1.2:
            # Activité modérée
            if price_1h > 0:
                bonus += 5

    # === Buy Pressure 1h (max 10 points) ===
    buy_ratio_1h = pool_data["buys_1h"] / pool_data["sells_1h"] if pool_data["sells_1h"] > 0 else 1.0
    buy_ratio_24h = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0

    # Buy ratio 1h DOIT être comparé au ratio 24h
    if buy_ratio_1h >= 1.2:  # Forte dominance acheteurs
        bonus += 10
    elif buy_ratio_1h >= 1.0:  # Léger avantage acheteurs
        bonus += 8
    elif buy_ratio_1h >= 0.8:  # Équilibre
        bonus += 5
    elif buy_ratio_1h < 0.5 and buy_ratio_24h < 0.5:
        # Vendeurs dominent 1h ET 24h = très mauvais
        bonus -= 5

    # === Multi-pool (max 10 points) ===
    if multi_pool_data.get("is_multi_pool"):
        bonus += 5
        if multi_pool_data.get("is_weth_dominant"):
            bonus += 5

    # === CORRECTION CONTEXTE GLOBAL ===
    # Si price_24h très négatif, limiter le momentum bonus max
    if price_24h < -30:
        bonus = min(bonus, 10)  # Max 10 points si token en crash
    elif price_24h < -20:
        bonus = min(bonus, 15)  # Max 15 points si token en chute

    return max(min(bonus, 30), -20)  # Max +30, Min -20

# ============================================
# WHALE ACTIVITY ANALYSIS (NOUVEAU)
# ============================================
def analyze_whale_activity(pool_data: Dict) -> Dict:
    """
    Analyse l'activité des whales via unique buyers/sellers.

    Détecte:
    - Whale manipulation (peu de wallets, beaucoup de txns)
    - Accumulation distribuée (beaucoup de wallets)
    - Sentiment du marché (buyers vs sellers)

    Returns:
        {
            'pattern': str,              # WHALE_MANIPULATION / DISTRIBUTED_BUYING / WHALE_SELLING / NORMAL
            'whale_score': int,          # -20 à +20 (bonus/malus au score)
            'avg_buys_per_buyer': float,
            'avg_sells_per_seller': float,
            'unique_wallet_ratio': float, # buyers / sellers
            'concentration_risk': str,    # LOW / MEDIUM / HIGH
            'signals': list               # Liste des signaux détectés
        }
    """
    signals = []
    whale_score = 0

    # Récupérer les données 1h (plus récent = plus important)
    # HOTFIX: Gérer None explicite de l'API (or 0 = fallback)
    buys_1h = pool_data.get('buys_1h') or 0
    sells_1h = pool_data.get('sells_1h') or 0
    buyers_1h = pool_data.get('buyers_1h') or 0
    sellers_1h = pool_data.get('sellers_1h') or 0

    # Récupérer 24h pour contexte
    buys_24h = pool_data.get('buys_24h') or 0
    buyers_24h = pool_data.get('buyers_24h') or 0
    sellers_24h = pool_data.get('sellers_24h') or 0

    # Calculer moyennes de transactions par wallet unique
    avg_buys_per_buyer = buys_1h / buyers_1h if buyers_1h > 0 else 0
    avg_sells_per_seller = sells_1h / sellers_1h if sellers_1h > 0 else 0

    # Ratio unique wallets
    unique_wallet_ratio = buyers_1h / sellers_1h if sellers_1h > 0 else 1.0

    # === DÉTECTION 1: WHALE MANIPULATION (Achat/Vente) ===

    # FIX BUG #2: Seuils plus réalistes pour détecter whale manipulation
    # avg_buys_per_buyer élevé = concentration whale (même avec beaucoup de buyers)

    # WHALE EXTREME: avg > 15 (whale très concentrée)
    if avg_buys_per_buyer > 15:
        signals.append("🐋🐋 WHALE MANIPULATION EXTRÊME détectée (avg: {:.1f}x buys/buyer)".format(avg_buys_per_buyer))
        whale_score -= 20  # GROS MALUS
        pattern = "WHALE_MANIPULATION"
        concentration_risk = "HIGH"

    # WHALE MODÉRÉE: avg > 10 (concentration significative)
    elif avg_buys_per_buyer > 10:
        signals.append("🐋 WHALE ACCUMULATION détectée (avg: {:.1f}x buys/buyer)".format(avg_buys_per_buyer))
        whale_score -= 15  # MALUS car whale peut dumper
        pattern = "WHALE_MANIPULATION"
        concentration_risk = "HIGH"

    # WHALE SELL EXTREME: avg > 15 sells/seller
    elif avg_sells_per_seller > 15:
        signals.append("🚨🚨 WHALE DUMP EXTRÊME détecté (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 30  # ÉNORME MALUS
        pattern = "WHALE_SELLING"
        concentration_risk = "HIGH"

    # WHALE SELL MODÉRÉE: avg > 10 sells/seller
    elif avg_sells_per_seller > 10:
        signals.append("🚨 WHALE DUMP détecté (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 25  # GROS MALUS car dump imminent
        pattern = "WHALE_SELLING"
        concentration_risk = "HIGH"

    # WHALE SELL FAIBLE: avg > 5 sells/seller (seulement si peu de sellers)
    elif avg_sells_per_seller > 5 and sellers_1h < 50:
        signals.append("⚠️ WHALE SELLING détectée (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 15
        pattern = "WHALE_SELLING"
        concentration_risk = "MEDIUM"

    # === DÉTECTION 2: ACCUMULATION DISTRIBUÉE (BULLISH) ===

    # Beaucoup de buyers uniques + ratio favorable
    elif buyers_1h > sellers_1h * 1.5 and buyers_1h > 15:
        signals.append("✅ ACCUMULATION DISTRIBUÉE (achat par many wallets)")
        whale_score += 15  # BONUS car accumulation saine
        pattern = "DISTRIBUTED_BUYING"
        concentration_risk = "LOW"

    # Buyers > sellers mais modéré
    elif buyers_1h > sellers_1h * 1.2 and buyers_1h > 10:
        signals.append("📈 Sentiment BULLISH (plus de buyers que sellers)")
        whale_score += 10
        pattern = "DISTRIBUTED_BUYING"
        concentration_risk = "LOW"

    # === DÉTECTION 3: DISTRIBUTION ÉQUILIBRÉE ===

    elif 0.8 <= unique_wallet_ratio <= 1.2:
        signals.append("⚖️ Marché équilibré (buyers ≈ sellers)")
        whale_score += 0  # Neutre
        pattern = "NORMAL"
        concentration_risk = "MEDIUM"

    # === DÉTECTION 4: SELLING PRESSURE ===

    elif sellers_1h > buyers_1h * 1.3:
        signals.append("⚠️ SELLING PRESSURE (plus de sellers que buyers)")
        whale_score -= 10  # MALUS
        pattern = "DISTRIBUTED_SELLING"
        concentration_risk = "MEDIUM"

    else:
        pattern = "NORMAL"
        concentration_risk = "MEDIUM"

    # === VÉRIFICATION SUPPLÉMENTAIRE: Activité 24h ===

    # Si buyers_24h faible malgré volume élevé → concentration whale
    if buyers_24h > 0:
        avg_buys_per_buyer_24h = buys_24h / buyers_24h
        if avg_buys_per_buyer_24h > 8:
            signals.append("⚠️ Concentration whale sur 24h (peu de wallets uniques)")
            whale_score -= 8
            concentration_risk = "HIGH"

    return {
        'pattern': pattern,
        'whale_score': whale_score,
        'avg_buys_per_buyer': round(avg_buys_per_buyer, 2),
        'avg_sells_per_seller': round(avg_sells_per_seller, 2),
        'unique_wallet_ratio': round(unique_wallet_ratio, 2),
        'concentration_risk': concentration_risk,
        'signals': signals,
        'buyers_1h': buyers_1h,
        'sellers_1h': sellers_1h
    }

# ============================================
# V3: SCORING ET TIERS DE CONFIANCE
# ============================================

def calculate_confidence_tier(pool_data: Dict) -> str:
    """
    Calcule le tier de confiance basé sur la stratégie SIGNAL V4.

    Pour ETH/SOLANA: utilise la nomenclature SIGNAL
    - SIGNAL_A+ : 88% WR (Solana) / 59% WR (ETH)
    - SIGNAL_A  : 78% WR (Solana) / 56% WR (ETH)
    - SIGNAL_B  : 62% WR (Solana) / 47% WR (ETH)

    Pour autres réseaux: utilise l'ancienne logique V3
    - HIGH = 35-50% WR attendu
    - MEDIUM = 25-30% WR attendu
    - LOW = 15-20% WR attendu
    """
    network = pool_data.get('network', '').lower()

    # Token watchlist = AUTO ULTRA_HIGH
    if check_watchlist_token(pool_data):
        return "ULTRA_HIGH"  # 77-100% WR historique!

    # === V4: STRATÉGIE SIGNAL POUR ETH/SOLANA ===
    if SIGNAL_STRATEGY_AVAILABLE and network in ['eth', 'solana']:
        try:
            signal_quality = get_signal_quality(pool_data, network)

            if signal_quality == 'A+':
                return "SIGNAL_A+"  # 88% WR (Solana) / 59% WR (ETH)
            elif signal_quality == 'A':
                return "SIGNAL_A"   # 78% WR (Solana) / 56% WR (ETH)
            elif signal_quality == 'B':
                return "SIGNAL_B"   # 62% WR (Solana) / 47% WR (ETH)
            else:
                # Vérifié mais exclu ou pas de signal
                excluded, reason = should_exclude(pool_data, network)
                if excluded:
                    return "EXCLUDED"
                return "NO_SIGNAL"
        except Exception as e:
            log(f"⚠️ Erreur calcul tier SIGNAL: {e}")
            # Fallback vers logique V3

    # === V3: LOGIQUE CLASSIQUE POUR AUTRES RÉSEAUX ===
    score = pool_data.get('score', 0)
    velocite = pool_data.get('velocite_pump', 0)
    type_pump = pool_data.get('type_pump', '')
    age_hours = pool_data.get('age_hours', 0)
    liquidity = pool_data.get('liquidity', 0)

    # HIGH CONFIDENCE (attendu: 35-50% WR)
    high_conditions = [
        network in ['eth', 'solana'],
        48 <= age_hours <= 72,  # 2-3 jours
        velocite >= OPTIMAL_VELOCITE_PUMP,  # >50
        type_pump in ['PARABOLIQUE', 'TRES_RAPIDE'],
        100000 <= liquidity <= 300000
    ]

    if sum(high_conditions) >= 4:  # 4 sur 5 critères
        return "HIGH"

    # MEDIUM CONFIDENCE (attendu: 25-30% WR)
    medium_conditions = [
        network in ['eth', 'solana', 'bsc'],
        age_hours >= 6,
        velocite >= 10,
        type_pump in ALLOWED_PUMP_TYPES,
        liquidity >= 50000,
        score >= 60
    ]

    if sum(medium_conditions) >= 4:
        return "MEDIUM"

    # LOW CONFIDENCE (attendu: 15-20% WR)
    if velocite >= MIN_VELOCITE_PUMP and type_pump in ALLOWED_PUMP_TYPES:
        return "LOW"

    # Très faible confiance
    return "VERY_LOW"

def calculate_final_score(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> Tuple[int, int, int, Dict]:
    """
    Score final = base + momentum + whale_score.

    Returns:
        (final_score, base_score, momentum_bonus, whale_analysis)
    """
    base = calculate_base_score(pool_data)
    momentum_bonus = calculate_momentum_bonus(pool_data, momentum, multi_pool_data)

    # NOUVEAU: Analyse whale activity
    whale_analysis = analyze_whale_activity(pool_data)
    whale_score = whale_analysis['whale_score']

    # Score final avec whale bonus/malus
    final = base + momentum_bonus + whale_score
    final = max(min(final, 100), 0)  # Entre 0 et 100

    return final, base, momentum_bonus, whale_analysis

def calculate_confidence_score(pool_data: Dict) -> int:
    """
    Calcule niveau de confiance dans les données (0-100%).
    Corrigé pour ALMANAK: ajout indicateur fiabilité.
    """
    confidence = 100

    # Réduire confiance si données incomplètes
    if pool_data.get("network", "").lower() == "unknown":
        confidence -= 20  # Données réseau manquantes

    # Réduire confiance si liquidité faible = données moins stables
    liq = pool_data.get("liquidity", 0)
    if liq < 200000:
        confidence -= 20  # Liquidité trop faible
    elif liq < 300000:
        confidence -= 10  # Liquidité moyenne-faible

    # Réduire confiance si trop récent = historique limité
    age = pool_data.get("age_hours", 999)
    if age < 6:
        confidence -= 20  # Moins de 6h = très peu d'historique
    elif age < 12:
        confidence -= 10  # Moins de 12h = historique limité

    # Réduire confiance si volume très faible
    vol = pool_data.get("volume_24h", 0)
    if vol < 100000:
        confidence -= 15  # Volume faible = données peu significatives

    # Réduire confiance si transactions trop peu nombreuses
    txns = pool_data.get("total_txns", 0)
    if txns < 200:
        confidence -= 10  # Peu de transactions = données peu représentatives

    return max(confidence, 0)


# ============================================
# V4: INTÉGRATION STRATÉGIE SIGNAL (ETH/SOLANA)
# ============================================

def get_signal_analysis(pool_data: Dict) -> Optional[Dict]:
    """
    Analyse complète avec la stratégie SIGNAL V4 (ETH/SOLANA uniquement).

    Args:
        pool_data: Données du pool

    Returns:
        Dict avec signal_quality, is_excluded, adjusted_score, etc.
        ou None si stratégie non disponible ou réseau non supporté
    """
    if not SIGNAL_STRATEGY_AVAILABLE:
        return None

    network = pool_data.get('network', '').lower()

    # Stratégie SIGNAL uniquement pour ETH et SOLANA
    if network not in ['eth', 'solana']:
        return None

    try:
        return analyze_signal(pool_data)
    except Exception as e:
        log(f"⚠️ Erreur analyse signal: {e}")
        return None


def calculate_final_score_v4(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> Tuple[int, int, int, Dict, Optional[Dict]]:
    """
    Score final V4 = base + momentum + whale + ajustements SIGNAL.

    Returns:
        (final_score, base_score, momentum_bonus, whale_analysis, signal_analysis)
    """
    # Calcul V3 classique
    base = calculate_base_score(pool_data)
    momentum_bonus = calculate_momentum_bonus(pool_data, momentum, multi_pool_data)
    whale_analysis = analyze_whale_activity(pool_data)
    whale_score = whale_analysis['whale_score']

    # Score V3
    final_v3 = base + momentum_bonus + whale_score
    final_v3 = max(min(final_v3, 100), 0)

    # Analyse SIGNAL V4 (ETH/SOLANA uniquement)
    signal_analysis = get_signal_analysis(pool_data)

    if signal_analysis and SIGNAL_STRATEGY_AVAILABLE:
        # Utiliser le score ajusté de la stratégie SIGNAL
        final = signal_analysis['adjusted_score']

        # Ajouter whale_score au score SIGNAL
        final = final + whale_score
        final = max(min(final, 100), 0)

        # Log de la différence
        network = pool_data.get('network', '').upper()
        signal_quality = signal_analysis.get('signal_quality')
        if signal_quality:
            log(f"   📊 SIGNAL_{signal_quality} ({network}): Score V3={final_v3} → V4={final}")
    else:
        final = final_v3

    return final, base, momentum_bonus, whale_analysis, signal_analysis


def should_skip_alert(pool_data: Dict) -> Tuple[bool, str]:
    """
    Vérifie si une alerte doit être ignorée selon la stratégie SIGNAL.

    Args:
        pool_data: Données du pool

    Returns:
        (should_skip, reason)
    """
    if not SIGNAL_STRATEGY_AVAILABLE:
        return False, ""

    network = pool_data.get('network', '').lower()

    # Stratégie SIGNAL uniquement pour ETH et SOLANA
    if network not in ['eth', 'solana']:
        return False, ""

    return should_exclude(pool_data, network)


def get_optimized_sltp(pool_data: Dict) -> Optional[Dict]:
    """
    Retourne les SL/TP optimisés selon le réseau.

    Args:
        pool_data: Données du pool

    Returns:
        Dict avec stop_loss_price, tp1_price, etc. ou None
    """
    if not SIGNAL_STRATEGY_AVAILABLE:
        return None

    network = pool_data.get('network', '').lower()

    # SL/TP optimisés uniquement pour ETH et SOLANA
    if network not in ['eth', 'solana']:
        return None

    entry_price = pool_data.get('price_usd', 0)
    if not entry_price:
        return None

    return calculate_sltp_prices(entry_price, network)
