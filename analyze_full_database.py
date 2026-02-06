#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE COMPLETE DE LA DATABASE RAILWAY
========================================
"""

import json
import pandas as pd
import numpy as np
import sys

# Fix encoding Windows
sys.stdout.reconfigure(encoding='utf-8')

# Charger les donnees
print("="*70)
print("   ANALYSE COMPLETE - DATABASE RAILWAY")
print("="*70)
print()

with open('exports/railway_alerts_latest.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data['alerts'])

# Convertir les colonnes numeriques
numeric_cols = ['score', 'velocite_pump', 'age_hours', 'liquidity', 'volume_24h',
                'final_gain_percent', 'buy_ratio', 'time_to_tp1', 'time_to_tp2',
                'time_to_tp3', 'time_to_sl', 'sl_hit', 'is_closed']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Creer colonnes booleennes pour l'analyse
df['is_win'] = df['final_outcome'].str.startswith('WIN', na=False)
df['is_loss'] = df['final_outcome'] == 'LOSS_SL'
df['is_timeout'] = df['final_outcome'] == 'TIMEOUT'

# Convertir highest_tp_reached en numerique
tp_map = {'TP1': 1, 'TP2': 2, 'TP3': 3}
df['tp_level'] = df['highest_tp_reached'].map(tp_map).fillna(0).astype(int)

print(f"Total alertes chargees: {len(df):,}")
print(f"Date export: {data['export_date']}")
print()

# Stats globales
total_tracked = df[df['final_outcome'].notna()].shape[0]
total_wins = df['is_win'].sum()
total_losses = df['is_loss'].sum()
total_timeouts = df['is_timeout'].sum()

print(f"Alertes avec tracking: {total_tracked:,}")
print(f"  - Wins (TP1+):  {total_wins:,} ({total_wins/total_tracked*100:.1f}%)")
print(f"  - Losses (SL):  {total_losses:,} ({total_losses/total_tracked*100:.1f}%)")
print(f"  - Timeouts:     {total_timeouts:,} ({total_timeouts/total_tracked*100:.1f}%)")
print()

# ============================================
# 1. ANALYSE GLOBALE PAR BLOCKCHAIN
# ============================================
print("="*70)
print("   1. WIN RATE PAR BLOCKCHAIN")
print("="*70)
print()

df_tracked = df[df['final_outcome'].notna()].copy()

print(f"{'Network':<12} {'Total':>10} {'Wins':>10} {'Losses':>10} {'Timeout':>10} {'WinRate':>10} {'LossRate':>10}")
print("-"*80)

network_stats = {}
for net in sorted(df['network'].unique()):
    subset = df_tracked[df_tracked['network'] == net]
    wins = subset['is_win'].sum()
    losses = subset['is_loss'].sum()
    timeouts = subset['is_timeout'].sum()
    wr = wins / len(subset) * 100 if len(subset) > 0 else 0
    lr = losses / len(subset) * 100 if len(subset) > 0 else 0

    network_stats[net] = {'total': len(subset), 'wins': wins, 'losses': losses, 'win_rate': wr, 'loss_rate': lr}
    print(f"{net:<12} {len(subset):>10,} {wins:>10,} {losses:>10,} {timeouts:>10,} {wr:>9.1f}% {lr:>9.1f}%")

print()

# ============================================
# 2. ANALYSE TP LEVELS PAR BLOCKCHAIN
# ============================================
print("="*70)
print("   2. NIVEAU TP ATTEINT PAR BLOCKCHAIN")
print("="*70)
print()

print(f"{'Network':<12} {'TP1':>10} {'TP2':>10} {'TP3':>10} {'TP3/Total':>12}")
print("-"*60)

for net in sorted(df['network'].unique()):
    subset = df_tracked[df_tracked['network'] == net]
    if len(subset) == 0:
        continue

    tp1 = (subset['tp_level'] >= 1).sum()
    tp2 = (subset['tp_level'] >= 2).sum()
    tp3 = (subset['tp_level'] >= 3).sum()

    tp1_pct = tp1 / len(subset) * 100
    tp2_pct = tp2 / len(subset) * 100
    tp3_pct = tp3 / len(subset) * 100

    print(f"{net:<12} {tp1_pct:>9.1f}% {tp2_pct:>9.1f}% {tp3_pct:>9.1f}% {tp3:>6,}/{len(subset):,}")

print()

# ============================================
# 3. WIN RATE PAR SCORE
# ============================================
print("="*70)
print("   3. WIN RATE PAR SCORE")
print("="*70)
print()

score_ranges = [(50, 70), (70, 80), (80, 85), (85, 90), (90, 95), (95, 100), (100, 101)]

print(f"{'Score':<12} {'Count':>10} {'Wins':>10} {'WinRate':>10} {'TP3 Rate':>10} {'Avg Gain':>12}")
print("-"*70)

for low, high in score_ranges:
    subset = df_tracked[(df_tracked['score'] >= low) & (df_tracked['score'] < high)]
    if len(subset) < 10:
        continue

    wins = subset['is_win'].sum()
    tp3 = (subset['tp_level'] >= 3).sum()
    wr = wins / len(subset) * 100
    tp3_rate = tp3 / len(subset) * 100
    avg_gain = subset['final_gain_percent'].mean()

    label = f"{low}-{high-1}" if high <= 100 else "100"
    print(f"{label:<12} {len(subset):>10,} {wins:>10,} {wr:>9.1f}% {tp3_rate:>9.1f}% {avg_gain:>11.1f}%")

print()

# ============================================
# 4. WIN RATE PAR VELOCITE
# ============================================
print("="*70)
print("   4. WIN RATE PAR VELOCITE PUMP")
print("="*70)
print()

vel_ranges = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 100), (100, 500)]

print(f"{'Velocite':<12} {'Count':>10} {'WinRate':>10} {'LossRate':>10} {'TP3 Rate':>10} {'Avg Gain':>12}")
print("-"*75)

for low, high in vel_ranges:
    subset = df_tracked[(df_tracked['velocite_pump'] >= low) & (df_tracked['velocite_pump'] < high)]
    if len(subset) < 50:
        continue

    wins = subset['is_win'].sum()
    losses = subset['is_loss'].sum()
    tp3 = (subset['tp_level'] >= 3).sum()
    wr = wins / len(subset) * 100
    lr = losses / len(subset) * 100
    tp3_rate = tp3 / len(subset) * 100
    avg_gain = subset['final_gain_percent'].mean()

    label = f"{low}-{high}"
    print(f"{label:<12} {len(subset):>10,} {wr:>9.1f}% {lr:>9.1f}% {tp3_rate:>9.1f}% {avg_gain:>11.1f}%")

print()

# ============================================
# 5. WIN RATE PAR TYPE PUMP
# ============================================
print("="*70)
print("   5. WIN RATE PAR TYPE PUMP")
print("="*70)
print()

print(f"{'Type Pump':<15} {'Count':>10} {'WinRate':>10} {'LossRate':>10} {'TP3 Rate':>10} {'Avg Gain':>12}")
print("-"*75)

for tp in df_tracked['type_pump'].value_counts().index:
    subset = df_tracked[df_tracked['type_pump'] == tp]
    if len(subset) < 50:
        continue

    wins = subset['is_win'].sum()
    losses = subset['is_loss'].sum()
    tp3 = (subset['tp_level'] >= 3).sum()
    wr = wins / len(subset) * 100
    lr = losses / len(subset) * 100
    tp3_rate = tp3 / len(subset) * 100
    avg_gain = subset['final_gain_percent'].mean()

    print(f"{str(tp):<15} {len(subset):>10,} {wr:>9.1f}% {lr:>9.1f}% {tp3_rate:>9.1f}% {avg_gain:>11.1f}%")

print()

# ============================================
# 6. WIN RATE PAR AGE TOKEN
# ============================================
print("="*70)
print("   6. WIN RATE PAR AGE DU TOKEN")
print("="*70)
print()

age_ranges = [(0, 3), (3, 12), (12, 24), (24, 48), (48, 72), (72, 168), (168, 500)]

print(f"{'Age (h)':<12} {'Count':>10} {'WinRate':>10} {'LossRate':>10} {'TP3 Rate':>10}")
print("-"*60)

for low, high in age_ranges:
    subset = df_tracked[(df_tracked['age_hours'] >= low) & (df_tracked['age_hours'] < high)]
    if len(subset) < 50:
        continue

    wins = subset['is_win'].sum()
    losses = subset['is_loss'].sum()
    tp3 = (subset['tp_level'] >= 3).sum()
    wr = wins / len(subset) * 100
    lr = losses / len(subset) * 100
    tp3_rate = tp3 / len(subset) * 100

    label = f"{low}-{high}h"
    print(f"{label:<12} {len(subset):>10,} {wr:>9.1f}% {lr:>9.1f}% {tp3_rate:>9.1f}%")

print()

# ============================================
# 7. ANALYSE DETAILLEE SOLANA
# ============================================
print("="*70)
print("   7. ANALYSE DETAILLEE SOLANA")
print("="*70)
print()

sol = df_tracked[df_tracked['network'] == 'solana']
sol_wins = sol[sol['is_win']]
sol_losses = sol[sol['is_loss']]

print(f"SOLANA - Statistiques globales:")
print(f"  Total:     {len(sol):,}")
print(f"  Wins:      {len(sol_wins):,} ({len(sol_wins)/len(sol)*100:.1f}%)")
print(f"  Losses:    {len(sol_losses):,} ({len(sol_losses)/len(sol)*100:.1f}%)")
print(f"  Gain moyen: {sol['final_gain_percent'].mean():.1f}%")
print()

print("SOLANA - Win Rate par Score:")
print("-"*40)
for low, high in [(80, 90), (90, 95), (95, 100), (100, 101)]:
    subset = sol[(sol['score'] >= low) & (sol['score'] < high)]
    if len(subset) < 20:
        continue
    wr = subset['is_win'].sum() / len(subset) * 100
    label = f"Score {low}-{high-1}" if high <= 100 else "Score 100"
    print(f"  {label}: {len(subset):>6,} alertes, WR: {wr:.1f}%")

print()

print("SOLANA - Win Rate par Velocite:")
print("-"*40)
for low, high in [(0, 10), (10, 20), (20, 40), (40, 70), (70, 150)]:
    subset = sol[(sol['velocite_pump'] >= low) & (sol['velocite_pump'] < high)]
    if len(subset) < 20:
        continue
    wr = subset['is_win'].sum() / len(subset) * 100
    avg_gain = subset['final_gain_percent'].mean()
    print(f"  Vel {low}-{high}: {len(subset):>6,} alertes, WR: {wr:.1f}%, Gain: {avg_gain:.1f}%")

print()

print("SOLANA - Win Rate par Liquidite:")
print("-"*40)
for low, high in [(0, 100000), (100000, 200000), (200000, 400000), (400000, 1000000)]:
    subset = sol[(sol['liquidity'] >= low) & (sol['liquidity'] < high)]
    if len(subset) < 20:
        continue
    wr = subset['is_win'].sum() / len(subset) * 100
    print(f"  ${low/1000:.0f}K-${high/1000:.0f}K: {len(subset):>6,} alertes, WR: {wr:.1f}%")

print()

print("SOLANA - Caracteristiques WINNERS vs LOSERS:")
print("-"*50)
print(f"{'Metrique':<20} {'Winners':>15} {'Losers':>15}")
print("-"*50)
for col, label in [('score', 'Score'), ('velocite_pump', 'Velocite'), ('age_hours', 'Age (h)'),
                    ('liquidity', 'Liquidite'), ('buy_ratio', 'Buy Ratio')]:
    w_val = sol_wins[col].mean()
    l_val = sol_losses[col].mean()
    if col == 'liquidity':
        print(f"{label:<20} ${w_val:>13,.0f} ${l_val:>13,.0f}")
    else:
        print(f"{label:<20} {w_val:>15.1f} {l_val:>15.1f}")

print()

# ============================================
# 8. ANALYSE DETAILLEE ETH
# ============================================
print("="*70)
print("   8. ANALYSE DETAILLEE ETH")
print("="*70)
print()

eth = df_tracked[df_tracked['network'] == 'eth']
eth_wins = eth[eth['is_win']]
eth_losses = eth[eth['is_loss']]

print(f"ETH - Statistiques globales:")
print(f"  Total:     {len(eth):,}")
print(f"  Wins:      {len(eth_wins):,} ({len(eth_wins)/len(eth)*100:.1f}%)")
print(f"  Losses:    {len(eth_losses):,} ({len(eth_losses)/len(eth)*100:.1f}%)")
print(f"  Gain moyen: {eth['final_gain_percent'].mean():.1f}%")
print()

print("ETH - Win Rate par Score:")
print("-"*40)
for low, high in [(80, 90), (90, 95), (95, 100), (100, 101)]:
    subset = eth[(eth['score'] >= low) & (eth['score'] < high)]
    if len(subset) < 10:
        continue
    wr = subset['is_win'].sum() / len(subset) * 100
    label = f"Score {low}-{high-1}" if high <= 100 else "Score 100"
    print(f"  {label}: {len(subset):>6,} alertes, WR: {wr:.1f}%")

print()

print("ETH - Win Rate par Liquidite:")
print("-"*40)
for low, high in [(0, 75000), (75000, 150000), (150000, 300000), (300000, 1000000)]:
    subset = eth[(eth['liquidity'] >= low) & (eth['liquidity'] < high)]
    if len(subset) < 10:
        continue
    wr = subset['is_win'].sum() / len(subset) * 100
    print(f"  ${low/1000:.0f}K-${high/1000:.0f}K: {len(subset):>6,} alertes, WR: {wr:.1f}%")

print()

print("ETH - Caracteristiques WINNERS vs LOSERS:")
print("-"*50)
print(f"{'Metrique':<20} {'Winners':>15} {'Losers':>15}")
print("-"*50)
for col, label in [('score', 'Score'), ('velocite_pump', 'Velocite'), ('age_hours', 'Age (h)'),
                    ('liquidity', 'Liquidite'), ('buy_ratio', 'Buy Ratio')]:
    w_val = eth_wins[col].mean()
    l_val = eth_losses[col].mean()
    if col == 'liquidity':
        print(f"{label:<20} ${w_val:>13,.0f} ${l_val:>13,.0f}")
    else:
        print(f"{label:<20} {w_val:>15.1f} {l_val:>15.1f}")

print()

# ============================================
# 9. PATTERNS GAGNANTS GLOBAUX (TP3)
# ============================================
print("="*70)
print("   9. PATTERNS GAGNANTS (TP3 atteint)")
print("="*70)
print()

tp3_winners = df_tracked[df_tracked['tp_level'] >= 3]
all_losses = df_tracked[df_tracked['is_loss']]

print(f"TP3 Winners: {len(tp3_winners):,} | Losers: {len(all_losses):,}")
print()

print("Comparaison TP3 Winners vs Losers:")
print("-"*60)
print(f"{'Metrique':<25} {'TP3 Winners':>15} {'Losers':>15} {'Delta':>12}")
print("-"*60)

for col, label in [('score', 'Score moyen'), ('velocite_pump', 'Velocite moyenne'),
                    ('age_hours', 'Age moyen (h)'), ('liquidity', 'Liquidite moy.'),
                    ('volume_24h', 'Volume 24h moy.'), ('buy_ratio', 'Buy ratio moy.')]:
    w_val = tp3_winners[col].mean()
    l_val = all_losses[col].mean()
    delta = ((w_val - l_val) / l_val * 100) if l_val != 0 else 0

    if col in ['liquidity', 'volume_24h']:
        print(f"{label:<25} ${w_val:>13,.0f} ${l_val:>13,.0f} {delta:>+10.1f}%")
    else:
        print(f"{label:<25} {w_val:>15.1f} {l_val:>15.1f} {delta:>+10.1f}%")

print()

# ============================================
# 10. TEMPS VERS TP/SL
# ============================================
print("="*70)
print("   10. TEMPS MOYEN VERS TP/SL (heures)")
print("="*70)
print()

print(f"{'Network':<12} {'To TP1':>10} {'To TP2':>10} {'To TP3':>10} {'To SL':>10}")
print("-"*55)

for net in sorted(df['network'].unique()):
    subset = df_tracked[df_tracked['network'] == net]

    def get_time(col):
        vals = subset[subset[col].notna()][col]
        if len(vals) == 0:
            return "N/A"
        mean = vals.mean()
        # Si > 100, probablement en minutes
        if mean > 100:
            return f"{mean/60:.1f}h"
        return f"{mean:.1f}h"

    print(f"{net:<12} {get_time('time_to_tp1'):>10} {get_time('time_to_tp2'):>10} {get_time('time_to_tp3'):>10} {get_time('time_to_sl'):>10}")

print()

# ============================================
# 11. FAIBLESSES ET AXES D'AMELIORATION
# ============================================
print("="*70)
print("   11. FAIBLESSES ET AXES D'AMELIORATION")
print("="*70)
print()

print("FAIBLESSES IDENTIFIEES - SOLANA:")
print("-"*50)
print(f"  1. Win Rate global: {network_stats['solana']['win_rate']:.1f}% (objectif: 30%+)")
print(f"  2. Loss Rate: {network_stats['solana']['loss_rate']:.1f}% (trop eleve)")

# Zones problematiques Solana
sol_low_vel = sol[sol['velocite_pump'] < 10]
if len(sol_low_vel) > 0:
    wr = sol_low_vel['is_win'].sum() / len(sol_low_vel) * 100
    print(f"  3. Velocite < 10: WR {wr:.1f}% ({len(sol_low_vel):,} alertes) --> FILTRER")

sol_danger = sol[(sol['age_hours'] >= 12) & (sol['age_hours'] <= 24)]
if len(sol_danger) > 0:
    wr = sol_danger['is_win'].sum() / len(sol_danger) * 100
    print(f"  4. Age 12-24h: WR {wr:.1f}% ({len(sol_danger):,} alertes) --> ZONE DANGER")

print()

print("FAIBLESSES IDENTIFIEES - ETH:")
print("-"*50)
print(f"  1. Win Rate global: {network_stats['eth']['win_rate']:.1f}%")
print(f"  2. Loss Rate: {network_stats['eth']['loss_rate']:.1f}%")

eth_low_liq = eth[eth['liquidity'] < 75000]
if len(eth_low_liq) > 0:
    wr = eth_low_liq['is_win'].sum() / len(eth_low_liq) * 100
    print(f"  3. Liquidite < $75K: WR {wr:.1f}% ({len(eth_low_liq):,} alertes)")

print()

print("RECOMMANDATIONS GLOBALES:")
print("-"*50)

# Trouver meilleur seuil de score
print("  1. SCORE MINIMUM OPTIMAL:")
for threshold in [85, 90, 95, 97, 99]:
    subset = df_tracked[df_tracked['score'] >= threshold]
    if len(subset) > 100:
        wr = subset['is_win'].sum() / len(subset) * 100
        print(f"     Score >= {threshold}: WR {wr:.1f}% ({len(subset):,} alertes)")

print()

print("  2. VELOCITE MINIMUM PAR NETWORK:")
for net in ['solana', 'eth', 'bsc', 'base']:
    net_data = df_tracked[df_tracked['network'] == net]
    best_wr = 0
    best_vel = 0
    for vel in [5, 10, 15, 20, 25, 30]:
        subset = net_data[net_data['velocite_pump'] >= vel]
        if len(subset) > 50:
            wr = subset['is_win'].sum() / len(subset) * 100
            if wr > best_wr:
                best_wr = wr
                best_vel = vel
    print(f"     {net.upper()}: velocite >= {best_vel} (WR: {best_wr:.1f}%)")

print()

print("  3. LIQUIDITE OPTIMALE:")
print("     SOLANA: $100K-$300K semble optimal")
print("     ETH: $75K-$200K semble optimal")

print()

print("  4. FILTRES RECOMMANDES:")
print("     - Score minimum: 90+")
print("     - Velocite minimum: 15+ (Solana), 10+ (ETH)")
print("     - Eviter age 12-24h")
print("     - Type pump: favoriser RAPIDE, TRES_RAPIDE")

print()
print("="*70)
print("   FIN DE L'ANALYSE")
print("="*70)
