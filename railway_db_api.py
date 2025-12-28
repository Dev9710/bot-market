"""
Railway DB API - Lit directement depuis la base SQLite Railway

À déployer SUR Railway avec le scanner V3.
Utilise la même base de données que alert_tracker.py

Architecture:
- Scanner V3 écrit dans alerts_history.db (via alert_tracker)
- Cette API lit alerts_history.db
- Frontend dashboard consomme cette API
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)
CORS(app)  # Permettre requêtes depuis frontend

# Chemin vers la base de données
# Railway: /data/alerts_history.db
# Local: alerts_tracker.db ou alerts_history.db
DB_PATH = os.getenv("DB_PATH")

if not DB_PATH:
    # Mode local: chercher la DB
    if os.path.exists("alerts_tracker.db"):
        DB_PATH = "alerts_tracker.db"
    elif os.path.exists("alerts_history.db"):
        DB_PATH = "alerts_history.db"
    elif os.path.exists("/data/alerts_history.db"):
        DB_PATH = "/data/alerts_history.db"
    else:
        DB_PATH = "alerts_tracker.db"  # Défaut

def get_db_connection():
    """Connexion à la base SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Retourner des dictionnaires
    return conn

def parse_alert_row(row):
    """Convertit une ligne DB en dict pour le dashboard."""
    import json

    # Charger alert_data JSON s'il existe
    alert_data = {}
    if row['alert_data']:
        try:
            alert_data = json.loads(row['alert_data'])
        except:
            pass

    return {
        'id': row['id'],
        'pool_address': row['pool_address'],
        'network': row['network'],
        'token_name': row['token_name'],
        'token_symbol': row['token_symbol'],
        'score': row['score'],
        'tier': row['tier'],
        'price': row['price'],
        'liquidity': row['liquidity'],
        'volume_24h': row['volume_24h'],
        'age_hours': row['age_hours'],
        'velocite_pump': alert_data.get('velocite_pump', 0),
        'type_pump': alert_data.get('type_pump', ''),
        'created_at': row['created_at'],
        'timestamp': row['timestamp']
    }

@app.route('/api/health', methods=['GET'])
def health():
    """Health check."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) as count FROM alerts")
        total = cursor.fetchone()['count']
        conn.close()

        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'total_alerts': total,
            'db_path': DB_PATH
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    Liste des alertes avec filtres.

    Query params:
    - network: eth, bsc, base, solana
    - tier: HIGH, MEDIUM, LOW, ULTRA_HIGH
    - min_score: score minimum
    - limit: nombre max (défaut 100)
    - offset: pagination
    - days: période en jours (défaut 7)
    """
    try:
        conn = get_db_connection()

        # Paramètres
        network = request.args.get('network')
        tier = request.args.get('tier')
        min_score = request.args.get('min_score', type=int, default=0)
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)
        days = request.args.get('days', type=int, default=7)

        # Construction requête
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []

        # Filtre date
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        query += " AND created_at >= ?"
        params.append(cutoff_date)

        # Filtres optionnels
        if network:
            query += " AND network = ?"
            params.append(network)

        if tier:
            query += " AND tier = ?"
            params.append(tier)

        if min_score > 0:
            query += " AND score >= ?"
            params.append(min_score)

        # Tri et pagination
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        alerts = [parse_alert_row(row) for row in cursor.fetchall()]

        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)").split("ORDER BY")[0]
        total = conn.execute(count_query, params[:len(params)-2]).fetchone()[0]

        conn.close()

        return jsonify({
            'alerts': alerts,
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiques globales."""
    try:
        days = request.args.get('days', type=int, default=7)
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        conn = get_db_connection()

        stats = {
            'total_alerts': 0,
            'avg_score': 0,
            'avg_liquidity': 0,
            'by_tier': {},
            'by_network': {},
            'score_distribution': {},
            'alerts_per_day': []
        }

        # Total et moyennes
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                AVG(score) as avg_score,
                AVG(liquidity) as avg_liq
            FROM alerts
            WHERE created_at >= ?
        """, [cutoff_date])

        row = cursor.fetchone()
        stats['total_alerts'] = row['total']
        stats['avg_score'] = round(row['avg_score'], 1) if row['avg_score'] else 0
        stats['avg_liquidity'] = round(row['avg_liq'], 0) if row['avg_liq'] else 0

        # Par tier
        cursor = conn.execute("""
            SELECT tier, COUNT(*) as count
            FROM alerts
            WHERE created_at >= ?
            GROUP BY tier
        """, [cutoff_date])

        for row in cursor.fetchall():
            stats['by_tier'][row['tier']] = row['count']

        # Par réseau
        cursor = conn.execute("""
            SELECT network, COUNT(*) as count, AVG(score) as avg_score
            FROM alerts
            WHERE created_at >= ?
            GROUP BY network
        """, [cutoff_date])

        for row in cursor.fetchall():
            stats['by_network'][row['network']] = {
                'count': row['count'],
                'avg_score': round(row['avg_score'], 1)
            }

        # Distribution scores
        cursor = conn.execute("""
            SELECT
                CASE
                    WHEN score >= 95 THEN '95-100'
                    WHEN score >= 90 THEN '90-94'
                    WHEN score >= 85 THEN '85-89'
                    WHEN score >= 80 THEN '80-84'
                    ELSE '<80'
                END as range,
                COUNT(*) as count
            FROM alerts
            WHERE created_at >= ?
            GROUP BY range
        """, [cutoff_date])

        for row in cursor.fetchall():
            stats['score_distribution'][row['range']] = row['count']

        # Alertes par jour
        cursor = conn.execute("""
            SELECT
                DATE(created_at) as day,
                COUNT(*) as count,
                AVG(score) as avg_score
            FROM alerts
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        """, [cutoff_date])

        stats['alerts_per_day'] = [
            {
                'date': row['day'],
                'count': row['count'],
                'avg_score': round(row['avg_score'], 1)
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/networks', methods=['GET'])
def get_networks():
    """Statistiques par réseau."""
    try:
        days = request.args.get('days', type=int, default=7)
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        conn = get_db_connection()

        cursor = conn.execute("""
            SELECT
                network,
                COUNT(*) as total,
                AVG(score) as avg_score,
                AVG(liquidity) as avg_liq,
                AVG(volume_24h) as avg_vol,
                MIN(score) as min_score,
                MAX(score) as max_score
            FROM alerts
            WHERE created_at >= ?
            GROUP BY network
            ORDER BY total DESC
        """, [cutoff_date])

        networks = []
        for row in cursor.fetchall():
            networks.append({
                'network': row['network'],
                'total': row['total'],
                'avg_score': round(row['avg_score'], 1),
                'avg_liquidity': round(row['avg_liq'], 0),
                'avg_volume': round(row['avg_vol'], 0),
                'min_score': row['min_score'],
                'max_score': row['max_score']
            })

        conn.close()

        return jsonify({'networks': networks})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent', methods=['GET'])
def get_recent():
    """Alertes les plus récentes."""
    try:
        limit = request.args.get('limit', type=int, default=10)

        conn = get_db_connection()

        cursor = conn.execute("""
            SELECT * FROM alerts
            ORDER BY created_at DESC
            LIMIT ?
        """, [limit])

        alerts = [parse_alert_row(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify({'alerts': alerts})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
def get_alert_detail(alert_id):
    """Détail d'une alerte."""
    try:
        conn = get_db_connection()

        cursor = conn.execute("SELECT * FROM alerts WHERE id = ?", [alert_id])
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Alert not found'}), 404

        alert = parse_alert_row(row)

        # Ajouter données complètes
        if row['alert_data']:
            import json
            alert['full_data'] = json.loads(row['alert_data'])

        conn.close()

        return jsonify(alert)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    # Vérifier DB
    if not os.path.exists(DB_PATH):
        print(f"⚠️ AVERTISSEMENT: Base de données non trouvée: {DB_PATH}")
        print(f"   L'API démarrera mais retournera des erreurs jusqu'à ce que le scanner crée la DB")
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT COUNT(*) FROM alerts")
        total = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Base de données connectée: {DB_PATH}")
        print(f"   {total} alertes disponibles")

    print(f"\n🚀 Railway DB API démarrée sur port {port}")
    print(f"📊 Endpoints disponibles:")
    print(f"   GET /api/health")
    print(f"   GET /api/alerts")
    print(f"   GET /api/stats")
    print(f"   GET /api/networks")
    print(f"   GET /api/recent")
    print(f"   GET /api/alerts/:id")
    print()

    app.run(host='0.0.0.0', port=port, debug=False)
