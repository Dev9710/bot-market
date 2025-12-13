# -*- coding: utf-8 -*-
"""
Script de test pour la vérification LP Lock
Teste plusieurs tokens sur différents réseaux
"""

import sys
import io
import json
import time

# Fix encoding BEFORE any imports
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

# NOW import the module
from security_checker import SecurityChecker

def test_token(checker, name, address, network):
    """Teste un token et affiche les résultats."""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*80}")
    print(f"📍 Address: {address}")
    print(f"🌐 Network: {network}")
    print()

    # Test LP Lock uniquement
    print("🔍 Vérification LP Lock...")
    lp_result = checker.check_lp_lock(address, network)

    print(f"\n📊 RÉSULTATS LP LOCK:")
    print(f"  ✓ Vérifié: {lp_result.get('checked', False)}")
    print(f"  🔒 Lockée: {lp_result.get('is_locked', False)}")

    if lp_result.get('is_locked'):
        print(f"  📈 Pourcentage lockée: {lp_result.get('lock_percentage', 0)}%")
        print(f"  ⏱️ Durée: {lp_result.get('lock_duration_days', 0)} jours")
        print(f"  🏢 Platform: {lp_result.get('locker_platform', 'unknown')}")

        if 'locked_holders' in lp_result:
            print(f"  👥 Holders lockés:")
            for holder in lp_result['locked_holders']:
                print(f"     - {holder['platform']}: {holder['percentage']:.2f}%")

    print(f"  📡 Source: {lp_result.get('source', 'unknown')}")

    if 'liquidity_usd' in lp_result:
        print(f"  💰 Liquidité: ${lp_result['liquidity_usd']:,.2f}")

    if 'error' in lp_result:
        print(f"  ⚠️ Erreur: {lp_result['error']}")

    print()

def main():
    print("="*80)
    print("🚀 TEST DE VÉRIFICATION LP LOCK")
    print("="*80)
    print()

    checker = SecurityChecker()

    # Liste de tokens à tester (exemples)
    test_cases = [
        {
            'name': 'PEPE (Ethereum)',
            'address': '0x6982508145454Ce325dDbE47a25d4ec3d2311933',
            'network': 'eth'
        },
        {
            'name': 'SHIB (Ethereum)',
            'address': '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE',
            'network': 'eth'
        },
        {
            'name': 'Cake (BSC)',
            'address': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
            'network': 'bsc'
        }
    ]

    # Tester chaque token
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'#'*80}")
        print(f"# Test {i}/{len(test_cases)}")
        print(f"{'#'*80}")

        test_token(
            checker,
            test['name'],
            test['address'],
            test['network']
        )

        if i < len(test_cases):
            print("\n⏳ Pause de 2 secondes avant le prochain test...")
            import time
            time.sleep(2)

    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80)

if __name__ == "__main__":
    main()