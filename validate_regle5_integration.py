"""
Script de validation complète de l'intégration RÈGLE 5
Vérifie que tous les composants sont correctement connectés
"""
import sys
import os

def test_imports():
    """Test 1: Vérifier que les fichiers Python sont importables."""
    print("\n" + "="*80)
    print("TEST 1: Validation Imports Python")
    print("="*80)

    try:
        # Test import alert_tracker
        print("📦 Import alert_tracker...", end=" ")
        import alert_tracker
        print("✅")

        # Test import scanner
        print("📦 Import geckoterminal_scanner_v2...", end=" ")
        import geckoterminal_scanner_v2
        print("✅")

        return True
    except Exception as e:
        print(f"❌\n   Erreur: {e}")
        return False

def test_alert_tracker_methods():
    """Test 2: Vérifier que les méthodes AlertTracker existent."""
    print("\n" + "="*80)
    print("TEST 2: Validation Méthodes AlertTracker")
    print("="*80)

    try:
        from alert_tracker import AlertTracker

        # Vérifier méthodes
        methods = ['save_alert', 'get_last_alert_for_token', 'create_tables']

        for method in methods:
            print(f"🔍 Méthode '{method}'...", end=" ")
            if hasattr(AlertTracker, method):
                print("✅")
            else:
                print("❌ MANQUANTE")
                return False

        return True
    except Exception as e:
        print(f"❌\n   Erreur: {e}")
        return False

def test_scanner_functions():
    """Test 3: Vérifier que les fonctions du scanner existent."""
    print("\n" + "="*80)
    print("TEST 3: Validation Fonctions Scanner")
    print("="*80)

    try:
        import geckoterminal_scanner_v2 as scanner

        # Vérifier fonctions
        functions = ['analyser_alerte_suivante', 'generer_alerte_complete']

        for func in functions:
            print(f"🔍 Fonction '{func}'...", end=" ")
            if hasattr(scanner, func):
                print("✅")
            else:
                print("❌ MANQUANTE")
                return False

        return True
    except Exception as e:
        print(f"❌\n   Erreur: {e}")
        return False

def test_db_schema():
    """Test 4: Créer une DB temporaire et vérifier le schéma."""
    print("\n" + "="*80)
    print("TEST 4: Validation Schéma Base de Données")
    print("="*80)

    try:
        import sqlite3
        from alert_tracker import AlertTracker

        # Créer DB temporaire
        test_db = "test_regle5.db"
        if os.path.exists(test_db):
            os.remove(test_db)

        print(f"📁 Création DB temporaire '{test_db}'...")
        tracker = AlertTracker(test_db)

        # Vérifier colonnes RÈGLE 5
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
            print(f"🔍 Colonne '{col}'...", end=" ")
            if col in columns:
                print("✅")
            else:
                print("❌ MANQUANTE")
                all_ok = False

        conn.close()

        # Nettoyer
        if os.path.exists(test_db):
            os.remove(test_db)
            print(f"🧹 DB temporaire supprimée")

        return all_ok
    except Exception as e:
        print(f"❌\n   Erreur: {e}")
        return False

def test_save_alert_with_regle5():
    """Test 5: Simuler une sauvegarde d'alerte avec données RÈGLE 5."""
    print("\n" + "="*80)
    print("TEST 5: Simulation Sauvegarde Alerte avec RÈGLE 5")
    print("="*80)

    try:
        import sqlite3
        from alert_tracker import AlertTracker

        # Créer DB temporaire
        test_db = "test_regle5_save.db"
        if os.path.exists(test_db):
            os.remove(test_db)

        tracker = AlertTracker(test_db)

        # Données alerte de test
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
            # RÈGLE 5
            'velocite_pump': 75.5,
            'type_pump': 'RAPIDE',
            'decision_tp_tracking': 'NOUVEAUX_NIVEAUX',
            'temps_depuis_alerte_precedente': 2.5,
            'is_alerte_suivante': 1
        }

        print("💾 Sauvegarde alerte test...", end=" ")
        alert_id = tracker.save_alert(alert_data)

        if alert_id > 0:
            print(f"✅ (ID: {alert_id})")

            # Vérifier que les données RÈGLE 5 ont bien été sauvegardées
            print("🔍 Vérification données RÈGLE 5...", end=" ")
            saved_alert = tracker.get_last_alert_for_token('0xTEST123')

            if saved_alert:
                checks = [
                    ('velocite_pump', 75.5),
                    ('type_pump', 'RAPIDE'),
                    ('decision_tp_tracking', 'NOUVEAUX_NIVEAUX'),
                    ('temps_depuis_alerte_precedente', 2.5),
                    ('is_alerte_suivante', 1)
                ]

                all_ok = True
                for key, expected in checks:
                    if key in saved_alert:
                        actual = saved_alert[key]
                        if actual == expected:
                            continue
                        else:
                            print(f"\n   ❌ {key}: attendu={expected}, reçu={actual}")
                            all_ok = False
                    else:
                        print(f"\n   ❌ {key}: MANQUANT")
                        all_ok = False

                if all_ok:
                    print("✅")
                    print("\n📊 Détails de l'alerte sauvegardée:")
                    print(f"   - Vélocité: {saved_alert['velocite_pump']}%/h")
                    print(f"   - Type pump: {saved_alert['type_pump']}")
                    print(f"   - Décision: {saved_alert['decision_tp_tracking']}")
                    print(f"   - Temps écoulé: {saved_alert['temps_depuis_alerte_precedente']}h")
                    print(f"   - Alerte suivante: {'Oui' if saved_alert['is_alerte_suivante'] else 'Non'}")
                else:
                    return False
            else:
                print("❌ Alerte non trouvée")
                return False
        else:
            print("❌")
            return False

        # Nettoyer
        if os.path.exists(test_db):
            os.remove(test_db)
            print("🧹 DB temporaire supprimée")

        return True
    except Exception as e:
        print(f"❌\n   Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_documentation():
    """Test 6: Vérifier que tous les fichiers de documentation existent."""
    print("\n" + "="*80)
    print("TEST 6: Validation Documentation")
    print("="*80)

    docs = [
        'TP_TRACKING_IMPLEMENTATION.md',
        'REGLE5_VELOCITE_EXEMPLES.md',
        'REGLE5_INTEGRATION_COMPLETE.md',
        'DEPLOIEMENT_REGLE5.md'
    ]

    all_ok = True
    for doc in docs:
        print(f"📄 Fichier '{doc}'...", end=" ")
        if os.path.exists(doc):
            print("✅")
        else:
            print("❌ MANQUANT")
            all_ok = False

    return all_ok

def main():
    """Exécuter tous les tests."""
    print("\n" + "="*80)
    print("VALIDATION COMPLETE - INTEGRATION REGLE 5")
    print("="*80)

    tests = [
        ("Imports Python", test_imports),
        ("Méthodes AlertTracker", test_alert_tracker_methods),
        ("Fonctions Scanner", test_scanner_functions),
        ("Schéma Base de Données", test_db_schema),
        ("Sauvegarde avec RÈGLE 5", test_save_alert_with_regle5),
        ("Documentation", test_documentation)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Erreur critique dans '{name}': {e}")
            results.append((name, False))

    # Résumé
    print("\n" + "="*80)
    print("RESUME DES TESTS")
    print("="*80)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12s} | {name}")

    # Conclusion
    all_passed = all(result for _, result in results)

    print("\n" + "="*80)
    if all_passed:
        print("TOUS LES TESTS SONT PASSES")
        print("="*80)
        print("\nL'integration REGLE 5 est COMPLETE et FONCTIONNELLE")
        print("\nProchaines etapes:")
        print("   1. Deployer sur Railway: git push railway main")
        print("   2. Surveiller les logs pendant 24-48h")
        print("   3. Lancer backtest apres 7 jours de collecte")
        print("\nConsultez DEPLOIEMENT_REGLE5.md pour les instructions detaillees")
        return 0
    else:
        print("CERTAINS TESTS ONT ECHOUE")
        print("="*80)
        print("\nVeuillez corriger les erreurs avant de deployer")
        return 1

if __name__ == "__main__":
    sys.exit(main())
