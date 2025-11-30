#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génération d'alertes pédagogiques pour détections Binance
Format identique à alerte.py mais avec métriques Binance temps réel
"""

import sys
import io
from datetime import datetime
from typing import Dict, Optional

# Fix encodage Windows (seulement si pas déjà fait)
if sys.platform == "win32" and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (ValueError, AttributeError):
        pass  # Déjà configuré


def generate_binance_analysis(anomaly: Dict, longshort_data: Optional[Dict] = None) -> str:
    """
    Génère une analyse intelligente et pédagogique pour une anomalie Binance.

    Format identique à generate_smart_analysis() de alerte.py mais avec:
    - Volume 1min temps réel (au lieu d'estimation)
    - Liquidations
    - Open Interest
    - Funding Rate

    Args:
        anomaly: Données de l'anomalie détectée
        longshort_data: Ratio long/short (optionnel, déjà implémenté)

    Returns:
        Texte formaté en Markdown pour Telegram
    """
    v = anomaly['volume_data']
    liq = anomaly.get('liquidations')
    oi = anomaly.get('open_interest')
    funding = anomaly.get('funding_rate')

    symbol = anomaly['symbol']
    price = v['price']
    vol_1min = v['current_1min_volume']
    vol_avg = v['avg_1h_volume']
    ratio = v['ratio']

    txt = ""

    # ========================================================================
    # SECTION 1: POURQUOI CETTE ALERTE ?
    # ========================================================================
    txt += "\n🚨 *POURQUOI CETTE ALERTE ?*\n"

    # Raison principale: Volume spike
    txt += f"✓ Volume x{ratio:.1f} supérieur à la moyenne ({vol_1min:,.0f}$/min vs {vol_avg:,.0f}$/min)\n"

    # Liquidations (si présentes)
    if liq and liq['total_liquidated_usd'] > 0:
        total_liq = liq['total_liquidated_usd']
        long_liq = liq['long_liquidated']
        short_liq = liq['short_liquidated']

        if total_liq > 1_000_000:  # >$1M
            txt += f"⚠️ LIQUIDATIONS MASSIVES : ${total_liq:,.0f} liquidés (5 min)\n"

            if long_liq > short_liq * 2:
                txt += f"   → {long_liq/total_liq*100:.0f}% de LONGS liquidés (vendeurs forcés)\n"
            elif short_liq > long_liq * 2:
                txt += f"   → {short_liq/total_liq*100:.0f}% de SHORTS liquidés (acheteurs forcés)\n"
        else:
            txt += f"✓ Liquidations modérées : ${total_liq:,.0f}\n"

    # Open Interest (si présent)
    if oi and oi['open_interest_usd'] > 0:
        oi_usd = oi['open_interest_usd']

        if oi_usd > 100_000_000:  # >$100M
            txt += f"✓ Open Interest élevé : ${oi_usd/1_000_000:.0f}M (fort intérêt institutionnel)\n"

    # Funding Rate (si présent)
    if funding is not None:
        funding_pct = funding * 100

        if abs(funding_pct) > 0.1:  # >0.1%
            if funding_pct > 0:
                txt += f"⚠️ Funding Rate élevé : +{funding_pct:.3f}% (majorité en LONG, coûteux)\n"
            else:
                txt += f"⚠️ Funding Rate négatif : {funding_pct:.3f}% (majorité en SHORT, coûteux)\n"

    # ========================================================================
    # SECTION 2: CE QUE ÇA SIGNIFIE
    # ========================================================================
    txt += "\n💡 *CE QUE ÇA SIGNIFIE :*\n"

    # Analyse contextuelle basée sur la combinaison des métriques

    # Scénario 1: SHORT SQUEEZE (shorts liquidés massivement)
    if liq and liq['short_liquidated'] > liq['long_liquidated'] * 3 and liq['total_liquidated_usd'] > 1_000_000:
        txt += f"🔥 *SHORT SQUEEZE DÉTECTÉ !* ${liq['short_liquidated']:,.0f} de shorts liquidés.\n"
        txt += "Les vendeurs à découvert sont forcés d'acheter → Pression acheteuse massive.\n"
        txt += "Le prix va probablement continuer à monter à court terme.\n"

    # Scénario 2: LONG SQUEEZE (longs liquidés massivement)
    elif liq and liq['long_liquidated'] > liq['short_liquidated'] * 3 and liq['total_liquidated_usd'] > 1_000_000:
        txt += f"🔴 *LONG SQUEEZE DÉTECTÉ !* ${liq['long_liquidated']:,.0f} de longs liquidés.\n"
        txt += "Les acheteurs sont forcés de vendre → Pression vendeuse massive.\n"
        txt += "Le prix va probablement continuer à baisser à court terme.\n"

    # Scénario 3: Volume élevé + OI croissant + Funding neutre = Accumulation
    elif ratio >= 5 and oi and oi['open_interest_usd'] > 50_000_000 and abs(funding or 0) < 0.05:
        txt += "📈 *ACCUMULATION EN COURS*\n"
        txt += f"Volume x{ratio:.1f} + Open Interest élevé (${oi['open_interest_usd']/1_000_000:.0f}M) = Gros joueurs entrent.\n"
        txt += "Signal haussier si le volume se maintient.\n"

    # Scénario 4: Volume élevé + Funding très positif = Risque correction
    elif ratio >= 5 and funding and funding > 0.1:
        txt += "⚠️ *SURCHARGE DE LONGS - RISQUE DE CORRECTION*\n"
        txt += f"Funding rate très élevé (+{funding*100:.3f}%) = Trop de traders en long.\n"
        txt += "Beaucoup paient des frais → Risque de prise de profits massive.\n"

    # Scénario 5: Volume élevé + Funding très négatif = Potentiel rebond
    elif ratio >= 5 and funding and funding < -0.1:
        txt += "🎯 *MAJORITÉ EN SHORT - POTENTIEL REBOND*\n"
        txt += f"Funding rate très négatif ({funding*100:.3f}%) = Trop de traders en short.\n"
        txt += "Si le prix commence à monter → Short squeeze possible.\n"

    # Scénario 6: Volume spike simple
    else:
        txt += f"Volume x{ratio:.1f} indique un intérêt soudain sur ce token.\n"
        txt += "Cela peut précéder un mouvement de prix important (haussier ou baissier).\n"

    # Ajouter contexte Long/Short si disponible
    if longshort_data:
        long_pct = longshort_data.get('long_pct', 0) * 100
        short_pct = longshort_data.get('short_pct', 0) * 100
        interpretation = longshort_data.get('interpretation', '')

        txt += f"\n📊 *POSITIONS TRADERS* (Binance):\n"
        txt += f"🟢 {long_pct:.1f}% LONGS | 🔴 {short_pct:.1f}% SHORTS\n"
        txt += f"{interpretation}\n"

    # ========================================================================
    # SECTION 3: QUE FAIRE ?
    # ========================================================================
    txt += "\n⚠️ *QUE FAIRE :*\n"

    # Recommandations basées sur le scénario

    # Short squeeze → Acheter rapidement
    if liq and liq['short_liquidated'] > liq['long_liquidated'] * 3 and liq['total_liquidated_usd'] > 1_000_000:
        txt += "✅ OPPORTUNITÉ D'ACHAT - Court terme (30 min - 2h)\n"
        txt += "→ Entrer maintenant pendant le squeeze\n"
        txt += "→ Stop loss à -3% (mouvement volatile)\n"
        txt += "→ Take profit à +5-10%\n"

    # Long squeeze → Vendre ou attendre
    elif liq and liq['long_liquidated'] > liq['short_liquidated'] * 3 and liq['total_liquidated_usd'] > 1_000_000:
        txt += "❌ NE PAS ACHETER - Pression vendeuse active\n"
        txt += "→ Attendre stabilisation (1-2h)\n"
        txt += "→ Ou shorter si vous êtes expérimenté\n"

    # Surcharge longs → Prudence
    elif funding and funding > 0.1:
        txt += "⚠️ PRUDENCE - Marché surchargé en longs\n"
        txt += "→ Si vous êtes en position: Prenez vos profits\n"
        txt += "→ Si vous voulez entrer: Attendez correction\n"

    # Majorité shorts → Opportunité contrarian
    elif funding and funding < -0.1:
        txt += "✅ OPPORTUNITÉ CONTRARIAN - Setup haussier\n"
        txt += "→ Majorité des traders en short = Fuel pour pump\n"
        txt += "→ Entrer progressivement (DCA)\n"
        txt += "→ Take profit si short squeeze démarre\n"

    # Accumulation → Hold moyen terme
    elif ratio >= 5 and oi and oi['open_interest_usd'] > 50_000_000:
        txt += "✓ SURVEILLER - Signal d'accumulation\n"
        txt += "→ Gros joueurs entrent = Bullish moyen terme\n"
        txt += "→ Acheter si le prix reste stable\n"
        txt += "→ Hold 1-7 jours\n"

    # Volume spike simple → Surveillance
    else:
        txt += "✓ SURVEILLER l'évolution des prochaines minutes\n"
        txt += "→ Attendre confirmation (prix monte ou baisse?)\n"
        txt += "→ Ne pas FOMO acheter immédiatement\n"

    return txt


def format_binance_alert(anomalies: list, max_alerts: int = 3) -> str:
    """
    Formate les anomalies Binance en alerte Telegram pédagogique.

    Format identique à format_global_alert() de alerte.py.

    Args:
        anomalies: Liste des anomalies détectées
        max_alerts: Nombre maximum d'alertes à envoyer

    Returns:
        Texte formaté pour Telegram (Markdown)
    """
    if not anomalies:
        return ""

    # Trier par ratio de volume (plus fort = plus important)
    sorted_anomalies = sorted(
        anomalies,
        key=lambda x: x['volume_data']['ratio'],
        reverse=True
    )[:max_alerts]

    txt = "🌍 *Top activités crypto détectées*\n"
    txt += "_(Volume temps réel Binance — Analyse détaillée)_\n\n"

    for i, anomaly in enumerate(sorted_anomalies, 1):
        symbol = anomaly['symbol']
        v = anomaly['volume_data']
        price = v['price']
        ratio = v['ratio']
        vol_1min = v['current_1min_volume']

        # Header
        txt += f"#{i} — *{symbol}*\n"
        txt += f"💰 Prix : ${price:,.4f}\n"
        txt += f"📈 Volume 1min : ${vol_1min:,.0f}\n"
        txt += f"🔥 Ratio : x{ratio:.1f}\n"

        # Open Interest si disponible
        if anomaly.get('open_interest'):
            oi = anomaly['open_interest']['open_interest_usd']
            txt += f"📊 Open Interest : ${oi/1_000_000:.1f}M\n"

        # Liquidations si disponibles
        if anomaly.get('liquidations') and anomaly['liquidations']['total_liquidated_usd'] > 0:
            liq = anomaly['liquidations']
            txt += f"⚡ Liquidations (5min) : ${liq['total_liquidated_usd']:,.0f}\n"

        txt += f"⏰ Détecté : {anomaly['detection_time'].strftime('%H:%M:%S')}\n"

        # Récupérer données long/short (si implémenté)
        longshort_data = None
        try:
            # Fonction déjà dans alerte.py
            import alerte
            longshort_data = alerte.get_binance_longshort_ratio(f"{symbol}USDT")
        except:
            pass

        # Analyse pédagogique
        analysis = generate_binance_analysis(anomaly, longshort_data)
        txt += analysis

        # Séparateur entre alertes
        if i < len(sorted_anomalies):
            txt += "\n" + "─" * 40 + "\n\n"

    txt += "\n🤖 _Détection automatique Binance API_\n"
    txt += f"_Scan effectué : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_"

    return txt


if __name__ == "__main__":
    # Test avec donnée exemple (SOL de notre test)
    test_anomaly = {
        'symbol': 'SOL',
        'volume_data': {
            'current_1min_volume': 3356184,
            'avg_1h_volume': 836309,
            'ratio': 4.0,
            'price': 136.10
        },
        'liquidations': {
            'total_liquidated_usd': 2500000,
            'long_liquidated': 2000000,
            'short_liquidated': 500000,
            'count': 45
        },
        'open_interest': {
            'open_interest_usd': 1112988915,
            'open_interest_amount': 8177552
        },
        'funding_rate': -0.000023,
        'detection_time': datetime.now()
    }

    # Test avec short squeeze
    test_anomaly_squeeze = {
        'symbol': 'XRP',
        'volume_data': {
            'current_1min_volume': 8500000,
            'avg_1h_volume': 1200000,
            'ratio': 7.1,
            'price': 1.12
        },
        'liquidations': {
            'total_liquidated_usd': 15000000,
            'long_liquidated': 2000000,
            'short_liquidated': 13000000,  # Short squeeze!
            'count': 234
        },
        'open_interest': {
            'open_interest_usd': 850000000,
            'open_interest_amount': 758928571
        },
        'funding_rate': 0.0015,
        'detection_time': datetime.now()
    }

    print("="*80)
    print("TEST 1: Alerte SOL (volume spike + long squeeze modéré)")
    print("="*80)
    alert1 = format_binance_alert([test_anomaly])
    print(alert1)

    print("\n\n")
    print("="*80)
    print("TEST 2: Alerte XRP (short squeeze massif)")
    print("="*80)
    alert2 = format_binance_alert([test_anomaly_squeeze])
    print(alert2)
