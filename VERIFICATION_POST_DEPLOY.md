# ✅ VÉRIFICATION POST-DÉPLOIEMENT

**Date**: 2025-12-19
**Commit**: 416753f
**Déploiement**: GitHub → Railway (auto-deploy)

---

## 🎯 CE QUI A ÉTÉ DÉPLOYÉ

### 1. Fix 6 Bugs Critiques
- ✅ Bug #1 - Alert Spam (système intelligent)
- ✅ Bug #2 - Whale threshold (avg > 10)
- ✅ Bug #3 - MAINTENIR_POSITION (conseils conditionnels)
- ✅ Bug #4 - Multi-TF Confluence (pullback sain)
- ✅ Bug #5 - Whale score display (toujours affiché)
- ✅ Bug #6 - Decision logic (Score 70+ → ENTRER)

### 2. Anti-Spam Désactivé
- `ENABLE_SMART_REALERT = False`
- **Objectif**: Collecte maximale de données (7 jours)
- **Impact attendu**: +1100% alertes (5-10/heure au lieu de 0.4/heure)

---

## 🔍 VÉRIFICATIONS IMMÉDIATES (5-10 minutes)

### 1. Railway Dashboard

**URL**: https://railway.app/

**Vérifier**:
- ✅ Build en cours / terminé
- ✅ Deployment "Active"
- ✅ Aucune erreur dans l'onglet "Deployments"

**Si erreur**:
- Cliquer sur "View Logs"
- Chercher `SyntaxError`, `ImportError`, `ModuleNotFoundError`
- Si erreur Python → Vérifier syntaxe localement

---

### 2. Logs Railway

**Commande**:
```bash
railway logs
```

**OU via Dashboard**: Cliquer sur "View Logs" dans le deployment actif

**Logs attendus** (dans les 5 premières minutes):
```
✅ AlertTracker initialisé - DB: alerts_history.db
✅ SecurityChecker initialisé
🔍 Scan réseau: eth
🔍 Scan réseau: bsc
🔍 Scan réseau: arbitrum

✅ Alerte envoyée: TOKEN_ABC (Score: 72)
✅ Alerte envoyée: TOKEN_XYZ (Score: 68)
✅ Alerte envoyée: TOKEN_DEF (Score: 75)
```

**Logs à NE PLUS VOIR**:
```
⏸️ Alerte bloquée (anti-spam): TOKEN_ABC  ← NE DEVRAIT PLUS APPARAÎTRE
   Raison: Pas de changement significatif
```

**Si erreurs**:
```
Traceback (most recent call last):
  File "geckoterminal_scanner_v2.py", line X
    ...
SyntaxError: ...
```
→ Rollback: `git revert HEAD && git push origin main`

---

### 3. Telegram (30 minutes après deploy)

**Vérifier**:
- ✅ **5-10 alertes reçues** dans la première heure
- ✅ Alertes variées (différents scores, réseaux, tokens)
- ✅ Section "WHALE ACTIVITY" visible (si whale_score != 0)
- ✅ Section "PULLBACK SAIN" pour tokens +5% 24h, -5% 1h
- ✅ Décisions "ENTRER" pour scores 70+

**Exemple d'alerte attendue**:
```
🆕 Nouvelle opportunité sur le token XYZ

🎯 SCORE: 75/100 ⭐⭐⭐ TRÈS BON
   Base: 65 | Momentum: +12 | Whale: -2

📊 WHALE ACTIVITY  ← Devrait apparaître si whale_score != 0
   Buyers: 180 | Sellers: 150
   Avg buys/buyer: 4.2x
   Risque concentration: MEDIUM

━━━ ACTION RECOMMANDÉE ━━━
✅ SIGNAL D'ENTRÉE VALIDÉ  ← Score 70+ devrait donner ENTRER

📈 Signaux haussiers:
   • Score bon (≥70)
   • 📊 PULLBACK SAIN: +8.5% 24h | -2.3% 1h (buy the dip)  ← Nouveau !
   • ✅ Multi-TF confluence: Opportunité d'entrée sur retracement
```

**Si toujours 1 alerte/7h**:
- Vérifier logs Railway → Erreur?
- Vérifier `ENABLE_SMART_REALERT` déployé
- Redémarrer service Railway

---

## 📊 VÉRIFICATIONS 24H (Lendemain)

### 1. Comptage Alertes

**Requête SQL**:
```sql
-- Via Railway Shell ou DB téléchargée
SELECT
    strftime('%Y-%m-%d %H:00', timestamp) as heure,
    COUNT(*) as nb_alertes
FROM alerts
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY heure
ORDER BY heure DESC;
```

**Attendu**:
```
2025-12-19 15:00 | 8
2025-12-19 16:00 | 12
2025-12-19 17:00 | 6
2025-12-19 18:00 | 10
...
```

**Si < 3 alertes/heure**: Problème, vérifier logs.

---

### 2. Distribution Scores

**Requête SQL**:
```sql
SELECT
    CASE
        WHEN score >= 80 THEN '80-100 (EXCELLENT)'
        WHEN score >= 70 THEN '70-79 (TRÈS BON)'
        WHEN score >= 60 THEN '60-69 (BON)'
        ELSE '55-59 (MOYEN)'
    END as score_range,
    COUNT(*) as nb_alertes
FROM alerts
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY score_range
ORDER BY score_range DESC;
```

**Attendu**:
```
80-100 (EXCELLENT) | 15
70-79 (TRÈS BON)   | 35
60-69 (BON)        | 60
55-59 (MOYEN)      | 10
```

---

### 3. Whales Détectées

**Requête SQL**:
```sql
SELECT
    type_pump,
    COUNT(*) as nb,
    AVG(score) as score_moyen
FROM alerts
WHERE timestamp >= datetime('now', '-24 hours')
  AND type_pump IS NOT NULL
GROUP BY type_pump
ORDER BY nb DESC;
```

**Attendu**: Au moins quelques WHALE_MANIPULATION détectées.

---

### 4. Multi-TF Confluence

**Logs à chercher**:
```bash
railway logs | grep "PULLBACK SAIN"
```

**Attendu**: Au moins 5-10 occurrences/jour.

---

## 🎯 INDICATEURS DE SUCCÈS

### ✅ Succès (24h après deploy)

- [x] **100+ alertes** reçues en 24h (vs 10 avant)
- [x] **5-10 alertes/heure** en moyenne
- [x] **Aucune erreur Python** dans les logs
- [x] **Sections WHALE ACTIVITY** visibles
- [x] **PULLBACK SAIN** détecté sur au moins 10 tokens
- [x] **Scores 70+** donnent "ENTRER" (pas "ATTENDRE")
- [x] **Whales avg > 10** détectées comme MANIPULATION

### ❌ Échec (nécessite investigation)

- [ ] < 50 alertes en 24h
- [ ] Erreurs Python fréquentes
- [ ] Sections WHALE manquantes
- [ ] Scores 70+ donnent "ATTENDRE"
- [ ] Aucun PULLBACK SAIN détecté

---

## 🔄 APRÈS 7 JOURS (Phase Backtesting)

### 1. Télécharger la DB

```bash
railway run cat /app/alerts_history.db > alerts_history_downloaded.db
```

### 2. Lancer le Backtest

```bash
python backtest_analyzer_optimized.py
```

**Attendu**:
- **800-1000 alertes** analysées
- **Win rate**: 30-40% (vs 20.9% avant)
- **ROI moyen**: +15% sur winners
- **Distribution pumps**: Petit 40%, Moyen 35%, Gros 20%, Moon 5%

### 3. RÉACTIVER L'Anti-Spam

**Fichier**: `geckoterminal_scanner_v2.py:67`

**Modifier**:
```python
ENABLE_SMART_REALERT = True  # Réactiver après backtesting
```

**Commit & Push**:
```bash
git add geckoterminal_scanner_v2.py
git commit -m "✅ Réactive anti-spam après backtesting (7 jours collecte)

Backtesting terminé: 800+ alertes analysées
Win rate amélioré: 20.9% → XX%

Réactivation anti-spam pour production:
- Re-alerte seulement si TP/±5%/4h/parabolique
- UX optimale pour utilisateur
- Évite spam Telegram

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin main
```

---

## 🚨 ROLLBACK D'URGENCE

**Si problème critique** (bot crashe, spam infini, etc.):

### Option 1: Revert Commit
```bash
git revert 416753f
git push origin main
```

### Option 2: Rollback Railway Dashboard
1. Aller sur Railway Dashboard
2. Cliquer "Deployments"
3. Trouver le deployment précédent (b741d94)
4. Cliquer "Redeploy"

### Option 3: Désactiver Temporairement
```bash
# Via Railway Shell
railway run pkill -f geckoterminal_scanner_v2.py
```

---

## 📞 SUPPORT

### Fichiers de Référence
- [BUGFIXES_CRITICAL_6.md](BUGFIXES_CRITICAL_6.md) - Documentation des 6 bugs
- [FIX_PEU_ALERTES.md](FIX_PEU_ALERTES.md) - Fix anti-spam
- [ANALYSE_EXPERT_COMPLETE.md](ANALYSE_EXPERT_COMPLETE.md) - Analyse complète

### Logs à Fournir (si problème)
```bash
railway logs > railway_logs.txt
```

---

## ✅ CHECKLIST POST-DEPLOY

### Immédiat (5-10 min)
- [ ] Railway build réussi
- [ ] Deployment actif
- [ ] Logs sans erreur Python
- [ ] Au moins 1 alerte reçue

### Court terme (30 min)
- [ ] 5-10 alertes reçues
- [ ] Sections WHALE ACTIVITY visibles
- [ ] PULLBACK SAIN détecté
- [ ] Scores 70+ → ENTRER

### Moyen terme (24h)
- [ ] 100+ alertes collectées
- [ ] Distribution scores normale
- [ ] Whales détectées (avg > 10)
- [ ] Aucun crash

### Long terme (7 jours)
- [ ] 800-1000 alertes collectées
- [ ] Backtest lancé
- [ ] Win rate amélioré
- [ ] Anti-spam réactivé

---

**Date**: 2025-12-19
**Commit**: 416753f
**Status**: ✅ DÉPLOYÉ - EN OBSERVATION
