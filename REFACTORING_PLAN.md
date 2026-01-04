# Plan de Refactoring - Scanner V3

## Objectif
Transformer le fichier monolithique `geckoterminal_scanner_v3.py` (3393 lignes) en une architecture modulaire, propre et maintenable.

## Principes
- **Cohérence**: Chaque module a une responsabilité claire
- **Simplicité**: Pas de sur-ingénierie, garder ce qui fonctionne
- **Flexibilité**: Faciliter les évolutions futures
- **Zéro régression**: Tester à chaque étape

---

## Architecture Cible

```
bot-market/
├── core/                          # Logique métier principale
│   ├── __init__.py
│   ├── scanner.py                 # Orchestrateur principal (scan_geckoterminal, main)
│   ├── scoring.py                 # Système de scoring et tiers
│   ├── filters.py                 # Filtres V3 (vélocité, age, type_pump)
│   ├── signals.py                 # Détection de signaux et patterns
│   └── whale_analyzer.py          # Analyse whale activity
│
├── utils/                         # Utilitaires et helpers
│   ├── __init__.py
│   ├── api_client.py              # Appels GeckoTerminal API
│   ├── telegram.py                # Envoi notifications Telegram
│   ├── formatters.py              # Formatage messages et prix
│   └── helpers.py                 # Fonctions utilitaires générales
│
├── data/                          # Gestion données et persistance
│   ├── __init__.py
│   ├── database.py                # Gestion SQLite (AlertTracker intégré)
│   ├── models.py                  # Structures de données (dataclasses)
│   └── cache.py                   # Cooldowns et historiques
│
├── config/                        # Configuration
│   ├── __init__.py
│   ├── settings.py                # Configuration centralisée (seuils, réseaux)
│   └── constants.py               # Constantes globales
│
├── geckoterminal_scanner_v3.py    # Point d'entrée (importe depuis core/)
├── security_checker.py            # Inchangé (déjà modulaire)
├── alert_tracker.py               # À migrer dans data/database.py
└── dashboard_api.py               # Inchangé (frontend/API)
```

---

## Mapping des Fonctions

### 1️⃣ **config/settings.py** (Configuration)
**Lignes 48-270** - Configuration centralisée
- `NETWORKS`, `GECKOTERMINAL_API`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `build_network_thresholds()` (ligne 91)
- `MODE_CONFIGS` (SAFETY, BALANCED, AGGRESSIVE)
- `NETWORK_THRESHOLDS`
- `WATCHLIST_TOKENS`

### 2️⃣ **config/constants.py** (Constantes)
- `COOLDOWN_REGLE_4`, `COOLDOWN_REGLE_5`
- `MAX_LIQUIDITY_THRESHOLD`
- Emojis et formats de messages

### 3️⃣ **utils/helpers.py** (Utilitaires généraux)
- `get_network_display_name()` (ligne 271)
- `log()` (ligne 275)
- `extract_base_token()` (ligne 294)
- `format_price()` (ligne 2242)

### 4️⃣ **utils/telegram.py** (Notifications)
- `send_telegram()` (ligne 278)

### 5️⃣ **utils/api_client.py** (API GeckoTerminal)
- `get_trending_pools()` (ligne 397)
- `get_new_pools()` (ligne 428)
- `get_pool_by_address()` (ligne 462)
- `parse_pool_data()` (ligne 501) - **CRITIQUE: 228 lignes**

### 6️⃣ **utils/formatters.py** (Formatage messages)
- `format_price()` (ligne 2242)
- `generer_alerte_complete()` (ligne 2258) - **ÉNORME: 654 lignes**

### 7️⃣ **data/cache.py** (Cooldowns & Historiques)
- `check_cooldown()` (ligne 301)
- `update_buy_ratio_history()` (ligne 729)
- `get_buy_ratio_change()` (ligne 745)
- `RECENT_ALERTS` (dict global)
- `BUY_RATIO_HISTORY` (dict global)

### 8️⃣ **data/database.py** (Persistance SQLite)
- Migrer `alert_tracker.py` (AlertTracker class)
- Intégrer `should_send_alert()` (ligne 312) - **85 lignes, logique Règle 4/5**

### 9️⃣ **data/models.py** (Structures de données)
- Dataclasses pour Pool, Alert, Momentum, MultiPoolData, WhaleData
- Remplacer les Dict par des objets typés

### 🔟 **core/filters.py** (Filtres V3)
- `filter_by_velocite()` (ligne 1269)
- `filter_by_type_pump()` (ligne 1301)
- `filter_by_age()` (ligne 1325)
- `filter_by_score_network()` (ligne 1375)
- `filter_by_liquidity_range()` (ligne 1403)
- `apply_v3_filters()` (ligne 1442) - Orchestrateur

### 1️⃣1️⃣ **core/scoring.py** (Système de scoring)
- `calculate_base_score()` (ligne 860) - **138 lignes**
- `calculate_momentum_bonus()` (ligne 998) - **108 lignes**
- `calculate_final_score()` (ligne 1538)
- `calculate_confidence_score()` (ligne 1558)
- `calculate_confidence_tier()` (ligne 1486)

### 1️⃣2️⃣ **core/whale_analyzer.py** (Analyse whales)
- `analyze_whale_activity()` (ligne 1106) - **145 lignes**

### 1️⃣3️⃣ **core/signals.py** (Détection signaux)
- `detect_signals()` (ligne 1598) - **76 lignes**
- `get_price_momentum_from_api()` (ligne 768)
- `find_resistance_simple()` (ligne 779)
- `group_pools_by_token()` (ligne 804)
- `analyze_multi_pool()` (ligne 812) - **48 lignes**
- `check_watchlist_token()` (ligne 1251)

### 1️⃣4️⃣ **core/evaluator.py** (Évaluation opportunités)
- `is_valid_opportunity()` (ligne 1674) - **67 lignes**
- `evaluer_conditions_marche()` (ligne 1741) - **190 lignes**
- `analyser_alerte_suivante()` (ligne 1931) - **311 lignes**

### 1️⃣5️⃣ **core/scanner.py** (Orchestrateur principal)
- `scan_geckoterminal()` (ligne 2912) - **424 lignes** - FONCTION PRINCIPALE
- `main()` (ligne 3336) - Point d'entrée

---

## Plan d'Exécution (Étapes)

### ✅ Phase 0: Préparation (FAIT)
- [x] Backup git (commit 96f3a35)
- [x] Glossaire créé et déployé
- [x] Configuration Railway Flask

### 🔵 Phase 1: Configuration (SAFE - Aucun risque)
**Étape 1.1** - Créer structure dossiers
```bash
mkdir -p core utils data config
touch core/__init__.py utils/__init__.py data/__init__.py config/__init__.py
```

**Étape 1.2** - Extraire configuration
- Créer `config/settings.py` avec NETWORKS, seuils, build_network_thresholds()
- Créer `config/constants.py` avec cooldowns, emojis
- Modifier `geckoterminal_scanner_v3.py`: importer depuis config/
- **Test**: `python geckoterminal_scanner_v3.py --dry-run` (si mode existe)

**Étape 1.3** - Commit et test
```bash
git add config/ geckoterminal_scanner_v3.py
git commit -m "REFACTOR Phase 1: Extract configuration"
```

### 🔵 Phase 2: Utilitaires (SAFE - Pas de logique métier)
**Étape 2.1** - Extraire helpers simples
- Créer `utils/helpers.py` (log, extract_base_token, get_network_display_name)
- Créer `utils/telegram.py` (send_telegram)
- Modifier imports dans scanner V3
- **Test**: Lancer scanner, vérifier logs et Telegram

**Étape 2.2** - Extraire formatters
- Créer `utils/formatters.py` (format_price, generer_alerte_complete)
- **Test**: Vérifier format alertes Telegram

**Étape 2.3** - Commit
```bash
git commit -m "REFACTOR Phase 2: Extract utilities"
```

### 🟡 Phase 3: API Client (MODÉRÉ - Critique mais isolable)
**Étape 3.1** - Créer API client
- Créer `utils/api_client.py` avec get_trending_pools, get_new_pools, get_pool_by_address, parse_pool_data
- **ATTENTION**: parse_pool_data est CRITIQUE (228 lignes)
- Conserver exactement la même logique
- **Test**: Comparer résultats parse_pool_data avant/après

**Étape 3.2** - Commit
```bash
git commit -m "REFACTOR Phase 3: Extract API client"
```

### 🟡 Phase 4: Gestion données (MODÉRÉ - Cache et DB)
**Étape 4.1** - Cache et cooldowns
- Créer `data/cache.py` (check_cooldown, buy_ratio_history)
- Migrer dicts globaux RECENT_ALERTS, BUY_RATIO_HISTORY
- **Test**: Vérifier cooldowns fonctionnent

**Étape 4.2** - Base de données
- Créer `data/database.py` en migrant alert_tracker.py
- Intégrer should_send_alert() (logique Règle 4/5)
- **Test**: Vérifier enregistrement alertes SQLite

**Étape 4.3** - Commit
```bash
git commit -m "REFACTOR Phase 4: Extract data layer"
```

### 🔴 Phase 5: Logique métier (RISQUÉ - Cœur du scanner)
**Étape 5.1** - Filtres V3
- Créer `core/filters.py` (tous les filter_by_*, apply_v3_filters)
- **Test**: Vérifier même nombre d'alertes filtrées

**Étape 5.2** - Whale analyzer
- Créer `core/whale_analyzer.py` (analyze_whale_activity)
- **Test**: Comparer whale_score avant/après

**Étape 5.3** - Signaux et patterns
- Créer `core/signals.py` (detect_signals, analyze_multi_pool, momentum, resistance)
- **Test**: Vérifier détection signaux identique

**Étape 5.4** - Système de scoring
- Créer `core/scoring.py` (calculate_base_score, calculate_final_score, tiers)
- **CRITIQUE**: Vérifier scores identiques à 100%
- **Test**: Comparer scores sur 10 pools réels

**Étape 5.5** - Évaluateur opportunités
- Créer `core/evaluator.py` (is_valid_opportunity, evaluer_conditions_marche, analyser_alerte_suivante)
- **Test**: Vérifier recommandations trade

**Étape 5.6** - Commit après chaque sous-étape
```bash
git commit -m "REFACTOR Phase 5.X: Extract [module]"
```

### 🔴 Phase 6: Scanner principal (TRÈS RISQUÉ)
**Étape 6.1** - Refactoriser scan_geckoterminal()
- Créer `core/scanner.py` avec scan_geckoterminal() et main()
- Simplifier en utilisant tous les modules extraits
- **Test**: Lancer scan complet, comparer résultats avec backup

**Étape 6.2** - Nettoyer point d'entrée
- `geckoterminal_scanner_v3.py` devient un simple lanceur:
```python
from core.scanner import main
if __name__ == "__main__":
    main()
```

**Étape 6.3** - Commit final
```bash
git commit -m "REFACTOR Phase 6: Finalize scanner architecture"
```

### ✅ Phase 7: Validation finale
- Lancer scanner pendant 1h, comparer avec ancienne version
- Vérifier alertes Telegram identiques
- Vérifier DB identique
- **Si tout OK**: Merger et déployer Railway

---

## Critères de Validation

### ✅ Tests à chaque phase:
1. **Import**: `python -c "import geckoterminal_scanner_v3"`
2. **Syntax**: Aucune erreur Python
3. **Fonctionnel**: Scanner démarre sans crash
4. **Comportemental**: Même nombre d'alertes générées
5. **Données**: DB identique, messages Telegram identiques

### ⚠️ Points d'attention:
- **parse_pool_data** (228 lignes): NE PAS casser le parsing
- **generer_alerte_complete** (654 lignes): Messages Telegram doivent rester identiques
- **calculate_base_score** (138 lignes): Scores DOIVENT être identiques
- **scan_geckoterminal** (424 lignes): Orchestration critique

---

## Bénéfices Attendus

### 📊 Avant (Monolithe)
- 1 fichier: 3393 lignes
- 42 fonctions mélangées
- Difficile à maintenir
- Impossible à tester unitairement

### 📊 Après (Modulaire)
- ~15 fichiers: 200-300 lignes chacun
- Responsabilités claires
- Tests unitaires possibles
- Évolutions facilitées
- Ajout nouvelles features sans casser l'existant

### 🎯 Prochaines évolutions facilitées:
- Ajouter nouveaux réseaux (1 ligne dans config)
- Modifier scoring (fichier isolé)
- Nouveaux filtres (ajouter dans filters.py)
- Nouveaux signaux (ajouter dans signals.py)
- Tests A/B de stratégies (dupliquer core/scoring.py)

---

## Notes Importantes

1. **Pas de réarchitecture du code**: On déplace, on ne réécrit pas
2. **Préserver la logique exacte**: Copier-coller, pas de "améliorations"
3. **Un commit = Une phase**: Toujours pouvoir revenir en arrière
4. **Tester avant de continuer**: Jamais avancer si phase N est cassée
5. **Garder V3 fonctionnel**: À chaque commit, le scanner doit marcher

---

## Prochaine Action

**COMMENCER PAR**: Phase 1 - Configuration (le plus safe)
