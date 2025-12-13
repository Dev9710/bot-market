# 💾 Comment Fonctionnent les Sauvegardes d'Alertes

## 🎯 Vue d'Ensemble

Chaque fois qu'une alerte Telegram est envoyée, le système :
1. ✅ Sauvegarde l'alerte dans la base de données SQLite
2. ✅ Lance automatiquement le tracking de prix (4 intervalles)
3. ✅ Analyse la performance après 24h

---

## 📊 Structure de la Base de Données

La base de données `alerts_history.db` contient **3 tables** :

### Table 1 : `alerts` (Alertes Principales)

**Quand** : Remplie immédiatement quand une alerte Telegram est envoyée

**Contenu** :
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                    -- Date/heure d'envoi

    -- Informations Token
    token_name TEXT NOT NULL,                   -- Nom du token (ex: "PEPE")
    token_address TEXT NOT NULL UNIQUE,         -- Adresse du contrat
    network TEXT NOT NULL,                      -- eth, bsc, arbitrum, etc.

    -- Prix et Scoring
    price_at_alert REAL NOT NULL,              -- Prix au moment de l'alerte
    score INTEGER NOT NULL,                     -- Score d'opportunité (0-100)
    base_score INTEGER,                         -- Score de base
    momentum_bonus INTEGER,                     -- Bonus momentum
    confidence_score INTEGER,                   -- Score de sécurité (0-100)

    -- Métriques du Token
    volume_24h REAL,                           -- Volume 24h en USD
    volume_6h REAL,                            -- Volume 6h en USD
    volume_1h REAL,                            -- Volume 1h en USD
    liquidity REAL,                            -- Liquidité en USD
    buys_24h INTEGER,                          -- Nombre d'achats 24h
    sells_24h INTEGER,                         -- Nombre de ventes 24h
    buy_ratio REAL,                            -- Ratio achats/ventes
    total_txns INTEGER,                        -- Total transactions 24h
    age_hours REAL,                            -- Age du token en heures

    -- Niveaux de Trading Calculés
    entry_price REAL NOT NULL,                 -- Prix d'entrée recommandé
    stop_loss_price REAL NOT NULL,             -- Prix stop loss
    stop_loss_percent REAL NOT NULL,           -- % stop loss (-10%)
    tp1_price REAL NOT NULL,                   -- Take Profit 1
    tp1_percent REAL NOT NULL,                 -- % TP1 (+5%)
    tp2_price REAL NOT NULL,                   -- Take Profit 2
    tp2_percent REAL NOT NULL,                 -- % TP2 (+10%)
    tp3_price REAL NOT NULL,                   -- Take Profit 3
    tp3_percent REAL NOT NULL,                 -- % TP3 (+15%)

    -- Message Complet
    alert_message TEXT                         -- Message Telegram envoyé
);
```

**Exemple de données** :
```json
{
    "id": 1,
    "timestamp": "2025-12-13 14:30:00",
    "token_name": "PEPE2.0",
    "token_address": "0x1234...",
    "network": "eth",
    "price_at_alert": 0.00000123,
    "score": 85,
    "confidence_score": 72,
    "volume_24h": 500000,
    "liquidity": 300000,
    "entry_price": 0.00000123,
    "stop_loss_price": 0.00000111,
    "tp1_price": 0.00000129,
    "tp2_price": 0.00000135,
    "tp3_price": 0.00000141
}
```

---

### Table 2 : `price_tracking` (Suivi des Prix)

**Quand** : Remplie à 15min, 1h, 4h, et 24h après l'alerte

**Contenu** :
```sql
CREATE TABLE price_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,                 -- Lien vers alerts.id
    timestamp TEXT NOT NULL,                   -- Date/heure du check
    minutes_after_alert INTEGER NOT NULL,      -- 15, 60, 240, ou 1440

    -- Prix et Performance
    price REAL,                                -- Prix actuel
    roi_percent REAL,                          -- ROI en % depuis l'alerte

    -- Détection TP/SL Touchés
    sl_hit INTEGER DEFAULT 0,                  -- 1 si SL touché
    tp1_hit INTEGER DEFAULT 0,                 -- 1 si TP1 touché
    tp2_hit INTEGER DEFAULT 0,                 -- 1 si TP2 touché
    tp3_hit INTEGER DEFAULT 0,                 -- 1 si TP3 touché

    -- Prix Min/Max
    highest_price REAL,                        -- Prix le plus haut atteint
    lowest_price REAL,                         -- Prix le plus bas atteint

    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);
```

**Exemple de données** :
```json
[
    {
        "id": 1,
        "alert_id": 1,
        "minutes_after_alert": 15,
        "price": 0.00000130,
        "roi_percent": 5.69,
        "tp1_hit": 1,
        "tp2_hit": 0
    },
    {
        "id": 2,
        "alert_id": 1,
        "minutes_after_alert": 60,
        "price": 0.00000145,
        "roi_percent": 17.89,
        "tp1_hit": 1,
        "tp2_hit": 1,
        "tp3_hit": 1
    }
]
```

---

### Table 3 : `alert_analysis` (Analyse de Performance)

**Quand** : Remplie après 24h pour analyser la performance globale

**Contenu** :
```sql
CREATE TABLE alert_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,                 -- Lien vers alerts.id
    timestamp TEXT NOT NULL,                   -- Date/heure de l'analyse

    -- Performance Globale
    was_profitable INTEGER,                    -- 1 si profitable, 0 sinon
    best_roi_4h REAL,                         -- Meilleur ROI dans les 4h
    worst_roi_4h REAL,                        -- Pire ROI dans les 4h
    roi_at_4h REAL,                           -- ROI à 4h précisément
    roi_at_24h REAL,                          -- ROI à 24h

    -- Atteinte des Objectifs
    tp1_was_hit INTEGER DEFAULT 0,            -- TP1 atteint à un moment?
    tp2_was_hit INTEGER DEFAULT 0,            -- TP2 atteint à un moment?
    tp3_was_hit INTEGER DEFAULT 0,            -- TP3 atteint à un moment?
    sl_was_hit INTEGER DEFAULT 0,             -- SL touché à un moment?

    -- Timing
    time_to_tp1 INTEGER,                      -- Minutes pour atteindre TP1
    time_to_tp2 INTEGER,                      -- Minutes pour atteindre TP2
    time_to_tp3 INTEGER,                      -- Minutes pour atteindre TP3
    time_to_sl INTEGER,                       -- Minutes pour toucher SL

    -- Qualité de la Prédiction
    prediction_quality TEXT,                   -- EXCELLENT/BON/MOYEN/MAUVAIS
    was_coherent INTEGER DEFAULT 0,            -- 1 si cohérent, 0 sinon
    coherence_notes TEXT,                      -- Explication de la cohérence

    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);
```

**Exemple de données** :
```json
{
    "id": 1,
    "alert_id": 1,
    "was_profitable": 1,
    "best_roi_4h": 25.30,
    "roi_at_24h": 12.50,
    "tp1_was_hit": 1,
    "tp2_was_hit": 1,
    "tp3_was_hit": 0,
    "time_to_tp1": 8,
    "time_to_tp2": 45,
    "prediction_quality": "BON",
    "was_coherent": 1,
    "coherence_notes": "Score élevé (85) confirmé par TP1/TP2 atteints"
}
```

---

## 🔄 Flux Complet de Sauvegarde

### Étape 1 : Token Détecté (dans `geckoterminal_scanner_v2.py`)

```python
# Le scanner GeckoTerminal trouve un nouveau token
opp = {
    "pool_data": {
        "name": "PEPE2.0",
        "base_token_address": "0x1234...",
        "network": "eth",
        "price_usd": 0.00000123,
        "volume_24h_usd": 500000,
        # ... autres données
    },
    "score": 85
}
```

### Étape 2 : Vérification de Sécurité

```python
# Ligne 1068 de geckoterminal_scanner_v2.py
security_result = security_checker.check_token_security(
    token_address="0x1234...",
    network="eth"
)

# Résultat:
{
    "security_score": 72,
    "is_safe": True,
    "checks": {
        "honeypot": {"is_honeypot": False},
        "lp_lock": {"is_locked": True},
        # ...
    }
}
```

### Étape 3 : Envoi Telegram (si sécurité OK)

```python
# Ligne 1101
if send_telegram(alert_msg):
    # ✅ Alerte envoyée avec succès
    # → Maintenant sauvegarder en DB
```

### Étape 4 : Préparation des Données (Lignes 1107-1144)

```python
# Calcul des niveaux de trading
price = 0.00000123
entry_price = price
stop_loss_price = price * 0.90  # -10%
tp1_price = price * 1.05        # +5%
tp2_price = price * 1.10        # +10%
tp3_price = price * 1.15        # +15%

alert_data = {
    'token_name': 'PEPE2.0',
    'token_address': '0x1234...',
    'network': 'eth',
    'price_at_alert': 0.00000123,
    'score': 85,
    'confidence_score': 72,
    'entry_price': entry_price,
    'stop_loss_price': stop_loss_price,
    'tp1_price': tp1_price,
    'tp2_price': tp2_price,
    'tp3_price': tp3_price,
    # ... toutes les autres données
}
```

### Étape 5 : Sauvegarde en DB (Ligne 1146)

```python
# Dans alert_tracker.py
alert_id = alert_tracker.save_alert(alert_data)
# → Retourne: 1 (ID de l'alerte créée)
```

**Ce qui se passe dans `save_alert()` :**

```python
def save_alert(self, alert_data: Dict) -> int:
    # 1. Insérer dans table alerts
    cursor.execute("""
        INSERT INTO alerts (
            timestamp, token_name, token_address, network,
            price_at_alert, score, confidence_score,
            entry_price, tp1_price, tp2_price, tp3_price, ...
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ...)
    """, (values...))

    alert_id = cursor.lastrowid  # Récupère l'ID auto-généré

    # 2. Lancer le tracking automatique (EN ARRIÈRE-PLAN)
    self.start_price_tracking(
        alert_id,
        alert_data['token_address'],
        alert_data['network'],
        alert_data['entry_price'],
        # ... niveaux TP/SL
    )

    return alert_id
```

### Étape 6 : Tracking Automatique (En Arrière-Plan)

```python
def start_price_tracking(self, alert_id, token_address, network, entry_price, ...):
    # Lancer 4 threads daemon (ne bloquent pas le programme)

    # Thread 1: Check à 15 minutes
    thread_15min = threading.Thread(
        target=self.update_price_tracking,
        args=(alert_id, token_address, network, 15, entry_price, ...)
    )
    thread_15min.daemon = True
    thread_15min.start()

    # Thread 2: Check à 1 heure
    # Thread 3: Check à 4 heures
    # Thread 4: Check à 24 heures + analyse complète
```

### Étape 7 : Check de Prix (à chaque intervalle)

**Exemple à 15 minutes :**

```python
def update_price_tracking(self, alert_id, token_address, network, minutes_after, ...):
    # 1. Attendre le délai
    time.sleep(minutes_after * 60)  # 15 * 60 = 900 secondes

    # 2. Récupérer le prix actuel
    current_price = self.fetch_current_price(token_address, network)
    # → API DexScreener retourne: 0.00000130

    # 3. Calculer le ROI
    roi = ((current_price - entry_price) / entry_price) * 100
    # → ((0.00000130 - 0.00000123) / 0.00000123) * 100 = +5.69%

    # 4. Vérifier si TP/SL touchés
    tp1_hit = 1 if current_price >= tp1_price else 0
    tp2_hit = 1 if current_price >= tp2_price else 0
    sl_hit = 1 if current_price <= sl_price else 0

    # 5. Sauvegarder dans price_tracking
    cursor.execute("""
        INSERT INTO price_tracking (
            alert_id, timestamp, minutes_after_alert,
            price, roi_percent,
            tp1_hit, tp2_hit, tp3_hit, sl_hit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (alert_id, now, 15, current_price, roi, tp1_hit, tp2_hit, 0, 0))

    print(f"📊 Tracking 15min - ROI: +5.69% - TP1 atteint!")
```

### Étape 8 : Analyse Finale (après 24h)

```python
def analyze_alert_performance(self, alert_id):
    # 1. Récupérer tous les trackings
    trackings = SELECT * FROM price_tracking WHERE alert_id = ?

    # 2. Calculer les métriques
    best_roi = max([t.roi_percent for t in trackings])      # +25.30%
    worst_roi = min([t.roi_percent for t in trackings])     # -3.20%
    roi_24h = trackings[-1].roi_percent                     # +12.50%

    # 3. Vérifier objectifs atteints
    tp1_hit = any([t.tp1_hit for t in trackings])  # True
    tp2_hit = any([t.tp2_hit for t in trackings])  # True
    tp3_hit = any([t.tp3_hit for t in trackings])  # False

    # 4. Timing
    time_to_tp1 = next(t for t in trackings if t.tp1_hit).minutes  # 8 min

    # 5. Qualité de prédiction
    if tp1_hit and tp2_hit and roi_24h > 10:
        quality = "BON"
    elif tp1_hit and roi_24h > 0:
        quality = "MOYEN"
    else:
        quality = "MAUVAIS"

    # 6. Cohérence score vs résultat
    coherent = (score >= 80 and roi_24h > 10) or (score < 50 and roi_24h < 0)

    # 7. Sauvegarder dans alert_analysis
    INSERT INTO alert_analysis (
        alert_id, was_profitable, best_roi_4h, roi_at_24h,
        tp1_was_hit, tp2_was_hit, time_to_tp1, time_to_tp2,
        prediction_quality, was_coherent, coherence_notes
    ) VALUES (...)
```

---

## 📊 Exemple de Cycle Complet

### Timeline d'une Alerte

```
T+0 min : 🔍 Token "PEPE2.0" détecté par scanner
          ├─ Score opportunité: 85/100
          ├─ Prix: $0.00000123
          └─ Volume 24h: $500,000

T+0 min : 🔒 Vérification sécurité
          ├─ Honeypot: ✅ Safe
          ├─ LP Lock: ✅ Locked (Unicrypt, 365 jours)
          ├─ Contract: ✅ Ownership renounced
          └─ Score sécurité: 72/100 → VALIDÉ

T+0 min : 📱 Envoi Telegram
          └─ Message envoyé avec succès

T+0 min : 💾 Sauvegarde en DB
          ├─ INSERT INTO alerts → ID: 1
          ├─ Entry: $0.00000123
          ├─ SL: $0.00000111 (-10%)
          ├─ TP1: $0.00000129 (+5%)
          ├─ TP2: $0.00000135 (+10%)
          └─ TP3: $0.00000141 (+15%)

T+0 min : 🚀 Lancement tracking (4 threads en arrière-plan)
          ├─ Thread 15min démarré
          ├─ Thread 1h démarré
          ├─ Thread 4h démarré
          └─ Thread 24h démarré

--- Le scanner continue normalement, threads en arrière-plan ---

T+15 min: 📊 Check automatique (Thread 15min)
          ├─ Prix actuel: $0.00000130
          ├─ ROI: +5.69%
          ├─ TP1 atteint: ✅
          └─ INSERT INTO price_tracking

T+1h    : 📊 Check automatique (Thread 1h)
          ├─ Prix actuel: $0.00000145
          ├─ ROI: +17.89%
          ├─ TP1/TP2/TP3 atteints: ✅✅✅
          └─ INSERT INTO price_tracking

T+4h    : 📊 Check automatique (Thread 4h)
          ├─ Prix actuel: $0.00000138
          ├─ ROI: +12.20%
          ├─ TP1/TP2 encore actifs: ✅✅
          └─ INSERT INTO price_tracking

T+24h   : 📊 Check final + Analyse complète
          ├─ Prix actuel: $0.00000141
          ├─ ROI final: +14.63%
          ├─ Meilleur ROI (4h): +25.30%
          ├─ Pire ROI (4h): -3.20%
          ├─ TP1 atteint en: 8 minutes
          ├─ TP2 atteint en: 45 minutes
          ├─ TP3 atteint en: 72 minutes
          ├─ Qualité: BON
          ├─ Cohérent: ✅ (Score 85 → ROI +14%)
          └─ INSERT INTO alert_analysis
```

---

## 🔍 Consulter les Données

### Requête SQL : Dernières Alertes

```sql
SELECT
    id,
    timestamp,
    token_name,
    network,
    score,
    confidence_score,
    price_at_alert,
    entry_price,
    tp1_price,
    tp2_price
FROM alerts
ORDER BY timestamp DESC
LIMIT 10;
```

### Requête SQL : Performance d'une Alerte

```sql
-- Alerte + Tous ses trackings + Analyse
SELECT
    a.token_name,
    a.score,
    p.minutes_after_alert,
    p.roi_percent,
    p.tp1_hit,
    p.tp2_hit,
    an.prediction_quality
FROM alerts a
LEFT JOIN price_tracking p ON a.id = p.alert_id
LEFT JOIN alert_analysis an ON a.id = an.alert_id
WHERE a.id = 1
ORDER BY p.minutes_after_alert;
```

### Requête SQL : Statistiques Globales

```sql
SELECT
    COUNT(*) as total_alerts,
    AVG(score) as avg_score,
    COUNT(CASE WHEN an.roi_at_24h > 0 THEN 1 END) as profitable_count,
    AVG(an.roi_at_24h) as avg_roi_24h,
    COUNT(CASE WHEN an.tp1_was_hit = 1 THEN 1 END) * 100.0 / COUNT(*) as tp1_rate
FROM alerts a
LEFT JOIN alert_analysis an ON a.id = an.alert_id;
```

---

## ✅ Points Clés à Retenir

1. **Sauvegarde Automatique** : Dès qu'une alerte Telegram est envoyée
2. **Tracking Automatique** : 4 vérifications programmées (15min, 1h, 4h, 24h)
3. **Threads en Arrière-Plan** : Le scanner continue pendant les trackings
4. **3 Tables** : alerts (alerte initiale), price_tracking (suivi), alert_analysis (analyse finale)
5. **Persistance** : Toutes les données restent en DB même si le bot redémarre
6. **Analyse Automatique** : Qualité de prédiction calculée après 24h

---

**La prochaine étape** : Mettre en place un accès à cette DB depuis Railway (voir [ACCES_DB_RAILWAY.md](ACCES_DB_RAILWAY.md))