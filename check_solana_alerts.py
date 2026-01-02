#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNOSTIC: Vérifier pourquoi pas d'alertes SOLANA
"""
import sys
import sqlite3
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = "alerts_history.db"

print("="*80)
print("🔍 DIAGNOSTIC ALERTES SOLANA")
print("="*80)
print()

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Vérifier total alertes SOLANA
    cursor.execute("""
        SELECT COUNT(*)
        FROM alerts
        WHERE network = 'solana'
    """)
    total_solana = cursor.fetchone()[0]
    print(f"📊 Total alertes SOLANA dans DB: {total_solana}")

    # 2. Alertes SOLANA par période
    periods = [
        ("Dernières 24h", 1),
        ("Derniers 7 jours", 7),
        ("Derniers 30 jours", 30)
    ]

    print("\n📅 ALERTES SOLANA PAR PÉRIODE:")
    for label, days in periods:
        cursor.execute("""
            SELECT COUNT(*)
            FROM alerts
            WHERE network = 'solana'
            AND created_at >= datetime('now', '-{} days')
        """.format(days))
        count = cursor.fetchone()[0]
        print(f"   {label}: {count} alertes")

    # 3. Dernière alerte SOLANA
    cursor.execute("""
        SELECT
            token_name,
            score,
            timestamp,
            liquidity,
            volume_24h
        FROM alerts
        WHERE network = 'solana'
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    last_alert = cursor.fetchone()

    if last_alert:
        print("\n🕐 DERNIÈRE ALERTE SOLANA:")
        print(f"   Token: {last_alert[0]}")
        print(f"   Score: {last_alert[1]}")
        print(f"   Date: {last_alert[2]}")
        print(f"   Liquidité: ${last_alert[3]:,.0f}" if last_alert[3] else "   Liquidité: N/A")
        print(f"   Volume 24h: ${last_alert[4]:,.0f}" if last_alert[4] else "   Volume 24h: N/A")

        # Calculer temps écoulé
        try:
            created_at = datetime.fromisoformat(last_alert[2].replace('Z', '+00:00'))
            now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
            elapsed = now - created_at
            hours_ago = elapsed.total_seconds() / 3600
            print(f"   Il y a: {hours_ago:.1f} heures")
        except:
            print(f"   Il y a: (date invalide)")
    else:
        print("\n❌ AUCUNE ALERTE SOLANA TROUVÉE DANS LA DB!")

    # 4. Top 10 alertes SOLANA récentes
    cursor.execute("""
        SELECT
            token_name,
            score,
            liquidity,
            volume_24h,
            timestamp
        FROM alerts
        WHERE network = 'solana'
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    recent = cursor.fetchall()

    if recent:
        print(f"\n📋 TOP 10 ALERTES SOLANA RÉCENTES:")
        for i, alert in enumerate(recent, 1):
            print(f"   {i:2}. {alert[0]:<15} | Score: {alert[1]:>3} | Liq: ${alert[2]:>10,.0f} | Vol: ${alert[3]:>10,.0f} | {alert[4]}")

    # 5. Statistiques SOLANA zone optimale
    print("\n🎯 ALERTES SOLANA ZONE OPTIMALE (Vol 1M-5M, Liq <200K):")
    cursor.execute("""
        SELECT COUNT(*)
        FROM alerts
        WHERE network = 'solana'
        AND volume_24h BETWEEN 1000000 AND 5000000
        AND liquidity < 200000
        AND timestamp >= datetime('now', '-7 days')
    """)
    optimal_count = cursor.fetchone()[0]
    print(f"   Derniers 7 jours: {optimal_count} alertes")

    # 6. Distribution par score
    print("\n⭐ DISTRIBUTION DES SCORES (7 derniers jours):")
    cursor.execute("""
        SELECT
            CASE
                WHEN score >= 95 THEN 'ULTRA_HIGH (95+)'
                WHEN score >= 85 THEN 'HIGH (85-94)'
                WHEN score >= 75 THEN 'MEDIUM (75-84)'
                WHEN score >= 60 THEN 'LOW (60-74)'
                ELSE 'VERY_LOW (<60)'
            END as tier,
            COUNT(*) as count
        FROM alerts
        WHERE network = 'solana'
        AND timestamp >= datetime('now', '-7 days')
        GROUP BY tier
        ORDER BY
            CASE
                WHEN score >= 95 THEN 1
                WHEN score >= 85 THEN 2
                WHEN score >= 75 THEN 3
                WHEN score >= 60 THEN 4
                ELSE 5
            END
    """)
    distribution = cursor.fetchall()

    for tier, count in distribution:
        print(f"   {tier}: {count} alertes")

    # 7. Vérifier si les données sont à jour
    cursor.execute("""
        SELECT
            MAX(timestamp) as latest,
            MIN(timestamp) as oldest
        FROM alerts
    """)
    dates = cursor.fetchone()
    print(f"\n📅 DATES DANS LA DB:")
    print(f"   Plus ancienne: {dates[1]}")
    print(f"   Plus récente: {dates[0]}")

    # 8. Comparer avec autres réseaux
    print("\n🌐 COMPARAISON AVEC AUTRES RÉSEAUX (7 derniers jours):")
    cursor.execute("""
        SELECT
            network,
            COUNT(*) as count
        FROM alerts
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY network
        ORDER BY count DESC
    """)
    by_network = cursor.fetchall()

    for network, count in by_network:
        print(f"   {network.upper():<10}: {count:>4} alertes")

    print("\n" + "="*80)
    print("💡 DIAGNOSTIC:")
    print("="*80)

    if total_solana == 0:
        print("❌ PROBLÈME: Aucune alerte SOLANA dans la base de données!")
        print("   → Vérifier que le scanner SOLANA fonctionne sur Railway")
        print("   → Vérifier les logs du serveur pour erreurs SOLANA")
        print("   → Vérifier la configuration des DEX SOLANA")
    elif last_alert and hours_ago > 24:
        print(f"⚠️  PROBLÈME: Dernière alerte SOLANA il y a {hours_ago:.1f}h")
        print("   → Le scanner semble ne plus fonctionner récemment")
        print("   → Vérifier les logs du serveur")
        print("   → Vérifier si les API SOLANA sont accessibles")
    elif optimal_count == 0:
        print("⚠️  PAS D'ALERTES ZONE OPTIMALE récemment")
        print("   → Le marché SOLANA est peut-être calme")
        print("   → Vérifier les critères de détection")
    else:
        print("✅ SOLANA semble fonctionner normalement")
        print(f"   → {optimal_count} alertes zone optimale (7j)")
        print(f"   → Dernière alerte il y a {hours_ago:.1f}h")

    conn.close()

except sqlite3.Error as e:
    print(f"❌ ERREUR DATABASE: {e}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()
