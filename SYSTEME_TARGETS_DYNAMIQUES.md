# 🎯 SYSTÈME DE TARGETS DYNAMIQUES (TP/SL/TS)

## Recalcul Automatique à Chaque Alerte

---

## 📊 PRINCIPE GÉNÉRAL

### ⚠️ RÈGLE FONDAMENTALE

**Les targets (TP1/TP2/TP3/SL/TS) sont RECALCULÉS à chaque nouvelle alerte!**

Pourquoi?
- L'évolution du token révèle sa vraie nature
- Conditions changent (liquidité, volume, momentum)
- Alertes multiples = performance confirmée = ajuster targets
- Conditions dégradées = réduire exposition rapidement

---

## 🔧 FACTEURS D'AJUSTEMENT

### 1. **BASE (selon réseau)**

Gains moyens identifiés par l'analyse:

| Réseau   | Gain Moyen | TP1 Base | TP2 Base | TP3 Base |
|----------|------------|----------|----------|----------|
| ETH      | +59.1%     | 15%      | 40%      | 80%      |
| BSC      | +27.0%     | 10%      | 25%      | 50%      |
| BASE     | +16.5%     | 8%       | 18%      | 35%      |
| SOLANA   | +13.3%     | 7%       | 15%      | 30%      |
| ARBITRUM | +13.2%     | 5%       | 12%      | 20%      |

### 2. **MULTIPLICATEURS (conditions actuelles)**

#### Score (qualité signal)
```
Score ≥95:  Targets × 1.3  (+30%)
Score ≥85:  Targets × 1.2  (+20%)
Score ≥75:  Targets × 1.1  (+10%)
Score <60:  Targets × 0.8  (-20%)
```

#### Liquidité (sécurité)
```
SOLANA:
  Liq ≥200K:  Targets × 1.15  (+15%)
  Liq <100K:  Targets × 0.9   (-10%), SL -8%

AUTRES:
  Liq ≥500K:  Targets × 1.2   (+20%)
  Liq <100K:  Targets × 0.85  (-15%), SL -8%
```

#### Volume/Liquidité (momentum)
```
Vol/Liq >500%:  Targets × 1.25  (+25%)
Vol/Liq >200%:  Targets × 1.1   (+10%)
Vol/Liq <50%:   Targets × 0.9   (-10%)
```

#### Accélération
```
Accel ≥6x:  Targets × 1.2  (+20%)
Accel ≥4x:  Targets × 1.1  (+10%)
Accel <1x:  Targets × 0.95 (-5%)
```

#### Freshness
```
<5min:   Targets × 1.15  (+15%)
<30min:  Targets × 1.05  (+5%)
>6h:     Targets × 0.9   (-10%)
```

### 3. **ÉVOLUTION (alertes multiples)**

#### Prix entre alertes
```
Prix HAUSSE:  Targets × 1.3  (+30%) 🚀
Prix STABLE:  Targets × 1.1  (+10%)
Prix BAISSE:  Targets × 0.85 (-15%), SL -7% ⚠️
```

#### Liquidité entre alertes
```
Liq HAUSSE:  Targets × 1.2  (+20%) ✅
Liq BAISSE:  Targets × 0.8  (-20%), SL -7% 🚨
```

#### Volume entre alertes
```
Vol HAUSSE:  Targets × 1.15 (+15%)
Vol BAISSE:  Targets × 0.9  (-10%)
```

#### Nombre d'alertes
```
×10+ alertes:  Targets × 1.4  (+40%) 🔥🔥🔥
×5+ alertes:   Targets × 1.25 (+25%) 🔥🔥
×2+ alertes:   Targets × 1.15 (+15%) 🔥
```

---

## 📈 EXEMPLES CONCRETS

### Exemple 1: SOLANA - Première Alerte (Zone Optimale)

**Conditions:**
```
Réseau:      SOLANA
Entry:       $0.00045
Liquidité:   $180K
Volume 24h:  $2.5M
Score:       95
Age:         3 minutes
Accélération: 6.0x
Alertes:     ×1 (première)
```

**Calcul:**
```
Base TP1 SOLANA: 7%

Multiplicateurs:
├─ Score 95:        × 1.3  (+30%)
├─ Vol/Liq 1389%:   × 1.25 (+25%)
├─ Accel 6x:        × 1.2  (+20%)
└─ <5min:           × 1.15 (+15%)

Multiplicateur total: 2.24x
TP1 final: 7% × 2.24 = 15.7%
```

**Targets Finaux:**
```
Entry:  $0.00045
SL:     $0.000405  (-10%)
TP1:    $0.000521  (+15.7%) → Exit 50%
TP2:    $0.000601  (+33.6%) → Exit 30%
TP3:    $0.000753  (+67.3%) → Exit 20%
Trail:  -5% après TP1
```

**Position Sizing:**
```
Score 95 + SOLANA zone optimale = 10% capital (MAX)
```

---

### Exemple 2: SOLANA - ×5 Alertes (Très Bullish)

**Conditions:**
```
Réseau:      SOLANA
Entry:       $0.00052 (était $0.00045 à première alerte)
Liquidité:   $216K (+20% depuis première)
Volume 24h:  $3.5M (+40%)
Score:       98
Age:         45 minutes
Accélération: 6.0x
Alertes:     ×5
```

**Évolution détectée:**
```
Prix:        +15% 🚀
Liquidité:   +20% ✅
Volume:      +40% 📈
```

**Calcul:**
```
Base TP1 SOLANA: 7%

Multiplicateurs:
├─ Score 98:          × 1.3  (+30%)
├─ Liq >200K:         × 1.15 (+15%)
├─ Vol/Liq 1620%:     × 1.25 (+25%)
├─ Accel 6x:          × 1.2  (+20%)
├─ Prix HAUSSE:       × 1.3  (+30%)
├─ Liq HAUSSE:        × 1.2  (+20%)
├─ Vol HAUSSE:        × 1.15 (+15%)
└─ ×5 alertes:        × 1.25 (+25%)

Multiplicateur total: 5.03x
TP1 final: 7% × 5.03 = 35.2%
```

**Targets Finaux:**
```
Entry:  $0.00052
SL:     $0.000468  (-10%)
TP1:    $0.000703  (+35.2%) → Exit 30% (hold plus)
TP2:    $0.000912  (+75.4%) → Exit 40%
TP3:    $0.001304  (+150.9%) → Exit 30%
Trail:  -7% après TP2 (large, laisser respirer)
```

**Répartition Exits Ajustée:**
```
Très bullish → Hold plus longtemps
TP1: 30% (au lieu de 50%)
TP2: 40% (au lieu de 30%)
TP3: 30% (au lieu de 20%)
```

**Position Sizing:**
```
×5 alertes + hausse confirmée = 10% capital (MAX)
```

---

### Exemple 3: BSC - Conditions Dégradées

**Conditions:**
```
Réseau:      BSC
Entry:       $0.00076 (était $0.00080 à première)
Liquidité:   $150K (-25% depuis première) 🚨
Volume 24h:  $400K (-20%)
Score:       75
Age:         30 minutes
Accélération: 0.8x
Alertes:     ×3
```

**Évolution détectée:**
```
Prix:        -5% ⚠️
Liquidité:   -25% 🚨
Volume:      -20% 📉
```

**Calcul:**
```
Base TP1 BSC: 10%

Multiplicateurs:
├─ Score 75:          × 1.1  (+10%)
├─ Vol/Liq 267%:      × 1.1  (+10%)
├─ Accel <1x:         × 0.95 (-5%)
├─ Prix BAISSE:       × 0.85 (-15%)
├─ Liq BAISSE:        × 0.8  (-20%)
├─ Vol BAISSE:        × 0.9  (-10%)
└─ ×3 alertes:        × 1.15 (+15%)

Multiplicateur total: 0.81x
TP1 final: 10% × 0.81 = 8.1%
```

**Targets Finaux:**
```
Entry:  $0.00076
SL:     $0.000707  (-7%) ⚠️ Plus serré!
TP1:    $0.000821  (+8.1%) → Exit 70% (sortir vite!)
TP2:    $0.000914  (+20.2%) → Exit 20%
TP3:    $0.001067  (+40.5%) → Exit 10%
Trail:  -3% après TP1 (très serré)
```

**Répartition Exits Ajustée:**
```
Conditions dégradées → Exit rapide
TP1: 70% (au lieu de 50%)
TP2: 20% (au lieu de 30%)
TP3: 10% (au lieu de 20%)
```

**Position Sizing:**
```
Conditions dégradées → Réduction
Base (5%) × 0.7 (pénalité liq/prix baisse) = 3.5%
Arrondi à 4.2% avec ×3 alertes
```

---

## 🎯 RÈGLES DE RECALCUL

### À Chaque Nouvelle Alerte:

1. **Analyser l'évolution**
   ```python
   from dynamic_targets_calculator import calculate_dynamic_targets

   # Récupérer alertes précédentes pour ce token
   previous_alerts = get_token_history(pool_address)

   # Calculer nouveaux targets
   targets = calculate_dynamic_targets(
       current_alert,
       previous_alerts
   )
   ```

2. **Comparer avec targets précédents**
   - Si targets augmentent = bullish confirmé ✅
   - Si targets diminuent = conditions se dégradent ⚠️

3. **Ajuster position ouverte**
   - Nouveaux targets remplacent les anciens
   - Trail stop recalculé
   - Répartition exits mise à jour

---

## 🛡️ PROTECTION (SL/TS)

### Stop Loss (SL)

**Standard:** -10%

**Ajustements:**
```
Liquidité <100K:          -8% (plus serré)
Liquidité BAISSE:         -7% (très serré)
Prix BAISSE:              -7% (très serré)
Liq BAISSE + Prix BAISSE: -7% (danger!)
```

**Règle absolue:** NON NÉGOCIABLE - Exit immédiat si touché

### Trail Stop (TS)

**Standard:** -5% après TP1

**Ajustements:**
```
Liquidité <100K:                        -3% (serré)
Liq BAISSE:                            -3% (serré)
×5+ alertes + Prix HAUSSE + Liq HAUSSE: -7% (large)
  → Activation: Après TP2
```

**Objectif:**
- Serré = protéger gains rapidement si risque
- Large = laisser respirer le pump si très bullish

---

## 💰 POSITION SIZING DYNAMIQUE

### Base
```
Standard: 5% capital
```

### Ajustements Score
```
Score ≥95:  10% capital (MAX)
Score ≥85:  7% capital
Score <70:  3% capital (prudent)
```

### Ajustements Alertes Multiples
```
×5+ alertes:  Position × 1.5 (max 10%)
×2+ alertes:  Position × 1.2 (max 10%)
```

### Pénalités Conditions Dégradées
```
Liq BAISSE ou Prix BAISSE:  Position × 0.7
```

### Cap Absolu
```
Maximum: 10% capital par position
Maximum simultané: 3-5 positions
```

---

## 📋 WORKFLOW PRATIQUE

### Nouvelle Alerte Arrive

```
1. Récupérer historique token
   └─ SELECT * FROM alerts WHERE pool_address = ?

2. Calculer targets dynamiques
   └─ python dynamic_targets_calculator.py

3. Analyser le raisonnement
   ├─ Multiplicateur total
   ├─ Facteurs positifs/négatifs
   └─ Niveau de risque

4. Décision

   SI première alerte:
   ├─ Targets = Base × Conditions actuelles
   └─ Entry selon checklist

   SI alerte multiple:
   ├─ Comparer évolution (prix, liq, vol)
   ├─ Targets ajustés selon tendances
   └─ Décision:
       ├─ HAUSSE confirmée → Augmenter position
       ├─ STABLE → Maintenir
       └─ BAISSE → Réduire ou EXIT

5. Appliquer nouveaux targets
   ├─ Remplacer anciens TP/SL/TS
   ├─ Ajuster répartition exits si besoin
   └─ Mettre ordres
```

---

## 🚨 SIGNAUX D'ALARME

### EXIT Immédiat Si:

1. **Liquidité baisse >20%** entre alertes
   ```
   Action: EXIT total immédiat
   Raison: Risque rug pull
   ```

2. **Prix baisse ET Liquidité baisse**
   ```
   Action: EXIT 70% minimum
   Raison: Double signal négatif
   ```

3. **Stop Loss touché**
   ```
   Action: EXIT 100% automatique
   Raison: Protection capital
   ```

4. **Aucune nouvelle alerte 6h+**
   ```
   Action: EXIT progressif
   Raison: Momentum perdu
   ```

---

## 📊 INTÉGRATION AVEC AUTO-SCORING

### Combiner les 2 Systèmes

```python
from auto_score_signal import calculate_signal_score
from dynamic_targets_calculator import calculate_dynamic_targets

# 1. Scorer le signal
score, breakdown, rec = calculate_signal_score(alert)

if score >= 70:  # Signal acceptable
    # 2. Calculer targets dynamiques
    targets = calculate_dynamic_targets(alert, previous_alerts)

    # 3. Décision finale
    print(f"Signal Score: {score}/100")
    print(f"Action: {rec['action']}")
    print(f"Position: {targets['position_size']:.1f}%")
    print(f"\nTargets:")
    print(f"TP1: {targets['tp1']['price']} (+{targets['tp1']['percent']:.1f}%)")
    print(f"TP2: {targets['tp2']['price']} (+{targets['tp2']['percent']:.1f}%)")
    print(f"TP3: {targets['tp3']['price']} (+{targets['tp3']['percent']:.1f}%)")
    print(f"SL:  {targets['stop_loss']['price']} ({targets['stop_loss']['percent']}%)")
```

---

## ✅ CONCLUSION

### Pattern Optimal

```
🎯 SOLANA + Vol 1M-5M + Liq <200K + ×5+ alertes + Prix HAUSSE
   = Targets × 5x
   = TP3 +150%
   = Position 10%
   = Hold plus longtemps (30/40/30)
```

### 3 Règles d'Or

1. **RECALCULER** targets à chaque alerte
2. **ADAPTER** selon évolution réelle
3. **PROTÉGER** avec SL/TS ajustés

### Fichiers Associés

- `dynamic_targets_calculator.py` - Calcul automatique
- `STRATEGIE_TRADING_COMPLETE.md` - Stratégie globale
- `README_ANALYSES.md` - Index complet

---

**💎 Système 100% basé sur analyse 4252 alertes réelles**

**🎯 Targets adaptés = Maximiser gains, Minimiser risques**
