# 🦎 GeckoTerminal Scanner - Documentation

## 📋 Vue d'ensemble

Scanner automatique pour détecter les **nouveaux tokens DEX** avec fort potentiel de pump. Utilise l'API gratuite GeckoTerminal pour surveiller Ethereum, BSC, Arbitrum, Base et Solana.

### 🎯 Objectif

Détecter les tokens **récents** (< 72h) avec:
- ✅ Liquidité suffisante (anti rug pull)
- ✅ Volume élevé (activité réelle)
- ✅ Transactions nombreuses (intérêt réel)
- ✅ Ratio achats/ventes équilibré (pas de pump & dump)

### 🔄 Différence avec Binance Scanner

| Critère | Binance Scanner | GeckoTerminal Scanner |
|---------|-----------------|----------------------|
| **Tokens** | Établis (DASH, XRP, SOL) | Nouveaux (< 72h) |
| **Source** | CEX (Binance) | DEX (Uniswap, PancakeSwap, etc.) |
| **Objectif** | Volume spikes temps réel | Nouveaux tokens avant listing CEX |
| **Exemples** | FIL, BCH, ENA | SAYLOR, Ensemble, tokens chinois |
| **Risque** | Moyen | Élevé (rug pull possible) |

---

## 🚀 Installation et Lancement

### Prérequis

```bash
pip install requests
```

### Variables d'environnement (optionnel)

```bash
set TELEGRAM_BOT_TOKEN=votre_token
set TELEGRAM_CHAT_ID=votre_chat_id
```

### Lancement

**Option 1: GeckoTerminal uniquement**
```bash
python geckoterminal_scanner.py
```

**Option 2: Tous les bots (recommandé)**
```bash
python run_all_bots.py
```

---

## ⚙️ Configuration

Fichier: `config_geckoterminal.json`

```json
{
  "networks": ["eth", "bsc", "arbitrum", "base", "solana"],

  "thresholds": {
    "min_liquidity_usd": 50000,        // Liquidité min (anti rug pull)
    "min_volume_24h_usd": 100000,      // Volume 24h min
    "min_transactions_24h": 100,       // Transactions min
    "max_token_age_hours": 72,         // Age max (3 jours)
    "volume_liquidity_ratio": 0.5      // Vol/Liq > 50%
  },

  "safety": {
    "max_buy_sell_ratio": 5.0,         // Max achats/ventes
    "min_buy_sell_ratio": 0.2          // Min achats/ventes
  },

  "scan_settings": {
    "scan_interval_seconds": 300,      // Scan tous les 5 min
    "alert_cooldown_seconds": 1800,    // 30 min entre alertes
    "max_alerts_per_scan": 3           // Max 3 alertes par scan
  }
}
```

### 🎚️ Ajuster les Seuils

**Plus conservateur (moins d'alertes, moins de risque):**
```json
{
  "min_liquidity_usd": 200000,    // 200K au lieu de 50K
  "min_volume_24h_usd": 500000,   // 500K au lieu de 100K
  "max_token_age_hours": 48       // 2 jours au lieu de 3
}
```

**Plus agressif (plus d'alertes, plus de risque):**
```json
{
  "min_liquidity_usd": 30000,     // 30K au lieu de 50K
  "min_volume_24h_usd": 50000,    // 50K au lieu de 100K
  "max_token_age_hours": 168      // 7 jours au lieu de 3
}
```

---

## 📊 Format des Alertes

### Exemple d'Alerte

```
🆕 NOUVEAU TOKEN DEX
━━━━━━━━━━━━━━━━
💎 SAYLOR / WETH
🌐 Reseau: ETH
💰 Prix: $0.00012345
📊 Vol 24h: $234K
💧 Liquidite: $156K
📈 Variation: +45.2%
⏰ Age: 18h
🔄 Txns: 456 (A:289 V:167)
📊 Vol/Liq: 150%

🔍 ANALYSE:
⚠️ Liquidite moyenne ($156K)
🔥 TRES actif! (Vol=150% Liq)
🟢 Plus d'achats! (289A vs 167V)
🆕 NOUVEAU! (Cree il y a 18h)
📈 Hausse forte +45%

⚡ ACTION:
👀 Surveille evolution
⚠️ Liquidite moyenne - petit risque

🔗 https://geckoterminal.com/eth/pools/0x...
```

### 📖 Comprendre les Indicateurs

| Indicateur | Signification | Bon signe |
|------------|--------------|-----------|
| **Vol 24h** | Volume échangé en 24h | > $100K |
| **Liquidité** | Fonds dans le pool | > $200K (sûr) |
| **Vol/Liq** | Activité relative | > 50% (actif) |
| **Txns** | Nombre de transactions | > 100 |
| **A/V** | Achats vs Ventes | 0.5 < ratio < 2 |
| **Age** | Heures depuis création | < 72h |
| **Variation** | Changement prix 24h | +20% à +100% |

---

## 🛡️ Filtres de Sécurité

### ❌ Rejets Automatiques

1. **Liquidité < $50K**
   - Risque: Rug pull (créateur retire liquidité)
   - Action: Alerte bloquée

2. **Ratio Achats/Ventes > 5**
   - Risque: Pump organisé
   - Action: Alerte bloquée

3. **Ratio Achats/Ventes < 0.2**
   - Risque: Dump en cours
   - Action: Alerte bloquée

4. **Volume < $100K**
   - Risque: Pas d'intérêt réel
   - Action: Alerte bloquée

5. **Age > 72h**
   - Risque: Pas "nouveau"
   - Action: Alerte bloquée (sauf si ajusté)

### ✅ Validations

Scanner affiche dans les logs:
```
✅ Opportunite: SAYLOR / WETH
⏭️  SPURDO / WETH: ⚠️ Volume trop faible: $27,093
⏭️  PEPE / WETH: ⏳ Token trop ancien: 22744h
⏭️  cat girl / WBNB: ❌ Liquidite trop faible: $17,984
```

---

## 🌐 Réseaux Surveillés

### Ordre de Priorité

1. **Ethereum (eth)**
   - DEX: Uniswap V2/V3
   - Gas fees élevés = tokens sérieux
   - Liquidité la plus élevée

2. **BSC (bsc)**
   - DEX: PancakeSwap
   - Gas fees faibles
   - Beaucoup de nouveaux tokens (⚠️ scams fréquents)

3. **Arbitrum (arbitrum)**
   - Layer 2 Ethereum
   - Gas fees bas + sécurité Ethereum

4. **Base (base)**
   - Layer 2 Coinbase
   - Tokens émergents

5. **Solana (solana)**
   - DEX: Raydium, Orca
   - Très rapide, gas minimal

### Ajouter/Retirer des Réseaux

Dans le code `geckoterminal_scanner.py`:

```python
NETWORKS = [
    "eth",
    "bsc",
    "arbitrum",
    # "base",      # Commenter pour désactiver
    # "solana",    # Commenter pour désactiver
]
```

---

## 📈 Stratégie d'Utilisation

### 🎯 Workflow Recommandé

1. **Recevoir alerte Telegram**
   - Lire analyse complète

2. **Vérifier sur GeckoTerminal**
   - Cliquer sur lien fourni
   - Regarder graphique prix
   - Vérifier holders (pas de whale avec 50%+)

3. **Décision**

   **✅ Acheter si:**
   - Liquidité > $200K
   - Vol/Liq > 100%
   - Ratio A/V entre 0.8 et 1.5
   - Graphique: hausse progressive (pas verticale)
   - Pas de whale > 20%

   **❌ NE PAS acheter si:**
   - Liquidité < $100K
   - Graphique vertical (pump artificiel)
   - Whale détient > 30%
   - Variation > +200% en 1h (pump & dump)

4. **Si achat:**
   - Montant: MAX 1-2% de votre capital
   - Stop loss: -15%
   - Take profit: +30% (vendre 50%), +50% (vendre 30%), laisser 20%

---

## 🔧 Troubleshooting

### Aucune Alerte

**Problème:** Scanner tourne mais pas d'alerte

**Solutions:**
1. Réduire seuils dans config
2. Vérifier logs: tokens rejetés avec raisons
3. Élargir à plus de réseaux

### Rate Limit

**Problème:** `⚠️ Rate limit atteint`

**Solution:**
- API gratuite: 30 calls/min
- Scanner pause automatiquement 60s
- Ne pas lancer plusieurs instances

### Réseau 404

**Problème:** `⚠️ Erreur polygon: 404`

**Explication:**
- Réseau pas supporté par GeckoTerminal
- Scanner passe automatiquement au suivant

### Erreurs de Parsing

**Problème:** `⚠️ Erreur parse pool`

**Explication:**
- Données API incomplètes (normal)
- Pool ignoré, scanner continue

---

## 📊 Exemples Réels (Test)

### Opportunités Détectées

**Test du 2025-11-17 10:13:**

```
✅ Opportunite: SAYLOR / WETH
   - Réseau: Ethereum
   - Age: ~24h
   - Liquidité: Suffisante
   - Volume: Actif

✅ Opportunite: Ensemble / WETH
   - Réseau: Ethereum
   - Age: < 24h
   - Liquidité: Suffisante

✅ Opportunite: 马到成功 / WBNB
   - Réseau: BSC
   - Age: < 72h
   - Volume élevé
```

### Rejets (Sécurité)

```
⏭️  SPURDO / WETH: ⚠️ Volume trop faible: $27,093
⏭️  cat girl / WBNB: ❌ Liquidite trop faible: $17,984
⏭️  NOTR / WETH: ❌ Liquidite trop faible: $8,427
```

---

## 🔄 Maintenance

### Logs

Scanner affiche logs détaillés:
```
2025-11-17 10:13:43 - 🦎 GECKOTERMINAL SCANNER - Detection Nouveaux Tokens DEX
2025-11-17 10:13:43 - 🔍 Scan reseau: ETH
2025-11-17 10:13:43 -    📊 20 pools trending trouves
2025-11-17 10:13:43 -    ✅ Opportunite: SAYLOR / WETH
```

### Cooldown

Chaque token a cooldown 30 min:
- Évite spam si token reste actif
- Reset automatique après 30 min

---

## 🆚 Comparaison avec Alternatives

| Scanner | Tokens | Temps Réel | Gratuit | Fiabilité |
|---------|--------|------------|---------|-----------|
| **GeckoTerminal** | DEX nouveaux | Quasi (~5min) | ✅ | ⭐⭐⭐⭐ |
| DexScreener | DEX nouveaux | Temps réel | ❌ (payant) | ⭐⭐⭐⭐⭐ |
| CoinGecko | Tous | Non (24h) | ✅ | ⭐⭐⭐ |
| **Binance** | CEX établis | Temps réel | ✅ | ⭐⭐⭐⭐⭐ |

**Recommandation:** Utiliser **Binance + GeckoTerminal** ensemble pour couvrir CEX (établis) et DEX (nouveaux).

---

## 🚨 Avertissements

### ⚠️ RISQUES

1. **Rug Pull**
   - Même avec liquidité $50K+
   - Créateur peut retirer liquidité
   - **Investir MAX 1-2% capital**

2. **Pump & Dump**
   - Groupes organisés
   - Montée artificielle puis chute
   - **Vérifier graphique avant achat**

3. **Scams**
   - Tokens honeypot (ne peut pas vendre)
   - Taxe vente 99%
   - **Toujours tester avec petit montant**

4. **Volatilité Extrême**
   - -50% en quelques minutes possible
   - **TOUJOURS mettre stop loss**

### ✅ Règles d'Or

1. ❌ **NE JAMAIS** investir plus de 1-2% capital par token
2. ✅ **TOUJOURS** mettre stop loss -15%
3. ✅ **TOUJOURS** vérifier sur GeckoTerminal avant achat
4. ✅ **TOUJOURS** tester petit montant d'abord
5. ❌ **NE JAMAIS** FOMO (Fear Of Missing Out)

---

## 📞 Support

- **Issues:** Consulter logs détaillés
- **Configuration:** Ajuster `config_geckoterminal.json`
- **API:** https://apiguide.geckoterminal.com

---

## 📝 Changelog

**v1.0 (2025-11-17)**
- ✅ Première version fonctionnelle
- ✅ Support ETH, BSC, Arbitrum, Base, Solana
- ✅ Filtres sécurité (rug pull, pump & dump)
- ✅ Alertes Telegram concises avec emojis
- ✅ Rate limit handling automatique
- ✅ Cooldown anti-spam
