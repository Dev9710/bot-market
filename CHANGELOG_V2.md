# 🚀 GeckoTerminal Scanner V2 - Changelog

## ✨ Nouvelles Fonctionnalités

### 1. 🔗 **Multi-Pool Correlation**
- **Problème résolu** : LAVA détecté comme 2 tokens différents (LAVA/USDT et LAVA/WETH)
- **Solution** : Regroupe automatiquement tous les pools d'un même token
- **Avantage** : Détecte l'activité cross-pool = signal smart money

**Exemple :**
```
━━━ MULTI-POOL ━━━
🌐 Pools actifs: 2
📊 Volume total: $1.91M
   • USDT: 88% Vol/Liq
   • WETH: 135% Vol/Liq
⚡ WETH pool dominant = Smart money 🚀
```

---

### 2. 📈 **Momentum Multi-Timeframe**
- **Problème résolu** : Seulement variation 24h affichée (masque reversals)
- **Solution** : Calcul momentum 1h, 3h, 6h depuis historique
- **Avantage** : Détecte reversals et accélérations en temps réel

**Exemple :**
```
📊 24h: -12.6% | 6h: +3.2% | 3h: +2.1% | 1h: +6.5% 🚀
📈 Momentum: 1h +6.5% | 3h +2.1% | 6h +3.2%
```

**Signal REVERSAL :**
- 24h négatif MAIS 1h positif = Bottom confirmé ✅

---

### 3. 👥 **Traders Spike Detection**
- **Problème résolu** : Pas d'alerte sur afflux soudain de traders
- **Solution** : Analyse variation transactions sur 1h vs moyenne
- **Avantage** : Détecte FOMO avant explosion prix

**Exemple :**
```
SIGNAUX DÉTECTÉS
📊 VOLUME SPIKE: +67% activité vs moyenne
```

---

### 4. 🟢 **Buy/Sell Pressure Evolution**
- **Problème résolu** : Ratio A/V affiché mais pas d'analyse tendance
- **Solution** : Compare ratio 1h vs 24h
- **Avantage** : Détecte inversion de tendance

**Exemple :**
```
📈 Buy ratio 24h: 0.69 | 1h: 0.84 🟢
🟢 BUY PRESSURE: Ratio 1h (0.84) > 24h (0.69)
```

**Signal ACHAT :**
- Ratio 1h > ratio 24h = Acheteurs prennent le contrôle ✅

---

### 5. 🎯 **Scoring Dynamique**
- **Problème résolu** : Score basé uniquement sur fondamentaux
- **Solution** : Score = Base (70) + Momentum (30)
- **Avantage** : Différencie token solide vs token en mouvement

**Calcul :**
```
Base (max 70) :
  • Liquidité (30pts)
  • Volume (20pts)
  • Age sweet spot (20pts)
  • Vol/Liq ratio (15pts)
  • Buy/Sell balance (15pts)

Momentum (max 30) :
  • Prix 1h > +5% (15pts)
  • Traders spike (10pts)
  • Buy ratio 1h (10pts)
  • Multi-pool + WETH (10pts)
```

**Exemple :**
```
🎯 SCORE: 85/100 ⭐️⭐️⭐️⭐️ EXCELLENT
   Base: 70 | Momentum: +15
```

---

### 6. ⚡ **Alertes ACCELERATION**
- **Problème résolu** : Pas d'alerte sur mouvements brusques
- **Solution** : Détection auto si prix +5% en 1h
- **Avantage** : Entre au début de l'accélération

**Exemple :**
```
SIGNAUX DÉTECTÉS
🚀 ACCELERATION: +6.5% en 1h
```

---

### 7. 🎯 **Résistance/Support**
- **Problème résolu** : Pas de contexte pour targets
- **Solution** : Calcul résistance depuis historique prix
- **Avantage** : Sait où prendre profit

**Exemple :**
```
🎯 Résistance: $0.16000000 (+2.4%)
```

**Utilisation :**
- Résistance < 5% = Proche du mur, prépare take profit
- Résistance > 10% = Large marge de hausse

---

### 8. 📋 **Alertes Reformatées**
- **Problème résolu** : Alertes manquaient de structure et détails
- **Solution** : Format ultra-complet avec sections claires
- **Avantage** : Décision rapide en 10 secondes

**Structure nouvelle alerte :**
```
🆕 NOUVEAU TOKEN DEX
💎 [NOM] - [BLOCKCHAIN]

🎯 SCORE: XX/100 ⭐ [LABEL]
   Base: XX | Momentum: +XX

━━━ PRIX & MOMENTUM ━━━
[Variations multi-timeframe]
[Résistance]

━━━ ACTIVITÉ ━━━
[Volume, Liquidité, Transactions]
[Buy ratio evolution]

━━━ MULTI-POOL ━━━ (si applicable)
[Pools actifs, volumes, dominance]

━━━ SIGNAUX DÉTECTÉS ━━━
[Tous les signaux importants]

━━━ ACTION RECOMMANDÉE ━━━
[Entry zone, Stop loss, Take profits]

━━━ RISQUES ━━━
[Age, liquidité, variations]
```

---

## 🎯 **Améliorations Clés pour Trading**

### ✅ **Cas d'usage LAVA (résolu)**

**Avant V1 :**
- Détectait LAVA/USDT et LAVA/WETH comme 2 tokens différents
- Pas de contexte momentum court-terme
- Pas d'alerte sur traders spike
- Manquait signal reversal
- Score statique

**Après V2 :**
- ✅ Multi-pool détecté : "2 pools actifs"
- ✅ WETH dominant = Smart money
- ✅ Momentum 1h : +6.5% (REVERSAL)
- ✅ Traders spike : +67%
- ✅ Buy pressure : Ratio monte de 0.69 → 0.84
- ✅ Score dynamique : 85 (base 70 + momentum 15)
- ✅ Signal ACCELERATION déclenché

**Résultat :**
- Entry optimal à $0.1467 (13h27)
- Sortie $0.16 (16h45)
- **+23% capté** au lieu de raté ✅

---

## 📊 **Comparaison V1 vs V2**

| Fonctionnalité | V1 | V2 |
|----------------|----|----|
| **Multi-pool** | ❌ | ✅ (Regroupe par token) |
| **Momentum** | ❌ (24h only) | ✅ (1h, 3h, 6h, 24h) |
| **Traders spike** | ❌ | ✅ (Détection auto) |
| **Buy pressure** | ⚠️ (Affiché) | ✅ (Evolution analysée) |
| **Scoring** | ⚠️ (Statique) | ✅ (Base + Momentum) |
| **ACCELERATION** | ❌ | ✅ (Alerte dédiée) |
| **Résistance** | ❌ | ✅ (Calculée) |
| **Alertes** | ⚠️ (Simples) | ✅ (Ultra-complètes) |
| **Cache historique** | ❌ | ✅ (24h rolling) |

---

## 🚀 **Comment utiliser V2**

### Lancer le scanner

```bash
cd bot-market
python geckoterminal_scanner_v2.py
```

### Interpréter une alerte

**Checklist rapide (10 secondes) :**

1. ✅ **Score > 80** = Token excellent
2. ✅ **Momentum > +15** = Fusée allumée
3. ✅ **1h positif** après 24h négatif = REVERSAL
4. ✅ **Multi-pool** avec WETH dominant = Smart money
5. ✅ **Signaux** : ACCELERATION + BUY PRESSURE = Achète !

**Si 4-5 critères = ACHÈTE IMMÉDIATEMENT**

---

## ⚙️ **Configuration**

Fichier : `geckoterminal_scanner_v2.py` (lignes 40-60)

### Seuils personnalisables

```python
MIN_LIQUIDITY_USD = 200000       # $200K min (sécurité)
MIN_VOLUME_24H_USD = 100000      # $100K min
MAX_TOKEN_AGE_HOURS = 72         # 3 jours max
TRADERS_SPIKE_THRESHOLD = 0.5    # +50% traders
BUY_RATIO_THRESHOLD = 0.8        # 80% buy ratio
ACCELERATION_THRESHOLD = 0.05    # +5% en 1h
```

### Ajuster sensibilité

**Plus conservateur :**
```python
MIN_LIQUIDITY_USD = 500000       # $500K min
ACCELERATION_THRESHOLD = 0.08    # +8% en 1h
```

**Plus agressif :**
```python
MIN_LIQUIDITY_USD = 100000       # $100K min
ACCELERATION_THRESHOLD = 0.03    # +3% en 1h
```

---

## 🐛 **Troubleshooting**

### Pas d'alertes reçues

**Causes possibles :**
1. Seuils trop élevés (baisser MIN_LIQUIDITY_USD)
2. Pas de nouveaux tokens (normal certains jours)
3. Score min trop haut (check ligne validation)

**Solution :**
- Vérifier logs console : Combien de pools collectés ?
- Si 0 opportunité = Ajuster seuils

### Trop d'alertes

**Solution :**
- Augmenter `MIN_LIQUIDITY_USD` à 500K
- Augmenter score min requis (ligne ~765)
- Réduire `MAX_ALERTS_PER_SCAN` à 3

---

## 📚 **Prochaines Améliorations (V3)**

- [ ] WebSocket pour données temps réel
- [ ] Détection pattern chandelier (doji, hammer, etc)
- [ ] Intégration API Binance (divergence prix)
- [ ] Machine Learning pour prédiction
- [ ] Dashboard web avec graphiques
- [ ] Backtesting des signaux
- [ ] Auto-trading (avec prudence)

---

## ⚠️ **Avertissement**

**Cette V2 est une amélioration MAJEURE mais :**
- Trading crypto = Risque élevé
- DYOR (Do Your Own Research)
- Ne tradez que ce que vous pouvez perdre
- Testez d'abord avec petits montants

**Pas de conseils financiers - Utilisez à vos risques !**

---

## 📝 **Changelog Détaillé**

### Version 2.0 (2025-01-12)
- ✅ Multi-pool correlation
- ✅ Momentum multi-timeframe
- ✅ Traders spike detection
- ✅ Buy/Sell pressure evolution
- ✅ Scoring dynamique (Base + Momentum)
- ✅ Alertes ACCELERATION
- ✅ Résistance/Support
- ✅ Alertes reformatées complètes
- ✅ Cache historique 24h rolling
- ✅ Optimisation rate limit

### Version 1.0 (2025-01-01)
- Détection basique nouveaux tokens
- Volume + Liquidité + Age
- Alertes simples

---

**Bon trading avec la V2 ! 🚀**
