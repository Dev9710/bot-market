"""
Signaux et Analyses - Détection de patterns et signaux de trading

Fonctions d'analyse:
- Momentum multi-timeframe (1h, 3h, 6h)
- Résistance/Support
- Corrélation multi-pool
- Whale activity (manipulation vs accumulation distribuée)
- Signaux composites (acceleration, reversal, volume spikes)
"""

from typing import Dict, List, Optional
from collections import defaultdict
from utils.helpers import log


def get_price_momentum_from_api(pool_data: Dict) -> Dict[str, Optional[float]]:
    """
    SIMPLIFIÉ: Utilise directement les données de l'API au lieu de recalculer.
    GeckoTerminal fournit déjà price_change_1h, price_change_3h, price_change_6h !
    """
    return {
        "1h": pool_data.get("price_change_1h"),
        "3h": pool_data.get("price_change_3h"),
        "6h": pool_data.get("price_change_6h"),
    }


def find_resistance_simple(pool_data: Dict) -> Dict:
    """
    SIMPLIFIÉ: Résistance basée sur prix actuel et variation.
    Pour une vraie résistance, il faudrait un historique long-terme.
    """
    # Résistance simple = prix actuel + 10% (estimation conservative)
    current_price = pool_data["price_usd"]

    # Si prix en hausse forte (>20% sur 24h), résistance proche
    if pool_data["price_change_24h"] > 20:
        resistance = current_price * 1.05  # +5% seulement
    else:
        resistance = current_price * 1.10  # +10%

    resistance_dist_pct = ((resistance - current_price) / current_price) * 100

    return {
        "resistance": resistance,
        "support": None,  # Pas calculé pour simplifier
        "resistance_dist_pct": resistance_dist_pct,
    }


def group_pools_by_token(all_pools: List[Dict]) -> Dict[str, List[Dict]]:
    """Regroupe pools par base token."""
    grouped = defaultdict(list)
    for pool in all_pools:
        base_token = pool["base_token_name"]
        grouped[base_token].append(pool)
    return grouped


def analyze_multi_pool(pools: List[Dict]) -> Dict:
    """Analyse activité cross-pool d'un token."""
    if len(pools) <= 1:
        return {"is_multi_pool": False}

    total_volume = sum(p["volume_24h"] for p in pools)
    total_liquidity = sum(p["liquidity"] for p in pools)

    # Identifier pool dominant
    pools_sorted = sorted(pools, key=lambda x: x["volume_24h"], reverse=True)
    dominant_pool = pools_sorted[0]

    # Type de pool dominant (USDT, WETH, etc)
    dominant_pair = dominant_pool["name"].split("/")[1].strip().split()[0] if "/" in dominant_pool["name"] else "Unknown"

    # Vol/Liq par pool
    pool_activities = []
    for p in pools:
        vol_liq = (p["volume_24h"] / p["liquidity"] * 100) if p["liquidity"] > 0 else 0
        pair_name = p["name"].split("/")[1].strip().split()[0] if "/" in p["name"] else "Unknown"
        pool_activities.append({
            "pair": pair_name,
            "vol_liq_pct": vol_liq,
            "volume": p["volume_24h"],
        })

    # Signal bullish si WETH > USDT
    is_bullish = False
    weth_activity = next((p for p in pool_activities if "WETH" in p["pair"] or "ETH" in p["pair"]), None)
    usdt_activity = next((p for p in pool_activities if "USDT" in p["pair"] or "USDC" in p["pair"]), None)

    if weth_activity and usdt_activity:
        if weth_activity["vol_liq_pct"] > usdt_activity["vol_liq_pct"]:
            is_bullish = True

    return {
        "is_multi_pool": True,
        "num_pools": len(pools),
        "total_volume": total_volume,
        "total_liquidity": total_liquidity,
        "dominant_pair": dominant_pair,
        "pool_activities": pool_activities,
        "is_weth_dominant": is_bullish,
    }


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
        signals.append("WHALE MANIPULATION EXTREME detectee (avg: {:.1f}x buys/buyer)".format(avg_buys_per_buyer))
        whale_score -= 20  # GROS MALUS
        pattern = "WHALE_MANIPULATION"
        concentration_risk = "HIGH"

    # WHALE MODÉRÉE: avg > 10 (concentration significative)
    elif avg_buys_per_buyer > 10:
        signals.append("WHALE ACCUMULATION detectee (avg: {:.1f}x buys/buyer)".format(avg_buys_per_buyer))
        whale_score -= 15  # MALUS car whale peut dumper
        pattern = "WHALE_MANIPULATION"
        concentration_risk = "HIGH"

    # WHALE SELL EXTREME: avg > 15 sells/seller
    elif avg_sells_per_seller > 15:
        signals.append("WHALE DUMP EXTREME detecte (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 30  # ÉNORME MALUS
        pattern = "WHALE_SELLING"
        concentration_risk = "HIGH"

    # WHALE SELL MODÉRÉE: avg > 10 sells/seller
    elif avg_sells_per_seller > 10:
        signals.append("WHALE DUMP detecte (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 25  # GROS MALUS car dump imminent
        pattern = "WHALE_SELLING"
        concentration_risk = "HIGH"

    # WHALE SELL FAIBLE: avg > 5 sells/seller (seulement si peu de sellers)
    elif avg_sells_per_seller > 5 and sellers_1h < 50:
        signals.append("WHALE SELLING detectee (avg: {:.1f}x sells/seller)".format(avg_sells_per_seller))
        whale_score -= 15
        pattern = "WHALE_SELLING"
        concentration_risk = "MEDIUM"

    # === DÉTECTION 2: ACCUMULATION DISTRIBUÉE (BULLISH) ===

    # Beaucoup de buyers uniques + ratio favorable
    elif buyers_1h > sellers_1h * 1.5 and buyers_1h > 15:
        signals.append("[OK] ACCUMULATION DISTRIBUEE (achat par many wallets)")
        whale_score += 15  # BONUS car accumulation saine
        pattern = "DISTRIBUTED_BUYING"
        concentration_risk = "LOW"

    # Buyers > sellers mais modéré
    elif buyers_1h > sellers_1h * 1.2 and buyers_1h > 10:
        signals.append("[!] Sentiment BULLISH (plus de buyers que sellers)")
        whale_score += 10
        pattern = "DISTRIBUTED_BUYING"
        concentration_risk = "LOW"

    # === DÉTECTION 3: DISTRIBUTION ÉQUILIBRÉE ===

    elif 0.8 <= unique_wallet_ratio <= 1.2:
        signals.append("[!] Marche equilibre (buyers ~= sellers)")
        whale_score += 0  # Neutre
        pattern = "NORMAL"
        concentration_risk = "MEDIUM"

    # === DÉTECTION 4: SELLING PRESSURE ===

    elif sellers_1h > buyers_1h * 1.3:
        signals.append("[!] SELLING PRESSURE (plus de sellers que buyers)")
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
            signals.append("[!] Concentration whale sur 24h (peu de wallets uniques)")
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


def detect_signals(pool_data: Dict, momentum: Dict, multi_pool_data: Dict) -> List[str]:
    """
    Détecte tous les signaux importants.
    Corrigé pour ALMANAK: ajoute warnings pour dead cat bounce et panic sell.
    """
    # VALIDATION: Vérifier que momentum est un dict valide
    if not momentum or not isinstance(momentum, dict):
        log(f"   [!] momentum invalide dans detect_signals: {type(momentum)}")
        return []  # Pas de signaux si momentum invalide

    signals = []

    price_1h = momentum.get("1h", 0)
    price_6h = pool_data.get("price_change_6h", 0)
    price_24h = pool_data.get("price_change_24h", 0)

    buy_ratio_1h = pool_data["buys_1h"] / pool_data["sells_1h"] if pool_data["sells_1h"] > 0 else 1.0
    buy_ratio_24h = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0

    # === DEAD CAT BOUNCE WARNING (NOUVEAU - Correction ALMANAK) ===
    if price_1h > 0 and price_24h < -20:
        if price_1h < 10:
            signals.append(f"[!] DEAD CAT BOUNCE: Rebond +{price_1h:.1f}% sur tendance baissiere {price_24h:.1f}%")
        else:
            signals.append(f"[!] REVERSAL FRAGILE: Rebond fort (+{price_1h:.1f}%) mais tendance 24h negative ({price_24h:.1f}%)")

    # ACCELERATION (seulement si pas dead cat bounce)
    elif price_1h >= 5:
        signals.append(f"[!] ACCELERATION: +{price_1h:.1f}% en 1h")

    # REVERSAL (uniquement si contexte positif)
    if price_24h < -10 and price_1h > 3 and price_6h > 0:
        # Reversal confirmé si 6h aussi positif
        signals.append(f"[!] REVERSAL CONFIRME: Hausse 1h/6h malgre {price_24h:.1f}% 24h")
    elif price_24h < -10 and price_1h > 5:
        # Reversal possible mais non confirmé
        signals.append(f"[!] REVERSAL: Hausse malgre {price_24h:.1f}% 24h (confirmation necessaire)")

    # === VOLUME SPIKE: QUALIFIÉ (NOUVEAU) ===
    vol_1h_normalized = pool_data["volume_1h"] * 24
    if vol_1h_normalized > pool_data["volume_24h"] * 1.5:
        spike_pct = ((vol_1h_normalized / pool_data["volume_24h"]) - 1) * 100

        # Qualifier le spike
        if price_1h > 3:
            signals.append(f"[!] VOLUME SPIKE BULLISH: +{spike_pct:.0f}% activite + prix hausse")
        elif price_1h < -5:
            signals.append(f"[!] VOLUME SPIKE BEARISH: +{spike_pct:.0f}% activite = panic sell detecte")
        else:
            signals.append(f"[!] VOLUME SPIKE: +{spike_pct:.0f}% activite vs moyenne")

    # === BUY PRESSURE (AMÉLIORÉ) ===
    if buy_ratio_1h > buy_ratio_24h * 1.2 and buy_ratio_1h >= 0.8:
        signals.append(f"[!] BUY PRESSURE: Ratio 1h ({buy_ratio_1h:.2f}) > 24h ({buy_ratio_24h:.2f})")
    elif buy_ratio_1h < buy_ratio_24h * 0.8 and buy_ratio_24h < 0.5:
        # SELL PRESSURE warning (NOUVEAU)
        signals.append(f"[!] SELL PRESSURE: Vendeurs intensifient (1h: {buy_ratio_1h:.2f}, 24h: {buy_ratio_24h:.2f})")

    # MULTI-POOL
    if multi_pool_data.get("is_multi_pool"):
        signals.append(f"[!] MULTI-POOL: {multi_pool_data['num_pools']} pools actifs")
        if multi_pool_data.get("is_weth_dominant"):
            signals.append(f"[!] WETH pool dominant = Smart money")

    # === BOTTOM CONFIRMÉ (AMÉLIORÉ - plus strict) ===
    # Bottom = prix bas + acheteurs reviennent + pression change
    if price_24h < -15 and price_1h > 0 and buy_ratio_1h > buy_ratio_24h * 1.3 and buy_ratio_1h > 0.9:
        signals.append(f"[OK] BOTTOM CONFIRME: Acheteurs reviennent massivement")
    elif price_24h < -10 and price_1h > 3 and price_6h > 0:
        signals.append(f"[OK] Bottom potentiel: Reversal multi-timeframe")

    return signals
