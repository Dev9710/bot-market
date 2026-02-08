"""
Smart Money Tracker V1.0
========================
Module pour tracker les "smart money" wallets et détecter les whale buys.

Basé sur la méthodologie du document Modop_bot_crypto:
1. Identifier les wallets qui achètent tôt les tokens gagnants
2. Tracker leur historique de performance
3. Utiliser leur activité comme signal supplémentaire

Intégration avec GeckoTerminal API pour les données de transactions.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configuration paths
SMART_MONEY_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'smart_money')
WATCHLIST_FILE = os.path.join(SMART_MONEY_DATA_DIR, 'wallet_watchlist.json')
WHALE_ALERTS_FILE = os.path.join(SMART_MONEY_DATA_DIR, 'whale_alerts.json')


class WalletTier(Enum):
    """Classification des wallets par performance"""
    LEGENDARY = "LEGENDARY"  # Win rate > 80%, 50+ trades
    ELITE = "ELITE"          # Win rate > 70%, 30+ trades
    PROVEN = "PROVEN"        # Win rate > 60%, 20+ trades
    PROMISING = "PROMISING"  # Win rate > 50%, 10+ trades
    UNRANKED = "UNRANKED"    # Pas assez de données


@dataclass
class SmartWallet:
    """Représentation d'un wallet smart money"""
    address: str
    network: str
    tier: str = WalletTier.UNRANKED.value
    total_trades: int = 0
    winning_trades: int = 0
    win_rate: float = 0.0
    avg_profit_percent: float = 0.0
    total_volume_usd: float = 0.0
    first_seen: str = ""
    last_active: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SmartWallet':
        return cls(**data)


@dataclass
class WhaleBuy:
    """Représentation d'un achat whale détecté"""
    wallet_address: str
    token_address: str
    token_symbol: str
    network: str
    buy_amount_usd: float
    buy_amount_native: float
    timestamp: str
    is_smart_money: bool = False
    wallet_tier: str = WalletTier.UNRANKED.value

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# CONFIGURATION SMART MONEY
# =============================================================================

SMART_MONEY_CONFIG = {
    # Critères pour identifier un "smart money" wallet
    'min_wallet_age_days': 30,           # Wallet doit exister depuis 30j+
    'min_historical_trades': 10,          # Au moins 10 trades historiques
    'min_win_rate': 55,                   # Au moins 55% de trades gagnants
    'min_avg_profit': 10,                 # Au moins +10% de profit moyen

    # Seuils pour les whale buys par network (en USD)
    'whale_buy_thresholds': {
        'solana': 5000,      # $5K+ = whale sur Solana
        'eth': 10000,        # $10K+ = whale sur ETH
        'base': 5000,        # $5K+ = whale sur Base
        'bsc': 3000,         # $3K+ = whale sur BSC
        'polygon_pos': 2000, # $2K+ = whale sur Polygon
        'avax': 3000,        # $3K+ = whale sur Avalanche
    },

    # Bonus de score selon le tier du wallet
    'tier_score_bonus': {
        WalletTier.LEGENDARY.value: 25,
        WalletTier.ELITE.value: 20,
        WalletTier.PROVEN.value: 15,
        WalletTier.PROMISING.value: 10,
        WalletTier.UNRANKED.value: 5,
    },

    # Time window pour considérer un achat comme "récent"
    'recent_buy_window_minutes': 60,
}


# =============================================================================
# STRATÉGIE DE VENTE PARTIELLE
# =============================================================================

PARTIAL_PROFIT_CONFIG = {
    # Pourcentage à vendre à chaque TP
    'TP1_sell_percent': 50,   # Vendre 50% au TP1 (sécuriser profits)
    'TP2_sell_percent': 30,   # Vendre 30% au TP2 (reste 20%)
    'TP3_sell_percent': 100,  # Vendre tout au TP3 (ou trailing)

    # Alternative: Mode "Let it ride"
    'let_it_ride_enabled': False,
    'let_it_ride_after_tp': 2,  # Après TP2, laisser courir avec trailing
    'trailing_stop_percent': 15,  # Trailing stop à -15% du high
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def ensure_data_dir():
    """Crée le répertoire de données si nécessaire"""
    os.makedirs(SMART_MONEY_DATA_DIR, exist_ok=True)


def load_wallet_watchlist() -> Dict[str, SmartWallet]:
    """Charge la watchlist des smart money wallets"""
    ensure_data_dir()
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {addr: SmartWallet.from_dict(w) for addr, w in data.items()}
        except Exception as e:
            print(f"[WARN] Error loading watchlist: {e}")
    return {}


def save_wallet_watchlist(watchlist: Dict[str, SmartWallet]):
    """Sauvegarde la watchlist des smart money wallets"""
    ensure_data_dir()
    data = {addr: w.to_dict() for addr, w in watchlist.items()}
    with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def add_wallet_to_watchlist(wallet: SmartWallet) -> bool:
    """Ajoute un wallet à la watchlist"""
    watchlist = load_wallet_watchlist()
    watchlist[wallet.address.lower()] = wallet
    save_wallet_watchlist(watchlist)
    return True


def get_wallet_tier(win_rate: float, total_trades: int) -> WalletTier:
    """Détermine le tier d'un wallet basé sur sa performance"""
    if total_trades >= 50 and win_rate >= 80:
        return WalletTier.LEGENDARY
    elif total_trades >= 30 and win_rate >= 70:
        return WalletTier.ELITE
    elif total_trades >= 20 and win_rate >= 60:
        return WalletTier.PROVEN
    elif total_trades >= 10 and win_rate >= 50:
        return WalletTier.PROMISING
    return WalletTier.UNRANKED


# =============================================================================
# DÉTECTION WHALE BUY
# =============================================================================

def is_whale_buy(network: str, buy_amount_usd: float) -> bool:
    """
    Vérifie si un achat est considéré comme un "whale buy" pour ce network.

    Args:
        network: Network identifier (solana, eth, etc.)
        buy_amount_usd: Montant de l'achat en USD

    Returns:
        bool: True si c'est un whale buy
    """
    threshold = SMART_MONEY_CONFIG['whale_buy_thresholds'].get(
        network.lower(),
        5000  # Default $5K
    )
    return buy_amount_usd >= threshold


def check_smart_money_activity(
    token_address: str,
    network: str,
    recent_buys: List[dict]
) -> Tuple[bool, List[dict]]:
    """
    Vérifie si des smart money wallets ont acheté ce token récemment.

    Args:
        token_address: Adresse du token
        network: Network identifier
        recent_buys: Liste des achats récents (from API)

    Returns:
        Tuple: (has_smart_money_activity, list of smart money buys)
    """
    watchlist = load_wallet_watchlist()
    smart_money_buys = []

    for buy in recent_buys:
        wallet_addr = buy.get('wallet_address', '').lower()
        if wallet_addr in watchlist:
            smart_wallet = watchlist[wallet_addr]
            smart_money_buys.append({
                'wallet': smart_wallet.to_dict(),
                'buy': buy,
                'tier': smart_wallet.tier,
            })

    return len(smart_money_buys) > 0, smart_money_buys


def calculate_whale_signal_bonus(
    network: str,
    whale_buys: List[dict],
    smart_money_buys: List[dict]
) -> dict:
    """
    Calcule le bonus de score basé sur l'activité whale/smart money.

    Returns:
        dict: {
            'bonus_score': int (0-30),
            'whale_count': int,
            'smart_money_count': int,
            'total_whale_volume_usd': float,
            'highest_tier': str,
            'signal_strength': str ('STRONG', 'MODERATE', 'WEAK', 'NONE')
        }
    """
    result = {
        'bonus_score': 0,
        'whale_count': len(whale_buys),
        'smart_money_count': len(smart_money_buys),
        'total_whale_volume_usd': sum(b.get('amount_usd', 0) for b in whale_buys),
        'highest_tier': WalletTier.UNRANKED.value,
        'signal_strength': 'NONE'
    }

    # Bonus pour whale buys
    if whale_buys:
        result['bonus_score'] += min(len(whale_buys) * 3, 10)  # Max +10 pour whales

    # Bonus pour smart money
    if smart_money_buys:
        tiers = [b['tier'] for b in smart_money_buys]

        # Trouver le meilleur tier
        tier_priority = [
            WalletTier.LEGENDARY.value,
            WalletTier.ELITE.value,
            WalletTier.PROVEN.value,
            WalletTier.PROMISING.value,
        ]
        for tier in tier_priority:
            if tier in tiers:
                result['highest_tier'] = tier
                result['bonus_score'] += SMART_MONEY_CONFIG['tier_score_bonus'][tier]
                break

    # Déterminer la force du signal
    if result['bonus_score'] >= 25:
        result['signal_strength'] = 'STRONG'
    elif result['bonus_score'] >= 15:
        result['signal_strength'] = 'MODERATE'
    elif result['bonus_score'] >= 5:
        result['signal_strength'] = 'WEAK'

    return result


# =============================================================================
# CALCUL PROFIT AVEC VENTE PARTIELLE
# =============================================================================

def calculate_partial_profit(
    entry_price: float,
    tp1_price: float,
    tp2_price: float,
    tp3_price: float,
    exit_at: str,  # 'TP1', 'TP2', 'TP3', 'SL'
    sl_price: float = None
) -> dict:
    """
    Calcule le profit réel avec la stratégie de vente partielle.

    Stratégie:
    - TP1: Vend 50%, garde 50%
    - TP2: Vend 30% du restant (=15% total), garde 20%
    - TP3: Vend tout le reste (20%)

    Args:
        entry_price: Prix d'entrée
        tp1_price: Prix TP1
        tp2_price: Prix TP2
        tp3_price: Prix TP3
        exit_at: Point de sortie ('TP1', 'TP2', 'TP3', 'SL')
        sl_price: Prix stop loss (si exit_at == 'SL')

    Returns:
        dict avec profit breakdown
    """
    config = PARTIAL_PROFIT_CONFIG

    # Calculer les % de gain pour chaque TP
    tp1_gain = (tp1_price - entry_price) / entry_price * 100
    tp2_gain = (tp2_price - entry_price) / entry_price * 100
    tp3_gain = (tp3_price - entry_price) / entry_price * 100

    result = {
        'exit_at': exit_at,
        'entry_price': entry_price,
        'partial_profits': [],
        'total_profit_percent': 0,
        'comparison_full_exit': 0,  # Si on avait tout vendu au point de sortie
    }

    if exit_at == 'TP1':
        # Vend 50% au TP1, reste 50% à entry (ou trailing)
        profit_tp1 = tp1_gain * 0.5  # 50% du portfolio à TP1 gain
        # Le reste sort à entry (worst case) ou continue
        result['partial_profits'] = [
            {'at': 'TP1', 'percent_sold': 50, 'gain': tp1_gain}
        ]
        result['total_profit_percent'] = profit_tp1
        result['comparison_full_exit'] = tp1_gain

    elif exit_at == 'TP2':
        # TP1: Vend 50%
        # TP2: Vend 30% du restant = 15% du total
        profit_tp1 = tp1_gain * 0.5
        profit_tp2 = tp2_gain * 0.15  # 30% of remaining 50% = 15%
        result['partial_profits'] = [
            {'at': 'TP1', 'percent_sold': 50, 'gain': tp1_gain},
            {'at': 'TP2', 'percent_sold': 15, 'gain': tp2_gain}
        ]
        result['total_profit_percent'] = profit_tp1 + profit_tp2
        result['comparison_full_exit'] = tp2_gain

    elif exit_at == 'TP3':
        # TP1: Vend 50%
        # TP2: Vend 15%
        # TP3: Vend 35% restant
        profit_tp1 = tp1_gain * 0.5
        profit_tp2 = tp2_gain * 0.15
        profit_tp3 = tp3_gain * 0.35
        result['partial_profits'] = [
            {'at': 'TP1', 'percent_sold': 50, 'gain': tp1_gain},
            {'at': 'TP2', 'percent_sold': 15, 'gain': tp2_gain},
            {'at': 'TP3', 'percent_sold': 35, 'gain': tp3_gain}
        ]
        result['total_profit_percent'] = profit_tp1 + profit_tp2 + profit_tp3
        result['comparison_full_exit'] = tp3_gain

    elif exit_at == 'SL' and sl_price:
        sl_loss = (sl_price - entry_price) / entry_price * 100
        result['partial_profits'] = [
            {'at': 'SL', 'percent_sold': 100, 'gain': sl_loss}
        ]
        result['total_profit_percent'] = sl_loss
        result['comparison_full_exit'] = sl_loss

    return result


# =============================================================================
# FONCTION D'INTÉGRATION PRINCIPALE
# =============================================================================

def enhance_alert_with_smart_money(
    alert_data: dict,
    recent_transactions: List[dict] = None
) -> dict:
    """
    Enrichit une alerte avec les données smart money.

    Args:
        alert_data: Données de l'alerte existante
        recent_transactions: Transactions récentes du token (optionnel)

    Returns:
        dict: alert_data enrichi avec:
            - smart_money_signal: dict avec info whale/smart money
            - quality_score_bonus: bonus à ajouter au score qualité
            - recommended_action: 'STRONG_BUY', 'BUY', 'HOLD', 'SKIP'
    """
    network = alert_data.get('network', '').lower()
    token_address = alert_data.get('pool_address', '')

    result = {
        **alert_data,
        'smart_money_signal': {
            'whale_detected': False,
            'smart_money_detected': False,
            'signal_strength': 'NONE',
            'bonus_score': 0,
        },
        'quality_score_bonus': 0,
        'recommended_action': 'HOLD'
    }

    if not recent_transactions:
        return result

    # Filtrer les whale buys
    whale_buys = []
    for tx in recent_transactions:
        if tx.get('type') == 'buy':
            amount_usd = tx.get('amount_usd', 0)
            if is_whale_buy(network, amount_usd):
                whale_buys.append(tx)

    # Vérifier smart money
    has_smart_money, smart_money_buys = check_smart_money_activity(
        token_address, network, recent_transactions
    )

    # Calculer le bonus
    signal = calculate_whale_signal_bonus(network, whale_buys, smart_money_buys)

    result['smart_money_signal'] = {
        'whale_detected': len(whale_buys) > 0,
        'smart_money_detected': has_smart_money,
        'whale_count': signal['whale_count'],
        'smart_money_count': signal['smart_money_count'],
        'total_whale_volume_usd': signal['total_whale_volume_usd'],
        'highest_tier': signal['highest_tier'],
        'signal_strength': signal['signal_strength'],
        'bonus_score': signal['bonus_score'],
    }

    result['quality_score_bonus'] = signal['bonus_score']

    # Déterminer l'action recommandée
    base_score = alert_data.get('quality_score', 50)
    final_score = base_score + signal['bonus_score']

    if signal['signal_strength'] == 'STRONG' and final_score >= 80:
        result['recommended_action'] = 'STRONG_BUY'
    elif signal['signal_strength'] in ['STRONG', 'MODERATE'] and final_score >= 70:
        result['recommended_action'] = 'BUY'
    elif final_score >= 60:
        result['recommended_action'] = 'HOLD'
    else:
        result['recommended_action'] = 'SKIP'

    return result


# =============================================================================
# EXEMPLES DE WALLETS SMART MONEY (À COMPLÉTER)
# =============================================================================

# Wallets connus pour leurs performances (exemple - à valider)
EXAMPLE_SMART_WALLETS = [
    # Format: (address, network, notes)
    # Ces wallets doivent être validés via analyse DexScreener
]


def initialize_example_watchlist():
    """Initialise la watchlist avec des exemples (pour démonstration)"""
    watchlist = load_wallet_watchlist()

    # Ajouter des wallets exemple si la watchlist est vide
    if not watchlist:
        print("[INFO] Watchlist vide. Utilisez add_wallet_to_watchlist() pour ajouter des wallets.")
        print("[INFO] Méthodologie: DexScreener > Top Gainers > Voir qui a acheté tôt > Analyser sur Debank")

    return watchlist


if __name__ == "__main__":
    # Test du module
    print("=" * 60)
    print("SMART MONEY TRACKER V1.0 - TEST")
    print("=" * 60)

    # Test whale detection
    print("\n[TEST] Whale Detection:")
    test_cases = [
        ('solana', 3000, False),
        ('solana', 6000, True),
        ('eth', 8000, False),
        ('eth', 15000, True),
    ]
    for network, amount, expected in test_cases:
        result = is_whale_buy(network, amount)
        status = "OK" if result == expected else "FAIL"
        print(f"  {status}: {network} ${amount:,} -> {'WHALE' if result else 'normal'}")

    # Test partial profit
    print("\n[TEST] Partial Profit Calculation:")
    profit = calculate_partial_profit(
        entry_price=1.0,
        tp1_price=1.10,  # +10%
        tp2_price=1.25,  # +25%
        tp3_price=1.50,  # +50%
        exit_at='TP3'
    )
    print(f"  Exit at TP3:")
    print(f"    Total profit: {profit['total_profit_percent']:.1f}%")
    print(f"    Full exit would be: {profit['comparison_full_exit']:.1f}%")
    print(f"    Breakdown: {profit['partial_profits']}")

    # Test tier classification
    print("\n[TEST] Wallet Tier Classification:")
    tier_tests = [
        (85, 60, WalletTier.LEGENDARY),
        (72, 35, WalletTier.ELITE),
        (65, 25, WalletTier.PROVEN),
        (55, 15, WalletTier.PROMISING),
        (40, 5, WalletTier.UNRANKED),
    ]
    for wr, trades, expected in tier_tests:
        result = get_wallet_tier(wr, trades)
        status = "OK" if result == expected else "FAIL"
        print(f"  {status}: WR={wr}% trades={trades} -> {result.value}")

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)
