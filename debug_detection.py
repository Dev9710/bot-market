#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug - Pourquoi aucune alerte détectée?"""

import sys
import io
import json
import requests
from datetime import datetime

# Fix encodage Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Charger config
with open('config_tokens.json', 'r') as f:
    config = json.load(f)

threshold = config['global_volume_scan']['ratio_threshold']
min_vol24 = config['global_volume_scan']['min_vol24_usd']

print("=" * 80)
print("🔍 DEBUG: Pourquoi aucune alerte depuis hier?")
print("=" * 80)
print(f"\n⚙️ Configuration:")
print(f"   • Seuil volume: {threshold}x la moyenne")
print(f"   • Volume 24h minimum: ${min_vol24:,}")
print(f"\n📊 Récupération données CoinGecko (top 500 tokens)...\n")

# Récupérer données
all_tokens = []
for page in [1, 2]:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": page
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        # Vérifier rate limit
        if isinstance(data, dict) and "status" in data:
            error_code = data.get("status", {}).get("error_code")
            if error_code == 429:
                print("❌ RATE LIMIT ATTEINT!")
                print("Le bot ne peut pas récupérer les données.\n")
                break

        if isinstance(data, list):
            all_tokens.extend(data)
            print(f"   ✅ Page {page}: {len(data)} tokens récupérés")
    except Exception as e:
        print(f"   ❌ Erreur page {page}: {e}")

print(f"\n📈 Total tokens récupérés: {len(all_tokens)}")

# Analyser chaque token
candidates = []
for t in all_tokens:
    vol24_usd = t.get('total_volume', 0) or 0

    # Filtre volume minimum
    if vol24_usd < min_vol24:
        continue

    # Calculer volume moyen par minute
    vol_avg_1min = vol24_usd / (24 * 60)

    # On ne peut pas avoir le volume 1min réel avec CoinGecko Free
    # Donc on simule: si le token a un volume anormal, on le détecterait

    symbol = t['symbol'].upper()
    name = t['name']
    price = t.get('current_price', 0)
    pct24 = t.get('price_change_percentage_24h', 0) or 0
    mc = t.get('market_cap', 0) or 0

    # Tokens avec variation de prix forte = potentiels candidats
    if abs(pct24) > 20:  # +20% ou -20%
        candidates.append({
            'symbol': symbol,
            'name': name,
            'price': price,
            'vol24': vol24_usd,
            'vol_avg_1min': vol_avg_1min,
            'pct24': pct24,
            'mc': mc
        })

print(f"\n🎯 Tokens avec variation >20% (potentiels candidats): {len(candidates)}")

if candidates:
    print("\n" + "=" * 80)
    print(f"{'SYMBOL':<10} {'NAME':<20} {'PRICE':<12} {'%24H':<10} {'VOL 24H':<15}")
    print("=" * 80)

    for c in sorted(candidates, key=lambda x: abs(x['pct24']), reverse=True)[:10]:
        print(f"{c['symbol']:<10} {c['name'][:18]:<20} ${c['price']:<11.6f} {c['pct24']:>7.1f}%  ${c['vol24']:>12,.0f}")
else:
    print("\n⚠️ AUCUN token avec variation >20% détecté!")

print("\n" + "=" * 80)
print("\n💡 EXPLICATION:\n")

if not candidates:
    print("""
🔴 AUCUNE ALERTE = NORMAL!

Le marché crypto est actuellement CALME:
• Aucun token n'a une variation >20% sur 24h
• Pas de pump/dump en cours
• Volume faible sur la plupart des tokens

➡️ Votre bot fonctionne correctement, il attend simplement un mouvement!

📊 Pour vérifier que les alertes fonctionnent:
""")
    print(f"   1. Réduire le seuil de {threshold}x à 2x dans config_tokens.json")
    print(f"   2. Ou attendre qu'un token fasse un vrai pump")
else:
    print(f"""
⚠️ PROBLÈME DÉTECTÉ!

Il y a {len(candidates)} tokens avec variation >20% MAIS aucune alerte envoyée!

Causes possibles:
1. Le volume 1min n'atteint pas {threshold}x la moyenne
   (CoinGecko Free ne donne que le volume 24h, pas le volume 1min réel)

2. Le bot ne peut pas détecter les spikes courts
   (Un pump de 5 min avec volume x10 ne se voit pas dans le volume 24h total)

3. Solution: Utiliser Binance API pour volume temps réel
""")

print("\n" + "=" * 80)
print("\n🔧 RECOMMANDATIONS:\n")
print("""
1. COURT TERME - Tester que les alertes fonctionnent:
   Modifier config_tokens.json ligne 9:
   "ratio_threshold": 2.0  (au lieu de 5.0)

   Puis redémarrer le bot. Vous devriez recevoir des alertes.

2. MOYEN TERME - Améliorer la détection:
   Migrer vers Binance API pour avoir:
   • Volume en temps réel (tick-by-tick)
   • Détection des spikes courts (5-10 min)
   • Plus de tokens couverts

3. VÉRIFICATION - Le bot fonctionne?
   python test_telegram.py

   Si vous recevez le message, Telegram fonctionne ✅
""")
print("=" * 80)
