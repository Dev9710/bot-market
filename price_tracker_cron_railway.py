"""
PRICE TRACKER - Script CRON pour tracker les prix apres alerte (VERSION RAILWAY)
Execute toutes les heures pour mettre a jour price_1h/2h/4h/24h_after
et calculer les resultats finaux (TP/SL atteints)

VERSION: Railway (PostgreSQL)
USAGE:
  - Via Railway cron: Configure dans railway.toml
  - Ou lancer manuellement: python price_tracker_cron_railway.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import time
from datetime import datetime, timedelta

# Detecter l'environnement (Railway ou local)
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("[WARNING] DATABASE_URL non trouve - Mode local SQLite")
    import sqlite3
    DB_PATH = r"c:\Users\ludo_\Documents\projets\owner\bot-market\alerts_history.db"
    USE_POSTGRES = False
else:
    USE_POSTGRES = True

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

def get_db_connection():
    """Retourne une connexion a la DB (PostgreSQL ou SQLite)"""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def fetch_current_price(network, pool_address):
    """Fetch prix actuel via GeckoTerminal API"""
    network_map = {
        'eth': 'eth',
        'bsc': 'bsc',
        'base': 'base',
        'solana': 'solana',
        'polygon_pos': 'polygon-pos',
        'avax': 'avax',
        'arbitrum': 'arbitrum'
    }

    gt_network = network_map.get(network.lower(), network)
    url = f"{GECKOTERMINAL_API}/networks/{gt_network}/pools/{pool_address}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price_usd = float(data['data']['attributes']['base_token_price_usd'])
            return price_usd
        else:
            return None
    except Exception as e:
        print(f"  [ERROR] Failed to fetch price for {pool_address}: {e}")
        return None

def get_alerts_to_track():
    """
    Recupere les alertes a tracker:
    - Alertes non cloturees (is_closed = 0 ou NULL)
    - Avec pool_address
    - Creees dans les dernieres 48h
    """
    conn = get_db_connection()

    # Date limite: 48h
    cutoff_date = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id, network, pool_address, created_at,
            entry_price, tp1_price, tp2_price, tp3_price, stop_loss_price,
            price_1h_after, price_2h_after, price_4h_after, price_24h_after,
            price_max_reached, price_min_reached,
            highest_tp_reached, sl_hit, is_closed
        FROM alerts
        WHERE pool_address IS NOT NULL
          AND pool_address != ''
          AND created_at >= %s
          AND (is_closed IS NULL OR is_closed = 0)
    """ if USE_POSTGRES else """
        SELECT
            id, network, pool_address, created_at,
            entry_price, tp1_price, tp2_price, tp3_price, stop_loss_price,
            price_1h_after, price_2h_after, price_4h_after, price_24h_after,
            price_max_reached, price_min_reached,
            highest_tp_reached, sl_hit, is_closed
        FROM alerts
        WHERE pool_address IS NOT NULL
          AND pool_address != ''
          AND created_at >= ?
          AND (is_closed IS NULL OR is_closed = 0)
    """, [cutoff_date])

    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return alerts

def calculate_time_elapsed(created_at):
    """Calcule le temps ecoule depuis la creation en heures"""
    try:
        alert_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(alert_time.tzinfo) if alert_time.tzinfo else datetime.now()
        elapsed = (now - alert_time).total_seconds() / 3600  # heures
        return elapsed
    except:
        return 0

def update_price_tracking(alert_id, hours_elapsed, current_price, alert):
    """Met a jour les colonnes de tracking prix"""
    conn = get_db_connection()

    updates = {}

    # Determiner quelle colonne mettre a jour
    if 0.5 <= hours_elapsed < 1.5 and alert['price_1h_after'] is None:
        updates['price_1h_after'] = current_price
    elif 1.5 <= hours_elapsed < 3 and alert['price_2h_after'] is None:
        updates['price_2h_after'] = current_price
    elif 3 <= hours_elapsed < 6 and alert['price_4h_after'] is None:
        updates['price_4h_after'] = current_price
    elif hours_elapsed >= 23 and alert['price_24h_after'] is None:
        updates['price_24h_after'] = current_price

    # Mettre a jour prix max/min
    price_max = alert['price_max_reached'] or current_price
    price_min = alert['price_min_reached'] or current_price

    updates['price_max_reached'] = max(price_max, current_price)
    updates['price_min_reached'] = min(price_min, current_price)

    # Construire la requete SQL
    if updates:
        if USE_POSTGRES:
            set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [alert_id]
            cursor = conn.cursor()
            cursor.execute(f"UPDATE alerts SET {set_clause} WHERE id = %s", values)
        else:
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [alert_id]
            conn.execute(f"UPDATE alerts SET {set_clause} WHERE id = ?", values)

        conn.commit()

    conn.close()

    return updates

def check_tp_sl_hit(alert, current_price):
    """Verifie si TP ou SL atteint et met a jour"""
    entry = alert['entry_price']
    tp1 = alert['tp1_price']
    tp2 = alert['tp2_price']
    tp3 = alert['tp3_price']
    sl = alert['stop_loss_price']

    price_max = alert['price_max_reached'] or current_price

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifier SL
    if current_price <= sl and alert['sl_hit'] != 1:
        hours_elapsed = calculate_time_elapsed(alert['created_at'])
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE alerts
                SET sl_hit = 1,
                    time_to_sl = %s,
                    final_outcome = 'LOSS_SL',
                    final_gain_percent = %s,
                    is_closed = 1,
                    closed_at = %s
                WHERE id = %s
            """, [hours_elapsed, ((current_price - entry) / entry * 100), datetime.now().isoformat(), alert['id']])
        else:
            cursor.execute("""
                UPDATE alerts
                SET sl_hit = 1,
                    time_to_sl = ?,
                    final_outcome = 'LOSS_SL',
                    final_gain_percent = ?,
                    is_closed = 1,
                    closed_at = ?
                WHERE id = ?
            """, [hours_elapsed, ((current_price - entry) / entry * 100), datetime.now().isoformat(), alert['id']])
        conn.commit()
        conn.close()
        return 'SL'

    # Verifier TP3
    if price_max >= tp3 and alert['highest_tp_reached'] != 'TP3':
        hours_elapsed = calculate_time_elapsed(alert['created_at'])
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE alerts
                SET highest_tp_reached = 'TP3',
                    time_to_tp3 = %s,
                    final_outcome = 'WIN_TP3',
                    final_gain_percent = %s,
                    is_closed = 1,
                    closed_at = %s
                WHERE id = %s
            """, [hours_elapsed, ((tp3 - entry) / entry * 100), datetime.now().isoformat(), alert['id']])
        else:
            cursor.execute("""
                UPDATE alerts
                SET highest_tp_reached = 'TP3',
                    time_to_tp3 = ?,
                    final_outcome = 'WIN_TP3',
                    final_gain_percent = ?,
                    is_closed = 1,
                    closed_at = ?
                WHERE id = ?
            """, [hours_elapsed, ((tp3 - entry) / entry * 100), datetime.now().isoformat(), alert['id']])
        conn.commit()
        conn.close()
        return 'TP3'

    # Verifier TP2
    elif price_max >= tp2 and alert['highest_tp_reached'] not in ['TP2', 'TP3']:
        hours_elapsed = calculate_time_elapsed(alert['created_at'])
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE alerts
                SET highest_tp_reached = 'TP2',
                    time_to_tp2 = %s
                WHERE id = %s
            """, [hours_elapsed, alert['id']])
        else:
            cursor.execute("""
                UPDATE alerts
                SET highest_tp_reached = 'TP2',
                    time_to_tp2 = ?
                WHERE id = ?
            """, [hours_elapsed, alert['id']])
        conn.commit()
        conn.close()
        return 'TP2'

    # Verifier TP1
    elif price_max >= tp1 and alert['highest_tp_reached'] not in ['TP1', 'TP2', 'TP3']:
        hours_elapsed = calculate_time_elapsed(alert['created_at'])
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE alerts
                SET highest_tp_reached = 'TP1',
                    time_to_tp1 = %s
                WHERE id = %s
            """, [hours_elapsed, alert['id']])
        else:
            cursor.execute("""
                UPDATE alerts
                SET highest_tp_reached = 'TP1',
                    time_to_tp1 = ?
                WHERE id = ?
            """, [hours_elapsed, alert['id']])
        conn.commit()
        conn.close()
        return 'TP1'

    conn.close()
    return 'ONGOING'

def close_old_alerts():
    """Cloture les alertes de plus de 48h qui sont encore ONGOING"""
    conn = get_db_connection()

    cutoff_date = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    if USE_POSTGRES:
        cursor.execute("""
            UPDATE alerts
            SET is_closed = 1,
                closed_at = %s,
                final_outcome = CASE
                    WHEN highest_tp_reached = 'TP3' THEN 'WIN_TP3'
                    WHEN highest_tp_reached = 'TP2' THEN 'WIN_TP2'
                    WHEN highest_tp_reached = 'TP1' THEN 'WIN_TP1'
                    WHEN sl_hit = 1 THEN 'LOSS_SL'
                    ELSE 'TIMEOUT'
                END,
                final_gain_percent = CASE
                    WHEN highest_tp_reached = 'TP3' THEN tp3_percent
                    WHEN highest_tp_reached = 'TP2' THEN tp2_percent
                    WHEN highest_tp_reached = 'TP1' THEN tp1_percent
                    WHEN sl_hit = 1 THEN stop_loss_percent
                    ELSE ((price_24h_after - entry_price) / entry_price * 100)
                END
            WHERE created_at < %s
              AND (is_closed IS NULL OR is_closed = 0)
        """, [datetime.now().isoformat(), cutoff_date])
    else:
        cursor.execute("""
            UPDATE alerts
            SET is_closed = 1,
                closed_at = ?,
                final_outcome = CASE
                    WHEN highest_tp_reached = 'TP3' THEN 'WIN_TP3'
                    WHEN highest_tp_reached = 'TP2' THEN 'WIN_TP2'
                    WHEN highest_tp_reached = 'TP1' THEN 'WIN_TP1'
                    WHEN sl_hit = 1 THEN 'LOSS_SL'
                    ELSE 'TIMEOUT'
                END,
                final_gain_percent = CASE
                    WHEN highest_tp_reached = 'TP3' THEN tp3_percent
                    WHEN highest_tp_reached = 'TP2' THEN tp2_percent
                    WHEN highest_tp_reached = 'TP1' THEN tp1_percent
                    WHEN sl_hit = 1 THEN stop_loss_percent
                    ELSE ((price_24h_after - entry_price) / entry_price * 100)
                END
            WHERE created_at < ?
              AND (is_closed IS NULL OR is_closed = 0)
        """, [datetime.now().isoformat(), cutoff_date])

    updated = cursor.rowcount
    conn.commit()
    conn.close()

    return updated

if __name__ == '__main__':
    print("=" * 80)
    print(f"PRICE TRACKER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Environment: {'PostgreSQL (Railway)' if USE_POSTGRES else 'SQLite (Local)'}")
    print("=" * 80)
    print()

    # 1. Recuperer alertes a tracker
    print("[1/4] Recuperation des alertes a tracker...")
    alerts = get_alerts_to_track()
    print(f"      OK {len(alerts)} alertes a tracker")
    print()

    if not alerts:
        print("Aucune alerte a tracker - Fin du script")
        exit(0)

    # 2. Tracker les prix
    print("[2/4] Tracking des prix...")
    tracked = 0
    tp_hit = {'TP1': 0, 'TP2': 0, 'TP3': 0, 'SL': 0, 'ONGOING': 0}

    for i, alert in enumerate(alerts, 1):
        if i % 10 == 0:
            print(f"      Progress: {i}/{len(alerts)}")
            time.sleep(2)  # Rate limit

        # Fetch prix actuel
        current_price = fetch_current_price(alert['network'], alert['pool_address'])

        if current_price is None:
            continue

        # Calculer temps ecoule
        hours_elapsed = calculate_time_elapsed(alert['created_at'])

        # Mettre a jour tracking prix
        updates = update_price_tracking(alert['id'], hours_elapsed, current_price, alert)

        # Verifier TP/SL
        outcome = check_tp_sl_hit(alert, current_price)
        tp_hit[outcome] += 1

        tracked += 1

        # Rate limit: 5 req/s
        time.sleep(0.2)

    print(f"      OK {tracked} alertes trackees")
    print()

    # 3. Cloture alertes anciennes
    print("[3/4] Cloture des alertes anciennes (>48h)...")
    closed = close_old_alerts()
    print(f"      OK {closed} alertes cloturees")
    print()

    # 4. Resume
    print("[4/4] Resume:")
    print(f"      TP3 atteint: {tp_hit['TP3']}")
    print(f"      TP2 atteint: {tp_hit['TP2']}")
    print(f"      TP1 atteint: {tp_hit['TP1']}")
    print(f"      SL atteint:  {tp_hit['SL']}")
    print(f"      En cours:    {tp_hit['ONGOING']}")
    print()

    print("=" * 80)
    print("TRACKING TERMINE")
    print("=" * 80)
