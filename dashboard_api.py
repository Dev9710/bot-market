"""
Dashboard API - Backend Flask pour visualiser les alertes du scanner V3

Endpoints:
- GET /api/alerts - Liste des alertes avec filtres
- GET /api/stats - Statistiques globales
- GET /api/networks - Stats par réseau
- GET /api/alerts/:id - Détail d'une alerte
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import os

app = Flask(__name__)
CORS(app)  # Permettre les requêtes depuis le frontend

# Path vers la base de données et fichiers statiques
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use environment variable DB_PATH if set (Railway: /data/alerts_history.db)
# Otherwise fall back to alerts_history.db to match scanner V3 default
DB_PATH = os.getenv('DB_PATH')
if not DB_PATH:
    # Check if we're on Railway (volume mounted at /data)
    if os.path.exists('/data/alerts_history.db'):
        DB_PATH = '/data/alerts_history.db'
    else:
        # Local development - use alerts_history.db to match scanner V3
        DB_PATH = os.path.join(BASE_DIR, 'alerts_history.db')

def get_db_connection():
    """Connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Retourner des dictionnaires
    return conn

def parse_alert_data(alert_row):
    """Parse une alerte de la DB en dict exploitable."""
    # Try to get velocite_pump and type_pump from direct columns first (preferred)
    # Fallback to parsing alert_data JSON if columns don't exist
    try:
        velocite_pump = alert_row.get('velocite_pump', 0) or 0
        type_pump = alert_row.get('type_pump', '') or ''
    except (KeyError, TypeError):
        # Fallback to JSON parsing for backward compatibility
        velocite_pump = json.loads(alert_row['alert_data']).get('velocite_pump', 0) if alert_row.get('alert_data') else 0
        type_pump = json.loads(alert_row['alert_data']).get('type_pump', '') if alert_row.get('alert_data') else ''

    return {
        'id': alert_row['id'],
        'pool_address': alert_row.get('token_address', alert_row.get('pool_address', '')),
        'network': alert_row['network'],
        'token_name': alert_row['token_name'],
        'token_symbol': alert_row.get('token_symbol', ''),
        'score': alert_row['score'],
        'tier': alert_row.get('tier', 'UNKNOWN'),
        'price': alert_row.get('price_at_alert', alert_row.get('price', 0)),
        'entry_price': alert_row.get('entry_price', alert_row.get('price_at_alert', alert_row.get('price', 0))),
        'liquidity': alert_row.get('liquidity', 0),
        'volume_24h': alert_row.get('volume_24h', 0),
        'volume_6h': alert_row.get('volume_6h', 0),
        'volume_1h': alert_row.get('volume_1h', 0),
        'age_hours': alert_row.get('age_hours', 0),
        'velocite_pump': velocite_pump,
        'type_pump': type_pump,
        'base_score': alert_row.get('base_score', 0),
        'momentum_bonus': alert_row.get('momentum_bonus', 0),
        'buys_24h': alert_row.get('buys_24h', 0),
        'sells_24h': alert_row.get('sells_24h', 0),
        'buy_ratio': alert_row.get('buy_ratio', 0),
        'total_txns': alert_row.get('total_txns', 0),
        'tp1_price': alert_row.get('tp1_price', 0),
        'tp2_price': alert_row.get('tp2_price', 0),
        'tp3_price': alert_row.get('tp3_price', 0),
        'stop_loss_price': alert_row.get('stop_loss_price', 0),
        'volume_acceleration_1h_vs_6h': alert_row.get('volume_acceleration_1h_vs_6h', 0),
        'volume_acceleration_6h_vs_24h': alert_row.get('volume_acceleration_6h_vs_24h', 0),
        'timestamp': alert_row.get('timestamp', ''),
        'created_at': alert_row.get('created_at', ''),
    }

@app.route('/')
def index():
    """Serve dashboard homepage."""
    try:
        return send_from_directory(BASE_DIR, 'dashboard_frontend.html')
    except FileNotFoundError:
        return jsonify({'error': 'dashboard_frontend.html not found', 'base_dir': BASE_DIR}), 404

@app.route('/glossary.html')
@app.route('/glossary')
@app.route('/glossaire')
def glossary():
    """Serve glossary page."""
    try:
        # Try multiple possible locations
        if os.path.exists(os.path.join(BASE_DIR, 'glossary.html')):
            return send_from_directory(BASE_DIR, 'glossary.html')
        # On Railway, check current working directory
        elif os.path.exists('glossary.html'):
            return send_from_directory('.', 'glossary.html')
        else:
            return jsonify({
                'error': 'glossary.html not found',
                'base_dir': BASE_DIR,
                'cwd': os.getcwd(),
                'files_in_base': os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else [],
                'files_in_cwd': os.listdir('.') if os.path.exists('.') else []
            }), 404
    except Exception as e:
        return jsonify({'error': str(e), 'base_dir': BASE_DIR, 'cwd': os.getcwd()}), 500

@app.route('/compare.html')
def compare():
    """Serve compare page."""
    try:
        return send_from_directory(BASE_DIR, 'compare.html')
    except FileNotFoundError:
        return jsonify({'error': 'compare.html not found', 'base_dir': BASE_DIR}), 404

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    Récupère la liste des alertes avec filtres optionnels.

    Query params:
    - network: filtre par réseau (eth, bsc, base, solana)
    - tier: filtre par tier (HIGH, MEDIUM, LOW)
    - min_score: score minimum
    - limit: nombre max d'alertes (défaut 100)
    - offset: pagination
    - days: alertes des N derniers jours (défaut 7)
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

        # Construction de la requête
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []

        # Filtre par date
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
        alerts = [parse_alert_data(row) for row in cursor.fetchall()]

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
    """
    Statistiques globales.

    Query params:
    - days: période en jours (défaut 7)
    """
    try:
        days = request.args.get('days', type=int, default=7)
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        conn = get_db_connection()

        # Stats globales
        stats = {
            'total_alerts': 0,
            'avg_score': 0,
            'avg_velocity': 0,
            'avg_liquidity': 0,
            'by_tier': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'VERY_LOW': 0, 'ULTRA_HIGH': 0},
            'by_network': {},
            'score_distribution': {},
            'alerts_per_day': [],
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
def get_networks_stats():
    """Statistiques détaillées par réseau."""
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
                'max_score': row['max_score'],
            })

        conn.close()

        return jsonify({'networks': networks})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
def get_alert_detail(alert_id):
    """Détail d'une alerte spécifique."""
    try:
        conn = get_db_connection()

        cursor = conn.execute("SELECT * FROM alerts WHERE id = ?", [alert_id])
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Alert not found'}), 404

        alert = parse_alert_data(row)

        # Ajouter les données complètes
        if row['alert_data']:
            alert['full_data'] = json.loads(row['alert_data'])

        conn.close()

        return jsonify(alert)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent', methods=['GET'])
def get_recent_alerts():
    """Alertes les plus récentes (temps réel)."""
    try:
        limit = request.args.get('limit', type=int, default=10)

        conn = get_db_connection()

        cursor = conn.execute("""
            SELECT * FROM alerts
            ORDER BY created_at DESC
            LIMIT ?
        """, [limit])

        alerts = [parse_alert_data(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify({'alerts': alerts})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Vérifier que la DB existe
    if not os.path.exists(DB_PATH):
        print(f"[!] ATTENTION: Base de donnees non trouvee: {DB_PATH}")
        print("[!] Les endpoints API ne fonctionneront pas sans la base de donnees.")
        print("[!] Lancez le scanner pour creer la base de donnees.")
        print("\n[OK] Le serveur demarre quand meme pour servir les pages HTML (glossaire, etc.)\n")

    print(f"[START] API Dashboard demarree")
    print("Pages disponibles:")
    print("  GET / (dashboard)")
    print("  GET /glossary.html, /glossary, /glossaire")
    print("  GET /compare.html")
    print("\nEndpoints API:")
    print("  GET /api/health")
    print("  GET /api/alerts")
    print("  GET /api/stats")
    print("  GET /api/networks")
    print("  GET /api/alerts/:id")
    print("  GET /api/recent")

    # Port from environment variable (Railway) or default 5000
    port = int(os.environ.get('PORT', 5000))

    # Detect production environment (Railway)
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') is not None

    print(f"\nEnvironment: {'PRODUCTION (Railway)' if is_production else 'DEVELOPMENT'}")
    print(f"Port: {port}")
    print(f"Acces: http://localhost:{port}" if not is_production else f"Acces: https://bot-market-production.up.railway.app")
    print(f"Glossaire: http://localhost:{port}/glossary\n" if not is_production else f"Glossaire: https://bot-market-production.up.railway.app/glossary\n")

    # En production, désactiver debug mode
    app.run(host='0.0.0.0', port=port, debug=not is_production)
