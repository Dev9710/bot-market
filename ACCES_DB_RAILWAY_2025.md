# 📊 Accès à la Base de Données SQLite sur Railway - Guide 2025

**Date** : 13 Décembre 2025
**Plateforme** : Railway (Version actuelle)

---

## 🎯 Objectif

Accéder et consulter votre base de données `alerts_history.db` qui est stockée sur Railway.

---

## ⚠️ Informations Importantes

### Structure sur Railway

Votre bot crée et utilise une base de données SQLite à cet emplacement :
```
/data/alerts_history.db
```

**MAIS** : Railway est éphémère par défaut ! Pour que la DB persiste, vous devez créer un **Volume**.

---

## 📋 ÉTAPE 1 : Vérifier si un Volume Existe

### 1.1 Se Connecter à Railway

1. Ouvrir votre navigateur
2. Aller sur : **https://railway.app**
3. Cliquer sur **"Login"** (en haut à droite)
4. Se connecter avec votre compte (GitHub, Google, ou email)

### 1.2 Accéder à Votre Projet

1. Vous verrez votre **Dashboard** avec tous vos projets
2. Cliquer sur le projet où votre bot est déployé
   - Le nom du projet est celui que vous avez choisi lors de la création
   - Vous devriez voir un service actif (icône verte)

### 1.3 Vérifier les Volumes

1. Dans votre projet, cliquer sur le **service** (votre bot)
2. Regarder en haut, il y a plusieurs onglets :
   - **Deployments**
   - **Variables**
   - **Settings**
   - **Metrics**
   - **Logs**
3. Cliquer sur l'onglet **"Settings"**
4. Descendre jusqu'à la section **"Volumes"**

**2 cas possibles** :

#### ❌ Cas A : Aucun Volume
Vous verrez :
```
No volumes attached
+ Add Volume
```

→ **Passez à l'ÉTAPE 2** pour créer un volume

#### ✅ Cas B : Volume Existe
Vous verrez :
```
/data → 1GB
Created: [date]
```

→ **Passez directement à l'ÉTAPE 3** pour accéder à la DB

---

## 📋 ÉTAPE 2 : Créer un Volume (Si Nécessaire)

### 2.1 Créer le Volume

1. Dans **Settings → Volumes**
2. Cliquer sur **"+ Add Volume"** (ou **"New Volume"**)
3. Une fenêtre s'ouvre avec 2 champs :

**Champ 1 : Mount Path**
```
/data
```
⚠️ **IMPORTANT** : Tapez exactement `/data` (c'est là où la DB est créée)

**Champ 2 : Size (optionnel)**
```
1
```
(1 GB est largement suffisant pour la DB)

4. Cliquer sur **"Add"** ou **"Create"**

### 2.2 Redémarrer le Service

**IMPORTANT** : Après avoir créé un volume, le service doit redémarrer.

Railway va :
- Afficher un message : "Service will restart"
- Redémarrer automatiquement le bot (~30 secondes)

**Attendre que le service soit à nouveau actif** (icône verte).

---

## 📋 ÉTAPE 3 : Installer Railway CLI (Une Seule Fois)

Pour accéder à la base de données, vous avez besoin du **Railway CLI** sur votre ordinateur.

### 3.1 Vérifier si Railway CLI est Installé

Ouvrir **PowerShell** ou **CMD** :

```bash
railway --version
```

**2 cas** :

#### ✅ Si ça affiche une version
```
railway version 3.x.x
```
→ **Railway CLI est installé**, passez à l'ÉTAPE 4

#### ❌ Si ça affiche une erreur
```
'railway' is not recognized as an internal or external command
```
→ **Installez Railway CLI** (étape 3.2)

---

### 3.2 Installer Railway CLI

#### Option A : Via PowerShell (Recommandé pour Windows)

1. Ouvrir **PowerShell en tant qu'Administrateur**
   - Clic droit sur le menu Démarrer → **Windows PowerShell (Admin)**

2. Exécuter cette commande :
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

3. Attendre l'installation (~30 secondes)

4. **Fermer et rouvrir PowerShell** (important !)

5. Vérifier :
```bash
railway --version
```

#### Option B : Via npm (Si vous avez Node.js)

```bash
npm install -g @railway/cli
```

#### Option C : Téléchargement Direct

1. Aller sur : https://docs.railway.app/guides/cli
2. Télécharger l'installeur Windows
3. Exécuter l'installeur
4. Redémarrer votre terminal

---

## 📋 ÉTAPE 4 : Se Connecter à Railway CLI

### 4.1 Connexion

Ouvrir **PowerShell** ou **CMD** :

```bash
railway login
```

**Ce qui va se passer** :
1. Une page web s'ouvre automatiquement dans votre navigateur
2. Vous verrez : "CLI Login - Authorize Railway CLI"
3. Cliquer sur **"Authorize"** ou **"Confirm"**
4. Vous verrez : "Success! You can close this window"
5. Retourner dans votre terminal

**Terminal affiche** :
```
✓ Logged in as [votre email/nom]
```

---

### 4.2 Lier au Projet

**Aller dans le répertoire de votre bot** :
```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market
```

**Lier au projet Railway** :
```bash
railway link
```

**Ce qui va se passer** :
1. Railway CLI affiche une liste de vos projets
2. Utilisez les **flèches ↑↓** pour sélectionner votre projet
3. Appuyez sur **Entrée**

**Exemple** :
```
? Select a project:
  > mon-bot-market
    autre-projet
    test-projet
```

**Terminal affiche** :
```
✓ Linked to project: mon-bot-market
```

---

## 📋 ÉTAPE 5 : Accéder à la Base de Données

### Méthode 1 : Télécharger la DB en Local (Recommandé)

#### 5.1 Télécharger la DB

```bash
railway run cat /data/alerts_history.db > alerts_railway.db
```

**Ce qui se passe** :
- Railway CLI se connecte à votre service
- Lit le fichier `/data/alerts_history.db`
- Le sauvegarde dans `alerts_railway.db` en local

**Durée** : ~5-10 secondes (selon taille de la DB)

**Terminal affiche** :
```
✓ Connected to [votre-service]
```

#### 5.2 Vérifier que la DB a été Téléchargée

```bash
dir alerts_railway.db
```

**Vous devriez voir** :
```
13/12/2025  15:30    45 056  alerts_railway.db
```

**Si la taille est 0 bytes** → La DB n'existe pas encore sur Railway (aucune alerte sauvegardée)

---

### Méthode 2 : Script Automatique (Plus Simple)

J'ai créé un script qui fait tout automatiquement.

#### Double-cliquez sur :
```
download_db_railway.bat
```

**Le script va** :
1. Vérifier que Railway CLI est installé
2. Créer un nom de fichier avec la date
3. Télécharger la DB
4. Afficher le résultat

**Exemple de nom de fichier** :
```
alerts_railway_20251213_1530.db
```

---

## 📋 ÉTAPE 6 : Consulter la Base de Données

Une fois la DB téléchargée en local, vous avez **3 options** :

### Option A : Script Python Interactif (Le Plus Simple)

```bash
python consulter_db.py
```

**Puis choisir** :
```
=== MENU PRINCIPAL ===
1. Dernières alertes
2. Détail d'une alerte
3. Statistiques globales
4. Liste des tokens suivis
5. Quitter
```

---

### Option B : DB Browser for SQLite (Interface Graphique)

#### 6.1 Télécharger DB Browser

1. Aller sur : https://sqlitebrowser.org/dl/
2. Télécharger **DB Browser for SQLite** pour Windows
3. Installer (installation classique)

#### 6.2 Ouvrir la DB

1. Lancer **DB Browser for SQLite**
2. Cliquer sur **"Ouvrir une base de données"** (icône dossier)
3. Sélectionner `alerts_railway.db`
4. Cliquer sur **"Ouvrir"**

#### 6.3 Consulter les Tables

1. Onglet **"Structure de la base de données"**
   - Voir les 3 tables : `alerts`, `price_tracking`, `alert_analysis`

2. Onglet **"Parcourir les données"**
   - Sélectionner une table dans le menu déroulant
   - Voir toutes les données

3. Onglet **"Exécuter le SQL"**
   - Tapez vos requêtes SQL personnalisées

**Exemple de requête** :
```sql
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```

---

### Option C : SQLite en Ligne de Commande

```bash
# Ouvrir la DB
sqlite3 alerts_railway.db

# Voir les tables
.tables

# Voir la structure
.schema alerts

# Requête
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5;

# Quitter
.quit
```

---

## 📋 ÉTAPE 7 : Vérifier que la DB se Remplit

### 7.1 Attendre une Alerte

Le bot scanne toutes les **5 minutes**. Quand il trouve un token intéressant :
1. ✅ Vérifie la sécurité
2. ✅ Envoie l'alerte sur Telegram
3. ✅ **Sauvegarde dans la DB**

### 7.2 Re-télécharger la DB

**Après quelques heures**, re-téléchargez la DB pour voir les nouvelles alertes :

```bash
railway run cat /data/alerts_history.db > alerts_railway_MAJ.db
```

### 7.3 Consulter les Nouvelles Alertes

```bash
python consulter_db.py
# → Option 1 : Dernières alertes
```

**Vous devriez voir** :
```
=== DERNIÈRES ALERTES (10) ===

ID: 1
Date: 2025-12-13 15:45:23
Token: PEPE/WETH
Réseau: eth
Score Opportunité: 87/100
Score Sécurité: 75/100
Prix: $0.0000123
Volume 24h: $1,234,567
```

---

## 🔄 Automatiser le Téléchargement (Optionnel)

### Script PowerShell Automatique

Créer un fichier `auto_download_db.ps1` :

```powershell
# Auto-téléchargement DB Railway
$date = Get-Date -Format "yyyyMMdd_HHmm"
$filename = "alerts_railway_$date.db"

Write-Host "Téléchargement de la DB Railway..." -ForegroundColor Cyan
railway run cat /data/alerts_history.db > $filename

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ DB téléchargée: $filename" -ForegroundColor Green

    # Ouvrir avec DB Browser (si installé)
    $dbBrowser = "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe"
    if (Test-Path $dbBrowser) {
        & $dbBrowser $filename
    }
} else {
    Write-Host "✗ Erreur lors du téléchargement" -ForegroundColor Red
}
```

**Utilisation** :
```powershell
.\auto_download_db.ps1
```

---

## 🆘 Dépannage

### ❌ Problème 1 : "No such file or directory: /data/alerts_history.db"

**Causes possibles** :
1. Le volume n'est pas créé → **Retour à l'ÉTAPE 2**
2. Aucune alerte n'a encore été sauvegardée → **Attendre**
3. Le chemin DB_PATH est incorrect → **Vérifier les variables**

**Solution** :

1. Vérifier les variables d'environnement sur Railway :
   - Dashboard → Votre service → Onglet **"Variables"**
   - Chercher `DB_PATH`

**Si DB_PATH existe** :
```
DB_PATH=/data/alerts_history.db
```
→ ✅ Correct

**Si DB_PATH n'existe pas** :
→ Le bot utilise la valeur par défaut `/data/alerts_history.db` (OK)

2. Vérifier que le volume est monté sur `/data` :
   - Onglet **"Settings" → "Volumes"**
   - Doit afficher : `/data → 1GB`

3. Vérifier les logs :
```bash
railway logs | grep "💾"
```

**Vous devriez voir** :
```
💾 Sauvegardé en DB: /data/alerts_history.db
```

**Si vous voyez** :
```
💾 Sauvegardé en DB: ./alerts_history.db
```
→ Le volume n'est pas utilisé (problème de configuration)

---

### ❌ Problème 2 : "railway: command not found"

**Cause** : Railway CLI n'est pas installé ou pas dans le PATH

**Solutions** :

1. **Réinstaller Railway CLI** :
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

2. **Fermer et rouvrir le terminal** (important !)

3. **Vérifier** :
```bash
railway --version
```

---

### ❌ Problème 3 : "Not logged in"

**Cause** : Non connecté à Railway CLI

**Solution** :
```bash
railway login
```

Suivre les instructions à l'écran (navigateur s'ouvre → Autoriser)

---

### ❌ Problème 4 : "No project linked"

**Cause** : Le répertoire n'est pas lié à un projet Railway

**Solution** :
```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link
```

Sélectionner votre projet avec les flèches ↑↓

---

### ❌ Problème 5 : DB téléchargée mais vide (0 bytes)

**Causes** :
1. Aucune alerte sauvegardée encore
2. Le bot a crash avant de sauvegarder
3. Problème de permissions

**Vérifications** :

1. **Vérifier les logs Railway** :
```bash
railway logs --follow
```

**Chercher** :
```
🔍 SCAN GeckoTerminal démarré
💾 Sauvegardé en DB
```

2. **Vérifier que le bot tourne** :
   - Dashboard Railway → Votre service → Icône verte (actif)

3. **Attendre une alerte** :
   - Le scan se fait toutes les **5 minutes**
   - Les alertes ne sont envoyées que si :
     - ✅ Score opportunité > seuil
     - ✅ Sécurité validée
     - ✅ Pas de honeypot
     - ✅ LP lockée

---

## 📊 Vérifier que Tout Fonctionne

### Checklist Complète

- [ ] Volume `/data` créé sur Railway
- [ ] Railway CLI installé et connecté
- [ ] Projet lié avec `railway link`
- [ ] DB téléchargée avec succès
- [ ] DB non vide (taille > 0)
- [ ] Consultation avec `consulter_db.py` ou DB Browser
- [ ] Logs Railway montrent "💾 Sauvegardé en DB"

**Si tous les ✅ sont cochés** → 🎉 **SYSTÈME OPÉRATIONNEL !**

---

## 🎯 Récapitulatif des Commandes Essentielles

```bash
# 1. Installer Railway CLI (une seule fois)
iwr https://railway.app/install.ps1 -useb | iex

# 2. Se connecter (une seule fois)
railway login

# 3. Lier au projet (une seule fois par répertoire)
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link

# 4. Télécharger la DB (à chaque fois que vous voulez consulter)
railway run cat /data/alerts_history.db > alerts_railway.db

# 5. Consulter la DB
python consulter_db.py

# 6. Voir les logs en temps réel
railway logs --follow
```

---

## 📱 Accès Mobile (Bonus)

Pour consulter la DB depuis votre smartphone/tablette, utilisez le **Dashboard Streamlit** :

### 1. Déployer le Dashboard

Voir le fichier : [GUIDE_DASHBOARD_STREAMLIT.md](GUIDE_DASHBOARD_STREAMLIT.md)

### 2. Accéder via URL

Une fois déployé :
```
https://votre-app.railway.app
```

Accessible depuis :
- 📱 Smartphone (iOS/Android)
- 💻 Tablette
- 🖥️ PC

---

## 📚 Fichiers de Référence

| Fichier | Utilité |
|---------|---------|
| [download_db_railway.bat](download_db_railway.bat) | Script automatique téléchargement |
| [consulter_db.py](consulter_db.py) | Script interactif consultation |
| [GUIDE_DB_BROWSER_SQLITE.md](GUIDE_DB_BROWSER_SQLITE.md) | Guide DB Browser complet |
| [GUIDE_DASHBOARD_STREAMLIT.md](GUIDE_DASHBOARD_STREAMLIT.md) | Dashboard web |
| [FONCTIONNEMENT_SAUVEGARDE.md](FONCTIONNEMENT_SAUVEGARDE.md) | Comment la DB fonctionne |

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Plateforme** : Railway (Version actuelle 2025)
**Statut** : ✅ **GUIDE COMPLET ET À JOUR**