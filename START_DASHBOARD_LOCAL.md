# Démarrer le Dashboard en Local avec Données Réelles

## 🎯 Objectif

Faire tourner le scanner V3 localement pour collecter de vraies alertes, puis visualiser dans le dashboard.

---

## Étape 1: Préparer le Scanner

Le scanner V3 est déjà configuré pour écrire dans `alerts_live.json` automatiquement.

**Vérifications**:
1. ✅ `json_alert_writer.py` existe
2. ✅ Scanner V3 importe `JSONAlertWriter` (ligne 37)
3. ✅ Scanner initialise `json_writer` dans `main()` (ligne 3172)
4. ✅ Scanner sauvegarde alertes dans JSON (ligne 3028)

---

## Étape 2: Lancer le Scanner V3

### Option A: Mode Normal (Scan Continu)

**Terminal 1** - Scanner:
```bash
cd c:\Users\ludo_\Documents\projets\owner\bot-market
python geckoterminal_scanner_v3.py
```

Le scanner va:
1. Scanner GeckoTerminal toutes les 5 minutes
2. Détecter des opportunités
3. Filtrer avec config ULTRA_RENTABLE (très strict)
4. Sauvegarder les alertes valides dans `alerts_live.json`
5. Envoyer notification Telegram

**Temps d'attente**: ~1-2h pour avoir les premières alertes (config stricte = 2.7/jour)

### Option B: Mode Test Rapide (Données Historiques)

Si tu veux tester le dashboard **immédiatement**, on peut importer les alertes depuis la base Railway:

**Créer un script d'import**:
```python
# import_railway_alerts.py
import json
import sqlite3
from datetime import datetime

# Connexion à la DB Railway exportée
conn = sqlite3.connect('alerts_railway_export.db')
cursor = conn.execute("""
    SELECT
        pool_address, network, token_name, token_symbol,
        score, tier, price, liquidity, volume_24h,
        age_hours, created_at
    FROM alerts
    ORDER BY created_at DESC
    LIMIT 100
""")

alerts = []
for row in cursor.fetchall():
    alert_data = json.loads(row[11]) if len(row) > 11 else {}

    alerts.append({
        'pool_address': row[0],
        'network': row[1],
        'token_name': row[2],
        'token_symbol': row[3],
        'score': row[4],
        'tier': row[5],
        'price': row[6],
        'liquidity': row[7],
        'volume_24h': row[8],
        'age_hours': row[9],
        'velocite_pump': alert_data.get('velocite_pump', 0),
        'type_pump': alert_data.get('type_pump', ''),
        'created_at': row[10]
    })

with open('alerts_live.json', 'w', encoding='utf-8') as f:
    json.dump(alerts, f, indent=2, ensure_ascii=False)

print(f"✅ {len(alerts)} alertes importées dans alerts_live.json")
```

Mais **MIEUX**: On peut utiliser le fichier d'export JSON que tu as déjà!

---

## Étape 3: Convertir les Alertes Railway Existantes

Tu as déjà un export des alertes Railway. Convertissons-le au format du dashboard:

**Script de conversion**:
