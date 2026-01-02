# 📊 Dashboard Scanner V3 - README

Dashboard web pour visualiser les alertes du scanner V3 en temps réel.

---

## 🎯 Ce que c'est

Un dashboard moderne qui affiche:
- **Stats globales**: Total alertes, score moyen, liquidité moyenne
- **Graphiques**: Distribution scores, alertes par réseau, timeline
- **Table des alertes**: Toutes tes alertes avec filtres
- **Temps réel**: Auto-refresh toutes les 60 secondes

**Données**: Directement depuis ta base de données Railway ✅

---

## 🚀 Démarrage Rapide (3 étapes)

### 1. Déployer l'API sur Railway

**Fichier**: `railway_db_api.py`

```bash
# Railway Dashboard
1. New Service
2. Link to GitHub repo
3. Start Command: python railway_db_api.py
4. Variables: DB_PATH=/data/alerts_history.db
5. Mount Volume: /data (MÊME que le scanner)
```

### 2. Configurer le Frontend

**Fichier**: `dashboard_frontend.html`

Ligne 293, modifier:
```javascript
API_URL: 'https://your-railway-api.up.railway.app/api',
```

### 3. Ouvrir le Dashboard

```bash
start dashboard_frontend.html
```

**C'est tout!** 🎉

---

## 📁 Fichiers Importants

| Fichier | Description | Déploiement |
|---------|-------------|-------------|
| `railway_db_api.py` | API REST qui lit la DB | Railway |
| `dashboard_frontend.html` | Interface web | Local ou Vercel |
| `requirements_dashboard.txt` | Dépendances (Flask) | Railway |
| `start_dashboard.bat` | Script démarrage local | Local Windows |

---

## 📚 Guides Disponibles

| Guide | Pour Quoi |
|-------|-----------|
| [DEMARRAGE_RAPIDE_DASHBOARD.md](DEMARRAGE_RAPIDE_DASHBOARD.md) | **Lancer le dashboard (10 min)** ⭐ |
| [GUIDE_DASHBOARD_RAILWAY_DB.md](GUIDE_DASHBOARD_RAILWAY_DB.md) | Déploiement Railway détaillé |
| [DASHBOARD_README.md](DASHBOARD_README.md) | Documentation complète API |

**Commencer par**: [DEMARRAGE_RAPIDE_DASHBOARD.md](DEMARRAGE_RAPIDE_DASHBOARD.md) ⭐

---

## 🔍 Aperçu

### Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Scanner V3 - Dashboard              [7 jours ▼] [🔄]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Total    │  │ Score    │  │ Liquidité│  │ Qualité  │   │
│  │ 244      │  │ 95.9     │  │ $412K    │  │ HIGH 72% │   │
│  │ 2.7/jour │  │ EXCELLENT│  │          │  │ MED  28% │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Distribution Score │  │ Alertes par Réseau │            │
│  │ [Graphique Barres] │  │ [Graphique Donut]  │            │
│  └────────────────────┘  └────────────────────┘            │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Timeline - Alertes/Jour [Graphique Ligne]            │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                               │
│  Filtres: [ETH ▼] [HIGH ▼] [Score 90+]  [Reset]            │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Date     │ Token │ Réseau │ Score │ Tier │ Liquidité   ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ 15/01 10h│ EXM   │ ETH    │  96   │ HIGH │ $350K       ││
│  │ 15/01 12h│ SGEM  │ SOLANA │  98   │ULTRA │ $180K   👁️ ││
│  │ 14/01 08h│ BPRO  │ BASE   │  94   │ HIGH │ $2.1M       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
│  [Précédent] [Suivant]                    Affichage 20/244  │
└─────────────────────────────────────────────────────────────┘
```

### API Endpoints

```bash
# Health check
GET /api/health
→ {"status": "ok", "total_alerts": 244}

# Stats globales
GET /api/stats?days=7
→ {score_distribution, by_network, alerts_per_day}

# Alertes filtrées
GET /api/alerts?network=eth&min_score=90
→ {alerts: [...], total: 103}

# Alertes récentes
GET /api/recent?limit=5
→ {alerts: [dernières 5 alertes]}

# Stats par réseau
GET /api/networks?days=30
→ {networks: [ETH, BASE, BSC, SOLANA]}
```

---

## ⚙️ Configuration

### Changer la Période par Défaut

`dashboard_frontend.html` ligne ~288:
```javascript
filterDays: 7,  // 1, 7, 30, ou 90
```

### Modifier l'Auto-Refresh

Ligne ~295:
```javascript
setInterval(() => this.loadData(), 60000);  // 60s
```

### Alertes par Page

Ligne ~291:
```javascript
pageSize: 20,  // Nombre d'alertes par page
```

---

## 🎨 Personnalisation

### Ajouter un Graphique

```javascript
// dashboard_frontend.html
const ctx = document.getElementById('newChart');
new Chart(ctx, {
    type: 'bar',  // 'line', 'doughnut', 'pie'
    data: { ... },
    options: { ... }
});
```

### Ajouter une Métrique

```python
# railway_db_api.py, endpoint /api/stats
cursor = conn.execute("""
    SELECT AVG(nouvelle_colonne) as new_metric
    FROM alerts
""")
stats['new_metric'] = cursor.fetchone()['new_metric']
```

---

## 🔧 Troubleshooting

| Problème | Solution |
|----------|----------|
| Dashboard vide | Vérifier URL API ligne 293 |
| "Cannot connect" | Tester `/api/health` dans navigateur |
| CORS error | Déjà configuré dans `railway_db_api.py` |
| 0 alertes | Vérifier volume `/data` monté sur Railway |
| Graphiques ne chargent pas | Vérifier connexion internet (CDN) |

**Logs Railway**:
```bash
railway logs --service dashboard-api
```

---

## 📊 Architecture

```
Railway:
  Scanner V3 → writes → /data/alerts_history.db
                          ↓
  API Dashboard → reads → /data/alerts_history.db
                          ↓
                       REST API
                          ↓
Frontend (Local/Vercel) → consumes → API
```

---

## ✅ Checklist Déploiement

- [ ] `railway_db_api.py` déployé sur Railway
- [ ] Variable `DB_PATH=/data/alerts_history.db`
- [ ] Volume `/data` monté (MÊME que scanner)
- [ ] Port 5000 exposé
- [ ] URL API récupérée
- [ ] `dashboard_frontend.html` modifié avec URL
- [ ] Dashboard ouvert → données visibles
- [ ] Filtres testés
- [ ] Auto-refresh fonctionne

---

## 🆘 Support

**Guides**:
- ⭐ [DEMARRAGE_RAPIDE_DASHBOARD.md](DEMARRAGE_RAPIDE_DASHBOARD.md) - START HERE
- 📖 [GUIDE_DASHBOARD_RAILWAY_DB.md](GUIDE_DASHBOARD_RAILWAY_DB.md) - Détails Railway
- 📚 [DASHBOARD_README.md](DASHBOARD_README.md) - Documentation API complète

**Tests**:
```bash
# API locale
python railway_db_api.py
curl http://localhost:5000/api/health

# Dashboard local
start dashboard_frontend.html
```

---

## 🎯 Résumé

**En 3 Fichiers**:
1. `railway_db_api.py` → Déployer sur Railway
2. `dashboard_frontend.html` → Modifier URL API, ouvrir
3. `requirements_dashboard.txt` → Dépendances auto

**Temps**: 10 minutes ⏱️

**Résultat**: Dashboard temps réel avec toutes tes alertes Railway 🎉

---

**Questions?** Voir [DEMARRAGE_RAPIDE_DASHBOARD.md](DEMARRAGE_RAPIDE_DASHBOARD.md) ⭐
