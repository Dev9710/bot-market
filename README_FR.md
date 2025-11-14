# Crypto Global Scanner Bot

Bot Telegram qui scanne l'ensemble du marché crypto (CoinGecko / CMC / Etherscan)
et envoie des alertes détaillées avec les informations de listing (exchanges + blockchains).

## ✨ Nouvelles fonctionnalités

- 📊 **Nom complet des tokens** : BTC (Bitcoin), ETH (Ethereum)...
- 🏪 **Exchanges listés** : Top 3-5 plateformes (Binance, Coinbase, KuCoin...)
- ⛓️ **Blockchains supportées** : Pour tokens multi-chain (ex: USDT sur Ethereum, Tron, BSC)
- 🚀 **Cache intelligent** : Évite les appels API répétés
- 🎯 **Alertes enrichies** : Toutes les infos en un seul message

Voir [EXEMPLE_ALERTE.md](EXEMPLE_ALERTE.md) pour un aperçu des nouvelles alertes.

## 🚀 Déploiement instantané sur Railway

Clique ici :

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=<URL_DU_GITHUB>)

## 🔧 Variables d'environnement requises

Dans Railway → Variables → ajoute :

```bash
TELEGRAM_BOT_TOKEN=ton_token_bot
TELEGRAM_CHAT_ID=ton_chat_id
CMC_API_KEY=ta_cle_cmc (optionnel)
ETHERSCAN_API_KEY=ta_cle_etherscan (optionnel)
```

## 📊 Configuration

Édite [config_tokens.json](config_tokens.json) :

```json
{
  "global_volume_scan": {
    "enabled": true,
    "interval_seconds": 60,
    "min_vol24_usd": 100000,
    "ratio_threshold": 5.0,
    "min_price_usd": 0.0001
  }
}
```

## 🧪 Test

```bash
# Test basique
python test.py

# Test infos de listing
python test_platforms.py
```

## 🚀 Lancement local

```bash
pip install -r requirements.txt
python alerte.py
```

