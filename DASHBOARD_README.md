# Dashboard V3 - Guide de Démarrage

Dashboard web moderne pour visualiser les alertes du scanner V3 en temps réel.

---

## Architecture

```
┌─────────────────┐      API REST      ┌──────────────┐
│  Frontend HTML  │ ←──────────────────→ │  Flask API   │
│   (Vue.js)      │    HTTP/JSON       │  (Python)    │
└─────────────────┘                     └──────────────┘
                                              │
                                              ↓
                                        ┌──────────────┐
                                        │   SQLite DB  │
                                        │ (alerts.db)  │
                                        └──────────────┘
```

---

## Installation

### 1. Installer les dépendances

```bash
pip install -r requirements_dashboard.txt
```

Cela installe:
- `flask` - Framework web Python
- `flask-cors` - Support CORS pour les requêtes cross-origin

### 2. Vérifier la base de données

Le dashboard utilise la base de données créée par `alert_tracker.py`.

Vérifiez qu'elle existe:
```bash
ls alerts_tracker.db
```

Si elle n'existe pas, lancez le scanner V3 une fois pour la créer:
```bash
python geckoterminal_scanner_v3.py
```

---

## Démarrage

### 1. Lancer l'API Backend

Dans un terminal:

```bash
python dashboard_api.py
```

Vous devriez voir:
```
API Dashboard démarrée - DB: alerts_tracker.db
Endpoints disponibles:
  GET /api/health
  GET /api/alerts
  GET /api/stats
  GET /api/networks
  GET /api/alerts/:id
  GET /api/recent
 * Running on http://0.0.0.0:5000
```

L'API est maintenant accessible sur `http://localhost:5000`

### 2. Ouvrir le Dashboard Frontend

Ouvrez simplement le fichier HTML dans votre navigateur:

```bash
# Windows
start dashboard_frontend.html

# macOS
open dashboard_frontend.html

# Linux
xdg-open dashboard_frontend.html
```

Ou double-cliquez sur [dashboard_frontend.html](dashboard_frontend.html)

---

## Fonctionnalités du Dashboard

### 📊 Vue d'ensemble

- **Total alertes** - Nombre d'alertes dans la période sélectionnée
- **Score moyen** - Qualité moyenne des alertes
- **Liquidité moyenne** - Liquidité moyenne des pools détectés
- **Distribution par tier** - Répartition HIGH/MEDIUM/LOW

### 📈 Graphiques

1. **Distribution des Scores**
   - Barres montrant la répartition des scores (95-100, 90-94, etc.)
   - Codes couleur: Vert (excellent) → Rouge (faible)

2. **Alertes par Réseau**
   - Graphique en donut montrant la distribution ETH/BASE/BSC/SOLANA
   - Cliquer sur une section pour filtrer

3. **Timeline**
   - Graphique linéaire des alertes par jour
   - Permet de visualiser les tendances

### 🔍 Filtres

- **Période**: 1 jour, 7 jours, 30 jours, 90 jours
- **Réseau**: ETH, BASE, BSC, SOLANA
- **Tier**: ULTRA_HIGH, HIGH, MEDIUM, LOW
- **Score minimum**: Seuil personnalisé

### 📋 Table des Alertes

Tableau détaillé avec:
- Date de l'alerte
- Token (symbole + nom)
- Réseau avec badge coloré
- Score avec code couleur
- Tier (niveau de confiance)
- Vélocité pump
- Liquidité
- Âge du token
- Bouton détails pour vue modale

### 🔄 Rafraîchissement Auto

Le dashboard se rafraîchit automatiquement toutes les 60 secondes pour afficher les nouvelles alertes en temps réel.

---

## API Endpoints

### GET /api/health

Health check de l'API.

**Réponse**:
```json
{
  "status": "ok",
  "timestamp": "2025-01-15T10:30:00"
}
```

### GET /api/alerts

Liste des alertes avec filtres.

**Paramètres**:
- `network` (optionnel): eth, bsc, base, solana
- `tier` (optionnel): HIGH, MEDIUM, LOW
- `min_score` (optionnel): score minimum (0-100)
- `limit` (défaut 100): nombre max d'alertes
- `offset` (défaut 0): pagination
- `days` (défaut 7): alertes des N derniers jours

**Exemple**:
```bash
curl "http://localhost:5000/api/alerts?network=eth&min_score=90&days=7"
```

**Réponse**:
```json
{
  "alerts": [
    {
      "id": 1,
      "pool_address": "0x...",
      "network": "eth",
      "token_name": "Token Name",
      "token_symbol": "TKN",
      "score": 95,
      "tier": "HIGH",
      "price": 0.000123,
      "liquidity": 450000,
      "volume_24h": 1200000,
      "age_hours": 48.5,
      "velocite_pump": 125.3,
      "type_pump": "RAPIDE",
      "timestamp": "2025-01-15T10:00:00",
      "created_at": "2025-01-15T10:00:00"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

### GET /api/stats

Statistiques globales.

**Paramètres**:
- `days` (défaut 7): période en jours

**Réponse**:
```json
{
  "total_alerts": 244,
  "avg_score": 95.9,
  "avg_velocity": 126.4,
  "avg_liquidity": 412944,
  "by_tier": {
    "HIGH": 186,
    "MEDIUM": 58,
    "LOW": 0
  },
  "by_network": {
    "eth": { "count": 103, "avg_score": 95.4 },
    "solana": { "count": 94, "avg_score": 95.1 },
    "base": { "count": 30, "avg_score": 99.0 },
    "bsc": { "count": 17, "avg_score": 97.6 }
  },
  "score_distribution": {
    "95-100": 186,
    "90-94": 30,
    "85-89": 21,
    "80-84": 7,
    "<80": 0
  },
  "alerts_per_day": [
    { "date": "2025-01-15", "count": 3, "avg_score": 96.2 },
    { "date": "2025-01-14", "count": 2, "avg_score": 94.8 }
  ]
}
```

### GET /api/networks

Statistiques détaillées par réseau.

**Réponse**:
```json
{
  "networks": [
    {
      "network": "eth",
      "total": 103,
      "avg_score": 95.4,
      "avg_liquidity": 350000,
      "avg_volume": 1200000,
      "min_score": 85,
      "max_score": 100
    }
  ]
}
```

### GET /api/alerts/:id

Détail d'une alerte spécifique.

**Exemple**:
```bash
curl "http://localhost:5000/api/alerts/1"
```

### GET /api/recent

Alertes les plus récentes (temps réel).

**Paramètres**:
- `limit` (défaut 10): nombre d'alertes

**Exemple**:
```bash
curl "http://localhost:5000/api/recent?limit=5"
```

---

## Déploiement Production

### Option 1: Local (Développement)

Déjà configuré avec les étapes ci-dessus.

### Option 2: Railway (Production)

1. **Créer un nouveau service Railway pour l'API**:
   ```bash
   # Dans Railway, ajouter:
   # - Service "dashboard-api"
   # - Command: python dashboard_api.py
   # - Port: 5000
   ```

2. **Variables d'environnement Railway**:
   ```
   DATABASE_PATH=/app/alerts_tracker.db
   ```

3. **Partager la DB entre scanner et dashboard**:
   - Utiliser Railway Volumes pour partager `alerts_tracker.db`
   - Ou utiliser PostgreSQL pour une base partagée

### Option 3: Vercel/Netlify (Frontend seulement)

1. **Héberger le frontend**:
   - Upload `dashboard_frontend.html` sur Vercel/Netlify
   - Modifier `API_URL` dans le HTML pour pointer vers l'API Railway

2. **Exemple**:
   ```javascript
   // Dans dashboard_frontend.html
   API_URL: 'https://your-api.railway.app/api'
   ```

---

## Personnalisation

### Modifier les couleurs

Les couleurs sont gérées par Tailwind CSS. Exemples:

```javascript
// Score colors
getScoreColor(score) {
    if (score >= 95) return 'text-green-400';  // Changer en 'text-blue-400'
    // ...
}
```

### Ajouter des graphiques

Le dashboard utilise Chart.js. Exemple pour ajouter un graphique:

```javascript
const ctx = document.getElementById('myChart');
new Chart(ctx, {
    type: 'bar',  // 'line', 'doughnut', 'pie', etc.
    data: {
        labels: ['Label 1', 'Label 2'],
        datasets: [{
            label: 'Mon Dataset',
            data: [10, 20]
        }]
    }
});
```

### Modifier la période de rafraîchissement

Dans `dashboard_frontend.html`:

```javascript
mounted() {
    this.loadData();
    setInterval(() => this.loadData(), 60000); // 60000ms = 1 minute
}
```

Changer `60000` pour une autre valeur (en millisecondes).

---

## Troubleshooting

### ❌ "Error loading stats"

**Problème**: L'API n'est pas accessible

**Solution**:
1. Vérifier que l'API est lancée: `python dashboard_api.py`
2. Vérifier qu'elle écoute sur le bon port: `http://localhost:5000/api/health`
3. Vérifier les CORS (déjà configuré avec `flask-cors`)

### ❌ "Base de données non trouvée"

**Problème**: `alerts_tracker.db` n'existe pas

**Solution**:
Lancer le scanner V3 une fois pour créer la base:
```bash
python geckoterminal_scanner_v3.py
```

### ❌ Graphiques ne s'affichent pas

**Problème**: Chart.js n'est pas chargé

**Solution**:
Vérifier la connexion internet (Chart.js est chargé depuis CDN).

Ou télécharger Chart.js localement et modifier le HTML:
```html
<script src="./chart.min.js"></script>
```

### ❌ Données vides / "0 alertes"

**Problème**: Pas d'alertes dans la DB pour la période sélectionnée

**Solution**:
- Augmenter la période (passer de 7j à 30j ou 90j)
- Lancer le scanner V3 pour générer des alertes
- Vérifier que la DB contient des données:
  ```bash
  sqlite3 alerts_tracker.db "SELECT COUNT(*) FROM alerts;"
  ```

---

## Prochaines Améliorations

### V1.1 (Court terme)

- [ ] Export CSV/JSON des alertes
- [ ] Notifications push (WebSocket)
- [ ] Mode sombre/clair
- [ ] Favoris / watchlist tokens

### V1.2 (Moyen terme)

- [ ] Graphique de performance (Win Rate tracking)
- [ ] Comparaison période vs période
- [ ] Alertes email sur critères
- [ ] API webhook pour intégrations

### V2.0 (Long terme)

- [ ] Migration vers PostgreSQL
- [ ] Backend FastAPI avec async
- [ ] Frontend Next.js avec TypeScript
- [ ] Authentification utilisateurs
- [ ] Trading direct depuis dashboard

---

## Support

Pour toute question ou bug:
1. Vérifier les logs de l'API dans le terminal
2. Vérifier la console JavaScript du navigateur (F12)
3. Consulter la documentation de l'API ci-dessus

---

**Dashboard V3 - Prêt à visualiser tes alertes! 🚀**
