# 🚀 LISTE DES AMÉLIORATIONS À FAIRE SUR LE BOT

> **Objectif:** Passer de 18.9% à 35-45% de win rate
> **Basé sur:** Analyse de 3,261 alertes historiques

---

## ⛔ PRIORITÉ 1 - URGENT (Impact immédiat)

### 1. DÉSACTIVER ARBITRUM
**Problème actuel:**
- Win rate catastrophique: 4.9% (24/488 alertes)
- ROI moyen: +14% (insuffisant)
- Seuils actuels trop bas: $2K liquidity, $400 volume, 10 txns

**Action:**
```python
# Dans geckoterminal_scanner_v2.py, ligne 49-97
NETWORK_THRESHOLDS = {
    "arbitrum": {"enabled": False},  # DÉSACTIVER
    # OU augmenter drastiquement:
    "arbitrum": {
        "min_liquidity": 100000,  # $2K → $100K
        "min_volume": 50000,       # $400 → $50K
        "min_txns": 100            # 10 → 100
    }
}
```

**Impact attendu:** Élimination de 488 alertes perdantes → +2-3% de win rate global

---

### 2. OPTIMISER BASE
**Problème actuel:**
- Win rate: 12.8% (27/211 alertes) - sous la moyenne
- Seuils actuels: $100K liquidity, $50K volume, 100 txns

**Action:**
```python
NETWORK_THRESHOLDS = {
    "base": {
        "min_liquidity": 300000,   # $100K → $300K
        "min_volume": 1000000,     # $50K → $1M
        "min_txns": 150            # 100 → 150
    }
}
```

**Impact attendu:** Réduction de 211 → ~80 alertes, mais win rate de 12.8% → 25%+

---

### 3. AJOUTER FILTRE VÉLOCITÉ MINIMUM
**Découverte clé:**
- Winners ont vélocité moyenne: 7.99
- Losers ont vélocité moyenne: 3.05
- Impact: +133% (facteur #1 de succès!)

**Action:**
```python
# Dans geckoterminal_scanner_v2.py, après calcul du score
def filter_by_velocity(alert_data):
    velocite = alert_data.get('velocite_pump', 0)

    # Filtre STRICT
    if velocite < 5:
        return False  # Rejeter

    return True
```

**Impact attendu:** +8-12% de win rate en éliminant les pumps trop lents

---

### 4. FILTRER PAR TYPE DE PUMP
**Découverte:**
- 73% des losers = type "LENT"
- Winners = majoritairement RAPIDE, TRES_RAPIDE, PARABOLIQUE

**Action:**
```python
# Dans geckoterminal_scanner_v2.py
ALLOWED_PUMP_TYPES = ["RAPIDE", "TRES_RAPIDE", "PARABOLIQUE"]

def filter_by_pump_type(alert_data):
    type_pump = alert_data.get('type_pump', '')

    if type_pump not in ALLOWED_PUMP_TYPES:
        return False  # Rejeter LENT, STAGNANT, etc.

    return True
```

**Impact attendu:** +5-8% de win rate

---

## 🔥 PRIORITÉ 2 - IMPORTANT (Amélioration significative)

### 5. FILTRER PAR ÂGE DU TOKEN
**Découverte contre-intuitive:**
- Meilleur timing: 2-3 jours (36.1% win rate, +234% ROI)
- Pire timing: 12-24h (8.6% win rate)
- 0-30min: Seulement 23.8% (risqué avec -34% drawdown)

**Action:**
```python
def filter_by_age(alert_data):
    age_hours = alert_data.get('age_hours', 0)

    # Zone DANGER à éviter
    if 12 <= age_hours < 24:
        return False  # PIRE moment

    # Préférer 2-3 jours
    if 48 <= age_hours <= 72:
        # Bonus de priorité
        alert_data['age_bonus'] = 1.5

    # Accepter aussi 3-6h et 1-2 jours
    if age_hours >= 3:
        return True

    # 0-3h: accepter seulement si vélocité exceptionnelle
    if alert_data.get('velocite_pump', 0) > 50:
        return True

    return False  # Rejeter <3h avec faible vélocité
```

**Impact attendu:** +10-15% de win rate

---

### 6. SYSTÈME DE TIERS (Confiance par niveaux)
**Principe:** Classer les alertes par niveau de confiance

**Action:**
```python
def calculate_confidence_tier(alert_data):
    """
    Retourne: 'HIGH', 'MEDIUM', 'LOW', ou None (rejeter)
    """
    score = alert_data.get('score', 0)
    velocite = alert_data.get('velocite_pump', 0)
    type_pump = alert_data.get('type_pump', '')
    network = alert_data.get('network', '')
    age_hours = alert_data.get('age_hours', 0)
    liquidity = alert_data.get('liquidity', 0)

    # HIGH CONFIDENCE (attendu: 35-45% WR)
    high_conditions = [
        network in ['eth', 'solana'],
        48 <= age_hours <= 72,  # 2-3 jours
        velocite > 50,
        type_pump == 'PARABOLIQUE',
        100000 <= liquidity <= 300000
    ]

    if sum(high_conditions) >= 4:  # 4 sur 5 critères
        return 'HIGH'

    # MEDIUM CONFIDENCE (attendu: 25-30% WR)
    medium_conditions = [
        network in ['eth', 'solana', 'bsc'],
        age_hours >= 6,
        velocite > 10,
        type_pump in ['RAPIDE', 'TRES_RAPIDE', 'PARABOLIQUE'],
        liquidity > 50000
    ]

    if sum(medium_conditions) >= 4:
        return 'MEDIUM'

    # LOW CONFIDENCE (attendu: 15-20% WR)
    if velocite >= 5 and type_pump != 'LENT':
        return 'LOW'

    return None  # Rejeter
```

**Utilisation dans l'alerte:**
```python
# Ajouter dans le message Discord/Telegram
tier = calculate_confidence_tier(alert_data)

if tier == 'HIGH':
    message = "🔥🔥🔥 HIGH CONFIDENCE (35-45% WR) 🔥🔥🔥\n" + message
elif tier == 'MEDIUM':
    message = "✅ MEDIUM CONFIDENCE (25-30% WR)\n" + message
elif tier == 'LOW':
    message = "⚠️ LOW CONFIDENCE (15-20% WR)\n" + message
```

**Impact attendu:** Permet aux traders de prioriser, +15-20% WR sur HIGH tier

---

### 7. FILTRER PAR JOUR DE LA SEMAINE
**Découverte:**
- Dimanche: 77.8% WR (!!)
- Lundi: 41.7% WR
- Jeudi: 7.9% WR (pire)

**Action - Option 1 (Conservatrice):**
```python
import datetime

def filter_by_day_of_week(alert_data):
    day = datetime.datetime.now().weekday()  # 0=Lundi, 6=Dimanche

    # Jeudi = éviter complètement
    if day == 3:  # Jeudi
        # Accepter seulement HIGH confidence
        if calculate_confidence_tier(alert_data) != 'HIGH':
            return False

    # Dimanche/Lundi = prendre tout
    if day in [6, 0]:  # Dimanche, Lundi
        alert_data['day_bonus'] = 2.0

    return True
```

**Action - Option 2 (Agressive):**
```python
def filter_by_day_of_week_aggressive(alert_data):
    day = datetime.datetime.now().weekday()

    # Accepter seulement Dimanche, Lundi, Mardi, Vendredi
    if day in [6, 0, 1, 4]:  # Dim, Lun, Mar, Ven
        return True

    # Mer, Jeu, Sam: rejeter sauf HIGH confidence
    if calculate_confidence_tier(alert_data) == 'HIGH':
        return True

    return False
```

**Impact attendu:** +3-5% WR (option 1), +8-12% WR (option 2 mais moins d'alertes)

---

### 8. FILTRER PAR HEURE (UTC)
**Découverte:**
- 21:00 UTC: 27.1% WR (meilleur)
- 16:00-17:00 UTC: 24.3% WR
- 18:00, 20:00, 22:00 UTC: <10% WR

**Action:**
```python
def filter_by_hour():
    hour = datetime.datetime.utcnow().hour

    # Dead zones - rejeter
    if hour in [18, 20, 22, 23, 0, 1, 2, 3, 4, 5]:
        return False

    # Golden hours - bonus
    if hour in [21, 16, 17, 10]:
        return True  # +bonus

    return True  # Accepter autres heures
```

**Impact attendu:** +2-4% WR

---

## ✅ PRIORITÉ 3 - OPTIMISATION (Fine-tuning)

### 9. AJUSTER SEUILS DE LIQUIDITÉ PAR RÉSEAU
**Découverte:**
- Solana: optimal $100K-$200K (43.8% WR)
- ETH: optimal $100K-$200K (55.6% WR!!)
- BSC: optimal $500K-$5M (36-39% WR)

**Action:**
```python
NETWORK_LIQUIDITY_RANGES = {
    "solana": {
        "min": 100000,
        "max": 500000,
        "optimal_min": 100000,
        "optimal_max": 200000
    },
    "eth": {
        "min": 100000,
        "max": 500000,
        "optimal_min": 100000,
        "optimal_max": 200000
    },
    "bsc": {
        "min": 500000,
        "max": 10000000,
        "optimal_min": 500000,
        "optimal_max": 5000000
    }
}

def filter_by_liquidity(alert_data):
    network = alert_data.get('network', '')
    liquidity = alert_data.get('liquidity', 0)

    ranges = NETWORK_LIQUIDITY_RANGES.get(network)
    if not ranges:
        return False

    # Rejeter si hors limites
    if liquidity < ranges['min'] or liquidity > ranges['max']:
        return False

    # Bonus si dans zone optimale
    if ranges['optimal_min'] <= liquidity <= ranges['optimal_max']:
        alert_data['liquidity_bonus'] = 1.3

    return True
```

**Impact attendu:** +3-6% WR

---

### 10. WATCHLIST AUTOMATIQUE (Tokens "Money Printer")
**Découverte:**
- snowball/SOL: 100% WR sur 81 alertes
- RTX/USDT: 100% WR sur 20 alertes
- TTD/USDT: 78% WR sur 45 alertes
- FIREBALL/SOL: 77% WR sur 31 alertes

**Action:**
```python
# Créer nouvelle table dans DB
WATCHLIST_TOKENS = {
    "snowball": {"network": "solana", "wins": 81, "total": 81},
    "RTX": {"network": "arbitrum", "wins": 20, "total": 20},
    "TTD": {"network": "arbitrum", "wins": 35, "total": 45},
    "FIREBALL": {"network": "solana", "wins": 24, "total": 31}
}

def check_watchlist(alert_data):
    token_name = alert_data.get('token_name', '').lower()

    for watch_token, stats in WATCHLIST_TOKENS.items():
        if watch_token.lower() in token_name:
            # AUTO-ACCEPT avec priorité maximale
            alert_data['watchlist_match'] = True
            alert_data['confidence_tier'] = 'ULTRA_HIGH'

            # Message spécial
            win_rate = (stats['wins'] / stats['total']) * 100
            alert_data['special_message'] = f"💎💎💎 WATCHLIST TOKEN: {win_rate:.1f}% WR historique! 💎💎💎"

            return True

    return False
```

**Impact attendu:** Garantit que les meilleurs tokens ne sont jamais ratés

---

### 11. SYSTÈME DE SCORING DYNAMIQUE
**Améliorer le calcul du score actuel:**

**Action:**
```python
def calculate_enhanced_score(alert_data):
    """
    Nouveau scoring qui prend en compte toutes les découvertes
    """
    base_score = alert_data.get('base_score', 50)

    # Facteurs avec leur poids
    velocity_factor = min(alert_data.get('velocite_pump', 0) / 10, 10)  # Max +10

    age_hours = alert_data.get('age_hours', 0)
    age_factor = 0
    if 48 <= age_hours <= 72:
        age_factor = 15  # +15 pour zone optimale
    elif 24 <= age_hours < 48:
        age_factor = 8
    elif 6 <= age_hours < 12:
        age_factor = 3
    elif 12 <= age_hours < 24:
        age_factor = -20  # Pénalité zone danger

    type_pump_factor = 0
    type_pump = alert_data.get('type_pump', '')
    if type_pump == 'PARABOLIQUE':
        type_pump_factor = 12
    elif type_pump == 'TRES_RAPIDE':
        type_pump_factor = 8
    elif type_pump == 'RAPIDE':
        type_pump_factor = 5
    elif type_pump == 'LENT':
        type_pump_factor = -15  # Pénalité

    network_factor = 0
    network = alert_data.get('network', '')
    if network == 'eth':
        network_factor = 10
    elif network == 'solana':
        network_factor = 8
    elif network == 'bsc':
        network_factor = 5
    elif network == 'arbitrum':
        network_factor = -30  # Forte pénalité
    elif network == 'base':
        network_factor = -5

    day_factor = 0
    day = datetime.datetime.now().weekday()
    if day == 6:  # Dimanche
        day_factor = 20
    elif day == 0:  # Lundi
        day_factor = 12
    elif day == 3:  # Jeudi
        day_factor = -12

    hour_factor = 0
    hour = datetime.datetime.utcnow().hour
    if hour == 21:
        hour_factor = 8
    elif hour in [16, 17]:
        hour_factor = 5
    elif hour in [18, 20, 22]:
        hour_factor = -8

    # Score final
    final_score = (
        base_score +
        velocity_factor * 2 +  # Vélocité a le poids le plus important
        age_factor +
        type_pump_factor +
        network_factor +
        day_factor +
        hour_factor
    )

    return max(0, min(100, final_score))  # Entre 0 et 100
```

**Nouveaux seuils:**
- Score < 60: Rejeter
- Score 60-70: LOW confidence
- Score 70-85: MEDIUM confidence
- Score 85+: HIGH confidence

**Impact attendu:** +5-10% WR avec meilleur filtrage

---

## 📊 RÉCAPITULATIF DES AMÉLIORATIONS

| # | Amélioration | Difficulté | Impact WR | Priorité |
|---|-------------|------------|-----------|----------|
| 1 | Désactiver Arbitrum | Facile | +2-3% | ⛔ URGENT |
| 2 | Optimiser Base | Facile | +1-2% | ⛔ URGENT |
| 3 | Filtre vélocité min | Facile | +8-12% | ⛔ URGENT |
| 4 | Filtre type pump | Facile | +5-8% | ⛔ URGENT |
| 5 | Filtre âge token | Moyen | +10-15% | 🔥 IMPORTANT |
| 6 | Système tiers | Moyen | +15-20% | 🔥 IMPORTANT |
| 7 | Filtre jour semaine | Facile | +3-12% | 🔥 IMPORTANT |
| 8 | Filtre heure | Facile | +2-4% | 🔥 IMPORTANT |
| 9 | Liquidité optimale | Moyen | +3-6% | ✅ OPTIMISATION |
| 10 | Watchlist auto | Facile | Garantie | ✅ OPTIMISATION |
| 11 | Scoring dynamique | Difficile | +5-10% | ✅ OPTIMISATION |

**Impact cumulé estimé:** 18.9% → **35-50% de win rate**

---

## 🚀 PLAN D'IMPLÉMENTATION RECOMMANDÉ

### Phase 1 - Quick Wins (1-2h de dev)
1. Désactiver Arbitrum (ou augmenter seuils)
2. Augmenter seuils Base
3. Ajouter filtre vélocité minimum (>5)
4. Ajouter filtre type pump (rejeter LENT)

**→ Impact immédiat: +15-25% WR**

### Phase 2 - Filtres Avancés (3-5h de dev)
5. Implémenter filtre âge token
6. Implémenter filtre jour de semaine
7. Implémenter filtre heure

**→ Impact cumulé: +25-40% WR**

### Phase 3 - Système Intelligent (5-10h de dev)
8. Système de tiers (HIGH/MEDIUM/LOW confidence)
9. Ajuster liquidité par réseau
10. Watchlist automatique
11. Scoring dynamique amélioré

**→ Impact cumulé: +35-50% WR**

---

## 📝 NOTES IMPORTANTES

**À NE PAS FAIRE:**
- ❌ Ne pas trop filtrer: risque de passer de 100 alertes/mois à 5 alertes/mois
- ❌ Ne pas ignorer les alertes LOW confidence: elles peuvent quand même être profitables (15-20% WR)
- ❌ Ne pas modifier plusieurs paramètres en même temps: tester incrementalement

**À FAIRE:**
- ✅ Implémenter progressivement (phase par phase)
- ✅ Logger toutes les alertes rejetées (pour analyse)
- ✅ Garder métriques avant/après chaque changement
- ✅ Tester sur 1-2 semaines avant de valider définitivement
- ✅ Créer un mode "permissif" et un mode "strict" que l'utilisateur peut choisir

**Metrics à suivre:**
- Win rate global
- Win rate par tier (HIGH/MEDIUM/LOW)
- Nombre d'alertes par jour/semaine
- ROI moyen
- Plus gros gain / plus grosse perte
- Losing streaks
