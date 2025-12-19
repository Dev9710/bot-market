# 🔧 FIX: Seulement 1 Alerte Depuis 13h06

**Date**: 2025-12-19
**Problème**: Anti-spam trop strict bloque les nouvelles alertes
**Solution**: Désactiver temporairement l'anti-spam pour collecte de données

---

## 🔍 DIAGNOSTIC

### Symptôme
- Depuis 13h06: **1 seule alerte** (LISA)
- Bot scanne mais n'alerte pas
- Phase de collecte de données ralentie

### Cause Racine

Le **Bug #1 fix** (anti-spam intelligent) a été appliqué avec `ENABLE_SMART_REALERT = True`.

**Comportement actuel**:
```python
def should_send_alert(token_address, current_price, tracker, regle5_data):
    # 1ère alerte: TOUJOURS envoyer
    if not tracker.token_already_alerted(token_address):
        return True

    # Alertes suivantes: SEULEMENT si...
    # ❌ TP atteint → NON (token jamais tradé)
    # ❌ Prix varié ±5% → NON (variation minime)
    # ❌ 4h écoulées → NON (scan toutes les 5min)
    # ❌ Pump parabolique → NON (rare)

    return False  # → BLOQUÉ !
```

**Résultat**: Tokens détectés mais **bloqués** car considérés "spam".

---

## ✅ SOLUTION APPLIQUÉE

### Modification

**Fichier**: [geckoterminal_scanner_v2.py](geckoterminal_scanner_v2.py:67)

**AVANT**:
```python
ENABLE_SMART_REALERT = True  # Activer le système intelligent (vs spam)
```

**APRÈS**:
```python
ENABLE_SMART_REALERT = False  # DÉSACTIVÉ pour phase backtesting (collecte max de données)
```

### Impact

**Avec `ENABLE_SMART_REALERT = False`**:
```python
def should_send_alert(token_address, current_price, tracker, regle5_data):
    # Si système intelligent désactivé, toujours envoyer
    if not ENABLE_SMART_REALERT:
        return True, "Smart re-alert désactivé"  # ✅ TOUJOURS ENVOYÉ

    # ... reste du code (jamais exécuté)
```

**Résultat attendu**:
- **TOUTES** les nouvelles alertes envoyées (comme avant)
- Collecte de données maximale pour backtesting
- Logs: Plus de `⏸️ Alerte bloquée (anti-spam)`

---

## 📊 COMPORTEMENTS COMPARÉS

### Mode PRODUCTION (ENABLE_SMART_REALERT = True)

**Avantages**:
- ✅ Pas de spam Telegram (1 alerte / 4h max par token)
- ✅ Alertes seulement sur changements significatifs
- ✅ Meilleure UX pour utilisateur final

**Inconvénients**:
- ❌ Moins d'alertes (collecte de données réduite)
- ❌ Tokens détectés mais non alertés
- ❌ Backtesting incomplet

**Quand l'utiliser**: En production, quand l'utilisateur reçoit les alertes Telegram.

---

### Mode BACKTESTING (ENABLE_SMART_REALERT = False)

**Avantages**:
- ✅ Collecte MAXIMALE de données
- ✅ Toutes les opportunités détectées sont alertées
- ✅ Backtesting complet et précis

**Inconvénients**:
- ❌ Spam Telegram si utilisateur écoute
- ❌ Beaucoup d'alertes répétitives

**Quand l'utiliser**:
- Phase de collecte de données (7 jours)
- Backtesting et calibration
- Tests de stratégies

---

## 🚀 DÉPLOIEMENT

### Commandes Git

```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market

git add geckoterminal_scanner_v2.py FIX_PEU_ALERTES.md
git commit -m "🔧 Désactive anti-spam pour phase backtesting

Problème: Seulement 1 alerte depuis 13h06
Cause: ENABLE_SMART_REALERT = True bloque les nouvelles alertes

Solution: ENABLE_SMART_REALERT = False pour collecte max de données

Impact:
- Toutes les alertes envoyées (pas de blocage anti-spam)
- Collecte de données maximale pour backtesting
- À réactiver en production après backtesting

Fichiers modifiés:
- geckoterminal_scanner_v2.py:67 (ENABLE_SMART_REALERT = False)
- FIX_PEU_ALERTES.md (documentation)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push railway main
```

---

## 🔍 VÉRIFICATION POST-DÉPLOIEMENT

### Logs Railway (5 min après deploy)

**Vérifier**:
```bash
railway logs | tail -50
```

**Attendu**:
```
✅ Alerte envoyée: TOKEN_ABC (Score: 72)
✅ Alerte envoyée: TOKEN_XYZ (Score: 68)
✅ Alerte envoyée: TOKEN_DEF (Score: 75)
```

**NE DEVRAIT PLUS voir**:
```
⏸️ Alerte bloquée (anti-spam): TOKEN_ABC  ← NE DEVRAIT PLUS APPARAÎTRE
   Raison: Pas de changement significatif
```

---

### Telegram (30 min après deploy)

**Attendu**:
- **5-10 alertes/heure** (au lieu de 1/7h)
- Mix de scores (60-90)
- Différents réseaux (ETH, BSC, Base, etc.)

**Si toujours 1 alerte/7h**:
1. Vérifier logs Railway → Erreur Python?
2. Vérifier `ENABLE_SMART_REALERT` déployé → `railway logs | grep SMART`
3. Redémarrer service → `railway up`

---

## 📈 RÉSULTATS ATTENDUS

### Avant Fix
- **13h06 → 15h30**: 1 alerte (LISA)
- **Taux**: ~0.4 alerte/heure
- **Collecte données**: INSUFFISANTE

### Après Fix
- **15h40 → 17h00**: 5-10 alertes
- **Taux**: ~5 alertes/heure
- **Collecte données**: EXCELLENTE

### Estimation 7 jours
- **Avant**: ~70 alertes (7 jours × 10 alertes/jour)
- **Après**: ~840 alertes (7 jours × 120 alertes/jour)
- **Gain**: **+1100% de données** pour backtesting

---

## ⚠️ IMPORTANT: RÉACTIVER EN PRODUCTION

**APRÈS la phase de backtesting (7 jours)**:

1. Analyser les résultats du backtest
2. Calibrer les seuils
3. **Réactiver l'anti-spam**:
   ```python
   ENABLE_SMART_REALERT = True
   ```
4. Redéployer sur Railway

**Pourquoi ?**
- En production, l'utilisateur ne veut PAS 120 alertes/jour
- Anti-spam améliore l'UX (alertes pertinentes seulement)
- Évite saturation Telegram

---

## 🎯 TIMELINE

### Phase 1: Collecte de Données (7 jours)
**Config**: `ENABLE_SMART_REALERT = False`
**Objectif**: Collecter 800+ alertes

### Phase 2: Backtesting (2 jours)
**Action**: Analyser les 800 alertes
**Output**: Win rate, ROI moyen, stratégies

### Phase 3: Production (permanent)
**Config**: `ENABLE_SMART_REALERT = True`
**Objectif**: Alertes pertinentes seulement

---

## 📊 MONITORING

### Requête SQL (vérifier collecte)

```sql
-- Nombre d'alertes par heure (dernières 24h)
SELECT
    strftime('%Y-%m-%d %H:00', timestamp) as heure,
    COUNT(*) as nb_alertes
FROM alerts
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY heure
ORDER BY heure DESC;

-- Attendu: 5-10 alertes/heure
```

### Dashboard Streamlit

```bash
python dashboard.py
```

**Vérifier**:
- Graph "Alertes par heure" → Courbe montante
- Win rate → Devrait rester ~20% (pas d'impact)
- Tokens uniques → Augmentation

---

## ✅ CHECKLIST

- [x] `ENABLE_SMART_REALERT = False` modifié
- [x] Documentation créée
- [ ] Commit Git créé
- [ ] Push sur Railway
- [ ] Vérification logs (5 min après)
- [ ] Vérification Telegram (30 min après)
- [ ] Monitoring 24h
- [ ] Après 7 jours: Backtest complet
- [ ] Après backtesting: Réactiver anti-spam

---

**Date**: 2025-12-19
**Status**: ✅ FIX APPLIQUÉ - EN ATTENTE DÉPLOIEMENT
**Impact**: +1100% collecte de données pour backtesting
