# Déploiement Dashboard V3 sur Railway

Guide complet pour déployer le scanner V3 avec dashboard API sur Railway.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAILWAY                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────┐      ┌──────────────────────────┐  │
│  │  Service 1: Scanner V3 │      │  Service 2: API Dashboard│  │
│  │                        │      │                          │  │
│  │  geckoterminal_       │──────▶│  scanner_api.py          │  │
│  │  scanner_v3.py        │ JSON  │                          │  │
│  │                        │ file  │  Port: 5000              │  │
│  │  Écrit:                │      │  Lit: alerts_live.json   │  │
│  │  - alerts_live.json    │      │                          │  │
│  │  - alerts_history.db   │      │  Expose API REST         │  │
│  └────────────────────────┘      └──────────────────────────┘  │
│              │                               │                   │
│              │                               │                   │
│              ▼                               ▼                   │
│     ┌─────────────────────────────────────────────┐            │
│     │         Railway Volume /data                │            │
│     │  - alerts_live.json (partagé)               │            │
│     │  - alerts_history.db                        │            │
│     └─────────────────────────────────────────────┘            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS
                               ▼
                    ┌────────────────────────┐
                    │   Frontend Dashboard   │
                    │  (Local ou Vercel)     │
                    │  dashboard_frontend    │
                    │  .html                 │
                    └────────────────────────┘
```

---

## Étape 1: Préparer les Fichiers

### Fichiers à déployer

**Service 1 - Scanner V3**:
- `geckoterminal_scanner_v3.py` ✅ (modifié avec json_writer)
- `security_checker.py`
- `alert_tracker.py`
- `json_alert_writer.py` ✅ (nouveau)
- `.env.v3` (pour Telegram tokens)
- `requirements.txt`

**Service 2 - API Dashboard**:
- `scanner_api.py` ✅ (nouveau)
- `requirements_dashboard.txt`

### Vérifier les modifications

1. **Scanner V3 modifié** ✅:
   - Import de `JSONAlertWriter` ligne 37
   - Variable `json_writer` ligne 242
   - Initialisation dans `main()` ligne 3172
   - Sauvegarde JSON après alerte ligne 3026-3030

2. **Configuration ULTRA_RENTABLE** ✅:
   - Lignes 137-167 du scanner
   - Objectif: 2.7 alertes/jour, Score 95.9

---

## Étape 2: Configuration Railway

### Service 1: Scanner V3

1. **Créer un nouveau service Railway** (ou utiliser l'existant):
   ```
   Nom: scanner-v3-ultra-rentable
   ```

2. **Variables d'environnement**:
   ```
   TELEGRAM_BOT_TOKEN=8451477317:AAFlppZm7GHGeV2Uv_gR7qfpDkDwONPktVM
   TELEGRAM_CHAT_ID=-1003393653837
   DB_PATH=/data/alerts_history.db
   ```

3. **Commande de démarrage**:
   ```
   python geckoterminal_scanner_v3.py
   ```

4. **Volume partagé** (IMPORTANT):
   - Créer ou utiliser volume existant: `/data`
   - Ce volume stockera:
     - `alerts_history.db` (base SQLite)
     - `alerts_live.json` (pour API)

### Service 2: API Dashboard

1. **Créer un nouveau service Railway**:
   ```
   Nom: dashboard-api
   ```

2. **Variables d'environnement**:
   ```
   PORT=5000
   ```

3. **Commande de démarrage**:
   ```
   python scanner_api.py
   ```

4. **Monter le MÊME volume** `/data`:
   - Partager le volume avec le Service 1
   - Permet de lire `alerts_live.json` écrit par le scanner

5. **Exposer le port**:
   - Railway génèrera automatiquement une URL publique
   - Format: `https://dashboard-api-production-xxxx.up.railway.app`

---

## Étape 3: Déploiement

### Via Railway CLI

```bash
# Se connecter à Railway
railway login

# Scanner V3
railway link scanner-v3-ultra-rentable
railway up

# API Dashboard
railway link dashboard-api
railway up
```

### Via GitHub (Recommandé)

1. **Pusher les fichiers sur GitHub**:
   ```bash
   git add .
   git commit -m "Add dashboard API and JSON writer"
   git push
   ```

2. **Connecter Railway au repo GitHub**:
   - Service 1: Pointer vers le repo, déploiement auto
   - Service 2: Même repo, commande différente

3. **Railway détectera `requirements.txt` et `requirements_dashboard.txt`**

---

## Étape 4: Vérification

### Scanner V3

1. **Vérifier les logs Railway**:
   ```
   🚀 Démarrage GeckoTerminal Scanner V3...
   ================================================================================
   V3.1 ULTRA_RENTABLE - Configuration active
   Objectif: 2.7 alertes/jour | Score 95.9 | WR 55-70% | ROI +10-15%/mois
   ================================================================================
   💾 Base de données: /data/alerts_history.db
   📄 JSON writer initialisé: alerts_live.json
   ✅ Système de sécurité activé
   ```

2. **Vérifier le fichier JSON**:
   - Se connecter via Railway Shell au service scanner
   - `cat /data/alerts_live.json`
   - Devrait contenir un array JSON d'alertes

### API Dashboard

1. **Vérifier les logs**:
   ```
   Scanner API démarrée sur port 5000
   Fichier alertes: alerts_live.json
   ```

2. **Tester l'API**:
   ```bash
   # Health check
   curl https://dashboard-api-production-xxxx.up.railway.app/api/health

   # Devrait retourner:
   {
     "status": "ok",
     "timestamp": "2025-01-15T10:30:00",
     "total_alerts": 0
   }
   ```

3. **Tester les endpoints**:
   ```bash
   # Stats
   curl https://your-api.railway.app/api/stats

   # Alertes récentes
   curl https://your-api.railway.app/api/recent?limit=5

   # Alertes filtrées
   curl "https://your-api.railway.app/api/alerts?network=eth&min_score=90"
   ```

---

## Étape 5: Configurer le Frontend

### Option A: Local (Développement)

1. **Modifier `dashboard_frontend.html`**:
   ```javascript
   // Ligne ~293
   API_URL: 'https://dashboard-api-production-xxxx.up.railway.app/api'
   ```

2. **Ouvrir dans le navigateur**:
   ```bash
   start dashboard_frontend.html
   ```

### Option B: Vercel/Netlify (Production)

1. **Créer un nouveau repo pour le frontend**:
   ```bash
   mkdir scanner-dashboard-frontend
   cd scanner-dashboard-frontend
   cp dashboard_frontend.html index.html
   ```

2. **Modifier l'URL de l'API**:
   ```javascript
   API_URL: 'https://dashboard-api-production-xxxx.up.railway.app/api'
   ```

3. **Déployer sur Vercel**:
   ```bash
   vercel
   ```

   Ou sur Netlify:
   - Drag & drop `index.html` sur netlify.com

4. **Accéder au dashboard**:
   ```
   https://scanner-dashboard.vercel.app
   ```

---

## Étape 6: Monitoring

### Vérifier que tout fonctionne

1. **Scanner génère des alertes**:
   - Surveiller les logs Railway du scanner
   - Vérifier les messages Telegram

2. **JSON est écrit**:
   - Railway Shell → `cat /data/alerts_live.json`
   - Devrait se remplir au fur et à mesure

3. **API répond**:
   - Tester `/api/health` régulièrement
   - Vérifier `/api/stats` pour voir les données

4. **Dashboard affiche les données**:
   - Ouvrir le frontend
   - Vérifier que les graphiques se chargent
   - Tester les filtres

---

## Troubleshooting

### ❌ API retourne "total_alerts: 0"

**Problème**: Le fichier JSON est vide ou pas partagé

**Solution**:
1. Vérifier que les 2 services montent le MÊME volume `/data`
2. Vérifier les logs du scanner: "📄 JSON writer initialisé"
3. Railway Shell scanner: `ls -la /data/alerts_live.json`
4. Railway Shell API: `ls -la /data/alerts_live.json`

### ❌ "FileNotFoundError: alerts_live.json"

**Problème**: Volume pas monté ou chemin incorrect

**Solution**:
1. Dans `scanner_api.py`, vérifier `ALERTS_FILE`:
   ```python
   ALERTS_FILE = '/data/alerts_live.json'  # Chemin absolu
   ```

2. Même chose dans le scanner:
   ```python
   json_writer = JSONAlertWriter('/data/alerts_live.json')
   ```

### ❌ CORS Error dans le navigateur

**Problème**: Frontend ne peut pas appeler l'API

**Solution**:
- `flask-cors` est déjà configuré dans `scanner_api.py`
- Vérifier que l'URL de l'API est correcte dans le frontend
- Tester l'API directement avec `curl` pour isoler le problème

### ❌ "Module not found: json_alert_writer"

**Problème**: Fichier manquant sur Railway

**Solution**:
1. Vérifier que `json_alert_writer.py` est committé dans git
2. Re-déployer le service scanner
3. Vérifier les logs Railway pendant le build

---

## Structure Finale sur Railway

```
/app
├── geckoterminal_scanner_v3.py
├── scanner_api.py
├── security_checker.py
├── alert_tracker.py
├── json_alert_writer.py
├── .env.v3
├── requirements.txt
└── requirements_dashboard.txt

/data (Volume partagé)
├── alerts_history.db      ← Base SQLite (scanner)
└── alerts_live.json       ← Fichier JSON (scanner → API)
```

---

## Prochaines Étapes

### Court Terme

1. ✅ Scanner V3 ULTRA_RENTABLE déployé
2. ✅ API Dashboard fonctionnelle
3. ⏳ Frontend configuré et accessible
4. ⏳ Monitoring des premières alertes

### Moyen Terme

- [ ] Ajouter authentification à l'API
- [ ] WebSocket pour temps réel
- [ ] Export CSV/JSON depuis le dashboard
- [ ] Alertes email configurables

### Long Terme

- [ ] Migration PostgreSQL (au lieu de SQLite + JSON)
- [ ] Backend FastAPI avec async
- [ ] Frontend Next.js
- [ ] Trading direct depuis dashboard

---

## Commandes Utiles Railway

```bash
# Voir les logs en temps réel
railway logs

# Se connecter au shell
railway shell

# Vérifier les variables d'environnement
railway vars

# Redéployer
railway up --detach

# Lister les volumes
railway volumes

# Voir l'utilisation
railway status
```

---

## Support

URL de l'API Dashboard: `https://dashboard-api-production-xxxx.up.railway.app`

Endpoints disponibles:
- GET `/api/health` - Health check
- GET `/api/alerts` - Liste des alertes (avec filtres)
- GET `/api/stats` - Statistiques globales
- GET `/api/networks` - Stats par réseau
- GET `/api/recent` - Alertes récentes

---

**Dashboard V3 - Prêt pour Railway! 🚀**
