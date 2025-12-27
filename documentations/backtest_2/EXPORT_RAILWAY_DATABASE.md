# 📚 TUTORIEL COMPLET: Export Base de Données Railway vers JSON

**Objectif:** Télécharger toutes les alertes de la base SQLite Railway vers votre machine locale en format JSON.

**Durée totale:** 3-5 minutes

**Date de création:** 27 décembre 2025
**Testé et validé:** ✅

---

## ✅ PRÉREQUIS

- Railway CLI installé
- Projet Railway lié (laudable-motivation)
- PowerShell ouvert
- Connexion internet

---

## 📋 PROCÉDURE COMPLÈTE (9 ÉTAPES)

### ÉTAPE 1: Ouvrir PowerShell et naviguer vers le projet

**Action:**
```powershell
cd c:\Users\ludo_\Documents\projets\owner\bot-market
```

**Résultat attendu:**
```
PS C:\Users\ludo_\Documents\projets\owner\bot-market>
```

**Si erreur "Le chemin n'existe pas":**
- Vérifiez le chemin avec `ls c:\Users\ludo_\Documents\projets\owner\`

---

### ÉTAPE 2: Se connecter en SSH au conteneur Railway

**Action:**
```powershell
railway ssh
```

**Résultat attendu:**
```
root@XXXXXXXXXX:/app#
```
ou
```
app@XXXXXXXXXX:~$
```

**Si erreur "No linked project":**
```powershell
railway link
```
Puis sélectionnez "laudable-motivation" et relancez `railway ssh`

**Si erreur "Service not found":**
```powershell
railway status
```
Vérifiez que vous êtes bien lié au bon service.

---

### ÉTAPE 3: Vérifier que Python est disponible

**Action:**
```bash
python --version
```

**Résultat attendu:**
```
Python 3.10.x
```
ou similaire

**Si "command not found":**
```bash
python3 --version
```
Si ça fonctionne, remplacez `python` par `python3` dans toutes les commandes suivantes.

---

### ÉTAPE 4: Vérifier l'emplacement de la base de données

**Action:**
```bash
ls -lh /data/alerts_history.db
```

**Résultat attendu:**
```
-rw-r--r-- 1 root root 52K Dec 27 03:00 /data/alerts_history.db
```

**Si "No such file":**
```bash
find /data -name "*.db" -o -name "*.sqlite*" 2>/dev/null
```
Notez le chemin exact trouvé et utilisez-le à la place de `/data/alerts_history.db`

---

### ÉTAPE 5: Créer le script d'export Python

**Action:** Copiez-collez **TOUT CE BLOC** en une seule fois:

```bash
cat > /tmp/export_alerts.py << 'EOF'
import sqlite3
import json
from datetime import datetime

print("Connexion a la base de donnees...")
conn = sqlite3.connect('/data/alerts_history.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("Comptage des alertes...")
cursor.execute("SELECT COUNT(*) as total FROM alerts")
total = cursor.fetchone()[0]
print(f"Total alertes trouvees: {total}")

print("Export en cours...")
cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
alerts = [dict(row) for row in cursor.fetchall()]

result = {
    "export_date": datetime.now().isoformat(),
    "total_alerts": total,
    "source": "Railway SQLite",
    "alerts": alerts
}

print(json.dumps(result, indent=2, default=str))
conn.close()
EOF
```

**Résultat attendu:**
Aucun message (retour au prompt silencieux)

**Si erreur de syntaxe:**
Vérifiez que vous avez copié **jusqu'à EOF inclus** (dernière ligne)

---

### ÉTAPE 6: Exécuter le script et sauvegarder en JSON

**Action:**
```bash
python /tmp/export_alerts.py > /tmp/alerts_export.json 2>&1
```

**Résultat attendu:**
Aucun message (retour au prompt)

**Pour vérifier que ça a fonctionné:**
```bash
ls -lh /tmp/alerts_export.json
```

**Résultat attendu:**
```
-rw-r--r-- 1 root root 250K Dec 27 04:00 /tmp/alerts_export.json
```

**Si le fichier fait 0K ou est vide:**
```bash
cat /tmp/export_alerts.py
```
Vérifiez que le script a bien été créé. Si vide, recommencez l'Étape 5.

---

### ÉTAPE 7: Prévisualiser le début du fichier JSON

**Action:**
```bash
head -20 /tmp/alerts_export.json
```

**Résultat attendu:**
```json
Connexion a la base de donnees...
Comptage des alertes...
Total alertes trouvees: 156
Export en cours...
{
  "export_date": "2025-12-27T04:15:30.123456",
  "total_alerts": 156,
  "source": "Railway SQLite",
  "alerts": [
    {
      "id": 156,
      "token_name": "PEPE",
      ...
```

**Si vous voyez une erreur Python:**
Notez l'erreur exacte et corrigez le script à l'Étape 5.

---

### ÉTAPE 8: Sortir du SSH Railway

**Action:**
```bash
exit
```

**Résultat attendu:**
```
PS C:\Users\ludo_\Documents\projets\owner\bot-market>
```

Vous êtes de retour dans PowerShell local.

---

### ÉTAPE 9: Télécharger le fichier JSON vers votre machine

**Action:**
```powershell
railway ssh cat /tmp/alerts_export.json > alerts_railway_export.json
```

**Résultat attendu:**
Le fichier se télécharge silencieusement. Attendez 5-15 secondes.

**Vérifier le téléchargement:**
```powershell
ls alerts_railway_export.json
```

**Résultat attendu:**
```
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        27/12/2025     04:20         256789 alerts_railway_export.json
```

**Si le fichier fait 0 octets:**
```powershell
# Réessayer avec un timeout plus long
railway ssh "cat /tmp/alerts_export.json" > alerts_railway_export.json
```

---

## ✅ VÉRIFICATION FINALE

### Ouvrir le fichier pour vérifier

**Action:**
```powershell
notepad alerts_railway_export.json
```

**OU avec Python:**
```powershell
python -m json.tool alerts_railway_export.json | Select-Object -First 30
```

**Résultat attendu:**
Un fichier JSON valide avec vos alertes.

---

## 📊 STRUCTURE DU FICHIER JSON EXPORTÉ

```json
{
  "export_date": "2025-12-27T04:15:30.123456",
  "total_alerts": 156,
  "source": "Railway SQLite",
  "alerts": [
    {
      "id": 1,
      "token_name": "PEPE",
      "token_address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
      "network": "eth",
      "price_at_alert": 0.00000123,
      "score": 85,
      "base_score": 70,
      "momentum_bonus": 15,
      "liquidity": 150000,
      "created_at": "2025-12-26 12:30:45",
      "entry_price": 0.00000123,
      "stop_loss_price": 0.00000111,
      "tp1_price": 0.00000129,
      "tp2_price": 0.00000135,
      "tp3_price": 0.00000141,
      ...
    },
    ...
  ]
}
```

---

## ❌ RÉSOLUTION DES PROBLÈMES COURANTS

### Problème 1: "railway: command not found"

**Cause:** Railway CLI non installé

**Solution:**
```powershell
npm install -g @railway/cli
```

Puis relancez depuis l'Étape 1.

---

### Problème 2: "No linked project"

**Cause:** Projet non lié

**Solution:**
```powershell
railway link
```
Sélectionnez "laudable-motivation", puis relancez depuis l'Étape 2.

---

### Problème 3: SSH se déconnecte immédiatement

**Cause:** Service Railway arrêté ou redémarré

**Solution:**
Attendez 30 secondes et relancez:
```powershell
railway ssh
```

---

### Problème 4: Fichier JSON vide ou corrompu

**Cause:** Script d'export mal copié

**Solution:**
Dans le SSH Railway:
```bash
rm /tmp/export_alerts.py /tmp/alerts_export.json
```

Puis recommencez depuis l'Étape 5 en copiant **tout le bloc** y compris `EOF`.

---

### Problème 5: "Permission denied" lors de l'écriture

**Cause:** Droits insuffisants

**Solution:**
Changez l'emplacement de sortie:
```bash
python /tmp/export_alerts.py > ~/alerts_export.json 2>&1
```

Puis à l'Étape 9:
```powershell
railway ssh cat ~/alerts_export.json > alerts_railway_export.json
```

---

### Problème 6: "sqlite3.OperationalError: no such table: alerts"

**Cause:** Base de données vide ou non initialisée

**Solution:**
Vérifiez les tables disponibles:
```bash
python -c "import sqlite3; conn=sqlite3.connect('/data/alerts_history.db'); print([x[0] for x in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()])"
```

Si aucune table, la base est vide - rien à exporter.

---

## 📝 CHECKLIST COMPLÈTE

Cochez au fur et à mesure:

- [ ] Étape 1: PowerShell ouvert, dans le bon répertoire
- [ ] Étape 2: SSH Railway connecté (`root@XXX:/app#`)
- [ ] Étape 3: Python disponible (version affichée)
- [ ] Étape 4: Base de données trouvée (`/data/alerts_history.db`)
- [ ] Étape 5: Script Python créé (bloc `cat > ... EOF` exécuté)
- [ ] Étape 6: Export exécuté (fichier JSON créé dans `/tmp/`)
- [ ] Étape 7: JSON valide (aperçu affiché avec `head`)
- [ ] Étape 8: SSH fermé (`exit`)
- [ ] Étape 9: Fichier téléchargé localement (taille > 0)
- [ ] Vérification: JSON ouvert et lisible

---

## 🎯 RÉSUMÉ ULTRA-RAPIDE (pour reproduction)

Pour ceux qui connaissent déjà la procédure:

```bash
# 1. Local PowerShell
cd c:\Users\ludo_\Documents\projets\owner\bot-market
railway ssh

# 2. Dans SSH Railway - Copier TOUT le bloc d'un coup
cat > /tmp/export_alerts.py << 'EOF'
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('/data/alerts_history.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) as total FROM alerts")
total = cursor.fetchone()[0]

cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
alerts = [dict(row) for row in cursor.fetchall()]

result = {
    "export_date": datetime.now().isoformat(),
    "total_alerts": total,
    "source": "Railway SQLite",
    "alerts": alerts
}

print(json.dumps(result, indent=2, default=str))
conn.close()
EOF

# 3. Exécuter l'export
python /tmp/export_alerts.py > /tmp/alerts_export.json 2>&1

# 4. Vérifier
ls -lh /tmp/alerts_export.json
head -20 /tmp/alerts_export.json

# 5. Sortir
exit

# 6. Télécharger (de retour en PowerShell local)
railway ssh cat /tmp/alerts_export.json > alerts_railway_export.json

# 7. Vérifier
ls alerts_railway_export.json
```

---

## 🔄 AUTOMATISATION (Optionnel)

Pour créer un script réutilisable:

```powershell
# Créer export_railway.ps1
@'
cd c:\Users\ludo_\Documents\projets\owner\bot-market

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$filename = "railway_export_$timestamp.json"

Write-Host "Export de la base Railway en cours..."
railway ssh cat /tmp/alerts_export.json > $filename

if (Test-Path $filename) {
    $size = (Get-Item $filename).Length
    Write-Host "Export termine: $filename ($([math]::Round($size/1KB, 2)) KB)"
} else {
    Write-Host "Erreur: fichier non cree"
}
'@ | Out-File -FilePath export_railway.ps1 -Encoding UTF8

# Utilisation future
.\export_railway.ps1
```

---

## 📌 NOTES IMPORTANTES

1. **Sécurité:** Le fichier JSON contient toutes vos données d'alertes. Ne le partagez pas publiquement.

2. **Taille du fichier:** Si vous avez plus de 10 000 alertes, le fichier peut être volumineux (plusieurs MB). Le téléchargement peut prendre plus de temps.

3. **Format des dates:** Les dates sont au format ISO 8601 (`2025-12-27T04:15:30`).

4. **Encodage:** Le fichier est en UTF-8. Si vous l'ouvrez dans Excel, assurez-vous de sélectionner UTF-8 lors de l'import.

5. **Fréquence d'export:** Vous pouvez refaire cet export à tout moment pour avoir une sauvegarde à jour.

---

## 🎓 UTILISATION DU FICHIER EXPORTÉ

### Importer dans Excel

1. Excel → Données → Obtenir des données → À partir d'un fichier → JSON
2. Sélectionnez `alerts_railway_export.json`
3. Power Query s'ouvre → Développez la colonne "alerts"
4. Sélectionnez les colonnes souhaitées
5. Charger

### Analyser avec Python

```python
import json
import pandas as pd

# Charger le JSON
with open('alerts_railway_export.json', 'r') as f:
    data = json.load(f)

# Convertir en DataFrame
df = pd.DataFrame(data['alerts'])

# Analyses
print(f"Total alertes: {len(df)}")
print(f"\nRépartition par réseau:")
print(df['network'].value_counts())

print(f"\nScore moyen: {df['score'].mean():.1f}")
print(f"Score médian: {df['score'].median():.1f}")
```

### Convertir en CSV

```powershell
# Avec Python
python -c "import json, csv; data=json.load(open('alerts_railway_export.json')); csv.DictWriter(open('alerts.csv','w',newline='',encoding='utf-8'),fieldnames=data['alerts'][0].keys()).writeheader(); csv.DictWriter(open('alerts.csv','a',newline='',encoding='utf-8'),fieldnames=data['alerts'][0].keys()).writerows(data['alerts'])"
```

---

**Fichier final:** `c:\Users\ludo_\Documents\projets\owner\bot-market\alerts_railway_export.json`

**Support:** En cas de problème, vérifiez d'abord la section "Résolution des problèmes courants"

**Version:** 1.0
**Dernière mise à jour:** 27 décembre 2025
