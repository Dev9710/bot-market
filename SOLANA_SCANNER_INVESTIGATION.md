# 🔍 INVESTIGATION: Pourquoi le scanner SOLANA s'est arrêté

## 📅 Timeline des Événements

### Dernière alerte SOLANA
- **Date**: 2025-12-27 à 22:19:44 UTC
- **Durée d'arrêt**: 125+ heures (5+ jours)

### Commits Critiques

#### ⚠️ COMMIT DÉCLENCHEUR (Probablement)
**`ab66345` | 2025-12-27 03:20:28**
```
"Upgrade to V3 with backtest optimizations (35-50% WR target)"
```

**Changements:**
- ✅ Switch de `geckoterminal_scanner_v2.py` → `geckoterminal_scanner_v3.py` dans alerte.py
- ✅ Ajout de 3,119 lignes de nouveau code V3
- ✅ Nouveaux filtres plus stricts:
  - Score min: 55 → 60
  - Arbitrum désactivé
  - Filtres vélocité, type pump, âge token
  - Système de tiers (HIGH/MEDIUM/LOW)

**Résultat:** Scanner a fonctionné 19 heures après ce commit, puis s'est arrêté vers 22:19

---

#### 🔧 TENTATIVES DE FIX (après constatation du problème)
**`b3d713d` | 2025-12-30 00:38:05**
```
"Auto-restart du scanner en cas de crash"
```
- Modifie `start_services.sh` pour redémarrer automatiquement

**`00d1300` | 2025-12-30 15:46:13**
```
"Scanner V3: Critères assouplis pour plus d'alertes + debug Telegram"
```
- **Réduit MIN_VELOCITE_PUMP**: 10.0 → 5.0
- **Réduit min_score SOLANA**: 85 → 80
- **Réduit min_velocity SOLANA**: 10 → 5
- **Élargi liquidité SOLANA**: (100K, 250K) → (50K, 500K)
- Ajoute debug Telegram

---

## 🔬 Analyse du Code V3

### ✅ SOLANA est configuré correctement

```python
NETWORKS = ["eth", "bsc", "base", "solana", "polygon_pos", "avax"]  # V3.2
```

### ✅ Configuration SOLANA présente

```python
"solana": {
    "min_liquidity": liq['solana'][0],
    "max_liquidity": liq['solana'][1],
    "min_volume": 50000,
    "min_txns": 100
}
```

### ✅ Boucle principale OK

```python
while True:
    try:
        scan_geckoterminal()  # Scan tous les réseaux dont SOLANA
        time.sleep(300)  # 5 min
    except Exception as e:
        log(f"❌ Erreur: {e}")
        time.sleep(60)  # Retry après 1 min
```

### ✅ Scan par réseau OK

```python
for network in NETWORKS:  # Inclut SOLANA
    trending = get_trending_pools(network)
    new_pools = get_new_pools(network)
```

---

## 🎯 CONCLUSION

### ❌ PAS de bug dans le code SOLANA

Le code ne contient aucun bug spécifique à SOLANA. Le réseau est:
- ✅ Présent dans la liste NETWORKS
- ✅ Correctement configuré
- ✅ Inclus dans la boucle de scan
- ✅ Pas de condition spéciale le désactivant

### ⚠️ HYPOTHÈSES PROBABLES

#### 1. **Crash du processus scanner (le plus probable)**
- Le scanner V3 a crash après 19h d'exécution
- Raisons possibles:
  - ❌ Exception non catchée dans le nouveau code V3
  - ❌ Memory leak qui accumule jusqu'au crash
  - ❌ Erreur API GeckoTerminal (rate limit, timeout)
  - ❌ Erreur Database (lock, corruption)

#### 2. **Problème Railway**
- ❌ Railway a redémarré le container
- ❌ Le scanner ne se relance pas automatiquement après crash
- ❌ Variables d'environnement manquantes/expirées

#### 3. **API GeckoTerminal rate-limited**
- ❌ Trop de requêtes pour SOLANA spécifiquement
- ❌ API bloque les requêtes SOLANA temporairement
- ❌ Scanner continue pour autres réseaux mais skip SOLANA silencieusement

---

## 🛠️ ACTIONS RECOMMANDÉES

### PRIORITÉ 1: Vérifier les logs Railway

```bash
railway logs --tail 500
railway logs | grep -i "solana\|error\|crash\|exception"
```

**Chercher:**
- ❌ Erreurs Python (traceback)
- ❌ API errors (429 rate limit, 500 server error)
- ❌ Database errors (lock, timeout)
- ❌ Memory errors (OOM killed)
- ❌ Dernière ligne avant arrêt

### PRIORITÉ 2: Vérifier status processus Railway

```bash
railway status
ps aux | grep gecko
```

**Vérifier:**
- ✅ Scanner V3 est-il en cours d'exécution?
- ✅ Depuis quand?
- ✅ CPU/Memory usage?

### PRIORITÉ 3: Redémarrer manuellement

```bash
# Sur Railway
railway run python alerte.py
# ou
railway restart
```

### PRIORITÉ 4: Ajouter monitoring

**Modifier `geckoterminal_scanner_v3.py`:**

```python
def scan_geckoterminal():
    # ... existing code ...

    for network in NETWORKS:
        log(f"\n🔍 Scan réseau: {network.upper()}")

        try:
            trending = get_trending_pools(network)
            if trending:
                log(f"   ✅ {len(trending)} pools trending trouvés")
            else:
                log(f"   ⚠️  AUCUN pool trending pour {network}")
        except Exception as e:
            log(f"   ❌ ERREUR get_trending_pools({network}): {e}")
            import traceback
            traceback.print_exc()
            continue  # Continue avec les autres réseaux
```

### PRIORITÉ 5: Tests API manuels

```bash
# Tester API GeckoTerminal pour SOLANA
curl "https://api.geckoterminal.com/api/v2/networks/solana/trending_pools" -H "Accept: application/json"

# Vérifier rate limits
curl -I "https://api.geckoterminal.com/api/v2/networks/solana/trending_pools"
```

---

## 📊 DONNÉES DIAGNOSTIC

### Base de données locale

```
Total alertes SOLANA: 1151
Dernières 24h: 0 ❌
Derniers 7 jours: 337
Zone optimale (7j): 333
```

### Résultats API aujourd'hui

```json
{
    "by_network": {
        "eth": {"count": 10, "avg_score": 100},
        "bsc": {"count": 4, "avg_score": 100}
        // SOLANA absent = 0 alertes
    }
}
```

**Confirmation:** API Dashboard fonctionne, mais SOLANA = 0 alertes

---

## 🎯 PROCHAINES ÉTAPES

1. **Consulter logs Railway** pour identifier l'erreur exacte
2. **Redémarrer le scanner** si processus arrêté
3. **Ajouter monitoring** par réseau pour détecter erreurs futures
4. **Tester API SOLANA** manuellement
5. **Implémenter alertes** si scanner crash (webhook, telegram)

---

## 📝 NOTES TECHNIQUES

### Commit qui a introduit V3
- **Hash**: `ab66345`
- **Date**: 2025-12-27 03:20:28
- **Taille**: +3,119 lignes
- **Impact**: Changement complet d'algorithme

### Commits de fix après crash
- `b3d713d`: Auto-restart (Dec 30)
- `00d1300`: Critères assouplis (Dec 30)
- Nombreux fixes liquidité/scoring Dec 30-31

### Configuration actuelle SOLANA
```python
'solana': {
    'min_score': 80,
    'min_velocity': 5,
    'liquidity': (50000, 500000),
    'min_volume': 50000,
    'min_txns': 100
}
```

---

**🔍 Investigation complète | Basée sur analyse git + code + diagnostic DB**

**📅 Date rapport**: 2026-01-02

**✅ Conclusion**: Pas de bug code, scanner probablement crashé. Besoin logs Railway pour confirmer.
