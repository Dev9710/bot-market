#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Démonstration complète des nouvelles fonctionnalités avec données réelles."""

import sys
import io
import requests
import time

# Fix encodage Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# =========================
# FONCTIONS BINANCE API
# =========================

def get_binance_longshort_ratio(symbol):
    """Récupère le ratio long/short depuis Binance Futures API."""
    try:
        url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
        params = {
            "symbol": symbol,
            "period": "5m",
            "limit": 1
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if isinstance(data, list) and len(data) > 0:
            latest = data[0]
            ratio = float(latest['longShortRatio'])
            long_pct = ratio / (1 + ratio)
            short_pct = 1 - long_pct

            # Interprétation
            if long_pct >= 0.65:
                interpretation = f"⚠️ MAJORITÉ EN LONG ({long_pct*100:.1f}%)"
                risk = "Risque de liquidations si baisse soudaine"
                action = "Stop-loss recommandé"
            elif short_pct >= 0.65:
                interpretation = f"⚠️ MAJORITÉ EN SHORT ({short_pct*100:.1f}%)"
                risk = "Risque de short squeeze si hausse"
                action = "Opportunité d'achat si squeeze confirmé"
            else:
                interpretation = f"✓ ÉQUILIBRÉ (L:{long_pct*100:.1f}% S:{short_pct*100:.1f}%)"
                risk = "Bataille indécise"
                action = "Attendre signal clair"

            return {
                'longShortRatio': ratio,
                'longPct': long_pct,
                'shortPct': short_pct,
                'interpretation': interpretation,
                'risk': risk,
                'action': action
            }
    except Exception as e:
        print(f"⚠️ Erreur Binance API pour {symbol}: {e}")
        return None

    return None


# =========================
# FONCTION ANALYSE INTELLIGENTE
# =========================

def generate_smart_analysis(t, longshort_data=None):
    """Génère une analyse intelligente."""
    ratio = t['ratio']
    pct24 = t['pct24']
    pct_from_low = t['pct_from_low']
    h_l_ratio = t['h_l_ratio']
    vol1m = t['vol1m']
    vol24 = t['vol24']

    avg1m = vol24 / 1440

    txt = "\n🚨 POURQUOI CETTE ALERTE ?\n"
    txt += f"✓ Volume x{ratio:.1f} supérieur à la moyenne ({vol1m:,.0f}$/min vs {avg1m:,.0f}$/min)\n"

    if pct24 > 2:
        txt += f"✓ Prix en hausse : +{pct24:.2f}% sur 24h, +{pct_from_low:.1f}% depuis le plus bas\n"
    elif pct24 < -2:
        txt += f"⚠️ Prix en baisse : {pct24:.2f}% sur 24h, à {pct_from_low:.1f}% du plus bas\n"
    else:
        txt += f"✓ Prix stable : {pct24:+.2f}% sur 24h avec faible variation\n"

    volatility_pct = (h_l_ratio - 1) * 100
    if volatility_pct > 10:
        txt += f"✓ Volatilité élevée : {volatility_pct:.1f}% d'écart haut/bas\n"
    else:
        txt += f"✓ Volatilité modérée : {volatility_pct:.1f}% d'écart haut/bas\n"

    if longshort_data:
        txt += f"✓ Positions : {longshort_data['interpretation']}\n"

    txt += "\n💡 CE QUE ÇA SIGNIFIE :\n"

    if ratio >= 10 and pct24 > 20:
        txt += f"🔥 PUMP DÉTECTÉ ! Volume x{ratio:.1f} + Prix +{pct24:.1f}% = FOMO massif.\n"
        txt += "⚠️ DANGER : Ce qui monte vite redescend vite !\n"
    elif pct24 > 3 and pct_from_low > 10:
        txt += "Gros acheteurs entrent massivement. Prix monte avec volume élevé\n"
        txt += "= Signal d'accumulation forte. Momentum haussier confirmé.\n"
        if longshort_data and longshort_data['longPct'] > 0.60:
            txt += f"⚠️ Attention : {longshort_data['longPct']*100:.0f}% en long, risque si correction.\n"
    elif pct24 < -3 and pct_from_low < 10:
        txt += "Gros vendeurs liquident leurs positions massivement.\n"
        txt += "⚠️ Pression vendeuse importante, proche du support critique.\n"
    else:
        txt += f"Activité inhabituelle détectée. Volume x{ratio:.1f} au-dessus de la normale.\n"

    txt += "\n⚠️ QUE FAIRE :\n"

    if ratio >= 10 and pct24 > 20:
        txt += "❌ NE PAS ACHETER maintenant (risque de dump imminent) !\n"
        txt += "✓ Si vous détenez : Prenez vos profits progressivement\n"
    elif pct24 > 3 and pct_from_low > 10:
        txt += "✓ Surveiller les prochaines minutes\n"
        txt += "✓ Si volume reste élevé + prix monte = Signal d'achat\n"
        if longshort_data:
            txt += f"✓ {longshort_data['action']}\n"
    elif pct24 < -3 and pct_from_low < 5:
        txt += "⚠️ ATTENTION - Signal de vente potentiel\n"
        txt += "✓ Si vous détenez : Surveillez le support\n"
    else:
        txt += "✓ Surveiller l'évolution\n"
        txt += "✓ Attendre confirmation avant d'entrer\n"

    return txt


# =========================
# EXEMPLES DE TEST
# =========================

# Exemple 1 : Hausse forte
exemple_hausse = {
    "symbol": "BTC",
    "name": "Bitcoin",
    "prix": 98765.43,
    "vol1m": 12345678,
    "vol24": 21000000000,
    "ratio": 8.3,
    "pct24": 5.67,
    "pct_from_low": 12.3,
    "h_l_ratio": 1.15
}

# Exemple 2 : Baisse forte
exemple_baisse = {
    "symbol": "ETH",
    "name": "Ethereum",
    "prix": 3456.78,
    "vol1m": 8765432,
    "vol24": 15000000000,
    "ratio": 7.1,
    "pct24": -3.45,
    "pct_from_low": 2.1,
    "h_l_ratio": 1.08
}

# Exemple 3 : PUMP
exemple_pump = {
    "symbol": "PEPE",
    "name": "Pepe",
    "prix": 0.000012,
    "vol1m": 2345678,
    "vol24": 3500000000,
    "ratio": 15.3,
    "pct24": 45.67,
    "pct_from_low": 78.9,
    "h_l_ratio": 1.89
}


if __name__ == "__main__":
    print("=" * 80)
    print("📱 DÉMONSTRATION COMPLÈTE - NOUVELLES ALERTES v2.0")
    print("=" * 80)
    print("\n⏳ Récupération des données réelles Binance...\n")

    # Test 1 : BTC avec données Binance
    print("─" * 80)
    print("EXEMPLE 1 : Bitcoin (Hausse forte)")
    print("─" * 80)

    longshort_btc = get_binance_longshort_ratio("BTCUSDT")

    print(f"\n💰 Prix : {exemple_hausse['prix']:.2f} $")
    print(f"📈 Volume 1m estimé : {exemple_hausse['vol1m']:,.0f} $")
    print(f"🔥 Multiplicateur : x{exemple_hausse['ratio']:.1f}")
    print(f"📊 Variation 24h : +{exemple_hausse['pct24']:.2f}%")
    print(f"📉 Depuis le bas 24h : {exemple_hausse['pct_from_low']:.1f}%")

    if longshort_btc:
        print(f"\n📊 POSITIONS (Binance Futures) :")
        print(f"🟢 LONGS : {longshort_btc['longPct']*100:.1f}%  |  🔴 SHORTS : {longshort_btc['shortPct']*100:.1f}%")
        print(f"{longshort_btc['interpretation']}")

    analysis = generate_smart_analysis(exemple_hausse, longshort_btc)
    print(analysis)

    # Test 2 : ETH avec données Binance
    print("\n" + "=" * 80)
    print("EXEMPLE 2 : Ethereum (Baisse forte)")
    print("─" * 80)

    longshort_eth = get_binance_longshort_ratio("ETHUSDT")

    print(f"\n💰 Prix : {exemple_baisse['prix']:.2f} $")
    print(f"📈 Volume 1m estimé : {exemple_baisse['vol1m']:,.0f} $")
    print(f"🔥 Multiplicateur : x{exemple_baisse['ratio']:.1f}")
    print(f"📊 Variation 24h : {exemple_baisse['pct24']:.2f}%")
    print(f"📉 Depuis le bas 24h : {exemple_baisse['pct_from_low']:.1f}%")

    if longshort_eth:
        print(f"\n📊 POSITIONS (Binance Futures) :")
        print(f"🟢 LONGS : {longshort_eth['longPct']*100:.1f}%  |  🔴 SHORTS : {longshort_eth['shortPct']*100:.1f}%")
        print(f"{longshort_eth['interpretation']}")

    analysis = generate_smart_analysis(exemple_baisse, longshort_eth)
    print(analysis)

    # Test 3 : PUMP (pas de données Binance pour PEPE souvent)
    print("\n" + "=" * 80)
    print("EXEMPLE 3 : Pepe (PUMP massif)")
    print("─" * 80)

    print(f"\n💰 Prix : {exemple_pump['prix']:.8f} $")
    print(f"📈 Volume 1m estimé : {exemple_pump['vol1m']:,.0f} $")
    print(f"🔥 Multiplicateur : x{exemple_pump['ratio']:.1f}")
    print(f"📊 Variation 24h : +{exemple_pump['pct24']:.2f}%")
    print(f"📉 Depuis le bas 24h : {exemple_pump['pct_from_low']:.1f}%")

    analysis = generate_smart_analysis(exemple_pump, None)
    print(analysis)

    print("\n" + "=" * 80)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("=" * 80)
    print("\n📋 RÉSUMÉ :")
    print("✓ Descriptions intelligentes selon le scénario (hausse/baisse/pump)")
    print("✓ Données long/short réelles de Binance (BTC, ETH)")
    print("✓ Métriques expliquées (volume, prix, volatilité)")
    print("✓ Recommandations d'action concrètes")
    print("\n🚀 Le bot est prêt à déployer avec ces nouvelles fonctionnalités !")
