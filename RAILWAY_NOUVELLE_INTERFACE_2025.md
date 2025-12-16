# 📊 Railway - Nouvelle Interface 2025 - Accès Base de Données

**Mise à jour** : Décembre 2025
**Projet** : `dd45f13b-3e76-4ca3-9d0b-2ef274d45845`

---

## ⚠️ Important : Railway a Changé son Interface

Railway a modifié la façon de gérer les volumes. Voici la **nouvelle procédure 2025**.

---

## 🎯 NOUVELLE MÉTHODE : Créer un Volume (Interface 2025)

### ÉTAPE 1 : Accéder à Votre Projet

1. **Ouvrir** : https://railway.com/project/dd45f13b-3e76-4ca3-9d0b-2ef274d45845

2. Vous verrez votre projet avec un ou plusieurs **services** (rectangles/cartes)

---

### ÉTAPE 2 : Créer un Nouveau Volume (Méthode 2025)

#### Option A : Via le Bouton "New" (Recommandé)

1. **En haut à droite**, chercher le bouton **"+ New"** ou **"New"**

2. **Cliquer dessus** → Un menu déroulant apparaît :
   ```
   Database
   Empty Service
   Template
   Volume         ← CLIQUER ICI
   ```

3. **Cliquer sur "Volume"**

4. Une fenêtre s'ouvre avec un formulaire :

   **Nom du Volume (optionnel)** :
   ```
   bot-data
   ```
   (ou laisser vide, Railway génère un nom automatique)

5. **Cliquer sur "Create"** ou "Add"

6. **Le volume est créé !** Vous verrez une nouvelle carte "Volume" dans votre projet

---

#### Option B : Via la Commande Palette

1. **Appuyer sur** : `Ctrl + K` (Windows) ou `Cmd + K` (Mac)

2. La palette de commandes s'ouvre

3. **Taper** : `volume`

4. **Sélectionner** : "New Volume" ou "Create Volume"

5. **Appuyer sur Entrée**

6. Suivre les mêmes étapes que l'Option A (formulaire)

---

### ÉTAPE 3 : Connecter le Volume au Service

Maintenant que le volume est créé, vous devez le **connecter** à votre service (bot).

1. **Cliquer sur votre service** (le carré/rectangle avec votre bot)

2. **En haut**, chercher l'onglet **"Variables"** et cliquer dessus

3. **Descendre** jusqu'à trouver la section **"Service Variables"** ou **"Variables"**

4. **Chercher une section appelée "Volumes" ou "Mounts"**

   **SI VOUS LA VOYEZ** :
   - Cliquer sur **"+ Add Mount"** ou **"Connect Volume"**
   - Sélectionner le volume que vous venez de créer
   - **Mount Path** : `/data`
   - Cliquer sur "Add" ou "Save"

   **SI VOUS NE LA VOYEZ PAS** :
   - Passer à la **MÉTHODE ALTERNATIVE** ci-dessous

---

### MÉTHODE ALTERNATIVE : Ajouter une Variable de Volume

Si l'interface ne montre pas d'option graphique pour les volumes, utilisez une **variable d'environnement** pour monter le volume.

1. **Rester dans l'onglet "Variables"** de votre service

2. **Cliquer sur "New Variable"** ou **"+ Variable"**

3. **Remplir** :

   **Variable Name** :
   ```
   RAILWAY_VOLUME_MOUNT_PATH
   ```

   **Variable Value** :
   ```
   /data
   ```

4. **Cliquer sur "Add"**

5. **Redémarrer le service** :
   - En haut à droite, chercher **"⋯"** (trois points) ou icône de menu
   - Cliquer sur **"Restart"**
   - Attendre 30-60 secondes

---

## 🎯 MÉTHODE LA PLUS SIMPLE : Railway CLI

Si l'interface web est trop complexe, utilisez la **ligne de commande** pour créer et connecter le volume.

### ÉTAPE 1 : Installer Railway CLI (Si Pas Déjà Fait)

**PowerShell en Administrateur** :
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

**Fermer et rouvrir PowerShell**, puis vérifier :
```bash
railway --version
```

---

### ÉTAPE 2 : Se Connecter et Lier

```bash
# Se connecter
railway login

# Aller dans le répertoire
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Lier le projet
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845
```

---

### ÉTAPE 3 : Créer le Volume via CLI

```bash
railway volume create
```

**Ce qui se passe** :
1. Railway CLI demande : **"Volume name?"**
   ```
   bot-data
   ```
   (ou appuyer sur Entrée pour nom automatique)

2. Railway CLI demande : **"Mount path?"**
   ```
   /data
   ```

3. Railway CLI crée le volume et l'attache au service

4. Railway CLI affiche :
   ```
   ✓ Volume created and attached to service
   ```

5. **Le service redémarre automatiquement**

---

### ÉTAPE 4 : Vérifier que le Volume est Monté

```bash
# Voir les logs en temps réel
railway logs --follow
```

**Chercher dans les logs** :
```
💾 Sauvegardé en DB: /data/alerts_history.db
```

✅ **Si vous voyez ce message** → Volume fonctionne !

---

## 🎯 ALTERNATIVE : Utiliser le Stockage Éphémère (Temporaire)

Si vous ne parvenez pas à créer un volume, vous pouvez quand même **télécharger la DB actuelle** (mais elle sera perdue au redémarrage du service).

### Télécharger la DB Éphémère

```bash
# Se connecter et lier (si pas déjà fait)
railway login
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845

# Télécharger la DB (même sans volume)
railway run cat /data/alerts_history.db > alerts_railway.db
```

**SI LA DB EXISTE** :
- ✅ Elle sera téléchargée
- ⚠️ ATTENTION : Elle sera **perdue au prochain redémarrage** du service (sans volume)

**SI ERREUR "No such file"** :
- ❌ Aucune alerte sauvegardée encore
- Ou le bot n'a pas pu écrire dans `/data`

---

## 🎯 SOLUTION RECOMMANDÉE : Utiliser la Nouvelle Interface Railway

Railway change régulièrement son interface. Voici comment naviguer dans la **version actuelle** (Décembre 2025) :

### Interface Actuelle (v2025)

1. **Cliquer sur votre projet**
2. **Vous voyez des "cartes"** pour chaque service/base/volume
3. **Chercher le bouton "+ New"** en haut à droite
4. **Sélectionner "Volume"** dans le menu
5. **Créer le volume**
6. **Cliquer sur votre service** (bot)
7. **Dans Settings**, chercher **"Mounts"**, **"Volumes"** ou **"Storage"**
8. **Connecter le volume** créé avec le mount path `/data`

---

## 🎯 VÉRIFICATION : La DB Est-Elle Accessible ?

Peu importe la méthode utilisée, voici comment vérifier que tout fonctionne :

### Test 1 : Vérifier via les Logs

1. **Railway Dashboard** → Votre projet → Votre service
2. **Onglet "Logs"**
3. **Chercher** (Ctrl+F) :
   ```
   💾 Sauvegardé en DB
   ```

**SI VOUS VOYEZ** :
```
💾 Sauvegardé en DB: /data/alerts_history.db
```
✅ **PARFAIT !** La DB est créée

**SI VOUS NE VOYEZ PAS** :
- Le bot n'a pas encore trouvé de token
- Ou il y a une erreur (chercher des messages d'erreur en rouge)

---

### Test 2 : Télécharger la DB

```bash
railway run cat /data/alerts_history.db > test_db.db
```

**Vérifier la taille** :
```bash
dir test_db.db
```

**SI TAILLE > 0** :
✅ La DB existe et contient des données !

**SI TAILLE = 0** :
❌ La DB n'existe pas encore

---

### Test 3 : Lister les Fichiers dans /data

```bash
railway run ls -lh /data
```

**Vous devriez voir** :
```
total 48K
-rw-r--r-- 1 root root 45K Dec 13 15:30 alerts_history.db
```

**SI VOUS VOYEZ "No such file or directory"** :
❌ Le répertoire `/data` n'existe pas → Volume pas monté

---

## 🆘 Dépannage Interface 2025

### ❌ Problème : "Je ne trouve pas où créer un volume"

**Solutions à essayer** :

1. **Bouton "+ New"** (en haut à droite du dashboard)
   → Chercher "Volume" dans le menu

2. **Palette de commandes** : `Ctrl + K` → taper "volume"

3. **Via CLI** :
   ```bash
   railway volume create
   ```

4. **Contacter le support Railway** si vraiment impossible via l'interface

---

### ❌ Problème : "Le volume est créé mais pas connecté au service"

**Dans l'interface 2025**, les volumes se connectent généralement automatiquement. Si ce n'est pas le cas :

1. **Cliquer sur le service**
2. **Settings** → Chercher "Mounts", "Volumes" ou "Storage"
3. **Ajouter manuellement** le mount path `/data` pointant vers le volume

**OU via variables** :
- Ajouter `RAILWAY_VOLUME_MOUNT_PATH=/data`
- Redémarrer le service

---

### ❌ Problème : "J'ai créé le volume mais la DB est toujours vide"

**Vérifications** :

1. **Le service a-t-il redémarré après création du volume ?**
   - Service → Menu (⋯) → Restart

2. **Le bot tourne-t-il sans erreurs ?**
   - Vérifier les logs (onglet "Logs")

3. **Le bot a-t-il trouvé des tokens ?**
   - Chercher dans les logs : "🔒 Vérification sécurité"
   - Si aucun : attendre 10-30 minutes

4. **Le volume est-il bien monté sur `/data` ?**
   - Tester : `railway run ls /data`

---

## 📋 Récapitulatif des Commandes CLI

```bash
# Installation Railway CLI (PowerShell Admin, une fois)
iwr https://railway.app/install.ps1 -useb | iex

# Connexion (une fois)
railway login

# Aller dans le répertoire
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Lier le projet (une fois)
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845

# Créer un volume (une fois)
railway volume create
# → Nom : bot-data
# → Mount path : /data

# Vérifier que le volume existe
railway run ls -lh /data

# Télécharger la DB (à chaque consultation)
railway run cat /data/alerts_history.db > alerts_railway.db

# Consulter la DB
python consulter_db.py

# Voir les logs en temps réel
railway logs --follow
```

---

## ✅ Checklist Complète

- [ ] Railway CLI installé (`railway --version`)
- [ ] Connecté (`railway login`)
- [ ] Projet lié (`railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845`)
- [ ] Volume créé (via interface ou CLI)
- [ ] Volume monté sur `/data`
- [ ] Service redémarré après création volume
- [ ] Logs montrent "💾 Sauvegardé en DB"
- [ ] DB téléchargée avec succès
- [ ] DB non vide (taille > 0)

**Si tous les ✅** → 🎉 **SYSTÈME OPÉRATIONNEL !**

---

## 🎯 Ma Recommandation

Étant donné que l'interface Railway change souvent, **utilisez la CLI** qui est stable et fonctionne toujours :

```bash
# Tout en 5 commandes
railway login
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845
railway volume create
railway run cat /data/alerts_history.db > alerts_railway.db
```

**Puis consulter** :
```bash
python consulter_db.py
```

C'est la méthode la plus rapide et fiable ! 🚀

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Interface** : Railway v2025 (Nouvelle version)
**Statut** : ✅ **GUIDE MIS À JOUR**