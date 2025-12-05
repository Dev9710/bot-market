# Déploiement sur Railway

## Problème résolu

L'application ne fonctionnait pas quand votre environnement local était éteint car `alerte.py` utilisait `subprocess.Popen()` pour lancer des scripts Python externes, qui ne fonctionnaient pas correctement sur Railway.

## Solution implémentée

✅ **Threading au lieu de subprocess** : Les bots sont maintenant exécutés dans des threads Python au lieu de sous-processus séparés.

## Configuration Railway

### 1. Variables d'environnement à configurer

Dans Railway, allez dans votre projet → Settings → Variables et ajoutez :

```
TELEGRAM_BOT_TOKEN=votre_token_telegram
TELEGRAM_CHAT_ID=votre_chat_id
CMC_API_KEY=votre_api_key_coinmarketcap (optionnel)
ETHERSCAN_API_KEY=votre_api_key_etherscan (optionnel)
```

### 2. Fichiers importants

- `Procfile` : Définit la commande de démarrage (`worker: python3 alerte.py`)
- `requirements.txt` : Liste des dépendances Python
- `railway.toml` : Configuration spécifique Railway
- `.gitignore` : Protège vos secrets (`.env` ne sera pas poussé sur Git)

### 3. Déploiement

```bash
# Ajouter les changements
git add .

# Créer un commit
git commit -m "Fix: Use threading instead of subprocess for Railway compatibility"

# Pousser sur GitHub (Railway va déployer automatiquement)
git push origin main
```

### 4. Vérification

Une fois déployé sur Railway :

1. Vérifiez les logs dans Railway Dashboard
2. Vous devriez voir :
   ```
   🚀 LANCEMENT DE TOUS LES BOTS
   📊 Bot 1: Binance Scanner (tokens etablis CEX)
   🦎 Bot 2: GeckoTerminal Scanner (nouveaux tokens DEX)
   ✅ Tous les bots sont demarres!
   ```

3. Les notifications Telegram devraient arriver même quand votre PC est éteint

## Architecture

```
alerte.py (processus principal)
├── Thread 1: run_binance_bot.boucle()
│   └── Scanne Binance toutes les 2 minutes
│   └── Envoie alertes Telegram
│
└── Thread 2: geckoterminal_scanner.main()
    └── Scanne GeckoTerminal toutes les 5 minutes
    └── Envoie alertes Telegram
```

## Avantages

✅ Fonctionne 24/7 sur Railway, indépendant de votre PC
✅ Auto-redémarrage si un thread crash
✅ Logs centralisés dans Railway Dashboard
✅ Variables d'environnement sécurisées
