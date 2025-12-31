"""
Railway DB API - Lit directement depuis la base SQLite Railway

À déployer SUR Railway avec le scanner V3.
Utilise la même base de données que alert_tracker.py

Architecture:
- Scanner V3 écrit dans alerts_history.db (via alert_tracker)
- Cette API lit alerts_history.db
- Frontend dashboard consomme cette API
"""

from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import sqlite3
import os
import time
import json
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
    # Convertir sqlite3.Row en dict pour utiliser .get()
    row_dict = dict(row)

    # Calculer le tier basé sur le score
    score = row_dict.get('score', 0)
    if score >= 95:
        tier = 'ULTRA_HIGH'
    elif score >= 85:
        tier = 'HIGH'
    elif score >= 75:
        tier = 'MEDIUM'
    else:
        tier = 'LOW'

    # Extraire le symbole du nom du token (ex: "PEPE/WETH" -> "PEPE")
    token_name = row_dict.get('token_name', '')
    token_symbol = token_name.split('/')[0] if '/' in token_name else token_name

    return {
        'id': row_dict.get('id', 0),
        'pool_address': row_dict.get('token_address', ''),
        'network': row_dict.get('network', ''),
        'token_name': token_name,
        'token_symbol': token_symbol,
        'score': score,
        'tier': tier,
        'price': row_dict.get('price_at_alert', 0),
        'liquidity': row_dict.get('liquidity', 0),
        'volume_24h': row_dict.get('volume_24h', 0),
        'age_hours': row_dict.get('age_hours', 0),
        'velocite_pump': 0,
        'type_pump': '',
        'created_at': row_dict.get('created_at', ''),
        'timestamp': row_dict.get('timestamp', '')
    }

@app.route('/')
def dashboard():
    """Serve the dashboard HTML."""
    try:
        return send_file('dashboard_frontend.html')
    except Exception as e:
        return f"Dashboard file not found: {str(e)}", 404

@app.route('/bot-market/<path:filename>')
def serve_bot_market_files(filename):
    """Serve static files from bot-market directory."""
    try:
        file_path = os.path.join('bot-market', filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return f"File not found: {filename}", 404
    except Exception as e:
        return f"Error serving file: {str(e)}", 500

@app.route('/compare.html')
def serve_compare():
    """Serve the token comparison page."""
    try:
        return send_file('compare.html')
    except Exception as e:
        return f"Compare page not found: {str(e)}", 404

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
            # Convertir le tier en filtre de score
            if tier == 'ULTRA_HIGH':
                query += " AND score >= 95"
            elif tier == 'HIGH':
                query += " AND score >= 85 AND score < 95"
            elif tier == 'MEDIUM':
                query += " AND score >= 75 AND score < 85"
            elif tier == 'LOW':
                query += " AND score < 75"

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

        # Par tier (calculé à partir du score)
        cursor = conn.execute("""
            SELECT
                CASE
                    WHEN score >= 95 THEN 'ULTRA_HIGH'
                    WHEN score >= 85 THEN 'HIGH'
                    WHEN score >= 75 THEN 'MEDIUM'
                    ELSE 'LOW'
                END as tier,
                COUNT(*) as count
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
            alert['full_data'] = json.loads(row['alert_data'])

        conn.close()

        return jsonify(alert)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream')
def stream():
    """Server-Sent Events stream for live updates."""
    def event_stream():
        last_id = 0

        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Live stream connected'})}\n\n"

        while True:
            try:
                conn = get_db_connection()

                # Check for new alerts since last_id
                cursor = conn.execute("""
                    SELECT * FROM alerts
                    WHERE id > ?
                    ORDER BY id ASC
                    LIMIT 10
                """, [last_id])

                new_alerts = cursor.fetchall()

                if new_alerts:
                    for row in new_alerts:
                        alert = parse_alert_row(row)
                        last_id = row['id']

                        # Send new alert event
                        yield f"data: {json.dumps({'type': 'new_alert', 'alert': alert})}\n\n"

                # Also send periodic stats update every 30 seconds
                cursor = conn.execute("SELECT COUNT(*) as total FROM alerts")
                total = cursor.fetchone()['total']

                yield f"data: {json.dumps({'type': 'heartbeat', 'total_alerts': total, 'timestamp': datetime.now().isoformat()})}\n\n"

                conn.close()

                # Wait 5 seconds before next check
                time.sleep(5)

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                time.sleep(5)

    return Response(event_stream(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })

# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get all portfolio positions."""
    try:
        status_filter = request.args.get('status', 'ACTIVE')  # ACTIVE, ALL, CLOSED

        conn = get_db_connection()

        if status_filter == 'ALL':
            cursor = conn.execute("""
                SELECT * FROM portfolio
                ORDER BY created_at DESC
            """)
        else:
            cursor = conn.execute("""
                SELECT * FROM portfolio
                WHERE status = ?
                ORDER BY created_at DESC
            """, [status_filter])

        positions = []
        for row in cursor.fetchall():
            positions.append(dict(row))

        conn.close()

        return jsonify({
            'positions': positions,
            'count': len(positions)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio', methods=['POST'])
def add_to_portfolio():
    """Add a new position to portfolio."""
    try:
        data = request.json

        required_fields = ['alert_id', 'pool_address', 'network', 'token_symbol', 'entry_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db_connection()

        cursor = conn.execute("""
            INSERT INTO portfolio (
                alert_id, pool_address, network, token_symbol, token_name,
                entry_price, position_size, tp1_price, tp2_price, tp3_price,
                stop_loss_price, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            data['alert_id'],
            data['pool_address'],
            data['network'],
            data['token_symbol'],
            data.get('token_name', ''),
            data['entry_price'],
            data.get('position_size'),
            data.get('tp1_price'),
            data.get('tp2_price'),
            data.get('tp3_price'),
            data.get('stop_loss_price'),
            data.get('notes', '')
        ])

        conn.commit()
        position_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'success': True,
            'position_id': position_id,
            'message': 'Position added to portfolio'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/<int:position_id>', methods=['PUT'])
def update_portfolio_position(position_id):
    """Update a portfolio position."""
    try:
        data = request.json

        conn = get_db_connection()

        # Build UPDATE query dynamically based on provided fields
        updates = []
        values = []

        allowed_fields = [
            'current_price', 'status', 'tp1_hit', 'tp2_hit', 'tp3_hit',
            'stop_loss_hit', 'current_pnl_percent', 'highest_price',
            'max_gain_percent', 'notes'
        ]

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                values.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Always update last_updated
        updates.append("last_updated = CURRENT_TIMESTAMP")

        values.append(position_id)
        query = f"UPDATE portfolio SET {', '.join(updates)} WHERE id = ?"

        conn.execute(query, values)
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Position updated'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/<int:position_id>', methods=['DELETE'])
def delete_portfolio_position(position_id):
    """Delete a portfolio position."""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM portfolio WHERE id = ?", [position_id])
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Position deleted'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/stats', methods=['GET'])
def get_portfolio_stats():
    """Get portfolio performance statistics."""
    try:
        conn = get_db_connection()

        # Active positions count
        cursor = conn.execute("SELECT COUNT(*) as count FROM portfolio WHERE status = 'ACTIVE'")
        active_count = cursor.fetchone()['count']

        # Total positions
        cursor = conn.execute("SELECT COUNT(*) as count FROM portfolio")
        total_count = cursor.fetchone()['count']

        # Win rate (TP1+ hit)
        cursor = conn.execute("""
            SELECT COUNT(*) as wins FROM portfolio
            WHERE tp1_hit = 1 OR tp2_hit = 1 OR tp3_hit = 1
        """)
        wins = cursor.fetchone()['wins']

        # Stop losses hit
        cursor = conn.execute("SELECT COUNT(*) as losses FROM portfolio WHERE stop_loss_hit = 1")
        losses = cursor.fetchone()['losses']

        # Average PnL for closed positions
        cursor = conn.execute("""
            SELECT AVG(current_pnl_percent) as avg_pnl
            FROM portfolio
            WHERE status != 'ACTIVE' AND current_pnl_percent IS NOT NULL
        """)
        avg_pnl = cursor.fetchone()['avg_pnl'] or 0

        # Best performing position
        cursor = conn.execute("""
            SELECT token_symbol, max_gain_percent
            FROM portfolio
            WHERE max_gain_percent IS NOT NULL
            ORDER BY max_gain_percent DESC
            LIMIT 1
        """)
        best = cursor.fetchone()

        conn.close()

        win_rate = (wins / total_count * 100) if total_count > 0 else 0

        return jsonify({
            'active_positions': active_count,
            'total_positions': total_count,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 1),
            'avg_pnl': round(avg_pnl, 2),
            'best_trade': {
                'symbol': best['token_symbol'] if best else 'N/A',
                'gain': round(best['max_gain_percent'], 2) if best and best['max_gain_percent'] else 0
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    # Vérifier DB
    if not os.path.exists(DB_PATH):
        print(f"[WARNING] Base de donnees non trouvee: {DB_PATH}")
        print(f"   L'API demarrera mais retournera des erreurs jusqu'a ce que le scanner cree la DB")
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT COUNT(*) FROM alerts")
        total = cursor.fetchone()[0]
        conn.close()
        print(f"[OK] Base de donnees connectee: {DB_PATH}")
        print(f"   {total} alertes disponibles")

    print(f"\n[START] Railway DB API demarree sur port {port}")
    print(f"[INFO] Endpoints disponibles:")
    print(f"   GET  /api/health")
    print(f"   GET  /api/alerts")
    print(f"   GET  /api/stats")
    print(f"   GET  /api/networks")
    print(f"   GET  /api/recent")
    print(f"   GET  /api/alerts/:id")
    print(f"   GET  /api/stream (Server-Sent Events)")
    print(f"   GET  /api/portfolio")
    print(f"   POST /api/portfolio")
    print(f"   PUT  /api/portfolio/:id")
    print(f"   DEL  /api/portfolio/:id")
    print(f"   GET  /api/portfolio/stats")
    print()

    app.run(host='0.0.0.0', port=port, debug=False)
