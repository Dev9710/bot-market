"""Test import du scanner après refactoring Phases 1-8"""
import geckoterminal_scanner_v3 as scanner
from utils.helpers import log, format_price, extract_base_token
from utils.telegram import send_telegram
from core.scanner_steps import (
    collect_pools_from_networks,
    update_price_max_for_tracked_tokens,
    analyze_and_filter_tokens,
    process_and_send_alerts,
    track_active_alerts,
    report_liquidity_stats,
)
from core.filters import is_valid_opportunity

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

# Test Phase 8 - Scanner Steps
print(f"\n✓ Scanner Steps modules importés OK")
print(f"✓ collect_pools_from_networks")
print(f"✓ update_price_max_for_tracked_tokens")
print(f"✓ analyze_and_filter_tokens")
print(f"✓ process_and_send_alerts")
print(f"✓ track_active_alerts")
print(f"✓ report_liquidity_stats")
print(f"✓ is_valid_opportunity")

print("\n=== TEST PHASES 1-8 RÉUSSI ===")
