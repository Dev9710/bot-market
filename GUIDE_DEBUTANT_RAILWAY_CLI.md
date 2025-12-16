# 🚀 Guide Débutant Complet - Railway CLI et Téléchargement DB

**Pour quelqu'un qui débute complètement avec la ligne de commande**

---

## 📋 PARTIE 1 : Installer Railway CLI

### ÉTAPE 1.1 : Ouvrir PowerShell en Administrateur

**C'est quoi PowerShell ?**
→ C'est un programme Windows qui permet de taper des commandes (comme l'ancien "Invite de commandes" mais plus moderne)

**Comment l'ouvrir EN TANT QU'ADMINISTRATEUR ?**

#### Méthode 1 : Via le Menu Démarrer (Le Plus Simple)

1. **Cliquer sur le bouton Windows** (en bas à gauche de l'écran)
   - C'est le logo Windows (4 carrés)

2. **Taper** : `PowerShell`
   - Vous allez voir apparaître "Windows PowerShell" dans les résultats

3. **NE PAS CLIQUER DIRECTEMENT DESSUS !**

4. **FAIRE UN CLIC DROIT** sur "Windows PowerShell"

5. Un menu s'ouvre. **Cliquer sur** : **"Exécuter en tant qu'administrateur"**
   - En anglais : "Run as administrator"

6. **Une fenêtre s'ouvre** vous demandant "Voulez-vous autoriser cette application à apporter des modifications ?"
   - **Cliquer sur "Oui"**

7. **PowerShell s'ouvre** avec un fond bleu foncé

8. **Vous voyez quelque chose comme** :
   ```
   Windows PowerShell
   Copyright (C) Microsoft Corporation. Tous droits réservés.

   PS C:\WINDOWS\system32>
   ```

✅ **Vous êtes prêt !** PowerShell est ouvert en mode Administrateur.

---

#### Méthode 2 : Via la Recherche

1. **Appuyer sur la touche Windows** (touche avec le logo Windows sur votre clavier)

2. **Taper** : `PowerShell`

3. Dans les résultats, **CLIC DROIT** sur "Windows PowerShell"

4. **Cliquer sur** : "Exécuter en tant qu'administrateur"

5. **Cliquer sur "Oui"** dans la fenêtre de confirmation

---

### ÉTAPE 1.2 : Installer Railway CLI

**Dans la fenêtre PowerShell qui vient de s'ouvrir** :

1. **Copier cette commande** (sélectionner le texte ci-dessous avec votre souris, puis Ctrl+C) :
   ```powershell
   iwr https://railway.app/install.ps1 -useb | iex
   ```

2. **Dans PowerShell** :
   - **Faire un CLIC DROIT** dans la fenêtre PowerShell
   - OU **Appuyer sur Ctrl+V**
   - La commande apparaît

3. **Appuyer sur la touche Entrée** (Enter)

4. **Attendre 20-30 secondes**

5. **Vous allez voir défiler du texte**, genre :
   ```
   Downloading Railway CLI...
   Installing...
   Railway CLI installed successfully
   ```

6. **À la fin**, vous revenez sur :
   ```
   PS C:\WINDOWS\system32>
   ```

✅ **Installation terminée !**

---

### ÉTAPE 1.3 : Fermer et Rouvrir PowerShell (IMPORTANT !)

**POURQUOI ?** → Pour que Windows "sache" que Railway CLI est installé

1. **Dans PowerShell, taper** :
   ```
   exit
   ```

2. **Appuyer sur Entrée**

3. **La fenêtre PowerShell se ferme**

4. **Rouvrir PowerShell** (cette fois, PAS besoin d'être Administrateur)
   - Menu Démarrer → Taper "PowerShell" → **Cliquer directement** (pas de clic droit)
   - **OU** appuyer sur Windows+X puis choisir "Windows PowerShell"

5. **Une nouvelle fenêtre PowerShell s'ouvre**

---

### ÉTAPE 1.4 : Vérifier que Railway CLI est Installé

**Dans la nouvelle fenêtre PowerShell** :

1. **Taper** (ou copier-coller) :
   ```
   railway --version
   ```

2. **Appuyer sur Entrée**

3. **Vous devriez voir** :
   ```
   railway version 3.x.x
   ```
   (Le numéro exact peut varier, par exemple 3.5.0)

✅ **Si vous voyez un numéro de version** → Railway CLI est installé !

❌ **Si vous voyez une erreur** comme :
```
railway : Le terme 'railway' n'est pas reconnu...
```
→ Retourner à l'ÉTAPE 1.2 et réinstaller

---

## 📋 PARTIE 2 : Se Connecter à Railway

### ÉTAPE 2.1 : Lancer la Connexion

**Dans PowerShell** (celle qui est ouverte, PAS besoin d'être Admin) :

1. **Taper** :
   ```
   railway login
   ```

2. **Appuyer sur Entrée**

3. **PowerShell affiche** :
   ```
   Opening browser to authenticate...
   ```
   (Traduction : "Ouverture du navigateur pour s'authentifier...")

4. **Votre navigateur web s'ouvre AUTOMATIQUEMENT**
   - Une nouvelle page s'ouvre sur railway.app
   - Titre de la page : "CLI Login" ou "Connexion CLI"

---

### ÉTAPE 2.2 : Autoriser Railway CLI

**Dans la page web qui vient de s'ouvrir** :

1. **La page affiche** :
   ```
   CLI Login
   Authorize Railway CLI to access your account

   [Cancel]  [Authorize]
   ```

2. **Cliquer sur le bouton "Authorize"** (ou "Autoriser")
   - C'est généralement un gros bouton bleu ou noir

3. **La page change** et affiche :
   ```
   Success! You can close this window.
   ```
   (Traduction : "Succès ! Vous pouvez fermer cette fenêtre.")

4. **Fermer l'onglet du navigateur** (cliquer sur la croix)

---

### ÉTAPE 2.3 : Retourner dans PowerShell

**Retourner dans la fenêtre PowerShell** :

1. **Vous devriez voir** :
   ```
   ✓ Logged in as votre@email.com
   ```
   (ou votre nom d'utilisateur)

✅ **Vous êtes connecté à Railway !**

❌ **Si vous voyez une erreur** :
- Vérifier que vous avez bien cliqué sur "Authorize" dans le navigateur
- Réessayer : `railway login`

---

## 📋 PARTIE 3 : Aller dans le Répertoire du Bot

### ÉTAPE 3.1 : Comprendre où Vous Êtes

**Dans PowerShell, vous voyez** :
```
PS C:\Users\ludo_>
```

**C'est quoi ?**
→ C'est votre "position" actuelle dans l'ordinateur. Vous êtes dans le dossier `C:\Users\ludo_`

**On veut aller où ?**
→ Dans le dossier où se trouve votre bot : `c:\Users\ludo_\Documents\projets\owner\bot-market`

---

### ÉTAPE 3.2 : Changer de Répertoire

**Dans PowerShell, taper** (ou copier-coller) :
```
cd c:\Users\ludo_\Documents\projets\owner\bot-market
```

**Explication de la commande** :
- `cd` = "Change Directory" (changer de dossier)
- Le reste = le chemin vers votre dossier bot

**Appuyer sur Entrée**

**Maintenant PowerShell affiche** :
```
PS c:\Users\ludo_\Documents\projets\owner\bot-market>
```

✅ **Vous êtes dans le bon dossier !**

---

### ÉTAPE 3.3 : Vérifier que Vous Êtes au Bon Endroit

**Taper** :
```
dir
```

**Appuyer sur Entrée**

**Vous devriez voir une liste de fichiers**, incluant :
```
geckoterminal_scanner_v2.py
alert_tracker.py
security_checker.py
consulter_db.py
requirements.txt
...
```

✅ **Si vous voyez ces fichiers** → Vous êtes au bon endroit !

❌ **Si vous ne les voyez pas** :
- Vérifier que vous avez tapé le bon chemin
- Vérifier que le dossier existe

---

## 📋 PARTIE 4 : Lier Votre Projet Railway

### ÉTAPE 4.1 : Lancer la Commande de Liaison

**Dans PowerShell** (toujours dans le dossier bot-market) :

1. **Taper** (ou copier-coller) :
   ```
   railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845
   ```

**Explication** :
- `railway link` = connecter ce dossier à un projet Railway
- `dd45f13b-3e76-4ca3-9d0b-2ef274d45845` = l'ID de votre projet (c'est unique)

2. **Appuyer sur Entrée**

3. **Attendre quelques secondes...**

---

### ÉTAPE 4.2 : Sélectionner le Service (Si Demandé)

**Railway CLI va peut-être afficher** :
```
? Select a service:
  > service-1
    service-2
```

**C'est quoi ?**
→ Railway vous demande QUEL service (dans votre projet) vous voulez utiliser

**Comment choisir ?**

1. **Utiliser les flèches ↑ et ↓** de votre clavier pour bouger

2. **Sélectionner le service de votre bot**
   - Généralement celui qui contient "geckoterminal", "bot", "scanner", etc.

3. **Appuyer sur Entrée**

---

### ÉTAPE 4.3 : Confirmation

**PowerShell affiche** :
```
✓ Linked to project: [nom-de-votre-projet]
✓ Linked to service: [nom-de-votre-service]
```

✅ **Votre dossier est maintenant lié au projet Railway !**

---

## 📋 PARTIE 5 : Télécharger la Base de Données

### ÉTAPE 5.1 : Lancer le Téléchargement

**Dans PowerShell** (toujours dans le dossier bot-market) :

1. **Taper** (ou copier-coller) :
   ```
   railway run cat /data/alerts_history.db > alerts_railway.db
   ```

**Explication de la commande** :
- `railway run` = exécuter une commande sur Railway (dans le cloud)
- `cat /data/alerts_history.db` = lire le fichier de la base de données
- `>` = sauvegarder le résultat dans...
- `alerts_railway.db` = un nouveau fichier en local (sur votre PC)

2. **Appuyer sur Entrée**

3. **Attendre 5-15 secondes**

**Vous verrez** :
```
Connecting to service...
```
(Traduction : "Connexion au service...")

4. **Puis PowerShell revient à** :
   ```
   PS c:\Users\ludo_\Documents\projets\owner\bot-market>
   ```

✅ **Le téléchargement est terminé !** (même si ça ne dit rien)

---

### ÉTAPE 5.2 : Vérifier que le Fichier a été Téléchargé

**Taper** :
```
dir alerts_railway.db
```

**Appuyer sur Entrée**

**Vous devriez voir** :
```
    Directory: c:\Users\ludo_\Documents\projets\owner\bot-market

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        13/12/2025     15:30          45056 alerts_railway.db
```

**Ce qui est IMPORTANT : la colonne "Length" (taille)**

---

#### ✅ CAS A : Length > 0 (ex: 45056)

**Exemple** :
```
Length = 45056
```

✅ **PARFAIT !** La base de données existe et contient des données !

➡️ **Passer directement à la PARTIE 6**

---

#### ❌ CAS B : Length = 0

**Exemple** :
```
Length = 0
```

**Ça veut dire** : Le fichier a été créé, mais il est vide.

**Pourquoi ?**
1. Le volume n'était pas créé sur Railway
2. Aucune alerte n'a encore été sauvegardée
3. Le bot vient de démarrer

**Que faire ?**

1. **Vérifier que le volume existe sur Railway** :
   - Aller sur : https://railway.com/project/dd45f13b-3e76-4ca3-9d0b-2ef274d45845
   - Ctrl+K → Taper "volume" → Vérifier qu'un volume existe

2. **Attendre 10-30 minutes** que le bot trouve un token intéressant

3. **Réessayer le téléchargement** :
   ```
   railway run cat /data/alerts_history.db > alerts_railway.db
   ```

---

## 📋 PARTIE 6 : Consulter la Base de Données

### ÉTAPE 6.1 : Lancer le Script de Consultation

**Dans PowerShell** (toujours dans le dossier bot-market) :

1. **Taper** :
   ```
   python consulter_db.py
   ```

2. **Appuyer sur Entrée**

3. **Le script démarre** et affiche :
   ```
   ========================================
       CONSULTATION BASE DE DONNÉES
   ========================================

   Fichier: alerts_railway.db
   Taille: 45.0 KB

   === MENU PRINCIPAL ===

   1. Afficher les dernières alertes
   2. Afficher le détail d'une alerte
   3. Afficher les statistiques globales
   4. Afficher les tokens suivis
   5. Quitter

   Votre choix (1-5):
   ```

---

### ÉTAPE 6.2 : Utiliser le Menu

**Le curseur clignote après "Votre choix (1-5):"**

#### Option 1 : Voir les Dernières Alertes

1. **Taper** : `1`
2. **Appuyer sur Entrée**
3. **Vous voyez les 10 dernières alertes** avec tous les détails

**Exemple de ce que vous verrez** :
```
=== DERNIÈRES ALERTES (10) ===

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ID: 1
Date: 2025-12-13 15:45:23
Token: PEPE/WETH
Réseau: eth
Score Opportunité: 87/100
Score Sécurité: 75/100
Prix Entry: $0.0000123
Volume 24h: $1,234,567
Liquidité: $567,890

🎯 Niveaux de Trading:
Entry: $0.0000123
Stop Loss: $0.0000110 (-10.0%)
TP1: $0.0000148 (+20.0%)
TP2: $0.0000172 (+40.0%)
TP3: $0.0000197 (+60.0%)

🛡️ Sécurité:
Honeypot: Non
LP Lock: Oui
Score: 75/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... 9 autres alertes ...]
```

---

#### Option 3 : Voir les Statistiques

1. **Taper** : `3`
2. **Appuyer sur Entrée**
3. **Vous voyez les stats globales**

**Exemple** :
```
=== STATISTIQUES GLOBALES ===

📊 Total alertes: 25
📈 Alertes analysées (24h): 10
💰 ROI moyen: +15.3%
🎯 Taux TP1 atteint: 60%
✅ Taux profitable: 70%

=== DISTRIBUTION PAR RÉSEAU ===

eth       : ████████████████ 16 alertes
bsc       : ████████ 8 alertes
arbitrum  : ██ 1 alertes
```

---

#### Option 5 : Quitter

1. **Taper** : `5`
2. **Appuyer sur Entrée**
3. **Le script se ferme**
4. **Vous revenez à PowerShell** :
   ```
   PS c:\Users\ludo_\Documents\projets\owner\bot-market>
   ```

---

### ÉTAPE 6.3 : Fermer PowerShell (Si Terminé)

**Quand vous avez fini de consulter la DB** :

1. **Taper** :
   ```
   exit
   ```

2. **Appuyer sur Entrée**

3. **La fenêtre PowerShell se ferme**

---

## 🔄 Comment Re-télécharger la DB Plus Tard

**Quand vous voulez consulter à nouveau la DB** (après quelques heures/jours) :

1. **Ouvrir PowerShell** (PAS besoin d'Admin)

2. **Aller dans le dossier** :
   ```
   cd c:\Users\ludo_\Documents\projets\owner\bot-market
   ```

3. **Télécharger** :
   ```
   railway run cat /data/alerts_history.db > alerts_railway.db
   ```

4. **Consulter** :
   ```
   python consulter_db.py
   ```

**C'est tout !** Pas besoin de refaire `railway login` ou `railway link` (c'est déjà fait).

---

## 🆘 Problèmes Fréquents

### ❌ Problème 1 : "railway : Le terme 'railway' n'est pas reconnu"

**Ça veut dire** : Railway CLI n'est pas installé

**Solution** :
1. Retourner à la **PARTIE 1** (Installation)
2. Vérifier que vous avez bien **fermé et rouvert PowerShell** après l'installation

---

### ❌ Problème 2 : "Not logged in"

**Ça veut dire** : Vous n'êtes pas connecté à Railway

**Solution** :
```
railway login
```
Puis suivre les étapes (navigateur s'ouvre → Cliquer "Authorize")

---

### ❌ Problème 3 : "No such file or directory: /data/alerts_history.db"

**Ça veut dire** : La base de données n'existe pas encore sur Railway

**Causes** :
1. Le volume n'a pas été créé sur Railway
2. Le bot n'a pas encore trouvé de token intéressant

**Solution** :
1. Créer le volume sur Railway (Ctrl+K → "volume" → Mount path `/data`)
2. Attendre 10-30 minutes
3. Réessayer

---

### ❌ Problème 4 : "python : Le terme 'python' n'est pas reconnu"

**Ça veut dire** : Python n'est pas installé (ou pas dans le PATH)

**Solution** :

1. **Vérifier si Python est installé** :
   ```
   python --version
   ```
   ou
   ```
   py --version
   ```

2. **Si "py" fonctionne**, utiliser :
   ```
   py consulter_db.py
   ```
   (au lieu de `python consulter_db.py`)

3. **Si rien ne fonctionne**, installer Python :
   - Aller sur : https://www.python.org/downloads/
   - Télécharger Python
   - **IMPORTANT** : Cocher "Add Python to PATH" pendant l'installation

---

## ✅ Checklist Finale

**Une fois que vous avez tout fait** :

- [ ] PowerShell ouvert
- [ ] Railway CLI installé (`railway --version` fonctionne)
- [ ] Connecté à Railway (`railway login` fait)
- [ ] Dans le bon dossier (`cd c:\Users\ludo_\Documents\projets\owner\bot-market`)
- [ ] Projet lié (`railway link dd45f13b-...`)
- [ ] DB téléchargée (`alerts_railway.db` existe et taille > 0)
- [ ] DB consultée (`python consulter_db.py` fonctionne)

**Si tous les ✅** → 🎉 **VOUS AVEZ RÉUSSI !**

---

## 📋 Aide-Mémoire (À Garder)

**Pour consulter la DB à l'avenir** :

```powershell
# 1. Ouvrir PowerShell

# 2. Aller dans le dossier
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# 3. Télécharger la DB
railway run cat /data/alerts_history.db > alerts_railway.db

# 4. Consulter
python consulter_db.py

# 5. Quand terminé
exit
```

**Copier-coller ces 5 lignes** et vous pourrez consulter votre DB en 30 secondes ! 🚀

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Public** : Débutants complets
**Statut** : ✅ **GUIDE ULTRA-DÉTAILLÉ COMPLET**