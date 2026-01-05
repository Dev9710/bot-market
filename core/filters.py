"""
Filtres V3 - Système de filtrage des opportunités

Filtres basés sur les enseignements du backtest Phase 2:
- Vélocité pump (min 5-15 selon réseau)
- Type pump (rejeter LENT - 73% des échecs)
- Âge token (zones optimales: 0-3h embryonic ou 48-72h mature)
- Score par réseau (seuils adaptés à la qualité du réseau)
- Liquidité (zones optimales par réseau)
"""

from typing import Dict, Tuple, List

from config.settings import (
    WATCHLIST_TOKENS,
    MIN_VELOCITE_PUMP,
    NETWORK_SCORE_FILTERS,
    OPTIMAL_VELOCITE_PUMP,
    REJECTED_PUMP_TYPES,
    ALLOWED_PUMP_TYPES,
    MIN_TOKEN_AGE_HOURS,
    MAX_TOKEN_AGE_HOURS,
    DANGER_ZONE_AGE_MIN,
    DANGER_ZONE_AGE_MAX,
    OPTIMAL_TOKEN_AGE_MIN_HOURS,
    OPTIMAL_TOKEN_AGE_MAX_HOURS,
    EMBRYONIC_AGE_MAX_HOURS,
    NETWORK_THRESHOLDS,
)


def check_watchlist_token(pool_data: Dict) -> bool:
    """
    Vérifie si le token est dans la watchlist "Money Printer"
    Ces tokens ont montré 77-100% win rate historique

    Returns:
        True si token dans watchlist
    """
    token_name = pool_data.get('token_name', '').lower()
    token_symbol = pool_data.get('token_symbol', '').lower()

    for watch_token in WATCHLIST_TOKENS:
        watch_lower = watch_token.lower()
        if watch_lower in token_name or watch_lower in token_symbol:
            return True

    return False


def filter_by_velocite(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre VÉLOCITÉ - V3.1 avec seuils différenciés par réseau

    Stratégie:
    - ETH/SOLANA: Vélocité min 10 (réseaux performants)
    - BASE: Vélocité min 15 (filtrage agressif, volume élevé)
    - BSC: Vélocité min 12 (modéré)

    Returns:
        (pass_filter, reason)
    """
    velocite = pool_data.get('velocite_pump', 0)
    network = pool_data.get('network', '').lower()

    # Token watchlist: bypass filtre vélocité
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass vélocité"

    # V3.1: Seuil par réseau (si défini), sinon seuil global
    min_velocity = NETWORK_SCORE_FILTERS.get(network, {}).get('min_velocity', MIN_VELOCITE_PUMP)

    # Filtre minimum CRITIQUE
    if velocite < min_velocity:
        return False, f"Vélocité trop faible: {velocite:.1f} < {min_velocity} ({network.upper()})"

    # Bonus si vélocité optimale
    if velocite >= OPTIMAL_VELOCITE_PUMP:
        return True, f"Vélocité EXCELLENTE: {velocite:.1f} (>{OPTIMAL_VELOCITE_PUMP} = pattern gagnant)"

    return True, f"Vélocité OK: {velocite:.1f} (min {network.upper()}: {min_velocity})"


def filter_by_type_pump(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre TYPE PUMP - 73% des losers sont "LENT"

    Returns:
        (pass_filter, reason)
    """
    type_pump = pool_data.get('type_pump', 'UNKNOWN')

    # Token watchlist: bypass filtre type
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass type pump"

    # Rejeter types problématiques
    if type_pump in REJECTED_PUMP_TYPES:
        return False, f"Type pump rejeté: {type_pump} (73% des échecs)"

    # Accepter types performants
    if type_pump in ALLOWED_PUMP_TYPES:
        return True, f"Type pump OK: {type_pump}"

    # Type inconnu: accepter avec warning
    return True, f"Type pump inconnu: {type_pump} (à vérifier)"


def filter_by_age(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre ÂGE TOKEN optimisé
    - Zone optimale: 2-3 jours (36.1% WR, +234% ROI)
    - Zone danger: 12-24h (8.6% WR - PIRE moment)
    - Trop tôt (0-30min): 23.8% WR, -34% drawdown

    Returns:
        (pass_filter, reason)
    """
    age_hours = pool_data.get('age_hours', 0)

    # Token watchlist: bypass filtre âge
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass âge"

    # Trop vieux (7+ jours: 0% WR historique)
    if age_hours > MAX_TOKEN_AGE_HOURS:
        return False, f"Token trop vieux: {age_hours:.1f}h (>7 jours = 0% WR)"

    # Trop jeune (< 3h: risqué, -34% drawdown moyen)
    if age_hours < MIN_TOKEN_AGE_HOURS:
        # Exception: si vélocité exceptionnelle (>50)
        velocite = pool_data.get('velocite_pump', 0)
        if velocite < OPTIMAL_VELOCITE_PUMP:
            return False, f"Token trop jeune: {age_hours:.1f}h (<3h risqué, drawdown -34%)"

    # ZONE DANGER 12-24h (8.6% WR - PIRE timing!)
    if DANGER_ZONE_AGE_MIN <= age_hours <= DANGER_ZONE_AGE_MAX:
        # Rejeter sauf si vélocité exceptionnelle ET score élevé
        velocite = pool_data.get('velocite_pump', 0)
        score = pool_data.get('score', 0)
        if velocite < OPTIMAL_VELOCITE_PUMP or score < 80:
            return False, f"ZONE DANGER âge: {age_hours:.1f}h (12-24h = 8.6% WR!)"

    # ZONE OPTIMALE 2-3 jours (36.1% WR, +234% ROI)
    if OPTIMAL_TOKEN_AGE_MIN_HOURS <= age_hours <= OPTIMAL_TOKEN_AGE_MAX_HOURS:
        return True, f"Âge OPTIMAL: {age_hours:.1f}h (2-3 jours = 36.1% WR!)"

    # V3.1: Zone embryonic 0-3h (Quality Index 182.83 - OPTIMAL!)
    if 0 <= age_hours <= EMBRYONIC_AGE_MAX_HOURS:
        velocite = pool_data.get('velocite_pump', 0)
        if velocite >= 20:  # Embryonic OK si vélocité forte
            return True, f"Âge EMBRYONIC OPTIMAL: {age_hours:.1f}h (QI 182.83!)"
        else:
            return True, f"Âge embryonic: {age_hours:.1f}h (acceptable si vélocité >20)"

    # Autres zones: acceptable
    return True, f"Âge OK: {age_hours:.1f}h"


def filter_by_score_network(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre SCORE par réseau - V3.1 NOUVEAU

    Stratégie différenciée:
    - ETH (77.4% quality): Score min 85 (moins strict, réseau excellent)
    - BASE (59.2% quality): Score min 90 (strict, filtrer volume élevé)
    - BSC (50.2% quality): Score min 88 (modéré)
    - SOLANA (39.2% quality): Score min 85 (moins strict, bon potentiel)

    Returns:
        (pass_filter, reason)
    """
    score = pool_data.get('score', 0)
    network = pool_data.get('network', '').lower()

    # Token watchlist: bypass filtre score
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass score"

    # V3.1: Seuil par réseau (si défini), sinon global 85
    min_score = NETWORK_SCORE_FILTERS.get(network, {}).get('min_score', 85)

    if score < min_score:
        return False, f"Score insuffisant: {score} < {min_score} ({network.upper()})"

    return True, f"Score OK: {score} (min {network.upper()}: {min_score})"


def filter_by_liquidity_range(pool_data: Dict) -> Tuple[bool, str]:
    """
    Filtre LIQUIDITÉ par réseau (zones optimales)
    - Solana: $100K-$200K optimal (43.8% WR)
    - ETH: $100K-$200K optimal (55.6% WR, +6,987% ROI!)
    - BSC: $500K-$5M optimal (36-39% WR)

    Returns:
        (pass_filter, reason)
    """
    network = pool_data.get('network', 'unknown')
    liquidity = pool_data.get('liquidity', 0)

    # Token watchlist: bypass filtre liquidité
    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass liquidité"

    thresholds = NETWORK_THRESHOLDS.get(network, NETWORK_THRESHOLDS.get("default"))

    # Check min
    min_liq = thresholds.get('min_liquidity', 0)
    if liquidity < min_liq:
        return False, f"Liquidité trop faible: ${liquidity:,.0f} < ${min_liq:,.0f}"

    # Check max (si défini)
    max_liq = thresholds.get('max_liquidity')
    if max_liq and liquidity > max_liq:
        return False, f"Liquidité trop élevée: ${liquidity:,.0f} > ${max_liq:,.0f} (tokens gros = déjà découverts)"

    # Zone optimale par réseau
    if network == "solana" and 100000 <= liquidity <= 200000:
        return True, f"Liquidité OPTIMALE Solana: ${liquidity:,.0f} (43.8% WR!)"
    elif network == "eth" and 100000 <= liquidity <= 200000:
        return True, f"Liquidité JACKPOT ETH: ${liquidity:,.0f} (55.6% WR, +6,987% ROI!)"
    elif network == "bsc" and 500000 <= liquidity <= 5000000:
        return True, f"Liquidité OPTIMALE BSC: ${liquidity:,.0f} (36-39% WR)"

    return True, f"Liquidité OK: ${liquidity:,.0f}"


def apply_v3_filters(pool_data: Dict) -> Tuple[bool, List[str]]:
    """
    Applique TOUS les filtres V3 dans l'ordre d'importance
    Retourne (pass_all_filters, reasons_list)

    NOTE IMPORTANTE: Le filtre de score est désactivé car le score est calculé
    APRÈS apply_v3_filters(). Le score sera vérifié plus tard dans is_valid_opportunity().
    """
    reasons = []

    # 1. SCORE PAR RÉSEAU - DÉSACTIVÉ (score pas encore calculé à ce stade!)
    # Le score sera vérifié après calculate_final_score() dans la fonction appelante
    # pass_score, reason_score = filter_by_score_network(pool_data)
    # reasons.append(f"✓ {reason_score}" if pass_score else f"✗ {reason_score}")
    # if not pass_score:
    #     return False, reasons

    # 2. VÉLOCITÉ PAR RÉSEAU (V3.1 - Amélioré avec seuils différenciés)
    pass_vel, reason_vel = filter_by_velocite(pool_data)
    reasons.append(f"✓ {reason_vel}" if pass_vel else f"✗ {reason_vel}")
    if not pass_vel:
        return False, reasons

    # 3. TYPE PUMP (73% des losers sont LENT)
    pass_type, reason_type = filter_by_type_pump(pool_data)
    reasons.append(f"✓ {reason_type}" if pass_type else f"✗ {reason_type}")
    if not pass_type:
        return False, reasons

    # 4. ÂGE TOKEN (V3.1 - Hybride: embryonic 0-3h + mature 48-72h)
    pass_age, reason_age = filter_by_age(pool_data)
    reasons.append(f"✓ {reason_age}" if pass_age else f"✗ {reason_age}")
    if not pass_age:
        return False, reasons

    # 5. LIQUIDITÉ (zones optimales par réseau)
    pass_liq, reason_liq = filter_by_liquidity_range(pool_data)
    reasons.append(f"✓ {reason_liq}" if pass_liq else f"✗ {reason_liq}")
    if not pass_liq:
        return False, reasons

    # Tous les filtres V3.1 passés!
    return True, reasons


def is_valid_opportunity(pool_data: Dict, score: int) -> Tuple[bool, str]:
    """
    Vérifie si pool est une opportunité valide.
    V3: Applique TOUS les filtres backtest avant validation classique.
    """

    # ===== V3: APPLIQUER FILTRES BACKTEST EN PRIORITÉ =====
    passes_v3, v3_reasons = apply_v3_filters(pool_data)

    # Stocker les raisons V3 dans pool_data pour affichage ultérieur
    pool_data['v3_filter_reasons'] = v3_reasons

    # Si échec filtres V3, rejeter immédiatement (sauf watchlist)
    if not passes_v3:
        # Concaténer toutes les raisons d'échec
        failed_reasons = [r for r in v3_reasons if r.startswith('✗')]
        if failed_reasons:
            return False, f"[V3 REJECT] {failed_reasons[0].replace('✗ ', '')}"
        return False, "[V3 REJECT] Filtres backtest non satisfaits"

    # ===== VALIDATION CLASSIQUE (si V3 passé) =====

    # Récupérer seuils par réseau (avec fallback sur default)
    network = pool_data.get("network", "")
    thresholds = NETWORK_THRESHOLDS.get(network, NETWORK_THRESHOLDS["default"])

    min_liq = thresholds["min_liquidity"]
    min_vol = thresholds["min_volume"]
    min_txns = thresholds["min_txns"]

    # Check liquidité min (déjà vérifié par V3 mais double sécurité)
    if pool_data["liquidity"] < min_liq:
        return False, f"❌ Liquidité trop faible: ${pool_data['liquidity']:,.0f}"

    # Check volume min
    if pool_data["volume_24h"] < min_vol:
        return False, f"⚠️ Volume trop faible: ${pool_data['volume_24h']:,.0f}"

    # Check transactions min
    if pool_data["total_txns"] < min_txns:
        return False, f"⚠️ Pas assez de txns: {pool_data['total_txns']}"

    # Check age max (déjà vérifié par V3)
    if pool_data["age_hours"] > MAX_TOKEN_AGE_HOURS:
        return False, f"⏳ Token trop ancien: {pool_data['age_hours']:.0f}h"

    # Check score minimum (ASSOUPLI pour backtesting: 55 → 50)
    if score < 50:
        return False, f"📉 Score trop faible: {score}/100"

    # Check ratio volume/liquidité
    from config.settings import VOLUME_LIQUIDITY_RATIO
    ratio = pool_data["volume_24h"] / pool_data["liquidity"] if pool_data["liquidity"] > 0 else 0
    if ratio < VOLUME_LIQUIDITY_RATIO:
        return False, f"📉 Ratio Vol/Liq trop faible: {ratio:.1%}"

    # Check pump & dump potentiel
    buy_sell_ratio = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 999
    if buy_sell_ratio > 5:
        return False, f"🚨 Trop d'achats vs ventes (pump?): {buy_sell_ratio:.1f}"
    if buy_sell_ratio < 0.2:
        return False, f"📉 Trop de ventes vs achats (dump?): {buy_sell_ratio:.1f}"

    return True, "✅ Opportunité valide [V3 APPROVED]"
