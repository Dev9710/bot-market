# 📊 Procédure d'Accès à Votre Base de Données - Step by Step

**Votre Projet Railway** : `dd45f13b-3e76-4ca3-9d0b-2ef274d45845`
**Votre Service** : `8ed08522-549d-40d4-9ae2-bcd8505bdcff`

---

## 🎯 PARTIE 1 : Créer le Volume (Sur Railway Dashboard)

### ÉTAPE 1.1 : Ouvrir Votre Projet

1. **Cliquer sur ce lien** :
   ```
   https://railway.com/project/dd45f13b-3e76-4ca3-9d0b-2ef274d45845
   ```

2. Vous verrez votre projet avec le service actif

---

### ÉTAPE 1.2 : Accéder aux Settings du Service

1. **Cliquer sur le service** (le carré/rectangle avec votre app)
   - Il devrait avoir une icône verte (= actif)

2. En haut de la page, vous verrez plusieurs onglets :
   ```
   Deployments | Variables | Settings | Metrics | Logs
   ```

3. **Cliquer sur l'onglet "Settings"**

---

### ÉTAPE 1.3 : Vérifier/Créer le Volume

1. Dans la page Settings, **descendre** jusqu'à trouver la section **"Volumes"**

2. **Regarder ce qui est affiché** :

#### ❌ CAS A : Vous voyez "No volumes attached"

**Action** :
1. **Cliquer sur le bouton "+ New Volume"** (ou "+ Add Volume")

2. Une fenêtre apparaît avec 2 champs :

   **CHAMP 1 - Mount Path** :
   ```
   /data
   ```
   ⚠️ **IMPORTANT** : Tapez exactement `/data` (avec le slash au début)

   **CHAMP 2 - Size (optionnel)** :
   ```
   1
   ```
   (1 GB = largement suffisant)

3. **Cliquer sur "Add"** ou "Create Volume"

4. **⚠️ IMPORTANT** : Railway va afficher un message :
   ```
   "The service will be restarted to apply changes"
   ```

5. **Cliquer sur "Confirm"** ou attendre le redémarrage automatique

6. **Attendre 30-60 secondes** que le service redémarre
   - Vous verrez un spinner/loader
   - Puis l'icône redevient verte

7. ✅ **Volume créé !** Vous devriez maintenant voir :
   ```
   /data → 1 GB
   Created: [date d'aujourd'hui]
   ```

#### ✅ CAS B : Vous voyez déjà un volume "/data"

**Parfait !** Le volume existe déjà.

Vous devriez voir quelque chose comme :
```
Mount Point: /data
Size: 1 GB
Created: [date]
```

➡️ **Passer directement à la PARTIE 2**

---

### ÉTAPE 1.4 : Vérifier que le Bot Utilise le Volume

1. **Cliquer sur l'onglet "Logs"** (en haut)

2. **Chercher dans les logs** (utilisez Ctrl+F) :
   ```
   💾 Sauvegardé en DB
   ```

3. **Si vous voyez** :
   ```
   💾 Sauvegardé en DB: /data/alerts_history.db
   ```
   ✅ **PARFAIT !** Le bot utilise bien le volume

4. **Si vous ne voyez rien** :
   - Le bot n'a pas encore trouvé de token intéressant
   - Attendre 5-10 minutes (le scan se fait toutes les 5 min)

---

## 🎯 PARTIE 2 : Installer Railway CLI (Sur Votre PC)

### ÉTAPE 2.1 : Ouvrir PowerShell en Administrateur

1. **Cliquer sur le menu Démarrer** (Windows)

2. **Taper** : `PowerShell`

3. **Clic droit** sur "Windows PowerShell"

4. **Sélectionner** : "Exécuter en tant qu'administrateur"

5. **Cliquer sur "Oui"** dans la fenêtre de confirmation

6. Une fenêtre PowerShell s'ouvre avec un fond bleu foncé

---

### ÉTAPE 2.2 : Vérifier si Railway CLI est Déjà Installé

Dans PowerShell, **taper** :
```powershell
railway --version
```

**Appuyer sur Entrée**

**2 RÉSULTATS POSSIBLES** :

#### ✅ Résultat A : Une version s'affiche
```
railway version 3.x.x
```
➡️ **Railway CLI est installé !** Passer à la PARTIE 3

#### ❌ Résultat B : Erreur
```
railway : Le terme 'railway' n'est pas reconnu...
```
➡️ **Railway CLI n'est pas installé**, continuer ci-dessous

---

### ÉTAPE 2.3 : Installer Railway CLI

Dans la même fenêtre PowerShell (Admin), **taper** :

```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

**Appuyer sur Entrée**

**Ce qui va se passer** :
1. Téléchargement du script d'installation (~5 secondes)
2. Installation de Railway CLI (~20 secondes)
3. Vous verrez des messages défiler
4. À la fin : `Railway CLI installed successfully!` ou similaire

**IMPORTANT** :
1. **Fermer la fenêtre PowerShell** (tapez `exit` ou cliquez sur la croix)
2. **Rouvrir PowerShell** (pas besoin d'Admin cette fois)
3. **Vérifier l'installation** :
   ```powershell
   railway --version
   ```

**Vous devriez voir** :
```
railway version 3.x.x
```

✅ **Installation réussie !**

---

## 🎯 PARTIE 3 : Se Connecter à Railway CLI

### ÉTAPE 3.1 : Login

Dans PowerShell (normal, pas Admin nécessaire), **taper** :

```bash
railway login
```

**Appuyer sur Entrée**

**Ce qui va se passer** :

1. PowerShell affiche :
   ```
   Opening browser to authenticate...
   ```

2. **Votre navigateur s'ouvre automatiquement** sur une page Railway

3. La page affiche :
   ```
   CLI Login
   Authorize Railway CLI to access your account

   [Authorize] [Cancel]
   ```

4. **Cliquer sur le bouton "Authorize"**

5. La page affiche :
   ```
   Success! You can close this window
   ```

6. **Retourner dans PowerShell**

7. PowerShell affiche :
   ```
   ✓ Logged in as [votre email ou nom]
   ```

✅ **Vous êtes connecté !**

---

## 🎯 PARTIE 4 : Lier Votre Projet

### ÉTAPE 4.1 : Aller dans Votre Répertoire Bot

Dans PowerShell, **taper** :

```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market
```

**Appuyer sur Entrée**

**PowerShell affiche maintenant** :
```
PS c:\Users\ludo_\Documents\projets\owner\bot-market>
```

---

### ÉTAPE 4.2 : Lier au Projet Railway

**Taper** :

```bash
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845
```

**Appuyer sur Entrée**

**Ce qui va se passer** :

1. Railway CLI se connecte à votre projet

2. **Si vous avez plusieurs services**, Railway affiche une liste :
   ```
   ? Select a service:
     > service-1
       service-2
   ```

   **Utiliser les flèches ↑↓** pour sélectionner le bon service
   **Appuyer sur Entrée**

3. Railway CLI affiche :
   ```
   ✓ Linked to project: [nom-du-projet]
   ✓ Linked to service: [nom-du-service]
   ```

✅ **Projet lié !**

---

## 🎯 PARTIE 5 : Télécharger la Base de Données

### ÉTAPE 5.1 : Vérifier que Vous Êtes dans le Bon Répertoire

Dans PowerShell, **taper** :

```bash
pwd
```

**Vous devriez voir** :
```
Path
----
c:\Users\ludo_\Documents\projets\owner\bot-market
```

✅ **Bon répertoire !**

---

### ÉTAPE 5.2 : Télécharger la DB

**Taper** :

```bash
railway run cat /data/alerts_history.db > alerts_railway.db
```

**Appuyer sur Entrée**

**Ce qui va se passer** :

1. Railway CLI se connecte à votre service
   ```
   Connecting to service...
   ```

2. Lit le fichier `/data/alerts_history.db` sur Railway

3. Le sauvegarde en local dans `alerts_railway.db`

4. **Durée** : 5-15 secondes (selon taille de la DB)

5. PowerShell revient au prompt :
   ```
   PS c:\Users\ludo_\Documents\projets\owner\bot-market>
   ```

---

### ÉTAPE 5.3 : Vérifier que la DB a été Téléchargée

**Taper** :

```bash
dir alerts_railway.db
```

**Vous devriez voir** :
```
    Directory: c:\Users\ludo_\Documents\projets\owner\bot-market

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        13/12/2025     15:30          45056 alerts_railway.db
```

**IMPORTANT** : Regarder la colonne **"Length"** (taille) :

#### ✅ CAS A : Taille > 0 (ex: 45056)
**PARFAIT !** La DB existe et contient des données

➡️ **Passer à la PARTIE 6** pour consulter

#### ❌ CAS B : Taille = 0
**Problème** : La DB n'existe pas encore sur Railway

**Raisons possibles** :
1. **Aucune alerte sauvegardée encore** (le bot vient de démarrer)
2. **Le volume n'était pas créé** quand les alertes ont été envoyées
3. **Le bot a crashé** avant de sauvegarder

**Solution** :

1. **Retourner sur Railway Dashboard** → Onglet "Logs"

2. **Chercher** (Ctrl+F) :
   ```
   💾 Sauvegardé en DB
   ```

3. **SI VOUS VOYEZ** ce message :
   ✅ La DB existe, réessayer le téléchargement :
   ```bash
   railway run cat /data/alerts_history.db > alerts_railway.db
   ```

4. **SI VOUS NE VOYEZ PAS** ce message :
   ⏳ Le bot n'a pas encore trouvé de token intéressant

   **Attendre 10-30 minutes** puis réessayer

---

## 🎯 PARTIE 6 : Consulter la Base de Données

### MÉTHODE 1 : Script Python (Le Plus Simple)

**Dans PowerShell, taper** :

```bash
python consulter_db.py
```

**Appuyer sur Entrée**

**Le script affiche un menu** :
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

**EXEMPLES D'UTILISATION** :

#### Voir les 10 Dernières Alertes
**Taper** : `1` **puis Entrée**

Vous verrez :
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[... 9 autres alertes ...]
```

#### Voir les Statistiques
**Taper** : `3` **puis Entrée**

Vous verrez :
```
=== STATISTIQUES GLOBALES ===

📊 Total alertes: 25
📈 Alertes analysées (24h): 10
💰 ROI moyen: +15.3%
🎯 Taux TP1 atteint: 60%
✅ Taux profitable: 70%

[... graphiques en texte ...]
```

#### Quitter
**Taper** : `5` **puis Entrée**

---

### MÉTHODE 2 : DB Browser for SQLite (Interface Graphique)

#### ÉTAPE 6.1 : Installer DB Browser

1. **Ouvrir votre navigateur**

2. **Aller sur** : https://sqlitebrowser.org/dl/

3. **Cliquer sur** : "DB Browser for SQLite - Standard installer for 64-bit Windows"

4. **Télécharger** le fichier `.exe`

5. **Double-cliquer** sur le fichier téléchargé

6. **Suivre l'installation** (tout laisser par défaut, cliquer "Next" → "Install" → "Finish")

---

#### ÉTAPE 6.2 : Ouvrir la DB

1. **Lancer "DB Browser for SQLite"** (icône sur le bureau ou menu Démarrer)

2. **Cliquer sur "Open Database"** (ou "Ouvrir une base de données")
   - Icône : Dossier ouvert (en haut à gauche)

3. **Naviguer vers** :
   ```
   c:\Users\ludo_\Documents\projets\owner\bot-market\
   ```

4. **Sélectionner** : `alerts_railway.db`

5. **Cliquer sur "Ouvrir"**

---

#### ÉTAPE 6.3 : Consulter les Tables

**Onglet "Database Structure"** (Structure de la base) :
- Voir les 3 tables :
  - `alerts` (alertes principales)
  - `price_tracking` (suivi des prix)
  - `alert_analysis` (analyses 24h)

**Onglet "Browse Data"** (Parcourir les données) :
1. **Menu déroulant "Table"** : Sélectionner `alerts`
2. **Voir toutes les alertes** dans un tableau

**Colonnes visibles** :
- `id`, `created_at`, `token_name`, `network`
- `opportunity_score`, `security_score`
- `price_usd`, `volume_24h`, `liquidity`
- `entry_price`, `stop_loss`, `tp1`, `tp2`, `tp3`
- etc.

**Onglet "Execute SQL"** (Exécuter SQL) :
**Taper vos propres requêtes**, exemple :

```sql
-- Voir les 5 meilleures alertes par score
SELECT
    token_name,
    network,
    opportunity_score,
    security_score,
    price_usd,
    volume_24h
FROM alerts
ORDER BY opportunity_score DESC
LIMIT 5;
```

**Cliquer sur le bouton "Play"** (▶️) pour exécuter

---

## 🔄 Mettre à Jour la DB (Re-télécharger)

Après quelques heures/jours, pour voir les nouvelles alertes :

```bash
# Dans PowerShell
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Re-télécharger (écrase l'ancienne version)
railway run cat /data/alerts_history.db > alerts_railway.db

# Consulter
python consulter_db.py
```

**OU** créer un fichier avec la date :

```bash
# Télécharger avec un nom unique
railway run cat /data/alerts_history.db > alerts_13dec.db

# Consulter
python consulter_db.py
# (puis choisir le fichier à ouvrir)
```

---

## 🆘 Dépannage

### ❌ Erreur : "No such file or directory: /data/alerts_history.db"

**Vérifications** :

1. **Le volume est-il créé ?**
   - Railway Dashboard → Service → Settings → Volumes
   - Doit afficher : `/data → 1GB`

2. **Le bot a-t-il sauvegardé des alertes ?**
   - Railway Dashboard → Service → Logs
   - Chercher : `💾 Sauvegardé en DB`

3. **Le bot tourne-t-il ?**
   - Railway Dashboard → Service → Icône verte (actif)

**Si le volume n'existe pas** :
➡️ **Retour à PARTIE 1** pour créer le volume

**Si aucune alerte** :
➡️ **Attendre 10-30 minutes** que le bot trouve un token

---

### ❌ Erreur : "railway: command not found"

**Solution** :

1. **Réinstaller Railway CLI** :
   ```powershell
   iwr https://railway.app/install.ps1 -useb | iex
   ```

2. **Fermer et rouvrir PowerShell**

3. **Vérifier** :
   ```bash
   railway --version
   ```

---

### ❌ Erreur : "Not logged in"

**Solution** :

```bash
railway login
```

Navigateur s'ouvre → Cliquer "Authorize"

---

### ❌ Erreur : "Project not found"

**Solution** : Re-lier le projet avec l'ID exact :

```bash
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845
```

---

## ✅ Checklist Finale

- [ ] Volume `/data` créé sur Railway (PARTIE 1)
- [ ] Railway CLI installé (PARTIE 2)
- [ ] Connecté avec `railway login` (PARTIE 3)
- [ ] Projet lié avec `railway link` (PARTIE 4)
- [ ] DB téléchargée avec succès (PARTIE 5)
- [ ] DB consultée (PARTIE 6)
- [ ] Logs Railway montrent "💾 Sauvegardé en DB"

**Si tous les ✅ sont cochés** → 🎉 **ACCÈS DB OPÉRATIONNEL !**

---

## 🎯 Commandes de Référence Rapide

```bash
# Se connecter (une fois)
railway login

# Aller dans le répertoire
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Lier le projet (une fois)
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845

# Télécharger la DB (à chaque consultation)
railway run cat /data/alerts_history.db > alerts_railway.db

# Consulter
python consulter_db.py

# Voir les logs Railway
railway logs --follow
```

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Projet Railway** : `dd45f13b-3e76-4ca3-9d0b-2ef274d45845`
**Statut** : ✅ **PROCÉDURE COMPLÈTE POUR VOTRE PROJET**