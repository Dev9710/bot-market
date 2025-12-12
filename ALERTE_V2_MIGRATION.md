# ✅ Migration alerte.py vers GeckoTerminal Scanner V2

## 🎯 Modifications effectuées

Le fichier **`alerte.py`** utilise maintenant **`geckoterminal_scanner_v2.py`** au lieu de l'ancienne version.

### 📝 Changements :

1. **Import modifié** (ligne 15) :
   ```python
   # AVANT :
   import geckoterminal_scanner

   # APRÈS :
   import geckoterminal_scanner_v2 as geckoterminal_scanner  # Utilise la V2 avec améliorations LAVA
   ```

2. **Documentation mise à jour** :
   - Header du fichier indique maintenant "V2 (avec améliorations LAVA)"
   - Log de démarrage affiche "GeckoTerminal Scanner V2"
   - Ajout de "Score min 55/100, multi-pool, momentum avancé"

---

## 🚀 Comment utiliser

### Option 1 : Lancer tous les bots en parallèle (recommandé)
```bash
cd C:\Users\BisolyL\Documents\owner\bot-market
python alerte.py
```

**Résultat :**
- ✅ Binance Scanner (tokens CEX établis)
- ✅ GeckoTerminal Scanner V2 (nouveaux tokens DEX)
- Les 2 bots tournent en parallèle dans des threads séparés

---

### Option 2 : Lancer seulement GeckoTerminal V2
```bash
cd C:\Users\BisolyL\Documents\owner\bot-market
python geckoterminal_scanner_v2.py
```

---

### Option 3 : Lancer seulement Binance
```bash
cd C:\Users\BisolyL\Documents\owner\bot-market
python run_binance_bot.py
```

---

## ✅ Fonctionnalités V2 activées

Quand tu lances **`alerte.py`**, tu bénéficies automatiquement de :

### 🦎 GeckoTerminal Scanner V2 :
- ✅ **Score minimum 55/100** (au lieu de 40)
- ✅ **Multi-pool correlation** (détecte LAVA/USDT + LAVA/WETH)
- ✅ **Momentum multi-timeframe** (1h, 3h, 6h, 24h)
- ✅ **Traders spike detection**
- ✅ **Buy/Sell pressure évolutive** (24h vs 1h)
- ✅ **Signaux avancés** (ACCELERATION, REVERSAL, BUY_PRESSURE, WETH_DOMINANCE)
- ✅ **Format alerte ultra-complet** avec :
  - Transactions explicites (🟢 ACHATS/🔴 VENTES avec %)
  - Pression dominante (ACHETEURS/VENDEURS)
  - Signaux détectés
  - Multi-pool info si applicable

### 💰 Binance Scanner (amélioré) :
- ✅ Liquidity checks (order book depth)
- ✅ Confidence scoring (0-100)
- ✅ Pre-pump detection
- ✅ Performance tracking (win rate)
- ✅ Exit signal alerts (TP1, TP2, TP3, Stop Loss)
- ✅ Market context verification (BTC/ETH)
- ✅ Anti-manipulation filters

---

## 🔧 Configuration requise

Crée un fichier **`.env`** avec tes credentials Telegram :

```env
TELEGRAM_BOT_TOKEN=ton_token_ici
TELEGRAM_CHAT_ID=ton_chat_id_ici
```

---

## 📊 Exemple d'alertes V2

### GeckoTerminal V2 :
```
🆕 NOUVEAU TOKEN DEX
━━━━━━━━━━━━━━━━
💎 LAVA
   Paire: LAVA / USDT 0.01%
⛓️ Blockchain: Ethereum

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
```

### Binance (amélioré) :
```
🔥 BTC (Bitcoin)
━━━━━━━━━━━━━━━━

🎯 SCORE: 85/100 ⭐️⭐️⭐️ EXCELLENT
   💡 Signal TRES fiable - Forte probabilite profit

📋 Raisons du score:
   • Volume exceptionnel (x10+)
   • ACCUMULATION PRE-PUMP! (x3.2)
   • Acceleration volume (t-2 < t-1 < t-0)

💰 Prix: $43250.00 (+2.5% 1h)
📊 Vol 1min: $850K (+320%)
📈 Ratio: x12.5
```

---

## 🎉 Avantages

En utilisant **`alerte.py`** :
1. **Un seul script** lance tous les bots
2. **Surveillance complète** : CEX + DEX
3. **Version V2 automatique** pour GeckoTerminal
4. **Auto-restart** si un bot crash
5. **Logs centralisés** avec timestamps

---

## 📌 Remarques

- Les deux scanners tournent **en parallèle** dans des threads séparés
- Si un scanner crash, il redémarre automatiquement après 30 secondes
- Pour arrêter : appuie sur **Ctrl+C**
- Les logs montrent quel bot envoie quelle alerte

---

✅ **Tout est prêt !** Lance `python alerte.py` pour démarrer 🚀
