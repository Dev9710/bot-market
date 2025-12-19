"""
Script de validation simple de l'integration REGLE 5
"""
import sys
import os

def test_imports():
    """Test 1: Verifier les imports Python."""
    print("\n" + "="*80)
    print("TEST 1: Validation Imports Python")
    print("="*80)

    try:
        print("Import alert_tracker...", end=" ")
        import alert_tracker
        print("OK")

        print("Import geckoterminal_scanner_v2...", end=" ")
        import geckoterminal_scanner_v2
        print("OK")

        return True
    except Exception as e:
        print(f"ERREUR\n   {e}")
        return False

def test_db_schema():
    """Test 2: Creer DB temporaire et verifier schema."""
    print("\n" + "="*80)
    print("TEST 2: Validation Schema Base de Donnees")
    print("="*80)

    try:
        import sqlite3
        from alert_tracker import AlertTracker

        test_db = "test_regle5.db"
        if os.path.exists(test_db):
            os.remove(test_db)

        print(f"Creation DB temporaire '{test_db}'...")
        tracker = AlertTracker(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(alerts)")
        columns = [col[1] for col in cursor.fetchall()]

        regle5_columns = [
            'velocite_pump',
            'type_pump',
            'decision_tp_tracking',
            'temps_depuis_alerte_precedente',
            'is_alerte_suivante'
        ]

        all_ok = True
        for col in regle5_columns:
            print(f"Colonne '{col}'...", end=" ")
            if col in columns:
                print("OK")
            else:
                print("MANQUANTE")
                all_ok = False

        conn.close()

        if os.path.exists(test_db):
            os.remove(test_db)
            print(f"DB temporaire supprimee")

        return all_ok
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

def test_save_alert():
    """Test 3: Simuler sauvegarde avec REGLE 5."""
    print("\n" + "="*80)
    print("TEST 3: Simulation Sauvegarde Alerte avec REGLE 5")
    print("="*80)

    try:
        from alert_tracker import AlertTracker

        test_db = "test_regle5_save.db"
        if os.path.exists(test_db):
            os.remove(test_db)

        tracker = AlertTracker(test_db)

        alert_data = {
            'token_name': 'TEST_TOKEN',
            'token_address': '0xTEST123',
            'network': 'eth',
            'price_at_alert': 0.5,
            'score': 75,
            'base_score': 65,
            'momentum_bonus': 10,
            'confidence_score': 80,
            'volume_24h': 1000000,
            'volume_6h': 500000,
            'volume_1h': 100000,
            'liquidity': 500000,
            'buys_24h': 100,
            'sells_24h': 50,
            'buy_ratio': 2.0,
            'total_txns': 150,
            'age_hours': 24,
            'volume_acceleration_1h_vs_6h': 1.5,
            'volume_acceleration_6h_vs_24h': 1.3,
            'entry_price': 0.5,
            'stop_loss_price': 0.45,
            'stop_loss_percent': -10,
            'tp1_price': 0.525,
            'tp1_percent': 5,
            'tp2_price': 0.55,
            'tp2_percent': 10,
            'tp3_price': 0.575,
            'tp3_percent': 15,
            'alert_message': 'Test alert',
            'velocite_pump': 75.5,
            'type_pump': 'RAPIDE',
            'decision_tp_tracking': 'NOUVEAUX_NIVEAUX',
            'temps_depuis_alerte_precedente': 2.5,
            'is_alerte_suivante': 1
        }

        print("Sauvegarde alerte test...", end=" ")
        alert_id = tracker.save_alert(alert_data)

        if alert_id > 0:
            print(f"OK (ID: {alert_id})")

            print("Verification donnees REGLE 5...", end=" ")
            saved_alert = tracker.get_last_alert_for_token('0xTEST123')

            if saved_alert and saved_alert.get('velocite_pump') == 75.5:
                print("OK")
                print("\nDetails alerte sauvegardee:")
                print(f"   - Velocite: {saved_alert['velocite_pump']}%/h")
                print(f"   - Type pump: {saved_alert['type_pump']}")
                print(f"   - Decision: {saved_alert['decision_tp_tracking']}")
                print(f"   - Temps ecoule: {saved_alert['temps_depuis_alerte_precedente']}h")
                print(f"   - Alerte suivante: {'Oui' if saved_alert['is_alerte_suivante'] else 'Non'}")
                result = True
            else:
                print("ERREUR - Donnees incorrectes")
                result = False
        else:
            print("ERREUR")
            result = False

        if os.path.exists(test_db):
            os.remove(test_db)
            print("DB temporaire supprimee")

        return result
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_documentation():
    """Test 4: Verifier documentation."""
    print("\n" + "="*80)
    print("TEST 4: Validation Documentation")
    print("="*80)

    docs = [
        'TP_TRACKING_IMPLEMENTATION.md',
        'REGLE5_VELOCITE_EXEMPLES.md',
        'REGLE5_INTEGRATION_COMPLETE.md',
        'DEPLOIEMENT_REGLE5.md'
    ]

    all_ok = True
    for doc in docs:
        print(f"Fichier '{doc}'...", end=" ")
        if os.path.exists(doc):
            print("OK")
        else:
            print("MANQUANT")
            all_ok = False

    return all_ok

def main():
    """Executer tous les tests."""
    print("\n" + "="*80)
    print("VALIDATION COMPLETE - INTEGRATION REGLE 5")
    print("="*80)

    tests = [
        ("Imports Python", test_imports),
        ("Schema Base de Donnees", test_db_schema),
        ("Sauvegarde avec REGLE 5", test_save_alert),
        ("Documentation", test_documentation)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nERREUR critique dans '{name}': {e}")
            results.append((name, False))

    print("\n" + "="*80)
    print("RESUME DES TESTS")
    print("="*80)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:8s} | {name}")

    all_passed = all(result for _, result in results)

    print("\n" + "="*80)
    if all_passed:
        print("TOUS LES TESTS SONT PASSES")
        print("="*80)
        print("\nL'integration REGLE 5 est COMPLETE et FONCTIONNELLE")
        print("\nProchaines etapes:")
        print("   1. Deployer sur Railway")
        print("   2. Surveiller les logs pendant 24-48h")
        print("   3. Lancer backtest apres 7 jours")
        print("\nConsultez DEPLOIEMENT_REGLE5.md pour les details")
        return 0
    else:
        print("CERTAINS TESTS ONT ECHOUE")
        print("="*80)
        print("\nVeuillez corriger les erreurs avant de deployer")
        return 1

if __name__ == "__main__":
    sys.exit(main())
