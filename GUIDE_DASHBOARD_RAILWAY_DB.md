# Dashboard avec Base de Données Railway - Guide Simplifié

## 🎯 Architecture Finale

```
┌─────────────────────────────────────────────────────────┐
│                      RAILWAY                             │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────┐      ┌────────────────────┐  │
│  │  Service 1:          │      │  Service 2:        │  │
│  │  Scanner V3          │      │  Dashboard API     │  │
│  │                      │      │                    │  │
│  │  Écrit dans:         │      │  Lit depuis:       │  │
│  │  alerts_history.db ─────────▶  alerts_history.db │  │
│  │  (via AlertTracker)  │      │  (via SQLite)      │  │
│  │                      │      │                    │  │
│  │                      │      │  Port: 5000        │  │
│  │                      │      │  railway_db_api.py │  │
│  └──────────────────────┘      └────────────────────┘  │
│              │                           │              │
│              └───────────┬───────────────┘              │
│                          ▼                              │
│               ┌──────────────────────┐                 │
│               │  Railway Volume      │                 │
│               │  /data               │                 │
│               │  alerts_history.db   │                 │
│               └──────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS API
                          ▼
              ┌─────────────────────────┐
              │  Frontend Dashboard     │
              │  (Local ou Vercel)      │
              │  dashboard_frontend.html│
              └─────────────────────────┘
```

**Avantages**:
- ✅ Utilise la **vraie** base de données Railway existante
- ✅ Pas besoin de JSON intermédiaire
- ✅ Toutes les alertes historiques disponibles
- ✅ Données en temps réel depuis le scanner

---

## 📋 Étape 1: Préparer les Fichiers

### Fichiers à Déployer sur Railway

**Service 1 - Scanner V3** (déjà déployé):
- Pas de modification nécessaire
- Continue d'écrire dans `alerts_history.db` via `AlertTracker`

**Service 2 - Dashboard API** (NOUVEAU):
- `railway_db_api.py` ← **Ce fichier lit la DB directement**
- `requirements_dashboard.txt`

---

## 📦 Étape 2: Déployer l'API Dashboard sur Railway

### Via Railway Dashboard Web

1. **Créer un nouveau service**:
   - Nom: `dashboard-api`
   - Lier au même repo GitHub que le scanner

2. **Configuration du service**:
   ```
   Build Command: pip install -r requirements_dashboard.txt
   Start Command: python railway_db_api.py
   ```

3. **Variables d'environnement**:
   ```
   PORT=5000
   DB_PATH=/data/alerts_history.db
   ```

4. **⚠️ IMPORTANT: Monter le MÊME volume que le scanner**:
   - Aller dans Settings → Volumes
   - Monter le volume existant `/data`
   - Cela permettra d'accéder à `alerts_history.db` écrit par le scanner

5. **Exposer le port**:
   - Railway génère automatiquement une URL publique
   - Format: `https://dashboard-api-production-xxxx.up.railway.app`

### Via Railway CLI

```bash
# Se connecter
railway login

# Créer nouveau service
railway init

# Lier au projet
railway link

# Déployer
railway up
```

---

## ✅ Étape 3: Vérifier que ça Fonctionne

### 1. Vérifier les logs de l'API

Dans Railway Dashboard → Service `dashboard-api` → Logs:

```
✅ Base de données connectée: /data/alerts_history.db
   4252 alertes disponibles

🚀 Railway DB API démarrée sur port 5000
📊 Endpoints disponibles:
   GET /api/health
   GET /api/alerts
   GET /api/stats
   ...
```

### 2. Tester l'API

Récupérer l'URL Railway de l'API (Settings → Networking):
```
https://dashboard-api-production-xxxx.up.railway.app
```

Tester le health check:
```bash
curl https://dashboard-api-production-xxxx.up.railway.app/api/health
```

Devrait retourner:
```json
{
  "status": "ok",
  "timestamp": "2025-01-15T10:30:00",
  "total_alerts": 4252,
  "db_path": "/data/alerts_history.db"
}
```

### 3. Tester les endpoints

```bash
# Stats globales
curl https://your-api.railway.app/api/stats?days=7

# Alertes récentes
curl https://your-api.railway.app/api/recent?limit=5

# Alertes filtrées
curl "https://your-api.railway.app/api/alerts?network=eth&min_score=90"
```

---

## 🖥️ Étape 4: Configurer le Frontend

### Option A: Local (Test Rapide)

1. **Modifier l'URL de l'API** dans `dashboard_frontend.html` (ligne ~293):
   ```javascript
   data() {
       return {
           API_URL: 'https://dashboard-api-production-xxxx.up.railway.app/api',
           // ... reste du code
   ```

2. **Ouvrir dans le navigateur**:
   ```bash
   start dashboard_frontend.html
   ```

3. **Vérifier que les données s'affichent**:
   - Stats globales
   - Graphiques
   - Table des alertes

### Option B: Vercel/Netlify (Production)

1. **Modifier l'URL de l'API** dans `dashboard_frontend.html`

2. **Renommer le fichier**:
   ```bash
   cp dashboard_frontend.html index.html
   ```

3. **Déployer sur Vercel**:
   ```bash
   vercel
   ```

4. **Ou drag & drop sur Netlify**:
   - Aller sur netlify.com
   - Drag & drop `index.html`
   - Publier

5. **Accéder au dashboard**:
   ```
   https://scanner-dashboard.vercel.app
   ```

---

## 🔍 Étape 5: Monitoring

### Vérifier les Données en Temps Réel

1. **Scanner génère des alertes**:
   - Surveiller Telegram pour nouvelles alertes
   - Vérifier logs Scanner Railway

2. **Alertes sauvegardées dans DB**:
   ```
   💾 Sauvegardé en DB (ID: 4253) - Tracking auto démarré
   ```

3. **API retourne les données**:
   - Rafraîchir `/api/health` → total_alerts augmente
   - `/api/recent` → nouvelles alertes apparaissent

4. **Dashboard se met à jour**:
   - Auto-refresh toutes les 60s
   - Nouvelles alertes en haut du tableau
   - Stats/graphiques actualisés

---

## 🎨 Personnalisation du Dashboard

### Changer l'intervalle de rafraîchissement

Dans `dashboard_frontend.html` (ligne ~295):
```javascript
mounted() {
    this.loadData();
    setInterval(() => this.loadData(), 60000); // 60s ← Changer ici
}
```

### Modifier les filtres par défaut

```javascript
data() {
    return {
        // ...
        filterDays: 7,      // ← Période par défaut
        pageSize: 20,       // ← Alertes par page
    }
}
```

### Ajouter des métriques

Dans `railway_db_api.py`, endpoint `/api/stats`:
```python
# Ajouter une nouvelle métrique
cursor = conn.execute("""
    SELECT AVG(velocite_pump) as avg_vel
    FROM alerts
    WHERE created_at >= ?
""", [cutoff_date])

stats['avg_velocity'] = cursor.fetchone()['avg_vel']
```

Puis dans le frontend:
```html
<div class="bg-gray-800 p-6 rounded-lg">
    <div class="text-gray-400 text-sm">Vélocité Moyenne</div>
    <div class="text-3xl font-bold">{{ stats.avg_velocity }}</div>
</div>
```

---

## ⚠️ Troubleshooting

### ❌ "total_alerts: 0" dans /api/health

**Problème**: Volume pas monté ou DB vide

**Solutions**:
1. Vérifier que le volume `/data` est bien monté
2. Railway Shell API: `ls -la /data/alerts_history.db`
3. Vérifier que le scanner a créé la DB
4. Railway Shell Scanner: `ls -la /data/alerts_history.db`

### ❌ "Database not found"

**Problème**: Chemin DB incorrect

**Solutions**:
1. Vérifier `DB_PATH` dans les variables d'environnement: `/data/alerts_history.db`
2. Vérifier que les 2 services montent le **même** volume
3. Railway Dashboard → Volumes → Vérifier le mount path

### ❌ CORS Error dans le navigateur

**Problème**: Frontend ne peut pas appeler l'API

**Solutions**:
- `flask-cors` est installé (déjà dans requirements_dashboard.txt)
- Vérifier que l'URL de l'API est correcte
- Tester l'API avec `curl` pour isoler le problème

### ❌ Dashboard ne charge pas les données

**Checklist**:
1. ✅ API fonctionne: `/api/health` retourne 200
2. ✅ URL API correcte dans le HTML
3. ✅ Console navigateur (F12) → pas d'erreurs
4. ✅ Network tab → requêtes API en 200

---

## 📊 Structure Finale Railway

```
Railway Project: scanner-v3-ultra-rentable
├── Service 1: scanner-v3
│   ├── Command: python geckoterminal_scanner_v3.py
│   ├── Volume: /data
│   └── Writes: /data/alerts_history.db
│
├── Service 2: dashboard-api
│   ├── Command: python railway_db_api.py
│   ├── Volume: /data (MÊME que Service 1)
│   ├── Reads: /data/alerts_history.db
│   └── Port: 5000 (Public URL)
│
└── Volume: /data
    └── alerts_history.db (4252+ alertes)
```

---

## 🚀 Résumé des Commandes

### Tester l'API Railway

```bash
# Health check
curl https://your-api.railway.app/api/health

# Stats 7 derniers jours
curl https://your-api.railway.app/api/stats?days=7

# 10 alertes récentes
curl https://your-api.railway.app/api/recent?limit=10

# Alertes ETH score >90
curl "https://your-api.railway.app/api/alerts?network=eth&min_score=90"

# Stats par réseau
curl https://your-api.railway.app/api/networks?days=30
```

### Railway CLI

```bash
# Logs temps réel
railway logs --service dashboard-api

# Shell
railway shell --service dashboard-api

# Vérifier DB
railway run --service dashboard-api ls -la /data/
```

---

## ✅ Checklist Finale

### Déploiement

- [ ] Service `dashboard-api` créé sur Railway
- [ ] `railway_db_api.py` déployé
- [ ] `requirements_dashboard.txt` présent
- [ ] Variable `DB_PATH=/data/alerts_history.db`
- [ ] Volume `/data` monté (MÊME que scanner)
- [ ] Port 5000 exposé publiquement

### Vérification

- [ ] `/api/health` retourne status ok + total_alerts
- [ ] `/api/stats` retourne statistiques
- [ ] `/api/recent` retourne alertes
- [ ] URL Railway notée quelque part

### Frontend

- [ ] `dashboard_frontend.html` modifié avec URL Railway
- [ ] Ouvert dans navigateur → données chargent
- [ ] Graphiques s'affichent
- [ ] Filtres fonctionnent
- [ ] Auto-refresh actif

---

## 🎯 Prochaines Étapes

1. ✅ API déployée et connectée à la DB
2. ✅ Frontend configuré avec URL Railway
3. ⏳ Monitoring pendant 1 semaine
4. ⏳ Ajustements selon besoins

**Dashboard connecté à la vraie DB Railway! 🎉**
