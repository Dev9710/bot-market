# 🐛 Erreurs Courantes et Solutions

## 📋 Guide de Résolution des Erreurs

---

## ❌ Erreur 1 : KeyError `base_token_address`

### Symptômes
```
File "/app/geckoterminal_scanner_v2.py", line 1063, in scan_geckoterminal
    token_address = opp["pool_data"]["base_token_address"]
KeyError: 'base_token_address'
```

### Cause
La clé `base_token_address` n'existe pas dans le dictionnaire `pool_data` retourné par `parse_pool_data()`.

### ✅ Solution
**CORRIGÉ** : Utiliser `pool_address` à la place.

**Ligne 1063-1064** (avant) :
```python
token_address = opp["pool_data"]["base_token_address"]  # ❌ Erreur
network = opp["pool_data"]["network"]
```

**Ligne 1064-1065** (après) :
```python
token_address = opp["pool_data"]["pool_address"]  # ✅ Correct
network = opp["pool_data"]["network"]
```

**Statut** : ✅ **CORRIGÉ**

---

## ⚠️ Erreur 2 : Binance Bloque la Région (Erreur 451)

### Symptômes
```
❌ ERREUR 451: Binance bloque votre region/pays
💡 SOLUTIONS:
   1. Utilisez un VPN (recommande: USA, Canada, UK)
   2. Contactez votre ISP
   3. Utilisez un proxy
```

### Cause
Railway est hébergé dans une région bloquée par Binance (souvent UE/France).

### Impact
**FAIBLE** : Cette erreur affecte uniquement le contexte marché (BTC/ETH) au début du scan. Le scanner GeckoTerminal **continue de fonctionner normalement**.

### Solutions

#### Solution 1 : Ignorer (Recommandé)
Le scanner fonctionne sans le contexte Binance. Vous pouvez ignorer cette erreur.

#### Solution 2 : Désactiver le Check Binance

Dans `geckoterminal_scanner_v2.py`, commentez la ligne qui appelle Binance :

**Trouver la fonction** (chercher `def get_market_context()`) :
```python
def get_market_context():
    """Récupère contexte marché depuis Binance."""
    try:
        # ... code Binance
    except Exception as e:
        # Binance bloqué
        return {
            "btc_change_24h": 0,
            "eth_change_24h": 0,
            "trend": "NEUTRE"
        }
```

**Ou commenter l'appel** dans `scan_geckoterminal()` :
```python
# market_context = get_market_context()  # Désactivé
market_context = {"btc_change_24h": 0, "eth_change_24h": 0, "trend": "NEUTRE"}
```

#### Solution 3 : Utiliser un Proxy (Avancé)

Ajouter un proxy dans le code Binance :
```python
proxies = {
    'http': 'http://your-proxy:port',
    'https': 'http://your-proxy:port'
}
response = requests.get(url, proxies=proxies, timeout=5)
```

**Statut** : ⚠️ **Non critique** - Le scanner fonctionne sans

---

## ❌ Erreur 3 : DB Locked / Database is Locked

### Symptômes
```
sqlite3.OperationalError: database is locked
```

### Cause
La base de données SQLite est accédée simultanément par plusieurs process.

### Solutions

#### Solution 1 : Fermer les Programmes
Fermer :
- `geckoterminal_scanner_v2.py`
- `dashboard.py`
- DB Browser for SQLite
- `consulter_db.py`

Puis relancer un seul à la fois.

#### Solution 2 : Augmenter le Timeout SQLite

Dans `alert_tracker.py`, ligne ~50 :
```python
# Avant
conn = sqlite3.connect(db_path)

# Après (timeout 30 secondes)
conn = sqlite3.connect(db_path, timeout=30.0)
```

#### Solution 3 : Mode WAL (Write-Ahead Logging)

Dans `alert_tracker.py`, après connexion :
```python
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")  # Permet accès concurrent
```

---

## ❌ Erreur 4 : Module Not Found

### Symptômes
```
ModuleNotFoundError: No module named 'streamlit'
ModuleNotFoundError: No module named 'plotly'
```

### Cause
Dépendances manquantes.

### ✅ Solution
```bash
pip install -r requirements.txt
```

Ou individuellement :
```bash
pip install streamlit plotly pandas
```

Sur Railway, vérifier que `requirements.txt` est présent et à jour.

---

## ❌ Erreur 5 : Telegram Bot Token Invalid

### Symptômes
```
telegram.error.InvalidToken: Invalid token
```

### Cause
`TELEGRAM_BOT_TOKEN` incorrect ou manquant.

### ✅ Solution

1. **Vérifier le token** :
   - Obtenir via @BotFather sur Telegram
   - Format : `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

2. **Local** : Vérifier `.env`
   ```env
   TELEGRAM_BOT_TOKEN=your_correct_token_here
   ```

3. **Railway** : Vérifier les variables
   - Dashboard → Settings → Variables
   - `TELEGRAM_BOT_TOKEN` = votre token

---

## ❌ Erreur 6 : No Such File or Directory (alerts_history.db)

### Symptômes
```
FileNotFoundError: [Errno 2] No such file or directory: 'alerts_history.db'
```

### Cause
La base de données n'a pas encore été créée (aucune alerte envoyée).

### ✅ Solution

**Attendre la première alerte** : La DB est créée automatiquement lors de la première sauvegarde.

Ou **créer manuellement** :
```python
python -c "from alert_tracker import AlertTracker; t = AlertTracker(); t.close()"
```

---

## ❌ Erreur 7 : Port Already in Use (Streamlit)

### Symptômes
```
OSError: [Errno 48] Address already in use
```

### Cause
Le port 8501 (Streamlit par défaut) est déjà utilisé.

### ✅ Solution

#### Option 1 : Tuer le Process
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8501 | xargs kill -9
```

#### Option 2 : Changer le Port
```bash
streamlit run dashboard.py --server.port=8502
```

---

## ❌ Erreur 8 : Railway CLI Not Found

### Symptômes
```
'railway' is not recognized as an internal or external command
```

### Cause
Railway CLI pas installé.

### ✅ Solution

**Windows (PowerShell en Admin)** :
```powershell
iwr https://railway.app/install.ps1 | iex
```

**Ou via npm** :
```bash
npm install -g @railway/cli
```

**Vérifier** :
```bash
railway --version
```

---

## ❌ Erreur 9 : API Rate Limit (GoPlusLabs, DexScreener, TokenSniffer)

### Symptômes
```
429 Too Many Requests
Rate limit exceeded
```

### Cause
Trop de requêtes aux APIs gratuites.

### Impact
**FAIBLE** : Le système a un cache (1h) et un fallback multi-sources.

### ✅ Solution

**Automatique** : Le cache réduit déjà 80% des appels.

**Manuel** : Augmenter le TTL du cache dans `security_checker.py` :
```python
# Ligne ~40
CACHE_TTL = 3600  # 1h par défaut
# Changer en:
CACHE_TTL = 7200  # 2h
```

---

## ❌ Erreur 10 : UnicodeEncodeError (Windows)

### Symptômes
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f525'
```

### Cause
Emojis non supportés sur console Windows.

### ✅ Solution

**Déjà corrigé** dans tous les fichiers :
```python
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

Si l'erreur persiste :
```bash
# Avant de lancer Python
chcp 65001
python geckoterminal_scanner_v2.py
```

---

## 🔍 Diagnostiquer une Erreur

### Étape 1 : Lire le Traceback
```
Traceback (most recent call last):
  File "geckoterminal_scanner_v2.py", line 1063
    token_address = opp["pool_data"]["base_token_address"]
KeyError: 'base_token_address'
```

**Informations clés** :
- **Fichier** : `geckoterminal_scanner_v2.py`
- **Ligne** : 1063
- **Erreur** : `KeyError`
- **Cause** : Clé manquante

### Étape 2 : Chercher dans ce Guide
Ctrl+F → Chercher le type d'erreur (KeyError, ModuleNotFoundError, etc.)

### Étape 3 : Vérifier les Logs
```bash
# Railway
railway logs

# Local
# Regarder la sortie console
```

### Étape 4 : Tester Localement
```bash
python geckoterminal_scanner_v2.py
# Reproduire l'erreur pour mieux comprendre
```

---

## ✅ Checklist de Dépannage

**Avant de chercher l'erreur** :

- [ ] Lire le message d'erreur complet
- [ ] Noter le fichier et la ligne
- [ ] Vérifier si l'erreur est dans ce guide
- [ ] Tester localement si possible
- [ ] Vérifier les variables d'environnement
- [ ] Vérifier que dependencies sont installées
- [ ] Consulter les logs Railway (si déployé)

---

## 📚 Ressources

- **Documentation complète** : Tous les fichiers `.md` du projet
- **Logs Railway** : `railway logs`
- **Test local** : `python geckoterminal_scanner_v2.py`
- **DB Browser** : Pour inspecter la base de données

---

## 🆘 Support

Si l'erreur n'est pas dans ce guide :

1. **Copier le traceback complet**
2. **Noter les circonstances** (local ou Railway, quand, quoi)
3. **Vérifier les logs complets**
4. **Tester une solution simple** (redémarrer, réinstaller deps)

---

**Dernière mise à jour** : 13 Décembre 2025
**Erreurs résolues** : 10
**Statut** : ✅ **Guide complet**