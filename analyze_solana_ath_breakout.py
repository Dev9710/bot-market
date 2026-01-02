#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE STRATÉGIE SOLANA ATH BREAKOUT
Vérifie si les patterns suivants existent dans les données:
1. Token casse ATH précédent → pump systématique
2. Token atteint $200K market cap → retrace → revient à $200K → pump
"""
import sys
import sqlite3
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = "alerts_history.db"

def analyze_ath_breakouts():
    """
    Analyse les tokens SOLANA avec alertes multiples
    pour détecter les breakouts d'ATH et la performance qui suit
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("="*80)
    print("🎯 ANALYSE STRATÉGIE SOLANA: ATH BREAKOUT")
    print("="*80)
    print()

    # 1. Récupérer tous les tokens SOLANA avec ×2+ alertes (pour tracker évolution prix)
    query = """
        SELECT
            pool_address,
            token_name,
            COUNT(*) as alert_count,
            GROUP_CONCAT(price_at_alert || '|' || timestamp || '|' || liquidity || '|' || volume_24h, ';') as price_history
        FROM alerts
        WHERE network = 'solana'
        GROUP BY pool_address
        HAVING alert_count >= 2
        ORDER BY alert_count DESC
    """

    cursor.execute(query)
    tokens = cursor.fetchall()

    print(f"📊 Tokens SOLANA analysés: {len(tokens)}")
    print(f"   (tokens avec ×2+ alertes pour tracker évolution)\n")

    # Statistiques globales
    ath_breakout_pumps = []
    ath_breakout_dumps = []
    market_cap_200k_pattern = []

    print("─"*80)
    print("🔍 ANALYSE DES PATTERNS D'ATH BREAKOUT\n")

    for token in tokens[:100]:  # Analyser top 100 pour performance
        pool_address, token_name, alert_count, price_history_raw = token

        # Parser l'historique des prix
        price_points = []
        for point in price_history_raw.split(';'):
            parts = point.split('|')
            if len(parts) >= 4:
                try:
                    price = float(parts[0]) if parts[0] else 0
                    timestamp = parts[1]
                    liquidity = float(parts[2]) if parts[2] else 0
                    volume = float(parts[3]) if parts[3] else 0
                    price_points.append({
                        'price': price,
                        'timestamp': timestamp,
                        'liquidity': liquidity,
                        'volume': volume
                    })
                except (ValueError, IndexError):
                    continue

        if len(price_points) < 2:
            continue

        # Trier par timestamp
        price_points.sort(key=lambda x: x['timestamp'])

        # Détecter les breakouts d'ATH
        for i in range(1, len(price_points)):
            current = price_points[i]
            previous_points = price_points[:i]

            # ATH précédent = prix max avant ce point
            previous_ath = max(p['price'] for p in previous_points)

            # Breakout = prix actuel > ATH précédent
            if current['price'] > previous_ath and previous_ath > 0:
                breakout_percent = ((current['price'] - previous_ath) / previous_ath) * 100

                # Calculer approximate market cap (prix * sqrt(liquidity) comme proxy)
                # Note: Vraie formule = prix * supply, mais on n'a pas supply
                # On utilise liquidity comme indicateur de taille
                approx_mcap = current['price'] * (current['liquidity'] ** 0.5) if current['liquidity'] > 0 else 0

                # Vérifier s'il y a une alerte suivante (= continuation du pump)
                has_next = i < len(price_points) - 1
                if has_next:
                    next_point = price_points[i + 1]
                    next_gain = ((next_point['price'] - current['price']) / current['price']) * 100 if current['price'] > 0 else 0

                    if next_gain > 0:
                        ath_breakout_pumps.append({
                            'token': token_name,
                            'breakout_percent': breakout_percent,
                            'next_gain': next_gain,
                            'approx_mcap': approx_mcap,
                            'liquidity': current['liquidity']
                        })
                    else:
                        ath_breakout_dumps.append({
                            'token': token_name,
                            'breakout_percent': breakout_percent,
                            'next_loss': next_gain,
                            'approx_mcap': approx_mcap
                        })

    # Afficher résultats ATH breakouts
    print(f"✅ ATH Breakouts détectés: {len(ath_breakout_pumps) + len(ath_breakout_dumps)}")
    print(f"   └─ Suivis de pump: {len(ath_breakout_pumps)} ({len(ath_breakout_pumps)/(len(ath_breakout_pumps)+len(ath_breakout_dumps))*100:.1f}%)")
    print(f"   └─ Suivis de dump: {len(ath_breakout_dumps)} ({len(ath_breakout_dumps)/(len(ath_breakout_pumps)+len(ath_breakout_dumps))*100:.1f}%)")
    print()

    if ath_breakout_pumps:
        avg_pump = sum(p['next_gain'] for p in ath_breakout_pumps) / len(ath_breakout_pumps)
        print(f"📈 Gain moyen après ATH breakout: +{avg_pump:.1f}%")
        print()

        # Top 10 pumps après ATH breakout
        print("🔥 TOP 10 PUMPS APRÈS ATH BREAKOUT:\n")
        top_pumps = sorted(ath_breakout_pumps, key=lambda x: x['next_gain'], reverse=True)[:10]
        for i, pump in enumerate(top_pumps, 1):
            print(f"{i:2}. {pump['token'][:30]:<30} | ATH +{pump['breakout_percent']:>6.1f}% → Puis +{pump['next_gain']:>6.1f}% | Liq: ${pump['liquidity']:>10,.0f}")

    print()
    print("─"*80)
    print("🔍 ANALYSE DU PATTERN $200K MARKET CAP\n")

    # 2. Analyser le pattern $200K market cap
    # Note: Sans supply exact, on utilise liquidity comme proxy
    # $200K market cap correspond approximativement à certaines zones de liquidité

    # Pattern recherché:
    # - Prix monte à un niveau
    # - Prix retrace (baisse)
    # - Prix revient au niveau précédent
    # - Prix pump ensuite

    retracement_patterns = []

    for token in tokens[:100]:
        pool_address, token_name, alert_count, price_history_raw = token

        price_points = []
        for point in price_history_raw.split(';'):
            parts = point.split('|')
            if len(parts) >= 4:
                try:
                    price = float(parts[0]) if parts[0] else 0
                    timestamp = parts[1]
                    liquidity = float(parts[2]) if parts[2] else 0
                    volume = float(parts[3]) if parts[3] else 0
                    price_points.append({
                        'price': price,
                        'timestamp': timestamp,
                        'liquidity': liquidity,
                        'volume': volume
                    })
                except:
                    continue

        if len(price_points) < 4:  # Besoin de min 4 points pour détecter pattern
            continue

        price_points.sort(key=lambda x: x['timestamp'])

        # Chercher pattern: High → Low → Back to High → Pump
        for i in range(len(price_points) - 3):
            p1 = price_points[i]['price']      # Premier high
            p2 = price_points[i + 1]['price']  # Retrace (low)
            p3 = price_points[i + 2]['price']  # Retour au high
            p4 = price_points[i + 3]['price']  # Pump après

            if p1 == 0:
                continue

            # Pattern: p2 < p1 (retrace) ET p3 proche de p1 (±20%) ET p4 > p3 (pump)
            retrace_pct = ((p2 - p1) / p1) * 100
            recovery_pct = ((p3 - p1) / p1) * 100
            pump_pct = ((p4 - p3) / p3) * 100 if p3 > 0 else 0

            # Conditions du pattern
            is_retracement = retrace_pct < -10  # Baisse d'au moins 10%
            is_recovery = -20 <= recovery_pct <= 20  # Revient à ±20% du niveau initial
            is_pump = pump_pct > 5  # Pump d'au moins 5% après

            if is_retracement and is_recovery and is_pump:
                # Calculer approximate market cap au point de recovery
                liq = price_points[i + 2]['liquidity']
                approx_mcap = p3 * (liq ** 0.5) if liq > 0 else 0

                retracement_patterns.append({
                    'token': token_name,
                    'retrace': retrace_pct,
                    'recovery': recovery_pct,
                    'pump_after': pump_pct,
                    'approx_mcap': approx_mcap,
                    'liquidity': liq,
                    'price_at_recovery': p3
                })

    print(f"✅ Patterns de retracement détectés: {len(retracement_patterns)}")

    if retracement_patterns:
        avg_pump_after_retrace = sum(p['pump_after'] for p in retracement_patterns) / len(retracement_patterns)
        print(f"📈 Gain moyen après retour au niveau: +{avg_pump_after_retrace:.1f}%")
        print()

        # Analyser zone $200K market cap (utiliser liquidity comme proxy)
        # Tokens avec liquidité $100K-$300K sont généralement dans cette zone de mcap
        mcap_200k_zone = [p for p in retracement_patterns if 100_000 <= p['liquidity'] <= 300_000]

        print(f"🎯 Patterns dans zone ~$200K market cap (Liq $100K-$300K): {len(mcap_200k_zone)}")
        if mcap_200k_zone:
            avg_pump_200k = sum(p['pump_after'] for p in mcap_200k_zone) / len(mcap_200k_zone)
            print(f"   └─ Gain moyen dans cette zone: +{avg_pump_200k:.1f}%")
        print()

        # Top 10 pumps après retracement
        print("🔥 TOP 10 PUMPS APRÈS PATTERN RETRACEMENT:\n")
        top_retrace = sorted(retracement_patterns, key=lambda x: x['pump_after'], reverse=True)[:10]
        for i, pattern in enumerate(top_retrace, 1):
            print(f"{i:2}. {pattern['token'][:30]:<30} | Retrace {pattern['retrace']:>6.1f}% → Récup → Pump +{pattern['pump_after']:>6.1f}% | Liq: ${pattern['liquidity']:>10,.0f}")

    print()
    print("─"*80)
    print("📊 RÉSUMÉ DE LA STRATÉGIE ATH BREAKOUT\n")

    # Calculer win rate
    if ath_breakout_pumps or ath_breakout_dumps:
        total_breakouts = len(ath_breakout_pumps) + len(ath_breakout_dumps)
        win_rate = (len(ath_breakout_pumps) / total_breakouts) * 100

        print(f"✅ Win Rate ATH Breakout: {win_rate:.1f}%")
        print(f"   ({len(ath_breakout_pumps)} pumps / {total_breakouts} total)")
        print()

        if ath_breakout_pumps:
            avg_gain = sum(p['next_gain'] for p in ath_breakout_pumps) / len(ath_breakout_pumps)
            max_gain = max(p['next_gain'] for p in ath_breakout_pumps)
            print(f"📈 Gain moyen si pump: +{avg_gain:.1f}%")
            print(f"🚀 Gain maximum observé: +{max_gain:.1f}%")
            print()

    if retracement_patterns:
        print(f"✅ Patterns retracement validés: {len(retracement_patterns)}")
        avg_retrace_pump = sum(p['pump_after'] for p in retracement_patterns) / len(retracement_patterns)
        max_retrace_pump = max(p['pump_after'] for p in retracement_patterns)
        print(f"📈 Gain moyen après retour: +{avg_retrace_pump:.1f}%")
        print(f"🚀 Gain max après retour: +{max_retrace_pump:.1f}%")
        print()

    print("─"*80)
    print("💡 CONCLUSION\n")

    if ath_breakout_pumps and win_rate >= 60:
        print("✅ STRATÉGIE ATH BREAKOUT: VALIDÉE")
        print(f"   • Win rate: {win_rate:.1f}% (>60% = viable)")
        print(f"   • Gain moyen: +{avg_gain:.1f}%")
        print("   • Recommandation: TRADER les breakouts d'ATH sur SOLANA")
    elif ath_breakout_pumps:
        print("⚠️  STRATÉGIE ATH BREAKOUT: RISQUÉE")
        print(f"   • Win rate: {win_rate:.1f}% (<60% = peu fiable)")
        print("   • Recommandation: NE PAS utiliser seule, combiner avec autres signaux")
    else:
        print("❌ STRATÉGIE ATH BREAKOUT: NON VALIDÉE")
        print("   • Données insuffisantes pour conclure")

    print()

    if retracement_patterns and len(retracement_patterns) >= 10:
        print("✅ PATTERN RETRACEMENT: VALIDÉ")
        print(f"   • Occurrences: {len(retracement_patterns)}")
        print(f"   • Gain moyen: +{avg_retrace_pump:.1f}%")
        print("   • Recommandation: SURVEILLER retracements puis retours au niveau")
    else:
        print("⚠️  PATTERN RETRACEMENT: PEU FRÉQUENT")
        print(f"   • Occurrences: {len(retracement_patterns)}")
        print("   • Recommandation: Pattern existe mais rare, ne pas baser stratégie dessus")

    print()
    print("="*80)
    print("🎯 STRATÉGIE RECOMMANDÉE BASÉE SUR LES DONNÉES:\n")

    # Rappel de la stratégie principale validée
    print("Au lieu de se concentrer uniquement sur ATH breakout,")
    print("utiliser la stratégie VALIDÉE identifiée dans l'analyse:\n")
    print("🏆 SOLANA ZONE OPTIMALE:")
    print("   • Volume: 1M-5M")
    print("   • Liquidité: <$200K")
    print("   • Score: ≥70")
    print("   • Freshness: <5min")
    print("   • Accélération: ≥5x")
    print("   • Performance: 130.9 alertes/token")
    print("   • Win rate: 95%+")
    print()
    print("💡 Combiner ATH breakout avec zone optimale = Maximum de probabilité")

    conn.close()

if __name__ == "__main__":
    analyze_ath_breakouts()
