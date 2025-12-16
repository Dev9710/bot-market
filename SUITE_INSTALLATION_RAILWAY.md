# ✅ Railway CLI Installé - Prochaines Étapes

**Statut** : ✅ Installation réussie !

---

## 🎉 Ce Que Vous Avez Vu

```
added 17 packages in 4s
```

✅ **C'est bon !** Railway CLI et ses dépendances sont installés.

**Les avertissements sont normaux** :
- `npm warn deprecated node-domexception@1.0.0` → Juste un avertissement, pas une erreur
- `New minor version of npm available! 11.6.2 -> 11.7.0` → Mise à jour optionnelle de npm (pas obligatoire)

---

## 📋 ÉTAPE SUIVANTE : Vérifier l'Installation

**Dans PowerShell, tapez** :

```powershell
railway --version
```

**Vous devriez voir** :
```
railway version 3.x.x
```

✅ **Si vous voyez un numéro de version** → Railway CLI fonctionne !

---

## 🚀 MAINTENANT : Se Connecter à Railway

### ÉTAPE 1 : Login

**Tapez** :
```powershell
railway login
```

**Appuyez sur Entrée**

**Ce qui va se passer** :
1. PowerShell affiche : `Opening browser to authenticate...`
2. **Votre navigateur s'ouvre automatiquement**
3. Page Railway : **Cliquez sur "Authorize"**
4. Page affiche : "Success! You can close this window"
5. **Retournez dans PowerShell**
6. Vous voyez : `✓ Logged in as [votre email]`

---

### ÉTAPE 2 : Aller dans le Dossier Bot

**Tapez** :
```powershell
cd c:\Users\ludo_\Documents\projets\owner\bot-market
```

**Appuyez sur Entrée**

---

### ÉTAPE 3 : Lier le Projet

**Tapez** :
```powershell
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845
```

**Appuyez sur Entrée**

**Si une liste de services apparaît** :
- Utilisez les **flèches ↑↓** pour sélectionner votre service (bot)
- **Appuyez sur Entrée**

**Vous verrez** :
```
✓ Linked to project: [nom-projet]
✓ Linked to service: [nom-service]
```

---

### ÉTAPE 4 : Télécharger la Base de Données

**Tapez** :
```powershell
railway run cat /data/alerts_history.db > alerts_railway.db
```

**Appuyez sur Entrée**

**Attendez 5-15 secondes**

**Vérifiez que le fichier a été créé** :
```powershell
dir alerts_railway.db
```

**Regardez la colonne "Length"** :
- **Si > 0** (ex: 45056) → ✅ DB téléchargée avec succès !
- **Si = 0** → La DB n'existe pas encore sur Railway (volume pas créé ou aucune alerte)

---

### ÉTAPE 5 : Consulter la DB

**Tapez** :
```powershell
python consulter_db.py
```

**Un menu s'affiche** :
```
=== MENU PRINCIPAL ===

1. Afficher les dernières alertes
2. Afficher le détail d'une alerte
3. Afficher les statistiques globales
4. Afficher les tokens suivis
5. Quitter

Votre choix (1-5):
```

**Tapez `1`** pour voir les dernières alertes → **Entrée**

**Tapez `5`** pour quitter → **Entrée**

---

## 📋 Résumé des Commandes (Copier-Coller)

**Tout en une fois** :

```powershell
# Vérifier l'installation
railway --version

# Se connecter
railway login

# Aller dans le dossier
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Lier le projet
railway link dd45f13b-3e76-4ca3-9d0b-2ef274d45845

# Télécharger la DB
railway run cat /data/alerts_history.db > alerts_railway.db

# Vérifier la taille
dir alerts_railway.db

# Consulter
python consulter_db.py
```

---

## ⚠️ Si la DB est Vide (Length = 0)

**Cela signifie** : Le volume n'est pas créé sur Railway OU aucune alerte sauvegardée

**Solution** :

1. **Créer le volume sur Railway** :
   - Aller sur : https://railway.com/project/dd45f13b-3e76-4ca3-9d0b-2ef274d45845
   - **Ctrl+K** → Taper "volume" → "Create Volume"
   - Sélectionner votre service (bot)
   - **Mount Path** : `/data`
   - Confirmer

2. **Redémarrer le service** :
   - Service → Menu (⋯) → Restart

3. **Attendre 10-30 minutes** que le bot trouve un token

4. **Re-télécharger la DB** :
   ```powershell
   railway run cat /data/alerts_history.db > alerts_railway.db
   ```

---

## 🎯 Prochaine Action

**Tapez maintenant** (dans PowerShell) :

```powershell
railway --version
```

**Pour vérifier que Railway CLI fonctionne !**

Ensuite, continuez avec les commandes ci-dessus. 🚀

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Statut** : ✅ **INSTALLATION RÉUSSIE - PRÊT À UTILISER**