# Déploiement Dashboard sur Railway avec CLI

Guide complet utilisant Railway CLI pour déployer le dashboard API.

**Docs Railway CLI**: https://docs.railway.com/guides/cli

---

## 📋 Prérequis

- Railway CLI installée
- Compte Railway
- Projet Railway existant (où tourne déjà le scanner V3)

---

## Étape 1: Installer Railway CLI

### Windows

```powershell
# Via PowerShell
iwr https://railway.app/install.ps1 | iex
```

Ou télécharger: https://github.com/railwayapp/cli/releases

### Vérifier l'installation

```bash
railway --version
# Devrait afficher: railway version x.x.x
```

---

## Étape 2: Se Connecter à Railway

```bash
# Login Railway
railway login
```

Une fenêtre de navigateur s'ouvre pour l'authentification.

---

## Étape 3: Lier au Projet Railway

### Option A: Si tu es dans le dossier du projet

```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Lier au projet existant
railway link
```

Sélectionner le projet où tourne déjà le scanner V3.

### Option B: Spécifier le projet directement

```bash
# Lister tes projets
railway list

# Lier à un projet spécifique
railway link [project-id]
```

---

## Étape 4: Créer un Nouveau Service pour l'API Dashboard

Railway CLI ne peut pas créer de nouveaux services directement. On va utiliser le Dashboard web pour créer le service, puis CLI pour déployer.

### Via Railway Dashboard Web

1. **Aller sur**: https://railway.app/dashboard
2. **Ouvrir ton projet** (où tourne le scanner)
3. **Cliquer sur** "+ New Service"
4. **Sélectionner** "Empty Service"
5. **Nommer**: `dashboard-api`

---

## Étape 5: Créer le Fichier de Configuration Railway

Dans le dossier du projet, créer `railway.toml`:

```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market
```

Créer le fichier `railway.toml`:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python railway_db_api.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

---

## Étape 6: Configurer les Variables d'Environnement

### Via CLI

```bash
# Se positionner sur le service dashboard-api
railway service

# Sélectionner "dashboard-api" dans la liste

# Définir les variables
railway variables set PORT=5000
railway variables set DB_PATH=/data/alerts_history.db

# Vérifier
railway variables
```

### Via Dashboard Web (Alternative)

1. Service `dashboard-api` → Variables
2. Ajouter:
   ```
   PORT=5000
   DB_PATH=/data/alerts_history.db
   ```

---

## Étape 7: Monter le Volume Partagé

⚠️ **CRITIQUE**: Le volume doit être le MÊME que celui du scanner pour accéder à `alerts_history.db`

### Via Railway Dashboard Web (Recommandé)

1. Service `dashboard-api` → Settings → Volumes
2. Click "Add Volume"
3. **Sélectionner le volume existant** (celui du scanner)
4. Mount Path: `/data`
5. Save

### Vérifier les Volumes

```bash
# Lister les volumes du projet
railway volumes list
```

---

## Étape 8: Déployer l'API

### Déployer depuis le dossier local

```bash
# S'assurer d'être sur le bon service
railway service
# Sélectionner "dashboard-api"

# Déployer
railway up
```

Railway va:
1. Détecter `requirements_dashboard.txt`
2. Installer Flask et Flask-CORS
3. Lancer `python railway_db_api.py`

### Voir les Logs en Temps Réel

```bash
railway logs
```

Tu devrais voir:
```
✅ Base de données connectée: /data/alerts_history.db
   4252 alertes disponibles

🚀 Railway DB API démarrée sur port 5000
📊 Endpoints disponibles:
   GET /api/health
   GET /api/alerts
   ...
```

---

## Étape 9: Obtenir l'URL Publique

### Via CLI

```bash
# Générer un domaine public
railway domain
```

Cela génère une URL comme:
```
https://dashboard-api-production-xxxx.up.railway.app
```

### Via Dashboard Web

Service `dashboard-api` → Settings → Networking → Generate Domain

---

## Étape 10: Tester l'API

### Tester le Health Check

```bash
# Récupérer l'URL
railway domain

# Tester (remplacer par ton URL)
curl https://dashboard-api-production-xxxx.up.railway.app/api/health
```

Réponse attendue:
```json
{
  "status": "ok",
  "timestamp": "2025-01-15T10:30:00",
  "total_alerts": 4252,
  "db_path": "/data/alerts_history.db"
}
```

### Tester les Stats

```bash
curl https://your-api.railway.app/api/stats?days=7
```

### Tester les Alertes

```bash
curl "https://your-api.railway.app/api/alerts?limit=5"
```

---

## Étape 11: Configurer le Frontend

### 1. Récupérer l'URL de l'API

```bash
railway domain
# Copier l'URL affichée
```

### 2. Modifier dashboard_frontend.html

Ouvrir `dashboard_frontend.html` et modifier ligne 293:

```javascript
API_URL: 'https://dashboard-api-production-xxxx.up.railway.app/api',
```

### 3. Tester localement

```bash
start dashboard_frontend.html
```

Le dashboard devrait charger avec toutes tes alertes Railway! 🎉

---

## 🔧 Commandes Railway CLI Utiles

### Logs

```bash
# Logs en temps réel
railway logs

# Logs des 100 dernières lignes
railway logs --limit 100
```

### Variables

```bash
# Lister les variables
railway variables

# Ajouter une variable
railway variables set KEY=value

# Supprimer une variable
railway variables delete KEY
```

### Service

```bash
# Changer de service
railway service

# Lister les services
railway status
```

### Shell

```bash
# Accéder au shell du service
railway shell

# Dans le shell:
ls -la /data/
cat /data/alerts_history.db | wc -c
```

### Redéployer

```bash
# Redéployer après modifications
railway up

# Forcer un nouveau build
railway up --detach
```

### Volumes

```bash
# Lister les volumes
railway volumes list

# Détails d'un volume
railway volumes info [volume-id]
```

---

## 📊 Vérifications Post-Déploiement

### 1. Service Démarre Correctement

```bash
railway logs
```

Chercher:
```
✅ Base de données connectée
🚀 Railway DB API démarrée sur port 5000
```

### 2. Volume Monté

```bash
railway shell
ls -la /data/alerts_history.db
```

Devrait afficher le fichier DB.

### 3. API Accessible

```bash
curl $(railway domain)/api/health
```

Devrait retourner `"status": "ok"`

### 4. Frontend Fonctionne

Ouvrir `dashboard_frontend.html` → données visibles

---

## 🐛 Troubleshooting

### ❌ "Database not found"

**Problème**: Volume pas monté

**Solution**:
```bash
# Vérifier les volumes
railway volumes list

# Vérifier le mount dans le shell
railway shell
ls -la /data/
```

Si `/data/` est vide:
1. Railway Dashboard → dashboard-api → Volumes
2. Vérifier que le volume est bien monté
3. Redéployer: `railway up`

### ❌ "Port already in use"

**Problème**: Variable PORT mal configurée

**Solution**:
```bash
railway variables set PORT=5000
railway up
```

### ❌ Build Failed

**Problème**: Dependencies manquantes

**Solution**:
Vérifier que `requirements_dashboard.txt` existe:
```bash
cat requirements_dashboard.txt
# Devrait contenir:
# flask==3.0.0
# flask-cors==4.0.0
```

### ❌ CORS Error

**Déjà configuré** dans `railway_db_api.py` avec `CORS(app)`

Si problème persiste:
```bash
# Vérifier les logs
railway logs

# Chercher des erreurs CORS
```

---

## 🔄 Workflow de Développement

### Modifier et Redéployer

```bash
# 1. Modifier railway_db_api.py localement

# 2. Tester localement
python railway_db_api.py

# 3. Déployer sur Railway
railway up

# 4. Vérifier les logs
railway logs
```

### Tester en Local avec Railway Vars

```bash
# Charger les variables Railway localement
railway run python railway_db_api.py
```

Cela charge automatiquement les variables d'environnement de Railway.

---

## 📁 Structure Finale

```
Railway Project: scanner-v3-ultra-rentable
│
├── Service: scanner-v3
│   ├── Command: python geckoterminal_scanner_v3.py
│   ├── Volume: /data
│   └── Writes: /data/alerts_history.db
│
├── Service: dashboard-api ← NOUVEAU
│   ├── Command: python railway_db_api.py
│   ├── Volume: /data (partagé avec scanner-v3)
│   ├── Reads: /data/alerts_history.db
│   ├── Port: 5000
│   └── Public URL: https://dashboard-api-production-xxxx.up.railway.app
│
└── Volume: /data
    └── alerts_history.db (4252+ alertes)
```

---

## 📝 Checklist Déploiement CLI

### Installation

- [ ] Railway CLI installée (`railway --version`)
- [ ] Connecté à Railway (`railway login`)
- [ ] Projet lié (`railway link`)

### Configuration Service

- [ ] Service `dashboard-api` créé (via web)
- [ ] `railway.toml` créé
- [ ] Variables définies (`PORT`, `DB_PATH`)
- [ ] Volume `/data` monté (via web)

### Déploiement

- [ ] Code déployé (`railway up`)
- [ ] Logs vérifiés (`railway logs`)
- [ ] DB accessible (`railway shell` → `ls /data/`)
- [ ] Domaine généré (`railway domain`)

### Tests

- [ ] `/api/health` retourne 200
- [ ] `/api/stats` retourne données
- [ ] Frontend modifié avec URL
- [ ] Dashboard affiche alertes

---

## 🚀 Commandes Rapides

```bash
# Déploiement complet
railway login
railway link
railway service  # Sélectionner dashboard-api
railway variables set PORT=5000
railway variables set DB_PATH=/data/alerts_history.db
railway up
railway domain

# Monitoring
railway logs
railway status
railway shell

# Frontend
# 1. Copier l'URL de "railway domain"
# 2. Modifier dashboard_frontend.html ligne 293
# 3. start dashboard_frontend.html
```

---

## 🎯 Résultat Final

Après ces étapes:

✅ **API Dashboard** déployée sur Railway
✅ **Connectée** à la DB du scanner
✅ **URL publique** générée
✅ **Frontend** affiche tes vraies alertes
✅ **Temps réel** avec auto-refresh

**Temps estimé**: 15 minutes ⏱️

---

## 📚 Ressources

- **Railway CLI Docs**: https://docs.railway.com/guides/cli
- **Railway Dashboard**: https://railway.app/dashboard
- **GitHub CLI**: https://github.com/railwayapp/cli

---

**Dashboard déployé avec Railway CLI! 🚀**

