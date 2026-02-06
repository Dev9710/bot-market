"""
Test script for V4.1 settings validation
Run: python test_v4_settings.py
"""
import sys
sys.path.insert(0, '.')

from config.settings import (
    calculate_dynamic_tps,
    is_in_age_danger_zone,
    passes_v4_filters,
    calculate_vol_liq_ratio,
    is_optimal_vol_liq,
    is_optimal_time,
    get_alert_quality_score,
    NETWORK_SCORE_FILTERS,
    NETWORK_AGE_DANGER_ZONES,
    NETWORK_VOL_LIQ_RANGES,
    DASHBOARD_CONFIG,
    STOP_LOSS_PERCENT,
    TP_MULTIPLIERS,
    DANGER_HOURS_UTC,
    OPTIMAL_HOURS_UTC,
)

print("=" * 70)
print("V4.1 SETTINGS VALIDATION")
print("=" * 70)

# Test 1: Dynamic TP calculation
print("\n[TEST 1] Dynamic TP Calculation")
print("-" * 50)
test_velocities = [10, 20, 30, 50, 80]
for vel in test_velocities:
    tps = calculate_dynamic_tps(vel)
    print(f"Velocite {vel:>2}: TP1={tps['TP1']:>5.1f}% | TP2={tps['TP2']:>5.1f}% | TP3={tps['TP3']:>5.1f}% | SL={tps['SL']}%")

# Test 2: Vol/Liq ratio check (NEW V4.1!)
print("\n[TEST 2] Vol/Liq Ratio Optimization (V4.1 NEW!)")
print("-" * 50)
vol_liq_tests = [
    ('solana', 1.5, False),   # Below optimal (2.0-5.0)
    ('solana', 3.0, True),    # In optimal range
    ('solana', 6.0, False),   # Above optimal
    ('eth', 3.0, False),      # Below optimal (5.0+)
    ('eth', 8.0, True),       # Good
    ('base', 5.0, False),     # Below optimal (10.0+)
    ('base', 25.0, True),     # Good
    ('bsc', 0.5, False),      # Below optimal (1.0-3.0)
    ('bsc', 2.0, True),       # In optimal
    ('bsc', 5.0, False),      # Above optimal
]
print(f"{'Network':<10} {'Vol/Liq':>8} {'Expected':>10} {'Result':>10} {'Status':>8}")
for network, ratio, expected in vol_liq_tests:
    is_good, reason = is_optimal_vol_liq(network, ratio)
    status = "OK" if is_good == expected else "FAIL"
    result = "OPTIMAL" if is_good else f"REJECT"
    print(f"{network:<10} {ratio:>8.1f} {'OPTIMAL' if expected else 'REJECT':>10} {result:>10} {status:>8}")

# Test 3: Time filtering (NEW V4.1!)
print("\n[TEST 3] Time-Based Filtering (V4.1 NEW!)")
print("-" * 50)
print(f"Danger hours (UTC): {DANGER_HOURS_UTC}")
print(f"Optimal hours (UTC): {OPTIMAL_HOURS_UTC}")
time_tests = [
    (2, True),    # Optimal hour
    (8, False),   # Danger hour
    (12, False),  # Danger hour
    (17, True),   # Optimal hour
    (21, True),   # Optimal hour
]
print(f"\n{'Hour UTC':>10} {'Expected':>10} {'Result':>10} {'Status':>8}")
for hour, expected in time_tests:
    is_good, reason = is_optimal_time(hour)
    status = "OK" if is_good == expected else "FAIL"
    result = "GOOD" if is_good else "AVOID"
    print(f"{hour:>10}:00 {'GOOD' if expected else 'AVOID':>10} {result:>10} {status:>8}")

# Test 4: Full V4.1 filter validation
print("\n[TEST 4] Complete V4.1 Filter Chain")
print("-" * 50)
filter_tests = [
    # (network, score, vel, buy_ratio, liq, age, volume, hour, should_pass, description)
    ('solana', 100, 10, 1.2, 300000, 10, 900000, 3, True, "Perfect Solana (Vol/Liq=3.0)"),
    ('solana', 100, 10, 1.2, 300000, 10, 300000, 3, False, "Solana Vol/Liq too low (1.0)"),
    ('solana', 100, 10, 1.2, 300000, 10, 900000, 12, False, "Solana bad hour (12 UTC)"),
    ('eth', 90, 35, 1.1, 50000, 3, 300000, 17, True, "Perfect ETH (Vol/Liq=6.0)"),
    ('eth', 90, 35, 1.1, 50000, 3, 100000, 17, False, "ETH Vol/Liq too low (2.0)"),
    ('base', 85, 35, 1.1, 500000, 48, 10000000, 21, True, "Perfect BASE (Vol/Liq=20)"),
    ('bsc', 95, 10, 1.1, 100000, 10, 200000, 4, True, "Perfect BSC (Vol/Liq=2.0)"),
]
for network, score, vel, buy_ratio, liq, age, vol, hour, should_pass, desc in filter_tests:
    passes, reason = passes_v4_filters(network, score, vel, buy_ratio, liq, age, vol, hour)
    status = "OK" if passes == should_pass else "FAIL"
    result_str = "PASS" if passes else f"REJECT: {reason}"
    print(f"{status}: {desc}")
    print(f"      -> {result_str}")

# Test 5: Quality scoring system
print("\n[TEST 5] Alert Quality Scoring System (V4.1 NEW!)")
print("-" * 50)
quality_tests = [
    ('solana', 100, 50, 1.5, 3.0, 3),   # Golden candidate
    ('solana', 95, 30, 1.2, 3.5, 17),   # Silver candidate
    ('eth', 90, 20, 1.1, 8.0, 14),      # Bronze (bad hour)
    ('bsc', 85, 10, 1.0, 2.0, 8),       # Standard (low vel, bad hour)
]
print(f"{'Network':<10} {'Score':>6} {'Vel':>5} {'V/L':>5} {'Hour':>5} {'Quality':>8} {'Tier':>8}")
for network, score, vel, buy_ratio, vol_liq, hour in quality_tests:
    result = get_alert_quality_score(network, score, vel, buy_ratio, vol_liq, hour)
    print(f"{network:<10} {score:>6} {vel:>5} {vol_liq:>5.1f} {hour:>5} {result['quality_score']:>8} {result['tier']:>8}")

# Summary
print("\n" + "=" * 70)
print("V4.1 CONFIGURATION SUMMARY")
print("=" * 70)

print(f"\nTP Multipliers: {TP_MULTIPLIERS}")
print(f"Stop Loss: {STOP_LOSS_PERCENT}%")

print(f"\nVol/Liq Optimal Ranges (V4.1 NEW!):")
for network, bounds in NETWORK_VOL_LIQ_RANGES.items():
    min_r, max_r = bounds
    max_str = str(max_r) if max_r else "unlimited"
    print(f"  {network:>12}: {min_r} - {max_str}")

print(f"\nTime Filtering (V4.1 NEW!):")
print(f"  Danger hours (UTC): {DANGER_HOURS_UTC}")
print(f"  Optimal hours (UTC): {OPTIMAL_HOURS_UTC}")

print(f"\nNetwork Filters:")
for network, filters in NETWORK_SCORE_FILTERS.items():
    print(f"  {network:>12}: score>={filters['min_score']}, vel>={filters['min_velocity']}, buy>={filters['min_buy_ratio']}")

print(f"\nLiquidity Bounds:")
for network, bounds in DASHBOARD_CONFIG['LIQUIDITY'].items():
    print(f"  {network:>12}: ${bounds[0]:>7,} - ${bounds[1]:>10,}")

print(f"\nAge Danger Zones:")
for network, zone in NETWORK_AGE_DANGER_ZONES.items():
    if zone:
        print(f"  {network:>12}: {zone[0]}h - {zone[1]}h (AVOID)")
    else:
        print(f"  {network:>12}: None")

print("\n" + "=" * 70)
print("All V4.1 tests completed!")
print("=" * 70)
