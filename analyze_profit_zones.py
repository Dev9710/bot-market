#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse des ZONES DE PROFIT SYSTÉMATIQUES
Identifie les patterns de performance à travers l'évolution des tokens
"""
import sqlite3
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Find the database
DB_PATH = os.getenv("DB_PATH")
if not DB_PATH:
    if os.path.exists("alerts_tracker.db"):
        DB_PATH = "alerts_tracker.db"
    elif os.path.exists("alerts_history.db"):
        DB_PATH = "alerts_history.db"
    else:
        print("❌ ERROR: Database not found!")
        exit(1)

print(f"📊 ANALYSE DES ZONES DE PROFIT SYSTÉMATIQUES\n")
print(f"Database: {DB_PATH}\n")

def analyze_price_evolution_patterns(conn):
    """
    Analyse l'évolution du prix entre alertes pour identifier les zones de profit
    """

    query = """
        WITH token_evolution AS (
            SELECT
                token_address,
                network,
                token_name,
                created_at,
                entry_price,
                liquidity,
                volume_24h,
                score,
                age_hours,
                ROW_NUMBER() OVER (PARTITION BY token_address ORDER BY created_at) as alert_num,
                LAG(entry_price) OVER (PARTITION BY token_address ORDER BY created_at) as prev_price,
                LAG(created_at) OVER (PARTITION BY token_address ORDER BY created_at) as prev_time,
                LAG(liquidity) OVER (PARTITION BY token_address ORDER BY created_at) as prev_liquidity,
                LAG(volume_24h) OVER (PARTITION BY token_address ORDER BY created_at) as prev_volume
            FROM alerts
            WHERE entry_price IS NOT NULL
              AND entry_price > 0
        )
        SELECT
            token_address,
            network,
            token_name,
            alert_num,
            created_at,
            prev_time,
            entry_price,
            prev_price,
            liquidity,
            prev_liquidity,
            volume_24h,
            prev_volume,
            score,
            age_hours,
            CASE
                WHEN prev_price > 0 THEN ((entry_price - prev_price) / prev_price * 100)
                ELSE NULL
            END as price_change_pct,
            CASE
                WHEN prev_time IS NOT NULL THEN
                    (julianday(created_at) - julianday(prev_time)) * 24
                ELSE NULL
            END as time_between_hours
        FROM token_evolution
        WHERE prev_price IS NOT NULL
        ORDER BY ABS(price_change_pct) DESC
        LIMIT 500
    """

    cursor = conn.execute(query)
    return cursor.fetchall()

def analyze_volume_performance_zones(conn):
    """
    Identifie les zones de volume qui performent systématiquement
    """

    query = """
        WITH first_alerts AS (
            SELECT
                token_address,
                network,
                MIN(created_at) as first_alert_time,
                COUNT(*) as total_alerts
            FROM alerts
            GROUP BY token_address
            HAVING COUNT(*) >= 2
        ),
        performance_data AS (
            SELECT
                a.token_address,
                a.network,
                a.token_name,
                fa.total_alerts,
                a.volume_24h,
                a.volume_6h,
                a.volume_1h,
                a.liquidity,
                a.score,
                a.age_hours,
                a.volume_acceleration_1h_vs_6h,
                CASE
                    WHEN a.volume_24h < 100000 THEN '<100K'
                    WHEN a.volume_24h < 500000 THEN '100K-500K'
                    WHEN a.volume_24h < 1000000 THEN '500K-1M'
                    WHEN a.volume_24h < 5000000 THEN '1M-5M'
                    ELSE '>5M'
                END as volume_zone,
                CASE
                    WHEN a.liquidity < 100000 THEN '<100K'
                    WHEN a.liquidity < 500000 THEN '100K-500K'
                    WHEN a.liquidity < 1000000 THEN '500K-1M'
                    WHEN a.liquidity < 2000000 THEN '1M-2M'
                    ELSE '>2M'
                END as liquidity_zone,
                CASE
                    WHEN a.age_hours * 60 < 5 THEN '<5min'
                    WHEN a.age_hours * 60 < 30 THEN '5-30min'
                    WHEN a.age_hours < 1 THEN '30min-1h'
                    WHEN a.age_hours < 6 THEN '1-6h'
                    WHEN a.age_hours < 24 THEN '6-24h'
                    ELSE '>24h'
                END as age_zone
            FROM alerts a
            INNER JOIN first_alerts fa ON a.token_address = fa.token_address
            WHERE a.created_at = fa.first_alert_time
        )
        SELECT
            network,
            volume_zone,
            liquidity_zone,
            age_zone,
            COUNT(*) as count,
            AVG(total_alerts) as avg_alerts,
            AVG(score) as avg_score,
            AVG(volume_acceleration_1h_vs_6h) as avg_accel
        FROM performance_data
        GROUP BY network, volume_zone, liquidity_zone, age_zone
        HAVING COUNT(*) >= 3
        ORDER BY avg_alerts DESC, count DESC
    """

    cursor = conn.execute(query)
    return cursor.fetchall()

def analyze_timeframe_performance(conn):
    """
    Analyse la performance par timeframe (combien de temps avant nouvelle alerte)
    """

    query = """
        WITH alert_sequences AS (
            SELECT
                token_address,
                network,
                token_name,
                created_at,
                score,
                liquidity,
                volume_24h,
                LAG(created_at) OVER (PARTITION BY token_address ORDER BY created_at) as prev_time,
                LEAD(created_at) OVER (PARTITION BY token_address ORDER BY created_at) as next_time,
                ROW_NUMBER() OVER (PARTITION BY token_address ORDER BY created_at) as alert_num
            FROM alerts
        ),
        timeframes AS (
            SELECT
                network,
                token_name,
                alert_num,
                score,
                liquidity,
                volume_24h,
                CASE
                    WHEN next_time IS NOT NULL THEN
                        (julianday(next_time) - julianday(created_at)) * 24
                    ELSE NULL
                END as hours_to_next_alert,
                CASE
                    WHEN next_time IS NOT NULL THEN
                        CASE
                            WHEN (julianday(next_time) - julianday(created_at)) * 60 < 15 THEN '<15min'
                            WHEN (julianday(next_time) - julianday(created_at)) * 60 < 60 THEN '15min-1h'
                            WHEN (julianday(next_time) - julianday(created_at)) < 1 THEN '1-24h'
                            WHEN (julianday(next_time) - julianday(created_at)) < 3 THEN '1-3 jours'
                            ELSE '>3 jours'
                        END
                    ELSE NULL
                END as timeframe_to_next
            FROM alert_sequences
            WHERE prev_time IS NOT NULL
        )
        SELECT
            network,
            timeframe_to_next,
            COUNT(*) as occurrences,
            AVG(score) as avg_score,
            AVG(liquidity) as avg_liquidity,
            AVG(volume_24h) as avg_volume
        FROM timeframes
        WHERE timeframe_to_next IS NOT NULL
        GROUP BY network, timeframe_to_next
        ORDER BY network, occurrences DESC
    """

    cursor = conn.execute(query)
    return cursor.fetchall()

def analyze_score_progression_zones(conn):
    """
    Identifie les patterns de progression de score qui indiquent un profit
    """

    query = """
        WITH score_evolution AS (
            SELECT
                token_address,
                network,
                token_name,
                created_at,
                score,
                liquidity,
                volume_24h,
                LAG(score) OVER (PARTITION BY token_address ORDER BY created_at) as prev_score,
                LEAD(score) OVER (PARTITION BY token_address ORDER BY created_at) as next_score,
                ROW_NUMBER() OVER (PARTITION BY token_address ORDER BY created_at) as alert_num
            FROM alerts
        )
        SELECT
            network,
            CASE
                WHEN prev_score IS NOT NULL AND score > prev_score THEN 'Score en hausse'
                WHEN prev_score IS NOT NULL AND score < prev_score THEN 'Score en baisse'
                WHEN prev_score IS NOT NULL AND score = prev_score THEN 'Score stable'
                ELSE 'Première alerte'
            END as score_trend,
            COUNT(*) as count,
            COUNT(DISTINCT token_address) as unique_tokens,
            AVG(score) as avg_score,
            AVG(liquidity) as avg_liquidity,
            AVG(volume_24h) as avg_volume,
            COUNT(next_score) * 100.0 / COUNT(*) as pct_continue_alerting
        FROM score_evolution
        GROUP BY network, score_trend
        ORDER BY network, count DESC
    """

    cursor = conn.execute(query)
    return cursor.fetchall()

def print_price_evolution_analysis(results):
    """Affiche l'analyse d'évolution des prix"""

    print(f"\n{'='*100}")
    print("💰 ANALYSE 1: ÉVOLUTION DES PRIX ENTRE ALERTES")
    print(f"{'='*100}\n")

    # Group by network and profit zones
    profit_zones = defaultdict(lambda: {'gains': [], 'pertes': [], 'tokens': set()})

    for row in results:
        network = row['network']
        price_change = row['price_change_pct']
        time_hours = row['time_between_hours']
        token = row['token_name'].split('/')[0] if row['token_name'] else 'Unknown'

        if price_change > 0:
            profit_zones[network]['gains'].append({
                'pct': price_change,
                'hours': time_hours,
                'token': token,
                'volume': row['volume_24h'],
                'liquidity': row['liquidity']
            })
        else:
            profit_zones[network]['pertes'].append({
                'pct': abs(price_change),
                'hours': time_hours,
                'token': token
            })

        profit_zones[network]['tokens'].add(row['token_address'])

    for network, data in sorted(profit_zones.items()):
        print(f"\n🌐 RÉSEAU: {network.upper()}")
        print(f"   Tokens analysés: {len(data['tokens'])}")

        if data['gains']:
            gains = sorted(data['gains'], key=lambda x: x['pct'], reverse=True)[:10]
            print(f"\n   📈 TOP 10 GAINS ENTRE ALERTES:")
            for i, gain in enumerate(gains, 1):
                print(f"      {i:2}. {gain['token'][:20]:20} | +{gain['pct']:>6.1f}% en {gain['hours']:>5.1f}h | Vol: ${gain['volume']/1000:>6.0f}K | Liq: ${gain['liquidity']/1000:>6.0f}K")

            # Stats
            avg_gain = sum(g['pct'] for g in data['gains']) / len(data['gains'])
            avg_time = sum(g['hours'] for g in data['gains']) / len(data['gains'])
            print(f"\n   📊 STATS GAINS:")
            print(f"      • Gain moyen: +{avg_gain:.1f}%")
            print(f"      • Temps moyen entre alertes: {avg_time:.1f}h")
            print(f"      • Total occurrences: {len(data['gains'])}")

def print_volume_zones_analysis(results):
    """Affiche l'analyse des zones de volume performantes"""

    print(f"\n\n{'='*100}")
    print("📊 ANALYSE 2: ZONES DE VOLUME QUI PERFORMENT")
    print(f"{'='*100}\n")

    # Group by network
    by_network = defaultdict(list)
    for row in results:
        by_network[row['network']].append(row)

    for network, rows in sorted(by_network.items()):
        print(f"\n🌐 {network.upper()}")
        print(f"\n   {'Volume':<12} {'Liquidité':<12} {'Âge':<12} {'Count':>6} {'Avg Alerts':>11} {'Avg Score':>10} {'Accel':>8}")
        print(f"   {'-'*85}")

        # Sort by avg_alerts (performance indicator)
        sorted_rows = sorted(rows, key=lambda x: x['avg_alerts'], reverse=True)[:15]

        for row in sorted_rows:
            print(f"   {row['volume_zone']:<12} {row['liquidity_zone']:<12} {row['age_zone']:<12} "
                  f"{row['count']:>6} {row['avg_alerts']:>11.1f} {row['avg_score']:>10.1f} {row['avg_accel'] or 0:>7.1f}x")

def print_timeframe_analysis(results):
    """Affiche l'analyse des timeframes de performance"""

    print(f"\n\n{'='*100}")
    print("⏱️  ANALYSE 3: TIMEFRAMES DE PERFORMANCE (Temps avant nouvelle alerte = performance)")
    print(f"{'='*100}\n")

    by_network = defaultdict(list)
    for row in results:
        by_network[row['network']].append(row)

    for network, rows in sorted(by_network.items()):
        print(f"\n🌐 {network.upper()}")
        print(f"\n   {'Timeframe':<15} {'Occurrences':>12} {'Avg Score':>10} {'Avg Liquidity':>15} {'Avg Volume':>15}")
        print(f"   {'-'*75}")

        for row in sorted(rows, key=lambda x: x['occurrences'], reverse=True):
            print(f"   {row['timeframe_to_next']:<15} {row['occurrences']:>12} "
                  f"{row['avg_score']:>10.1f} ${row['avg_liquidity']/1000:>13.0f}K ${row['avg_volume']/1000:>13.0f}K")

def print_score_progression_analysis(results):
    """Affiche l'analyse de progression du score"""

    print(f"\n\n{'='*100}")
    print("📈 ANALYSE 4: PROGRESSION DU SCORE = INDICATEUR DE PERFORMANCE")
    print(f"{'='*100}\n")

    by_network = defaultdict(list)
    for row in results:
        by_network[row['network']].append(row)

    for network, rows in sorted(by_network.items()):
        print(f"\n🌐 {network.upper()}")
        print(f"\n   {'Trend Score':<20} {'Count':>8} {'Tokens':>8} {'% Continue':>12} {'Avg Score':>10} {'Avg Liq':>12}")
        print(f"   {'-'*85}")

        for row in rows:
            print(f"   {row['score_trend']:<20} {row['count']:>8} {row['unique_tokens']:>8} "
                  f"{row['pct_continue_alerting']:>11.1f}% {row['avg_score']:>10.1f} ${row['avg_liquidity']/1000:>10.0f}K")

def generate_trading_insights(conn):
    """Génère des insights actionnables pour le trading"""

    print(f"\n\n{'='*100}")
    print("🎯 INSIGHTS ACTIONNABLES POUR LE TRADING")
    print(f"{'='*100}\n")

    # Best volume/liquidity combinations
    query_best_combos = """
        WITH first_alerts AS (
            SELECT
                token_address,
                network,
                MIN(created_at) as first_time,
                COUNT(*) as alert_count
            FROM alerts
            GROUP BY token_address
            HAVING COUNT(*) >= 3
        )
        SELECT
            a.network,
            CASE
                WHEN a.volume_24h < 200000 THEN '<200K'
                WHEN a.volume_24h < 1000000 THEN '200K-1M'
                WHEN a.volume_24h < 5000000 THEN '1M-5M'
                ELSE '>5M'
            END as vol_range,
            CASE
                WHEN a.liquidity < 200000 THEN '<200K'
                WHEN a.liquidity < 1000000 THEN '200K-1M'
                WHEN a.liquidity < 2000000 THEN '1M-2M'
                ELSE '>2M'
            END as liq_range,
            COUNT(DISTINCT a.token_address) as tokens,
            AVG(fa.alert_count) as avg_performance,
            AVG(a.score) as avg_entry_score
        FROM alerts a
        INNER JOIN first_alerts fa ON a.token_address = fa.token_address AND a.created_at = fa.first_time
        GROUP BY a.network, vol_range, liq_range
        HAVING COUNT(DISTINCT a.token_address) >= 3
        ORDER BY avg_performance DESC
        LIMIT 20
    """

    cursor = conn.execute(query_best_combos)
    combos = cursor.fetchall()

    print("💡 MEILLEURS PROFILS D'ENTRY (Volume + Liquidité):\n")
    print(f"   {'Réseau':<10} {'Volume':<12} {'Liquidité':<12} {'Tokens':>8} {'Perf Moy':>10} {'Score':>8}")
    print(f"   {'-'*75}")

    for combo in combos:
        print(f"   {combo['network']:<10} {combo['vol_range']:<12} {combo['liq_range']:<12} "
              f"{combo['tokens']:>8} {combo['avg_performance']:>9.1f}x {combo['avg_entry_score']:>8.1f}")

    print(f"\n\n🎲 RÈGLES DE TRADING RECOMMANDÉES:\n")

    # Find best performers
    best = combos[0] if combos else None
    if best:
        print(f"   ✅ ZONE OPTIMALE IDENTIFIÉE:")
        print(f"      • Réseau: {best['network'].upper()}")
        print(f"      • Volume: {best['vol_range']}")
        print(f"      • Liquidité: {best['liq_range']}")
        print(f"      • Performance moyenne: {best['avg_performance']:.1f} alertes/token")
        print(f"      • Score entry moyen: {best['avg_entry_score']:.1f}")

    # Score trend rules
    query_score_rules = """
        WITH score_changes AS (
            SELECT
                token_address,
                network,
                score,
                LAG(score) OVER (PARTITION BY token_address ORDER BY created_at) as prev_score,
                LEAD(created_at) OVER (PARTITION BY token_address ORDER BY created_at) as has_next
            FROM alerts
        )
        SELECT
            network,
            CASE
                WHEN score > prev_score THEN 'hausse'
                WHEN score < prev_score THEN 'baisse'
                ELSE 'stable'
            END as trend,
            COUNT(*) as total,
            SUM(CASE WHEN has_next IS NOT NULL THEN 1 ELSE 0 END) as continued,
            SUM(CASE WHEN has_next IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as continue_rate
        FROM score_changes
        WHERE prev_score IS NOT NULL
        GROUP BY network, trend
        ORDER BY continue_rate DESC
    """

    cursor = conn.execute(query_score_rules)
    score_trends = cursor.fetchall()

    print(f"\n   📊 SIGNAUX DE CONTINUATION:\n")
    for trend in score_trends[:5]:
        if trend['continue_rate'] > 60:
            print(f"      ✓ {trend['network'].upper()}: Score en {trend['trend']} → {trend['continue_rate']:.0f}% chance de nouvelle alerte")

def main():
    """Main analysis"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. Price Evolution Analysis
    print("1️⃣  Analyse de l'évolution des prix...")
    price_results = analyze_price_evolution_patterns(conn)
    if price_results:
        print_price_evolution_analysis(price_results)

    # 2. Volume Zones Analysis
    print("\n2️⃣  Analyse des zones de volume...")
    volume_results = analyze_volume_performance_zones(conn)
    if volume_results:
        print_volume_zones_analysis(volume_results)

    # 3. Timeframe Analysis
    print("\n3️⃣  Analyse des timeframes...")
    timeframe_results = analyze_timeframe_performance(conn)
    if timeframe_results:
        print_timeframe_analysis(timeframe_results)

    # 4. Score Progression Analysis
    print("\n4️⃣  Analyse de la progression du score...")
    score_results = analyze_score_progression_zones(conn)
    if score_results:
        print_score_progression_analysis(score_results)

    # 5. Generate Trading Insights
    print("\n5️⃣  Génération des insights...")
    generate_trading_insights(conn)

    conn.close()

    print("\n\n✅ Analyse terminée!\n")

if __name__ == "__main__":
    main()
