# Comment arrêter l'ancien bot et lancer seulement le nouveau

## 🔴 PROBLÈME DÉTECTÉ

Vous recevez **2 types d'alertes** :
1. ✅ Nouvelle alerte (20:16) : "Analyse détaillée" avec descriptions intelligentes
2. ❌ Ancienne alerte (20:18) : "explications adaptées débutants" sans descriptions

**Cause** : Deux instances du bot tournent en même temps (ancien + nouveau code)

---

## ✅ SOLUTION : Arrêter tous les bots et relancer

### Étape 1 : Arrêter TOUS les bots Python en cours

#### Sur Windows (Local)

```bash
# Ouvrir le Gestionnaire des tâches
Ctrl + Shift + Esc

# Onglet "Processus"
# Chercher "python" ou "python.exe"
# Clic droit → Arrêter le processus

# OU en ligne de commande :
taskkill /F /IM python.exe
```

#### Sur Railway

```bash
# Dans le dashboard Railway
→ Aller dans votre service
→ Cliquer sur "Settings"
→ Cliquer sur "Redeploy"

# OU supprimer et recréer le déploiement
```

#### Sur Docker

```bash
# Arrêter tous les conteneurs
docker-compose down

# OU arrêter un conteneur spécifique
docker stop crypto-monitor
```

---

### Étape 2 : Vérifier qu'aucun bot ne tourne

```bash
# Windows
tasklist | findstr python

# Si vide = OK, aucun bot ne tourne
```

---

### Étape 3 : Relancer SEULEMENT le nouveau bot

#### Local

```bash
cd C:\Users\BisolyL\Documents\owner\bot-market
python alerte.py
```

#### Railway

Le bot redémarre automatiquement après le redeploy.

#### Docker

```bash
docker-compose up -d --build
```

---

## 🔍 COMMENT IDENTIFIER L'ANCIEN BOT

### Ancien format (à SUPPRIMER)
```
🌍 Top activités crypto détectées
(Volume anormal — explications adaptées débutants)    ← ANCIEN

#1 — WETH
💰 Prix : 3194.780000 $
📈 Volume 1m estimé : 721,864,611 $
🔥 Multiplicateur : x1047.7
→ Cela indique qu'un mouvement inhabituel...       ← ANCIEN
```

**Indices** :
- ❌ "explications adaptées débutants"
- ❌ "→ Cela indique qu'un mouvement inhabituel..."
- ❌ Pas de section "POURQUOI CETTE ALERTE ?"
- ❌ Pas de section "CE QUE ÇA SIGNIFIE"
- ❌ Pas de section "QUE FAIRE"

---

### Nouveau format (à GARDER)
```
🌍 Top activités crypto détectées
(Volume anormal — Analyse détaillée)              ← NOUVEAU

#1 — TORN (Tornado Cash)
💰 Prix : 13.960000 $
📈 Volume 1m estimé : 21,564 $
🔥 Multiplicateur : x7.3

🚨 POURQUOI CETTE ALERTE ?                         ← NOUVEAU
✓ Volume x7.3 supérieur à la moyenne
⚠️ Prix en baisse : -3.84% sur 24h

💡 CE QUE ÇA SIGNIFIE :                            ← NOUVEAU
Gros vendeurs liquident leurs positions...

⚠️ QUE FAIRE :                                     ← NOUVEAU
⚠️ ATTENTION - Signal de vente potentiel
```

**Indices** :
- ✅ "Analyse détaillée"
- ✅ Section "🚨 POURQUOI CETTE ALERTE ?"
- ✅ Section "💡 CE QUE ÇA SIGNIFIE"
- ✅ Section "⚠️ QUE FAIRE"
- ✅ Exchanges et blockchains affichés

---

## 🎯 VÉRIFICATION POST-REDÉMARRAGE

Attendez la prochaine alerte et vérifiez qu'elle contient :

✅ "(Volume anormal — Analyse détaillée)"
✅ "🚨 POURQUOI CETTE ALERTE ?"
✅ "💡 CE QUE ÇA SIGNIFIE :"
✅ "⚠️ QUE FAIRE :"
✅ Exchanges listés
✅ Blockchains affichées

❌ PLUS DE "(Volume anormal — explications adaptées débutants)"
❌ PLUS DE "→ Cela indique qu'un mouvement inhabituel..."

---

## 🔧 SI LE PROBLÈME PERSISTE

### Vérifier les fichiers déployés

```bash
# Vérifier que alerte.py contient le nouveau code
cd bot-market
grep "Analyse détaillée" alerte.py

# Doit retourner :
# txt += "_(Volume anormal — Analyse détaillée)_\n\n"
```

### Vérifier Railway/Docker

Si déployé sur Railway/Docker, assurez-vous que :
1. Le code a bien été push sur GitHub
2. Railway a bien redéployé
3. Pas d'ancien déploiement actif

```bash
# Push le nouveau code
git add .
git commit -m "Fix: Supprimer ancien format alertes"
git push origin main

# Railway redéploie automatiquement
```

---

## ✅ RÉSOLUTION RAPIDE (RÉSUMÉ)

```bash
# 1. Arrêter TOUS les bots
taskkill /F /IM python.exe

# 2. Vérifier qu'aucun ne tourne
tasklist | findstr python

# 3. Relancer SEULEMENT le nouveau
cd bot-market
python alerte.py

# 4. Attendre la prochaine alerte et vérifier
# Doit contenir "Analyse détaillée" + sections explicatives
```

---

## 📞 SI VOUS ÊTES SUR RAILWAY

```bash
# Option 1 : Redéployer
Dashboard → Service → Settings → Redeploy

# Option 2 : Restart
Dashboard → Service → Settings → Restart

# Option 3 : Variables d'environnement
Vérifier que TELEGRAM_BOT_TOKEN est bien configuré
```

---

**Date** : 2025-11-14
**Version** : 3.0
