"""
Test du système de TP Tracking
Simule une alerte suivante avec TP atteints
"""
import sys
sys.path.insert(0, 'c:\\Users\\ludo_\\Documents\\projets\\owner\\bot-market')

from alert_tracker import AlertTracker
from geckoterminal_scanner_v2 import analyser_alerte_suivante, generer_alerte_complete

# Initialiser le tracker
tracker = AlertTracker(db_path='alerts_history.db')

print("=" * 80)
print("TEST 1: Token avec TP1 atteint + conditions favorables")
print("=" * 80)

# Simuler une alerte précédente
previous_alert = {
    'id': 999,
    'token_name': 'TEST / USDT',
    'token_address': '0xTEST123',
    'network': 'bsc',
    'price_at_alert': 0.00001,
    'entry_price': 0.00001,
    'stop_loss_price': 0.000009,  # -10%
    'stop_loss_percent': -10.0,
    'tp1_price': 0.0000105,  # +5%
    'tp1_percent': 5.0,
    'tp2_price': 0.000011,   # +10%
    'tp2_percent': 10.0,
    'tp3_price': 0.0000115,  # +15%
    'tp3_percent': 15.0,
    'score': 80,
    'base_score': 60,
    'momentum_bonus': 20,
}

# Prix actuel = TP1 atteint (+8%)
current_price = 0.0000108

# Pool data actuel avec bonnes conditions
pool_data = {
    'name': 'TEST / USDT',
    'base_token_name': 'TEST',
    'pool_address': '0xTEST123',
    'network': 'bsc',
    'price_usd': current_price,
    'volume_24h': 500000,
    'volume_6h': 250000,
    'volume_1h': 100000,  # Forte accélération
    'liquidity': 300000,
    'price_change_24h': 15.0,
    'price_change_6h': 10.0,
    'price_change_3h': 8.0,
    'price_change_1h': 5.0,
    'buys_24h': 1200,
    'sells_24h': 600,
    'buys_1h': 300,
    'sells_1h': 100,
    'total_txns': 1800,
    'age_hours': 8,
    'confidence_score': 85
}

# Momentum favorable
momentum = {
    '1h': 5.0,
    '3h': 8.0,
    '6h': 10.0,
    '24h': 15.0
}

# Analyser
analyse = analyser_alerte_suivante(
    previous_alert, current_price, pool_data,
    score=85, momentum=momentum,
    signal_1h="FORTE_ACCELERATION",
    signal_6h="PUMP_EN_COURS"
)

print(f"\nDÉCISION: {analyse['decision']}")
print(f"TP ATTEINTS: {analyse['tp_hit']}")
print(f"GAINS TP: {analyse['tp_gains']}")
print(f"PRIX TROP ÉLEVÉ: {analyse['prix_trop_eleve']}")
print(f"CONDITIONS FAVORABLES: {analyse['conditions_favorables']}")
print(f"HAUSSE DEPUIS ALERTE: {analyse['hausse_depuis_alerte']:.1f}%")
print(f"\nRAISONS:")
for raison in analyse['raisons']:
    print(f"  {raison}")

if analyse['nouveaux_niveaux']:
    print(f"\n📊 NOUVEAUX NIVEAUX:")
    nv = analyse['nouveaux_niveaux']
    print(f"  Entry: ${nv['entry_price']:.8f}")
    print(f"  SL: ${nv['stop_loss_price']:.8f} ({nv['stop_loss_percent']:.1f}%)")
    print(f"  TP1: ${nv['tp1_price']:.8f} (+{nv['tp1_percent']:.1f}%)")
    print(f"  TP2: ${nv['tp2_price']:.8f} (+{nv['tp2_percent']:.1f}%)")
    print(f"  TP3: ${nv['tp3_price']:.8f} (+{nv['tp3_percent']:.1f}%)")

print("\n" + "=" * 80)
print("TEST 2: Token avec TP1+TP2 atteints + prix trop élevé (>20%)")
print("=" * 80)

# Prix actuel = TP2 atteint + hausse de 25% depuis alerte initiale
current_price_2 = 0.0000125  # +25% depuis entry

pool_data_2 = pool_data.copy()
pool_data_2['price_usd'] = current_price_2

analyse_2 = analyser_alerte_suivante(
    previous_alert, current_price_2, pool_data_2,
    score=75, momentum=momentum,
    signal_1h="RALENTISSEMENT",
    signal_6h="PUMP_EN_COURS"
)

print(f"\nDÉCISION: {analyse_2['decision']}")
print(f"TP ATTEINTS: {analyse_2['tp_hit']}")
print(f"GAINS TP: {analyse_2['tp_gains']}")
print(f"PRIX TROP ÉLEVÉ: {analyse_2['prix_trop_eleve']}")
print(f"HAUSSE DEPUIS ALERTE: {analyse_2['hausse_depuis_alerte']:.1f}%")
print(f"\nRAISONS:")
for raison in analyse_2['raisons']:
    print(f"  {raison}")

print("\n" + "=" * 80)
print("TEST 3: Token avec TP1 atteint + conditions devenues défavorables")
print("=" * 80)

# Pool data avec mauvaises conditions (volume en chute)
pool_data_3 = {
    'name': 'TEST / USDT',
    'base_token_name': 'TEST',
    'pool_address': '0xTEST123',
    'network': 'bsc',
    'price_usd': 0.0000106,  # TP1 atteint
    'volume_24h': 500000,
    'volume_6h': 100000,  # Baisse
    'volume_1h': 20000,   # Fort ralentissement
    'liquidity': 250000,  # Liquidité en baisse
    'price_change_24h': 8.0,
    'price_change_6h': 3.0,
    'price_change_1h': -2.0,  # Momentum négatif
    'buys_24h': 800,
    'sells_24h': 1200,  # Plus de ventes que d'achats
    'buys_1h': 50,
    'sells_1h': 150,
    'total_txns': 2000,
    'age_hours': 10,
    'confidence_score': 75
}

momentum_3 = {
    '1h': -2.0,
    '3h': 1.0,
    '6h': 3.0,
    '24h': 8.0
}

analyse_3 = analyser_alerte_suivante(
    previous_alert, 0.0000106, pool_data_3,
    score=65, momentum=momentum_3,
    signal_1h="FORT_RALENTISSEMENT",
    signal_6h="BAISSE_TENDANCIELLE"
)

print(f"\nDÉCISION: {analyse_3['decision']}")
print(f"TP ATTEINTS: {analyse_3['tp_hit']}")
print(f"CONDITIONS FAVORABLES: {analyse_3['conditions_favorables']}")
print(f"\nRAISONS:")
for raison in analyse_3['raisons']:
    print(f"  {raison}")

print("\n" + "=" * 80)
print("TEST 4: Aucun TP atteint")
print("=" * 80)

# Prix en dessous de TP1
current_price_4 = 0.00001  # Prix identique à l'entry

pool_data_4 = pool_data.copy()
pool_data_4['price_usd'] = current_price_4

analyse_4 = analyser_alerte_suivante(
    previous_alert, current_price_4, pool_data_4,
    score=80, momentum=momentum,
    signal_1h="STABLE",
    signal_6h="STABLE"
)

print(f"\nDÉCISION: {analyse_4['decision']}")
print(f"TP ATTEINTS: {analyse_4['tp_hit']}")
print(f"\nRAISONS:")
for raison in analyse_4['raisons']:
    print(f"  {raison}")

print("\n" + "=" * 80)
print("✅ TESTS TERMINÉS")
print("=" * 80)
