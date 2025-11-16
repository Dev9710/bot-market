#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostic - Pourquoi pas d'alertes?"""

import os
import sys
import io
import json
import requests
from datetime import datetime

# Fix encodage Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_volume_conditions():
    """Vérifie les conditions de volume pour les top tokens."""
    print("🔍 DIAGNOSTIC: Pourquoi pas d'alertes?\n")
    print("=" * 80)

    # Charger config
    with open('config_tokens.json', 'r') as f:
        config = json.load(f)

    threshold = config['global_volume_scan']['ratio_threshold']
    min_vol24 = config['global_volume_scan']['min_vol24_usd']

    print(f"⚙️ Configuration actuelle:")
    print(f"   • Seuil volume: {threshold}x la moyenne")
    print(f"   • Volume 24h minimum: ${min_vol24:,}")
    print(f"   • Cooldown: {config['alert_cooldown_seconds']} secondes ({config['alert_cooldown_seconds']/60:.0f} min)\n")
    print("=" * 80)

    # Récupérer données CoinGecko
    print("\n📊 Récupération données CoinGecko (top 100)...\n")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        # Debug
        print(f"Type de réponse: {type(data)}")
        if isinstance(data, dict):
            print(f"Clés: {list(data.keys())[:5]}")
        elif isinstance(data, list):
            print(f"Nombre de tokens: {len(data)}")

        # Vérifier si c'est une erreur
        if isinstance(data, dict) and 'error' in data:
            print(f"❌ Erreur API CoinGecko: {data['error']}")
            return

        if not isinstance(data, list):
            print(f"❌ Format inattendu: {data}")
            return

        tokens = data
    except Exception as e:
        print(f"❌ Erreur CoinGecko: {e}")
        return

    # Analyser chaque token
    candidates = []

    for t in tokens:
        if not isinstance(t, dict):
            print(f"⚠️ Token invalide (type: {type(t)}): {t}")
            continue
        vol24_usd = t.get('total_volume', 0) or 0

        # Filtre 1: Volume 24h minimum
        if vol24_usd < min_vol24:
            continue

        # Calculer volume 1min estimé
        vol1m = vol24_usd / (24 * 60)  # Volume moyen par minute

        # Simuler une alerte si volume actuel était 5x supérieur
        # (En réalité, on devrait avoir le volume 1min réel, mais CoinGecko ne le fournit pas)

        symbol = t['symbol'].upper()
        name = t['name']
        price = t.get('current_price', 0)
        pct24 = t.get('price_change_percentage_24h', 0) or 0

        # On ne peut pas détecter le ratio exact sans le volume 1min réel
        # Mais on peut voir quels tokens POURRAIENT trigger une alerte

        candidates.append({
            'rank': t['market_cap_rank'],
            'symbol': symbol,
            'name': name,
            'price': price,
            'vol24_usd': vol24_usd,
            'vol1m_avg': vol1m,
            'pct24': pct24
        })

    # Afficher les candidats potentiels
    print(f"✅ Tokens éligibles (volume > ${min_vol24:,}): {len(candidates)}\n")
    print("=" * 80)
    print(f"{'#':<4} {'SYMBOL':<8} {'NAME':<20} {'VOL 24H (USD)':<18} {'VOL/MIN':<15} {'%24H':<8}")
    print("=" * 80)

    for c in candidates[:20]:  # Top 20
        print(f"{c['rank']:<4} {c['symbol']:<8} {c['name'][:18]:<20} ${c['vol24_usd']:>15,.0f}  ${c['vol1m_avg']:>12,.0f}  {c['pct24']:>6.1f}%")

    print("\n" + "=" * 80)
    print("\n💡 EXPLICATION:")
    print(f"""
Le bot scanne {len(candidates)} tokens qui dépassent le volume minimum.

🚨 POURQUOI VOUS NE RECEVEZ PAS D'ALERTES:

1. **Détection en temps réel impossible avec CoinGecko FREE**
   • CoinGecko free ne donne que le volume 24h total
   • Pour détecter un spike de volume 1min, il faudrait:
     - Suivre le volume toutes les minutes
     - Comparer chaque minute au volume moyen
     - Détecter quand volume 1min > {threshold}x moyenne

2. **Le bot utilise une approximation:**
   • Volume moyen/min = Volume 24h / 1440
   • Mais il ne peut pas voir les spikes en temps réel!

3. **Solutions possibles:**

   A) Utiliser CoinGecko PRO ($129/mois)
      → Accès aux données tick-by-tick

   B) Utiliser Binance API (GRATUIT ✅)
      → Volume en temps réel
      → Klines 1min pour détecter les spikes

   C) Réduire le seuil temporairement pour tester
      → Passer de {threshold}x à 2x
      → Juste pour voir si les alertes fonctionnent

🔧 RECOMMANDATION:
Je peux modifier le bot pour utiliser **Binance API** (gratuit) au lieu de
CoinGecko pour la détection de volume. Cela permettra de vraiment détecter
les spikes en temps réel!

Voulez-vous que je l'implémente?
""")

if __name__ == "__main__":
    check_volume_conditions()
