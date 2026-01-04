"""Test import du scanner après refactoring Phase 1 & 2"""
import geckoterminal_scanner_v3 as scanner
from utils.helpers import log, format_price, extract_base_token
from utils.telegram import send_telegram

print(f"✓ Scanner importé OK")
print(f"✓ {len(scanner.NETWORKS)} réseaux configurés: {scanner.NETWORKS}")
print(f"✓ Config Telegram: {'OK' if scanner.TELEGRAM_CHAT_ID else 'NON CONFIGURÉ'}")
print(f"✓ MIN_VELOCITE_PUMP: {scanner.MIN_VELOCITE_PUMP}")
print(f"✓ NETWORK_THRESHOLDS: {len(scanner.NETWORK_THRESHOLDS)} réseaux")

# Test utils
print(f"\n✓ Helpers importés OK")
print(f"✓ format_price(1.23456): {format_price(1.23456)}")
print(f"✓ format_price(0.056789): {format_price(0.056789)}")
print(f"✓ format_price(0.00012345): {format_price(0.00012345)}")
print(f"✓ extract_base_token('LAVA / USDT 0.01%'): {extract_base_token('LAVA / USDT 0.01%')}")
print(f"✓ Telegram module importé")

print("\n=== TEST PHASE 1 & 2 RÉUSSI ===")
