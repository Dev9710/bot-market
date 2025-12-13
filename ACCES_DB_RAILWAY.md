# 📊 Accès à la Base de Données sur Railway

## 🎯 Problématique

Votre bot tourne sur Railway et sauvegarde les alertes dans `alerts_history.db`.
Comment consulter cette base de données depuis votre ordinateur ?

---

## 📥 Méthode 1 : Télécharger la DB via Railway CLI (Recommandé)

### Installation Railway CLI

```bash
# Windows (PowerShell en Admin)
iwr https://railway.app/install.ps1 | iex

# Ou avec npm
npm install -g @railway/cli
```

### Connexion à Railway

```bash
# Se connecter
railway login

# Lister vos projets
railway list

# Se connecter au projet du bot
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link
```

### Télécharger la Base de Données

```bash
# Se connecter au conteneur Railway
railway shell

# Dans le shell Railway, localiser la DB
ls -la *.db
# Devrait afficher: alerts_history.db

# Sortir du shell
exit

# Télécharger le fichier (depuis votre PC)
railway run cat alerts_history.db > alerts_history_downloaded.db
```

### Consulter la DB Téléchargée

```bash
# Option 1: DB Browser for SQLite (GUI)
# Télécharger depuis: https://sqlitebrowser.org/
# Ouvrir le fichier: alerts_history_downloaded.db

# Option 2: Ligne de commande
sqlite3 alerts_history_downloaded.db "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10;"
```

---

## 📡 Méthode 2 : API Webhook pour Consulter la DB

Créer un endpoint dans votre bot qui expose les données via une API.

### Créer l'API d'accès DB

Créez un nouveau fichier `db_api.py` :

```python
# -*- coding: utf-8 -*-
"""
API Flask pour consulter la base de données à distance
À déployer avec le bot sur Railway
"""

from flask import Flask, jsonify, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Port fourni par Railway
PORT = int(os.getenv("PORT", 8080))

# Clé API pour sécuriser (à mettre dans variables Railway)
API_KEY = os.getenv("DB_API_KEY", "votre_cle_secrete")

def get_db():
    """Connexion à la DB SQLite."""
    conn = sqlite3.connect('alerts_history.db')
    conn.row_factory = sqlite3.Row  # Pour avoir des résultats en dict
    return conn

def require_api_key(f):
    """Décorateur pour vérifier la clé API."""
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/health', methods=['GET'])
def health():
    """Health check."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/api/alerts', methods=['GET'])
@require_api_key
def get_alerts():
    """
    Récupère les alertes.
    Query params:
        - limit: nombre de résultats (défaut: 50)
        - offset: pagination (défaut: 0)
        - token: filtrer par nom de token
    """
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    token_filter = request.args.get('token', None)

    conn = get_db()
    cursor = conn.cursor()

    if token_filter:
        query = """
            SELECT * FROM alerts
            WHERE token_name LIKE ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, (f"%{token_filter}%", limit, offset))
    else:
        query = "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        cursor.execute(query, (limit, offset))

    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "count": len(alerts),
        "alerts": alerts
    })

@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
@require_api_key
def get_alert(alert_id):
    """Récupère une alerte spécifique avec son tracking."""
    conn = get_db()
    cursor = conn.cursor()

    # Alerte
    cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    alert = cursor.fetchone()

    if not alert:
        conn.close()
        return jsonify({"error": "Alert not found"}), 404

    # Tracking
    cursor.execute("""
        SELECT * FROM price_tracking
        WHERE alert_id = ?
        ORDER BY minutes_after_alert
    """, (alert_id,))
    tracking = [dict(row) for row in cursor.fetchall()]

    # Analyse
    cursor.execute("SELECT * FROM alert_analysis WHERE alert_id = ?", (alert_id,))
    analysis = cursor.fetchone()

    conn.close()

    return jsonify({
        "alert": dict(alert),
        "tracking": tracking,
        "analysis": dict(analysis) if analysis else None
    })

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Récupère les statistiques globales."""
    conn = get_db()
    cursor = conn.cursor()

    # Total alertes
    cursor.execute("SELECT COUNT(*) as total FROM alerts")
    total_alerts = cursor.fetchone()['total']

    # Alertes analysées
    cursor.execute("SELECT COUNT(*) as total FROM alert_analysis")
    analyzed = cursor.fetchone()['total']

    # ROI moyen
    cursor.execute("""
        SELECT AVG(roi_at_24h) as avg_roi
        FROM alert_analysis
        WHERE roi_at_24h IS NOT NULL
    """)
    avg_roi = cursor.fetchone()['avg_roi'] or 0

    # Taux TP1
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN tp1_was_hit = 1 THEN 1 END) * 100.0 / COUNT(*) as tp1_rate
        FROM alert_analysis
    """)
    tp1_rate = cursor.fetchone()['tp1_rate'] or 0

    conn.close()

    return jsonify({
        "total_alerts": total_alerts,
        "analyzed_alerts": analyzed,
        "avg_roi_24h": round(avg_roi, 2),
        "tp1_hit_rate": round(tp1_rate, 1)
    })

@app.route('/api/tokens', methods=['GET'])
@require_api_key
def get_tokens():
    """Liste tous les tokens trackés."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            token_name,
            token_address,
            network,
            COUNT(*) as alert_count,
            MAX(timestamp) as last_alert
        FROM alerts
        GROUP BY token_address
        ORDER BY last_alert DESC
    """)

    tokens = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "count": len(tokens),
        "tokens": tokens
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
```

### Déployer l'API sur Railway

```bash
# 1. Ajouter Flask aux dépendances
# Dans requirements.txt, ajouter:
flask==3.0.0

# 2. Créer un nouveau service Railway pour l'API
# Ou modifier le Procfile existant:
web: python db_api.py
worker: python geckoterminal_scanner_v2.py

# 3. Ajouter la variable d'environnement sur Railway
# DB_API_KEY=votre_cle_secrete_complexe

# 4. Déployer
railway up
```

### Utiliser l'API depuis votre PC

```python
# script_consulter_db.py
import requests

# URL de votre API Railway
API_URL = "https://votre-app.railway.app"
API_KEY = "votre_cle_secrete_complexe"

headers = {"X-API-Key": API_KEY}

# Récupérer les 10 dernières alertes
response = requests.get(f"{API_URL}/api/alerts?limit=10", headers=headers)
alerts = response.json()

print(f"Total: {alerts['count']} alertes")
for alert in alerts['alerts']:
    print(f"- {alert['token_name']}: Score {alert['score']}, Prix ${alert['price_at_alert']}")

# Récupérer les stats
response = requests.get(f"{API_URL}/api/stats", headers=headers)
stats = response.json()
print(f"\nStats: {stats}")
```

---

## 🗄️ Méthode 3 : Volume Persistant Railway + SFTP

Railway permet de monter un volume persistant et d'y accéder via SFTP.

### Configuration Railway Volume

```bash
# 1. Créer un volume persistant dans Railway Dashboard
# Settings → Volumes → Add Volume
# Mount Path: /data
# Size: 1GB (gratuit)

# 2. Modifier le code pour utiliser le volume
# Dans geckoterminal_scanner_v2.py et alert_tracker.py:
DB_PATH = os.getenv("DB_PATH", "/data/alerts_history.db")
# Au lieu de:
# DB_PATH = "alerts_history.db"
```

### Accès SFTP

```bash
# Railway expose un endpoint SFTP
railway sftp

# Télécharger la DB
sftp> get /data/alerts_history.db alerts_history_local.db
```

---

## 📊 Méthode 4 : Dashboard Web (Le Plus Élégant)

Créer un dashboard web hébergé sur Railway pour visualiser vos données.

### Créer un Dashboard Streamlit

Créez `dashboard.py` :

```python
# -*- coding: utf-8 -*-
"""
Dashboard Streamlit pour visualiser les alertes
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Bot Market Dashboard", page_icon="🚀", layout="wide")

@st.cache_resource
def get_connection():
    return sqlite3.connect('alerts_history.db', check_same_thread=False)

conn = get_connection()

st.title("🚀 Bot Market - Dashboard")

# Statistiques globales
col1, col2, col3, col4 = st.columns(4)

total_alerts = pd.read_sql("SELECT COUNT(*) as total FROM alerts", conn).iloc[0]['total']
analyzed = pd.read_sql("SELECT COUNT(*) as total FROM alert_analysis", conn).iloc[0]['total']
avg_roi = pd.read_sql("SELECT AVG(roi_at_24h) as avg FROM alert_analysis", conn).iloc[0]['avg'] or 0
tp1_rate = pd.read_sql("""
    SELECT COUNT(CASE WHEN tp1_was_hit = 1 THEN 1 END) * 100.0 / COUNT(*) as rate
    FROM alert_analysis
""", conn).iloc[0]['rate'] or 0

col1.metric("Total Alertes", total_alerts)
col2.metric("Analysées (24h+)", analyzed)
col3.metric("ROI Moyen 24h", f"{avg_roi:.2f}%")
col4.metric("Taux TP1", f"{tp1_rate:.1f}%")

# Tableau des alertes récentes
st.subheader("📊 Dernières Alertes")
recent = pd.read_sql("""
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
    LIMIT 50
""", conn)

st.dataframe(recent, use_container_width=True)

# Graphiques
st.subheader("📈 Performance des Alertes")

col1, col2 = st.columns(2)

with col1:
    # Distribution des scores
    scores = pd.read_sql("SELECT score FROM alerts", conn)
    fig = px.histogram(scores, x='score', nbins=20, title="Distribution des Scores")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # ROI par tranche de score
    roi_by_score = pd.read_sql("""
        SELECT
            CASE
                WHEN a.score >= 80 THEN '80-100'
                WHEN a.score >= 60 THEN '60-79'
                ELSE '0-59'
            END as score_range,
            AVG(an.roi_at_24h) as avg_roi
        FROM alerts a
        LEFT JOIN alert_analysis an ON a.id = an.alert_id
        WHERE an.roi_at_24h IS NOT NULL
        GROUP BY score_range
    """, conn)
    fig = px.bar(roi_by_score, x='score_range', y='avg_roi', title="ROI Moyen par Score")
    st.plotly_chart(fig, use_container_width=True)

# Détail d'une alerte
st.subheader("🔍 Détail d'une Alerte")
alert_id = st.number_input("ID de l'alerte", min_value=1, value=1)

if st.button("Charger"):
    alert = pd.read_sql(f"SELECT * FROM alerts WHERE id = {alert_id}", conn)
    tracking = pd.read_sql(f"SELECT * FROM price_tracking WHERE alert_id = {alert_id}", conn)
    analysis = pd.read_sql(f"SELECT * FROM alert_analysis WHERE alert_id = {alert_id}", conn)

    if not alert.empty:
        st.json(alert.iloc[0].to_dict())

        if not tracking.empty:
            st.line_chart(tracking[['minutes_after_alert', 'roi_percent']].set_index('minutes_after_alert'))

        if not analysis.empty:
            st.success(f"Qualité: {analysis.iloc[0]['prediction_quality']}")
            st.write(analysis.iloc[0].to_dict())
```

### Déployer le Dashboard

```bash
# requirements.txt
streamlit==1.29.0
plotly==5.18.0
pandas==2.1.4

# Procfile
web: streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0
worker: python geckoterminal_scanner_v2.py

# Déployer
railway up
```

Votre dashboard sera accessible sur `https://votre-app.railway.app` !

---

## 🎯 Méthode Recommandée par Scénario

| Scénario | Méthode Recommandée |
|----------|---------------------|
| Consultation ponctuelle | Railway CLI + DB Browser |
| Accès programmatique | API REST (Méthode 2) |
| Visualisation | Dashboard Streamlit (Méthode 4) |
| Automatisation | API REST + Scripts Python |

---

## 🔒 Sécurité

### Pour l'API REST
- ✅ Utiliser une clé API forte (variable d'environnement)
- ✅ Activer HTTPS uniquement (Railway le fait automatiquement)
- ✅ Rate limiting si accès public
- ✅ Ne jamais exposer la clé API dans le code

### Pour le Dashboard
- ✅ Ajouter authentification (Streamlit auth ou Basic Auth)
- ✅ Restreindre l'accès par IP si possible
- ✅ Utiliser variables d'environnement Railway

---

## 📱 Accès Mobile

Avec le Dashboard Streamlit ou l'API REST, vous pouvez accéder à vos données depuis :
- 📱 Smartphone (navigateur web)
- 💻 Ordinateur
- 📊 Scripts automatisés
- 🔔 Webhooks externes

---

## ✅ Checklist

- [ ] Installer Railway CLI
- [ ] Se connecter au projet Railway
- [ ] Choisir méthode d'accès (API / Dashboard)
- [ ] Déployer les composants
- [ ] Configurer variables d'environnement
- [ ] Tester l'accès depuis votre PC
- [ ] Documenter l'URL et clé API

---

**Recommandation** : Commencez par le **Dashboard Streamlit** (Méthode 4) - c'est le plus simple et le plus visuel !