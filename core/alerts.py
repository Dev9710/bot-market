"""
Gestion des Alertes - Génération, analyse et décisions de trading

Fonctions de gestion d'alertes:
- Vérification cooldown et spam prevention
- Évaluation conditions marché (BUY/WAIT/EXIT)
- Analyse alertes suivantes (TP tracking)
- Génération alertes complètes (Entry/SL/TP + analyse)
"""

from typing import Dict, Tuple, List
from datetime import datetime
from utils.helpers import log, format_price, get_network_display_name
from config.settings import (
    ENABLE_SMART_REALERT,
    MIN_PRICE_CHANGE_PERCENT,
    MIN_TIME_HOURS_FOR_REALERT,
)


# Note: alert_cooldown global variable is managed in main scanner
# This file provides pure functions for alert logic
def check_cooldown(alert_key: str) -> bool:
    """
    Vérifie si alerte en cooldown (LEGACY - utiliser should_send_alert à la place).

    Note: Utilise la variable globale alert_cooldown
    """
    from utils.helpers import check_cooldown as _check_cooldown
    return _check_cooldown(alert_key, alert_cooldown)


def should_send_alert(token_address: str, current_price: float, tracker, regle5_data: Dict = None) -> Tuple[bool, str]:
    """
    Détermine si une alerte doit être envoyée pour un token (FIX BUG #1 - SPAM).

    Logique intelligente:
    - 1ère alerte: TOUJOURS envoyer
    - Alertes suivantes: SEULEMENT si:
        * TP atteint (TP1/TP2/TP3) OU
        * Prix a varié de ±5% depuis entry OU
        * 4h se sont écoulées depuis dernière alerte OU
        * Pump parabolique détecté (vélocité >100%/h)

    Returns:
        (should_send: bool, reason: str)
    """
    # Vérifier si c'est la première alerte pour ce token
    if not tracker.token_already_alerted(token_address):
        return True, "Première alerte pour ce token"

    # Si système intelligent désactivé, toujours envoyer
    if not ENABLE_SMART_REALERT:
        return True, "Smart re-alert désactivé"

    # Récupérer la dernière alerte pour ce token
    previous_alert = tracker.get_last_alert_for_token(token_address)
    if not previous_alert:
        return True, "Pas d'alerte précédente trouvée"

    # 1. Vérifier si un TP a été atteint
    entry_price = previous_alert.get('entry_price', 0)
    tp1_price = previous_alert.get('tp1_price', 0)
    tp2_price = previous_alert.get('tp2_price', 0)
    tp3_price = previous_alert.get('tp3_price', 0)

    # Récupérer le prix MAX atteint (pas seulement le prix actuel)
    alert_id = previous_alert.get('id', 0)
    prix_max_atteint = current_price
    if alert_id > 0:
        prix_max_db = tracker.get_highest_price_for_alert(alert_id)
        if prix_max_db:
            prix_max_atteint = max(prix_max_db, current_price)

    # FIX HARMONISATION: Tolérance 0.5% pour cohérence avec analyser_alerte_suivante()
    TP_TOLERANCE_PERCENT = 0.5

    def tp_reached_with_tolerance(prix: float, tp_target: float) -> bool:
        """Vérifie si TP atteint avec tolérance pour arrondi."""
        if tp_target <= 0:
            return False
        ecart_percent = ((prix - tp_target) / tp_target) * 100
        return ecart_percent >= -TP_TOLERANCE_PERCENT

    if tp_reached_with_tolerance(prix_max_atteint, tp1_price):
        return True, f"TP atteint (prix max: ${prix_max_atteint:.6f} >= TP1: ${tp1_price:.6f})"

    # 2. Vérifier si le prix a varié de ±5% depuis entry
    if entry_price > 0:
        price_change_pct = abs((current_price - entry_price) / entry_price * 100)
        if price_change_pct >= MIN_PRICE_CHANGE_PERCENT:
            return True, f"Variation prix significative: {price_change_pct:.1f}% depuis entry"

    # 3. Vérifier le temps écoulé depuis la dernière alerte
    created_at_str = previous_alert.get('created_at', '')
    if created_at_str:
        try:
            from datetime import datetime
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
            elapsed = (now - created_at).total_seconds() / 3600  # En heures

            if elapsed >= MIN_TIME_HOURS_FOR_REALERT:
                return True, f"Temps écoulé suffisant: {elapsed:.1f}h"
        except Exception as e:
            log(f"⚠️ Erreur parsing date: {e}")

    # 4. Vérifier si pump parabolique (RÈGLE 5)
    if regle5_data and regle5_data.get('type_pump') == 'PARABOLIQUE':
        return True, f"Pump PARABOLIQUE détecté - Alerte SORTIR urgente"

    # Aucune raison de re-alerter → SPAM PREVENTION
    return False, "Pas de raison de re-alerter"
def evaluer_conditions_marche(pool_data: Dict, score: int, momentum: Dict,
                              signal_1h: str = None, signal_6h: str = None) -> tuple:
    """
    Évalue TOUTES les conditions du marché pour décider si afficher ACTION RECOMMANDÉE.

    Returns:
        (bool, str, list): (should_enter, decision_type, reasons)
        - should_enter: True = afficher Entry/SL/TP, False = afficher analyse de sortie
        - decision_type: "BUY", "WAIT", "EXIT"
        - reasons: Liste des raisons qui justifient la décision
    """

    reasons_bullish = []
    reasons_bearish = []
    reasons_neutral = []

    # Extraire les données
    pct_24h = pool_data.get("price_change_24h", 0)
    pct_6h = pool_data.get("price_change_6h", 0)
    pct_1h = pool_data.get("price_change_1h", 0)
    vol_24h = pool_data.get("volume_24h", 0)
    vol_6h = pool_data.get("volume_6h", 0)
    vol_1h = pool_data.get("volume_1h", 0)
    liq = pool_data.get("liquidity", 0)
    buys = pool_data.get("buys_24h", 0)
    sells = pool_data.get("sells_24h", 0)
    buys_1h = pool_data.get("buys_1h", 0)
    sells_1h = pool_data.get("sells_1h", 0)
    age = pool_data.get("age_hours", 0)

    buy_ratio_24h = buys / sells if sells > 0 else 1.0
    buy_ratio_1h = buys_1h / sells_1h if sells_1h > 0 else 1.0

    # ===== 1. ANALYSE DU SCORE =====
    if score >= 80:
        reasons_bullish.append("Score excellent (≥80)")
    elif score >= 70:
        reasons_bullish.append("Score bon (≥70)")
    elif score < 60:
        reasons_bearish.append(f"Score faible ({score})")

    # ===== 2. ANALYSE VOLUME (CRITIQUE) =====
    if vol_24h > 0 and vol_6h > 0 and vol_1h > 0:
        vol_24h_avg = vol_24h / 24
        vol_6h_avg = vol_6h / 6
        ratio_1h_vs_6h = (vol_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
        ratio_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

        # Volume court terme (1h vs 6h)
        if signal_1h == "FORTE_ACCELERATION":
            reasons_bullish.append("Volume 1h en FORTE accélération")
        elif signal_1h == "ACCELERATION":
            reasons_bullish.append("Volume 1h en accélération")
        elif signal_1h == "RALENTISSEMENT":
            reasons_bearish.append("Volume 1h en RALENTISSEMENT")
        elif signal_1h == "FORT_RALENTISSEMENT":
            reasons_bearish.append("Volume 1h en FORT RALENTISSEMENT")

        # Volume moyen terme (6h vs 24h)
        if signal_6h == "PUMP_EN_COURS":
            reasons_bullish.append("Pump confirmé sur 6h")
        elif signal_6h == "HAUSSE_PROGRESSIVE":
            reasons_bullish.append("Hausse progressive")
        elif signal_6h == "BAISSE_TENDANCIELLE":
            reasons_bearish.append("Baisse tendancielle sur 6h")

        # PATTERNS CRITIQUES
        if signal_1h in ["FORTE_ACCELERATION", "ACCELERATION"] and signal_6h == "PUMP_EN_COURS":
            reasons_bullish.append("🎯 PATTERN IDÉAL: Pump actif + accélération")
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"] and signal_6h == "PUMP_EN_COURS":
            reasons_bearish.append("⚠️ PATTERN SORTIE: Essoufflement détecté")
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"]:
            reasons_bearish.append("🔴 PATTERN ÉVITER: Volume en chute")

    # ===== 3. ANALYSE PRIX / MOMENTUM (FIX BUG #4 - Multi-TF Confluence) =====

    # Tendance prix 24h
    if pct_24h >= 20:
        reasons_bullish.append(f"Prix 24h en hausse forte (+{pct_24h:.1f}%)")
    elif pct_24h >= 5:
        reasons_bullish.append(f"Prix 24h en hausse (+{pct_24h:.1f}%)")
    elif pct_24h < -15:
        reasons_bearish.append(f"Prix 24h en baisse ({pct_24h:.1f}%)")

    # NOUVEAU: Multi-Timeframe Confluence (Quick Win #3)
    # Détecter PULLBACK SAIN sur uptrend (buy the dip)
    if pct_24h >= 5 and -8 < pct_1h < 0:
        # Uptrend 24h + pullback léger 1h = BUY THE DIP
        reasons_bullish.append(f"📊 PULLBACK SAIN: +{pct_24h:.1f}% 24h | {pct_1h:.1f}% 1h (buy the dip)")
        reasons_bullish.append("✅ Multi-TF confluence: Opportunité d'entrée sur retracement")
    # Détecter continuation haussière (multi-TF bullish)
    elif pct_24h >= 5 and pct_6h >= 3 and pct_1h >= 2:
        reasons_bullish.append(f"🚀 MULTI-TF BULLISH: Hausse confirmée sur 24h/6h/1h")
    # Tendance prix court terme (si pas de pullback sain)
    elif pct_1h >= 5:
        reasons_bullish.append(f"Momentum 1h positif (+{pct_1h:.1f}%)")
    elif pct_1h <= -10:
        # Seulement considérer bearish si vraiment négatif (-10%)
        reasons_bearish.append(f"Momentum 1h très négatif ({pct_1h:.1f}%)")

    # Analyse de la décélération (CRITIQUE pour sortie)
    # MODIFIÉ: Seulement si AUCUN pullback sain
    if pct_1h > 0 and pct_6h > 0 and not (pct_24h >= 5 and -8 < pct_1h < 0):
        if pct_1h < pct_6h * 0.5:  # 1h fait moins de 50% du 6h = décélération
            reasons_bearish.append("Décélération: momentum 1h < 50% du 6h")

    # ===== 4. ANALYSE PRESSION ACHAT/VENTE =====
    ratio_change = buy_ratio_1h - buy_ratio_24h

    if ratio_change > 0.15:  # Forte augmentation pression acheteuse
        reasons_bullish.append(f"Pression acheteuse en hausse (+{ratio_change:.1%})")
    elif ratio_change < -0.15:  # Forte augmentation pression vendeuse
        reasons_bearish.append(f"Pression vendeuse en hausse ({ratio_change:.1%})")

    if buy_ratio_1h >= 1.3:
        reasons_bullish.append(f"Acheteurs dominent 1h (ratio {buy_ratio_1h:.2f})")
    elif buy_ratio_1h <= 0.7:
        reasons_bearish.append(f"Vendeurs dominent 1h (ratio {buy_ratio_1h:.2f})")

    # ===== 5. ANALYSE LIQUIDITÉ =====
    if liq < 150000:
        reasons_bearish.append(f"Liquidité très faible (${liq/1000:.0f}K) - Risque rug élevé")
    elif liq < 200000:
        reasons_neutral.append(f"Liquidité faible (${liq/1000:.0f}K) - Prudence")
    elif liq >= 500000:
        reasons_bullish.append(f"Liquidité solide (${liq/1000:.0f}K)")

    # ===== 6. ANALYSE ÂGE =====
    if age > 48:
        reasons_neutral.append(f"Token mature ({age:.0f}h) - Exit window peut être passée")
    elif age < 1:
        reasons_neutral.append(f"Token très jeune ({age:.1f}h) - Volatilité extrême")

    # ===== DÉCISION FINALE (FIX BUG #6 - Score 70+ devrait donner BUY) =====
    score_bullish = len(reasons_bullish)
    score_bearish = len(reasons_bearish)

    # Détecter patterns critiques
    has_critical_bullish = any("PATTERN IDÉAL" in r or "FORTE accélération" in r or "MULTI-TF BULLISH" in r or "PULLBACK SAIN" in r for r in reasons_bullish)
    has_critical_bearish = any("PATTERN SORTIE" in r or "PATTERN ÉVITER" in r or "FORT RALENTISSEMENT" in r for r in reasons_bearish)

    # NOUVELLE LOGIQUE:
    # 1. Score 70+ avec multi-TF confluence → BUY
    # 2. Pattern critique bearish → EXIT
    # 3. Pattern critique bullish + score >= 65 → BUY
    # 4. Score bullish dominant → BUY
    # 5. Sinon → WAIT ou EXIT

    if has_critical_bearish:
        # Bearish critique = SORTIR (même si score élevé)
        decision = "EXIT"
        should_enter = False
    elif score >= 75 and score_bullish >= 3 and score_bearish <= 1:
        # Score excellent + plusieurs signaux bullish = BUY
        decision = "BUY"
        should_enter = True
    elif score >= 70 and (has_critical_bullish or score_bullish >= 2) and score_bearish <= 1:
        # Score bon + signaux bullish = BUY
        decision = "BUY"
        should_enter = True
    elif has_critical_bullish and score >= 65 and score_bearish <= 2:
        # Pattern idéal/Multi-TF/Pullback sain + score OK = BUY
        decision = "BUY"
        should_enter = True
    elif score_bullish >= 4 and score_bearish <= 1:
        # Beaucoup de signaux bullish = BUY
        decision = "BUY"
        should_enter = True
    elif score_bearish >= 3 or score < 60:
        # Trop bearish ou score faible = EXIT
        decision = "EXIT"
        should_enter = False
    elif score_bullish >= 2 and score_bearish <= 2:
        # Mitigé = WAIT
        decision = "WAIT"
        should_enter = False
    else:
        # Défaut = EXIT
        decision = "EXIT"
        should_enter = False

    return should_enter, decision, {
        'bullish': reasons_bullish,
        'bearish': reasons_bearish,
        'neutral': reasons_neutral
    }

# ============================================
# ANALYSE ALERTE SUIVANTE (TP TRACKING)
# ============================================
def analyser_alerte_suivante(previous_alert: Dict, current_price: float, pool_data: Dict,
                             score: int, momentum: Dict, signal_1h: str = None,
                             signal_6h: str = None, tracker=None) -> Dict:
    """
    Analyse une alerte suivante sur un token déjà alerté.
    Vérifie si les TP ont été atteints et décide de la stratégie.

    VERSION SIMPLE+ - 5 RÈGLES ESSENTIELLES:
    1. Détection des TP atteints
    2. Vérification du prix (pas trop élevé pour re-entry)
    3. Réévaluation des conditions actuelles
    4. Décision: NOUVEAUX_NIVEAUX / SECURISER_HOLD / SORTIR
    5. Analyse vélocité du pump (protection pump parabolique)

    Args:
        previous_alert: Dernière alerte sur ce token (depuis DB)
        current_price: Prix actuel du token
        pool_data: Données actuelles du pool
        score: Score actuel
        momentum: Momentum actuel
        signal_1h: Signal volume 1h vs 6h
        signal_6h: Signal volume 6h vs 24h

    Returns:
        Dict avec:
            - decision: "NOUVEAUX_NIVEAUX" / "SECURISER_HOLD" / "SORTIR"
            - tp_hit: Liste des TP atteints ["TP1", "TP2", "TP3"]
            - tp_gains: Dict avec les gains réalisés {"TP1": 5.0, ...}
            - prix_trop_eleve: bool
            - conditions_favorables: bool
            - raisons: Liste des raisons de la décision
            - nouveaux_niveaux: Dict (si applicable) avec entry/sl/tp
            - velocite_pump: float (% par heure)
            - type_pump: str (PARABOLIQUE / RAPIDE / NORMAL / LENT)
    """

    # VALIDATION: Vérifier que previous_alert et pool_data sont valides
    if not previous_alert or not isinstance(previous_alert, dict):
        log(f"   ⚠️ previous_alert invalide: {type(previous_alert)}")
        return {
            'decision': 'ERROR',
            'tp_hit': [],
            'tp_gains': {},
            'prix_trop_eleve': False,
            'conditions_favorables': False,
            'raisons': ["Données d'alerte précédente invalides"],
            'nouveaux_niveaux': {},
            'hausse_depuis_alerte': 0,
            'velocite_pump': 0,
            'type_pump': 'UNKNOWN',
            'temps_ecoule_heures': 0
        }

    if not pool_data or not isinstance(pool_data, dict):
        log(f"   ⚠️ pool_data invalide dans analyser_alerte_suivante: {type(pool_data)}")
        return {
            'decision': 'ERROR',
            'tp_hit': [],
            'tp_gains': {},
            'prix_trop_eleve': False,
            'conditions_favorables': False,
            'raisons': ["Données de pool invalides"],
            'nouveaux_niveaux': {},
            'hausse_depuis_alerte': 0,
            'velocite_pump': 0,
            'type_pump': 'UNKNOWN',
            'temps_ecoule_heures': 0
        }

    if not momentum or not isinstance(momentum, dict):
        log(f"   ⚠️ momentum invalide dans analyser_alerte_suivante: {type(momentum)}")
        return {
            'decision': 'ERROR',
            'tp_hit': [],
            'tp_gains': {},
            'prix_trop_eleve': False,
            'conditions_favorables': False,
            'raisons': ["Données de momentum invalides"],
            'nouveaux_niveaux': {},
            'hausse_depuis_alerte': 0,
            'velocite_pump': 0,
            'type_pump': 'UNKNOWN',
            'temps_ecoule_heures': 0
        }

    # RÈGLE 1: Détection des TP atteints
    # IMPORTANT: On vérifie si les TP ont été atteints DANS LE PASSÉ (pas juste le prix actuel)
    tp_hit = []
    tp_gains = {}

    tp1_price = previous_alert.get('tp1_price', 0)
    tp2_price = previous_alert.get('tp2_price', 0)
    tp3_price = previous_alert.get('tp3_price', 0)
    entry_price = previous_alert.get('entry_price', previous_alert.get('price_at_alert', 0))

    # Récupérer le prix MAX atteint depuis l'alerte précédente (depuis price_tracking)
    # Si pas de tracking disponible, utiliser le prix actuel comme fallback
    alert_id = previous_alert.get('id', 0)
    prix_max_atteint = current_price  # Fallback par défaut

    # Si le tracker est disponible, récupérer le VRAI prix MAX depuis la DB
    if tracker is not None and alert_id > 0:
        prix_max_db = tracker.get_highest_price_for_alert(alert_id)
        if prix_max_db is not None:
            # Comparer avec le prix actuel et prendre le max
            prix_max_atteint = max(prix_max_db, current_price)
            # Note: On prend le max car le prix actuel peut être > que le dernier tracking

    # FIX HARMONISATION: Tolérance 0.5% pour éviter problèmes d'arrondi
    # Exemple: TP1=$0.1575, prix=$0.1574 → considéré comme atteint (écart 0.06%)
    TP_TOLERANCE_PERCENT = 0.5  # 0.5% de tolérance

    def tp_reached(prix: float, tp_target: float) -> bool:
        """Vérifie si TP atteint avec tolérance pour arrondi."""
        if tp_target <= 0:
            return False
        ecart_percent = ((prix - tp_target) / tp_target) * 100
        # TP atteint si prix >= TP - 0.5%
        return ecart_percent >= -TP_TOLERANCE_PERCENT

    # DEBUG: Log pour comprendre détection TP
    if alert_id > 0:
        log(f"   🔍 DEBUG TP: prix_max={prix_max_atteint:.8f}, tp1={tp1_price:.8f}, tp2={tp2_price:.8f}, tp3={tp3_price:.8f}")

    # Vérification des TP basée sur le prix MAX atteint (historique + actuel)
    # AVEC TOLÉRANCE pour éviter problèmes d'arrondi
    if tp_reached(prix_max_atteint, tp3_price):
        tp_hit.extend(["TP1", "TP2", "TP3"])
        tp_gains["TP1"] = ((tp1_price - entry_price) / entry_price) * 100
        tp_gains["TP2"] = ((tp2_price - entry_price) / entry_price) * 100
        tp_gains["TP3"] = ((tp3_price - entry_price) / entry_price) * 100
    elif tp_reached(prix_max_atteint, tp2_price):
        tp_hit.extend(["TP1", "TP2"])
        tp_gains["TP1"] = ((tp1_price - entry_price) / entry_price) * 100
        tp_gains["TP2"] = ((tp2_price - entry_price) / entry_price) * 100
    elif tp_reached(prix_max_atteint, tp1_price):
        tp_hit.append("TP1")
        tp_gains["TP1"] = ((tp1_price - entry_price) / entry_price) * 100

    # RÈGLE 2: Vérifier si le prix est trop élevé pour re-entry (>20% depuis alerte initiale)
    hausse_depuis_alerte = ((current_price - entry_price) / entry_price) * 100
    prix_trop_eleve = hausse_depuis_alerte > 20.0

    # RÈGLE 5: Analyser la vélocité du pump (protection pump parabolique)
    from datetime import datetime

    # Calculer le temps écoulé depuis l'alerte précédente
    try:
        if isinstance(previous_alert.get('created_at'), str):
            created_at = datetime.strptime(previous_alert['created_at'], '%Y-%m-%d %H:%M:%S')
        else:
            created_at = previous_alert.get('created_at')

        temps_ecoule_heures = (datetime.now() - created_at).total_seconds() / 3600
    except:
        # Si erreur de parsing, estimer à 1h par défaut
        temps_ecoule_heures = 1.0

    # Éviter division par zéro
    if temps_ecoule_heures < 0.01:  # Moins de 36 secondes
        temps_ecoule_heures = 0.01

    # Calculer la vélocité: % de hausse par heure
    velocite_pump = hausse_depuis_alerte / temps_ecoule_heures

    # Classifier le type de pump
    pump_parabolique = False
    pump_tres_rapide = False
    type_pump = ""

    if velocite_pump > 100:  # >100% par heure = PARABOLIQUE
        type_pump = "PARABOLIQUE"
        pump_parabolique = True
    elif velocite_pump > 50:  # >50% par heure = TRÈS RAPIDE
        type_pump = "TRES_RAPIDE"
        pump_tres_rapide = True
    elif velocite_pump > 20:  # >20% par heure = RAPIDE
        type_pump = "RAPIDE"
    elif velocite_pump > 5:  # >5% par heure = NORMAL
        type_pump = "NORMAL"
    else:  # ≤5% par heure = LENT (sain)
        type_pump = "LENT"

    # RÈGLE 3: Réévaluer les conditions actuelles du marché
    log(f"   🔍 DEBUG avant evaluer_conditions_marche: pool_data={type(pool_data)}, score={score}, momentum={type(momentum)}, signal_1h={signal_1h}, signal_6h={signal_6h}")
    conditions_favorables, decision_marche, raisons_marche = evaluer_conditions_marche(
        pool_data, score, momentum, signal_1h, signal_6h
    )
    log(f"   🔍 DEBUG après evaluer_conditions_marche: raisons_marche={type(raisons_marche)}")

    # RÈGLE 4: Décision finale
    raisons = []
    decision = ""
    nouveaux_niveaux = {}

    # CAS 1: Aucun TP atteint → Évaluation selon conditions (FIX BUG #3)
    if not tp_hit:
        # Évaluer si c'est toujours une bonne opportunité d'entrée
        if conditions_favorables and score >= 70:
            decision = "ENTRER"
            raisons.append(f"Aucun TP atteint mais conditions excellentes (Score: {score})")
            raisons.append(f"💡 Si pas en position: ENTRER maintenant")
            raisons.append(f"💡 Si déjà en position: MAINTENIR (pas de TP atteint)")
            log(f"   🔍 DEBUG AVANT extend bullish: raisons_marche type={type(raisons_marche)}, bullish type={type(raisons_marche.get('bullish') if isinstance(raisons_marche, dict) else 'N/A')}")
            raisons.extend(raisons_marche['bullish'][:3])
            log(f"   🔍 DEBUG APRÈS extend bullish")
        elif conditions_favorables and score >= 60:
            decision = "ATTENDRE"
            raisons.append(f"Aucun TP atteint, conditions moyennes (Score: {score})")
            raisons.append(f"💡 Si pas en position: ATTENDRE meilleure entrée")
            raisons.append(f"💡 Si déjà en position: MAINTENIR position initiale")
        else:
            decision = "EVITER"
            raisons.append("Aucun TP atteint et conditions défavorables")
            raisons.append(f"💡 Si pas en position: ÉVITER")
            raisons.append(f"💡 Si en position: Considérer SORTIE si SL proche")
            if raisons_marche['bearish']:
                raisons.extend(raisons_marche['bearish'][:2])

    # CAS 2a: PUMP PARABOLIQUE → SORTIR IMMÉDIATEMENT (risque dump violent)
    elif pump_parabolique and tp_hit:
        decision = "SORTIR"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s) (+{hausse_depuis_alerte:.1f}%)")
        raisons.append(f"🚨 PUMP PARABOLIQUE détecté ({velocite_pump:.0f}%/h)")
        raisons.append(f"⚠️ Risque de dump violent - SÉCURISER IMMÉDIATEMENT")
        raisons.append("💰 Prendre les profits maintenant avant le retournement")

    # CAS 2b: TP atteint(s) + prix trop élevé → Ne pas re-rentrer
    elif prix_trop_eleve:
        decision = "SORTIR"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s) (+{hausse_depuis_alerte:.1f}%)")
        raisons.append(f"⚠️ Prix trop élevé pour re-entry (+{hausse_depuis_alerte:.1f}% depuis alerte initiale)")
        raisons.append("💰 Sécuriser les gains déjà réalisés")

    # CAS 3a: PUMP TRÈS RAPIDE + conditions favorables → Nouveaux niveaux TRÈS SERRÉS
    elif pump_tres_rapide and conditions_favorables and tp_hit:
        decision = "NOUVEAUX_NIVEAUX"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s)")
        for tp_name, gain in tp_gains.items():
            raisons.append(f"   {tp_name}: +{gain:.1f}%")
        raisons.append(f"⚡ Pump très rapide ({velocite_pump:.0f}%/h)")
        raisons.append(f"🚀 Conditions encore favorables ({decision_marche})")
        raisons.append("⚠️ SL TRÈS SERRÉ (-3%) car pump rapide")

        # SL TRÈS SERRÉ à 97% pour pump très rapide
        nouveaux_niveaux = {
            'entry_price': current_price,
            'stop_loss_price': current_price * 0.97,  # -3% au lieu de -5%
            'stop_loss_percent': -3.0,
            'tp1_price': current_price * 1.05,
            'tp1_percent': 5.0,
            'tp2_price': current_price * 1.10,
            'tp2_percent': 10.0,
            'tp3_price': current_price * 1.15,
            'tp3_percent': 15.0
        }

    # CAS 3b: TP atteint(s) + conditions favorables → Nouveaux niveaux
    elif conditions_favorables:
        decision = "NOUVEAUX_NIVEAUX"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s)")
        for tp_name, gain in tp_gains.items():
            raisons.append(f"   {tp_name}: +{gain:.1f}%")
        raisons.append(f"🚀 Conditions encore favorables ({decision_marche})")
        raisons.extend(raisons_marche['bullish'][:3])  # Top 3 raisons haussières

        # Afficher type de pump
        if type_pump == "LENT":
            raisons.append(f"✅ Pump sain ({velocite_pump:.1f}%/h) - Progression stable")

        # Calculer NOUVEAUX niveaux depuis le prix actuel
        # SL plus serré à 95% (car déjà en profit)
        nouveaux_niveaux = {
            'entry_price': current_price,
            'stop_loss_price': current_price * 0.95,
            'stop_loss_percent': -5.0,
            'tp1_price': current_price * 1.05,
            'tp1_percent': 5.0,
            'tp2_price': current_price * 1.10,
            'tp2_percent': 10.0,
            'tp3_price': current_price * 1.15,
            'tp3_percent': 15.0
        }

    # CAS 4: TP atteint(s) + conditions neutres/baissières → Sécuriser
    else:
        decision = "SECURISER_HOLD"
        raisons.append(f"✅ {', '.join(tp_hit)} atteint(s)")
        for tp_name, gain in tp_gains.items():
            raisons.append(f"   {tp_name}: +{gain:.1f}%")
        raisons.append(f"⚠️ Conditions actuelles: {decision_marche}")
        raisons.extend(raisons_marche['bearish'][:2])  # Top 2 raisons baissières
        raisons.append("💡 Trailing stop à -5% recommandé pour sécuriser")

    return {
        'decision': decision,
        'tp_hit': tp_hit,
        'tp_gains': tp_gains,
        'prix_trop_eleve': prix_trop_eleve,
        'conditions_favorables': conditions_favorables,
        'raisons': raisons,
        'nouveaux_niveaux': nouveaux_niveaux,
        'hausse_depuis_alerte': hausse_depuis_alerte,
        'velocite_pump': velocite_pump,
        'type_pump': type_pump,
        'temps_ecoule_heures': temps_ecoule_heures
    }

# ============================================
# GÉNÉRATION ALERTE COMPLÈTE
def generer_alerte_complete(pool_data: Dict, score: int, base_score: int, momentum_bonus: int,
                            momentum: Dict, multi_pool_data: Dict, signals: List[str],
                            resistance_data: Dict, whale_analysis: Dict = None, is_first_alert: bool = True,
                            tracker: 'AlertTracker' = None) -> tuple:
    """Génère alerte ultra-complète avec toutes les données.

    Args:
        tracker: Instance d'AlertTracker pour accéder à l'historique (optionnel)

    Returns:
        tuple: (message_texte, donnees_regle5_dict)
    """

    # Initialiser les données RÈGLE 5 par défaut
    regle5_data = {
        'velocite_pump': 0,
        'type_pump': 'UNKNOWN',
        'decision_tp_tracking': None,
        'temps_depuis_alerte_precedente': 0,
        'is_alerte_suivante': 0
    }

    name = pool_data["name"]
    base_token = pool_data["base_token_name"]
    price = pool_data["price_usd"]
    vol_24h = pool_data["volume_24h"]
    vol_6h = pool_data["volume_6h"]
    vol_1h = pool_data["volume_1h"]
    liq = pool_data["liquidity"]
    pct_24h = pool_data["price_change_24h"]
    pct_6h = pool_data["price_change_6h"]
    pct_3h = pool_data["price_change_3h"]
    pct_1h = pool_data["price_change_1h"]
    age = pool_data["age_hours"]
    txns = pool_data["total_txns"]
    buys = pool_data["buys_24h"]
    sells = pool_data["sells_24h"]
    buys_1h = pool_data["buys_1h"]
    sells_1h = pool_data["sells_1h"]
    network_id = pool_data["network"]  # ID original pour le lien
    network_display = get_network_display_name(network_id)  # Nom lisible pour affichage
    ratio_vol_liq = (vol_24h / liq * 100) if liq > 0 else 0
    buy_ratio_24h = buys / sells if sells > 0 else 1.0
    buy_ratio_1h = buys_1h / sells_1h if sells_1h > 0 else 1.0

    # Initialiser les signaux volume (seront définis dans l'analyse volume)
    signal_1h = None
    signal_6h = None

    # Emojis score
    if score >= 80:
        score_emoji = "⭐️⭐️⭐️⭐️"
        score_label = "EXCELLENT"
    elif score >= 70:
        score_emoji = "⭐️⭐️⭐️"
        score_label = "TRÈS BON"
    elif score >= 60:
        score_emoji = "⭐️⭐️"
        score_label = "BON"
    elif score >= 50:
        score_emoji = "⭐️"
        score_label = "MOYEN"
    else:
        score_emoji = ""
        score_label = "FAIBLE"

    # ========== CONSTRUCTION ALERTE ==========
    # Titre différent selon s'il s'agit de la première alerte ou d'une mise à jour
    if is_first_alert:
        txt = f"\n🆕 *Nouvelle opportunité sur le token {base_token}*\n"
    else:
        txt = f"\n🔄 *Nouvelle analyse sur le token {base_token}*\n"
    txt += f"━━━━━━━━━━━━━━━━\n"
    txt += f"💎 {name}\n"
    txt += f"⛓️ Blockchain: {network_display}\n\n"

    # SCORE + CONFIANCE (NOUVEAU)
    confidence = calculate_confidence_score(pool_data)
    txt += f"🎯 *SCORE: {score}/100 {score_emoji} {score_label}*\n"
    txt += f"   Base: {base_score} | Momentum: {momentum_bonus:+d}"

    # Afficher whale score si disponible
    if whale_analysis:
        whale_score = whale_analysis['whale_score']
        if whale_score != 0:
            txt += f" | Whale: {whale_score:+d}"

    txt += f"\n📊 Confiance: {confidence}% (fiabilité données)\n"

    # ===== V3: TIER DE CONFIANCE BACKTEST =====
    tier = calculate_confidence_tier(pool_data)
    tier_emojis = {
        "ULTRA_HIGH": "💎💎💎",
        "HIGH": "💎💎",
        "MEDIUM": "💎",
        "LOW": "⚪",
        "VERY_LOW": "⚫"
    }
    tier_labels = {
        "ULTRA_HIGH": "ULTRA HIGH (Watchlist - 77-100% WR historique)",
        "HIGH": "HIGH (35-50% WR attendu)",
        "MEDIUM": "MEDIUM (25-30% WR attendu)",
        "LOW": "LOW (15-20% WR attendu)",
        "VERY_LOW": "VERY LOW (<15% WR attendu)"
    }
    tier_emoji = tier_emojis.get(tier, "⚪")
    tier_label = tier_labels.get(tier, "UNKNOWN")

    txt += f"🎖️ *TIER V3: {tier_emoji} {tier_label}*\n"

    # Afficher les raisons de filtrage V3 (si disponibles)
    v3_reasons = pool_data.get('v3_filter_reasons', [])
    if v3_reasons:
        # Afficher seulement les raisons positives (succès)
        positive_reasons = [r.replace('✓ ', '') for r in v3_reasons if r.startswith('✓')]
        if positive_reasons:
            txt += f"   V3 Checks: {' | '.join(positive_reasons[:3])}\n"  # Max 3 raisons

    txt += "\n"

    # NOUVEAU: Section WHALE ACTIVITY (FIX BUG #5 - Toujours afficher si whale_score != 0)
    if whale_analysis:
        whale_score_val = whale_analysis.get('whale_score', 0)
        pattern = whale_analysis.get('pattern', 'NORMAL')
        signals = whale_analysis.get('signals', [])

        # Afficher si whale_score != 0 OU si pattern != NORMAL OU si signals non vide
        if whale_score_val != 0 or pattern != 'NORMAL' or signals:
            concentration_risk = whale_analysis['concentration_risk']
            buyers_1h = whale_analysis['buyers_1h']
            sellers_1h = whale_analysis['sellers_1h']
            avg_buys = whale_analysis['avg_buys_per_buyer']
            avg_sells = whale_analysis.get('avg_sells_per_seller', 0)

            # Emoji selon pattern
            if pattern == 'WHALE_MANIPULATION':
                pattern_emoji = "🐋"
                pattern_label = "WHALE MANIPULATION"
            elif pattern == 'WHALE_SELLING':
                pattern_emoji = "🚨"
                pattern_label = "WHALE SELLING"
            elif pattern == 'DISTRIBUTED_BUYING':
                pattern_emoji = "✅"
                pattern_label = "ACCUMULATION DISTRIBUÉE"
            elif pattern == 'DISTRIBUTED_SELLING':
                pattern_emoji = "⚠️"
                pattern_label = "SELLING PRESSURE"
            else:
                # Pattern NORMAL mais whale_score != 0 (ex: concentration 24h)
                pattern_emoji = "📊"
                pattern_label = "WHALE ACTIVITY"

            txt += f"\n{pattern_emoji} *{pattern_label}*\n"
            txt += f"   Buyers: {buyers_1h} | Sellers: {sellers_1h}\n"
            txt += f"   Avg buys/buyer: {avg_buys:.1f}x"
            if avg_sells > 0:
                txt += f" | Avg sells/seller: {avg_sells:.1f}x"
            txt += f"\n   Risque concentration: {concentration_risk}\n"

            # Afficher les signaux si disponibles
            if signals:
                txt += f"   Signaux: {', '.join(signals[:2])}\n"

    txt += "\n"

    # ========== ANALYSE TP TRACKING (pour alertes suivantes) ==========
    if not is_first_alert and tracker is not None:
        token_address = pool_data.get("pool_address", "")
        previous_alert = tracker.get_last_alert_for_token(token_address)

        if previous_alert:
            # Pré-calculer les signaux volume pour l'analyse
            vol_24h_avg = vol_24h / 24
            vol_6h_avg = vol_6h / 6 if vol_6h > 0 else 0
            ratio_1h_vs_6h = (vol_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
            ratio_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

            # Déterminer signaux
            if ratio_1h_vs_6h >= 2.0:
                signal_1h = "FORTE_ACCELERATION"
            elif ratio_1h_vs_6h >= 1.5:
                signal_1h = "ACCELERATION"
            elif ratio_1h_vs_6h <= 0.3:
                signal_1h = "FORT_RALENTISSEMENT"
            elif ratio_1h_vs_6h <= 0.5:
                signal_1h = "RALENTISSEMENT"
            else:
                signal_1h = "STABLE"

            if ratio_6h_vs_24h >= 1.8:
                signal_6h = "PUMP_EN_COURS"
            elif ratio_6h_vs_24h >= 1.3:
                signal_6h = "HAUSSE_PROGRESSIVE"
            elif ratio_6h_vs_24h <= 0.7:
                signal_6h = "BAISSE_TENDANCIELLE"
            else:
                signal_6h = "STABLE"

            # Analyser TP tracking (passer le tracker pour vérifier le prix MAX atteint)
            analyse_tp = analyser_alerte_suivante(
                previous_alert, price, pool_data, score, momentum, signal_1h, signal_6h, tracker
            )
            log(f"   🔍 DEBUG RETOUR analyser_alerte_suivante: decision={analyse_tp.get('decision') if analyse_tp else None}, type={type(analyse_tp)}")

            # VALIDATION: Vérifier que analyse_tp est un dict valide
            if not analyse_tp or not isinstance(analyse_tp, dict):
                log(f"   ⚠️ analyse_tp invalide: {type(analyse_tp)}")
                # Ne pas afficher la section TP tracking si erreur
            elif analyse_tp['decision'] == 'ERROR':
                # Vérifier si l'analyse a échoué (decision == 'ERROR')
                log(f"   ⚠️ Analyse TP tracking échouée, skip section suivi")
                # Ne pas afficher la section TP tracking si erreur
            else:
                # Mettre à jour les données RÈGLE 5
                regle5_data = {
                    'velocite_pump': analyse_tp['velocite_pump'],
                    'type_pump': analyse_tp['type_pump'],
                    'decision_tp_tracking': analyse_tp['decision'],
                    'temps_depuis_alerte_precedente': analyse_tp['temps_ecoule_heures'],
                    'is_alerte_suivante': 1
                }

                # Afficher section TP TRACKING
                txt += f"━━━ SUIVI ALERTE PRÉCÉDENTE ━━━\n"
                entry_prev = previous_alert.get('entry_price', previous_alert.get('price_at_alert', 0))
                txt += f"📍 Entry précédente: {format_price(entry_prev)}\n"
                txt += f"💰 Prix actuel: {format_price(price)} ({analyse_tp['hausse_depuis_alerte']:+.1f}%)\n"

                # Afficher vélocité du pump
                temps_h = analyse_tp['temps_ecoule_heures']
                velocite = analyse_tp['velocite_pump']
                type_pump = analyse_tp['type_pump']

                if temps_h < 1:
                    temps_display = f"{temps_h * 60:.0f} min"
                else:
                    temps_display = f"{temps_h:.1f}h"

                # Emoji selon type de pump
                if type_pump == "PARABOLIQUE":
                    pump_emoji = "🚨"
                    pump_label = "PARABOLIQUE (DANGER)"
                elif type_pump == "TRES_RAPIDE":
                    pump_emoji = "⚡"
                    pump_label = "TRÈS RAPIDE"
                elif type_pump == "RAPIDE":
                    pump_emoji = "🔥"
                    pump_label = "RAPIDE"
                elif type_pump == "NORMAL":
                    pump_emoji = "📈"
                    pump_label = "NORMAL"
                else:  # LENT
                    pump_emoji = "✅"
                    pump_label = "SAIN"

                txt += f"⏱️ Temps écoulé: {temps_display} | {pump_emoji} Vélocité: {velocite:.0f}%/h ({pump_label})\n"

                # Afficher Prix MAX atteint (CRITIQUE pour comprendre détection TP)
                if tracker is not None and 'previous_alert' in locals() and previous_alert:
                    alert_id = previous_alert.get('id', 0)
                    prix_max_db = tracker.get_highest_price_for_alert(alert_id) if alert_id > 0 else None
                    prix_max_display = max(prix_max_db or 0, price)

                    if prix_max_display > 0:
                        entry_price_ref = previous_alert.get('entry_price', price)
                        gain_max = ((prix_max_display - entry_price_ref) / entry_price_ref) * 100
                        txt += f"📈 Prix MAX atteint: {format_price(prix_max_display)} (+{gain_max:.1f}%)\n"

                # Afficher TP atteints (basé sur Prix MAX, pas prix actuel)
                if analyse_tp['tp_hit']:
                    txt += f"✅ *TP ATTEINTS:* {', '.join(analyse_tp['tp_hit'])}\n"
                    for tp_name, gain in analyse_tp['tp_gains'].items():
                        txt += f"   {tp_name}: +{gain:.1f}%\n"
                else:
                    txt += f"⏳ Aucun TP atteint pour le moment\n"

                txt += f"\n🎯 *DÉCISION: {analyse_tp['decision']}*\n"

                # Afficher raisons
                for raison in analyse_tp['raisons']:
                    txt += f"{raison}\n"

                txt += "\n"

    # PRIX & MOMENTUM
    txt += f"━━━ PRIX & MOMENTUM ━━━\n"
    txt += f"💰 Prix: {format_price(price)}\n"

    # Multi-timeframe avec analyse de tendance
    txt += f"📊 "
    txt += f"24h: {pct_24h:+.1f}% "
    if pct_6h != 0:
        txt += f"| 6h: {pct_6h:+.1f}% "
    if pct_3h != 0:
        txt += f"| 3h: {pct_3h:+.1f}% "
    if pct_1h != 0:
        emoji_1h = "🚀" if pct_1h > 5 else ("🟢" if pct_1h > 0 else "🔴")
        txt += f"| 1h: {pct_1h:+.1f}% {emoji_1h}"
    txt += "\n"

    # Analyse de la structure de tendance (NOUVEAU)
    if pct_6h != 0 and pct_3h != 0 and pct_1h != 0:
        # Déterminer si accélération haussière ou essoufflement
        if pct_1h > pct_3h > pct_6h and pct_1h > 0:
            txt += f"📈 Tendance: ACCÉLÉRATION HAUSSIÈRE 🔥\n"
        elif pct_6h > pct_3h > pct_1h and pct_6h > 0:
            txt += f"⚠️ Tendance: ESSOUFFLEMENT (sortie proche) 📉\n"
        elif pct_1h < 0 < pct_3h < pct_6h:
            txt += f"🔄 Tendance: REPRISE après correction (bon entry) ✅\n"
        elif pct_1h < pct_3h < pct_6h and pct_1h < 0:
            txt += f"🔴 Tendance: DÉCÉLÉRATION BAISSIÈRE ⚠️\n"

    # Résistance
    if resistance_data and resistance_data.get("resistance"):
        txt += f"🎯 Résistance: {format_price(resistance_data['resistance'])} "
        txt += f"(+{resistance_data['resistance_dist_pct']:.1f}%)\n"

    txt += "\n"

    # ACTIVITÉ
    txt += f"━━━ ACTIVITÉ ━━━\n"
    txt += f"📊 Vol 24h: ${vol_24h/1000:.0f}K\n"

    # Analyse de l'évolution du volume MULTI-NIVEAUX (NOUVEAU)
    if vol_24h > 0 and vol_6h > 0 and vol_1h > 0:
        # Calculer les moyennes horaires
        vol_24h_avg = vol_24h / 24  # Volume moyen par heure sur 24h
        vol_6h_avg = vol_6h / 6     # Volume moyen par heure sur 6h

        # Ratios d'accélération
        ratio_1h_vs_6h = (vol_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
        ratio_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

        # ANALYSE DOUBLE NIVEAU pour détecter les meilleurs setups

        # Niveau 1: Court terme (1h vs 6h)
        if ratio_1h_vs_6h >= 2.0:
            signal_1h = "FORTE_ACCELERATION"
            emoji_1h = "🔥"
            text_1h = f"FORTE ACCÉLÉRATION ({ratio_1h_vs_6h:.1f}x)"
        elif ratio_1h_vs_6h >= 1.5:
            signal_1h = "ACCELERATION"
            emoji_1h = "📈"
            text_1h = f"ACCÉLÉRATION ({ratio_1h_vs_6h:.1f}x)"
        elif ratio_1h_vs_6h <= 0.5:
            signal_1h = "RALENTISSEMENT"
            emoji_1h = "⚠️"
            text_1h = f"RALENTISSEMENT ({ratio_1h_vs_6h:.1f}x)"
        elif ratio_1h_vs_6h <= 0.3:
            signal_1h = "FORT_RALENTISSEMENT"
            emoji_1h = "🔴"
            text_1h = f"FORT RALENTISSEMENT ({ratio_1h_vs_6h:.1f}x)"
        else:
            signal_1h = "STABLE"
            emoji_1h = "➡️"
            text_1h = f"STABLE ({ratio_1h_vs_6h:.1f}x)"

        # Niveau 2: Moyen terme (6h vs 24h)
        if ratio_6h_vs_24h >= 1.8:
            signal_6h = "PUMP_EN_COURS"
            emoji_6h = "🚀"
            text_6h = f"Pump en cours ({ratio_6h_vs_24h:.1f}x)"
        elif ratio_6h_vs_24h >= 1.3:
            signal_6h = "HAUSSE_PROGRESSIVE"
            emoji_6h = "📊"
            text_6h = f"Hausse progressive ({ratio_6h_vs_24h:.1f}x)"
        elif ratio_6h_vs_24h <= 0.7:
            signal_6h = "BAISSE_TENDANCIELLE"
            emoji_6h = "📉"
            text_6h = f"Baisse tendancielle ({ratio_6h_vs_24h:.1f}x)"
        else:
            signal_6h = "STABLE"
            emoji_6h = "➡️"
            text_6h = f"Normal ({ratio_6h_vs_24h:.1f}x)"

        # VERDICT FINAL combinant les deux niveaux
        txt += f"📊 Volume Multi-Timeframe:\n"
        txt += f"   Court terme (1h): {emoji_1h} {text_1h}\n"
        txt += f"   Moyen terme (6h): {emoji_6h} {text_6h}\n"

        # PATTERN GAGNANTS (basé sur backtest)
        if signal_1h in ["FORTE_ACCELERATION", "ACCELERATION"] and signal_6h == "PUMP_EN_COURS":
            txt += f"✅ PATTERN: ENTRÉE IDÉALE - Pump actif + accélération récente 🎯\n"
        elif signal_1h == "FORTE_ACCELERATION" and signal_6h in ["HAUSSE_PROGRESSIVE", "STABLE"]:
            txt += f"✅ PATTERN: BON ENTRY - Nouveau pump qui démarre 🟢\n"
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"] and signal_6h == "PUMP_EN_COURS":
            txt += f"⚠️ PATTERN: SORTIE PROCHE - Volume qui faiblit (essoufflement) 🚪\n"
        elif signal_1h == "STABLE" and signal_6h == "PUMP_EN_COURS":
            txt += f"⏸️ PATTERN: CONSOLIDATION - Pause avant continuation possible\n"
        elif signal_1h in ["RALENTISSEMENT", "FORT_RALENTISSEMENT"]:
            txt += f"🔴 PATTERN: ÉVITER - Volume en chute libre ❌\n"

        # Afficher détails volumes
        txt += f"   Vol: 24h ${vol_24h/1000:.0f}K | 6h ${vol_6h/1000:.0f}K | 1h ${vol_1h/1000:.0f}K\n"

    # Volume spike ?
    elif vol_1h > 0:
        vol_1h_normalized = vol_1h * 24
        if vol_1h_normalized > vol_24h * 1.3:
            spike = ((vol_1h_normalized / vol_24h) - 1) * 100
            txt += f"⚡ Vol 1h: ${vol_1h/1000:.0f}K (x{vol_1h_normalized/vol_24h:.1f} activité!) 🔥\n"
        else:
            txt += f"📉 Vol 1h: ${vol_1h/1000:.0f}K\n"

    txt += f"💧 Liquidité: ${liq/1000:.0f}K\n"

    # Transactions 24h - Format explicite avec estimation traders (NOUVEAU)
    txt += f"🔄 Transactions 24h: {txns}\n"
    # Estimation traders: moyenne 2-3 tx par trader
    traders_estimate = int(txns / 2.5)  # Estimation conservative
    txt += f"👥 Traders estimés: ~{traders_estimate} (basé sur txns)\n"
    buys_pct = (buys / txns * 100) if txns > 0 else 0
    sells_pct = (sells / txns * 100) if txns > 0 else 0
    txt += f"   🟢 ACHATS: {buys} ({buys_pct:.0f}%)\n"
    txt += f"   🔴 VENTES: {sells} ({sells_pct:.0f}%)\n"

    # Pression dominante
    if buy_ratio_24h >= 1.0:
        txt += f"   ⚖️ Pression: ACHETEURS dominent (ratio {buy_ratio_24h:.2f})\n"
    elif buy_ratio_24h >= 0.8:
        txt += f"   ⚖️ Pression: ÉQUILIBRÉE (ratio {buy_ratio_24h:.2f})\n"
    else:
        txt += f"   ⚖️ Pression: VENDEURS dominent (ratio {buy_ratio_24h:.2f})\n"

    # Pression 1h (si différente)
    if buys_1h > 0 and sells_1h > 0 and abs(buy_ratio_1h - buy_ratio_24h) > 0.1:
        txt += f"\n📊 Pression 1h:\n"
        buys_1h_pct = (buys_1h / (buys_1h + sells_1h) * 100)
        sells_1h_pct = (sells_1h / (buys_1h + sells_1h) * 100)
        txt += f"   🟢 ACHATS: {buys_1h} ({buys_1h_pct:.0f}%)"

        if buy_ratio_1h > buy_ratio_24h:
            txt += f" ⬆️\n"
        else:
            txt += f" ⬇️\n"

        txt += f"   🔴 VENTES: {sells_1h} ({sells_1h_pct:.0f}%)"

        if buy_ratio_1h > buy_ratio_24h:
            txt += f" ⬇️\n"
        else:
            txt += f" ⬆️\n"

        # Analyse de la tendance de pression (focus sur l'évolution, pas les absolus)
        ratio_change = buy_ratio_1h - buy_ratio_24h

        if ratio_change > 0.1:  # Pression acheteuse augmente significativement
            txt += f"   ✅ ACHETEURS prennent le contrôle ! (+{ratio_change:.1%})\n"
        elif ratio_change < -0.1:  # Pression vendeuse augmente significativement
            txt += f"   ⚠️ VENDEURS prennent le contrôle ! ({ratio_change:.1%})\n"
        else:  # Pression stable
            if buy_ratio_1h >= 0.75:
                txt += f"   ➡️ Pression ACHETEUSE stable ({buy_ratio_1h:.0%})\n"
            elif buy_ratio_1h <= 0.55:
                txt += f"   ➡️ Pression VENDEUSE stable ({buy_ratio_1h:.0%})\n"
            else:
                txt += f"   ➡️ Équilibre acheteurs/vendeurs ({buy_ratio_1h:.0%})\n"

    txt += f"\n⚡ Vol/Liq: {ratio_vol_liq:.0f}%\n"
    txt += f"⏰ Créé il y a {age:.0f}h\n\n"

    # MULTI-POOL (si applicable)
    if multi_pool_data.get("is_multi_pool"):
        txt += f"━━━ MULTI-POOL ━━━\n"
        txt += f"🌐 Pools actifs: {multi_pool_data['num_pools']}\n"
        txt += f"📊 Volume total: ${multi_pool_data['total_volume']/1000:.0f}K\n"
        txt += f"💧 Liquidité totale: ${multi_pool_data['total_liquidity']/1000:.0f}K\n"

        # Détail pools
        for activity in multi_pool_data['pool_activities']:
            txt += f"   • {activity['pair']}: {activity['vol_liq_pct']:.0f}% Vol/Liq\n"

        if multi_pool_data.get("is_weth_dominant"):
            txt += f"⚡ WETH pool dominant = Smart money 🚀\n"
        txt += "\n"

    # SIGNAUX
    if signals:
        txt += f"━━━ SIGNAUX DÉTECTÉS ━━━\n"
        for signal in signals:
            txt += f"{signal}\n"
        txt += "\n"

    # ÉVALUATION DES CONDITIONS MARCHÉ POUR DÉCISION D'ENTRÉE
    should_enter, decision, analysis_reasons = evaluer_conditions_marche(
        pool_data, score, momentum, signal_1h, signal_6h
    )

    # ACTION RECOMMANDÉE - CONDITIONNELLE
    txt += f"━━━ ACTION RECOMMANDÉE ━━━\n"

    # Vérifier si on a une analyse TP avec nouveaux niveaux (alerte suivante)
    show_nouveaux_niveaux = (not is_first_alert and tracker is not None and
                             'analyse_tp' in locals() and
                             analyse_tp['decision'] == "NOUVEAUX_NIVEAUX")

    if show_nouveaux_niveaux:
        # ✅ NOUVEAUX NIVEAUX TP/SL (car TP précédents atteints + conditions favorables)
        txt += f"🚀 NOUVEAUX NIVEAUX - TP précédents atteints !\n\n"

        nouveaux = analyse_tp['nouveaux_niveaux']
        entry_new = nouveaux['entry_price']
        stop_loss_new = nouveaux['stop_loss_price']
        tp1_new = nouveaux['tp1_price']
        tp2_new = nouveaux['tp2_price']
        tp3_new = nouveaux['tp3_price']

        txt += f"⚡ Entry: {format_price(entry_new)} 🎯\n"
        txt += f"📍 Limite entrée: {format_price(entry_new * 1.03)} (max +3%)\n"
        txt += f"🛑 Stop loss: {format_price(stop_loss_new)} (-5%) ⚡ SL SERRÉ\n"
        txt += f"🎯 TP1 (50%): {format_price(tp1_new)} (+5%)\n"
        txt += f"🎯 TP2 (30%): {format_price(tp2_new)} (+10%)\n"
        txt += f"🎯 TP3 (20%): {format_price(tp3_new)} (+15%)\n"
        txt += f"🔄 Trail stop: -5% après TP1\n\n"

        txt += f"💡 NOTE: SL plus serré (-5%) car déjà en profit !\n\n"

    elif should_enter and decision == "BUY":
        # ✅ CONDITIONS FAVORABLES - Afficher Entry/SL/TP
        txt += f"✅ SIGNAL D'ENTRÉE VALIDÉ\n\n"

        # Afficher les raisons bullish
        if analysis_reasons['bullish']:
            txt += f"📈 Signaux haussiers:\n"
            for reason in analysis_reasons['bullish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        # FIX COHÉRENCE TP: Si alerte suivante, utiliser TP de l'alerte ORIGINALE
        if not is_first_alert and tracker is not None and 'previous_alert' in locals() and previous_alert:
            # Utiliser les TP de la première alerte (COHÉRENCE)
            entry_original = previous_alert.get('entry_price', price)
            sl_original = previous_alert.get('stop_loss_price', price * 0.90)
            tp1_original = previous_alert.get('tp1_price', price * 1.05)
            tp2_original = previous_alert.get('tp2_price', price * 1.10)
            tp3_original = previous_alert.get('tp3_price', price * 1.15)

            txt += f"⚡ Entry (alerte initiale): {format_price(entry_original)} 🎯\n"
            txt += f"📍 Limite entrée: {format_price(entry_original * 1.03)} (max +3%)\n"
            txt += f"🛑 Stop loss: {format_price(sl_original)} (-10%)\n"
            txt += f"🎯 TP1 (50%): {format_price(tp1_original)} (+5%)\n"
            txt += f"🎯 TP2 (30%): {format_price(tp2_original)} (+10%)\n"
            txt += f"🎯 TP3 (20%): {format_price(tp3_original)} (+15%)\n"
            txt += f"🔄 Trail stop: -5% après TP1\n\n"
        else:
            # Première alerte: calculer nouveaux TP depuis prix actuel
            price_max_entry = price * 1.03
            txt += f"⚡ Entry: {format_price(price)} 🎯\n"
            txt += f"📍 Limite entrée: {format_price(price_max_entry)} (max +3%)\n"

            # Stop loss
            stop_loss = price * 0.90
            txt += f"🛑 Stop loss: {format_price(stop_loss)} (-10%)\n"

            # Take profits
            tp1 = price * 1.05
            tp2 = price * 1.10
            tp3 = price * 1.15
            txt += f"🎯 TP1 (50%): {format_price(tp1)} (+5%)\n"
            txt += f"🎯 TP2 (30%): {format_price(tp2)} (+10%)\n"
            txt += f"🎯 TP3 (20%): {format_price(tp3)} (+15%)\n"
            txt += f"🔄 Trail stop: -5% après TP1\n\n"

    elif decision == "WAIT":
        # ⏸️ CONDITIONS INCERTAINES - Attendre
        txt += f"⏸️ ATTENDRE - Conditions pas encore idéales\n\n"

        # Afficher les raisons
        if analysis_reasons['bearish']:
            txt += f"⚠️ Signaux négatifs détectés:\n"
            for reason in analysis_reasons['bearish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        if analysis_reasons['bullish']:
            txt += f"✅ Signaux positifs:\n"
            for reason in analysis_reasons['bullish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        txt += f"💡 RECOMMANDATION:\n"
        txt += f"   • Surveiller l'évolution du volume et du prix\n"
        txt += f"   • Attendre confirmation d'une tendance haussière claire\n"
        txt += f"   • Entrer si le volume accélère et la pression acheteuse augmente\n"
        txt += f"   • Risque modéré - Prudence recommandée\n\n"

    else:  # EXIT
        # 🚫 CONDITIONS DÉFAVORABLES - Ne pas entrer / Sortir
        txt += f"🚫 PAS D'ENTRÉE - Sortie ou éviter le marché\n\n"

        # Afficher les raisons bearish
        if analysis_reasons['bearish']:
            txt += f"🔴 Raisons de sortie/éviter:\n"
            for reason in analysis_reasons['bearish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        # Afficher les points positifs s'il y en a
        if analysis_reasons['bullish']:
            txt += f"⚠️ Points positifs (insuffisants):\n"
            for reason in analysis_reasons['bullish']:
                txt += f"   • {reason}\n"
            txt += "\n"

        txt += f"💡 RECOMMANDATION:\n"

        # Déterminer si c'est un pump qui s'essouffle ou un token à éviter
        is_essoufflement = any("SORTIE" in r or "Essoufflement" in r or "Décélération" in r for r in analysis_reasons['bearish'])
        is_volume_problem = any("ÉVITER" in r or "RALENTISSEMENT" in r or "chute" in r for r in analysis_reasons['bearish'])

        if is_essoufflement:
            txt += f"   • ⚠️ SORTIR si vous êtes en position (pump s'essouffle)\n"
            txt += f"   • NE PAS ENTRER - Momentum en décélération\n"
            txt += f"   • Attendre un éventuel rebound seulement si volume se stabilise\n"
            txt += f"   • Risque élevé de correction\n"
        elif is_volume_problem:
            txt += f"   • 🔴 NE PAS ENTRER - Volume en chute\n"
            txt += f"   • Éviter ce token pour le moment\n"
            txt += f"   • Chercher d'autres opportunités avec volume sain\n"
            txt += f"   • Rebound peu probable sans nouvelle impulsion\n"
        else:
            txt += f"   • 🚫 Conditions actuelles défavorables\n"
            txt += f"   • NE PAS ENTRER tant que la situation ne s'améliore pas\n"
            txt += f"   • Surveiller pour un éventuel rebound avec:\n"
            txt += f"     - Reprise du volume\n"
            txt += f"     - Augmentation de la pression acheteuse\n"
            txt += f"     - Momentum redevenant positif\n"

        txt += "\n"

    # RISQUES
    txt += f"━━━ RISQUES ━━━\n"
    if age < 24:
        txt += f"⚠️ Très jeune ({age:.0f}h) - Volatilité élevée\n"
    elif age > 72:
        txt += f"⚠️ Age: {age:.0f}h (exit window passée?)\n"

    if pct_24h < -15:
        txt += f"⚠️ Variation 24h négative ({pct_24h:.1f}%) - Risque re-dump\n"

    if liq >= 500000:
        txt += f"✅ Liquidité solide (${liq/1000:.0f}K) - Faible risque rug\n"
    elif liq >= 200000:
        txt += f"⚠️ Liquidité moyenne (${liq/1000:.0f}K) - Prudence\n"
    else:
        txt += f"🚨 Liquidité faible (${liq/1000:.0f}K) - Risque élevé\n"

    txt += f"\n🔗 https://geckoterminal.com/{network_id.lower()}/pools/{pool_data['pool_address']}\n"

    return txt, regle5_data

# ============================================
# SCAN PRINCIPAL
