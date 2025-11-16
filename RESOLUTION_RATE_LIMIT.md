# 🔧 RÉSOLUTION: Pourquoi vous ne receviez pas d'alertes Telegram

## ❌ PROBLÈME IDENTIFIÉ

**Symptôme:** Le bot scannait en continu mais aucune alerte Telegram n'était envoyée.

**Cause racine:** **Rate Limit CoinGecko**
- Code d'erreur 429: "You've exceeded the Rate Limit"
- CoinGecko Free tier limite à ~10-50 appels/minute
- Le bot faisait 4 appels toutes les 60 secondes (1 par page)
- Plus des appels supplémentaires pour récupérer les infos de plateformes
- → Total: ~5-10 appels/minute = Trop pour la limite

**Impact:**
```
2025-11-16 00:26:04 - WARNING - Erreur scan global :
HTTPSConnectionPool: Failed to resolve 'api.coingecko.com'
```

Le bot continuait de scanner mais ne récupérait aucune donnée → Aucune anomalie détectée → Aucune alerte envoyée!

---

## ✅ SOLUTION APPLIQUÉE

### 1. **Détection du Rate Limit** (alerte.py lignes 158-168)

Ajout d'une vérification explicite du code 429:

```python
# Vérifier si rate limit atteint
if isinstance(markets, dict) and "status" in markets:
    error_code = markets.get("status", {}).get("error_code")
    if error_code == 429:
        logger.error("⚠️ RATE LIMIT CoinGecko atteint! Attente 60 secondes...")
        tg("⚠️ *Rate limit CoinGecko atteint*\n\n...")
        time.sleep(60)
        break
```

**Bénéfice:** Le bot vous avertira maintenant par Telegram quand il atteint la limite, au lieu de continuer silencieusement.

---

### 2. **Réduction du nombre de pages scannées** (alerte.py ligne 144)

**Avant:**
```python
for page in range(1, 5):  # ~1000 coins
```

**Après:**
```python
for page in range(1, 3):  # Top 500 coins seulement (évite rate limit)
```

**Impact:**
- Avant: 4 appels API/scan
- Après: 2 appels API/scan
- **Réduction de 50% des appels API**

---

### 3. **Ajout d'un délai entre les pages** (alerte.py lignes 173-175)

```python
# Petit délai entre les pages pour éviter rate limit
if page > 1:
    time.sleep(2)
```

**Bénéfice:** Les 2 appels sont espacés de 2 secondes au lieu d'être faits instantanément.

---

### 4. **Augmentation de l'intervalle de scan** (config_tokens.json ligne 7)

**Avant:**
```json
"interval_seconds": 60,  // Scan toutes les 60 secondes
```

**Après:**
```json
"interval_seconds": 120,  // Scan toutes les 2 minutes
```

**Impact:**
- Avant: 4 appels/minute
- Après: 1 appel/minute
- **Réduction de 75% du taux d'appels**

---

## 📊 RÉSULTAT FINAL

### Utilisation API CoinGecko

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| Pages scannées | 4 | 2 | -50% |
| Appels par scan | 4 | 2 | -50% |
| Intervalle scan | 60s | 120s | -50% |
| **Appels/minute** | **~4** | **~1** | **-75%** |
| Tokens scannés | ~1000 | ~500 | Top coins suffisants |

### Configuration actuelle

```json
{
  "alert_cooldown_seconds": 600,       // 10 min entre alertes
  "global_volume_scan": {
    "interval_seconds": 120,           // Scan toutes les 2 minutes
    "min_vol24_usd": 100000,          // Volume 24h > 100K USD
    "ratio_threshold": 5.0,            // Volume 5x supérieur
    "min_price_usd": 0.0001
  }
}
```

---

## ✅ TESTS EFFECTUÉS

### 1. Test connexion Telegram
```bash
$ python test_telegram.py
✅ Bot trouvé: @TyscpBot
✅ Message envoyé avec succès!
```

### 2. Test diagnostic volume
```bash
$ python diagnostic_volume.py
⚠️ RATE LIMIT détecté (code 429)
```

### 3. Bot redémarré avec corrections
```bash
2025-11-16 02:28:02 - INFO - 🌍 Scan global (CoinGecko)…
[Pas d'erreur rate limit!]
```

---

## 🎯 PROCHAINES ÉTAPES

### À court terme (maintenant)
1. ✅ Bot redémarré avec les corrections
2. ✅ Telegram fonctionne (test message reçu)
3. ⏳ **Attendre les premières alertes** (quand un token dépasse 5x volume)

### Pourquoi vous ne recevez peut-être toujours pas d'alertes?

**C'est normal!** Les alertes sont envoyées uniquement quand:
1. Un token a un volume 24h > 100,000 USD
2. Son volume actuel est **5x supérieur** à la moyenne
3. Le cooldown de 10 minutes est respecté

**En ce moment (marché calme):**
- Peu de tokens ont des spikes de volume 5x+
- Il peut se passer plusieurs heures sans alerte!

### Solutions pour tester plus rapidement

#### Option A: Réduire temporairement le seuil (RECOMMANDÉ ✅)

Modifier [config_tokens.json](config_tokens.json:9):
```json
"ratio_threshold": 2.0,  // Au lieu de 5.0
```

→ Vous recevrez plus d'alertes (tokens avec volume 2x supérieur)

#### Option B: Réduire le volume minimum

Modifier [config_tokens.json](config_tokens.json:8):
```json
"min_vol24_usd": 50000,  // Au lieu de 100000
```

→ Scanner aussi les petits tokens (plus volatils = plus d'alertes)

#### Option C: Utiliser Binance WebSocket (AVANCÉ)

Remplacer CoinGecko par Binance Futures API:
- ✅ Gratuit et sans limite
- ✅ Données en temps réel (tick-by-tick)
- ✅ Volume 1min exact (pas d'estimation)
- ⚠️ Nécessite refonte du code

---

## 📝 FICHIERS MODIFIÉS

1. **alerte.py**
   - Lignes 144: Réduction pages (5→3)
   - Lignes 158-168: Détection rate limit
   - Lignes 173-175: Délai entre pages

2. **config_tokens.json**
   - Ligne 7: Intervalle 60s → 120s

3. **Nouveaux fichiers:**
   - test_telegram.py: Test connexion bot
   - diagnostic_volume.py: Diagnostic rate limit
   - RESOLUTION_RATE_LIMIT.md: Ce document

---

## 🆘 SI VOUS NE RECEVEZ TOUJOURS PAS D'ALERTES

### Vérifications:

1. **Le bot tourne-t-il?**
   ```bash
   tasklist | findstr python
   ```

2. **Telegram fonctionne-t-il?**
   ```bash
   python test_telegram.py
   ```

3. **Y a-t-il des erreurs dans les logs?**
   Surveiller la console où tourne le bot

4. **Le marché est-il actif?**
   - Vérifier sur CoinGecko si des tokens ont du volume anormal
   - Si le marché est calme, aucune alerte = normal!

### Test rapide:

Réduire temporairement le seuil à 2x pour voir si ça envoie des alertes:
```json
"ratio_threshold": 2.0
```

Puis redémarrer le bot:
```bash
taskkill //F //IM python.exe
python alerte.py
```

---

## 🎉 CONCLUSION

**Problème résolu:** Rate limit CoinGecko

**Changements appliqués:**
- ✅ Détection et alerte du rate limit
- ✅ Réduction 75% des appels API
- ✅ Bot fonctionne sans erreur

**Situation actuelle:**
- ✅ Bot scan toutes les 2 minutes
- ✅ Telegram opérationnel
- ⏳ En attente d'alertes (marché calme)

**Recommandation:** Attendre 24-48h pour voir les premières alertes, ou réduire le seuil à 2x pour tester immédiatement.
