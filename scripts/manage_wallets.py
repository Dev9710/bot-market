#!/usr/bin/env python3
"""
Smart Money Wallet Manager
==========================
CLI pour gérer les wallets smart money pour le copy trading.

Usage:
    python scripts/manage_wallets.py add <address> <network> [options]
    python scripts/manage_wallets.py list
    python scripts/manage_wallets.py remove <address>
    python scripts/manage_wallets.py analyze <address> <network>

Examples:
    python scripts/manage_wallets.py add 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU solana --name "SolWhale01" --tier PROVEN --wr 65
    python scripts/manage_wallets.py list
    python scripts/manage_wallets.py remove 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.copy_trading import (
    add_wallet,
    remove_wallet,
    list_wallets,
    print_wallet_list,
    update_wallet_stats,
    load_wallets
)


def cmd_add(args):
    """Ajouter un wallet"""
    success, message = add_wallet(
        address=args.address,
        network=args.network,
        name=args.name or "",
        tier=args.tier or "UNRANKED",
        win_rate=args.wr or 0.0,
        notes=args.notes or ""
    )

    if success:
        print(f"[OK] {message}")
    else:
        print(f"[ERROR] {message}")


def cmd_list(args):
    """Lister les wallets"""
    print_wallet_list()


def cmd_remove(args):
    """Supprimer un wallet"""
    success, message = remove_wallet(args.address)

    if success:
        print(f"[OK] {message}")
    else:
        print(f"[ERROR] {message}")


def cmd_analyze(args):
    """Analyser un wallet (placeholder - necessite API)"""
    print(f"\n[ANALYZE] Wallet: {args.address}")
    print(f"          Network: {args.network}")
    print("\n[WARNING] L'analyse automatique necessite une API key pour:")
    print("          - Solscan (Solana)")
    print("          - Etherscan (ETH/Base)")
    print("          - BscScan (BSC)")
    print("\n[INFO] Pour l'instant, analysez manuellement sur:")

    if args.network.lower() == 'solana':
        print(f"        https://solscan.io/account/{args.address}")
        print(f"        https://debank.com/profile/{args.address}")
    elif args.network.lower() in ['eth', 'base']:
        print(f"        https://etherscan.io/address/{args.address}")
        print(f"        https://debank.com/profile/{args.address}")
    elif args.network.lower() == 'bsc':
        print(f"        https://bscscan.com/address/{args.address}")
        print(f"        https://debank.com/profile/{args.address}")

    print("\n[CRITERIA] Pour un bon wallet:")
    print("           [+] Win rate > 60%")
    print("           [+] Au moins 20 trades historiques")
    print("           [+] Wallet actif depuis 30+ jours")
    print("           [+] Profit moyen > 10%")


def cmd_stats(args):
    """Show statistics"""
    wallets = load_wallets()

    if not wallets:
        print("[EMPTY] No wallets in watchlist")
        return

    # Stats by tier
    tier_counts = {}
    network_counts = {}
    total_wr = 0
    wr_count = 0

    for w in wallets.values():
        tier_counts[w.tier] = tier_counts.get(w.tier, 0) + 1
        network_counts[w.network] = network_counts.get(w.network, 0) + 1
        if w.win_rate > 0:
            total_wr += w.win_rate
            wr_count += 1

    print("\n" + "=" * 50)
    print("WATCHLIST STATISTICS")
    print("=" * 50)

    print(f"\nTotal wallets: {len(wallets)}")

    print("\nBy Tier:")
    for tier in ['LEGENDARY', 'ELITE', 'PROVEN', 'PROMISING', 'UNRANKED']:
        count = tier_counts.get(tier, 0)
        if count > 0:
            print(f"  {tier}: {count}")

    print("\nBy Network:")
    for network, count in sorted(network_counts.items()):
        print(f"  {network.upper()}: {count}")

    if wr_count > 0:
        print(f"\nAverage Win Rate: {total_wr / wr_count:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Money Wallet Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add 7xKXtg... solana --name "SolWhale01" --tier PROVEN --wr 65
  %(prog)s list
  %(prog)s remove 7xKXtg...
  %(prog)s analyze 7xKXtg... solana
  %(prog)s stats
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commande')

    # ADD command
    add_parser = subparsers.add_parser('add', help='Ajouter un wallet')
    add_parser.add_argument('address', help='Adresse du wallet')
    add_parser.add_argument('network', help='Network (solana, eth, base, bsc)')
    add_parser.add_argument('--name', '-n', help='Surnom du wallet')
    add_parser.add_argument('--tier', '-t',
                           choices=['LEGENDARY', 'ELITE', 'PROVEN', 'PROMISING', 'UNRANKED'],
                           default='UNRANKED',
                           help='Tier du wallet')
    add_parser.add_argument('--wr', type=float, help='Win rate estimé (0-100)')
    add_parser.add_argument('--notes', help='Notes sur le wallet')
    add_parser.set_defaults(func=cmd_add)

    # LIST command
    list_parser = subparsers.add_parser('list', help='Lister les wallets')
    list_parser.set_defaults(func=cmd_list)

    # REMOVE command
    remove_parser = subparsers.add_parser('remove', help='Supprimer un wallet')
    remove_parser.add_argument('address', help='Adresse du wallet à supprimer')
    remove_parser.set_defaults(func=cmd_remove)

    # ANALYZE command
    analyze_parser = subparsers.add_parser('analyze', help='Analyser un wallet')
    analyze_parser.add_argument('address', help='Adresse du wallet')
    analyze_parser.add_argument('network', help='Network (solana, eth, base, bsc)')
    analyze_parser.set_defaults(func=cmd_analyze)

    # STATS command
    stats_parser = subparsers.add_parser('stats', help='Afficher les statistiques')
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
