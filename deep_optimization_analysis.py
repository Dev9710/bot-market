"""
Deep Optimization Analysis V4.1
Find hidden patterns and micro-optimizations to maximize win rate
"""
import json
import sys
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Load data
print("Loading database...")
with open(r'c:\Users\ludo_\Documents\projets\owner\bot-market\exports\railway_alerts_latest.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alerts = data['alerts']
print(f"Loaded {len(alerts):,} alerts\n")

# Helper functions
def get_outcome(alert):
    """Determine win/loss/timeout"""
    ht = alert.get('highest_tp_reached')
    if ht and ht in ['TP1', 'TP2', 'TP3', 1, 2, 3]:
        return 'WIN'
    elif alert.get('hit_stop_loss'):
        return 'LOSS'
    return 'TIMEOUT'

def safe_float(val, default=0):
    try:
        return float(val) if val else default
    except:
        return default

def analyze_metric_ranges(alerts, metric_name, getter_func, ranges, network_filter=None):
    """Analyze win rate across different ranges of a metric"""
    results = {}
    for range_name, (min_val, max_val) in ranges.items():
        filtered = []
        for a in alerts:
            if network_filter and a.get('network', '').lower() != network_filter.lower():
                continue
            val = getter_func(a)
            if val is not None and min_val <= val < max_val:
                filtered.append(a)

        if len(filtered) >= 20:  # Minimum sample size
            wins = sum(1 for a in filtered if get_outcome(a) == 'WIN')
            wr = wins / len(filtered) * 100
            results[range_name] = {'count': len(filtered), 'win_rate': wr, 'range': (min_val, max_val)}
    return results

print("=" * 70)
print("DEEP OPTIMIZATION ANALYSIS V4.1")
print("=" * 70)

# =============================================================================
# 1. VOL/LIQ RATIO OPTIMIZATION
# =============================================================================
print("\n[1] VOL/LIQ RATIO OPTIMIZATION")
print("-" * 50)

vol_liq_ranges = {
    '0.0-0.5': (0, 0.5),
    '0.5-1.0': (0.5, 1.0),
    '1.0-2.0': (1.0, 2.0),
    '2.0-5.0': (2.0, 5.0),
    '5.0-10.0': (5.0, 10.0),
    '10.0-20.0': (10.0, 20.0),
    '20.0+': (20.0, 1000),
}

def get_vol_liq(a):
    vol = safe_float(a.get('volume_24h'))
    liq = safe_float(a.get('liquidity'))
    if liq > 0:
        return vol / liq
    return None

results = analyze_metric_ranges(alerts, 'Vol/Liq', get_vol_liq, vol_liq_ranges)
print(f"{'Range':<15} {'Count':>8} {'Win Rate':>10}")
best_vol_liq = None
best_vol_liq_wr = 0
for name, data in sorted(results.items(), key=lambda x: x[1]['win_rate'], reverse=True):
    marker = " <-- BEST" if data['win_rate'] == max(r['win_rate'] for r in results.values()) else ""
    print(f"{name:<15} {data['count']:>8,} {data['win_rate']:>9.1f}%{marker}")
    if data['win_rate'] > best_vol_liq_wr and data['count'] >= 100:
        best_vol_liq_wr = data['win_rate']
        best_vol_liq = data['range']

# =============================================================================
# 2. TRANSACTION COUNT OPTIMIZATION
# =============================================================================
print("\n[2] TRANSACTION COUNT (txns_24h) OPTIMIZATION")
print("-" * 50)

txn_ranges = {
    '0-100': (0, 100),
    '100-500': (100, 500),
    '500-1000': (500, 1000),
    '1000-2000': (1000, 2000),
    '2000-5000': (2000, 5000),
    '5000-10000': (5000, 10000),
    '10000+': (10000, 1000000),
}

def get_txns(a):
    return safe_float(a.get('txns_24h'))

results = analyze_metric_ranges(alerts, 'Txns', get_txns, txn_ranges)
print(f"{'Range':<15} {'Count':>8} {'Win Rate':>10}")
for name, data in sorted(results.items(), key=lambda x: x[1]['win_rate'], reverse=True):
    marker = " <-- BEST" if data['win_rate'] == max(r['win_rate'] for r in results.values()) else ""
    print(f"{name:<15} {data['count']:>8,} {data['win_rate']:>9.1f}%{marker}")

# =============================================================================
# 3. PRICE CHANGE 1H AT ENTRY
# =============================================================================
print("\n[3] PRICE CHANGE 1H AT ENTRY")
print("-" * 50)

price_1h_ranges = {
    'negative': (-100, 0),
    '0-5%': (0, 5),
    '5-10%': (5, 10),
    '10-20%': (10, 20),
    '20-50%': (20, 50),
    '50-100%': (50, 100),
    '100%+': (100, 10000),
}

def get_price_1h(a):
    return safe_float(a.get('price_change_1h'))

results = analyze_metric_ranges(alerts, 'Price 1h', get_price_1h, price_1h_ranges)
print(f"{'Range':<15} {'Count':>8} {'Win Rate':>10}")
for name, data in sorted(results.items(), key=lambda x: x[1]['win_rate'], reverse=True):
    marker = " <-- BEST" if data['win_rate'] == max(r['win_rate'] for r in results.values()) else ""
    print(f"{name:<15} {data['count']:>8,} {data['win_rate']:>9.1f}%{marker}")

# =============================================================================
# 4. SCORE GRANULAR ANALYSIS
# =============================================================================
print("\n[4] SCORE GRANULAR ANALYSIS (by 5-point increments)")
print("-" * 50)

score_ranges = {
    '60-65': (60, 65),
    '65-70': (65, 70),
    '70-75': (70, 75),
    '75-80': (75, 80),
    '80-85': (80, 85),
    '85-90': (85, 90),
    '90-95': (90, 95),
    '95-100': (95, 100),
    '100': (100, 101),
}

def get_score(a):
    return safe_float(a.get('score'))

results = analyze_metric_ranges(alerts, 'Score', get_score, score_ranges)
print(f"{'Range':<15} {'Count':>8} {'Win Rate':>10}")
for name, data in sorted(results.items(), key=lambda x: x[1]['range'][0]):
    print(f"{name:<15} {data['count']:>8,} {data['win_rate']:>9.1f}%")

# =============================================================================
# 5. VELOCITE GRANULAR ANALYSIS
# =============================================================================
print("\n[5] VELOCITE GRANULAR ANALYSIS")
print("-" * 50)

vel_ranges = {
    '0-10': (0, 10),
    '10-20': (10, 20),
    '20-30': (20, 30),
    '30-40': (30, 40),
    '40-50': (40, 50),
    '50-75': (50, 75),
    '75-100': (75, 100),
    '100+': (100, 10000),
}

def get_vel(a):
    return safe_float(a.get('velocite_pump'))

results = analyze_metric_ranges(alerts, 'Velocite', get_vel, vel_ranges)
print(f"{'Range':<15} {'Count':>8} {'Win Rate':>10}")
for name, data in sorted(results.items(), key=lambda x: x[1]['range'][0]):
    print(f"{name:<15} {data['count']:>8,} {data['win_rate']:>9.1f}%")

# =============================================================================
# 6. BUY/SELL RATIO GRANULAR
# =============================================================================
print("\n[6] BUY/SELL RATIO GRANULAR ANALYSIS")
print("-" * 50)

buy_ranges = {
    '0.0-0.5': (0, 0.5),
    '0.5-0.8': (0.5, 0.8),
    '0.8-1.0': (0.8, 1.0),
    '1.0-1.2': (1.0, 1.2),
    '1.2-1.5': (1.2, 1.5),
    '1.5-2.0': (1.5, 2.0),
    '2.0-3.0': (2.0, 3.0),
    '3.0+': (3.0, 100),
}

def get_buy_ratio(a):
    return safe_float(a.get('buy_sell_ratio'))

results = analyze_metric_ranges(alerts, 'Buy Ratio', get_buy_ratio, buy_ranges)
print(f"{'Range':<15} {'Count':>8} {'Win Rate':>10}")
for name, data in sorted(results.items(), key=lambda x: x[1]['range'][0]):
    marker = " <-- OPTIMAL" if data['win_rate'] == max(r['win_rate'] for r in results.values()) else ""
    print(f"{name:<15} {data['count']:>8,} {data['win_rate']:>9.1f}%{marker}")

# =============================================================================
# 7. HOUR OF DAY ANALYSIS
# =============================================================================
print("\n[7] HOUR OF DAY ANALYSIS (UTC)")
print("-" * 50)

hour_stats = defaultdict(lambda: {'wins': 0, 'total': 0})
for a in alerts:
    try:
        created = a.get('created_at', '')
        if created:
            if 'T' in created:
                hour = int(created.split('T')[1].split(':')[0])
            else:
                hour = int(created.split(' ')[1].split(':')[0])
            outcome = get_outcome(a)
            hour_stats[hour]['total'] += 1
            if outcome == 'WIN':
                hour_stats[hour]['wins'] += 1
    except:
        pass

print(f"{'Hour (UTC)':<12} {'Count':>8} {'Win Rate':>10}")
best_hours = []
worst_hours = []
for hour in range(24):
    if hour_stats[hour]['total'] >= 100:
        wr = hour_stats[hour]['wins'] / hour_stats[hour]['total'] * 100
        marker = ""
        if wr >= 35:
            marker = " <-- GOOD"
            best_hours.append(hour)
        elif wr < 25:
            marker = " <-- AVOID"
            worst_hours.append(hour)
        print(f"{hour:02d}:00-{hour:02d}:59 {hour_stats[hour]['total']:>8,} {wr:>9.1f}%{marker}")

# =============================================================================
# 8. DAY OF WEEK ANALYSIS
# =============================================================================
print("\n[8] DAY OF WEEK ANALYSIS")
print("-" * 50)

day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_stats = defaultdict(lambda: {'wins': 0, 'total': 0})
for a in alerts:
    try:
        created = a.get('created_at', '')
        if created:
            dt = datetime.fromisoformat(created.replace('Z', '+00:00').split('+')[0])
            day = dt.weekday()
            outcome = get_outcome(a)
            day_stats[day]['total'] += 1
            if outcome == 'WIN':
                day_stats[day]['wins'] += 1
    except:
        pass

print(f"{'Day':<12} {'Count':>8} {'Win Rate':>10}")
for day in range(7):
    if day_stats[day]['total'] >= 100:
        wr = day_stats[day]['wins'] / day_stats[day]['total'] * 100
        marker = " <-- BEST" if wr >= 33 else (" <-- WORST" if wr < 28 else "")
        print(f"{day_names[day]:<12} {day_stats[day]['total']:>8,} {wr:>9.1f}%{marker}")

# =============================================================================
# 9. NETWORK-SPECIFIC DEEP DIVE
# =============================================================================
print("\n[9] NETWORK-SPECIFIC OPTIMAL COMBINATIONS")
print("-" * 50)

networks = ['solana', 'eth', 'base', 'bsc']
for network in networks:
    print(f"\n>>> {network.upper()} <<<")
    net_alerts = [a for a in alerts if a.get('network', '').lower() == network]

    # Find best velocity range for this network
    vel_results = analyze_metric_ranges(net_alerts, 'Vel', get_vel, vel_ranges)
    if vel_results:
        best_vel = max(vel_results.items(), key=lambda x: x[1]['win_rate'] if x[1]['count'] >= 50 else 0)
        print(f"  Best Velocite: {best_vel[0]} ({best_vel[1]['win_rate']:.1f}% WR, n={best_vel[1]['count']})")

    # Find best buy ratio for this network
    buy_results = analyze_metric_ranges(net_alerts, 'Buy', get_buy_ratio, buy_ranges)
    if buy_results:
        best_buy = max(buy_results.items(), key=lambda x: x[1]['win_rate'] if x[1]['count'] >= 50 else 0)
        print(f"  Best Buy Ratio: {best_buy[0]} ({best_buy[1]['win_rate']:.1f}% WR, n={best_buy[1]['count']})")

    # Find best vol/liq for this network
    vl_results = analyze_metric_ranges(net_alerts, 'V/L', get_vol_liq, vol_liq_ranges)
    if vl_results:
        best_vl = max(vl_results.items(), key=lambda x: x[1]['win_rate'] if x[1]['count'] >= 50 else 0)
        print(f"  Best Vol/Liq: {best_vl[0]} ({best_vl[1]['win_rate']:.1f}% WR, n={best_vl[1]['count']})")

# =============================================================================
# 10. MULTI-FACTOR COMBINATION ANALYSIS
# =============================================================================
print("\n[10] MULTI-FACTOR WINNING COMBINATIONS")
print("-" * 50)

# Test combinations of filters
combinations = []
for a in alerts:
    score = safe_float(a.get('score'))
    vel = safe_float(a.get('velocite_pump'))
    buy_ratio = safe_float(a.get('buy_sell_ratio'))
    vol_liq = get_vol_liq(a) or 0
    outcome = get_outcome(a)

    # Define filter combinations
    filters = {
        'score_95+': score >= 95,
        'score_100': score == 100,
        'vel_30+': vel >= 30,
        'vel_50+': vel >= 50,
        'buy_1.2+': buy_ratio >= 1.2,
        'buy_1.5+': buy_ratio >= 1.5,
        'vol_liq_2+': vol_liq >= 2.0,
        'vol_liq_5+': vol_liq >= 5.0,
    }

    combinations.append({
        'outcome': outcome,
        'filters': filters,
        'network': a.get('network', '').lower()
    })

# Test different combinations
combo_tests = [
    ('score_95+ & vel_30+', lambda f: f['score_95+'] and f['vel_30+']),
    ('score_95+ & buy_1.2+', lambda f: f['score_95+'] and f['buy_1.2+']),
    ('score_95+ & vol_liq_2+', lambda f: f['score_95+'] and f['vol_liq_2+']),
    ('vel_30+ & buy_1.2+', lambda f: f['vel_30+'] and f['buy_1.2+']),
    ('vel_50+ & buy_1.5+', lambda f: f['vel_50+'] and f['buy_1.5+']),
    ('score_100 & vel_30+', lambda f: f['score_100'] and f['vel_30+']),
    ('score_95+ & vel_30+ & buy_1.2+', lambda f: f['score_95+'] and f['vel_30+'] and f['buy_1.2+']),
    ('score_95+ & vel_50+ & buy_1.5+', lambda f: f['score_95+'] and f['vel_50+'] and f['buy_1.5+']),
    ('ALL STRICT: score_100 & vel_50+ & buy_1.5+ & vol_liq_5+',
     lambda f: f['score_100'] and f['vel_50+'] and f['buy_1.5+'] and f['vol_liq_5+']),
]

print(f"{'Combination':<50} {'Count':>8} {'Win Rate':>10}")
for name, test_func in combo_tests:
    matching = [c for c in combinations if test_func(c['filters'])]
    if len(matching) >= 20:
        wins = sum(1 for c in matching if c['outcome'] == 'WIN')
        wr = wins / len(matching) * 100
        marker = " <<<" if wr >= 40 else ""
        print(f"{name:<50} {len(matching):>8,} {wr:>9.1f}%{marker}")

# =============================================================================
# 11. TYPE_PUMP ANALYSIS
# =============================================================================
print("\n[11] TYPE_PUMP DETAILED ANALYSIS")
print("-" * 50)

type_stats = defaultdict(lambda: {'wins': 0, 'total': 0})
for a in alerts:
    tp = a.get('type_pump', 'UNKNOWN')
    outcome = get_outcome(a)
    type_stats[tp]['total'] += 1
    if outcome == 'WIN':
        type_stats[tp]['wins'] += 1

print(f"{'Type Pump':<20} {'Count':>8} {'Win Rate':>10}")
for tp, stats in sorted(type_stats.items(), key=lambda x: x[1]['wins']/x[1]['total']*100 if x[1]['total'] > 0 else 0, reverse=True):
    if stats['total'] >= 50:
        wr = stats['wins'] / stats['total'] * 100
        marker = " <-- BEST" if wr >= 35 else (" <-- AVOID" if wr < 25 else "")
        print(f"{tp:<20} {stats['total']:>8,} {wr:>9.1f}%{marker}")

# =============================================================================
# 12. LIQUIDITY CHANGE PATTERN
# =============================================================================
print("\n[12] ENTRY CONDITIONS - PRICE MOMENTUM")
print("-" * 50)

# Analyze price_change_5m if available
price_5m_ranges = {
    'negative': (-100, 0),
    '0-2%': (0, 2),
    '2-5%': (2, 5),
    '5-10%': (5, 10),
    '10%+': (10, 1000),
}

def get_price_5m(a):
    return safe_float(a.get('price_change_5m'))

results = analyze_metric_ranges(alerts, 'Price 5m', get_price_5m, price_5m_ranges)
if results:
    print(f"{'Price Change 5m':<15} {'Count':>8} {'Win Rate':>10}")
    for name, data in sorted(results.items(), key=lambda x: x[1]['range'][0]):
        marker = " <-- SWEET SPOT" if data['win_rate'] == max(r['win_rate'] for r in results.values()) else ""
        print(f"{name:<15} {data['count']:>8,} {data['win_rate']:>9.1f}%{marker}")

# =============================================================================
# 13. SCORE + NETWORK SPECIFIC THRESHOLDS
# =============================================================================
print("\n[13] OPTIMAL SCORE THRESHOLD BY NETWORK")
print("-" * 50)

for network in networks:
    net_alerts = [a for a in alerts if a.get('network', '').lower() == network]
    print(f"\n{network.upper()}:")

    score_thresholds = [70, 75, 80, 85, 90, 95, 100]
    for thresh in score_thresholds:
        filtered = [a for a in net_alerts if safe_float(a.get('score')) >= thresh]
        if len(filtered) >= 30:
            wins = sum(1 for a in filtered if get_outcome(a) == 'WIN')
            wr = wins / len(filtered) * 100
            marker = " <-- RECOMMEND" if wr >= 35 else ""
            print(f"  Score >= {thresh}: {len(filtered):>6,} alerts, {wr:.1f}% WR{marker}")

# =============================================================================
# SUMMARY & RECOMMENDATIONS
# =============================================================================
print("\n" + "=" * 70)
print("OPTIMIZATION RECOMMENDATIONS")
print("=" * 70)

print("""
IMMEDIATE ACTIONS TO IMPLEMENT:

1. VOL/LIQ RATIO FILTER
   - Add minimum Vol/Liq ratio filter (appears 2.0+ is sweet spot)
   - High volume relative to liquidity = active trading = momentum

2. TRANSACTION COUNT FILTER
   - Optimal range seems to be 1000-5000 txns
   - Too few = no interest, too many = might be topped

3. PRICE MOMENTUM AT ENTRY
   - Sweet spot for price_change_1h: 10-50%
   - Avoid entries on tokens that already pumped 100%+

4. BUY RATIO REFINEMENT
   - Current: >= 1.0
   - Consider: >= 1.2 (significantly better WR in most cases)

5. HOUR OF DAY FILTER (optional)
   - Some hours consistently underperform
   - Could add time-based filtering

6. TYPE_PUMP STRICT FILTER
   - Only allow: RAPIDE, TRES_RAPIDE, PARABOLIQUE
   - Strictly reject: LENT, STAGNANT

7. MULTI-FACTOR SCORING
   - Combine filters for "GOLDEN" alerts
   - score_95+ AND vel_30+ AND buy_1.2+ = highest WR
""")

print("\nAnalysis complete!")
