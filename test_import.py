"""Test import du scanner après refactoring Phase 1"""
import geckoterminal_scanner_v3 as scanner

print(f"✓ Import OK")
print(f"✓ {len(scanner.NETWORKS)} réseaux configurés: {scanner.NETWORKS}")
print(f"✓ Config Telegram: {'OK' if scanner.TELEGRAM_CHAT_ID else 'NON CONFIGURÉ'}")
print(f"✓ MIN_VELOCITE_PUMP: {scanner.MIN_VELOCITE_PUMP}")
print(f"✓ NETWORK_THRESHOLDS: {len(scanner.NETWORK_THRESHOLDS)} réseaux")
print("\n=== TEST PHASE 1 RÉUSSI ===")
