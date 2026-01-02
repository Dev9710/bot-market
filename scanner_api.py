"""
Scanner API - API REST pour accéder aux alertes en live depuis Railway

À déployer AVEC le scanner V3 sur Railway.
Le scanner écrira les alertes dans un fichier JSON que l'API lira.

Architecture:
- Scanner V3 écrit dans alerts_live.json (thread séparé)
- API Flask lit alerts_live.json et expose via REST
- Frontend dashboard consomme l'API depuis Railway
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

app = Flask(__name__)
CORS(app)  # Permettre requêtes depuis frontend

# Fichier de stockage des alertes (écrit par le scanner)
ALERTS_FILE = 'alerts_live.json'
file_lock = Lock()

def load_alerts():
    """Charge les alertes depuis le fichier JSON."""
    if not os.path.exists(ALERTS_FILE):
        return []

    try:
        with file_lock:
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erreur lecture alertes: {e}")
        return []

def save_alert(alert_data):
    """Sauvegarde une nouvelle alerte (appelé par le scanner)."""
    alerts = load_alerts()

    # Ajouter timestamp si absent
    if 'created_at' not in alert_data:
        alert_data['created_at'] = datetime.now().isoformat()

    alerts.append(alert_data)

    # Garder seulement les 1000 dernières alertes
    alerts = alerts[-1000:]

    try:
        with file_lock:
            with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde alerte: {e}")

@app.route('/api/health', methods=['GET'])
def health():
    """Health check."""
    alerts = load_alerts()
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'total_alerts': len(alerts)
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Liste des alertes avec filtres."""
    alerts = load_alerts()

    # Paramètres
    network = request.args.get('network')
    tier = request.args.get('tier')
    min_score = request.args.get('min_score', type=int, default=0)
    limit = request.args.get('limit', type=int, default=100)
    offset = request.args.get('offset', type=int, default=0)
    days = request.args.get('days', type=int, default=7)

    # Filtre par date
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered = []

    for alert in alerts:
        # Parse date
        try:
            alert_date = datetime.fromisoformat(alert.get('created_at', ''))
            if alert_date < cutoff_date:
                continue
        except:
            pass

        # Filtres
        if network and alert.get('network', '').lower() != network.lower():
            continue

        if tier and alert.get('tier', '') != tier:
            continue

        if alert.get('score', 0) < min_score:
            continue

        filtered.append(alert)

    # Tri par date décroissante
    filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    total = len(filtered)
    paginated = filtered[offset:offset+limit]

    return jsonify({
        'alerts': paginated,
        'total': total,
        'limit': limit,
        'offset': offset
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiques globales."""
    alerts = load_alerts()
    days = request.args.get('days', type=int, default=7)

    # Filtre par date
    cutoff_date = datetime.now() - timedelta(days=days)
    recent = []

    for alert in alerts:
        try:
            alert_date = datetime.fromisoformat(alert.get('created_at', ''))
            if alert_date >= cutoff_date:
                recent.append(alert)
        except:
            pass

    if not recent:
        return jsonify({
            'total_alerts': 0,
            'avg_score': 0,
            'avg_liquidity': 0,
            'by_tier': {},
            'by_network': {},
            'score_distribution': {},
            'alerts_per_day': []
        })

    # Calculs
    total = len(recent)
    avg_score = sum(a.get('score', 0) for a in recent) / total
    avg_liq = sum(a.get('liquidity', 0) for a in recent) / total

    # Par tier
    by_tier = defaultdict(int)
    for a in recent:
        by_tier[a.get('tier', 'UNKNOWN')] += 1

    # Par réseau
    by_network = defaultdict(lambda: {'count': 0, 'total_score': 0})
    for a in recent:
        net = a.get('network', 'unknown')
        by_network[net]['count'] += 1
        by_network[net]['total_score'] += a.get('score', 0)

    for net in by_network:
        count = by_network[net]['count']
        by_network[net]['avg_score'] = by_network[net]['total_score'] / count if count > 0 else 0
        del by_network[net]['total_score']

    # Distribution scores
    score_dist = {
        '95-100': 0,
        '90-94': 0,
        '85-89': 0,
        '80-84': 0,
        '<80': 0
    }

    for a in recent:
        score = a.get('score', 0)
        if score >= 95:
            score_dist['95-100'] += 1
        elif score >= 90:
            score_dist['90-94'] += 1
        elif score >= 85:
            score_dist['85-89'] += 1
        elif score >= 80:
            score_dist['80-84'] += 1
        else:
            score_dist['<80'] += 1

    # Par jour
    by_day = defaultdict(lambda: {'count': 0, 'total_score': 0})
    for a in recent:
        try:
            date_str = a.get('created_at', '')[:10]  # YYYY-MM-DD
            by_day[date_str]['count'] += 1
            by_day[date_str]['total_score'] += a.get('score', 0)
        except:
            pass

    alerts_per_day = []
    for day in sorted(by_day.keys(), reverse=True):
        count = by_day[day]['count']
        alerts_per_day.append({
            'date': day,
            'count': count,
            'avg_score': by_day[day]['total_score'] / count if count > 0 else 0
        })

    return jsonify({
        'total_alerts': total,
        'avg_score': round(avg_score, 1),
        'avg_liquidity': round(avg_liq, 0),
        'by_tier': dict(by_tier),
        'by_network': dict(by_network),
        'score_distribution': score_dist,
        'alerts_per_day': alerts_per_day
    })

@app.route('/api/recent', methods=['GET'])
def get_recent():
    """Alertes récentes (temps réel)."""
    alerts = load_alerts()
    limit = request.args.get('limit', type=int, default=10)

    # Tri par date décroissante
    alerts.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return jsonify({
        'alerts': alerts[:limit]
    })

@app.route('/api/networks', methods=['GET'])
def get_networks():
    """Stats par réseau."""
    alerts = load_alerts()
    days = request.args.get('days', type=int, default=7)

    # Filtre par date
    cutoff_date = datetime.now() - timedelta(days=days)
    recent = []

    for alert in alerts:
        try:
            alert_date = datetime.fromisoformat(alert.get('created_at', ''))
            if alert_date >= cutoff_date:
                recent.append(alert)
        except:
            pass

    # Par réseau
    by_network = defaultdict(lambda: {
        'total': 0,
        'total_score': 0,
        'total_liq': 0,
        'total_vol': 0,
        'scores': []
    })

    for a in recent:
        net = a.get('network', 'unknown')
        by_network[net]['total'] += 1
        by_network[net]['total_score'] += a.get('score', 0)
        by_network[net]['total_liq'] += a.get('liquidity', 0)
        by_network[net]['total_vol'] += a.get('volume_24h', 0)
        by_network[net]['scores'].append(a.get('score', 0))

    networks = []
    for net, data in by_network.items():
        count = data['total']
        if count > 0:
            networks.append({
                'network': net,
                'total': count,
                'avg_score': round(data['total_score'] / count, 1),
                'avg_liquidity': round(data['total_liq'] / count, 0),
                'avg_volume': round(data['total_vol'] / count, 0),
                'min_score': min(data['scores']),
                'max_score': max(data['scores'])
            })

    # Tri par total décroissant
    networks.sort(key=lambda x: x['total'], reverse=True)

    return jsonify({'networks': networks})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Scanner API démarrée sur port {port}")
    print(f"Fichier alertes: {ALERTS_FILE}")
    app.run(host='0.0.0.0', port=port, debug=False)
