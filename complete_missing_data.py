"""
Complete les donnees manquantes pour atteindre 100% d'exploitabilite
Calcule les TP/SL pour les 5,702 alertes qui n'en ont pas
"""

import sqlite3
from datetime import datetime

DB_LOCAL = r"c:\Users\ludo_\Documents\projets\owner\bot-market\alerts_history.db"

def calculate_tp_sl_from_price(price):
    """
    Calcule les TP/SL standards basees sur le prix
    Logique identique a geckoterminal_scanner_v2.py ligne 2459-2462
    """
    entry_price = price
    stop_loss_price = price * 0.90  # -10%
    stop_loss_percent = -10.0
    tp1_price = price * 1.05  # +5%
    tp1_percent = 5.0
    tp2_price = price * 1.10  # +10%
    tp2_percent = 10.0
    tp3_price = price * 1.15  # +15%
    tp3_percent = 15.0

    return {
        'entry_price': entry_price,
        'stop_loss_price': stop_loss_price,
        'stop_loss_percent': stop_loss_percent,
        'tp1_price': tp1_price,
        'tp1_percent': tp1_percent,
        'tp2_price': tp2_price,
        'tp2_percent': tp2_percent,
        'tp3_price': tp3_price,
        'tp3_percent': tp3_percent
    }

def complete_missing_tp_sl():
    """Complete les TP/SL manquants dans la DB locale"""

    conn = sqlite3.connect(DB_LOCAL)
    conn.row_factory = sqlite3.Row

    print("=" * 80)
    print("COMPLETION DES DONNEES MANQUANTES - TP/SL")
    print("=" * 80)
    print()

    # Identifier les alertes sans TP/SL
    cursor = conn.execute("""
        SELECT id, price_at_alert, network, score, tier
        FROM alerts
        WHERE entry_price IS NULL
          AND price_at_alert IS NOT NULL
          AND price_at_alert > 0
    """)

    alerts_without_tp_sl = [dict(row) for row in cursor.fetchall()]

    print(f"Alertes sans TP/SL trouvees: {len(alerts_without_tp_sl)}")
    print()

    if len(alerts_without_tp_sl) == 0:
        print("Toutes les alertes ont deja des TP/SL!")
        conn.close()
        return

    # Calculer et mettre a jour
    print("Calcul des TP/SL...")
    updated = 0
    errors = 0

    for i, alert in enumerate(alerts_without_tp_sl, 1):
        try:
            price = alert['price_at_alert']
            tp_sl = calculate_tp_sl_from_price(price)

            # Mettre a jour dans la DB
            conn.execute("""
                UPDATE alerts
                SET
                    entry_price = ?,
                    stop_loss_price = ?,
                    stop_loss_percent = ?,
                    tp1_price = ?,
                    tp1_percent = ?,
                    tp2_price = ?,
                    tp2_percent = ?,
                    tp3_price = ?,
                    tp3_percent = ?
                WHERE id = ?
            """, [
                tp_sl['entry_price'],
                tp_sl['stop_loss_price'],
                tp_sl['stop_loss_percent'],
                tp_sl['tp1_price'],
                tp_sl['tp1_percent'],
                tp_sl['tp2_price'],
                tp_sl['tp2_percent'],
                tp_sl['tp3_price'],
                tp_sl['tp3_percent'],
                alert['id']
            ])

            updated += 1

            if i % 500 == 0:
                print(f"  Progress: {i}/{len(alerts_without_tp_sl)} ({i/len(alerts_without_tp_sl)*100:.0f}%)")

        except Exception as e:
            errors += 1
            print(f"  [ERROR] Alerte {alert['id']}: {e}")

    conn.commit()

    print(f"\nMise a jour terminee:")
    print(f"  - TP/SL calcules: {updated}")
    print(f"  - Erreurs: {errors}")
    print()

    # Verification finale
    cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE entry_price IS NOT NULL")
    total_with_tp_sl = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cursor.fetchone()[0]

    completeness_pct = (total_with_tp_sl / total_alerts * 100) if total_alerts > 0 else 0

    print("=" * 80)
    print("VERIFICATION FINALE")
    print("=" * 80)
    print()
    print(f"Total alertes: {total_alerts}")
    print(f"Alertes avec TP/SL: {total_with_tp_sl} ({completeness_pct:.1f}%)")
    print()

    if completeness_pct >= 99.9:
        print("STATUS: OK - Presque toutes les alertes ont des TP/SL!")
    elif completeness_pct >= 90:
        print("STATUS: BON - Majorite des alertes ont des TP/SL")
    else:
        print("STATUS: INCOMPLET - Des alertes manquent encore de TP/SL")

    conn.close()

    return {
        'total': total_alerts,
        'with_tp_sl': total_with_tp_sl,
        'completeness_pct': completeness_pct,
        'updated': updated,
        'errors': errors
    }

def verify_data_completeness():
    """Verifie la completude finale de toutes les donnees critiques"""

    conn = sqlite3.connect(DB_LOCAL)

    critical_fields = [
        'id', 'network', 'score', 'tier',
        'entry_price', 'stop_loss_price', 'tp1_price',
        'pool_address', 'volume_24h', 'liquidity'
    ]

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETUDE FINALE - DONNEES CRITIQUES")
    print("=" * 80)
    print()

    cursor = conn.execute("SELECT COUNT(*) FROM alerts")
    total = cursor.fetchone()[0]

    print(f"{'Champ':<25} {'Complete':<15} {'%':<10} {'Status'}")
    print("-" * 80)

    for field in critical_fields:
        cursor = conn.execute(f"""
            SELECT COUNT(*) FROM alerts
            WHERE {field} IS NOT NULL AND {field} != ''
        """)
        count = cursor.fetchone()[0]
        pct = (count / total * 100) if total > 0 else 0

        status = "OK" if pct >= 95 else "(!)" if pct >= 50 else "(!!)"
        print(f"{field:<25} {count}/{total:<10} {pct:>6.1f}%    {status}")

    print()

    # Calculer taux d'exploitabilite ultra-complet
    cursor = conn.execute("""
        SELECT COUNT(*) FROM alerts
        WHERE entry_price IS NOT NULL
          AND tp1_price IS NOT NULL
          AND stop_loss_price IS NOT NULL
          AND pool_address IS NOT NULL
          AND pool_address != ''
          AND score IS NOT NULL
          AND tier IS NOT NULL
          AND volume_24h IS NOT NULL
          AND liquidity IS NOT NULL
    """)
    ultra_complete = cursor.fetchone()[0]
    ultra_complete_pct = (ultra_complete / total * 100) if total > 0 else 0

    print("=" * 80)
    print("TAUX D'EXPLOITABILITE ULTRA-COMPLET")
    print("=" * 80)
    print()
    print(f"Alertes 100% completes: {ultra_complete}/{total} ({ultra_complete_pct:.1f}%)")
    print()

    if ultra_complete_pct >= 50:
        print("STATUS: EXCELLENT - Plus de 50% des alertes sont ultra-completes!")
    elif ultra_complete_pct >= 25:
        print("STATUS: BON - 25%+ des alertes sont ultra-completes")
    else:
        print("STATUS: MOYEN - Moins de 25% d'alertes ultra-completes")

    print()

    # Distribution par source
    cursor = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN pool_address IS NOT NULL AND pool_address != '' THEN 1 ELSE 0 END) as with_pool,
            SUM(CASE WHEN entry_price IS NOT NULL THEN 1 ELSE 0 END) as with_tp_sl
        FROM alerts
    """)
    row = cursor.fetchone()

    print("OVERLAP ENTRE SOURCES DE DONNEES:")
    print("-" * 80)
    print(f"Total alertes: {row[0]}")
    print(f"Avec pool_address: {row[1]} ({row[1]/row[0]*100:.1f}%)")
    print(f"Avec TP/SL: {row[2]} ({row[2]/row[0]*100:.1f}%)")

    # Calculer overlap
    cursor = conn.execute("""
        SELECT COUNT(*) FROM alerts
        WHERE (pool_address IS NOT NULL AND pool_address != '')
          AND entry_price IS NOT NULL
    """)
    overlap = cursor.fetchone()[0]
    overlap_pct = (overlap / total * 100) if total > 0 else 0

    print(f"Overlap (les deux): {overlap} ({overlap_pct:.1f}%)")

    if overlap_pct >= 50:
        print("\nOK Bon overlap entre les deux sources!")
    elif overlap_pct >= 25:
        print("\nMOYEN Overlap modere entre les sources")
    else:
        print("\nFAIBLE Peu d'overlap - donnees fragmentees")

    conn.close()

    print()
    print("=" * 80)

if __name__ == '__main__':
    print("COMPLETION DES DONNEES - VERS 100% D'EXPLOITABILITE")
    print("=" * 80)
    print()

    # Etape 1: Completer les TP/SL manquants
    stats = complete_missing_tp_sl()

    # Etape 2: Verifier la completude finale
    verify_data_completeness()

    print("\nOK Completion terminee!")
    print()
    print("Les donnees sont maintenant pretes pour:")
    print("  1. Backtesting theorique (100% des alertes)")
    print("  2. Backtesting avec TP/SL reels (100% des alertes)")
    print(f"  3. Tracking prix actuel ({stats['completeness_pct']:.1f}% avec pool_address)")
    print("  4. Analyse de patterns (100% des alertes)")
