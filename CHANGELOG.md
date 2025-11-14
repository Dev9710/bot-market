# Changelog - Bot Market

## [v2.0.0] - 2025-11-14

### ✨ Nouvelles fonctionnalités

#### Ajout des informations de listing dans les alertes Telegram

**Avant** : Les alertes affichaient uniquement le symbole (BTC, ETH, etc.)

**Maintenant** : Chaque alerte affiche :
- 📊 **Nom complet** : `BTC (Bitcoin)`, `ETH (Ethereum)`, `UNI (Uniswap)`
- 🏪 **Exchanges** : Top 3-5 plateformes où le token est listé (Binance, Coinbase, KuCoin, etc.)
- ⛓️ **Blockchains** : Pour les tokens multi-chain (ex: USDT sur Ethereum, Tron, BSC)

#### Système de cache intelligent

- Les informations de plateformes sont mises en cache en mémoire
- Évite les appels API répétés pour le même token
- Améliore les performances et respecte les rate limits CoinGecko

### 🔧 Modifications techniques

#### Fichier : `alerte.py`

**Fonction `scan_global()` (ligne 125-231)**
- Ajout de la récupération du nom complet : `name = c.get("name") or "Unknown"`
- Ajout du `coingecko_id` dans les anomalies détectées

**Nouvelle fonction `get_token_platforms()` (ligne 241-288)**
```python
def get_token_platforms(coingecko_id):
    """Récupère les plateformes (exchanges + blockchains) depuis CoinGecko."""
```

Récupère pour chaque token :
- Top 5 exchanges depuis l'endpoint `/coins/{id}` avec paramètre `tickers=true`
- Liste des blockchains depuis le champ `platforms`
- Mise en cache automatique des résultats

**Fonction `format_global_alert()` (ligne 292-318)**
- Appel de `get_token_platforms()` pour chaque token alerté
- Formatage des exchanges : `🏪 Exchanges : Binance, Coinbase, KuCoin`
- Formatage des blockchains : `⛓️ Blockchains : Ethereum, Tron, BSC`
- Fallback : Si aucune blockchain, affiche "Natif (blockchain propre)"

#### Structure des données

**Objet anomalie (avant)** :
```python
{
    "symbol": "BTC",
    "prix": 98765.43,
    "mc": 1234567890,
    # ...
}
```

**Objet anomalie (maintenant)** :
```python
{
    "symbol": "BTC",
    "name": "Bitcoin",           # NOUVEAU
    "coingecko_id": "bitcoin",   # NOUVEAU
    "prix": 98765.43,
    "mc": 1234567890,
    # ...
}
```

**Objet platforms** :
```python
{
    "exchanges": ["Binance", "Coinbase", "KuCoin"],
    "blockchains": ["Ethereum", "Polygon", "Avalanche"]
}
```

### 📝 Nouveaux fichiers

- `test_platforms.py` : Script de test pour vérifier la récupération des infos de listing
- `EXEMPLE_ALERTE.md` : Documentation avec exemples avant/après des alertes
- `CHANGELOG.md` : Ce fichier

### 🔄 API CoinGecko utilisées

#### Endpoint existant (inchangé)
```
GET /coins/markets
```
Pour le scan global des 1000 coins.

#### Nouvel endpoint
```
GET /coins/{id}?localization=false&tickers=true&community_data=false&developer_data=false
```

Utilisé pour récupérer :
- `tickers[]` : Liste des exchanges et paires de trading
- `platforms{}` : Dictionnaire blockchain_id → contract_address

**Rate limits** :
- Free tier CoinGecko : 10-50 calls/minute
- Avec cache : 1 appel par token unique détecté
- Top 10 alertes = Maximum 10 appels par scan (si tous nouveaux)

### 🎯 Impact utilisateur

#### Avantages

✅ **Plus d'informations contextuelles** : Comprendre immédiatement où trader un token
✅ **Aide à la décision** : Savoir si le token est sur des exchanges majeurs
✅ **Meilleure identification** : Nom complet pour les débutants
✅ **Multi-chain awareness** : Comprendre sur quelles blockchains existe le token

#### Exemple d'alerte enrichie

```
🌍 Top activités crypto détectées

#1 — USDT (Tether)
💰 Prix : `1.000500 $`
📈 Volume 1m estimé : `45,678,900 $`
🔥 Multiplicateur : `x6.2`
🏦 Market Cap : `98,765,432,100 $`
📊 Variation 24h : `+0.12%`
📉 Depuis le bas 24h : `0.3%`
🧱 Ratio Haut/Bas : `1.01`
🏪 Exchanges : `Binance, KuCoin, OKX`
⛓️ Blockchains : `Ethereum, Tron, Avalanche`
→ Mouvement inhabituel détecté. Les traders s'intéressent à ce token.
```

### ⚠️ Notes importantes

#### Performance
- Ajout de ~1-3 secondes par alerte (10 tokens)
- Cache réduit drastiquement ce temps pour les tokens récurrents
- Timeout API : 10 secondes max par requête

#### Gestion d'erreurs
- Si l'API CoinGecko échoue, l'alerte est quand même envoyée sans les infos de listing
- Logs d'avertissement en cas d'erreur : `logger.warning()`
- Cache les erreurs pour éviter de réessayer constamment

#### Limitations
- Maximum 10 tokens dans une alerte (top 10)
- Exchanges limités à 3 dans l'affichage (5 en cache)
- Blockchains limitées à 3
- Cache mémoire seulement (perdu au redémarrage)

### 🔮 Améliorations futures possibles

- [ ] Cache persistant (fichier JSON) pour survivre aux redémarrages
- [ ] TTL (Time To Live) sur le cache (ex: 24h)
- [ ] Affichage des volumes par exchange
- [ ] Détection des nouveaux listings
- [ ] Alertes spécifiques "Token listé sur Binance"
- [ ] Support multi-langues pour les noms de tokens

---

## [v1.0.0] - 2025-09-04

### 🎉 Version initiale

- Scan global CoinGecko (~1000 coins)
- Détection anomalies de volume (ratio 5x+)
- Alertes Telegram formatées
- Anti-spam avec cooldown
- Configuration via `config_tokens.json`
- Support Docker et Railway
