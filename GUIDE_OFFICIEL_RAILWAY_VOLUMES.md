# 📊 Guide Officiel Railway - Créer un Volume (Documentation 2025)

**Source** : https://docs.railway.com/guides/volumes
**Projet** : `dd45f13b-3e76-4ca3-9d0b-2ef274d45845`
**Date** : 13 Décembre 2025

---

## 🎯 ÉTAPE 1 : Créer un Volume (2 Méthodes Officielles)

### Méthode 1 : Command Palette (Recommandé)

1. **Ouvrir votre projet Railway** :
   ```
   https://railway.com/project/dd45f13b-3e76-4ca3-9d0b-2ef274d45845
   ```

2. **Appuyer sur** : `Ctrl + K` (Windows/Linux) ou `⌘ + K` (Mac)
   - La "Command Palette" s'ouvre (barre de recherche)

3. **Taper** : `volume`
   - Vous verrez apparaître : "Create Volume" ou "New Volume"

4. **Cliquer sur** : "Create Volume" (ou appuyer sur Entrée)

5. **Une fenêtre s'ouvre** : "Create Volume"

---

### Méthode 2 : Menu Contextuel (Clic Droit)

1. **Ouvrir votre projet Railway** :
   ```
   https://railway.com/project/dd45f13b-3e76-4ca3-9d0b-2ef274d45845
   ```

2. **Clic droit** sur le canvas (zone vide de votre projet, à côté de vos services)

3. Un menu contextuel s'ouvre

4. **Cliquer sur** : "Create Volume" ou "New Volume"

5. **Une fenêtre s'ouvre** : "Create Volume"

---

## 🎯 ÉTAPE 2 : Connecter le Volume au Service

Après avoir cliqué sur "Create Volume", Railway vous demande :

### Question 1 : "Select a service to connect the volume to"

**Vous verrez la liste de vos services** (exemple) :
```
○ geckoterminal-scanner
○ autre-service
```

**Sélectionner** : Votre service de bot (celui qui contient `geckoterminal_scanner_v2.py`)

**Cliquer sur** : Le nom du service ou appuyer sur Entrée

---

## 🎯 ÉTAPE 3 : Configurer le Mount Path

Après avoir sélectionné le service, Railway demande :

### Question 2 : "Mount Path"

**C'est le chemin où le volume sera accessible dans votre container.**

⚠️ **ATTENTION - Information Cruciale de la Documentation** :

> "Since Railway's default buildpack (Nixpacks) places application files in `/app`, relative paths require adjustment."

**Ce que ça signifie pour VOUS** :

#### ❌ NE PAS UTILISER `/data` directement

Votre bot écrit dans `/data/alerts_history.db`, qui est un **chemin absolu**.

**SI votre bot utilise un chemin absolu** (`/data/...`) :
✅ **Mount Path à utiliser** : `/data`

**SI votre bot utilise un chemin relatif** (`./data/...`) :
✅ **Mount Path à utiliser** : `/app/data`

---

### Vérifier le Chemin dans Votre Bot

**Ouvrir** : `geckoterminal_scanner_v2.py`

**Chercher** : `DB_PATH` (environ ligne 30-40)

**Vous devriez voir** :
```python
DB_PATH = os.getenv("DB_PATH", "/data/alerts_history.db")
```

✅ **C'est un chemin absolu** (`/data/...`)

**DONC le Mount Path est** : `/data`

---

### Configuration du Mount Path

Dans la fenêtre "Mount Path" :

**Taper** : `/data`

**Cliquer sur** : "Add" ou "Create" ou appuyer sur Entrée

---

## 🎯 ÉTAPE 4 : Le Volume est Créé !

Railway affiche :
```
✓ Volume created successfully
```

**Vous verrez maintenant** :
- Une nouvelle **carte "Volume"** dans votre projet
- Le volume est **connecté** à votre service (ligne de connexion)

---

## 🎯 ÉTAPE 5 : Redémarrage du Service

⚠️ **Important de la documentation** :

> "Volumes are mounted to your service's container when it is started, not during build time."

**Ce que ça signifie** : Le volume n'est disponible qu'**après le redémarrage** du service.

### Redémarrer Manuellement

1. **Cliquer sur votre service** (carte avec votre bot)

2. **En haut à droite**, chercher **"⋯"** (trois points) ou l'icône menu

3. **Cliquer sur "Restart"**

4. **Attendre 30-60 secondes** que le service redémarre

5. **Vérifier l'icône** : Elle doit redevenir verte (service actif)

---

## 🎯 ÉTAPE 6 : Vérification - Variables d'Environnement

Railway ajoute automatiquement des variables d'environnement pour les volumes.

### Vérifier les Variables

1. **Cliquer sur votre service**

2. **Onglet "Variables"**

3. **Chercher** (Ctrl+F dans la page) :

**Vous devriez voir** (automatiquement ajouté par Railway) :
```
RAILWAY_VOLUME_NAME=<nom-du-volume>
RAILWAY_VOLUME_MOUNT_PATH=/data
```

✅ **Si vous voyez ces variables** : Le volume est bien monté !

---

## 🎯 ÉTAPE 7 : Vérifier dans les Logs

1. **Onglet "Logs"** de votre service

2. **Chercher** (Ctrl+F) :
   ```
   💾 Sauvegardé en DB
   ```

**Vous devriez voir** :
```
💾 Sauvegardé en DB: /data/alerts_history.db
```

✅ **Si vous voyez ce message** : Le bot utilise bien le volume !

---

## 🎯 ÉTAPE 8 : Télécharger la Base de Données

Maintenant que le volume est créé et monté, vous pouvez télécharger la DB.

### Installer Railway CLI (Si Pas Déjà Fait)

**PowerShell en Administrateur** :
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

**Fermer et rouvrir PowerShell**, puis :

```bash
# Vérifier l'installation
railway --version
```

---

### Se Connecter et Lier le Projet

```bash
# Connexion
railway login

# Aller dans le répertoire
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Lier le projet
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845
```

---

### Télécharger la DB

```bash
railway run cat /data/alerts_history.db > alerts_railway.db
```

**Vérifier la taille** :
```bash
dir alerts_railway.db
```

**Si taille > 0** :
✅ **DB téléchargée avec succès !**

---

### Consulter la DB

```bash
python consulter_db.py
```

---

## ⚠️ Informations Importantes de la Documentation

### 1. Les Volumes ne Sont PAS Disponibles au Build

> "Volumes are mounted when the service is started, not during build time."

**Ce que ça signifie** :
- ❌ Vous ne pouvez PAS écrire dans le volume pendant le `build`
- ✅ Vous POUVEZ écrire dans le volume pendant le `runtime` (quand l'app tourne)

**Pour votre bot** :
✅ Pas de problème ! Le bot écrit dans la DB quand il **tourne** (runtime), pas au build.

---

### 2. Les Pre-Deploy Commands ne Peuvent PAS Accéder aux Volumes

> "Pre-deploy commands cannot access volumes; write operations should occur in your start command instead."

**Ce que ça signifie** :
- ❌ N'utilisez PAS de pre-deploy command pour initialiser la DB
- ✅ Initialisez la DB dans votre script Python directement

**Pour votre bot** :
✅ Pas de problème ! `alert_tracker.py` crée automatiquement la DB au démarrage si elle n'existe pas.

---

### 3. Permissions pour Utilisateurs Non-Root

> "For non-root users, add `RAILWAY_RUN_UID=0` to your service variables."

**Si vous avez des erreurs de permissions** sur la DB, ajoutez cette variable :

1. **Service → Variables**
2. **Nouvelle Variable** :
   - **Name** : `RAILWAY_RUN_UID`
   - **Value** : `0`
3. **Redémarrer le service**

---

### 4. Agrandir un Volume (Pro Tier)

> "Pro tier users can expand volume capacity through volume settings by clicking the Grow option."

**Si vous manquez d'espace** (peu probable pour une DB SQLite) :
1. Cliquer sur la carte "Volume"
2. Chercher l'option "Grow" ou "Expand"
3. Augmenter la taille

---

## 🆘 Dépannage

### ❌ Erreur : "No such file or directory: /data/alerts_history.db"

**Causes possibles** :

1. **Le volume n'est pas monté**
   - Vérifier : Service → Variables → Chercher `RAILWAY_VOLUME_MOUNT_PATH`
   - Si absent : Re-créer le volume

2. **Le service n'a pas redémarré après création du volume**
   - Service → Menu (⋯) → Restart

3. **Aucune alerte sauvegardée encore**
   - Vérifier les logs : Chercher "💾 Sauvegardé en DB"
   - Si absent : Attendre que le bot trouve un token (10-30 min)

4. **Mauvais mount path**
   - Vérifier : `RAILWAY_VOLUME_MOUNT_PATH=/data` (pas `/app/data`)

---

### ❌ Erreur : Permission denied

**Solution** : Ajouter la variable `RAILWAY_RUN_UID=0`

1. Service → Variables → New Variable
2. **Name** : `RAILWAY_RUN_UID`
3. **Value** : `0`
4. Restart service

---

### ❌ Le volume existe mais la DB est vide

**Vérifications** :

1. **Vérifier que le bot tourne** :
   - Logs → Chercher "🔍 SCAN GeckoTerminal démarré"

2. **Vérifier que le bot trouve des tokens** :
   - Logs → Chercher "🔒 Vérification sécurité"
   - Si aucun : Le bot scanne mais ne trouve rien (normal, il est sélectif)

3. **Vérifier le chemin DB dans le code** :
   ```bash
   railway run env | grep DB_PATH
   ```
   Devrait afficher : `DB_PATH=/data/alerts_history.db`

---

## ✅ Checklist Complète

### Sur Railway Dashboard

- [ ] Volume créé (via Ctrl+K ou clic droit)
- [ ] Volume connecté au service de bot
- [ ] Mount Path configuré : `/data`
- [ ] Service redémarré après création du volume
- [ ] Variables `RAILWAY_VOLUME_NAME` et `RAILWAY_VOLUME_MOUNT_PATH` présentes
- [ ] Logs montrent "💾 Sauvegardé en DB: /data/alerts_history.db"

### Sur Votre PC

- [ ] Railway CLI installé (`railway --version`)
- [ ] Connecté (`railway login`)
- [ ] Projet lié (`railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845`)
- [ ] DB téléchargée (`railway run cat /data/alerts_history.db > alerts_railway.db`)
- [ ] DB non vide (taille > 0)
- [ ] Consultée avec `python consulter_db.py`

**Si tous les ✅** → 🎉 **SYSTÈME OPÉRATIONNEL !**

---

## 📋 Résumé des Étapes (Guide Rapide)

### Sur Railway Dashboard

```
1. Ctrl+K → Taper "volume" → Create Volume
2. Sélectionner votre service (bot)
3. Mount Path : /data
4. Service → Menu (⋯) → Restart
5. Logs → Vérifier "💾 Sauvegardé en DB"
```

### Sur Votre PC (PowerShell)

```bash
# Installation CLI (une fois, PowerShell Admin)
iwr https://railway.app/install.ps1 -useb | iex

# Connexion et configuration (une fois)
railway login
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845

# Télécharger la DB (à chaque consultation)
railway run cat /data/alerts_history.db > alerts_railway.db

# Consulter
python consulter_db.py
```

---

## 🎯 Diagramme du Flux

```
┌─────────────────────────────────────────┐
│  1. Ctrl+K → Create Volume              │
│     Mount Path: /data                   │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  2. Service Restart (automatique/manuel)│
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  3. Bot Démarre                         │
│     Variables auto-ajoutées:            │
│     - RAILWAY_VOLUME_NAME               │
│     - RAILWAY_VOLUME_MOUNT_PATH=/data   │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  4. Bot Trouve un Token                 │
│     → Vérifie sécurité                  │
│     → Envoie alerte Telegram            │
│     → Sauvegarde dans /data/alerts...   │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  5. Vous: Télécharger la DB             │
│     railway run cat /data/... > local.db│
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  6. Consulter avec consulter_db.py      │
│     ou DB Browser for SQLite            │
└─────────────────────────────────────────┘
```

---

## 📚 Références

| Document | Utilité |
|----------|---------|
| [Documentation Railway Volumes](https://docs.railway.com/guides/volumes) | Guide officiel |
| [consulter_db.py](consulter_db.py) | Script consultation interactif |
| [GUIDE_DB_BROWSER_SQLITE.md](GUIDE_DB_BROWSER_SQLITE.md) | Interface graphique |
| [FONCTIONNEMENT_SAUVEGARDE.md](FONCTIONNEMENT_SAUVEGARDE.md) | Comment la DB fonctionne |

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Source** : Documentation Officielle Railway
**Statut** : ✅ **GUIDE OFFICIEL COMPLET**