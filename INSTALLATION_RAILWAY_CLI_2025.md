# 🚀 Installation Railway CLI - Méthodes 2025 (Mise à Jour)

**Date** : 13 Décembre 2025
**Source** : Documentation officielle Railway
**Plateforme** : Windows 10/11

---

## 💻 NOTE IMPORTANTE POUR WINDOWS

Ce guide est **adapté pour Windows**. Les différences principales :

1. **Installation** : Via npm, Scoop ou téléchargement manuel (PowerShell au lieu de bash)
2. **Accès aux fichiers distants** : Utilisez `railway ssh -c "commande"` pour exécuter des commandes sur le serveur
3. **Chemins** : Utilisez `c:\Users\...` ou `c:/Users/...` au lieu de `/home/...`
4. **Volume persistant** : Configuration requise pour sauvegarder les données (voir section dédiée)

➡️ **Voir les sections "Spécificités Windows" et "Configuration du Volume Railway" ci-dessous**

---

## ⚠️ L'Ancienne Méthode Ne Fonctionne Plus

❌ **Cette commande NE FONCTIONNE PLUS** :
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

**Erreur** : `(404) Introuvable` → Le script a été supprimé/déplacé

---

## ✅ NOUVELLE MÉTHODE 1 : Via npm (Recommandé)

**C'est quoi npm ?**
→ C'est le gestionnaire de paquets de Node.js (comme un "magasin d'applications" en ligne de commande)

### ÉTAPE 1 : Vérifier si Node.js est Installé

**Ouvrir PowerShell** (pas besoin d'Admin) :

```powershell
node --version
```

**Appuyer sur Entrée**

#### ✅ CAS A : Vous Voyez un Numéro de Version

**Exemple** :
```
v20.10.0
```

**Vérifier que c'est >= 16** :
- v16.x.x → ✅ OK
- v18.x.x → ✅ OK
- v20.x.x → ✅ OK
- v14.x.x → ❌ Trop ancien, mettre à jour

**Si version >= 16** → ✅ **Passer directement à l'ÉTAPE 2**

---

#### ❌ CAS B : Erreur "node n'est pas reconnu"

**Ça veut dire** : Node.js n'est pas installé

➡️ **Installer Node.js d'abord** (voir section ci-dessous)

---

### INSTALLATION DE NODE.JS (Si Nécessaire)

#### Option A : Téléchargement Direct (Le Plus Simple)

1. **Ouvrir votre navigateur**

2. **Aller sur** : https://nodejs.org/

3. **Vous verrez 2 boutons de téléchargement** :
   - **LTS** (Long Term Support) - Recommandé
   - Current (Dernière version)

4. **Cliquer sur le bouton "LTS"** (généralement vert)
   - Exemple : "20.10.0 LTS - Recommended For Most Users"

5. **Le fichier `.msi` se télécharge** (environ 30 MB)

6. **Double-cliquer sur le fichier téléchargé**
   - Nom du fichier : `node-v20.x.x-x64.msi`

7. **Suivre l'installation** :
   - **Welcome** → Cliquer "Next"
   - **License Agreement** → Cocher "I accept" → "Next"
   - **Destination Folder** → Laisser par défaut → "Next"
   - **Custom Setup** → Laisser par défaut → "Next"
   - **Tools for Native Modules** → **NE PAS cocher** → "Next"
   - **Ready to Install** → "Install"
   - **Autoriser les modifications** → Cliquer "Oui"
   - **Completed** → "Finish"

8. **IMPORTANT** : **Fermer et rouvrir PowerShell**

9. **Vérifier l'installation** :
   ```powershell
   node --version
   npm --version
   ```

   **Vous devriez voir** :
   ```
   v20.10.0
   10.2.3
   ```

✅ **Node.js et npm sont installés !**

---

### ÉTAPE 2 : Installer Railway CLI via npm

**Dans PowerShell** :

```powershell
npm install -g @railway/cli
```

**Explication** :
- `npm install` = installer un paquet
- `-g` = globalement (accessible partout)
- `@railway/cli` = le paquet Railway CLI

**Appuyer sur Entrée**

**Vous allez voir** :
```
added 1 package in 5s
```

**Durée** : 10-20 secondes

---

### ÉTAPE 3 : Vérifier l'Installation

```powershell
railway --version
```

**Vous devriez voir** :
```
railway version 3.x.x
```

✅ **Railway CLI est installé !**

---

## ✅ NOUVELLE MÉTHODE 2 : Via Scoop (Alternative)

**C'est quoi Scoop ?**
→ Un gestionnaire de paquets pour Windows (comme npm mais pour les applications Windows)

### ÉTAPE 1 : Installer Scoop

**PowerShell (PAS besoin d'Admin)** :

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Appuyer sur Entrée** → Taper `Y` → Entrée

**Puis** :

```powershell
irm get.scoop.sh | iex
```

**Attendre 30 secondes** → Scoop s'installe

---

### ÉTAPE 2 : Installer Railway CLI via Scoop

```powershell
scoop install railway
```

**Attendre 10-20 secondes**

---

### ÉTAPE 3 : Vérifier

```powershell
railway --version
```

✅ **Railway CLI installé !**

---

## ✅ NOUVELLE MÉTHODE 3 : Téléchargement Manuel

**Si npm et Scoop ne marchent pas**, téléchargez directement l'exécutable.

### ÉTAPE 1 : Télécharger le Binaire

1. **Aller sur** : https://github.com/railwayapp/cli/releases

2. **Chercher la dernière version** (en haut de la page)
   - Exemple : "v3.5.0"

3. **Cliquer sur "Assets"** (pour déplier)

4. **Télécharger** : `railway_windows_amd64.zip`
   - Ou `railway_windows_arm64.zip` si vous avez un PC ARM

5. **Le fichier .zip se télécharge**

---

### ÉTAPE 2 : Extraire et Installer

1. **Ouvrir le dossier "Téléchargements"**

2. **Clic droit sur** `railway_windows_amd64.zip`

3. **"Extraire tout..."** → Choisir un dossier (exemple : `C:\Railway`)

4. **Vous avez maintenant** : `C:\Railway\railway.exe`

---

### ÉTAPE 3 : Ajouter au PATH

**PowerShell en Administrateur** :

```powershell
$env:Path += ";C:\Railway"
[Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::Machine)
```

**Fermer et rouvrir PowerShell**

---

### ÉTAPE 4 : Vérifier

```powershell
railway --version
```

✅ **Railway CLI fonctionne !**

---

## 🎯 Quelle Méthode Choisir ?

| Méthode | Avantages | Inconvénients | Recommandé Pour |
|---------|-----------|---------------|-----------------|
| **npm** | Simple, mises à jour faciles | Nécessite Node.js | ✅ **Vous** (si vous avez déjà Python, vous pouvez installer Node.js facilement) |
| **Scoop** | Installation native Windows | Nécessite Scoop | Utilisateurs avancés Windows |
| **Manuel** | Aucune dépendance | Mises à jour manuelles | Dernier recours |

**MA RECOMMANDATION** : **Méthode 1 (npm)**

**Pourquoi ?**
- Node.js est utile pour d'autres projets
- Installation simple
- Mises à jour automatiques

---

## 📋 PROCÉDURE COMPLÈTE (Méthode npm Recommandée)

### SI VOUS N'AVEZ PAS NODE.JS

```
1. Aller sur https://nodejs.org/
2. Télécharger "LTS" (bouton vert)
3. Installer (suivre l'assistant)
4. Fermer et rouvrir PowerShell
5. Vérifier : node --version
```

### INSTALLER RAILWAY CLI

```powershell
# Dans PowerShell (normal, pas Admin)
npm install -g @railway/cli
```

### VÉRIFIER

```powershell
railway --version
```

### UTILISER

**ÉTAPE 1 : Se connecter et lier le projet**
```powershell
railway login
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link
# Sélectionner : dev9710's Projects → laudable-motivation → production → bot-market
```

**ÉTAPE 2 : Télécharger la base de données**
```powershell
# Méthode recommandée : via SSH
railway ssh -c "cat /app/alerts_history.db" > alerts_railway.db
```

**ÉTAPE 3 : Consulter la base de données localement**
```powershell
python consulter_db.py
```

**⚠️ NOTES IMPORTANTES** :
- La commande `railway ssh -c "commande"` exécute une commande sur le serveur Railway (Linux)
- Le fichier se télécharge avec la redirection `>` qui fonctionne normalement sur Windows
- Actuellement, la DB est dans `/app/alerts_history.db` (non-persistant)
- **Voir la section "Configuration du Volume Railway" ci-dessous pour rendre les données persistantes**

---

## 📦 Configuration du Volume Railway (Important !)

### Pourquoi configurer un volume ?

**PROBLÈME ACTUEL** : La base de données `alerts_history.db` est stockée dans `/app/` qui est **non-persistant**. Cela signifie que :
- ❌ Les données sont perdues à chaque redéploiement
- ❌ Les données sont perdues si le conteneur redémarre
- ❌ L'historique des alertes disparaît régulièrement

**SOLUTION** : Créer un volume persistant monté sur `/data/`

### Étapes pour configurer le volume (Interface Web)

1. **Ouvrir Railway dans votre navigateur**
   - Aller sur : https://railway.app/
   - Se connecter avec votre compte (ludo_du_97.2@hotmail.com)

2. **Naviguer vers votre projet**
   - Cliquer sur le projet "laudable-motivation"
   - Sélectionner l'environnement "production"
   - Cliquer sur le service "bot-market"

3. **Créer un nouveau volume**
   - Aller dans l'onglet **"Settings"**
   - Scroller jusqu'à la section **"Volumes"**
   - Cliquer sur **"+ New Volume"**

4. **Configurer le volume**
   - **Mount Path** : `/data`
   - **Size** : `1 GB` (largement suffisant pour la base de données)
   - Cliquer sur **"Add"**

5. **Ajouter la variable d'environnement**
   - Dans le même service, aller dans **"Variables"**
   - Cliquer sur **"+ New Variable"**
   - **Nom** : `DB_PATH`
   - **Valeur** : `/data/alerts_history.db`
   - Cliquer sur **"Add"**

6. **Migrer la base de données existante**

   **Depuis votre PowerShell local** :
   ```powershell
   # Se connecter en SSH
   railway ssh

   # Copier la DB existante vers le volume persistant
   cp /app/alerts_history.db /data/alerts_history.db

   # Vérifier que le fichier existe
   ls -la /data/

   # Quitter
   exit
   ```

7. **Redémarrer le service**
   - Retourner dans Railway web
   - Cliquer sur **"Deploy" → "Restart"**
   - Ou attendre le redéploiement automatique

### Vérification

Après configuration, vérifiez que tout fonctionne :

```powershell
# Télécharger la nouvelle DB depuis /data
railway ssh -c "cat /data/alerts_history.db" > alerts_railway.db

# Vérifier la taille du fichier
ls -l alerts_railway.db
```

**Si le fichier a une taille > 0**, c'est bon ! Les données sont maintenant persistantes.

### Commandes mises à jour après configuration du volume

**Avant (DB dans /app - non-persistant)** :
```powershell
railway ssh -c "cat /app/alerts_history.db" > alerts_railway.db
```

**Après (DB dans /data - persistant)** :
```powershell
railway ssh -c "cat /data/alerts_history.db" > alerts_railway.db
```

---

## 💻 Spécificités Windows

### Commandes Railway sur Windows

**IMPORTANT** : Railway s'exécute sur des serveurs Linux, donc certaines commandes nécessitent une syntaxe spéciale sur Windows.

#### ❌ INCORRECT (syntaxe Linux)
```powershell
railway run cat /data/alerts_history.db > alerts_railway.db
```

#### ✅ CORRECT (syntaxe Windows)
```powershell
railway run -- sh -c "cat /data/alerts_history.db" > alerts_railway.db
```

**Explication** :
- `railway run` → exécute une commande sur le serveur Railway (Linux)
- `--` → indique que tout ce qui suit est pour la commande distante
- `sh -c "commande"` → enveloppe la commande Linux pour l'exécuter correctement
- `> fichier` → la redirection fonctionne normalement sur Windows

### Autres Exemples de Commandes Railway sur Windows

```powershell
# Lister des fichiers sur le serveur
railway run -- sh -c "ls -la /data"

# Vérifier le contenu d'un fichier distant
railway run -- sh -c "cat /app/config.json"

# Exécuter plusieurs commandes
railway run -- sh -c "cd /data && ls -la"

# Télécharger un fichier
railway run -- sh -c "cat /data/fichier.txt" > fichier_local.txt
```

### Chemins de Fichiers Windows

Dans PowerShell, utilisez toujours des chemins absolus avec `\` ou `/` :

```powershell
# Ces 3 syntaxes fonctionnent
cd c:\Users\ludo_\Documents\projets\owner\bot-market
cd c:/Users/ludo_/Documents/projets/owner/bot-market
cd "c:\Users\ludo_\Documents\projets\owner\bot-market"

# Utilisez des guillemets si le chemin contient des espaces
cd "c:\Mon Dossier\Projet"
```

---

## 🆘 Dépannage

### ❌ "npm : Le terme 'npm' n'est pas reconnu"

**Solution** :
1. Vérifier que Node.js est installé : `node --version`
2. Si non : Installer Node.js (voir section ci-dessus)
3. Si oui : Fermer et rouvrir PowerShell

---

### ❌ "EPERM: operation not permitted"

**Cause** : Problème de permissions avec npm

**Solution** :
```powershell
# Ouvrir PowerShell en Admin
npm install -g @railway/cli --force
```

---

### ❌ "railway : Le terme 'railway' n'est pas reconnu" (après installation)

**Solution** :
1. **Fermer PowerShell**
2. **Rouvrir PowerShell** (nouvelle fenêtre)
3. **Vérifier** : `railway --version`

**Si ça ne marche toujours pas** :
```powershell
# Vérifier où Railway est installé
npm list -g @railway/cli
```

---

### ❌ Node.js version trop ancienne

**Erreur** :
```
npm WARN EBADENGINE Unsupported engine
```

**Solution** :
1. Désinstaller l'ancien Node.js (Panneau de configuration → Programmes)
2. Réinstaller la dernière version LTS depuis https://nodejs.org/

---

## ✅ Checklist Finale

- [ ] Node.js installé (`node --version` >= 16)
- [ ] npm fonctionne (`npm --version`)
- [ ] Railway CLI installé (`npm install -g @railway/cli`)
- [ ] Railway CLI fonctionne (`railway --version`)
- [ ] PowerShell fermé et rouvert

**Si tous les ✅** → 🎉 **PRÊT À UTILISER RAILWAY CLI !**

---

## 🚀 Prochaines Étapes

Maintenant que Railway CLI est installé, retournez au guide :

**[GUIDE_DEBUTANT_RAILWAY_CLI.md](GUIDE_DEBUTANT_RAILWAY_CLI.md)**

➡️ **Commencez à la PARTIE 2 : Se Connecter à Railway**

Ou directement :

```powershell
railway login
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link
# Sélectionner : dev9710's Projects → laudable-motivation → production → bot-market

# Télécharger la DB (avant configuration du volume)
railway ssh -c "cat /app/alerts_history.db" > alerts_railway.db

# Ou après configuration du volume :
railway ssh -c "cat /data/alerts_history.db" > alerts_railway.db

# Consulter
python consulter_db.py
```

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Statut** : ✅ **MÉTHODES 2025 À JOUR**