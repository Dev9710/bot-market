"""
Module Telegram - Envoi de notifications

Gère l'envoi des alertes via Telegram.
"""

import requests
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(message: str) -> bool:
    """
    Envoie une alerte via Telegram.

    Args:
        message: Message à envoyer (format Markdown supporté)

    Returns:
        True si envoi réussi, False sinon
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        # Import local pour éviter circular dependency
        from utils.helpers import log
        log(f"❌ Erreur Telegram: {e}")
        return False
