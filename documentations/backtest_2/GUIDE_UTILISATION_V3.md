# 🚀 GUIDE RAPIDE - Scanner V3

> **Comment utiliser la version 3 optimisée du scanner GeckoTerminal**

---

## 📁 FICHIERS

- **V2 (actuel):** `geckoterminal_scanner_v2.py` - Version originale (18.9% WR)
- **V3 (nouveau):** `geckoterminal_scanner_v3.py` - Version optimisée (35-50% WR attendu)

---

## 🚀 DÉMARRAGE RAPIDE

### Option 1: Tester V3 en parallèle (RECOMMANDÉ)

```bash
# Terminal 1 - V2 continue de tourner
python geckoterminal_scanner_v2.py

# Terminal 2 - V3 en test
python geckoterminal_scanner_v3.py
```

**Avantages:**
- Comparer les performances V2 vs V3
- Pas de risque si V3 a des bugs
- Mesurer l'amélioration réelle

**Inconvénient:**
- Doublons d'alertes possibles (même token détecté par V2 et V3)

---

### Option 2: Basculer directement sur V3

```bash
# Arrêter V2
# Ctrl+C sur le terminal V2

# Lancer V3
python geckoterminal_scanner_v3.py
```

**Avantages:**
- Pas de doublons
- Plus simple

**Inconvénient:**
- Pas de comparaison directe
- Si V3 a un bug, pas de backup actif

---

## 🎯 CE QUI A CHANGÉ EN V3

### 1. Filtres Automatiques Stricts

**Vélocité minimum: 5%/h**
- V2: Acceptait tout
- V3: Rejette si vélocité < 5%/h
- Impact: Élimine les pumps trop lents (73% des échecs)

**Type pump**
- V2: Ignorait le type
- V3: Rejette "LENT", "STAGNANT", "STABLE"
- Accepte: "RAPIDE", "TRES_RAPIDE", "PARABOLIQUE"

**Âge optimal: 2-3 jours**
- V2: Acceptait 0h-∞
- V3: Zone danger 12-24h (8.6% WR), optimal 48-72h (36.1% WR)

**Liquidité par zones**
- V2: Seuils fixes
- V3: Zones optimales (ex: ETH $100K-$200K = 55.6% WR!)

---

### 2. Watchlist Automatique

Tokens qui BYPASS tous les filtres (historique 77-100% WR):
- snowball (Solana): 100% WR sur 81 alertes
- RTX (Arbitrum): 100% WR sur 20 alertes
- TTD (Arbitrum): 77.8% WR sur 45 alertes
- FIREBALL (Solana): 77.4% WR sur 31 alertes

**Comportement:** Alerte IMMÉDIATE dès détection, aucun filtre appliqué.

---

### 3. Système de Tiers (Confiance)

Chaque alerte affiche un tier:

| Tier | Symbole | Win Rate Attendu | Action Recommandée |
|------|---------|------------------|-------------------|
| ULTRA_HIGH | 💎💎💎 | 77-100% | ENTRER IMMÉDIATEMENT (watchlist) |
| HIGH | 💎💎 | 35-50% | Prendre la plupart |
| MEDIUM | 💎 | 25-30% | Prendre si conditions bonnes |
| LOW | ⚪ | 15-20% | Prudence, petit montant |
| VERY_LOW | ⚫ | <15% | Éviter ou ignorer |

---

### 4. Seuils Réseau Optimisés

**Arbitrum (anciennement catastrophique: 4.9% WR)**
- V2: $2K liq, $400 vol
- V3: $100K liq, $50K vol (+50-125x!)
- Effet: 90% moins d'alertes Arbitrum (gardé seulement le top)

**Base (anciennement faible: 12.8% WR)**
- V2: $100K liq, $50K vol
- V3: $300K liq, $1M vol (+3-20x)
- Effet: 60% moins d'alertes Base

**Solana, ETH, BSC**
- Zones optimales définies
- Max liquidity ajouté (gros tokens déjà découverts = moins bon)

---

## 📊 ATTENTES RÉALISTES

### Nombre d'Alertes

**V2:** 10-20 alertes/jour
**V3:** 5-10 alertes/jour (56% moins)

**Interprétation:** C'est NORMAL. Moins d'alertes = plus de qualité.

---

### Win Rate Attendu

| Version | Win Rate | Profit Net (100 trades) |
|---------|----------|------------------------|
| V2 | 18.9% | +32.6% |
| V3 | 35-50% | +90-140% |

**Délai validation:** 1-2 semaines minimum pour avoir assez de trades.

---

## 🔍 COMPRENDRE LES ALERTES V3

### Exemple d'Alerte ULTRA_HIGH

```
🆕 Nouvelle opportunité sur le token snowball

💎 snowball/SOL
⛓️ Blockchain: Solana

🎯 SCORE: 78/100 ⭐️⭐️⭐️ TRÈS BON
   Base: 65 | Momentum: +13
📊 Confiance: 88% (fiabilité données)
🎖️ TIER V3: 💎💎💎 ULTRA_HIGH (Watchlist - 77-100% WR historique)
   V3 Checks: Watchlist token - bypass vélocité | Watchlist token - bypass type pump | Watchlist token - bypass âge

[Reste de l'alerte...]
```

**Action:** ENTRER IMMÉDIATEMENT. Watchlist = 100% WR historique sur 81 alertes!

---

### Exemple d'Alerte HIGH

```
🆕 Nouvelle opportunité sur le token PEPE2.0

💎 PEPE2.0/WETH
⛓️ Blockchain: Ethereum

🎯 SCORE: 82/100 ⭐️⭐️⭐️⭐️ EXCELLENT
   Base: 68 | Momentum: +14
📊 Confiance: 90% (fiabilité données)
🎖️ TIER V3: 💎💎 HIGH (35-50% WR attendu)
   V3 Checks: Vélocité EXCELLENTE: 52.3 (>50 = pattern gagnant) | Type pump OK: TRES_RAPIDE | Âge OPTIMAL: 63.2h (2-3 jours = 36.1% WR!)

[Reste de l'alerte...]
```

**Action:** Très bon signal. 4/5 conditions optimales remplies.

---

### Exemple d'Alerte MEDIUM

```
🆕 Nouvelle opportunité sur le token SHIB2

💎 SHIB2/USDT
⛓️ Blockchain: BSC

🎯 SCORE: 67/100 ⭐️⭐️ BON
   Base: 58 | Momentum: +9
📊 Confiance: 75% (fiabilité données)
🎖️ TIER V3: 💎 MEDIUM (25-30% WR attendu)
   V3 Checks: Vélocité OK: 18.5 | Type pump OK: RAPIDE | Âge OK: 12.3h

[Reste de l'alerte...]
```

**Action:** Signal correct mais pas optimal. Âge 12h = juste sorti de zone danger. Prendre si bon contexte.

---

## ⚙️ PERSONNALISATION V3

### Ajouter un Token à la Watchlist

**Fichier:** `geckoterminal_scanner_v3.py`
**Ligne:** 162

```python
# Avant
WATCHLIST_TOKENS = ["snowball", "RTX", "TTD", "FIREBALL"]

# Après (exemple: ajouter BONK)
WATCHLIST_TOKENS = ["snowball", "RTX", "TTD", "FIREBALL", "BONK"]
```

**Effet:** BONK recevra tier ULTRA_HIGH et bypass tous filtres.

---

### Ajuster Vélocité Minimum

**Fichier:** `geckoterminal_scanner_v3.py`
**Ligne:** 131

```python
# Actuel (conservateur)
MIN_VELOCITE_PUMP = 5.0

# Plus strict (moins d'alertes, meilleure qualité)
MIN_VELOCITE_PUMP = 10.0

# Plus permissif (plus d'alertes, qualité baisse)
MIN_VELOCITE_PUMP = 3.0
```

**Recommandation:** Garder 5.0 basé sur backtest. Tester sur 1-2 semaines avant modifier.

---

### Désactiver Complètement Arbitrum

Si vous voulez 0 alerte Arbitrum au lieu de seulement 90% moins:

**Fichier:** `geckoterminal_scanner_v3.py`
**Ligne:** ~95

```python
# Actuel (seuils très élevés)
"arbitrum": {
    "min_liquidity": 100000,
    "max_liquidity": 1000000,
    "min_volume": 50000,
    "min_txns": 100
},

# Pour désactiver (ajouter enabled: false)
"arbitrum": {
    "enabled": False,  # AJOUTER CETTE LIGNE
    "min_liquidity": 100000,
    "max_liquidity": 1000000,
    "min_volume": 50000,
    "min_txns": 100
},
```

Puis modifier le code de scan pour vérifier `enabled` (requiert modification code).

**Alternative simple:** Mettre des seuils impossibles:
```python
"arbitrum": {
    "min_liquidity": 999999999,  # 1 milliard (aucun token n'atteindra)
    "max_liquidity": 1000000000,
    "min_volume": 999999999,
    "min_txns": 99999
},
```

---

## 📈 SUIVI PERFORMANCE V3

### Métriques à Suivre

**Journalier:**
- Nombre d'alertes V3
- Nombre d'alertes par tier (ULTRA/HIGH/MEDIUM/LOW)
- Nombre d'alertes rejetées (logs)

**Hebdomadaire:**
- Win rate réel vs attendu
- ROI moyen par tier
- Tokens watchlist: maintiennent 100% WR?

**Mensuel:**
- Win rate global V3 vs V2
- Profit net V3 vs V2
- Nouveaux patterns émergents

---

### Logs Utiles

V3 log les rejets dans la console. Chercher:

```
[V3 REJECT] Vélocité trop faible: 3.2 < 5.0
[V3 REJECT] Type pump rejeté: LENT (73% des échecs)
[V3 REJECT] ZONE DANGER âge: 18.5h (12-24h = 8.6% WR!)
```

**Utilité:** Voir quels tokens sont filtrés et pourquoi.

---

## 🚨 PROBLÈMES FRÉQUENTS

### "Trop peu d'alertes V3"

**Normal:** V3 filtre 56% des alertes V2. C'est voulu.

**Vérifier:**
- Y a-t-il des alertes ULTRA_HIGH ou HIGH? (ce sont les meilleures)
- Comparer win rate V3 vs V2 après 1 semaine

**Solution:** Si vraiment trop peu, baisser MIN_VELOCITE_PUMP de 5.0 à 3.0.

---

### "Un bon token V2 est rejeté par V3"

**Possible:** V3 peut rejeter quelques bons tokens (faux négatifs).

**Analyser:**
1. Regarder le log de rejet
2. Vérifier quelle condition a échoué
3. Est-ce que c'était vraiment un bon token? (TP1 atteint?)

**Solution:** Si pattern récurrent, ajuster le seuil concerné.

---

### "Watchlist token pas détecté"

**Vérifier:**
1. Le nom exact du token dans WATCHLIST_TOKENS
2. Le matching est insensible à la casse (snowball = SNOWBALL = Snowball)
3. Le matching est partiel ("snowball" match "snowball/SOL", "Snowball Token", etc.)

**Debug:**
```python
# Ligne 1026 dans check_watchlist_token()
print(f"DEBUG: Checking {token_name} / {token_symbol} against watchlist")
```

---

### "V3 plante / erreur"

**Erreur fréquente:** Données manquantes (velocite_pump, type_pump, etc.)

**Solution:** V3 calcule ces valeurs dans `parse_pool_data()`. Si erreur, vérifier que:
1. `price_change_1h` existe dans les données API
2. Le pool a bien toutes les données requises

**Rollback:** En cas de problème critique, relancer V2:
```bash
# Arrêter V3
Ctrl+C

# Relancer V2
python geckoterminal_scanner_v2.py
```

---

## 📚 DOCUMENTATION COMPLÈTE

Pour plus de détails:

- **CHANGELOG_V3.md** - Tous les changements techniques ligne par ligne
- **AMELIORATIONS_BOT.md** - Liste prioritaire des améliorations avec code
- **RAPPORT_SIMPLE.md** - Analyse backtest détaillée (700+ lignes)
- **ENSEIGNEMENTS_CLES.md** - Top 10 découvertes game-changing
- **BACKTEST_PHASE_2_RAPPORT_COMPLET.pdf** - Rapport professionnel 15 pages

Tous ces fichiers sont dans: `documentations/backtest_2/`

---

## 🎯 RÉSUMÉ: QUAND UTILISER V3?

### ✅ Utiliser V3 si vous voulez:
- Meilleur win rate (35-50% vs 18.9%)
- Moins d'alertes mais plus qualitatives
- Filtrage automatique basé sur 3,261 alertes historiques
- Système de tiers (savoir quelle alerte est la meilleure)
- Watchlist auto pour tokens "money printer"

### ⚠️ Rester sur V2 si vous voulez:
- Plus d'alertes (quantité > qualité)
- Ne pas manquer de potentiels gems (même faible WR)
- Ne pas faire confiance aux filtres automatiques
- Décider manuellement pour chaque alerte

---

## 📞 BESOIN D'AIDE?

1. Lire les fichiers documentation dans `documentations/backtest_2/`
2. Chercher dans CHANGELOG_V3.md si le problème est connu
3. Vérifier les logs console pour les messages [V3 REJECT]
4. Comparer comportement V2 vs V3 côte à côte

---

**Date:** 26 décembre 2025
**Version:** 3.0.0
**Statut:** ✅ Prêt pour utilisation
