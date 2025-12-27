# 📱 GUIDE: Configurer 2 Canaux Telegram (V2 + V3)

> **Objectif:** Faire tourner V2 et V3 en parallèle avec des canaux Telegram séparés pour comparer les performances

---

## 🎯 POURQUOI 2 CANAUX SÉPARÉS?

### Avantages
1. **Comparaison directe** - Voir côte à côte les alertes V2 vs V3
2. **Pas de confusion** - Savoir quelle version a envoyé quelle alerte
3. **Test sécurisé** - V2 continue normalement pendant test V3
4. **Statistiques séparées** - Mesurer win rate de chaque version indépendamment
5. **Rollback facile** - Si V3 a un problème, V2 continue de fonctionner

### Inconvénients
- Nécessite créer un nouveau canal/groupe Telegram
- 2 terminaux à surveiller

---

## 🔧 MÉTHODE 1: Un Bot, Deux Canaux (RECOMMANDÉ)

**Principe:** Utiliser le MÊME bot Telegram mais envoyer vers des canaux différents.

### Étape 1: Créer le Nouveau Canal V3

**Sur Telegram:**

1. Ouvrir Telegram
2. Menu → **Nouveau Canal** (ou **New Channel**)
3. Nom du canal: `Bot Trading V3 Test` (ou autre nom)
4. Type: **Canal Public** ou **Privé** (recommandé: privé)
5. Cliquer **Créer**
6. **Ajouter votre bot au canal:**
   - Dans le canal, cliquer sur le nom
   - **Administrateurs** → **Ajouter administrateur**
   - Chercher votre bot (ex: `@VotreBot`)
   - Lui donner les permissions (au minimum: **Publier des messages**)

### Étape 2: Récupérer le Chat ID du Nouveau Canal

**Méthode A: Via votre bot (si déjà fonctionnel)**

1. Envoyer un message dans le nouveau canal (n'importe quoi)
2. Aller sur: `https://api.telegram.org/bot<VOTRE_TOKEN>/getUpdates`
3. Chercher dans le JSON le `"chat":{"id":` pour votre nouveau canal
4. Le Chat ID commence généralement par `-100` pour les canaux

**Exemple JSON:**
```json
{
  "message": {
    "chat": {
      "id": -1001234567890,  ← C'EST ÇA!
      "title": "Bot Trading V3 Test",
      "type": "channel"
    }
  }
}
```

**Méthode B: Via @userinfobot**

1. Ajouter `@userinfobot` au canal comme admin
2. Il enverra automatiquement le Chat ID

**Méthode C: Via script Python rapide**

```bash
python -c "import requests; print(requests.get('https://api.telegram.org/bot<VOTRE_TOKEN>/getUpdates').json())"
```

### Étape 3: Créer le Fichier `.env.v3`

**Dans le dossier du bot:**

```bash
# Créer .env.v3
notepad .env.v3
```

**Contenu de `.env.v3`:**
```bash
# Configuration V3 - Canal Telegram Séparé
TELEGRAM_BOT_TOKEN=votre_token_bot_complet
TELEGRAM_CHAT_ID=-1001234567890

# Remplacer:
# - votre_token_bot_complet par le token de votre bot (même que V2)
# - -1001234567890 par le Chat ID du nouveau canal V3
```

**Exemple concret:**
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
TELEGRAM_CHAT_ID=-1001987654321
```

### Étape 4: Vérifier la Configuration V2

**Votre `.env` existant (pour V2):**
```bash
# Configuration V2 - Canal Telegram Actuel
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
TELEGRAM_CHAT_ID=-1001234567890  # Ancien canal (V2)
```

**Important:** V2 continue d'utiliser `.env`, V3 utilisera `.env.v3`.

---

### Étape 5: Lancer les Deux Versions en Parallèle

**Terminal 1 - V2:**
```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market
python geckoterminal_scanner_v2.py
```

**Sortie attendue:**
```
🚀 Bot Trading V2 démarré...
📱 Telegram configuré: Chat ID = -1001234567890
...
```

**Terminal 2 - V3:**
```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market
python geckoterminal_scanner_v3.py
```

**Sortie attendue:**
```
🔧 V3: Configuration chargée depuis .env.v3
📱 V3 Telegram: Chat ID = -1001987654321
🚀 Scanner V3 démarré...
...
```

**Vérification:**
- Les deux Chat ID doivent être **DIFFÉRENTS**
- V2 envoie vers l'ancien canal
- V3 envoie vers le nouveau canal

---

## 🔧 MÉTHODE 2: Deux Bots Séparés (OPTIONNEL)

**Si vous voulez vraiment 2 bots différents (pas recommandé mais possible):**

### Étape 1: Créer un Deuxième Bot

**Via @BotFather:**

1. Aller sur Telegram, chercher `@BotFather`
2. `/newbot`
3. Nom du bot: `Trading Bot V3` (ou autre)
4. Username: `VotreNomV3Bot` (doit finir par `bot`)
5. Copier le nouveau **token**

### Étape 2: Créer `.env.v3` avec le Nouveau Bot

```bash
# .env.v3 - Bot séparé pour V3
TELEGRAM_BOT_TOKEN=9876543210:XYZabcDEFghiJKLmnoPQRstu9876543  # NOUVEAU token
TELEGRAM_CHAT_ID=-1001987654321  # Nouveau canal
```

### Étape 3: Ajouter le Nouveau Bot au Canal V3

Même procédure qu'avant mais avec le **nouveau bot**.

---

## 📊 COMPARAISON DES ALERTES

### Structure Attendue

**Canal V2 (Ancien):**
```
🆕 Nouvelle opportunité sur le token PEPE

💎 PEPE/WETH
⛓️ Blockchain: Ethereum

🎯 SCORE: 72/100 ⭐️⭐️ BON
   Base: 58 | Momentum: +14
📊 Confiance: 80% (fiabilité données)

[... reste de l'alerte V2 ...]
```

**Canal V3 (Nouveau):**
```
🆕 Nouvelle opportunité sur le token PEPE

💎 PEPE/WETH
⛓️ Blockchain: Ethereum

🎯 SCORE: 85/100 ⭐️⭐️⭐️ TRÈS BON
   Base: 68 | Momentum: +17
📊 Confiance: 80% (fiabilité données)
🎖️ TIER V3: 💎💎 HIGH (35-50% WR attendu)
   V3 Checks: Vélocité EXCELLENTE: 52.3 | Type pump OK: TRES_RAPIDE | Âge OPTIMAL: 63.2h

[... reste de l'alerte V3 avec tier ...]
```

**Différences visibles:**
- ✅ V3 a le **TIER** (💎💎 HIGH)
- ✅ V3 a les **V3 Checks** (raisons filtrage)
- ✅ V3 peut avoir **score plus élevé** (bonus réseau/vélocité/âge)

---

## 🧪 TESTER LA CONFIGURATION

### Test 1: Vérifier Que V3 Utilise Bien `.env.v3`

**Lancer V3:**
```bash
python geckoterminal_scanner_v3.py
```

**Regarder les premiers logs:**
```
🔧 V3: Configuration chargée depuis .env.v3  ← BON
📱 V3 Telegram: Chat ID = -1001987654321     ← Nouveau canal

OU

⚠️ V3: .env.v3 non trouvé, utilisation .env par défaut  ← Créer .env.v3!
```

### Test 2: Vérifier Séparation des Canaux

**Envoyer un message test:**

Temporairement ajouter dans V3 au démarrage (ligne ~3000):
```python
# TEST - À RETIRER APRÈS
send_telegram("🧪 TEST V3: Bot V3 démarré!")
```

**Résultat attendu:**
- Message `🧪 TEST V3` apparaît SEULEMENT dans canal V3
- Canal V2 ne reçoit RIEN

### Test 3: Vérifier les Deux Tournent en Parallèle

**Après 5-10 minutes:**

**Canal V2:**
- Reçoit alertes normales V2
- Pas de mention "TIER" ou "V3"

**Canal V3:**
- Reçoit alertes avec TIER
- Moins d'alertes que V2 (filtrage plus strict)
- Mention "V3 Checks"

---

## 📈 SUIVI DES PERFORMANCES

### Tableau de Comparaison (1 Semaine)

| Métrique | V2 | V3 | Différence |
|----------|----|----|------------|
| **Alertes total** | 78 | 34 | -56% |
| **Trades pris** | 78 | 34 | - |
| **Winners** | 15 (19.2%) | 14 (41.2%) | +115% |
| **Losers** | 63 (80.8%) | 20 (58.8%) | -27% |
| **ROI moyen** | +32% | +87% | +172% |

**Exemple réel attendu après 1 semaine.**

---

## 🚨 PROBLÈMES FRÉQUENTS

### Problème 1: V3 Envoie dans le Canal V2

**Cause:** `.env.v3` non lu ou mal configuré

**Solution:**
```bash
# Vérifier que .env.v3 existe
dir .env.v3

# Vérifier le contenu
type .env.v3

# Vérifier les logs au démarrage de V3
python geckoterminal_scanner_v3.py
# Doit afficher: "V3: Configuration chargée depuis .env.v3"
```

---

### Problème 2: "python-dotenv non installé"

**Erreur:**
```
⚠️ V3: python-dotenv non installé, variables système utilisées
```

**Solution:**
```bash
pip install python-dotenv
```

**OU définir variables système (Windows):**
```cmd
set TELEGRAM_BOT_TOKEN=votre_token
set TELEGRAM_CHAT_ID=-1001987654321
python geckoterminal_scanner_v3.py
```

---

### Problème 3: Les Deux Versions Envoient dans le Même Canal

**Cause:** `.env.v3` a le même Chat ID que `.env`

**Solution:**
```bash
# Vérifier les Chat ID
type .env
type .env.v3

# Doivent être DIFFÉRENTS:
# .env:     TELEGRAM_CHAT_ID=-1001234567890  (V2)
# .env.v3:  TELEGRAM_CHAT_ID=-1001987654321  (V3 - différent!)
```

---

### Problème 4: "Chat not found" ou "Forbidden"

**Cause:** Bot pas ajouté au canal ou pas les permissions

**Solution:**
1. Aller dans le canal V3
2. Paramètres → Administrateurs
3. Vérifier que le bot est admin
4. Permissions: **Publier des messages** = activé

---

### Problème 5: Alertes Dupliquées

**Cause:** Le même token détecté par V2 et V3 (normal!)

**Comportement attendu:**
- V2 peut alerter sur un token avec score 65
- V3 peut rejeter ce même token (vélocité < 5)
- OU V3 peut alerter avec tier MEDIUM vs V2 sans tier

**Ce n'est PAS un problème** - C'est justement l'intérêt de comparer!

---

## 📋 CHECKLIST FINALE

Avant de lancer en production:

- [ ] ✅ Nouveau canal Telegram V3 créé
- [ ] ✅ Bot ajouté au canal V3 comme admin
- [ ] ✅ Chat ID du canal V3 récupéré
- [ ] ✅ Fichier `.env.v3` créé avec bon Chat ID
- [ ] ✅ `python-dotenv` installé (`pip install python-dotenv`)
- [ ] ✅ Test V3: log affiche "Configuration chargée depuis .env.v3"
- [ ] ✅ Test V3: Chat ID affiché = celui du nouveau canal
- [ ] ✅ V2 tourne toujours normalement
- [ ] ✅ V3 envoie vers canal séparé (vérifié avec message test)
- [ ] ✅ Tableau Excel/Google Sheets prêt pour tracker performances

---

## 🎯 RÉSUMÉ RAPIDE

### Configuration Minimale (5 Minutes)

```bash
# 1. Créer canal Telegram "Bot V3 Test"
# 2. Ajouter votre bot au canal comme admin
# 3. Récupérer Chat ID du canal (méthode @userinfobot ou getUpdates)
# 4. Créer .env.v3
echo TELEGRAM_BOT_TOKEN=votre_token > .env.v3
echo TELEGRAM_CHAT_ID=-1001987654321 >> .env.v3

# 5. Installer dotenv si nécessaire
pip install python-dotenv

# 6. Lancer V2 (terminal 1)
python geckoterminal_scanner_v2.py

# 7. Lancer V3 (terminal 2)
python geckoterminal_scanner_v3.py

# 8. Vérifier logs:
# V2: "Telegram configuré: Chat ID = -100123..."
# V3: "V3 Telegram: Chat ID = -100198..."
# Les deux Chat ID doivent être DIFFÉRENTS
```

---

## 📊 EXEMPLE DE FICHIERS

### `.env` (V2 - Existant)
```bash
# Bot Trading V2 - Canal Principal
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
TELEGRAM_CHAT_ID=-1001234567890
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### `.env.v3` (V3 - Nouveau)
```bash
# Bot Trading V3 - Canal Test
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
TELEGRAM_CHAT_ID=-1001987654321
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/.../v3
```

**Note:** Même bot token, Chat ID différents!

---

## 🔄 ROLLBACK SI PROBLÈME

Si V3 a un bug critique:

```bash
# Terminal 2 (V3)
Ctrl+C  # Arrêter V3

# Terminal 1 (V2)
# Continuer normalement, pas d'impact
```

V2 n'est **jamais affecté** par V3!

---

**Date:** 26 décembre 2025
**Version:** Guide pour configuration V2 + V3 parallèle
**Statut:** ✅ Prêt pour déploiement
