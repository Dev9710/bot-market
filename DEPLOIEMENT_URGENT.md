# 🚨 DÉPLOIEMENT URGENT - Corriger l'Erreur Railway

## ⚠️ Situation Actuelle

**Erreur sur Railway** :
```
KeyError: 'base_token_address'
File "/app/geckoterminal_scanner_v2.py", line 1063
```

**Cause** : Railway utilise encore l'**ancienne version** du code (non corrigée).

**Solution** : Redéployer le code corrigé.

---

## ✅ SOLUTION RAPIDE (2 minutes)

### Option A : Script Automatique (Recommandé)

**Double-cliquez sur** : `DEPLOYER_CORRECTIONS.bat`

Le script va :
1. ✅ Vérifier que le fichier corrigé existe
2. ✅ Ajouter les fichiers au commit Git
3. ✅ Créer le commit avec message descriptif
4. ✅ Pousser vers GitHub

**Si Railway est connecté à GitHub** → Déploiement automatique !

---

### Option B : Commandes Manuelles

```bash
# 1. Vérifier que vous êtes dans le bon répertoire
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# 2. Ajouter les fichiers corrigés
git add geckoterminal_scanner_v2.py
git add ERREURS_COURANTES.md
git add CORRECTIONS_APPLIQUEES.md
git add VERIFICATION_FINALE.md
git add requirements.txt

# 3. Commit
git commit -m "fix: correct pool_data keys integration - resolve KeyError base_token_address"

# 4. Push
git push origin main
```

**Attendre 2-3 minutes** → Railway redéploie automatiquement

---

### Option C : Railway CLI Direct (Si Git ne fonctionne pas)

```bash
# 1. Se connecter
railway login

# 2. Lier au projet
railway link

# 3. Déployer directement
railway up
```

---

## 🔍 Vérifier le Déploiement

### Étape 1 : Vérifier sur Railway Dashboard

1. Aller sur https://railway.app/dashboard
2. Cliquer sur votre projet
3. Onglet **"Deployments"**
4. Vérifier qu'un nouveau déploiement est en cours

**Vous devriez voir** :
```
Building...
→ Running build command
→ Installing dependencies
→ Deployment successful ✓
```

---

### Étape 2 : Vérifier les Logs

**Via Railway Dashboard** :
- Onglet **"Logs"**
- Chercher : `🔍 SCAN GeckoTerminal démarré`

**Via CLI** :
```bash
railway logs --follow
```

**Vous NE devriez PLUS voir** :
```
❌ KeyError: 'base_token_address'
```

**Vous DEVRIEZ voir** :
```
🔍 SCAN GeckoTerminal démarré
🔒 Vérification sécurité: TOKEN_NAME
✅ Sécurité validée
💾 Sauvegardé en DB
```

---

## 📋 Checklist de Vérification

### Avant Déploiement
- [x] Fichier `geckoterminal_scanner_v2.py` corrigé localement
- [x] Ligne 1064 utilise `pool_address` (pas `base_token_address`)
- [x] Lignes 1126-1134 utilisent les bonnes clés

### Pendant Déploiement
- [ ] Commit créé avec succès
- [ ] Push vers GitHub réussi
- [ ] Railway détecte le nouveau commit
- [ ] Build en cours sur Railway

### Après Déploiement
- [ ] Build terminé avec succès
- [ ] Logs Railway sans `KeyError`
- [ ] Scanner démarre sans erreur
- [ ] Première alerte reçue avec infos sécurité

---

## ⏱️ Temps d'Attente

| Étape | Durée |
|-------|-------|
| Git commit + push | ~10 secondes |
| Railway détecte le push | ~30 secondes |
| Railway build | ~2-3 minutes |
| **TOTAL** | **~3-4 minutes** |

---

## 🆘 Dépannage

### Erreur : "Nothing to commit"

**Cause** : Les fichiers n'ont pas été modifiés ou sont déjà committés.

**Solution** :
```bash
# Vérifier le statut
git status

# Si les modifications sont déjà committées mais pas poussées
git push origin main
```

---

### Erreur : "Railway not found"

**Cause** : Railway CLI n'est pas installé ou pas connecté.

**Solution** :
```bash
# Installer Railway CLI
npm install -g @railway/cli

# OU via PowerShell
iwr https://railway.app/install.ps1 | iex

# Puis se connecter
railway login

# Lier au projet
railway link
```

---

### Erreur : "Permission denied"

**Cause** : Pas les droits d'écriture sur le dépôt GitHub.

**Solution** :
```bash
# Vérifier la configuration Git
git config --list

# Reconfigurer si nécessaire
git config user.name "Votre Nom"
git config user.email "votre@email.com"
```

---

## 📊 Comparaison Avant/Après

### ❌ AVANT (Code Actuel sur Railway)
```python
# Ligne 1063 - ERREUR
token_address = opp["pool_data"]["base_token_address"]  # ← Clé inexistante
```

**Résultat** : `KeyError: 'base_token_address'` → Scanner crash

---

### ✅ APRÈS (Code Corrigé Local)
```python
# Ligne 1064 - CORRIGÉ
token_address = opp["pool_data"]["pool_address"]  # ← Clé correcte
```

**Résultat** : Scanner fonctionne sans erreur

---

## 🎯 Résumé

**Problème** : Railway utilise l'ancienne version avec le bug

**Solution** : Pousser la nouvelle version corrigée

**Méthode la plus simple** :
1. Double-cliquer sur `DEPLOYER_CORRECTIONS.bat`
2. Attendre 3-4 minutes
3. Vérifier les logs Railway

**Aucune erreur** → ✅ **DÉPLOIEMENT RÉUSSI !**

---

## 📞 Support

Si le problème persiste après le redéploiement :

1. **Vérifier la version déployée** :
   ```bash
   railway run cat /app/geckoterminal_scanner_v2.py | grep -A 2 "line 1063"
   ```

2. **Forcer le redéploiement** :
   ```bash
   railway restart
   ```

3. **Consulter les logs détaillés** :
   ```bash
   railway logs --follow
   ```

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Urgence** : 🚨 **HAUTE** - Déployer immédiatement