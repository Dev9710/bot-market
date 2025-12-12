# 🚀 Hyperliquid Scanner - Documentation

Scanner de détection d'opportunités de trading sur Hyperliquid (perpétuels).

---

## 📋 Vue d'ensemble

Le **Hyperliquid Scanner** surveille en temps réel les marchés de perpétuels sur Hyperliquid et détecte automatiquement :

- 🆕 **Nouveaux marchés** avec fort volume initial
- 🐋 **Positions whales** (>$500k)
- ⚡ **Liquidations massives** (>$1M en 5min)
- 💰 **Funding rates extrêmes** (opportunités d'arbitrage)
- 📊 **Volume spikes** (+500% vs moyenne)
- 🚀 **Breakouts** confirmés par le volume
- ⚡ **Squeeze potentials** (déséquilibres long/short)

---

## ⚙️ Fonctionnalités

### 🔔 Alertes Haute Priorité

| Alerte | Seuil | Description |
|--------|-------|-------------|
| **Nouveau marché** | $1M volume/1h | Perpétuel nouvellement listé avec activité immédiate |
| **Whale position** | $500k | Grosse position ouverte (via spike Open Interest) |
| **Liquidation cascade** | $1M en 5min | Cascade de liquidations = potentiel reversal |
| **Funding extrême** | >0.1% | Opportunité d'arbitrage market neutral |
| **Volume spike** | +500% | Volume explosif vs moyenne |
| **Smart money** | Top traders | Positions des meilleurs traders (à implémenter) |

### ⚡ Alertes Trading

| Alerte | Description |
|--------|-------------|
| **Breakout** | Prix casse résistance + volume 2x moyenne |
| **Accumulation** | Whales accumulent discrètement (via OI) |
| **Squeeze potential** | Funding rate extrême = risque squeeze |
| **Long/Short ratio** | Déséquilibre >85% d'un côté |

### 💎 Opportunités Long-Terme

- **Nouveaux tokens prometteurs** : Volume stable croissant sur 7 jours
- **Intérêt institutionnel** : Wallets >$1M entrent progressivement
- **Tendances émergentes** : Nouveaux secteurs (AI, gaming, RWA, etc.)

---

## 🚀 Installation

### 1. Prérequis

```bash
pip install requests
```

### 2. Configuration Telegram

Éditer [config_hyperliquid.json](config_hyperliquid.json) :

```json
{
  "telegram": {
    "bot_token": "VOTRE_BOT_TOKEN",
    "chat_id": "VOTRE_CHAT_ID"
  }
}
```

### 3. Lancer le scanner

```bash
python hyperliquid_scanner.py
```

---

## 📊 API Hyperliquid

### Informations

- **Endpoint** : `https://api.hyperliquid.xyz/info`
- **Rate limit** : **1200 points/minute** (très généreux)
- **Prix** : **Gratuit** (pas de clé API nécessaire)

### Endpoints utilisés

| Endpoint | Weight | Usage |
|----------|--------|-------|
| `meta` | 20 | Récupère liste des marchés |
| `metaAndAssetCtxs` | 20 | Volume, funding, Open Interest |
| `allMids` | 2 | Prix mid actuels |
| `recentTrades` | 20+ | Trades récents (liquidations) |
| `clearinghouseState` | 2 | Positions d'un wallet (whales) |
| `fundingHistory` | 20+ | Historique funding rates |

### Budget par scan

**Scan complet (~2 min)** :
- Metadata : 20 points
- Asset contexts : 20 points
- Prix : 2 points
- Top 5 marchés trades : 5 × 20 = 100 points
- **Total : ~150 points/scan**

**Scans possibles** : 1200 / 150 = **~8 scans/minute** (on fait 1 scan/2min = confortable)

---

## 📖 Configuration

Fichier : [config_hyperliquid.json](config_hyperliquid.json)

### Seuils personnalisables

```json
{
  "thresholds": {
    "new_market_volume_1h": 1000000,     // $1M
    "whale_position_size": 500000,        // $500k
    "liquidation_cascade": 1000000,       // $1M
    "funding_rate_extreme": 0.001,        // 0.1%
    "volume_spike_ratio": 5.0,            // +500%
    "breakout_volume_multiplier": 2.0,    // 2x moyenne
    "long_short_squeeze_threshold": 0.85  // 85%
  }
}
```

### Paramètres de scan

```json
{
  "scan_settings": {
    "scan_interval_seconds": 120,        // 2 minutes
    "alert_cooldown_seconds": 1800,      // 30 min
    "max_alerts_per_scan": 5,
    "api_call_delay_seconds": 2,
    "top_markets_liquidation_check": 5   // Top 5 seulement
  }
}
```

### Activer/Désactiver alertes

```json
{
  "alerts_enabled": {
    "new_markets": true,
    "whale_positions": true,
    "liquidations": true,
    "extreme_funding": true,
    "volume_spikes": true,
    "breakouts": true,
    "squeeze_potential": true
  }
}
```

---

## 📈 Exemples d'alertes

### 🆕 Nouveau marché

```
🆕 NOUVEAU MARCHE PERPETUEL
━━━━━━━━━━━━━━━━
💎 AI-USD
📊 Volume 24h: $2.5M
⚡ Volume 1h: $1.2M
💰 Funding: 0.015%
📈 Open Interest: $5.8M

🔍 ANALYSE:
✅ Nouveau marche avec volume immediat!
⚡ Opportunite early entry

⚠️ ACTION:
👀 Surveiller momentum initial
🎯 Entry si confirmation trend

🔗 https://app.hyperliquid.xyz/trade/AI
```

### 🐋 Whale alert

```
🐋 WHALE ALERT
━━━━━━━━━━━━━━━━
💎 ETH
📈 Position ouverte: $850K
💰 Prix: $3,245.50
📊 OI Total: $125.5M

🔍 ANALYSE:
🐋 Grosse position institutionnelle
📈 Potentiel mouvement directionnel

⚠️ ACTION:
👀 Suivre direction (long ou short)
🎯 Possible trend suiveur
```

### ⚡ Liquidation cascade

```
⚡ LIQUIDATION CASCADE
━━━━━━━━━━━━━━━━
💎 SOL
💥 Volume liquide: $1.8M
🔄 Nb liquidations: 47

🔍 ANALYSE:
⚡ Cascade de liquidations massive!
📉 Possible bottom/top local

⚠️ ACTION:
🎯 Opportunite contre-tendance
⚠️ Attendre stabilisation prix
```

### 💰 Funding rate extrême

```
💰 FUNDING RATE EXTREME
━━━━━━━━━━━━━━━━
💎 PEPE
💸 Funding: 0.125%
📊 Cote dominant: LONG

🔍 ANALYSE:
💰 Opportunite d'arbitrage!
⚖️ Desequilibre long/short extreme

⚠️ ACTION:
📉 Short + hedge spot = collect funding
🎯 Strategie market neutral
```

### 🚀 Breakout

```
🚀 BREAKOUT DETECTE
━━━━━━━━━━━━━━━━
💎 DOGE
💰 Prix: $0.0825
📊 Resistance: $0.0800
⚡ Breakout: +3.1%
📈 Volume ratio: 3.2x

🔍 ANALYSE:
🚀 Prix casse resistance!
📊 Volume confirme le mouvement

⚠️ ACTION:
✅ Entry possible maintenant
🎯 Stop: resistance (support)
🎯 Target: +20-30% ou prochaine resistance
```

---

## 🎯 Stratégies de trading

### 1. Nouveau marché (Early Entry)

**Conditions** :
- ✅ Volume 1h >$1M
- ✅ Funding rate neutre (<0.05%)
- ✅ Open Interest croissant

**Action** :
1. Surveiller les 30 premières minutes
2. Entry si momentum confirmé
3. Stop loss : -10%
4. Take profit : +30-50%

---

### 2. Whale Position (Trend Following)

**Conditions** :
- ✅ Position >$500k ouverte
- ✅ Funding rate dans la même direction
- ✅ Volume croissant

**Action** :
1. Identifier direction (long/short)
2. Entry dans la même direction
3. Stop loss : -5-7%
4. Suivre jusqu'à reversal ou funding extrême

---

### 3. Liquidation Cascade (Counter-Trend)

**Conditions** :
- ✅ >$1M liquidé en 5min
- ✅ Prix a chuté/monté rapidement
- ✅ Funding rate extrême

**Action** :
1. **Attendre stabilisation** (30-60min)
2. Entry contre-tendance si support/resistance tient
3. Stop loss serré : -3-5%
4. Take profit rapide : +10-20%

---

### 4. Funding Rate Extreme (Arbitrage)

**Conditions** :
- ✅ Funding >0.1% ou <-0.1%
- ✅ Market stable (pas de volatilité extrême)

**Action** :
1. **Si funding positif** (trop de longs) :
   - Short perp sur Hyperliquid
   - Long spot sur CEX (Binance)
   - Collecter funding 8h

2. **Si funding négatif** (trop de shorts) :
   - Long perp sur Hyperliquid
   - Short spot sur CEX
   - Collecter funding 8h

3. Fermer positions après normalisation funding

---

### 5. Breakout (Momentum)

**Conditions** :
- ✅ Prix casse résistance >2%
- ✅ Volume 2x+ moyenne
- ✅ OI croissant

**Action** :
1. Entry immédiate au breakout
2. Stop loss : ancien niveau de résistance
3. Take profit : +20-30% ou prochaine résistance
4. Trail stop si momentum continue

---

## 🔧 Avancé

### Rate Limiting

Le scanner respecte intelligemment les limites :
- Pause de **2s entre requêtes**
- Scan toutes les **2 minutes**
- Liquidations vérifiées sur **top 5 marchés** seulement

### Cache & Historique

Le scanner maintient un cache en mémoire pour :
- **Nouveaux marchés** : Éviter re-détection
- **Volume history** : Calcul moyennes (7 scans)
- **Prix history** : Détection breakouts (20 points)
- **Open Interest** : Détection variations

### Cooldown

Chaque alerte a un cooldown de **30 minutes** pour éviter spam.

---

## 🐛 Troubleshooting

### Erreur "Rate limit atteint"

**Cause** : Trop de requêtes
**Solution** : Augmenter `api_call_delay_seconds` dans config

### Pas d'alertes reçues

**Vérifications** :
1. Token/Chat ID Telegram corrects ?
2. Seuils trop élevés ?
3. Marchés en blacklist ?

### Erreur API

**Cause** : API Hyperliquid down ou changement structure
**Solution** : Vérifier [docs officielles](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)

---

## 📚 Ressources

- **API Docs** : https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **Plateforme** : https://app.hyperliquid.xyz
- **Rate Limits** : https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits

---

## 🚀 Améliorations futures

- [ ] WebSocket pour données temps réel
- [ ] Détection smart money (top traders)
- [ ] Divergence prix Hyperliquid vs Binance
- [ ] Backtesting des signaux
- [ ] Dashboard web avec graphiques
- [ ] Intégration Discord
- [ ] Auto-trading (avec prudence !)

---

## ⚠️ Avertissement

**Ce scanner est à but éducatif et informatif uniquement.**

- ⚠️ Le trading de perpétuels est **extrêmement risqué**
- 💸 Ne tradez que ce que vous pouvez vous permettre de perdre
- 📚 Faites vos propres recherches (DYOR)
- 🚫 Pas de conseils financiers

**Utilisez à vos propres risques !**

---

## 📝 Licence

MIT License - Libre d'utilisation et modification

---

**Bon trading ! 🚀**
