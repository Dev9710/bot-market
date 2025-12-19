# 🔍 DEBUG - TP Detection Issue

**Date**: 2025-12-19 16:00
**Commit**: fdd1c90
**Status**: 🔍 INVESTIGATION EN COURS

---

## 🚨 PROBLÈME SIGNALÉ

### Alerte LISA (15:42)

**Données affichées**:
```
📍 Entry précédente: $0.15
💰 Prix actuel: $0.16 (+3.6%)
TP1 (50%): $0.16 (+5%)
⏳ Aucun TP atteint pour le moment  ← ❌ INCORRECT ?
```

**Question utilisateur**:
> "Ici le TP1 a été touché non ? Pourquoi l'alerte affiche 'Aucun TP atteint' alors que oui ?"

---

## 🔍 HYPOTHÈSE

### Calcul TP1

```python
Entry: $0.15
TP1: $0.15 × 1.05 = $0.1575 (exactement)
```

### Affichage vs Réalité

**Affiché** (format_price avec 2 décimales):
```
Prix actuel: $0.16
```

**Réalité possible**:
```
Prix actuel (exact): $0.15740000  ← En dessous de TP1 !
TP1 (exact):         $0.15750000
```

**Résultat**: $0.1574 < $0.1575 → TP1 **PAS atteint** ✅ (techniquement correct)

Mais **affiché** comme $0.16 > $0.16 → Confusion utilisateur ❌

---

## 🔧 DEBUG AJOUTÉ

### Modification

**Fichier**: [geckoterminal_scanner_v2.py:1251-1253](geckoterminal_scanner_v2.py#L1251-L1253)

**Code ajouté**:
```python
# DEBUG: Log pour comprendre détection TP
if alert_id > 0:
    log(f"   🔍 DEBUG TP: prix_max={prix_max_atteint:.8f}, tp1={tp1_price:.8f}, tp2={tp2_price:.8f}, tp3={tp3_price:.8f}")
```

### Logs Attendus (prochaine alerte LISA)

```
🔍 DEBUG TP: prix_max=0.15740000, tp1=0.15750000, tp2=0.16500000, tp3=0.17250000
⏳ Aucun TP atteint pour le moment
```

**OU si TP atteint**:
```
🔍 DEBUG TP: prix_max=0.16000000, tp1=0.15750000, tp2=0.16500000, tp3=0.17250000
✅ TP1 atteint (+5.0%)
```

---

## 📊 SCÉNARIOS POSSIBLES

### Scénario 1: Arrondi d'Affichage (PROBABLE)

**Symptôme**: Prix exact $0.1574 affiché comme $0.16

**Cause**:
```python
def format_price(price: float) -> str:
    if price >= 0.01:
        return f"${price:.2f}"  # Arrondi à 2 décimales
```

**Solution**:
- ✅ Logs DEBUG montreront le vrai prix
- Aucune modification nécessaire (logique correcte)
- User comprendra que $0.16 affiché = $0.1574 réel

### Scénario 2: Tracking Automatique Manquant (POSSIBLE)

**Symptôme**: Prix a atteint $0.16 mais pas détecté car pas de tracking

**Cause**:
- Table `price_tracking` vide (tracking auto pas activé)
- `get_highest_price_for_alert()` retourne `None`
- Utilise seulement `current_price` (fallback)

**Vérification**:
```sql
SELECT * FROM price_tracking WHERE alert_id = (
    SELECT id FROM alerts WHERE token_address LIKE '%LISA%' ORDER BY id DESC LIMIT 1
);
```

**Si vide** → Tracking auto pas activé

**Solution**:
- Activer tracking background (future feature)
- Ou accepter détection basée sur current_price seulement

### Scénario 3: Erreur de Calcul TP (IMPROBABLE)

**Symptôme**: TP1 calculé incorrectement

**Vérification**:
```python
# Ligne 2130 (lors sauvegarde alerte)
tp1_price = price * 1.05  # Devrait être $0.15 * 1.05 = $0.1575
```

**Debug log montrera**:
```
tp1=0.15750000  ← Correct
```

**Si différent** → Bug de calcul (peu probable)

---

## ✅ ACTIONS

### Immédiat (Fait)
- [x] Ajout logs DEBUG avec 8 décimales
- [x] Commit + Push (fdd1c90)
- [x] Déploiement Railway en cours

### Prochaine Alerte LISA
- [ ] Observer logs DEBUG
- [ ] Vérifier prix_max exact vs tp1 exact
- [ ] Confirmer hypothèse arrondi

### Si Arrondi Confirmé
- [ ] Option 1: Accepter (logique correcte, juste affichage)
- [ ] Option 2: Changer seuil TP (1.06 au lieu de 1.05)
- [ ] Option 3: Afficher prix avec plus de décimales

### Si Tracking Manquant
- [ ] Activer tracking auto background
- [ ] Ou documenter limitation

---

## 📈 ANALYSE DÉTAILLÉE DES ALERTES

### Alerte 1 (13:06) - Première alerte LISA
```
Entry: $0.15
TP1: $0.1575 (+5%)
TP2: $0.165 (+10%)
TP3: $0.1725 (+15%)
```

### Alerte 2 (15:24) - 2h18 après
```
Prix actuel: $0.15 (+0.1%)
TP détecté: Aucun
```
**Analyse**: Prix stable, TP1 pas atteint ✅

### Alerte 3 (15:42) - 2h36 après (18min après alerte 2)
```
Prix actuel: $0.16 (+3.6%)  ← Affiché
Prix exact:   $0.157X?      ← À confirmer avec DEBUG
TP1:          $0.1575
TP détecté:   Aucun         ← Correct SI prix < $0.1575
```

**Questions**:
1. Prix exact = $0.1574 ou $0.16 ?
2. Si $0.16 exact, pourquoi TP1 pas détecté ?

**Réponses attendues** (prochaine alerte):
```
🔍 DEBUG TP: prix_max=0.15740000, tp1=0.15750000
→ Confirme hypothèse arrondi

OU

🔍 DEBUG TP: prix_max=0.16000000, tp1=0.15750000
→ BUG de détection TP !
```

---

## 🎯 RÉSOLUTION ATTENDUE

### Si Arrondi (90% probable)

**Explication**:
```
Prix réel:     $0.1574
Prix affiché:  $0.16 (arrondi)
TP1:           $0.1575

Logique: $0.1574 < $0.1575 ✅ Correct !
UX: User voit $0.16 > $0.16 ❌ Confusion
```

**Solution UX**:
- Afficher prix avec 4 décimales pour tokens < $1
- Ou tolérance 0.1% pour TP ($0.1574 considéré = TP1)

### Si Bug Tracking (10% probable)

**Explication**:
```
Prix a atteint $0.16 à 15:30
Prix actuel à 15:42: $0.155 (retrace)

Sans tracking auto: utilise $0.155 (current) → TP1 pas détecté ❌
Avec tracking auto: utilise $0.16 (max) → TP1 détecté ✅
```

**Solution**:
- Activer tracking background (feature complète)
- Ou accepter limitation (détection seulement si prix actuel >= TP)

---

## 📝 LOGS À SURVEILLER

### Railway Logs (prochaine alerte LISA)

**Rechercher**:
```bash
railway logs | grep "DEBUG TP"
```

**Attendu**:
```
🔍 DEBUG TP: prix_max=0.15740000, tp1=0.15750000, tp2=0.16500000, tp3=0.17250000
```

**Analyse**:
- Si `prix_max < tp1` → Hypothèse arrondi confirmée ✅
- Si `prix_max >= tp1` → Bug détection TP ❌

---

## �� SUIVI

### Timeline

**16:00**: DEBUG ajouté et déployé
**16:05**: Attente prochaine alerte LISA
**16:XX**: Analyse logs DEBUG
**16:XX**: Décision sur fix à appliquer

### Commit

- **fdd1c90**: DEBUG TP detection logging

---

**Date**: 2025-12-19 16:00
**Status**: 🔍 INVESTIGATION
**Prochaine étape**: Analyser logs DEBUG à la prochaine alerte LISA
