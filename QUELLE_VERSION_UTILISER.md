# 🚀 QUEL SCANNER UTILISER ?

## ⚠️ IMPORTANT : Versions des Scanners

### 📊 **GECKOTERMINAL (DEX Tokens)**

#### ✅ **UTILISE CETTE VERSION :**
```bash
python geckoterminal_scanner_v2.py
```

**Pourquoi ?**
- ✅ Toutes les améliorations LAVA intégrées
- ✅ Score minimum 55/100 (filtre les mauvais tokens)
- ✅ Multi-pool correlation (détecte LAVA/USDT + LAVA/WETH)
- ✅ Momentum multi-timeframe (1h, 3h, 6h, 24h)
- ✅ Traders spike detection
- ✅ Buy/Sell pressure évolutive (24h vs 1h)
- ✅ Signaux avancés (ACCELERATION, REVERSAL, BUY_PRESSURE, etc.)
- ✅ Format alerte ultra-complet avec pression explicite

#### ❌ **N'UTILISE PAS :**
```bash
python geckoterminal_scanner.py  # ANCIENNE VERSION !
```

**Pourquoi pas ?**
- ❌ Score minimum 40/100 (trop de faux positifs)
- ❌ Pas de multi-pool
- ❌ Pas d'analyse momentum avancée
- ❌ Format alerte simplifié
- ❌ Moins précis pour détecter les vrais pumps

---

### 💰 **BINANCE (CEX Tokens)**

#### ✅ **UTILISE CETTE VERSION :**
```bash
python run_binance_bot.py
```

**Version améliorée avec :**
- ✅ Liquidity checks (order book depth)
- ✅ Confidence scoring (0-100)
- ✅ Pre-pump detection
- ✅ Performance tracking (win rate)
- ✅ Exit signal alerts (TP1, TP2, TP3, Stop Loss)
- ✅ Market context verification (BTC/ETH)
- ✅ Anti-manipulation filters

---

### 🌊 **HYPERLIQUID (Perpetuals)**

#### ✅ **UTILISE CETTE VERSION :**
```bash
python hyperliquid_scanner.py
```

**Détecte :**
- Nouveaux marchés >$1M volume 1h
- Whale positions >$500k
- Liquidations massives >$1M
- Funding rates extrêmes
- Volume spikes
- Breakouts, squeezes

---

## 📋 Résumé

| Scanner | Fichier | Utiliser ? |
|---------|---------|------------|
| **GeckoTerminal V2** | `geckoterminal_scanner_v2.py` | ✅ OUI |
| GeckoTerminal V1 | `geckoterminal_scanner.py` | ❌ NON (ancienne) |
| **Binance** | `run_binance_bot.py` | ✅ OUI |
| **Hyperliquid** | `hyperliquid_scanner.py` | ✅ OUI |

---

## 🔧 Configuration

Assure-toi d'avoir un fichier `.env` avec :

```env
TELEGRAM_BOT_TOKEN=ton_token_ici
TELEGRAM_CHAT_ID=ton_chat_id_ici
```

---

## 🎯 Exemple d'alerte V2 (améliorée)

```
🆕 NOUVEAU TOKEN DEX
━━━━━━━━━━━━━━━━
💎 LAVA / USDT 0.01%
⛓️ Blockchain: ETH

🎯 SCORE: 72/100 ⭐️⭐️⭐️ TRÈS BON
   Base: 65 | Momentum: +7

━━━ PRIX & MOMENTUM ━━━
💰 Prix: $0.00123456
📊 24h: +15.2% | 6h: +8.3% | 1h: +5.1% 🚀

━━━ ACTIVITÉ ━━━
📊 Vol 24h: $450K
💧 Liquidité: $890K
🔄 Transactions 24h: 2808
   🟢 ACHATS: 1680 (60%)
   🔴 VENTES: 1128 (40%)
   ⚖️ Pression: ACHETEURS dominent (ratio 1.49)

📊 Pression 1h:
   🟢 ACHATS: 280 (56%) ⬆️
   🔴 VENTES: 220 (44%) ⬇️
   ✅ ACHETEURS prennent le contrôle !

━━━ SIGNAUX DÉTECTÉS ━━━
🚀 ACCELERATION: +5.1% en 1h
🟢 BUY PRESSURE: Ratio 1h (1.27) > 24h (1.49)
🌐 MULTI-POOL: 2 pools actifs
⚡ WETH pool dominant = Smart money
```

**vs alerte V1 (basique) :**
```
🆕 NOUVEAU TOKEN DEX
━━━━━━━━━━━━━━━━
💎 PEPE
   Paire: PEPE / WETH
⛓️ Blockchain: Ethereum

🎯 SCORE: 40/100 ⭐️ MOYEN
   ⚠️ Risque moyen - Prudence

📋 Raisons du score:
   • Liquidite excellente ($1M+)
   • Trop vieux (23348h)
   • Activite faible (3%)
```

La différence est claire ! 🎯
