# 📊 Guide - DB Browser for SQLite

## 🎯 Solution Recommandée pour Consulter la DB en Local

**DB Browser for SQLite** est un outil **gratuit, open-source et facile à utiliser** pour consulter et modifier votre base de données SQLite.

---

## 📥 Installation (2 minutes)

### Windows

1. **Télécharger** depuis le site officiel :
   - https://sqlitebrowser.org/dl/
   - Choisir : **DB Browser for SQLite - Standard installer for 64-bit Windows**
   - Fichier : `DB.Browser.for.SQLite-3.12.2-win64.msi` (ou version plus récente)

2. **Installer** :
   - Double-cliquer sur le fichier téléchargé
   - Suivre l'assistant d'installation
   - Accepter les paramètres par défaut

3. **Lancer** :
   - Icône créée sur le bureau
   - Ou : Menu Démarrer → DB Browser (SQLite)

### Alternative : Version Portable (sans installation)

1. Télécharger : **Portable App (no installer)**
2. Décompresser le ZIP
3. Lancer `DB Browser for SQLite.exe`

---

## 🗂️ Ouvrir Votre Base de Données

### Méthode 1 : Via l'Interface

1. **Lancer DB Browser for SQLite**

2. **Ouvrir la base de données** :
   - Cliquer sur **"Ouvrir une base de données"** (ou File → Open Database)
   - Naviguer vers : `c:\Users\ludo_\Documents\projets\owner\bot-market\`
   - Sélectionner : `alerts_history.db`
   - Cliquer sur **"Ouvrir"**

### Méthode 2 : Glisser-Déposer

1. Lancer DB Browser for SQLite
2. Glisser le fichier `alerts_history.db` dans la fenêtre
3. → La DB s'ouvre automatiquement

### Méthode 3 : Double-clic

1. Clic droit sur `alerts_history.db`
2. **"Ouvrir avec"** → DB Browser for SQLite
3. → La DB s'ouvre directement

---

## 📊 Interface et Onglets

Une fois la DB ouverte, vous verrez **4 onglets principaux** :

### 1. Structure de la Base de Données

**Onglet : "Structure de la base de données"**

Affiche la structure des tables :
```
📁 alerts_history.db
  ├─ 📋 alerts (18 colonnes)
  ├─ 📋 price_tracking (11 colonnes)
  └─ 📋 alert_analysis (15 colonnes)
```

**Actions possibles** :
- Voir les colonnes de chaque table
- Voir les types de données
- Voir les contraintes (PRIMARY KEY, FOREIGN KEY)

### 2. Parcourir les Données

**Onglet : "Parcourir les données"**

C'est **l'onglet le plus utilisé** !

**Menu déroulant "Table"** :
- Sélectionner `alerts` → Voir toutes les alertes
- Sélectionner `price_tracking` → Voir tous les trackings
- Sélectionner `alert_analysis` → Voir toutes les analyses

**Fonctionnalités** :
- ✅ Voir toutes les lignes de la table
- ✅ Trier par colonne (clic sur l'en-tête)
- ✅ Filtrer (barre de recherche en haut)
- ✅ Modifier une cellule (double-clic)
- ✅ Exporter en CSV/JSON

**Exemple - Voir les dernières alertes** :
1. Table : `alerts`
2. Cliquer sur l'en-tête `timestamp` pour trier par date
3. → Les plus récentes en premier

### 3. Modifier la Base de Données

**Onglet : "Modifier la base de données"**

Permet de :
- Créer une nouvelle table
- Modifier une table existante
- Supprimer une table
- Ajouter/supprimer des colonnes

**⚠️ Attention** : Utilisez avec précaution, modifications irréversibles !

### 4. Exécuter SQL

**Onglet : "Exécuter le SQL"**

C'est là que vous pouvez **exécuter des requêtes SQL personnalisées**.

**Interface** :
```
┌─────────────────────────────────────┐
│ [Zone de texte SQL]                 │
│ SELECT * FROM alerts                │
│ WHERE score > 80                    │
│                                     │
│ [▶ Exécuter SQL]                   │
├─────────────────────────────────────┤
│ [Résultats de la requête]          │
│ id | timestamp | token_name | ...  │
│ 1  | 2025-...  | PEPE2.0   | ...  │
└─────────────────────────────────────┘
```

---

## 🔍 Requêtes SQL Utiles

### 1. Voir les 10 Dernières Alertes

```sql
SELECT
    id,
    timestamp,
    token_name,
    network,
    score,
    confidence_score,
    price_at_alert,
    volume_24h,
    liquidity
FROM alerts
ORDER BY timestamp DESC
LIMIT 10;
```

**Comment exécuter** :
1. Onglet **"Exécuter le SQL"**
2. Copier-coller la requête
3. Cliquer sur **▶ Exécuter SQL** (ou F5)
4. → Résultats affichés en bas

### 2. Alertes avec ROI > 10%

```sql
SELECT
    a.token_name,
    a.network,
    a.score,
    an.roi_at_24h,
    an.prediction_quality
FROM alerts a
JOIN alert_analysis an ON a.id = an.alert_id
WHERE an.roi_at_24h > 10
ORDER BY an.roi_at_24h DESC;
```

### 3. Statistiques Globales

```sql
SELECT
    COUNT(*) as total_alertes,
    AVG(score) as score_moyen,
    MIN(price_at_alert) as prix_min,
    MAX(price_at_alert) as prix_max
FROM alerts;
```

### 4. Performance par Réseau

```sql
SELECT
    a.network,
    COUNT(*) as nb_alertes,
    AVG(an.roi_at_24h) as roi_moyen,
    COUNT(CASE WHEN an.tp1_was_hit = 1 THEN 1 END) as tp1_atteints
FROM alerts a
LEFT JOIN alert_analysis an ON a.id = an.alert_id
GROUP BY a.network
ORDER BY nb_alertes DESC;
```

### 5. Tracking Complet d'une Alerte

```sql
-- Remplacer 1 par l'ID de votre alerte
SELECT
    pt.minutes_after_alert,
    pt.price,
    pt.roi_percent,
    pt.tp1_hit,
    pt.tp2_hit,
    pt.tp3_hit,
    pt.sl_hit
FROM price_tracking pt
WHERE pt.alert_id = 1
ORDER BY pt.minutes_after_alert;
```

### 6. Top 10 Meilleurs Tokens (ROI 24h)

```sql
SELECT
    a.token_name,
    a.network,
    a.score,
    an.roi_at_24h,
    an.prediction_quality
FROM alerts a
JOIN alert_analysis an ON a.id = an.alert_id
ORDER BY an.roi_at_24h DESC
LIMIT 10;
```

### 7. Alertes Cohérentes (Score élevé + ROI positif)

```sql
SELECT
    a.token_name,
    a.score,
    a.confidence_score,
    an.roi_at_24h,
    an.was_coherent,
    an.coherence_notes
FROM alerts a
JOIN alert_analysis an ON a.id = an.alert_id
WHERE an.was_coherent = 1
ORDER BY a.score DESC;
```

### 8. Tokens avec Plus de 2 Alertes

```sql
SELECT
    token_name,
    token_address,
    COUNT(*) as nb_alertes,
    AVG(score) as score_moyen,
    MAX(timestamp) as derniere_alerte
FROM alerts
GROUP BY token_address
HAVING nb_alertes > 2
ORDER BY nb_alertes DESC;
```

---

## 📤 Exporter les Données

### Méthode 1 : Export CSV (depuis "Parcourir les données")

1. **Onglet "Parcourir les données"**
2. Sélectionner la table (ex: `alerts`)
3. Filtrer si nécessaire
4. Cliquer sur **File → Export → Table as CSV file**
5. Choisir le nom du fichier
6. → Fichier CSV créé

### Méthode 2 : Export SQL (depuis "Exécuter le SQL")

1. **Onglet "Exécuter le SQL"**
2. Exécuter votre requête
3. Clic droit sur les résultats → **Copy as SQL**
4. Ou : **Export → Save results to CSV**

### Méthode 3 : Export Complet de la DB

1. **File → Export → Database to SQL file**
2. → Crée un fichier `.sql` avec toutes les données
3. Peut être réimporté plus tard

---

## 🔧 Fonctionnalités Avancées

### Filtrer les Données

**Dans "Parcourir les données"** :
1. Cliquer sur l'icône **🔍 Filtrer** dans une colonne
2. Entrer une condition (ex: `> 80` pour score > 80)
3. → Seules les lignes correspondantes s'affichent

### Modifier une Valeur

1. Double-cliquer sur une cellule
2. Modifier la valeur
3. Appuyer sur **Entrée**
4. **File → Write Changes** pour sauvegarder

**⚠️ Attention** : Les modifications sont permanentes !

### Créer un Index (Optimisation)

Si vos requêtes sont lentes :

1. **Onglet "Exécuter le SQL"**
2. Créer un index :
   ```sql
   CREATE INDEX idx_timestamp ON alerts(timestamp);
   CREATE INDEX idx_score ON alerts(score);
   ```
3. → Les requêtes sur `timestamp` et `score` seront plus rapides

### Vérifier l'Intégrité de la DB

1. **Onglet "Exécuter le SQL"**
2. Exécuter :
   ```sql
   PRAGMA integrity_check;
   ```
3. → Résultat : `ok` (tout va bien) ou liste d'erreurs

---

## 📊 Visualiser les Données

DB Browser inclut un **onglet "Graphique"** :

1. **Onglet "Exécuter le SQL"**
2. Exécuter une requête (ex: ROI par réseau)
3. Cliquer sur l'onglet **"Graphique"** en bas
4. Configurer :
   - **Axe X** : network
   - **Axe Y** : roi_moyen
   - **Type** : Bar Chart
5. → Graphique généré !

**Limitations** : Graphiques basiques (pour mieux, utilisez le Dashboard Streamlit)

---

## 🔄 Synchroniser avec Railway

### Télécharger la DB depuis Railway

```bash
# Via Railway CLI
railway run cat /data/alerts_history.db > alerts_railway.db
```

Ensuite, ouvrir `alerts_railway.db` dans DB Browser.

### Comparer Local vs Railway

1. Ouvrir `alerts_history.db` (local)
2. **Attach Database** :
   - File → Attach Database
   - Sélectionner `alerts_railway.db`
   - Nom : `railway`
3. Comparer :
   ```sql
   -- Nombre d'alertes local
   SELECT COUNT(*) FROM alerts;

   -- Nombre d'alertes Railway
   SELECT COUNT(*) FROM railway.alerts;
   ```

---

## 🛠️ Configuration Recommandée

### Paramètres Pratiques

**Edit → Preferences** :

1. **Data Browser** :
   - ✅ "Afficher les nombres avec séparateurs de milliers"
   - ✅ "Complétion automatique SQL"

2. **SQL** :
   - Font : Consolas 10pt (ou votre préférée)
   - ✅ "Coloration syntaxique"

3. **Extensions** :
   - Activer l'extension **JSON** si vous stockez du JSON

### Thème Sombre

**View → Preferences → General** :
- Theme : **Dark**
- → Interface en mode sombre (plus confortable)

---

## 📱 Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| **Ctrl + O** | Ouvrir une DB |
| **Ctrl + W** | Écrire les changements |
| **Ctrl + T** | Nouvelle table |
| **F5** | Exécuter SQL |
| **Ctrl + E** | Exporter en CSV |
| **Ctrl + R** | Rafraîchir |
| **Ctrl + F** | Rechercher |

---

## 🔍 Cas d'Usage Pratiques

### 1. Vérifier qu'une Alerte a Bien Été Sauvegardée

```sql
SELECT * FROM alerts
WHERE token_name = 'PEPE2.0'
ORDER BY timestamp DESC
LIMIT 1;
```

### 2. Voir si le Tracking a Fonctionné

```sql
SELECT
    a.token_name,
    COUNT(pt.id) as nb_trackings
FROM alerts a
LEFT JOIN price_tracking pt ON a.id = pt.alert_id
GROUP BY a.id
HAVING nb_trackings = 0;
```

Si résultat = vide → Tous les trackings ont fonctionné ✅

### 3. Analyser les Tokens qui Ont le Mieux Performé

```sql
SELECT
    a.token_name,
    a.network,
    a.score,
    an.roi_at_24h,
    an.best_roi_4h
FROM alerts a
JOIN alert_analysis an ON a.id = an.alert_id
WHERE an.roi_at_24h > 0
ORDER BY an.roi_at_24h DESC
LIMIT 20;
```

### 4. Identifier les Faux Positifs (Score élevé mais ROI négatif)

```sql
SELECT
    a.token_name,
    a.score,
    a.confidence_score,
    an.roi_at_24h,
    an.coherence_notes
FROM alerts a
JOIN alert_analysis an ON a.id = an.alert_id
WHERE a.score >= 80 AND an.roi_at_24h < 0;
```

---

## 📊 Comparaison : DB Browser vs Dashboard Streamlit

| Fonctionnalité | DB Browser | Dashboard Streamlit |
|----------------|------------|---------------------|
| **Installation** | Télécharger logiciel | Déployer sur Railway |
| **Accès** | Local uniquement | Web (partout) |
| **Interface** | Desktop app | Web moderne |
| **Requêtes SQL** | ✅ Complet | ❌ Pas de SQL direct |
| **Modification DB** | ✅ Oui | ❌ Lecture seule |
| **Graphiques** | ⚠️ Basiques | ✅ Plotly interactifs |
| **Mobile** | ❌ Non | ✅ Responsive |
| **Performance** | ✅ Rapide | ⚠️ Dépend connexion |
| **Export CSV** | ✅ Oui | ✅ Possible (à ajouter) |

**Recommandation** :
- **DB Browser** : Pour analyse approfondie, requêtes SQL, modifications
- **Dashboard Streamlit** : Pour consultation rapide, visualisation, accès mobile

---

## 🎯 Workflow Recommandé

### Usage Quotidien

1. **Dashboard Streamlit** (Railway)
   - Consulter les dernières alertes
   - Voir les statistiques globales
   - Graphiques de performance

### Analyse Approfondie

2. **DB Browser for SQLite** (Local)
   - Télécharger DB depuis Railway
   - Requêtes SQL personnalisées
   - Export CSV pour Excel
   - Modification si nécessaire

### Backup

3. **Sauvegarde Régulière**
   ```bash
   # Tous les jours/semaines
   railway run cat /data/alerts_history.db > backup_$(date +%Y%m%d).db
   ```

---

## ✅ Checklist d'Utilisation

**Première utilisation** :
- [ ] Télécharger DB Browser for SQLite
- [ ] Installer sur Windows
- [ ] Ouvrir `alerts_history.db`
- [ ] Explorer les 3 tables
- [ ] Tester quelques requêtes SQL

**Utilisation régulière** :
- [ ] Vérifier nouvelles alertes
- [ ] Analyser performances
- [ ] Exporter stats si nécessaire
- [ ] Télécharger DB Railway périodiquement

---

## 🆘 Dépannage

### "Impossible d'ouvrir la base de données"

**Cause** : Fichier verrouillé par un autre programme

**Solution** :
1. Fermer `geckoterminal_scanner_v2.py` (si en cours)
2. Fermer `dashboard.py` (si en cours)
3. Réessayer d'ouvrir avec DB Browser

### "Base de données vide"

**Cause** : Aucune alerte n'a encore été envoyée

**Solution** :
1. Lancer le scanner : `python geckoterminal_scanner_v2.py`
2. Attendre qu'une alerte soit envoyée
3. Rafraîchir DB Browser (Ctrl + R)

### "Erreur SQL"

**Cause** : Syntaxe SQL incorrecte

**Solution** :
1. Vérifier la syntaxe
2. Utiliser les exemples de ce guide
3. Copier-coller exactement

---

## 📚 Ressources

### Liens Utiles

- **Site officiel** : https://sqlitebrowser.org/
- **Documentation** : https://github.com/sqlitebrowser/sqlitebrowser/wiki
- **Tutoriels SQL** : https://www.sqlitetutorial.net/

### Tutoriels Vidéo

- YouTube : "DB Browser for SQLite tutorial"
- YouTube : "SQLite database tutorial"

---

## 🎉 Conclusion

**DB Browser for SQLite** est l'outil parfait pour :

✅ **Consulter** votre base de données localement
✅ **Analyser** en profondeur avec SQL
✅ **Exporter** les données en CSV/JSON
✅ **Modifier** la structure si nécessaire
✅ **Visualiser** rapidement (graphiques basiques)

**Combiné avec le Dashboard Streamlit**, vous avez :
- 🖥️ Analyse locale (DB Browser)
- 🌐 Consultation web (Dashboard)
- 📱 Accès mobile (Dashboard)

**Workflow optimal** : Dashboard pour le quotidien, DB Browser pour l'analyse approfondie ! 🚀

---

**Créé par** : Claude Sonnet 4.5
**Date** : 13 Décembre 2025
**Outil** : DB Browser for SQLite (gratuit & open-source)