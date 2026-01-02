# 🚀 Démarrage Rapide - Dashboard V3

Guide ultra-simplifié pour lancer le dashboard et voir tes alertes.

---

## Option 1: Test Immédiat avec Données Railway (RECOMMANDÉ)

### Étape 1: Déployer l'API sur Railway

1. **Aller sur Railway Dashboard**: https://railway.app

2. **Créer un nouveau service**:
   - Cliquer sur "+ New"
   - Sélectionner "GitHub Repo"
   - Choisir ton repo `bot-market`

3. **Configurer le service**:
   ```
   Nom du service: dashboard-api

   Build Command: (laisser vide, détecté auto)
   Start Command: python railway_db_api.py

   Variables d'environnement:
   PORT=5000
   DB_PATH=/data/alerts_history.db
   ```

4. **Monter le volume** (IMPORTANT):
   - Settings → Volumes
   - Cliquer "Mount Volume"
   - Sélectionner le volume existant `/data` (celui du scanner)
   - Mount Path: `/data`

5. **Déployer**:
   - Railway va build et démarrer automatiquement
   - Une URL sera générée: `https://dashboard-api-production-xxxx.up.railway.app`

### Étape 2: Configurer le Frontend

1. **Récupérer l'URL de l'API**:
   - Dans Railway → dashboard-api → Settings → Networking
   - Copier l'URL publique

2. **Modifier le dashboard**:
   - Ouvrir `dashboard_frontend.html` dans un éditeur
   - Ligne 293, remplacer:
   ```javascript
   API_URL: 'http://localhost:5000/api',
   ```
   Par:
   ```javascript
   API_URL: 'https://dashboard-api-production-xxxx.up.railway.app/api',
   ```

3. **Ouvrir dans le navigateur**:
   ```bash
   # Windows
   start dashboard_frontend.html

   # OU double-cliquer sur le fichier
   ```

### Étape 3: Vérifier

✅ **Stats s'affichent** (Total alertes, score moyen, etc.)
✅ **Graphiques chargent** (Distribution scores, réseaux, timeline)
✅ **Table montre les alertes** avec toutes tes vraies alertes Railway

**C'est tout!** 🎉

---

## Option 2: Test Local (Si DB locale existe)

### Si tu as déjà une base de données locale

1. **Double-cliquer sur** `start_dashboard.bat`

   Ou manuellement:

   ```bash
   # Terminal 1: API
   python railway_db_api.py

   # Terminal 2: Frontend
   start dashboard_frontend.html
   ```

2. **Le dashboard s'ouvre automatiquement** sur `http://localhost:5000`

3. **Vérifier** que les données chargent

---

## ✅ Vérification Rapide

### Tester l'API

Ouvrir dans le navigateur:
```
https://your-api.railway.app/api/health
```

Devrait afficher:
```json
{
  "status": "ok",
  "total_alerts": 4252,
  "db_path": "/data/alerts_history.db"
}
```

### Dashboard Fonctionne?

- [ ] Cartes de stats en haut affichent des chiffres
- [ ] 3 graphiques s'affichent (barres, donut, ligne)
- [ ] Table en bas montre des alertes
- [ ] Filtres fonctionnent (changer la période, réseau, etc.)

---

## 🔧 Troubleshooting

### ❌ "0 alertes" dans le dashboard

**Problème**: L'API ne trouve pas la DB

**Solution Railway**:
1. Vérifier que le volume `/data` est monté sur `dashboard-api`
2. Railway Shell: `ls -la /data/alerts_history.db`
3. Vérifier que c'est le MÊME volume que le scanner

**Solution Local**:
1. Vérifier que `alerts_tracker.db` existe dans le dossier
2. Si non, lancer le scanner une fois: `python geckoterminal_scanner_v3.py`

### ❌ "Cannot connect to API"

**Problème**: URL API incorrecte

**Solution**:
1. Vérifier l'URL dans `dashboard_frontend.html` ligne 293
2. Tester l'URL dans le navigateur: `/api/health`
3. Vérifier qu'il n'y a pas de `/` en trop

### ❌ Graphiques ne s'affichent pas

**Problème**: Connexion internet (Chart.js chargé depuis CDN)

**Solution**:
- Vérifier la connexion internet
- Ouvrir Console navigateur (F12) → voir les erreurs

---

## 📊 Endpoints Disponibles

Une fois l'API déployée:

| Endpoint | Description | Exemple |
|----------|-------------|---------|
| `/api/health` | Status de l'API | `total_alerts: 4252` |
| `/api/stats?days=7` | Stats 7 derniers jours | Distribution, moyennes |
| `/api/alerts?network=eth` | Alertes filtrées | Par réseau, score, etc. |
| `/api/recent?limit=10` | 10 dernières alertes | Temps réel |
| `/api/networks` | Stats par réseau | ETH, BASE, BSC, SOLANA |

**Tester dans le navigateur**:
```
https://your-api.railway.app/api/stats?days=30
```

---

## 🎯 Prochaines Étapes

### Court Terme

- [x] API déployée sur Railway
- [x] Frontend configuré
- [ ] Vérifier que les nouvelles alertes apparaissent
- [ ] Monitorer pendant 1 semaine

### Améliorations Possibles

- [ ] Déployer frontend sur Vercel (au lieu de local)
- [ ] Ajouter authentification
- [ ] Notifications email
- [ ] Export CSV

---

## 📝 Récapitulatif

**Ce qui a été fait**:
1. ✅ API qui lit directement la DB Railway
2. ✅ Frontend dashboard avec graphiques
3. ✅ Script de démarrage rapide (.bat)
4. ✅ Guide de déploiement simplifié

**Pour démarrer**:
1. Déployer `railway_db_api.py` sur Railway
2. Monter le volume `/data` (MÊME que scanner)
3. Modifier URL API dans `dashboard_frontend.html`
4. Ouvrir le dashboard dans le navigateur

**Temps estimé**: 10 minutes ⏱️

---

## 🆘 Support

**Logs Railway**:
```bash
railway logs --service dashboard-api
```

**Railway Shell**:
```bash
railway shell --service dashboard-api
ls -la /data/
```

**Tester API localement**:
```bash
curl http://localhost:5000/api/health
```

---

**Dashboard prêt à l'emploi! 🚀**
