#!/usr/bin/env python3
"""
BACKTESTING COMPLET - Comparaison performances par réseau
Analyse des 3,233+ alertes pour valider seuils Arbitrum vs autres réseaux
"""
import sqlite3
import os
from datetime import datetime
from collections import defaultdict

# Configuration
DB_PATH = os.getenv("DB_PATH", "/data/alerts_history.db")

# Seuils configurés
NETWORK_THRESHOLDS = {
    "solana": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "bsc": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "eth": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "base": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "arbitrum": {"min_liquidity": 2000, "min_volume": 400, "min_txns": 10},
    "avax": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
    "polygon_pos": {"min_liquidity": 100000, "min_volume": 50000, "min_txns": 100},
}

def analyze_network_performance():
    """Analyse complète des performances par réseau"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("📊 BACKTESTING - COMPARAISON RÉSEAUX")
    print("=" * 80)

    # 1. STATISTIQUES GLOBALES
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cursor.fetchone()[0]
    print(f"\n✅ Total alertes analysées: {total_alerts:,}")

    # 2. RÉPARTITION PAR RÉSEAU
    cursor.execute("""
        SELECT network, COUNT(*) as count
        FROM alerts
        GROUP BY network
        ORDER BY count DESC
    """)
    networks = cursor.fetchall()

    print(f"\n📡 RÉPARTITION PAR RÉSEAU:")
    for network, count in networks:
        pct = (count / total_alerts * 100) if total_alerts > 0 else 0
        thresholds = NETWORK_THRESHOLDS.get(network, NETWORK_THRESHOLDS.get("default", {}))
        liq = thresholds.get("min_liquidity", 0) / 1000
        vol = thresholds.get("min_volume", 0) / 1000
        txns = thresholds.get("min_txns", 0)
        print(f"   {network.upper():15} {count:5} alertes ({pct:5.1f}%) - Seuils: ${liq:.0f}K/${vol:.0f}K/{txns}txns")

    # 3. ANALYSE TP HIT PAR RÉSEAU
    print(f"\n🎯 ANALYSE TP HIT PAR RÉSEAU:")
    print(f"{'Réseau':<15} {'Alertes':>8} {'TP1':>8} {'TP2':>8} {'TP3':>8} {'Win%':>8} {'Score Moy':>10}")
    print("-" * 80)

    results = {}

    for network, count in networks:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(score) as avg_score,
                SUM(CASE WHEN prix_max_atteint >= tp1_price THEN 1 ELSE 0 END) as tp1_hits,
                SUM(CASE WHEN prix_max_atteint >= tp2_price THEN 1 ELSE 0 END) as tp2_hits,
                SUM(CASE WHEN prix_max_atteint >= tp3_price THEN 1 ELSE 0 END) as tp3_hits
            FROM alerts
            WHERE network = ?
            AND tp1_price > 0
            AND prix_max_atteint > 0
        """, (network,))

        row = cursor.fetchone()
        if row and row[0] > 0:
            total, avg_score, tp1, tp2, tp3 = row
            win_rate = (tp1 / total * 100) if total > 0 else 0

            results[network] = {
                'total': total,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'win_rate': win_rate,
                'avg_score': avg_score or 0
            }

            print(f"{network.upper():<15} {total:8} {tp1:8} {tp2:8} {tp3:8} {win_rate:7.1f}% {avg_score:9.1f}")

    # 4. COMPARAISON ARBITRUM VS AUTRES
    print(f"\n" + "=" * 80)
    print("🔬 COMPARAISON DÉTAILLÉE: ARBITRUM vs AUTRES RÉSEAUX")
    print("=" * 80)

    if 'arbitrum' in results:
        arb = results['arbitrum']
        print(f"\n📊 ARBITRUM (Seuils: $2K / $400 / 10txns):")
        print(f"   Alertes: {arb['total']}")
        print(f"   TP1 Hit: {arb['tp1']} ({arb['tp1']/arb['total']*100:.1f}%)")
        print(f"   TP2 Hit: {arb['tp2']} ({arb['tp2']/arb['total']*100:.1f}%)")
        print(f"   TP3 Hit: {arb['tp3']} ({arb['tp3']/arb['total']*100:.1f}%)")
        print(f"   Win Rate: {arb['win_rate']:.1f}%")
        print(f"   Score Moyen: {arb['avg_score']:.1f}/100")

    # Moyenne des autres réseaux (seuils stricts)
    strict_networks = ['solana', 'bsc', 'eth', 'base']
    strict_stats = {
        'total': 0,
        'tp1': 0,
        'tp2': 0,
        'tp3': 0
    }

    for net in strict_networks:
        if net in results:
            strict_stats['total'] += results[net]['total']
            strict_stats['tp1'] += results[net]['tp1']
            strict_stats['tp2'] += results[net]['tp2']
            strict_stats['tp3'] += results[net]['tp3']

    if strict_stats['total'] > 0:
        strict_win_rate = (strict_stats['tp1'] / strict_stats['total'] * 100)
        print(f"\n📊 RÉSEAUX STRICTS COMBINÉS (Seuils: $100K / $50K / 100txns):")
        print(f"   Réseaux: Solana, BSC, ETH, Base")
        print(f"   Alertes: {strict_stats['total']}")
        print(f"   TP1 Hit: {strict_stats['tp1']} ({strict_stats['tp1']/strict_stats['total']*100:.1f}%)")
        print(f"   TP2 Hit: {strict_stats['tp2']} ({strict_stats['tp2']/strict_stats['total']*100:.1f}%)")
        print(f"   TP3 Hit: {strict_stats['tp3']} ({strict_stats['tp3']/strict_stats['total']*100:.1f}%)")
        print(f"   Win Rate: {strict_win_rate:.1f}%")

        # Comparaison
        if 'arbitrum' in results:
            diff = arb['win_rate'] - strict_win_rate
            print(f"\n🔬 COMPARAISON:")
            print(f"   Arbitrum Win Rate: {arb['win_rate']:.1f}%")
            print(f"   Stricts Win Rate:  {strict_win_rate:.1f}%")
            print(f"   Différence:        {diff:+.1f}%")

            if diff > 0:
                print(f"   ✅ Arbitrum MEILLEUR de {abs(diff):.1f}%!")
            elif diff < -5:
                print(f"   ⚠️ Arbitrum MOINS BON de {abs(diff):.1f}% - Seuils trop bas?")
            else:
                print(f"   ✅ Performances SIMILAIRES - Seuils valides!")

    # 5. TOP/BOTTOM TOKENS PAR RÉSEAU
    print(f"\n" + "=" * 80)
    print("🏆 TOP 5 TOKENS PAR WIN RATE (min 2 alertes)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            network,
            token_name,
            COUNT(*) as total,
            SUM(CASE WHEN prix_max_atteint >= tp1_price THEN 1 ELSE 0 END) as tp1_hits
        FROM alerts
        WHERE tp1_price > 0 AND prix_max_atteint > 0
        GROUP BY network, token_name
        HAVING total >= 2
        ORDER BY (CAST(tp1_hits AS FLOAT) / total) DESC
        LIMIT 5
    """)

    for network, token, total, tp1_hits in cursor.fetchall():
        win_rate = (tp1_hits / total * 100) if total > 0 else 0
        print(f"   {network.upper():<10} {token:<30} {total:3} alertes, {tp1_hits:3} TP1 ({win_rate:.0f}%)")

    # 6. RECOMMANDATIONS
    print(f"\n" + "=" * 80)
    print("💡 RECOMMANDATIONS")
    print("=" * 80)

    if 'arbitrum' in results and strict_stats['total'] > 0:
        arb_wr = arb['win_rate']
        strict_wr = strict_win_rate

        if arb_wr >= strict_wr - 5:  # Dans les 5% de marge
            print(f"\n✅ SEUILS ARBITRUM VALIDÉS!")
            print(f"   Win rate {arb_wr:.1f}% comparable aux réseaux stricts ({strict_wr:.1f}%)")
            print(f"   Recommandation: GARDER les seuils Arbitrum actuels")
            print(f"   → $2K liquidity / $400 volume / 10 txns")
        elif arb_wr < strict_wr - 10:
            print(f"\n⚠️ SEUILS ARBITRUM À AJUSTER")
            print(f"   Win rate {arb_wr:.1f}% significativement inférieur ({strict_wr:.1f}%)")
            print(f"   Recommandation: AUGMENTER les seuils Arbitrum")
            print(f"   → Tester: $5K liquidity / $1K volume / 20 txns")
        else:
            print(f"\n✅ SEUILS ARBITRUM ACCEPTABLES")
            print(f"   Win rate {arb_wr:.1f}% légèrement inférieur ({strict_wr:.1f}%)")
            print(f"   Recommandation: MONITORER encore 1-2 jours puis décider")

    conn.close()

    print(f"\n" + "=" * 80)
    print(f"✅ Analyse terminée - {total_alerts:,} alertes analysées")
    print("=" * 80)

if __name__ == "__main__":
    analyze_network_performance()