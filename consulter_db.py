# -*- coding: utf-8 -*-
"""
Script simple pour consulter la base de données alerts_history.db
Utilisable localement ou via Railway CLI
"""

import sqlite3
import sys
from datetime import datetime

# Fix encoding pour Windows
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (ValueError, AttributeError):
            pass

def connect_db(db_path='alerts_history.db'):
    """Connexion à la base de données."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Pour avoir des résultats en dict
        return conn
    except Exception as e:
        print(f"❌ Erreur connexion DB: {e}")
        return None

def afficher_dernieres_alertes(conn, limit=10):
    """Affiche les dernières alertes."""
    print("\n" + "="*100)
    print(f"📊 DERNIÈRES {limit} ALERTES")
    print("="*100)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            timestamp,
            token_name,
            network,
            score,
            confidence_score,
            price_at_alert,
            volume_24h,
            liquidity
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))

    alerts = cursor.fetchall()

    if not alerts:
        print("Aucune alerte trouvée.")
        return

    print(f"{'ID':<5} {'Date':<20} {'Token':<15} {'Net':<8} {'Score':<6} {'Sécu':<6} {'Prix':<12} {'Vol 24h':<12} {'Liq':<12}")
    print("-"*100)

    for alert in alerts:
        print(
            f"{alert['id']:<5} "
            f"{alert['timestamp']:<20} "
            f"{alert['token_name']:<15} "
            f"{alert['network']:<8} "
            f"{alert['score']:<6} "
            f"{alert['confidence_score']:<6} "
            f"${alert['price_at_alert']:<11.10f} "
            f"${alert['volume_24h'] or 0:<11,.0f} "
            f"${alert['liquidity'] or 0:<11,.0f}"
        )

    print("="*100)

def afficher_detail_alerte(conn, alert_id):
    """Affiche le détail complet d'une alerte."""
    print("\n" + "="*100)
    print(f"🔍 DÉTAIL ALERTE #{alert_id}")
    print("="*100)

    cursor = conn.cursor()

    # Récupérer l'alerte
    cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    alert = cursor.fetchone()

    if not alert:
        print(f"❌ Alerte #{alert_id} introuvable.")
        return

    # Afficher les infos principales
    print(f"\n📊 INFORMATIONS GÉNÉRALES:")
    print(f"  Token: {alert['token_name']}")
    print(f"  Adresse: {alert['token_address']}")
    print(f"  Réseau: {alert['network']}")
    print(f"  Date: {alert['timestamp']}")
    print(f"  Score opportunité: {alert['score']}/100")
    print(f"  Score sécurité: {alert['confidence_score']}/100")

    print(f"\n💰 NIVEAUX DE PRIX:")
    print(f"  Prix à l'alerte: ${alert['price_at_alert']:.10f}")
    print(f"  Entry: ${alert['entry_price']:.10f}")
    print(f"  Stop Loss: ${alert['stop_loss_price']:.10f} ({alert['stop_loss_percent']:+.1f}%)")
    print(f"  TP1: ${alert['tp1_price']:.10f} ({alert['tp1_percent']:+.1f}%)")
    print(f"  TP2: ${alert['tp2_price']:.10f} ({alert['tp2_percent']:+.1f}%)")
    print(f"  TP3: ${alert['tp3_price']:.10f} ({alert['tp3_percent']:+.1f}%)")

    print(f"\n📈 MÉTRIQUES:")
    print(f"  Volume 24h: ${alert['volume_24h'] or 0:,.0f}")
    print(f"  Liquidité: ${alert['liquidity'] or 0:,.0f}")
    print(f"  Transactions 24h: {alert['total_txns'] or 0}")
    print(f"  Buy Ratio: {alert['buy_ratio'] or 0:.2f}")
    print(f"  Age: {alert['age_hours'] or 0:.1f}h")

    # Récupérer les trackings
    cursor.execute("""
        SELECT * FROM price_tracking
        WHERE alert_id = ?
        ORDER BY minutes_after_alert
    """, (alert_id,))
    trackings = cursor.fetchall()

    if trackings:
        print(f"\n📊 TRACKING DES PRIX:")
        print(f"  {'Temps':<10} {'Prix':<15} {'ROI':<10} {'TP1':<5} {'TP2':<5} {'TP3':<5} {'SL':<5}")
        print("  " + "-"*60)

        for t in trackings:
            tp1 = "✅" if t['tp1_hit'] else "❌"
            tp2 = "✅" if t['tp2_hit'] else "❌"
            tp3 = "✅" if t['tp3_hit'] else "❌"
            sl = "⛔" if t['sl_hit'] else "✅"

            interval = f"{t['minutes_after_alert']}min"
            if t['minutes_after_alert'] >= 60:
                interval = f"{t['minutes_after_alert']//60}h"

            print(
                f"  {interval:<10} "
                f"${t['price'] or 0:<14.10f} "
                f"{t['roi_percent'] or 0:+9.2f}% "
                f"{tp1:<5} {tp2:<5} {tp3:<5} {sl:<5}"
            )

    # Récupérer l'analyse
    cursor.execute("""
        SELECT * FROM alert_analysis
        WHERE alert_id = ?
    """, (alert_id,))
    analysis = cursor.fetchone()

    if analysis:
        print(f"\n🎯 ANALYSE DE PERFORMANCE (24h):")
        print(f"  Profitable: {'✅ OUI' if analysis['was_profitable'] else '❌ NON'}")
        print(f"  ROI à 24h: {analysis['roi_at_24h'] or 0:+.2f}%")
        print(f"  Meilleur ROI (4h): {analysis['best_roi_4h'] or 0:+.2f}%")
        print(f"  Pire ROI (4h): {analysis['worst_roi_4h'] or 0:+.2f}%")
        print(f"\n  Objectifs atteints:")
        print(f"    TP1: {'✅' if analysis['tp1_was_hit'] else '❌'} {f'(en {analysis['time_to_tp1']}min)' if analysis['time_to_tp1'] else ''}")
        print(f"    TP2: {'✅' if analysis['tp2_was_hit'] else '❌'} {f'(en {analysis['time_to_tp2']}min)' if analysis['time_to_tp2'] else ''}")
        print(f"    TP3: {'✅' if analysis['tp3_was_hit'] else '❌'} {f'(en {analysis['time_to_tp3']}min)' if analysis['time_to_tp3'] else ''}")
        print(f"    Stop Loss: {'⛔' if analysis['sl_was_hit'] else '✅'} {f'(touché en {analysis['time_to_sl']}min)' if analysis['time_to_sl'] else ''}")
        print(f"\n  Qualité prédiction: {analysis['prediction_quality'] or 'N/A'}")
        print(f"  Cohérent: {'✅ OUI' if analysis['was_coherent'] else '❌ NON'}")
        if analysis['coherence_notes']:
            print(f"  Notes: {analysis['coherence_notes']}")

    print("="*100)

def afficher_statistiques(conn):
    """Affiche les statistiques globales."""
    print("\n" + "="*100)
    print("📊 STATISTIQUES GLOBALES")
    print("="*100)

    cursor = conn.cursor()

    # Total alertes
    cursor.execute("SELECT COUNT(*) as total FROM alerts")
    total_alerts = cursor.fetchone()['total']

    # Alertes analysées
    cursor.execute("SELECT COUNT(*) as total FROM alert_analysis")
    analyzed = cursor.fetchone()['total']

    # Taux de cohérence
    cursor.execute("""
        SELECT COUNT(CASE WHEN was_coherent = 1 THEN 1 END) * 100.0 / COUNT(*) as rate
        FROM alert_analysis
    """)
    coherence_rate = cursor.fetchone()['rate'] or 0

    # ROI moyen
    cursor.execute("SELECT AVG(roi_at_24h) as avg FROM alert_analysis WHERE roi_at_24h IS NOT NULL")
    avg_roi = cursor.fetchone()['avg'] or 0

    # Taux TP
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN tp1_was_hit = 1 THEN 1 END) * 100.0 / COUNT(*) as tp1,
            COUNT(CASE WHEN tp2_was_hit = 1 THEN 1 END) * 100.0 / COUNT(*) as tp2,
            COUNT(CASE WHEN tp3_was_hit = 1 THEN 1 END) * 100.0 / COUNT(*) as tp3,
            COUNT(CASE WHEN sl_was_hit = 1 THEN 1 END) * 100.0 / COUNT(*) as sl
        FROM alert_analysis
    """)
    tp_rates = cursor.fetchone()

    print(f"\n📊 Vue d'ensemble:")
    print(f"  Total alertes envoyées: {total_alerts}")
    print(f"  Alertes analysées (24h+): {analyzed}")
    print(f"  Taux de cohérence: {coherence_rate:.1f}%")

    print(f"\n💰 Performance:")
    print(f"  ROI moyen 24h: {avg_roi:+.2f}%")

    print(f"\n🎯 Taux d'atteinte des objectifs:")
    print(f"  TP1 (+5%): {tp_rates['tp1'] or 0:.1f}%")
    print(f"  TP2 (+10%): {tp_rates['tp2'] or 0:.1f}%")
    print(f"  TP3 (+15%): {tp_rates['tp3'] or 0:.1f}%")
    print(f"  Stop Loss (-10%): {tp_rates['sl'] or 0:.1f}%")

    # ROI par score
    cursor.execute("""
        SELECT
            CASE
                WHEN a.score >= 80 THEN '80-100'
                WHEN a.score >= 60 THEN '60-79'
                WHEN a.score >= 40 THEN '40-59'
                ELSE '0-39'
            END as score_range,
            AVG(an.roi_at_24h) as avg_roi,
            COUNT(*) as count
        FROM alerts a
        LEFT JOIN alert_analysis an ON a.id = an.alert_id
        WHERE an.roi_at_24h IS NOT NULL
        GROUP BY score_range
        ORDER BY score_range DESC
    """)
    roi_by_score = cursor.fetchall()

    if roi_by_score:
        print(f"\n📊 ROI moyen par tranche de score:")
        for row in roi_by_score:
            print(f"  Score {row['score_range']}: {row['avg_roi']:+.2f}% ({row['count']} alertes)")

    print("="*100)

def afficher_tokens_suivis(conn):
    """Affiche la liste des tokens suivis."""
    print("\n" + "="*100)
    print("🪙 TOKENS SUIVIS")
    print("="*100)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            token_name,
            token_address,
            network,
            COUNT(*) as alert_count,
            MAX(timestamp) as last_alert,
            AVG(score) as avg_score
        FROM alerts
        GROUP BY token_address
        ORDER BY last_alert DESC
    """)

    tokens = cursor.fetchall()

    if not tokens:
        print("Aucun token suivi.")
        return

    print(f"{'Token':<15} {'Réseau':<8} {'Nb Alertes':<12} {'Score Moy':<10} {'Dernière Alerte':<20}")
    print("-"*100)

    for token in tokens:
        print(
            f"{token['token_name']:<15} "
            f"{token['network']:<8} "
            f"{token['alert_count']:<12} "
            f"{token['avg_score']:.1f}/100{'':<4} "
            f"{token['last_alert']:<20}"
        )

    print("="*100)

def menu_principal():
    """Menu interactif."""
    print("\n" + "="*100)
    print("🚀 CONSULTATION BASE DE DONNÉES - Bot Market")
    print("="*100)
    print("\nOptions:")
    print("  1. Afficher les dernières alertes")
    print("  2. Afficher le détail d'une alerte")
    print("  3. Afficher les statistiques globales")
    print("  4. Afficher les tokens suivis")
    print("  5. Quitter")

    choix = input("\nVotre choix (1-5): ").strip()
    return choix

def main():
    """Fonction principale."""
    # Connexion à la DB
    db_path = 'alerts_history.db'
    conn = connect_db(db_path)

    if not conn:
        print(f"❌ Impossible de se connecter à {db_path}")
        return

    print(f"✅ Connecté à {db_path}")

    while True:
        choix = menu_principal()

        if choix == '1':
            limit = input("Nombre d'alertes à afficher (défaut: 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            afficher_dernieres_alertes(conn, limit)

        elif choix == '2':
            alert_id = input("ID de l'alerte: ").strip()
            if alert_id.isdigit():
                afficher_detail_alerte(conn, int(alert_id))
            else:
                print("❌ ID invalide")

        elif choix == '3':
            afficher_statistiques(conn)

        elif choix == '4':
            afficher_tokens_suivis(conn)

        elif choix == '5':
            print("\n👋 Au revoir!")
            break

        else:
            print("❌ Choix invalide")

        input("\nAppuyez sur Entrée pour continuer...")

    conn.close()

if __name__ == "__main__":
    main()