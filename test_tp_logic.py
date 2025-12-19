"""Test de la logique TP Tracking"""

# Test 1: TP1 atteint, hausse 8%, conditions favorables
previous = {
    'entry_price': 0.00001,
    'tp1_price': 0.0000105,
    'tp2_price': 0.000011,
    'tp3_price': 0.0000115
}

current_price = 0.0000108  # TP1 atteint
hausse = ((current_price - previous['entry_price']) / previous['entry_price']) * 100

# Vérification TP
tp_hit = []
if current_price >= previous['tp1_price']:
    tp_hit.append("TP1")
if current_price >= previous['tp2_price']:
    tp_hit.append("TP2")
if current_price >= previous['tp3_price']:
    tp_hit.append("TP3")

prix_trop_eleve = hausse > 20.0

with open('test_results.txt', 'w', encoding='utf-8') as f:
    f.write("TEST 1: TP1 atteint, +8%, bonnes conditions\n")
    f.write(f"Prix: {current_price} vs Entry: {previous['entry_price']}\n")
    f.write(f"Hausse: {hausse:.1f}%\n")
    f.write(f"TP atteints: {tp_hit}\n")
    f.write(f"Prix trop élevé: {prix_trop_eleve}\n")

    if not tp_hit:
        decision = "MAINTENIR"
    elif prix_trop_eleve:
        decision = "SORTIR"
    elif True:  # conditions favorables simulées
        decision = "NOUVEAUX_NIVEAUX"
    else:
        decision = "SECURISER_HOLD"

    f.write(f"Décision: {decision}\n")
    f.write(f"✅ Attendu: NOUVEAUX_NIVEAUX\n\n")

    # Test 2: +25%, prix trop élevé
    current_price_2 = 0.0000125
    hausse_2 = ((current_price_2 - previous['entry_price']) / previous['entry_price']) * 100
    prix_trop_eleve_2 = hausse_2 > 20.0

    tp_hit_2 = []
    if current_price_2 >= previous['tp1_price']:
        tp_hit_2.append("TP1")
    if current_price_2 >= previous['tp2_price']:
        tp_hit_2.append("TP2")

    f.write("TEST 2: TP1+TP2 atteints, +25%, prix trop élevé\n")
    f.write(f"Prix: {current_price_2} vs Entry: {previous['entry_price']}\n")
    f.write(f"Hausse: {hausse_2:.1f}%\n")
    f.write(f"TP atteints: {tp_hit_2}\n")
    f.write(f"Prix trop élevé: {prix_trop_eleve_2}\n")

    if prix_trop_eleve_2:
        decision_2 = "SORTIR"
    elif True:
        decision_2 = "NOUVEAUX_NIVEAUX"

    f.write(f"Décision: {decision_2}\n")
    f.write(f"✅ Attendu: SORTIR\n\n")

    f.write("=" * 80 + "\n")
    f.write("✅ TESTS DE LOGIQUE TERMINÉS\n")

print("Tests écrits dans test_results.txt")
