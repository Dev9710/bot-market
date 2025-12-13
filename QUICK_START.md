# ⚡ Quick Start Guide

Guide ultra-rapide pour démarrer en 5 minutes.

---

## 🚀 Démarrage Local (2 minutes)

### 1. Variables d'environnement

Créer `.env` :
```env
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 2. Installer & Lancer

```bash
pip install -r requirements.txt
python geckoterminal_scanner_v2.py
```

✅ **C'est tout !** Le bot scanne et envoie des alertes Telegram.

---

## 🚂 Démarrage Railway (3 minutes)

### 1. Déployer

```bash
railway login
railway init
railway up
```

### 2. Configurer

**Dans Railway Dashboard → Variables** :
```
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

**Dans Railway Dashboard → Settings → Volumes** :
- Add Volume : `/data` (1GB)

### 3. Vérifier

```bash
railway logs
```

Devrait afficher :
```
✅ Système de sécurité activé
🔍 Scan réseau: ETH
```

✅ **En production !**

---

## 📊 Consulter la Base de Données

### Option 1 : Script Local

```bash
python consulter_db.py
```

### Option 2 : Télécharger depuis Railway

```bash
railway run cat /data/alerts_history.db > alerts_local.db
python consulter_db.py
```

### Option 3 : Dashboard Web (Recommandé)

Voir [ACCES_DB_RAILWAY.md](ACCES_DB_RAILWAY.md) pour déployer le dashboard Streamlit.

---

## 🛡️ Comprendre le Système de Sécurité

### Blocage Automatique

Le bot **NE VOUS ENVERRA PAS** d'alerte si :
- ❌ Honeypot détecté
- ❌ LP non lockée
- ❌ Score sécurité < 50/100
- ❌ Risque CRITICAL

### Protection Active

Chaque token est vérifié via **3 APIs** avant envoi :
1. **Honeypot.is** - Peut-on vendre ?
2. **GoPlusLabs** - LP lockée ?
3. **TokenSniffer** - Contrat sûr ?

---

## 📈 Tracking Automatique

### Ce qui se passe après chaque alerte

```
T+0   : 📱 Alerte Telegram envoyée
        💾 Sauvegarde en DB
        🚀 Tracking lancé (4 threads)

T+15m : 📊 Check prix → ROI calculé
T+1h  : 📊 Check prix → TP atteints ?
T+4h  : 📊 Check prix → Performance
T+24h : 📊 Analyse complète → Qualité prédiction
```

**Tout est automatique.** Vous n'avez rien à faire.

---

## 🔧 Ajuster les Paramètres

### Score de Sécurité Minimum

Dans `geckoterminal_scanner_v2.py`, ligne 1071 :
```python
min_security_score=50  # Modifier ici (50-100)
```

Plus strict (70+) = Moins d'alertes mais plus sûres
Plus permissif (40-) = Plus d'alertes mais plus risquées

### Réseaux Surveillés

Dans `geckoterminal_scanner_v2.py`, ligne 39 :
```python
NETWORKS = ["eth", "bsc", "arbitrum", "base", "solana"]
```

Ajouter/retirer des réseaux selon vos besoins.

### Seuils de Volume/Liquidité

Dans `geckoterminal_scanner_v2.py`, lignes 42-43 :
```python
MIN_LIQUIDITY_USD = 200000    # Liquidité min
MIN_VOLUME_24H_USD = 100000   # Volume 24h min
```

---

## ❓ FAQ

### Q: Combien d'alertes par jour ?
**R:** Variable, dépend du marché. En moyenne : 5-20 par jour (après filtres sécurité).

### Q: Combien coûte Railway ?
**R:** $5 de crédits gratuits/mois = ~20 jours 24/7. Largement suffisant.

### Q: Où est sauvegardée la DB ?
**R:**
- **Local** : `alerts_history.db`
- **Railway** : `/data/alerts_history.db` (volume persistant)

### Q: Les APIs sont gratuites ?
**R:** ✅ OUI. Toutes les APIs utilisées sont gratuites (GoPlusLabs, DexScreener, TokenSniffer, Honeypot.is).

### Q: Puis-je arrêter/redémarrer le bot ?
**R:** ✅ OUI. La DB est persistante, rien n'est perdu.

### Q: Comment voir les statistiques ?
**R:** `python consulter_db.py` → Option 3 (Statistiques globales)

### Q: Le bot peut manquer des opportunités ?
**R:** OUI. Il scanne toutes les 5 minutes. Mais c'est un compromis pour éviter les rate limits API.

### Q: Puis-je utiliser plusieurs bots Telegram ?
**R:** OUI. Dupliquez le projet et changez `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.

---

## 📚 Documentation Complète

| Besoin | Document |
|--------|----------|
| Vue d'ensemble | [README.md](README.md) |
| Comprendre l'intégration | [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) |
| Comprendre les sauvegardes | [FONCTIONNEMENT_SAUVEGARDE.md](FONCTIONNEMENT_SAUVEGARDE.md) |
| Accès DB sur Railway | [ACCES_DB_RAILWAY.md](ACCES_DB_RAILWAY.md) |
| Déployer sur Railway | [DEPLOIEMENT_RAILWAY.md](DEPLOIEMENT_RAILWAY.md) |
| Système de sécurité | [README_SECURITE.md](README_SECURITE.md) |
| Technique LP Lock | [LP_LOCK_DOCUMENTATION.md](LP_LOCK_DOCUMENTATION.md) |

---

## ✅ Checklist Rapide

**Avant de lancer** :
- [ ] `.env` créé avec TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID
- [ ] `requirements.txt` installé
- [ ] Test local réussi (alertes reçues sur Telegram)

**Sur Railway** :
- [ ] Variables d'environnement configurées
- [ ] Volume `/data` créé (1GB)
- [ ] Logs vérifiés (bot démarré)
- [ ] Première alerte reçue

**Base de données** :
- [ ] Script `consulter_db.py` testé
- [ ] Premières entrées visibles
- [ ] Tracking fonctionne (vérifier après 15min)

---

## 🎉 Vous êtes Prêt !

Le système est **entièrement automatisé** :
- ✅ Scan automatique toutes les 5 minutes
- ✅ Vérification de sécurité automatique
- ✅ Envoi Telegram automatique
- ✅ Sauvegarde DB automatique
- ✅ Tracking automatique (4 intervalles)
- ✅ Analyse automatique (après 24h)

**Il n'y a plus rien à faire.** Profitez des alertes ! 🚀

---

**Besoin d'aide ?** Consultez la documentation complète dans les fichiers .md du projet.