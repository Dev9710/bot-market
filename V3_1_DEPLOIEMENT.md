# V3.1 DASHBOARD - Prêt pour déploiement

Configuration active dans [geckoterminal_scanner_v3.py](geckoterminal_scanner_v3.py)

---

## Configuration Déployée: DASHBOARD

**Objectif**: Volume optimal pour dashboard front-end
**Test validé**: 5.0 alertes/jour sur 4252 alertes historiques

### Résultats de Test

```
Total alertes:        454 / 4252 (10.7%)
Alertes/jour:        5.0
Score moyen:         91.4
Velocité moyenne:    87.2
Liquidité moyenne:   $541,199

Win Rate estimé:     45-58%
ROI mensuel projeté: +4.4%
```

### Distribution Qualité

```
Score 95-100:  248 alertes (54.6%) ← EXCELLENT, majorité
Score 90-94:    39 alertes ( 8.6%)
Score 85-89:    54 alertes (11.9%)
Score 80-84:    50 alertes (11.0%)
Score <80:      63 alertes (13.9%) ← Risque acceptable
```

**Qualité**: 63.2% des alertes avec score 90+ (bon niveau)

### Répartition par Réseau

```
SOLANA: 186 alertes (2.1/jour) - Score 87.2
ETH:    150 alertes (1.7/jour) - Score 92.6
BASE:    89 alertes (1.0/jour) - Score 97.2
BSC:     29 alertes (0.3/jour) - Score 94.2
```

### Paramètres Techniques

```python
MIN_VELOCITE_PUMP = 5.0

NETWORK_SCORE_FILTERS = {
    'eth': {'min_score': 78, 'min_velocity': 5},
    'base': {'min_score': 82, 'min_velocity': 8},
    'bsc': {'min_score': 80, 'min_velocity': 6},
    'solana': {'min_score': 72, 'min_velocity': 5},
}

LIQUIDITY (par réseau):
- ETH: $80K - $600K
- BASE: $250K - $2.5M
- BSC: $400K - $6M
- SOLANA: $80K - $300K
```

---

## Validation

✅ **Volume**: 5 alertes/jour = flux régulier
✅ **Qualité**: Score moyen 91.4 (>90 excellent)
✅ **ROI**: +4.4%/mois positif
✅ **Diversification**: 4 réseaux bien couverts
✅ **Risque**: 13.9% alertes <80 (acceptable)

**Statut**: ✅ CONFIGURATION VALIDÉE - Prêt pour déploiement Railway

---

## Déploiement sur Railway

### Fichiers à déployer

1. **geckoterminal_scanner_v3.py** ← Scanner principal avec config DASHBOARD
2. **security_checker.py** ← Module sécurité
3. **alert_tracker.py** ← Module tracking
4. **.env.v3** ← Variables d'environnement (Telegram tokens)
5. **requirements.txt** ← Dépendances Python

### Variables d'environnement Railway

Dans Railway, configurer:
```
TELEGRAM_BOT_TOKEN=<votre_token>
TELEGRAM_CHAT_ID=<votre_chat_id>
```

Le scanner affichera au démarrage:
```
================================================================================
V3.1 DASHBOARD - Configuration active
Objectif: 5 alertes/jour | Score 91.4 | WR 45-58% | ROI +4-7%/mois
================================================================================
```

---

## Monitoring Post-Déploiement

**Métriques à suivre (2-3 semaines)**:

1. **Volume réel**: Confirmer ~5 alertes/jour
2. **Score moyen**: Doit rester >90
3. **Win Rate réel**: Comparer avec estimation 45-58%
4. **Distribution**: Vérifier % alertes par réseau

**Fichier de suivi**: L'`alert_tracker.py` enregistre toutes les alertes

---

## Ajustements Possibles

### Si Win Rate réel >55%
→ Bon signal, peut assouplir davantage pour plus de volume

### Si Win Rate réel 45-55%
→ **PARFAIT**, configuration optimale, garder

### Si Win Rate réel <45%
→ Resserrer vers configuration STRICTE (2.7/jour)
→ Voir [V3_1_MODES_CONFIG.md](V3_1_MODES_CONFIG.md) pour procédure

---

## Configuration Alternative: STRICTE

**Disponible si besoin de qualité maximale**

- 2.7 alertes/jour (vs 5/jour)
- Score 95.9 (vs 91.4)
- WR 55-70% (vs 45-58%)
- ROI +10-15% (vs +4-7%)
- 0% alertes <80 (vs 13.9%)

**Trade-off**: Volume réduit de -46% mais qualité maximale

**Procédure**: Voir [V3_1_MODES_CONFIG.md](V3_1_MODES_CONFIG.md) section "Comment passer en mode ULTRA_RENTABLE"

---

## Tests de Validation

**Tester config DASHBOARD actuelle**:
```bash
python test_v3_1_final.py alerts_railway_export_utf8.json
```
Attendu: 454 alertes, score 91.4

**Tester config STRICTE alternative**:
```bash
python test_v3_1_strict.py alerts_railway_export_utf8.json
```
Attendu: 244 alertes, score 95.9

---

## Améliorations V3.1 vs V2

✅ Arbitrum désactivé (4.4% quality → gaspillage)
✅ Filtres différenciés par réseau (ETH moins strict, BASE plus strict)
✅ Zone embryonic 0-3h acceptée (QI 182.83, meilleur potentiel)
✅ Zone danger 12-24h évitée (QI 36.87, pire zone)
✅ Limites liquidité optimisées par backtest
✅ Configuration testée sur 4252 alertes réelles

**Résultat**: Meilleur compromis volume/qualité pour dashboard

---

## Récapitulatif

| Métrique | V3.1 DASHBOARD |
|----------|----------------|
| Volume | 5/jour |
| Score moyen | 91.4 |
| % Score 90+ | 63.2% |
| Win Rate | 45-58% |
| ROI/mois | +4-7% |
| Risque (<80) | 13.9% |

**Recommandation**: ✅ **DÉPLOYER EN PRODUCTION**

Volume régulier + qualité acceptable + ROI positif = Configuration idéale pour dashboard front-end

---

## Prochaines Étapes

1. ✅ Configuration DASHBOARD implémentée
2. ✅ Tests validés (5/jour, score 91.4)
3. ⏳ Déployer sur Railway
4. ⏳ Monitorer 2-3 semaines
5. ⏳ Ajuster selon Win Rate réel

**Configuration alternative STRICTE disponible si nécessaire**
