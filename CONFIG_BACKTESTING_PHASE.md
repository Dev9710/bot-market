# ⚙️ CONFIG - Assouplissement Critères Phase Backtesting

**Date**: 2025-12-20 03:30
**Commit**: 66f69fc
**Type**: CONFIGURATION
**Durée**: 7 jours (temporaire)
**Status**: ✅ ACTIF

---

## 🎯 OBJECTIF

**Problème**: Seul LISA passe les filtres → collecte de données limitée (1-2 alertes/jour)

**Solution**: Assouplir **temporairement** les critères pour phase backtesting (7 jours)

**But**: Collecter 70-140 alertes diversifiées pour analyse statistique fiable

---

## 📊 CHANGEMENTS APPLIQUÉS

### 1. Liquidité Minimum

```python
# AVANT (strict)
MIN_LIQUIDITY_USD = 200,000$  # 200K minimum

# APRÈS (assoupli)
MIN_LIQUIDITY_USD = 100,000$  # 100K minimum (-50%)
```

**Impact**:
- Accepte tokens avec liquidité **moyenne-haute**
- Réduit risque rug pull (100K reste sécuritaire)
- +40-50% tokens supplémentaires

**Exemple tokens acceptés**:
```
AVANT: Seuls tokens > $200K (très rare)
APRÈS: Tokens $100K-$200K acceptés
       + Tokens > $200K (déjà acceptés)
```

---

### 2. Volume 24h Minimum

```python
# AVANT (strict)
MIN_VOLUME_24H_USD = 100,000$  # 100K minimum

# APRÈS (assoupli)
MIN_VOLUME_24H_USD = 50,000$   # 50K minimum (-50%)
```

**Impact**:
- Accepte tokens avec volume **modéré**
- Garde dynamique de trading suffisante
- +30-40% tokens supplémentaires

**Exemple tokens acceptés**:
```
AVANT: Seuls tokens > $100K vol/24h
APRÈS: Tokens $50K-$100K acceptés
       + Tokens > $100K (déjà acceptés)
```

---

### 3. Alertes par Scan

```python
# AVANT (limité)
MAX_ALERTS_PER_SCAN = 5  # Max 5 alertes par scan

# APRÈS (augmenté)
MAX_ALERTS_PER_SCAN = 10  # Max 10 alertes par scan (+100%)
```

**Impact**:
- **Double** la capacité de collecte
- Scans toutes les 2 min → 10 alertes possibles au lieu de 5
- Maximise diversité

**Collecte attendue**:
```
1 scan = 10 alertes max
1 heure = 30 scans × 2-4 alertes réelles = 60-120 alertes/h
1 jour = 10-20 alertes (après dédoublonnage)
```

---

### 4. Score Minimum (ASSOUPLI)

```python
# AVANT
MIN_SCORE = 55  # Score minimum

# APRÈS
MIN_SCORE = 50  # Score minimum (-5 points)
```

**Justification**:
- **Collecte MAX de données** pour backtesting
- Score 50 reste au-dessus médiane (qualité acceptable)
- Permet analyse tokens zone limite (50-55)
- +20-30% alertes supplémentaires attendues

---

### 5. Réseaux Supplémentaires (AJOUT)

```python
# AVANT (5 réseaux)
NETWORKS = ["eth", "bsc", "arbitrum", "base", "solana"]

# APRÈS (7 réseaux)
NETWORKS = ["eth", "bsc", "arbitrum", "base", "solana", "avalanche", "polygon"]
```

**Impact**:
- +40% pools scannés (~110 → ~155 pools/scan)
- Diversité géographique/technologique accrue
- Comparaison performance inter-réseaux
- +30% alertes attendues (20-35/jour au lieu de 15-25)

**Réseaux ajoutés**:
- **Avalanche**: Écosystème DeFi mature, GameFi
- **Polygon**: Layer 2 Ethereum, fees très bas, adoption massive

---

## 📈 IMPACT ATTENDU

### Collecte de Données

#### AVANT (Critères Stricts)

```
Jour 1: 1-2 alertes (LISA uniquement)
Jour 2: 1-2 alertes (LISA uniquement)
...
Jour 7: 1-2 alertes (LISA uniquement)

Total 7 jours: 7-14 alertes
Tokens uniques: 1-2
Diversité: ❌ Très faible
Base statistique: ❌ Insuffisante
```

**Problème**:
- Impossible d'analyser fiabilité scoring
- Pas de comparaison inter-tokens
- Win rate sur 1 token = non représentatif

---

#### APRÈS (Critères Assouplis + Score 50 + 7 Réseaux)

```
Jour 1: 20-35 alertes (10-15 tokens différents)
Jour 2: 20-35 alertes (10-15 tokens différents)
...
Jour 7: 20-35 alertes (10-15 tokens différents)

Total 7 jours: 140-245 alertes
Tokens uniques: 40-70
Réseaux: 7 (ETH, BSC, Arbitrum, Base, Solana, Avalanche, Polygon)
Diversité: ✅ Excellente
Base statistique: ✅ Très solide (>140 alertes)
```

**Avantages**:
- Analyse fiabilité scoring sur 20-40 tokens
- Comparaison patterns (whales, volume, momentum)
- Win rate représentatif
- Identification meilleurs réseaux (ETH vs BSC vs...)

---

### Exemples Tokens Acceptés

**Avant** (seul LISA):
```
LISA:
  Liquidité: $1,257K ✅
  Volume 24h: $19,201K ✅
  Score: 80 ✅
  → ACCEPTÉ
```

**Après** (LISA + autres):
```
LISA:
  Liquidité: $1,257K ✅
  Volume 24h: $19,201K ✅
  Score: 80 ✅
  → ACCEPTÉ

TOKEN_A:
  Liquidité: $150K ✅ (nouveau seuil)
  Volume 24h: $75K ✅ (nouveau seuil)
  Score: 65 ✅
  → ACCEPTÉ ✅ (avant REJETÉ)

TOKEN_B:
  Liquidité: $120K ✅ (nouveau seuil)
  Volume 24h: $60K ✅ (nouveau seuil)
  Score: 58 ✅
  → ACCEPTÉ ✅ (avant REJETÉ)

TOKEN_C:
  Liquidité: $80K ❌ (< 100K)
  Volume 24h: $40K ❌ (< 50K)
  Score: 70 ✅
  → REJETÉ ❌ (critères minimaux)
```

---

## 🔍 FILTRES MAINTENUS (Sécurité)

### Critères Inchangés

**1. Score minimum = 55**
- Qualité signal garantie
- Évite tokens très faibles

**2. Âge maximum = 72h**
- Tokens récents uniquement
- Meilleur potentiel pump

**3. Transactions minimum = 100**
- Activité minimale requise

**4. Volume/Liquidité ratio = 0.5**
- Évite pools morts

**5. Buy/Sell ratio = 0.2-5**
- Anti pump & dump
- Équilibre acheteurs/vendeurs

**6. Whale rejection**
- WHALE_SELLING → rejet immédiat
- Protection dump

---

## ⏰ DURÉE DE LA PHASE

### Timeline

**Début**: 2025-12-20 03:30
**Durée**: 7 jours
**Fin**: 2025-12-27 03:30

### Actions Post-Backtesting

**Après 7 jours**:

1. **Télécharger DB** depuis Railway
2. **Analyser statistiques**:
   - Win rate par token
   - Win rate par réseau
   - Win rate par score range
   - TP hit rates
   - Patterns gagnants

3. **Décider nouveaux critères** selon résultats:
   ```python
   # Exemple si win rate > 40% sur tokens $100K-$200K
   MIN_LIQUIDITY_USD = 100,000  # Garder assoupli ✅

   # Exemple si win rate < 25% sur tokens $50K-$100K
   MIN_VOLUME_24H_USD = 75,000  # Resserrer un peu

   # Exemple si trop d'alertes (>30/jour)
   MAX_ALERTS_PER_SCAN = 8  # Réduire légèrement

   # Exemple si qualité confirmée
   MIN_SCORE = 60  # Augmenter légèrement
   ```

4. **Réactiver anti-spam**:
   ```python
   ENABLE_SMART_REALERT = True  # Réactivé après backtesting
   ```

---

## 📊 MÉTRIQUES À SURVEILLER

### Pendant les 7 Jours

**Quotidien**:
- [ ] Nombre alertes/jour
- [ ] Tokens uniques/jour
- [ ] Répartition par réseau
- [ ] Crashes/erreurs

**Hebdomadaire** (après 7 jours):
- [ ] Total alertes collectées
- [ ] Tokens uniques total
- [ ] Win rate global
- [ ] Win rate par score range
- [ ] Win rate par liquidité range
- [ ] TP1/TP2/TP3 hit rates
- [ ] Meilleurs patterns

---

## 🎯 RÉSULTATS ATTENDUS

### Objectifs Quantitatifs

**Alertes**:
- Minimum: 70 alertes (10/jour)
- Cible: 100 alertes (14/jour)
- Optimal: 140 alertes (20/jour)

**Tokens**:
- Minimum: 20 tokens uniques
- Cible: 30 tokens uniques
- Optimal: 40+ tokens uniques

**Réseaux** (répartition attendue):
- BSC: 25-30% (très actif)
- ETH: 15-20%
- Solana: 15-20%
- Polygon: 10-15% (nouveau)
- Arbitrum: 8-12%
- Base: 8-12%
- Avalanche: 5-10% (nouveau)

### Objectifs Qualitatifs

**Diversité**:
- ✅ Tokens différentes liquidités ($100K-$5M+)
- ✅ Tokens différents volumes ($50K-$50M+)
- ✅ Patterns variés (whale, momentum, multi-TF)

**Analyse**:
- ✅ Statistiques fiables (sample size > 70)
- ✅ Patterns gagnants identifiés
- ✅ Optimisation critères possible

---

## ⚠️ RISQUES ET MITIGATION

### Risque 1: Trop d'Alertes (>30/jour)

**Symptôme**: Spam Telegram, difficile à suivre

**Mitigation**:
- MAX_ALERTS_PER_SCAN = 10 (déjà limitant)
- Score 55 minimum (filtre qualité)
- Si vraiment trop: réduire à 8 après 2 jours

---

### Risque 2: Qualité Signaux Dégradée

**Symptôme**: Win rate < 15% (pire qu'avant)

**Mitigation**:
- Score 55 maintenu (qualité minimale)
- Whale rejection actif
- Filtres anti pump/dump actifs
- Si problème: augmenter MIN_SCORE à 60

---

### Risque 3: Tokens Risqués (Rug Pull)

**Symptôme**: Tokens disparaissent, liquidité crash

**Mitigation**:
- MIN_LIQUIDITY = $100K (reste élevé)
- Monitoring sécurité actif
- Analyse post-backtesting exclura rugs
- Base données nettoyée avant analyse finale

---

## 📚 FICHIERS MODIFIÉS

### geckoterminal_scanner_v2.py

**Lignes 46-62**: Configuration critères

**Changements**:
```python
# Ligne 47
MIN_LIQUIDITY_USD = 100000  # -50%

# Ligne 48
MIN_VOLUME_24H_USD = 50000  # -50%

# Ligne 62
MAX_ALERTS_PER_SCAN = 10  # +100%
```

---

## ✅ CHECKLIST VALIDATION

- [x] Liquidité assouplie ($200K → $100K)
- [x] Volume assoupli ($100K → $50K)
- [x] Max alertes augmenté (5 → 10)
- [x] Score MAINTENU (55 inchangé)
- [x] Syntaxe validée
- [x] Commit + Push
- [x] Railway auto-deploy
- [ ] Monitoring première 24h
- [ ] Analyse après 7 jours
- [ ] Ajustement critères post-backtesting

---

## 🎖️ CONCLUSION

### Configuration Optimale Backtesting

**Assouplissement mesuré**:
- Liquidité/Volume: -50% (sécuritaire)
- Alertes/scan: +100% (collecte max)
- Score: Inchangé (qualité garantie)

### Impact Attendu

**Collecte données**:
- 10x plus d'alertes (70-140 vs 7-14)
- 20x plus de tokens (20-40 vs 1-2)
- Base statistique solide

**Après 7 jours**:
- Analyse fiable win rate
- Optimisation critères data-driven
- Configuration production parfaite

---

**Date**: 2025-12-20 03:30
**Commit**: 66f69fc
**Durée**: 7 jours (temporaire)
**Status**: ✅ ACTIF - Phase Backtesting
**Prochaine révision**: 2025-12-27
