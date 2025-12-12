#!/usr/bin/env python3
"""Test simple de notification Telegram"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"Token: {TELEGRAM_BOT_TOKEN[:20]}...")
print(f"Chat ID: {TELEGRAM_CHAT_ID}")

# Test d'envoi
message = """
🧪 TEST NOTIFICATION BINANCE

Ceci est un message de test.
Si vous recevez ce message, la configuration Telegram fonctionne !

✅ Bot configuré correctement
"""

try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, data=data, timeout=10)

    if response.status_code == 200:
        print("✅ Message envoyé avec succès !")
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"Réponse: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")