"""
PRICE TRACKER STANDALONE - Independent service for tracking alert prices
Run this from a SEPARATE Railway service to avoid data loss during bot-market deployments.

Usage: python price_tracker_standalone.py
"""

import os
import sqlite3
import requests
import time
from datetime import datetime, timedelta

# Database path - shared volume with bot-market
DB_PATH = '/data/alerts_history.db'

GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2"

# Tracking interval in seconds (30 minutes)
TRACKING_INTERVAL = 1800

def get_db_connection():
    """Returns a SQLite connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_current_price(network, pool_address):
    """Fetch current price via GeckoTerminal API"""
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
    except Exception:
        return None

def get_alerts_to_track():
    """Get alerts to track (last 48h, not closed)"""
    conn = get_db_connection()
    cutoff_date = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id, network, token_address as pool_address, timestamp as created_at,
            entry_price, tp1_price, tp2_price, tp3_price, stop_loss_price,
            price_1h_after, price_2h_after, price_4h_after, price_24h_after,
            price_max_reached, price_min_reached,
            highest_tp_reached, sl_hit, is_closed
        FROM alerts
        WHERE token_address IS NOT NULL
          AND token_address != ''
          AND timestamp >= ?
          AND (is_closed IS NULL OR is_closed = 0)
    """, [cutoff_date])

    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alerts

def calculate_time_elapsed(created_at):
    """Calculate time elapsed since creation in hours"""
    try:
        if isinstance(created_at, str):
            alert_time = datetime.fromisoformat(created_at.replace('Z', '+00:00').replace(' ', 'T'))
        else:
            alert_time = created_at
        now = datetime.now()
        elapsed = (now - alert_time.replace(tzinfo=None)).total_seconds() / 3600
        return elapsed
    except Exception:
        return 0

def update_price_tracking(alert_id, hours_elapsed, current_price, alert):
    """Update price tracking columns"""
    conn = get_db_connection()
    updates = {}

    # Determine which column to update
    if 0.5 <= hours_elapsed < 1.5 and alert['price_1h_after'] is None:
        updates['price_1h_after'] = current_price
    elif 1.5 <= hours_elapsed < 3 and alert['price_2h_after'] is None:
        updates['price_2h_after'] = current_price
    elif 3 <= hours_elapsed < 6 and alert['price_4h_after'] is None:
        updates['price_4h_after'] = current_price
    elif hours_elapsed >= 23 and alert['price_24h_after'] is None:
        updates['price_24h_after'] = current_price

    # Always update max/min
    price_max = alert['price_max_reached'] or current_price
    price_min = alert['price_min_reached'] or current_price
    updates['price_max_reached'] = max(price_max, current_price)
    updates['price_min_reached'] = min(price_min, current_price)

    if updates:
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [alert_id]
        conn.execute(f"UPDATE alerts SET {set_clause} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return updates

def check_tp_sl_hit(alert, current_price):
    """Check if TP or SL hit and update"""
    entry = alert['entry_price']
    tp1, tp2, tp3 = alert['tp1_price'], alert['tp2_price'], alert['tp3_price']
    sl = alert['stop_loss_price']

    if not entry or entry == 0:
        return 'ONGOING'

    price_max = alert['price_max_reached'] or current_price
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check SL
    if sl and current_price <= sl and alert['sl_hit'] != 1:
        hours = calculate_time_elapsed(alert['created_at'])
        cursor.execute("""
            UPDATE alerts SET sl_hit = 1, time_to_sl = ?, final_outcome = 'LOSS_SL',
            final_gain_percent = ?, is_closed = 1, closed_at = ? WHERE id = ?
        """, [hours, ((current_price - entry) / entry * 100), datetime.now().isoformat(), alert['id']])
        conn.commit()
        conn.close()
        return 'SL'

    # Check TP3
    if tp3 and price_max >= tp3 and alert['highest_tp_reached'] != 'TP3':
        hours = calculate_time_elapsed(alert['created_at'])
        cursor.execute("""
            UPDATE alerts SET highest_tp_reached = 'TP3', time_to_tp3 = ?, final_outcome = 'WIN_TP3',
            final_gain_percent = ?, is_closed = 1, closed_at = ? WHERE id = ?
        """, [hours, ((tp3 - entry) / entry * 100), datetime.now().isoformat(), alert['id']])
        conn.commit()
        conn.close()
        return 'TP3'

    # Check TP2
    if tp2 and price_max >= tp2 and alert['highest_tp_reached'] not in ['TP2', 'TP3']:
        hours = calculate_time_elapsed(alert['created_at'])
        cursor.execute("UPDATE alerts SET highest_tp_reached = 'TP2', time_to_tp2 = ? WHERE id = ?",
                       [hours, alert['id']])
        conn.commit()
        conn.close()
        return 'TP2'

    # Check TP1
    if tp1 and price_max >= tp1 and alert['highest_tp_reached'] not in ['TP1', 'TP2', 'TP3']:
        hours = calculate_time_elapsed(alert['created_at'])
        cursor.execute("UPDATE alerts SET highest_tp_reached = 'TP1', time_to_tp1 = ? WHERE id = ?",
                       [hours, alert['id']])
        conn.commit()
        conn.close()
        return 'TP1'

    conn.close()
    return 'ONGOING'

def close_old_alerts():
    """Close alerts older than 48h"""
    conn = get_db_connection()
    cutoff = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alerts SET is_closed = 1, closed_at = ?,
            final_outcome = CASE
                WHEN highest_tp_reached = 'TP3' THEN 'WIN_TP3'
                WHEN highest_tp_reached = 'TP2' THEN 'WIN_TP2'
                WHEN highest_tp_reached = 'TP1' THEN 'WIN_TP1'
                WHEN sl_hit = 1 THEN 'LOSS_SL'
                ELSE 'TIMEOUT'
            END
        WHERE timestamp < ? AND (is_closed IS NULL OR is_closed = 0)
    """, [datetime.now().isoformat(), cutoff])

    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated

def run_tracking_cycle():
    """Run one complete tracking cycle"""
    print("=" * 70)
    print(f"PRICE TRACKER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"[WAIT] Database not found: {DB_PATH}")
        return

    print("[1/4] Getting alerts...")
    alerts = get_alerts_to_track()
    print(f"      {len(alerts)} alerts to track")

    if not alerts:
        return

    print("[2/4] Tracking prices...")
    tracked = 0
    results = {'TP1': 0, 'TP2': 0, 'TP3': 0, 'SL': 0, 'ONGOING': 0}

    for i, alert in enumerate(alerts, 1):
        if i % 50 == 0:
            print(f"      Progress: {i}/{len(alerts)}")

        price = fetch_current_price(alert['network'], alert['pool_address'])
        if price is None:
            continue

        hours = calculate_time_elapsed(alert['created_at'])
        update_price_tracking(alert['id'], hours, price, alert)
        outcome = check_tp_sl_hit(alert, price)
        results[outcome] += 1
        tracked += 1
        time.sleep(0.2)

    print(f"      Tracked: {tracked}")

    print("[3/4] Closing old alerts...")
    closed = close_old_alerts()
    print(f"      Closed: {closed}")

    print(f"[4/4] Results: TP3={results['TP3']} TP2={results['TP2']} TP1={results['TP1']} SL={results['SL']}")
    print("=" * 70)

def main():
    print("=" * 70)
    print("PRICE TRACKER STANDALONE SERVICE")
    print(f"Interval: {TRACKING_INTERVAL // 60} minutes")
    print("=" * 70)

    print("[START] First cycle in 60 seconds...")
    time.sleep(60)

    while True:
        try:
            run_tracking_cycle()
        except Exception as e:
            print(f"[ERROR] {e}")

        print(f"[NEXT] in {TRACKING_INTERVAL // 60} minutes...")
        time.sleep(TRACKING_INTERVAL)

if __name__ == '__main__':
    main()
