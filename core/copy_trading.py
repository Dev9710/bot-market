"""
Copy Trading System V1.0
=========================
Système de copy trading basé sur les smart money wallets.

Fonctionnalités:
1. Ajouter/gérer des wallets à copier
2. Monitorer leurs transactions en temps réel
3. Générer des signaux BUY/SELL quand ils tradent
4. Intégrer avec le scanner existant

Sources de données:
- DexScreener API (transactions récentes)
- Solscan/Etherscan (historique wallet)
- GeckoTerminal (données pool)
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Lazy import for requests (only needed for API calls)
requests = None

def _get_requests():
    """Lazy import requests module"""
    global requests
    if requests is None:
        try:
            import requests as req
            requests = req
        except ImportError:
            raise ImportError("Module 'requests' required for API calls. Install with: pip install requests")
    return requests

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'copy_trading')
WALLETS_FILE = os.path.join(DATA_DIR, 'smart_wallets.json')
TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'wallet_transactions.json')
SIGNALS_FILE = os.path.join(DATA_DIR, 'copy_signals.json')

# API endpoints
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
SOLSCAN_API = "https://public-api.solscan.io"

# Thresholds
MIN_BUY_USD = 1000  # Minimum $1K pour générer un signal
COPY_DELAY_SECONDS = 30  # Délai max pour copier (freshness)


@dataclass
class SmartWallet:
    """Wallet smart money à copier"""
    address: str
    network: str
    name: str = ""  # Surnom optionnel
    tier: str = "UNRANKED"
    win_rate: float = 0.0
    total_trades: int = 0
    avg_profit: float = 0.0
    added_date: str = ""
    last_activity: str = ""
    is_active: bool = True
    notes: str = ""
    # Stats de copy trading
    signals_generated: int = 0
    signals_profitable: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SmartWallet':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CopySignal:
    """Signal de copy trading"""
    signal_id: str
    wallet_address: str
    wallet_name: str
    action: str  # 'BUY' or 'SELL'
    token_address: str
    token_symbol: str
    network: str
    amount_usd: float
    amount_native: float
    price_at_signal: float
    timestamp: str
    tx_hash: str = ""
    is_executed: bool = False
    execution_price: float = 0.0
    profit_loss: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# GESTION DES WALLETS
# =============================================================================

def ensure_data_dir():
    """Crée le répertoire de données"""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_wallets() -> Dict[str, SmartWallet]:
    """Charge tous les wallets smart money"""
    ensure_data_dir()
    if os.path.exists(WALLETS_FILE):
        try:
            with open(WALLETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {addr: SmartWallet.from_dict(w) for addr, w in data.items()}
        except Exception as e:
            print(f"[ERROR] Loading wallets: {e}")
    return {}


def save_wallets(wallets: Dict[str, SmartWallet]):
    """Sauvegarde les wallets"""
    ensure_data_dir()
    data = {addr: w.to_dict() for addr, w in wallets.items()}
    with open(WALLETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def add_wallet(
    address: str,
    network: str,
    name: str = "",
    tier: str = "UNRANKED",
    win_rate: float = 0.0,
    notes: str = ""
) -> Tuple[bool, str]:
    """
    Ajoute un wallet à la watchlist.

    Args:
        address: Adresse du wallet
        network: Network (solana, eth, base, bsc)
        name: Surnom optionnel
        tier: LEGENDARY, ELITE, PROVEN, PROMISING, UNRANKED
        win_rate: Win rate estimé (0-100)
        notes: Notes sur le wallet

    Returns:
        (success, message)
    """
    wallets = load_wallets()
    addr_lower = address.lower()

    if addr_lower in wallets:
        return False, f"Wallet already in watchlist: {wallets[addr_lower].name or addr_lower[:8]}"

    wallet = SmartWallet(
        address=addr_lower,
        network=network.lower(),
        name=name or f"Wallet_{addr_lower[:6]}",
        tier=tier,
        win_rate=win_rate,
        added_date=datetime.now(timezone.utc).isoformat(),
        last_activity="",
        is_active=True,
        notes=notes
    )

    wallets[addr_lower] = wallet
    save_wallets(wallets)

    return True, f"Wallet added: {wallet.name} ({network.upper()})"


def remove_wallet(address: str) -> Tuple[bool, str]:
    """Remove a wallet from watchlist"""
    wallets = load_wallets()
    addr_lower = address.lower()

    if addr_lower not in wallets:
        return False, "Wallet not found"

    name = wallets[addr_lower].name
    del wallets[addr_lower]
    save_wallets(wallets)

    return True, f"Wallet removed: {name}"


def list_wallets() -> List[SmartWallet]:
    """Liste tous les wallets actifs"""
    wallets = load_wallets()
    return [w for w in wallets.values() if w.is_active]


def update_wallet_stats(address: str, **kwargs) -> bool:
    """Met à jour les stats d'un wallet"""
    wallets = load_wallets()
    addr_lower = address.lower()

    if addr_lower not in wallets:
        return False

    wallet = wallets[addr_lower]
    for key, value in kwargs.items():
        if hasattr(wallet, key):
            setattr(wallet, key, value)

    wallets[addr_lower] = wallet
    save_wallets(wallets)
    return True


# =============================================================================
# MONITORING DES TRANSACTIONS
# =============================================================================

def get_recent_transactions_dexscreener(token_address: str, network: str) -> List[dict]:
    """
    Récupère les transactions récentes d'un token via DexScreener.

    Note: DexScreener montre les transactions du pool, pas par wallet.
    Pour le copy trading par wallet, on aurait besoin de Solscan/Etherscan.
    """
    try:
        req = _get_requests()
        url = f"{DEXSCREENER_API}/tokens/{token_address}"
        response = req.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # DexScreener retourne les pairs, pas les transactions individuelles
            # On peut extraire les "makers" (top traders)
            pairs = data.get('pairs', [])
            if pairs:
                return pairs[0].get('txns', {})
        return []
    except Exception as e:
        print(f"[ERROR] DexScreener API: {e}")
        return []


def check_wallet_activity_solana(wallet_address: str) -> List[dict]:
    """
    Vérifie l'activité récente d'un wallet Solana via Solscan.

    Returns:
        Liste des transactions récentes avec token swaps
    """
    try:
        req = _get_requests()
        url = f"{SOLSCAN_API}/account/transactions"
        params = {
            'account': wallet_address,
            'limit': 20
        }
        headers = {
            'Accept': 'application/json'
        }
        response = req.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            txs = response.json()
            # Filtrer les swaps (token transfers)
            swaps = []
            for tx in txs:
                if tx.get('txType') in ['swap', 'transfer']:
                    swaps.append({
                        'tx_hash': tx.get('txHash'),
                        'timestamp': tx.get('blockTime'),
                        'type': tx.get('txType'),
                        'status': tx.get('status'),
                    })
            return swaps
        return []
    except Exception as e:
        print(f"[ERROR] Solscan API: {e}")
        return []


def monitor_wallet_for_signals(wallet: SmartWallet) -> List[CopySignal]:
    """
    Monitore un wallet et génère des signaux de copy trading.

    Returns:
        Liste de nouveaux signaux détectés
    """
    signals = []

    if wallet.network == 'solana':
        transactions = check_wallet_activity_solana(wallet.address)
    else:
        # Pour ETH/Base/BSC, on aurait besoin d'Etherscan API
        # Pour l'instant, on retourne vide
        transactions = []

    for tx in transactions:
        # Analyser la transaction pour détecter buy/sell
        # Ceci est simplifié - une vraie implémentation parserait les logs
        pass

    return signals


# =============================================================================
# GÉNÉRATION DE SIGNAUX
# =============================================================================

def generate_copy_signal(
    wallet: SmartWallet,
    action: str,
    token_address: str,
    token_symbol: str,
    amount_usd: float,
    amount_native: float,
    price: float,
    tx_hash: str = ""
) -> CopySignal:
    """Génère un signal de copy trading"""
    signal_id = f"{wallet.address[:8]}_{token_symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    signal = CopySignal(
        signal_id=signal_id,
        wallet_address=wallet.address,
        wallet_name=wallet.name,
        action=action,
        token_address=token_address,
        token_symbol=token_symbol,
        network=wallet.network,
        amount_usd=amount_usd,
        amount_native=amount_native,
        price_at_signal=price,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tx_hash=tx_hash
    )

    # Sauvegarder le signal
    save_signal(signal)

    return signal


def save_signal(signal: CopySignal):
    """Sauvegarde un signal"""
    ensure_data_dir()
    signals = load_signals()
    signals.append(signal.to_dict())

    # Garder seulement les 1000 derniers signaux
    if len(signals) > 1000:
        signals = signals[-1000:]

    with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(signals, f, indent=2)


def load_signals() -> List[dict]:
    """Charge les signaux existants"""
    if os.path.exists(SIGNALS_FILE):
        try:
            with open(SIGNALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []


def get_recent_signals(hours: int = 24) -> List[dict]:
    """Récupère les signaux des dernières X heures"""
    signals = load_signals()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    recent = []
    for s in signals:
        try:
            ts = datetime.fromisoformat(s['timestamp'].replace('Z', '+00:00'))
            if ts > cutoff:
                recent.append(s)
        except:
            pass

    return recent


# =============================================================================
# INTÉGRATION AVEC LE SCANNER
# =============================================================================

def check_smart_money_bought_token(token_address: str, network: str) -> dict:
    """
    Vérifie si des smart money wallets ont acheté ce token.

    Utilisé par le scanner pour enrichir les alertes.

    Returns:
        {
            'has_smart_money': bool,
            'wallets': list of wallet names,
            'total_amount_usd': float,
            'highest_tier': str,
            'signal_strength': str
        }
    """
    result = {
        'has_smart_money': False,
        'wallets': [],
        'total_amount_usd': 0,
        'highest_tier': 'NONE',
        'signal_strength': 'NONE'
    }

    # Pour une vraie implémentation, on queryrait les APIs blockchain
    # pour vérifier les holders du token et croiser avec notre watchlist

    wallets = load_wallets()

    # Placeholder - dans une vraie implémentation:
    # 1. Récupérer les top holders du token
    # 2. Croiser avec notre watchlist
    # 3. Vérifier les achats récents

    return result


def format_copy_signal_message(signal: CopySignal) -> str:
    """Formate un signal pour Telegram"""
    emoji = "🟢" if signal.action == "BUY" else "🔴"
    tier_emoji = {
        'LEGENDARY': '👑',
        'ELITE': '⭐',
        'PROVEN': '✅',
        'PROMISING': '📈',
        'UNRANKED': '❓'
    }

    wallets = load_wallets()
    wallet = wallets.get(signal.wallet_address.lower())
    tier = wallet.tier if wallet else 'UNRANKED'

    msg = f"""
{emoji} **COPY SIGNAL - {signal.action}** {emoji}

{tier_emoji.get(tier, '❓')} Wallet: {signal.wallet_name} ({tier})
🪙 Token: {signal.token_symbol}
🔗 Network: {signal.network.upper()}

💰 Montant: ${signal.amount_usd:,.2f}
💵 Prix: ${signal.price_at_signal:.8f}

⏰ {signal.timestamp[:19]}

🔍 TX: {signal.tx_hash[:20]}... (si disponible)
"""
    return msg.strip()


# =============================================================================
# CLI POUR GESTION DES WALLETS
# =============================================================================

def print_wallet_list():
    """Display wallet list"""
    wallets = list_wallets()

    if not wallets:
        print("\n[EMPTY] No wallets in watchlist")
        print("        Use add_wallet() to add one")
        return

    print("\n" + "=" * 70)
    print("SMART MONEY WATCHLIST")
    print("=" * 70)

    tier_order = ['LEGENDARY', 'ELITE', 'PROVEN', 'PROMISING', 'UNRANKED']

    for tier in tier_order:
        tier_wallets = [w for w in wallets if w.tier == tier]
        if tier_wallets:
            print(f"\n{tier} ({len(tier_wallets)}):")
            print("-" * 50)
            for w in tier_wallets:
                status = "[OK]" if w.is_active else "[X]"
                print(f"  {status} {w.name:<20} | {w.network:<8} | WR: {w.win_rate:>5.1f}%")
                print(f"       {w.address[:20]}...")
                if w.notes:
                    print(f"       Note: {w.notes}")

    print("\n" + "=" * 70)
    print(f"Total: {len(wallets)} wallets")
    print("=" * 70)


# =============================================================================
# EXEMPLES DE WALLETS À AJOUTER
# =============================================================================

# Méthode pour trouver des smart wallets:
# 1. DexScreener > Top Gainers 24h
# 2. Cliquer sur un token qui a bien performé
# 3. Onglet "Top Traders" ou "Transactions"
# 4. Filtrer par BUY, gros montants ($10K+)
# 5. Copier l'adresse du wallet
# 6. Analyser sur Debank/Solscan l'historique
# 7. Si win rate > 60%, ajouter à la watchlist

EXAMPLE_WALLETS = [
    # Ces wallets sont des EXEMPLES - à remplacer par de vrais wallets analysés
    # {
    #     'address': '0x1234...abcd',
    #     'network': 'eth',
    #     'name': 'WhaleTrader_ETH_01',
    #     'tier': 'ELITE',
    #     'win_rate': 72.5,
    #     'notes': 'Trouvé via DexScreener, WR validé sur Debank'
    # },
]


if __name__ == "__main__":
    print("=" * 60)
    print("COPY TRADING SYSTEM V1.0")
    print("=" * 60)

    # Afficher la watchlist
    print_wallet_list()

    # Exemple d'ajout de wallet
    print("\n[EXEMPLE] Pour ajouter un wallet:")
    print("""
    from core.copy_trading import add_wallet

    # Ajouter un wallet Solana
    add_wallet(
        address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        network="solana",
        name="SolanaWhale_01",
        tier="PROVEN",
        win_rate=65.0,
        notes="Trouvé sur DexScreener, vérifié sur Solscan"
    )

    # Ajouter un wallet ETH
    add_wallet(
        address="0x1234567890abcdef1234567890abcdef12345678",
        network="eth",
        name="ETH_SmartMoney_01",
        tier="ELITE",
        win_rate=70.0,
        notes="Top trader sur CFY token"
    )
    """)

    print("\n[INFO] Méthodologie pour trouver des smart wallets:")
    print("  1. Aller sur https://dexscreener.com")
    print("  2. Filtrer par Top Gainers 24h")
    print("  3. Cliquer sur un token performant")
    print("  4. Onglet 'Transactions' > Filtrer 'Buy' > Gros montants")
    print("  5. Copier l'adresse du 'Maker' (wallet)")
    print("  6. Analyser sur Debank/Solscan son historique")
    print("  7. Si WR > 60%, ajouter à la watchlist")
