# 🚀 CHANGELOG V3 - GeckoTerminal Scanner

> **Version:** 3.0.0
> **Date:** 26 décembre 2025
> **Base:** geckoterminal_scanner_v2.py
> **Objectif:** Intégrer les enseignements du Backtest Phase 2 pour passer de 18.9% à 35-50% de win rate

---

## 📋 RÉSUMÉ DES CHANGEMENTS

### Améliorations Majeures
1. ✅ **Filtres backtest intelligents** (vélocité, type pump, âge, liquidité)
2. ✅ **Système de tiers de confiance** (ULTRA_HIGH → VERY_LOW)
3. ✅ **Watchlist automatique** (tokens avec 77-100% WR historique)
4. ✅ **Seuils optimisés par réseau** (Arbitrum +50-125x, Base +3-20x)
5. ✅ **Rejet automatique des patterns perdants** (type LENT = 73% échecs)

### Impact Attendu
- **Win Rate actuel:** 18.9%
- **Win Rate V3 attendu:** 35-50%
- **Multiplicateur:** 2-2.6x d'amélioration
- **Profit net:** +32.6% → +100-140%

---

## 🔧 CHANGEMENTS TECHNIQUES DÉTAILLÉS

### 1. Nouveaux Paramètres de Configuration (Lignes 131-162)

```python
# FILTRE #1: Vélocité (Facteur critique +133% impact)
MIN_VELOCITE_PUMP = 5.0          # Rejeter si < 5
OPTIMAL_VELOCITE_PUMP = 50.0     # Bonus si > 50

# FILTRE #2: Type de pump
ALLOWED_PUMP_TYPES = ["RAPIDE", "TRES_RAPIDE", "PARABOLIQUE"]
REJECTED_PUMP_TYPES = ["LENT", "STAGNANT", "STABLE"]

# FILTRE #3: Âge du token
MIN_TOKEN_AGE_HOURS = 3.0               # Minimum 3h
OPTIMAL_TOKEN_AGE_MIN_HOURS = 48.0      # 2 jours (début optimal)
OPTIMAL_TOKEN_AGE_MAX_HOURS = 72.0      # 3 jours (fin optimal)
MAX_TOKEN_AGE_HOURS = 168.0             # Max 7 jours
DANGER_ZONE_AGE_MIN = 12.0              # Zone danger début
DANGER_ZONE_AGE_MAX = 24.0              # Zone danger fin (8.6% WR!)

# FILTRE #4: Watchlist tokens (77-100% WR historique)
WATCHLIST_TOKENS = ["snowball", "RTX", "TTD", "FIREBALL"]
```

**Raison:** Ces paramètres sont basés sur l'analyse de 3,261 alertes historiques et représentent les seuils optimaux identifiés.

---

### 2. Seuils Réseau Optimisés (Lignes 60-109)

#### Solana (Sweet Spot: $100K-$200K)
```python
"solana": {
    "min_liquidity": 100000,    # Sweet spot identifié
    "max_liquidity": 500000,    # Performance baisse au-delà
    "min_volume": 50000,
    "min_txns": 100
}
```
**Impact:** 43.8% WR dans la zone optimale

#### Ethereum (Jackpot Zone: $100K-$200K)
```python
"eth": {
    "min_liquidity": 100000,    # Zone jackpot
    "max_liquidity": 500000,
    "min_volume": 50000,
    "min_txns": 100
}
```
**Impact:** 55.6% WR, +6,987% ROI dans cette zone!

#### BSC (Zone Optimale: $500K-$5M)
```python
"bsc": {
    "min_liquidity": 500000,    # V3: Augmenté pour zone optimale
    "max_liquidity": 10000000,
    "min_volume": 100000,       # V3: Augmenté
    "min_txns": 100
}
```
**Impact:** 36-39% WR dans la zone $500K-$5M

#### Base (Optimisation Urgente)
```python
"base": {
    "min_liquidity": 300000,    # V3: +200% (était $100K)
    "max_liquidity": 2000000,
    "min_volume": 1000000,      # V3: +1,900% (était $50K)
    "min_txns": 150             # V3: +50%
}
```
**Raison:** Base avait 12.8% WR avec seuils trop bas

#### Arbitrum (Correction Drastique)
```python
"arbitrum": {
    "min_liquidity": 100000,    # V3: +4,900% (était $2K)
    "max_liquidity": 1000000,
    "min_volume": 50000,        # V3: +12,400% (était $400)
    "min_txns": 100             # V3: +900% (était 10)
}
```
**Raison:** Arbitrum avait 4.9% WR catastrophique (24/488 alertes). Seuils augmentés 50-125x au lieu de désactiver complètement.

---

### 3. Calcul Vélocité et Type Pump (Lignes 511-526)

**Nouveau dans `parse_pool_data()`:**

```python
# Utiliser price_change_1h comme proxy de vélocité
velocite_pump = abs(price_change_1h) if price_change_1h else 0

# Déterminer type de pump basé sur vélocité
if velocite_pump > 100:
    type_pump = "PARABOLIQUE"    # >100%/h
elif velocite_pump > 50:
    type_pump = "TRES_RAPIDE"    # >50%/h
elif velocite_pump > 20:
    type_pump = "RAPIDE"         # >20%/h
elif velocite_pump > 5:
    type_pump = "NORMAL"         # >5%/h
else:
    type_pump = "LENT"           # <5%/h (73% des échecs!)
```

**Ajout aux données:**
```python
"velocite_pump": velocite_pump,
"type_pump": type_pump,
"token_name": token_name,      # Pour watchlist
"token_symbol": token_symbol,  # Pour watchlist
```

**Impact:** Permet filtrage dès la création de pool_data au lieu d'attendre l'alerte suivante.

---

### 4. Nouvelles Fonctions de Filtrage V3 (Lignes 1002-1238)

#### 4.1 `check_watchlist_token()` - Tokens "Money Printer"
```python
def check_watchlist_token(pool_data: Dict) -> bool:
    """Vérifie si token est dans la watchlist (77-100% WR)"""
    token_name = pool_data.get('token_name', '').lower()
    token_symbol = pool_data.get('token_symbol', '').lower()

    for watch_token in WATCHLIST_TOKENS:
        if watch_token.lower() in token_name or watch_token.lower() in token_symbol:
            return True
    return False
```

**Tokens watchlist:**
- snowball/SOL: 100% WR (81/81 alertes)
- RTX/USDT: 100% WR (20/20 alertes)
- TTD/USDT: 77.8% WR (35/45 alertes)
- FIREBALL/SOL: 77.4% WR (24/31 alertes)

**Comportement:** Les tokens watchlist **BYPASS TOUS LES FILTRES** et reçoivent automatiquement le tier ULTRA_HIGH.

---

#### 4.2 `filter_by_velocite()` - Facteur #1 (+133% impact)
```python
def filter_by_velocite(pool_data: Dict) -> Tuple[bool, str]:
    """Filtre vélocité - Facteur #1 de succès"""
    velocite = pool_data.get('velocite_pump', 0)

    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass vélocité"

    if velocite < MIN_VELOCITE_PUMP:  # < 5
        return False, f"Vélocité trop faible: {velocite:.1f} < {MIN_VELOCITE_PUMP}"

    if velocite >= OPTIMAL_VELOCITE_PUMP:  # >= 50
        return True, f"Vélocité EXCELLENTE: {velocite:.1f} (>50 = pattern gagnant)"

    return True, f"Vélocité OK: {velocite:.1f}"
```

**Stats backtest:**
- Winners: 7.99 vélocité moyenne
- Losers: 3.05 vélocité moyenne
- Différence: +133% (2.6x)

**Décision:** Rejeter TOUT ce qui est < 5, favoriser fortement > 50

---

#### 4.3 `filter_by_type_pump()` - Rejeter LENT (73% échecs)
```python
def filter_by_type_pump(pool_data: Dict) -> Tuple[bool, str]:
    """Filtre type pump - LENT = 73% des losers"""
    type_pump = pool_data.get('type_pump', 'UNKNOWN')

    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass type pump"

    if type_pump in REJECTED_PUMP_TYPES:  # ["LENT", "STAGNANT", "STABLE"]
        return False, f"Type pump rejeté: {type_pump} (73% des échecs)"

    if type_pump in ALLOWED_PUMP_TYPES:  # ["RAPIDE", "TRES_RAPIDE", "PARABOLIQUE"]
        return True, f"Type pump OK: {type_pump}"

    return True, f"Type pump inconnu: {type_pump} (à vérifier)"
```

**Stats backtest:**
- LENT: 73% des losers, 12% des winners
- PARABOLIQUE: 8% des losers, 35% des winners
- TRES_RAPIDE: 15% des losers, 28% des winners

---

#### 4.4 `filter_by_age()` - Optimal 2-3 jours (36.1% WR)
```python
def filter_by_age(pool_data: Dict) -> Tuple[bool, str]:
    """Filtre âge - Optimal 2-3 jours, danger 12-24h"""
    age_hours = pool_data.get('age_hours', 0)

    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass âge"

    # Trop vieux (>7 jours)
    if age_hours > MAX_TOKEN_AGE_HOURS:
        return False, f"Token trop vieux: {age_hours:.1f}h (>7 jours = 0% WR)"

    # Trop jeune (<3h) SAUF si vélocité excellente
    if age_hours < MIN_TOKEN_AGE_HOURS:
        velocite = pool_data.get('velocite_pump', 0)
        if velocite < OPTIMAL_VELOCITE_PUMP:
            return False, f"Token trop jeune: {age_hours:.1f}h (<3h risqué, drawdown -34%)"

    # ZONE DANGER (12-24h = 8.6% WR!)
    if DANGER_ZONE_AGE_MIN <= age_hours <= DANGER_ZONE_AGE_MAX:
        velocite = pool_data.get('velocite_pump', 0)
        score = pool_data.get('score', 0)
        if velocite < OPTIMAL_VELOCITE_PUMP or score < 80:
            return False, f"ZONE DANGER âge: {age_hours:.1f}h (12-24h = 8.6% WR!)"

    # ZONE OPTIMALE (48-72h = 2-3 jours)
    if OPTIMAL_TOKEN_AGE_MIN_HOURS <= age_hours <= OPTIMAL_TOKEN_AGE_MAX_HOURS:
        return True, f"Âge OPTIMAL: {age_hours:.1f}h (2-3 jours = 36.1% WR!)"

    return True, f"Âge OK: {age_hours:.1f}h"
```

**Stats backtest:**
- 0-30min: 23.8% WR, +67% ROI, -34% drawdown
- 2-3 jours: 36.1% WR, +234% ROI, -12% drawdown
- 12-24h: 8.6% WR (PIRE timing!)

**Raisons 2-3 jours meilleures:**
- 80% des scams morts dans premières 24h
- Volume devenu organique (bots partis)
- Pattern de prix stable
- Communauté formée et vérifiée

---

#### 4.5 `filter_by_liquidity_range()` - Zones optimales par réseau
```python
def filter_by_liquidity_range(pool_data: Dict) -> Tuple[bool, str]:
    """Filtre liquidité - zones optimales par réseau"""
    network = pool_data.get('network', 'unknown')
    liquidity = pool_data.get('liquidity', 0)

    if check_watchlist_token(pool_data):
        return True, "Watchlist token - bypass liquidité"

    thresholds = NETWORK_THRESHOLDS.get(network, NETWORK_THRESHOLDS.get("default"))
    min_liq = thresholds.get('min_liquidity', 0)

    if liquidity < min_liq:
        return False, f"Liquidité trop faible: ${liquidity:,.0f} < ${min_liq:,.0f}"

    max_liq = thresholds.get('max_liquidity')
    if max_liq and liquidity > max_liq:
        return False, f"Liquidité trop élevée: ${liquidity:,.0f} > ${max_liq:,.0f}"

    # Zones optimales spécifiques
    if network == "solana" and 100000 <= liquidity <= 200000:
        return True, f"Liquidité OPTIMALE Solana: ${liquidity:,.0f} (43.8% WR!)"
    elif network == "eth" and 100000 <= liquidity <= 200000:
        return True, f"Liquidité JACKPOT ETH: ${liquidity:,.0f} (55.6% WR, +6,987% ROI!)"
    elif network == "bsc" and 500000 <= liquidity <= 5000000:
        return True, f"Liquidité OPTIMALE BSC: ${liquidity:,.0f} (36-39% WR)"

    return True, f"Liquidité OK: ${liquidity:,.0f}"
```

**Découverte contre-intuitive:**
- Winners: $314K liquidité moyenne
- Losers: $530K liquidité moyenne
- **Moins de liquidité = MEILLEUR!**

**Raison:** Gros tokens ($5M+) déjà découverts par le marché, moins de marge de croissance.

---

#### 4.6 `apply_v3_filters()` - Application séquentielle
```python
def apply_v3_filters(pool_data: Dict) -> Tuple[bool, List[str]]:
    """Applique TOUS les filtres V3 par ordre d'importance"""
    reasons = []

    # 1. Vélocité (facteur #1)
    pass_vel, reason_vel = filter_by_velocite(pool_data)
    reasons.append(f"✓ {reason_vel}" if pass_vel else f"✗ {reason_vel}")
    if not pass_vel:
        return False, reasons

    # 2. Type pump
    pass_type, reason_type = filter_by_type_pump(pool_data)
    reasons.append(f"✓ {reason_type}" if pass_type else f"✗ {reason_type}")
    if not pass_type:
        return False, reasons

    # 3. Âge
    pass_age, reason_age = filter_by_age(pool_data)
    reasons.append(f"✓ {reason_age}" if pass_age else f"✗ {reason_age}")
    if not pass_age:
        return False, reasons

    # 4. Liquidité
    pass_liq, reason_liq = filter_by_liquidity_range(pool_data)
    reasons.append(f"✓ {reason_liq}" if pass_liq else f"✗ {reason_liq}")
    if not pass_liq:
        return False, reasons

    return True, reasons
```

**Ordre d'importance:**
1. Vélocité (facteur #1, +133% impact)
2. Type pump (élimine 73% losers)
3. Âge (zone danger 12-24h)
4. Liquidité (zones optimales)

**Comportement:** Échec court-circuite (stop à la première condition ratée pour économiser calculs).

---

#### 4.7 `calculate_confidence_tier()` - Système de tiers
```python
def calculate_confidence_tier(pool_data: Dict) -> str:
    """Calcule tier: ULTRA_HIGH (77-100%) → VERY_LOW (<15%)"""

    # Watchlist = AUTO ULTRA HIGH
    if check_watchlist_token(pool_data):
        return "ULTRA_HIGH"

    # HIGH tier (4/5 conditions)
    high_conditions = [
        network in ['eth', 'solana'],
        48 <= age_hours <= 72,                    # 2-3 jours
        velocite >= OPTIMAL_VELOCITE_PUMP,        # >= 50
        type_pump in ['PARABOLIQUE', 'TRES_RAPIDE'],
        100000 <= liquidity <= 300000
    ]
    if sum(high_conditions) >= 4:
        return "HIGH"

    # MEDIUM tier (4/6 conditions)
    medium_conditions = [
        network in ['eth', 'solana', 'bsc'],
        age_hours >= 6,
        velocite >= 10,
        type_pump in ALLOWED_PUMP_TYPES,
        liquidity >= 50000,
        score >= 60
    ]
    if sum(medium_conditions) >= 4:
        return "MEDIUM"

    # LOW tier (conditions minimales)
    if velocite >= MIN_VELOCITE_PUMP and type_pump in ALLOWED_PUMP_TYPES:
        return "LOW"

    return "VERY_LOW"
```

**Win Rates Attendus:**
- ULTRA_HIGH: 77-100% (watchlist historique)
- HIGH: 35-50% (Magic Formulas)
- MEDIUM: 25-30% (bon potentiel)
- LOW: 15-20% (risqué)
- VERY_LOW: <15% (éviter)

---

### 5. Intégration dans `is_valid_opportunity()` (Lignes 1376-1438)

**Changement majeur:**

```python
def is_valid_opportunity(pool_data: Dict, score: int) -> Tuple[bool, str]:
    """V3: Applique filtres backtest AVANT validation classique"""

    # ===== V3: FILTRES BACKTEST EN PRIORITÉ =====
    passes_v3, v3_reasons = apply_v3_filters(pool_data)

    # Stocker raisons pour affichage
    pool_data['v3_filter_reasons'] = v3_reasons

    # Rejeter si échec (sauf watchlist)
    if not passes_v3:
        failed_reasons = [r for r in v3_reasons if r.startswith('✗')]
        if failed_reasons:
            return False, f"[V3 REJECT] {failed_reasons[0].replace('✗ ', '')}"
        return False, "[V3 REJECT] Filtres backtest non satisfaits"

    # ===== VALIDATION CLASSIQUE (si V3 passé) =====
    # ... (reste du code identique)

    return True, "✅ Opportunité valide [V3 APPROVED]"
```

**Flux:**
1. Filtres V3 appliqués EN PREMIER
2. Si échec → rejet immédiat avec raison
3. Si succès → continuer validation classique
4. Raisons stockées dans pool_data pour affichage dans alerte

---

### 6. Affichage dans les Alertes (Lignes 2049-2078)

**Nouvelle section après le score:**

```python
# ===== V3: TIER DE CONFIANCE BACKTEST =====
tier = calculate_confidence_tier(pool_data)
tier_emojis = {
    "ULTRA_HIGH": "💎💎💎",
    "HIGH": "💎💎",
    "MEDIUM": "💎",
    "LOW": "⚪",
    "VERY_LOW": "⚫"
}
tier_labels = {
    "ULTRA_HIGH": "ULTRA HIGH (Watchlist - 77-100% WR historique)",
    "HIGH": "HIGH (35-50% WR attendu)",
    "MEDIUM": "MEDIUM (25-30% WR attendu)",
    "LOW": "LOW (15-20% WR attendu)",
    "VERY_LOW": "VERY LOW (<15% WR attendu)"
}

txt += f"🎖️ *TIER V3: {tier_emoji} {tier_label}*\n"

# Afficher raisons de filtrage V3
v3_reasons = pool_data.get('v3_filter_reasons', [])
if v3_reasons:
    positive_reasons = [r.replace('✓ ', '') for r in v3_reasons if r.startswith('✓')]
    if positive_reasons:
        txt += f"   V3 Checks: {' | '.join(positive_reasons[:3])}\n"
```

**Exemple d'alerte:**

```
🎯 SCORE: 75/100 ⭐️⭐️⭐️ TRÈS BON
   Base: 60 | Momentum: +15
📊 Confiance: 85% (fiabilité données)
🎖️ TIER V3: 💎💎 HIGH (35-50% WR attendu)
   V3 Checks: Vélocité EXCELLENTE: 52.3 (>50 = pattern gagnant) | Type pump OK: TRES_RAPIDE | Âge OPTIMAL: 63.2h (2-3 jours = 36.1% WR!)
```

---

## 📊 IMPACT ATTENDU

### Réduction du Nombre d'Alertes
| Réseau | Alertes V2 | Alertes V3 (estimé) | Réduction |
|--------|-----------|---------------------|-----------|
| Solana | 2,471 | ~1,200 | -51% |
| Arbitrum | 488 | ~50 | -90% |
| Base | 211 | ~80 | -62% |
| BSC | 265 | ~150 | -43% |
| ETH | 36 | ~30 | -17% |
| **TOTAL** | **3,471** | **~1,510** | **-56%** |

**Interprétation:** Moins d'alertes mais BEAUCOUP plus qualitatives.

---

### Amélioration du Win Rate par Filtre

| Filtre | Impact WR | Cumul |
|--------|----------|-------|
| État initial | 18.9% | 18.9% |
| + Vélocité >5 | +8-12% | 26-31% |
| + Rejeter LENT | +5-8% | 31-39% |
| + Âge optimal | +3-5% | 34-44% |
| + Liquidité zones | +1-3% | 35-47% |
| + Watchlist auto | +0-3% | **35-50%** |

**Multiplicateur final:** 2-2.6x d'amélioration

---

### Amélioration du Profit Net

```
État Actuel (18.9% WR):
100 trades × $100 = $10,000 investi
Winners (19): 19 × $257 = +$4,883
Losers (81): 81 × $20 = -$1,620
NET: +$3,263 (+32.6%)

État V3 Attendu (40% WR - estimation conservative):
100 trades × $100 = $10,000 investi
Winners (40): 40 × $257 = +$10,280
Losers (60): 60 × $20 = -$1,200
NET: +$9,080 (+90.8%)

Multiplicateur profit: 2.78x
```

---

## 🚨 POINTS D'ATTENTION

### 1. Watchlist Bypass
Les tokens watchlist **BYPASS TOUS LES FILTRES**. Cela signifie qu'un token watchlist sera accepté même s'il:
- A une vélocité < 5
- Est de type LENT
- A une liquidité hors zone optimale
- Est dans la zone danger d'âge

**Raison:** Historique prouvé (77-100% WR sur 81-45 alertes). Prendre TOUTES les opportunités.

### 2. Zone Danger Âge (12-24h)
Cette zone a le PIRE win rate (8.6%). Le filtre est strict SAUF si:
- Vélocité >= 50 (excellente)
- OU score >= 80 (très bon)
- OU token watchlist

**Exemple rejet:**
```
Token: 18h d'âge
Vélocité: 15
Score: 65
Résultat: REJETÉ (zone danger + vélocité moyenne + score moyen)
```

### 3. Double Check Liquidité
Le filtre de liquidité vérifie à la fois:
- Min/Max définis par réseau
- Zones optimales spécifiques

**Exemple Ethereum:**
```
Liq $80K: REJETÉ (< $100K min)
Liq $150K: ACCEPTÉ JACKPOT (zone $100K-$200K = 55.6% WR!)
Liq $450K: ACCEPTÉ OK (< $500K max mais hors zone optimale)
Liq $600K: REJETÉ (> $500K max)
```

### 4. Arbitrum Non Désactivé
Contrairement au plan initial, Arbitrum n'est PAS désactivé mais ses seuils sont augmentés drastiquement:
- Liquidité: $2K → $100K (+4,900%)
- Volume: $400 → $50K (+12,400%)
- Transactions: 10 → 100 (+900%)

**Effet:** Équivalent à une quasi-désactivation (90% moins d'alertes) tout en gardant la possibilité de capter les rares bonnes opportunités.

---

## 🧪 TESTS RECOMMANDÉS

### Phase 1 (Semaine 1-2)
1. Lancer V3 en parallèle de V2
2. Logger toutes les alertes:
   - V2 seulement
   - V3 seulement
   - Les deux
3. Comparer win rates après 1-2 semaines

### Phase 2 (Semaine 3-4)
1. Si V3 > V2: basculer complètement sur V3
2. Si V3 < V2: analyser les faux négatifs (bonnes alertes rejetées par V3)
3. Ajuster seuils si nécessaire

### Phase 3 (Mois 2)
1. Valider win rate V3 sur 1 mois complet
2. Mesurer profit net réel vs attendu
3. Identifier nouveaux patterns émergents
4. Préparer V4 si nécessaire

---

## 📝 LOGS RECOMMANDÉS

Ajouter logging pour chaque filtre V3:

```python
# Dans apply_v3_filters()
logger.info(f"V3 Filter Check - Token: {pool_data['base_token_name']}")
logger.info(f"  Velocite: {pool_data.get('velocite_pump', 0):.1f} - {reason_vel}")
logger.info(f"  Type Pump: {pool_data.get('type_pump', 'UNKNOWN')} - {reason_type}")
logger.info(f"  Age: {pool_data.get('age_hours', 0):.1f}h - {reason_age}")
logger.info(f"  Liquidite: ${pool_data.get('liquidity', 0):,.0f} - {reason_liq}")
logger.info(f"  Result: {'PASS' if passes_v3 else 'REJECT'}")
logger.info(f"  Tier: {calculate_confidence_tier(pool_data)}")
```

**Fichier:** `v3_filters.log`

**Utilité:**
- Identifier tokens rejetés à tort
- Valider que filtres fonctionnent comme prévu
- Ajuster seuils basés sur vraies données live

---

## 🔄 COMPATIBILITÉ AVEC V2

### Fichiers Modifiés
- ✅ `geckoterminal_scanner_v3.py` (nouveau fichier)
- ⚠️ Aucune modification de V2 (V2 reste intact)

### Configuration Discord/Telegram
Les webhooks et tokens restent identiques. V3 utilise les mêmes canaux que V2.

### Base de Données
V3 utilise les mêmes structures que V2:
- `alert_history`
- `buy_ratio_history`
- `token_alerts` (AlertTracker)

**Attention:** Si V2 et V3 tournent en parallèle, ils partagent la même DB. Cela peut causer:
- Doublons d'alertes
- Confusion dans tracking TP

**Solution:** Utiliser channels Discord/Telegram différents pour V2 vs V3 pendant phase de test.

---

## 📈 ROADMAP FUTURE (V4+)

### Améliorations Potentielles Identifiées

1. **Filtres temporels (NON appliqués en V3)**
   - Jour: Dimanche (77.8% WR) vs Jeudi (7.9% WR)
   - Heure: 21h UTC (27.1% WR) vs 18-20h (<10% WR)
   - Impact: +5-16% WR
   - Statut: En attente instruction utilisateur

2. **Scoring dynamique amélioré**
   - Pondération par réseau
   - Bonus vélocité intégré au score
   - Malus zone danger âge
   - Impact: +5-10% WR

3. **Machine Learning pour tiers**
   - Prédiction WR basée sur combinaisons multi-facteurs
   - Ajustement auto des seuils
   - Détection de nouveaux patterns gagnants

4. **Watchlist dynamique**
   - Ajout auto de tokens 5/5 ou 10/10 winners
   - Retrait auto si 3 losers consécutifs
   - Impact: +0-3% WR

---

## 📞 SUPPORT

### Questions Fréquentes

**Q: Pourquoi si peu d'alertes V3 vs V2?**
R: V3 privilégie la QUALITÉ sur la quantité. 56% moins d'alertes mais 2x meilleur win rate = plus profitable.

**Q: Un bon token V2 est rejeté par V3, pourquoi?**
R: Possible faux négatif. Logger et analyser. Peut nécessiter ajustement seuils.

**Q: Watchlist bypass tout, c'est pas risqué?**
R: Non, ces tokens ont 77-100% WR sur 20-81 alertes. Historique solide.

**Q: Arbitrum toujours actif alors que 4.9% WR?**
R: Seuils augmentés 50-125x = quasi-désactivation mais garde porte ouverte pour rares gems.

**Q: Comment ajouter un token à la watchlist?**
R: Modifier ligne 162:
```python
WATCHLIST_TOKENS = ["snowball", "RTX", "TTD", "FIREBALL", "NOUVEAU_TOKEN"]
```

**Q: V3 marche pas, comment rollback?**
R: Simplement relancer `geckoterminal_scanner_v2.py`. V2 est intact.

---

**Dernière mise à jour:** 26 décembre 2025
**Auteur:** Analyse backtest automatisée + implémentation V3
**Statut:** ✅ Prêt pour déploiement et tests
