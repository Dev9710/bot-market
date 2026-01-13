# GUIDE DE DÉPLOIEMENT - PRICE TRACKER SUR RAILWAY

**Date:** 2026-01-11
**Objectif:** Faire tourner le price tracker 24/7 même quand votre PC est éteint

---

## 🎯 SOLUTION: Déployer sur Railway

Railway va exécuter le script `price_tracker_cron_railway.py` automatiquement toutes les heures, 24h/24, 7j/7.

---

## 📋 ÉTAPES DE DÉPLOIEMENT

### Étape 1: Vérifier que les fichiers sont prêts

Les fichiers suivants ont été créés/modifiés:

- `price_tracker_cron_railway.py` - Script compatible PostgreSQL (Railway) et SQLite (local)
- `railway.toml` - Configuration Railway avec cron job
- `migrate_railway_db.py` - Script de migration base de données

### Étape 2: Commit et Push vers Railway

```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market

# Ajouter les nouveaux fichiers
git add price_tracker_cron_railway.py
git add migrate_railway_db.py
git add railway.toml
git add DEPLOIEMENT_PRICE_TRACKER.md

# Commit
git commit -m "Add price tracker cron job for Railway with database migration"

# Push vers Railway
git push
```

### Étape 3: Exécuter la migration sur Railway

**IMPORTANT:** Il faut ajouter les 18 nouvelles colonnes à la base PostgreSQL de Railway.

**Via Railway Dashboard:**

1. Aller sur https://railway.app
2. Ouvrir votre projet bot-market
3. Aller dans "Deployments"
4. Attendre que le déploiement soit terminé
5. Cliquer sur "..." → "Run Command"
6. Exécuter: `python migrate_railway_db.py`

**OU via Railway CLI:**

```bash
railway run python migrate_railway_db.py
```

Le script va:
- Vérifier les colonnes existantes
- Ajouter uniquement les colonnes manquantes (18 nouvelles)
- Afficher un rapport détaillé

### Étape 4: Vérifier que le cron job est actif

**Via Railway Dashboard:**

1. Aller dans votre projet Railway
2. Section "Settings" → "Cron Jobs"
3. Vous devriez voir:
   - Schedule: `0 * * * *` (toutes les heures)
   - Command: `python price_tracker_cron_railway.py`
   - Status: Active

**Via logs Railway:**

Les logs du cron job apparaîtront dans la section "Logs" de Railway.

Chaque heure, vous verrez:
```
================================================================================
PRICE TRACKER - 2026-01-11 14:00:00
Environment: PostgreSQL (Railway)
================================================================================

[1/4] Recuperation des alertes a tracker...
      OK 15 alertes a tracker

[2/4] Tracking des prix...
      Progress: 10/15
      OK 15 alertes trackees

[3/4] Cloture des alertes anciennes (>48h)...
      OK 2 alertes cloturees

[4/4] Resume:
      TP3 atteint: 8
      TP2 atteint: 3
      TP1 atteint: 2
      SL atteint: 0
      En cours: 2

================================================================================
TRACKING TERMINE
================================================================================
```

---

## 🔍 VÉRIFICATION

### Vérifier que la migration a fonctionné

Connectez-vous à la base Railway et exécutez:

```sql
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'alerts'
ORDER BY ordinal_position;
```

Vous devriez voir les 18 nouvelles colonnes.

### Vérifier que des données sont trackées

Après quelques heures:

```sql
-- Voir combien d'alertes ont été trackées
SELECT COUNT(*) FROM alerts WHERE price_1h_after IS NOT NULL;

-- Voir les alertes fermées
SELECT COUNT(*) FROM alerts WHERE is_closed = 1;

-- Distribution des résultats
SELECT final_outcome, COUNT(*)
FROM alerts
WHERE is_closed = 1
GROUP BY final_outcome;
```

---

## 📊 MONITORING

### Logs du cron job

Pour voir les logs du price tracker:

**Via Railway Dashboard:**
- Aller dans "Logs"
- Filtrer par "price_tracker"

**Via Railway CLI:**
```bash
railway logs --filter price_tracker
```

### Statistiques

Créez un endpoint dans votre dashboard pour voir les stats en temps réel:

```python
@app.route('/api/tracking-stats')
def tracking_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total tracked
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_closed = 1")
    total_closed = cursor.fetchone()[0]

    # Par outcome
    cursor.execute("""
        SELECT final_outcome, COUNT(*)
        FROM alerts
        WHERE is_closed = 1
        GROUP BY final_outcome
    """)
    outcomes = dict(cursor.fetchall())

    conn.close()

    return {
        'total_closed': total_closed,
        'outcomes': outcomes,
        'win_rate': (outcomes.get('WIN_TP1', 0) + outcomes.get('WIN_TP2', 0) + outcomes.get('WIN_TP3', 0)) / total_closed * 100 if total_closed > 0 else 0
    }
```

---

## ⚠️ IMPORTANT

### Dépendances Python

Assurez-vous que `requirements.txt` contient:

```
psycopg2-binary==2.9.9
requests==2.31.0
```

Si ce n'est pas le cas, ajoutez-les.

### Variables d'environnement

Railway doit avoir la variable `DATABASE_URL` configurée (déjà fait normalement).

Pour vérifier:
```bash
railway variables
```

Vous devriez voir:
```
DATABASE_URL=postgresql://...
```

---

## 🎯 RÉSULTAT FINAL

Après déploiement:

- Le price tracker tourne **24/7 sur Railway**
- Tracking automatique **toutes les heures**
- Votre PC peut être **éteint**
- Données sauvegardées dans **PostgreSQL Railway**
- Logs visibles dans **Railway Dashboard**

---

## 📈 PROCHAINES ÉTAPES

1. **Déployer** (suivre les étapes ci-dessus)
2. **Attendre 3-7 jours** pour accumuler des données
3. **Analyser** les résultats réels
4. **Comparer** avec le backtesting théorique
5. **Ajuster** les stratégies si nécessaire

---

## 🆘 TROUBLESHOOTING

### Le cron job ne se lance pas

- Vérifier que `railway.toml` est bien commit et push
- Redéployer le projet sur Railway
- Vérifier les logs pour les erreurs

### Erreur "DATABASE_URL not found"

- Vérifier que la variable d'environnement existe
- Railway l'ajoute automatiquement si vous avez un service PostgreSQL

### Erreur "relation 'alerts' does not exist"

- La table n'existe pas dans PostgreSQL Railway
- Vérifier que le bot a bien créé la table lors du premier lancement

### Erreur "column does not exist"

- La migration n'a pas été exécutée
- Relancer `python migrate_railway_db.py`

### API GeckoTerminal rate limit

- Le script limite déjà à 5 req/s
- Si trop d'alertes (>1000), le script prendra plusieurs minutes
- Normal, laisser terminer

---

## 📞 SUPPORT

Pour toute question:
- Vérifier les logs Railway
- Consulter `SESSION_SUMMARY.md`
- Consulter `BACKTESTING_REEL_SETUP.md`

---

**Guide créé le:** 2026-01-11
**Version:** 1.0
**Status:** Ready to deploy
