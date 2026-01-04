"""
Fonctions utilitaires générales du Scanner V3

Fonctions helper simples pour log, extraction de données, etc.
"""

import time
from datetime import datetime
from typing import Dict
from config.settings import NETWORK_NAMES, COOLDOWN_SECONDS


def get_network_display_name(network_id: str) -> str:
    """Convertit ID network en nom lisible."""
    return NETWORK_NAMES.get(network_id.lower(), network_id.upper())


def log(msg: str):
    """Affiche un message avec timestamp."""
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")


def extract_base_token(pool_name: str) -> str:
    """Extrait le nom du base token depuis le nom du pool."""
    # Ex: "LAVA / USDT 0.01%" -> "LAVA"
    if "/" in pool_name:
        return pool_name.split("/")[0].strip()
    return pool_name.strip()


def check_cooldown(alert_key: str, alert_cooldown: Dict) -> bool:
    """
    Vérifie si alerte en cooldown (LEGACY - utiliser should_send_alert à la place).

    Args:
        alert_key: Clé unique pour l'alerte
        alert_cooldown: Dictionnaire des cooldowns (modifié en place)

    Returns:
        True si alerte peut être envoyée, False sinon
    """
    now = time.time()
    if alert_key in alert_cooldown:
        elapsed = now - alert_cooldown[alert_key]
        if elapsed < COOLDOWN_SECONDS:
            return False
    alert_cooldown[alert_key] = now
    return True


def format_price(price: float) -> str:
    """
    Formate le prix de manière intelligente et cohérente (FIX HARMONISATION):
    - Prix >= $1: 2 décimales (ex: $1.23)
    - Prix >= $0.01: 4 décimales (ex: $0.1574) - ÉVITE PROBLÈMES ARRONDI TP
    - Prix < $0.01: 8 décimales (ex: $0.00012345)
    """
    if price >= 1.0:
        return f"${price:.2f}"
    elif price >= 0.01:
        # 4 décimales pour précision TP (évite arrondi $0.1574 → $0.16)
        return f"${price:.4f}"
    else:
        # Pour les très petits prix, garder 8 décimales
        return f"${price:.8f}"
