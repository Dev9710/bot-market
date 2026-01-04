"""
Module de gestion du cache - Historiques et cooldowns

Gère les données en mémoire qui ne sont pas fournies par l'API:
- Historique buy ratio pour détecter les changements de pression
- Cooldowns pour éviter spam d'alertes
"""

import time
from typing import Dict, Optional
from collections import defaultdict


# ============================================
# CACHE GLOBAL - Buy Ratio History
# ============================================
# Historique des buy ratios par pool (pas fourni par API)
# Structure: buy_ratio_history[base_token][pool_addr] = [(timestamp, ratio), ...]
buy_ratio_history = defaultdict(lambda: defaultdict(list))


def update_buy_ratio_history(pool_data: Dict):
    """
    Met à jour seulement l'historique buy ratio (pas fourni par API).

    Args:
        pool_data: Données du pool avec buys_24h, sells_24h, base_token_name, pool_address
    """
    base_token = pool_data["base_token_name"]
    pool_addr = pool_data["pool_address"]
    now = time.time()

    # Buy ratio 24h
    buy_ratio = pool_data["buys_24h"] / pool_data["sells_24h"] if pool_data["sells_24h"] > 0 else 1.0
    buy_ratio_history[base_token][pool_addr].append((now, buy_ratio))

    # Nettoyer historique (garder 2h seulement - on a besoin que de 1h)
    cutoff = now - 7200  # 2h
    buy_ratio_history[base_token][pool_addr] = [
        (t, v) for t, v in buy_ratio_history[base_token][pool_addr] if t > cutoff
    ]


def get_buy_ratio_change(base_token: str, pool_addr: str) -> Optional[float]:
    """
    Calcule variation buy ratio sur 1h.

    Args:
        base_token: Nom du token de base
        pool_addr: Adresse du pool

    Returns:
        Variation en pourcentage, ou None si pas assez de données
    """
    hist = buy_ratio_history[base_token][pool_addr]

    if not hist or len(hist) < 2:
        return None

    now = time.time()
    one_hour_ago = now - 3600  # 1h

    # Trouver valeur la plus proche d'il y a 1h
    past_values = [v for t, v in hist if t < one_hour_ago]
    if not past_values:
        return None

    past = past_values[-1]  # Plus récente valeur avant 1h
    current = hist[-1][1]

    if past == 0:
        return None

    return ((current - past) / past) * 100


def clear_buy_ratio_history():
    """Efface tout l'historique buy ratio (utile pour tests)."""
    buy_ratio_history.clear()


def get_buy_ratio_history_size() -> int:
    """Retourne le nombre total d'entrées dans l'historique (debug)."""
    total = 0
    for token_dict in buy_ratio_history.values():
        for pool_list in token_dict.values():
            total += len(pool_list)
    return total
