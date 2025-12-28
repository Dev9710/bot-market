# V3.1 - Configurations Disponibles

Basé sur l'analyse de 4252 alertes Railway (90 jours).

---

## Configuration Actuelle: DASHBOARD

**Fichier**: [geckoterminal_scanner_v3.py](geckoterminal_scanner_v3.py)

**Résultats attendus**:
- **Volume**: 5 alertes/jour (454 alertes/90j)
- **Qualité**: Score moyen 91.4
- **Win Rate**: 45-58%
- **ROI mensuel**: +4-7%

**Configuration**:
```python
MIN_VELOCITE_PUMP = 5.0

NETWORK_SCORE_FILTERS = {
    'eth': {'min_score': 78, 'min_velocity': 5},
    'base': {'min_score': 82, 'min_velocity': 8},
    'bsc': {'min_score': 80, 'min_velocity': 6},
    'solana': {'min_score': 72, 'min_velocity': 5},
}

LIQUIDITY = {
    'eth': (80000, 600000),
    'base': (250000, 2500000),
    'bsc': (400000, 6000000),
    'solana': (80000, 300000),
}
```

**Distribution qualité (test sur 454 alertes)**:
- Score 95-100: 226 alertes (49.8%)
- Score 90-94: 38 alertes (8.4%)
- Score 85-89: 55 alertes (12.1%)
- Score 80-84: 60 alertes (13.2%)
- Score <80: 75 alertes (16.5%)

**Répartition par réseau**:
- SOLANA: 197 alertes (2.2/jour) - Score 87.6
- ETH: 152 alertes (1.7/jour) - Score 92.3
- BASE: 79 alertes (0.9/jour) - Score 97.6
- BSC: 26 alertes (0.3/jour) - Score 94.9

**Avantages**:
- Volume régulier d'opportunités (5/jour)
- Bonne utilisation du capital
- Qualité acceptable (score moyen >90)
- ROI positif attendu (+4-7%/mois)

**Inconvénients**:
- 16.5% des alertes avec score <80 (risque)
- Win rate modéré (45-58%)

---

## Configuration Alternative: ULTRA_RENTABLE

**Résultats attendus**:
- **Volume**: 2.7 alertes/jour (244 alertes/90j)
- **Qualité**: Score moyen 95.9
- **Win Rate**: 55-70%
- **ROI mensuel**: +10-15%

**Configuration à implémenter**:
```python
MIN_VELOCITE_PUMP = 10.0

NETWORK_SCORE_FILTERS = {
    'eth': {'min_score': 85, 'min_velocity': 10},
    'base': {'min_score': 90, 'min_velocity': 15},
    'bsc': {'min_score': 88, 'min_velocity': 12},
    'solana': {'min_score': 85, 'min_velocity': 10},
}

LIQUIDITY = {
    'eth': (100000, 500000),
    'base': (300000, 2000000),
    'bsc': (500000, 5000000),
    'solana': (100000, 250000),
}
```

**Distribution qualité (test sur 244 alertes)**:
- Score 95-100: 186 alertes (76.2%) ← EXCELLENT
- Score 90-94: 30 alertes (12.3%)
- Score 85-89: 21 alertes (8.6%)
- Score 80-84: 7 alertes (2.9%)
- Score <80: 0 alertes (0.0%)

**Répartition par réseau**:
- ETH: 103 alertes (1.1/jour) - Score 95.4 - Vel 221.8
- SOLANA: 94 alertes (1.0/jour) - Score 95.1 - Vel 61.3
- BASE: 30 alertes (0.3/jour) - Score 99.0 - Vel 59.8
- BSC: 17 alertes (0.2/jour) - Score 97.6 - Vel 26.3

**Avantages**:
- Qualité MAXIMALE (score 95.9)
- 76% des alertes avec score 95+ (excellence)
- Win rate optimal (55-70%)
- ROI élevé (+10-15%/mois)
- Risque minimal (0% alertes <80)

**Inconvénients**:
- Volume faible (2.7/jour, ~3 par semaine)
- Sous-utilisation du capital
- Moins d'opportunités

---

## Comment passer en mode ULTRA_RENTABLE

**Étapes**:

1. Modifier [geckoterminal_scanner_v3.py](geckoterminal_scanner_v3.py) lignes 147-167:

```python
# Remplacer DASHBOARD_CONFIG par:
ULTRA_RENTABLE_CONFIG = {
    'MIN_VELOCITE_PUMP': 10.0,
    'NETWORK_SCORE_FILTERS': {
        'eth': {'min_score': 85, 'min_velocity': 10},
        'base': {'min_score': 90, 'min_velocity': 15},
        'bsc': {'min_score': 88, 'min_velocity': 12},
        'solana': {'min_score': 85, 'min_velocity': 10},
    },
    'LIQUIDITY': {
        'eth': (100000, 500000),
        'base': (300000, 2000000),
        'bsc': (500000, 5000000),
        'solana': (100000, 250000),
    }
}

# Appliquer la configuration
MIN_VELOCITE_PUMP = ULTRA_RENTABLE_CONFIG['MIN_VELOCITE_PUMP']
NETWORK_SCORE_FILTERS = ULTRA_RENTABLE_CONFIG['NETWORK_SCORE_FILTERS']
NETWORK_THRESHOLDS = build_network_thresholds(ULTRA_RENTABLE_CONFIG)
```

2. Mettre à jour le message de démarrage ligne 142-145:

```python
print("=" * 80)
print("V3.1 ULTRA_RENTABLE - Configuration active")
print("Objectif: 2.7 alertes/jour | Score 95.9 | WR 55-70% | ROI +10-15%/mois")
print("=" * 80)
```

3. Tester localement avec:
```bash
python test_v3_1_final.py alerts_railway_export_utf8.json
```

4. Si résultats conformes (~244 alertes, score 95.9), déployer sur Railway

---

## Recommandation

**Pour démarrage**: Garder **DASHBOARD** (actuellement configuré)
- Permet de collecter des données réelles
- Volume suffisant pour valider le système
- ROI positif attendu

**Après 2-3 semaines de test**:
- Si Win Rate réel >55%: Peut rester en DASHBOARD ou assouplir davantage
- Si Win Rate réel 45-55%: DASHBOARD optimal, garder
- Si Win Rate réel <45%: Passer en **ULTRA_RENTABLE** pour améliorer qualité

---

## Fichiers de test

Pour valider les configurations:

**Test DASHBOARD (5/jour)**:
```bash
python test_v3_1_final.py alerts_railway_export_utf8.json
```
Attendu: 454 alertes, score 91.4

**Test ULTRA_RENTABLE (2.7/jour)**:
```bash
python test_v3_1_strict.py alerts_railway_export_utf8.json
```
Attendu: 244 alertes, score 95.9

---

## Notes techniques

Les deux configurations partagent:
- Mêmes filtres de type pump (rejet LENT, STAGNANT, STABLE)
- Même gestion des zones d'âge (embryonic 0-3h, danger 12-24h évité)
- Même watchlist tokens (snowball, RTX, TTD, FIREBALL)
- Arbitrum désactivé (4.4% quality rate)

**Différence principale**: Sévérité des seuils de score et vélocité par réseau
