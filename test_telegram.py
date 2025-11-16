#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Telegram connection and send test alert."""

import os
import sys
import io
import requests
from dotenv import load_dotenv

# Fix encodage Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Charger variables d'environnement
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def test_telegram_connection():
    """Test la connexion à l'API Telegram."""
    print(f"🔍 Test de connexion Telegram...")
    print(f"   Bot Token: {TELEGRAM_BOT_TOKEN[:10]}..." if TELEGRAM_BOT_TOKEN else "   ❌ Bot Token manquant!")
    print(f"   Chat ID: {TELEGRAM_CHAT_ID}" if TELEGRAM_CHAT_ID else "   ❌ Chat ID manquant!")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n❌ Configuration Telegram incomplète!")
        return False

    # Test 1: Vérifier que le bot existe
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            bot_info = r.json()
            if bot_info.get('ok'):
                print(f"\n✅ Bot trouvé: @{bot_info['result']['username']}")
                print(f"   Nom: {bot_info['result']['first_name']}")
            else:
                print(f"\n❌ Erreur API: {bot_info}")
                return False
        else:
            print(f"\n❌ Erreur HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ Erreur connexion: {e}")
        return False

    # Test 2: Envoyer un message de test
    print("\n📤 Envoi d'un message de test...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    message = """🧪 *TEST CONNEXION TELEGRAM*

✅ Le bot peut envoyer des messages!

🔍 *Configuration actuelle:*
• Alert cooldown: 600 secondes (10 minutes)
• Volume threshold: 5x la moyenne
• Scan interval: 60 secondes

Si vous recevez ce message, votre bot Telegram fonctionne correctement! 🎉"""

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            result = r.json()
            if result.get('ok'):
                print("✅ Message envoyé avec succès!")
                print(f"   Message ID: {result['result']['message_id']}")
                return True
            else:
                print(f"❌ Erreur API: {result}")
                return False
        else:
            print(f"❌ Erreur HTTP {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST CONNEXION TELEGRAM BOT")
    print("=" * 60)

    success = test_telegram_connection()

    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCÈS - Le bot Telegram fonctionne!")
        print("\nSi vous ne recevez PAS d'alertes, c'est probablement parce que:")
        print("1. Aucun token ne dépasse le seuil de volume (5x)")
        print("2. Les alertes sont en cooldown (10 min entre chaque)")
        print("3. Le volume 24h est trop faible (< 100 000 USD)")
    else:
        print("❌ ÉCHEC - Vérifiez votre configuration!")
        print("\nActions à faire:")
        print("1. Vérifiez votre fichier .env")
        print("2. Assurez-vous que le bot token est valide")
        print("3. Vérifiez que vous avez démarré une conversation avec le bot")
    print("=" * 60)
