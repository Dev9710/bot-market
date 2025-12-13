# 🚂 Déploiement sur Railway - Guide Complet

## 📋 Checklist Avant Déploiement

- [ ] Code testé localement
- [ ] Variables d'environnement préparées
- [ ] Compte Railway créé
- [ ] Git repository configuré
- [ ] Base de données comprend le fonctionnement

---

## 🔧 Étape 1 : Préparer les Fichiers

### 1.1 Créer `requirements.txt`

```txt
python-telegram-bot==20.7
requests==2.31.0
beautifulsoup4==4.12.2
schedule==1.2.0
python-dotenv==1.0.1
```

### 1.2 Créer `Procfile`

```
worker: python geckoterminal_scanner_v2.py
```

### 1.3 Créer `runtime.txt` (optionnel)

```
python-3.11.6
```

### 1.4 Créer `.gitignore`

```
# Base de données locale (ne pas commit)
*.db
*.sqlite
*.sqlite3

# Environment variables
.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## 🚀 Étape 2 : Déployer sur Railway

### 2.1 Créer un Projet Railway

```bash
# Option 1: Via le Dashboard Web
# 1. Aller sur https://railway.app
# 2. Cliquer sur "New Project"
# 3. Choisir "Deploy from GitHub repo"
# 4. Sélectionner votre repository

# Option 2: Via CLI
railway login
railway init
railway up
```

### 2.2 Configurer les Variables d'Environnement

**Dans le Dashboard Railway** :
- Settings → Variables → Add Variable

**Variables requises** :
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
```

**Variables optionnelles** :
```
DB_PATH=/data/alerts_history.db
MIN_SECURITY_SCORE=50
```

### 2.3 Configurer le Volume Persistant (IMPORTANT pour la DB)

La base de données SQLite doit être sur un **volume persistant** sinon elle sera effacée à chaque redémarrage.

**Dans Railway Dashboard** :
1. Aller dans votre service
2. Settings → Volumes
3. Click "Add Volume"
   - Mount Path: `/data`
   - Size: 1GB (gratuit)

**Modifier le code pour utiliser le volume** :

Dans `alert_tracker.py`, ligne ~50 :
```python
# AVANT
DB_PATH = 'alerts_history.db'

# APRÈS
import os
DB_PATH = os.getenv('DB_PATH', '/data/alerts_history.db')
```

Faire la même chose dans tous les fichiers qui utilisent la DB.

---

## 📊 Étape 3 : Accès à la Base de Données

### Option A : Railway CLI (Recommandé pour consultation ponctuelle)

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Se connecter
railway login

# Lier le projet
cd votre-projet
railway link

# Shell dans le conteneur
railway shell

# Dans le shell, voir la DB
ls -la /data/
sqlite3 /data/alerts_history.db "SELECT COUNT(*) FROM alerts;"
exit

# Télécharger la DB sur votre PC
railway run cat /data/alerts_history.db > alerts_local.db
```

### Option B : API REST (Recommandé pour accès automatisé)

Déployez l'API REST créée dans [ACCES_DB_RAILWAY.md](ACCES_DB_RAILWAY.md).

**Avantages** :
- Accès depuis n'importe où
- Pas besoin de télécharger la DB
- Intégration facile avec d'autres outils

### Option C : Dashboard Streamlit (Recommandé pour visualisation)

Le plus simple et visuel !

1. Créer `dashboard.py` (voir [ACCES_DB_RAILWAY.md](ACCES_DB_RAILWAY.md))
2. Ajouter dans `requirements.txt` :
   ```
   streamlit==1.29.0
   plotly==5.18.0
   pandas==2.1.4
   ```
3. Modifier `Procfile` :
   ```
   web: streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0
   worker: python geckoterminal_scanner_v2.py
   ```
4. Déployer
5. Accéder au dashboard via `https://votre-app.railway.app`

---

## 🔐 Étape 4 : Sécurité

### 4.1 Protéger les Variables d'Environnement

- ❌ Ne JAMAIS commit `.env` dans git
- ✅ Utiliser Railway Variables pour les secrets
- ✅ Utiliser des clés API fortes

### 4.2 Protéger l'API REST (si vous l'utilisez)

```python
# Dans db_api.py
API_KEY = os.getenv("DB_API_KEY", "votre_cle_complexe_123456")

# Ajouter dans Railway Variables
DB_API_KEY=votre_cle_tres_complexe_et_longue_xyz789
```

### 4.3 Protéger le Dashboard (si vous l'utilisez)

Option 1 : Basic Auth via Railway
```bash
# Dans Railway Variables
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
```

Option 2 : Authentification custom dans Streamlit
```python
# Au début de dashboard.py
import streamlit as st

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.getenv("DASHBOARD_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Reste du dashboard...
```

---

## 📈 Étape 5 : Monitoring

### 5.1 Logs Railway

```bash
# Via CLI
railway logs

# Via Dashboard
# Deployments → Latest → Logs
```

### 5.2 Vérifier que le Bot Tourne

**Indicateurs de santé** :
- ✅ Logs montrent "🚀 Démarrage GeckoTerminal Scanner V2..."
- ✅ Logs montrent "🔒 Initialisation du système de sécurité..."
- ✅ Logs montrent "✅ Système de sécurité activé"
- ✅ Pas d'erreur dans les logs
- ✅ Alertes reçues sur Telegram

### 5.3 Alertes en Cas d'Erreur

Créer un script de monitoring :

```python
# health_check.py
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": f"⚠️ HEALTH CHECK: {message}"})

try:
    # Vérifier que la DB existe
    import sqlite3
    conn = sqlite3.connect('/data/alerts_history.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alerts")
    count = cursor.fetchone()[0]
    conn.close()

    print(f"✅ DB OK - {count} alertes")

except Exception as e:
    send_alert(f"Erreur DB: {e}")
    raise
```

---

## 💰 Coûts Railway

### Plan Gratuit (Hobby)
- ✅ $5 de crédits gratuits par mois
- ✅ 500h d'exécution/mois (~20 jours)
- ✅ 1GB de stockage (volume)
- ✅ Suffisant pour un bot 24/7

### Plan Pro (si nécessaire)
- $20/mois
- Exécution illimitée
- 100GB de stockage

**Estimation pour votre bot** :
- Scanner 24/7 : ~720h/mois
- Volume DB : ~100MB/mois
- → **Plan Gratuit SUFFISANT** (avec $5 de crédits)

---

## 🔄 Workflow Complet

```
1. Développement Local
   ├─ Tester le code
   ├─ Vérifier la DB locale
   └─ Commit sur Git

2. Push sur GitHub
   └─ git push origin main

3. Railway Auto-Deploy
   ├─ Détecte le push
   ├─ Build l'image
   ├─ Deploy automatiquement
   └─ Redémarre le worker

4. Vérification
   ├─ Railway Logs : Vérifier démarrage
   ├─ Telegram : Attendre première alerte
   └─ Dashboard : Consulter les stats

5. Monitoring Continu
   ├─ Railway Logs : Erreurs?
   ├─ Telegram : Alertes reçues?
   ├─ Dashboard : DB se remplit?
   └─ Health check quotidien
```

---

## 🛠️ Dépannage

### Problème 1 : Bot ne démarre pas

**Symptômes** :
- Logs montrent des erreurs d'import
- Logs montrent "ModuleNotFoundError"

**Solution** :
```bash
# Vérifier requirements.txt est à jour
# Vérifier que le Procfile pointe vers le bon fichier
# Rebuild le projet dans Railway
```

### Problème 2 : DB perdue à chaque redémarrage

**Symptômes** :
- Alertes ne s'accumulent pas
- Statistiques toujours à 0

**Solution** :
```bash
# Vérifier qu'un Volume est configuré (/data)
# Vérifier que DB_PATH pointe vers /data/alerts_history.db
# Redémarrer le service
```

### Problème 3 : Pas d'alertes Telegram

**Symptômes** :
- Bot tourne mais pas d'alertes

**Solution** :
```bash
# Vérifier TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID dans Railway Variables
# Vérifier les logs : tokens rejetés pour sécurité?
# Tester en local d'abord
```

### Problème 4 : Erreurs de sécurité API

**Symptômes** :
- Logs montrent "API rate limit"
- Logs montrent "Failed to check security"

**Solution** :
```bash
# Les APIs gratuites ont des rate limits
# Le cache aide (1h de validité)
# Le système de fallback gère ces erreurs
# Vérifier que les 3 APIs (GoPlusLabs, DexScreener, TokenSniffer) sont accessibles
```

---

## 📱 Accès Mobile

Une fois le Dashboard Streamlit déployé :

1. **Depuis votre smartphone** :
   - Ouvrir `https://votre-app.railway.app`
   - Ajouter à l'écran d'accueil (PWA)
   - Consulter les stats en temps réel

2. **Via API** :
   - Créer une app mobile custom
   - Utiliser l'API REST
   - Webhooks pour notifications

---

## ✅ Checklist Post-Déploiement

- [ ] Bot démarré sans erreur
- [ ] Première alerte Telegram reçue
- [ ] Première entrée en DB créée
- [ ] Volume persistant configuré
- [ ] Dashboard accessible (si déployé)
- [ ] API REST fonctionnelle (si déployée)
- [ ] Monitoring activé
- [ ] Logs consultables
- [ ] Variables d'environnement sécurisées
- [ ] Backup DB planifié (railway CLI cron)

---

## 🎉 Résultat Final

Une fois tout configuré, vous aurez :

✅ **Bot 24/7 sur Railway**
- Scanne automatiquement les DEX
- Vérifie la sécurité des tokens
- Envoie alertes Telegram
- Sauvegarde tout en DB

✅ **Base de Données Persistante**
- Toutes les alertes sauvegardées
- Tracking automatique (15min, 1h, 4h, 24h)
- Analyses de performance

✅ **Accès aux Données**
- Dashboard web (Streamlit)
- API REST (si déployée)
- Railway CLI (téléchargement DB)
- Scripts Python locaux

✅ **Monitoring**
- Logs Railway en temps réel
- Statistiques de performance
- Alertes en cas d'erreur

---

**Prêt à déployer ?** 🚀

```bash
git add .
git commit -m "Deploy bot with security and tracking"
git push origin main

# Railway déploie automatiquement!
```