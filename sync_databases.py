"""
Synchronise la base de donnees locale avec Railway
Recupe les alertes recentes de Railway et les ajoute a la DB locale
"""

import sqlite3
import requests
import time
from datetime import datetime

DB_LOCAL = r"c:\Users\ludo_\Documents\projets\owner\bot-market\alerts_history.db"
API_RAILWAY = "https://bot-market-production.up.railway.app/api"

def fetch_all_railway_alerts(days=7):
    """Recupere toutes les alertes de Railway"""
    all_alerts = []
    offset = 0
    limit = 100

    print(f"Recuperation des alertes Railway (derniers {days} jours)...")

    while True:
        response = requests.get(f"{API_RAILWAY}/alerts", params={
            'limit': limit,
            'offset': offset,
            'days': days
        })
        data = response.json()
        alerts = data.get('alerts', [])

        if not alerts:
            break

        all_alerts.extend(alerts)
        offset += limit

        if offset % 500 == 0:
            print(f"  Progress: {offset} alertes recuperees...")

        if len(alerts) < limit:
            break

    print(f"  OK {len(all_alerts)} alertes recuperees de Railway")
    return all_alerts

def get_existing_ids(conn):
    """Recupere les IDs deja presents dans la DB locale"""
    cursor = conn.execute("SELECT id FROM alerts")
    existing = set(row[0] for row in cursor.fetchall())
    return existing

def sync_to_local_db(railway_alerts):
    """Synchronise les alertes Railway vers la DB locale"""

    conn = sqlite3.connect(DB_LOCAL)

    # Verifier les IDs existants
    existing_ids = get_existing_ids(conn)
    print(f"\nDB locale contient actuellement {len(existing_ids)} alertes")

    # Filtrer les nouvelles alertes
    new_alerts = [a for a in railway_alerts if a['id'] not in existing_ids]
    print(f"Nouvelles alertes a ajouter: {len(new_alerts)}")

    if not new_alerts:
        print("Aucune nouvelle alerte a synchroniser!")
        conn.close()
        return

    # Inserer les nouvelles alertes
    inserted = 0
    errors = 0

    for alert in new_alerts:
        try:
            # Mapper les champs Railway vers DB locale
            conn.execute("""
                INSERT INTO alerts (
                    id, timestamp, token_name, network,
                    price_at_alert, score, volume_24h, liquidity,
                    age_hours, created_at, velocite_pump, type_pump,
                    pool_address, tier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                alert['id'],
                alert['timestamp'],
                alert.get('token_name', ''),
                alert['network'],
                alert.get('price', 0),  # Railway utilise 'price' au lieu de 'price_at_alert'
                alert['score'],
                alert.get('volume_24h', 0),
                alert.get('liquidity', 0),
                alert.get('age_hours', 0),
                alert['created_at'],
                alert.get('velocite_pump', 0),
                alert.get('type_pump', ''),
                alert.get('pool_address', ''),
                alert.get('tier', '')
            ])
            inserted += 1

            if inserted % 100 == 0:
                print(f"  Progress: {inserted}/{len(new_alerts)} alertes inserees...")

        except Exception as e:
            errors += 1
            print(f"  [ERROR] Impossible d'inserer alerte {alert['id']}: {e}")

    conn.commit()
    conn.close()

    print(f"\nSynchronisation terminee:")
    print(f"  - Alertes inserees: {inserted}")
    print(f"  - Erreurs: {errors}")

def update_tiers_in_local_db():
    """Met a jour les tiers NULL dans la DB locale basee sur le score"""

    conn = sqlite3.connect(DB_LOCAL)

    # Compter les NULL
    cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE tier IS NULL OR tier = ''")
    null_count = cursor.fetchone()[0]

    print(f"\nMise a jour des tiers NULL: {null_count} alertes")

    if null_count == 0:
        print("Tous les tiers sont deja renseignes!")
        conn.close()
        return

    # Mettre a jour basee sur le score
    conn.execute("""
        UPDATE alerts
        SET tier = CASE
            WHEN score >= 98 THEN 'ULTRA_HIGH'
            WHEN score >= 95 THEN 'HIGH'
            WHEN score >= 90 THEN 'MEDIUM'
            WHEN score >= 80 THEN 'LOW'
            ELSE 'VERY_LOW'
        END
        WHERE tier IS NULL OR tier = ''
    """)

    conn.commit()

    # Verifier
    cursor = conn.execute("SELECT tier, COUNT(*) FROM alerts GROUP BY tier ORDER BY COUNT(*) DESC")
    tier_distribution = cursor.fetchall()

    print("\nDistribution des tiers apres mise a jour:")
    for tier, count in tier_distribution:
        print(f"  {tier}: {count}")

    conn.close()

def analyze_sync_results():
    """Analyse les resultats de la synchronisation"""

    conn = sqlite3.connect(DB_LOCAL)

    # Stats globales
    cursor = conn.execute("SELECT COUNT(*) FROM alerts")
    total = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE pool_address IS NOT NULL AND pool_address != ''")
    with_pool = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE tier IS NOT NULL AND tier != ''")
    with_tier = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE entry_price IS NOT NULL")
    with_tp_sl = cursor.fetchone()[0]

    print("\n" + "=" * 80)
    print("ETAT DE LA BASE DE DONNEES LOCALE APRES SYNCHRONISATION")
    print("=" * 80)
    print()
    print(f"Total alertes: {total}")
    print(f"Avec pool_address: {with_pool} ({with_pool/total*100:.1f}%)")
    print(f"Avec tier: {with_tier} ({with_tier/total*100:.1f}%)")
    print(f"Avec TP/SL: {with_tp_sl} ({with_tp_sl/total*100:.1f}%)")
    print()

    # Distribution par reseau
    cursor = conn.execute("SELECT network, COUNT(*) FROM alerts GROUP BY network ORDER BY COUNT(*) DESC")
    print("Distribution par reseau:")
    for net, count in cursor.fetchall():
        print(f"  {net}: {count}")

    print()

    # Distribution par tier
    cursor = conn.execute("SELECT tier, COUNT(*) FROM alerts WHERE tier IS NOT NULL GROUP BY tier ORDER BY COUNT(*) DESC")
    print("Distribution par tier:")
    for tier, count in cursor.fetchall():
        print(f"  {tier}: {count}")

    conn.close()
    print()
    print("=" * 80)

if __name__ == '__main__':
    print("=" * 80)
    print("SYNCHRONISATION DB LOCALE <-> DB RAILWAY")
    print("=" * 80)
    print()

    # Etape 1: Recuperer alertes Railway
    railway_alerts = fetch_all_railway_alerts(days=7)

    # Etape 2: Synchroniser vers DB locale
    print("\n[Etape 1/3] Synchronisation des alertes Railway -> DB locale")
    sync_to_local_db(railway_alerts)

    # Etape 3: Mettre a jour les tiers NULL
    print("\n[Etape 2/3] Mise a jour des tiers NULL")
    update_tiers_in_local_db()

    # Etape 4: Analyser
    print("\n[Etape 3/3] Analyse des resultats")
    analyze_sync_results()

    print("\nOK Synchronisation terminee!")
