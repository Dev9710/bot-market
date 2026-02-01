"""
Whale Wallet Tracker - Suivi des wallets de gros traders memecoins

Ce module track les wallets connus de traders memecoins performants.
Si plusieurs de ces wallets achètent le même token = signal fort d'entrée.

LOGIQUE:
1. Liste des whale wallets (from data/wallet.py)
2. Pour chaque token détecté, vérifier si des whales ont acheté récemment
3. Si 2+ whales achètent le même token → SIGNAL FORT (A++)

API utilisée: Helius (Solana) ou fallback sur Solscan
"""

import os
import time
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache

# ============================================
# WHALE WALLETS - Traders memecoins connus
# ============================================
# Source: data/wallet.py

WHALE_WALLETS = {
    # Nom: Adresse wallet
    "Gake": "DNfuF1L62WWyW3pNakVkyGGFzVVhj4Yr52jSmdTyeBHm",
    "Cupsey": "2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f",
    "Jidn": "3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE",
    "Soloxbt": "FTg1gqW7vPm4kdU1LPM7JJnizbgPdRDy2PitKw6mY27j",
    "Pow": "8zFZHuSRuDpuAR7J6FzwyF3vKNx4CVW3DFHJerQhc7Zd",
    "Loopierr": "9yYya3F5EJoLnBNKW6z4bZvyQytMXzDcpU5D6yYr4jqL",
    "OGAntD": "215nhcAHjQQGgwpQSJQ7zR26etbjjtVdW74NLzwEgQjP",
    "Coyote": "A4DCAjDwkq5jYhNoZ5Xn2NbkTLimARkerVv81w2dhXgL",
    "Marcell_1": "ACHhRQMbTxuWqU3bmbBbgUNGsPsYnvB8KLcPkkXCY1C7",
    "Marcell_2": "3zD1armVsd4UUDW4RvcaE4ve6oEkmGyHPEjtB7q5Q9LU",
}

# Inverser pour lookup rapide par adresse
WALLET_TO_NAME = {v: k for k, v in WHALE_WALLETS.items()}

# ============================================
# CONFIGURATION
# ============================================

# API Helius (gratuit avec rate limit)
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
HELIUS_BASE_URL = "https://api.helius.xyz/v0"

# Fallback: Solscan API (gratuit)
SOLSCAN_BASE_URL = "https://api.solscan.io"

# Cache des transactions (évite de spammer l'API)
CACHE_TTL_SECONDS = 300  # 5 minutes

# Seuils
MIN_WHALES_FOR_STRONG_SIGNAL = 2  # Minimum 2 whales pour signal fort
LOOKBACK_HOURS = 24  # Regarder les transactions des dernières 24h


class WhaleTracker:
    """
    Tracker des whale wallets pour détecter les signaux d'entrée.
    """

    def __init__(self, helius_api_key: str = None):
        self.api_key = helius_api_key or HELIUS_API_KEY
        self._cache = {}  # Cache des tokens achetés par wallet
        self._cache_timestamps = {}

    def _is_cache_valid(self, wallet: str) -> bool:
        """Vérifie si le cache est encore valide."""
        if wallet not in self._cache_timestamps:
            return False
        age = time.time() - self._cache_timestamps[wallet]
        return age < CACHE_TTL_SECONDS

    def get_whale_recent_buys(self, wallet_address: str) -> List[Dict]:
        """
        Récupère les achats récents d'un whale wallet.

        Returns:
            Liste de tokens achetés avec timestamp et montant
        """
        # Vérifier le cache
        if self._is_cache_valid(wallet_address):
            return self._cache.get(wallet_address, [])

        buys = []

        # Essayer Helius d'abord (meilleure API)
        if self.api_key:
            buys = self._fetch_from_helius(wallet_address)

        # Fallback sur Solscan si Helius échoue
        if not buys:
            buys = self._fetch_from_solscan(wallet_address)

        # Mettre en cache
        self._cache[wallet_address] = buys
        self._cache_timestamps[wallet_address] = time.time()

        return buys

    def _fetch_from_helius(self, wallet_address: str) -> List[Dict]:
        """
        Récupère les transactions depuis Helius API.
        """
        if not self.api_key:
            return []

        try:
            url = f"{HELIUS_BASE_URL}/addresses/{wallet_address}/transactions"
            params = {
                "api-key": self.api_key,
                "limit": 50,  # Dernières 50 transactions
                "type": "SWAP"  # Seulement les swaps
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"[WhaleTracker] Helius error: {response.status_code}")
                return []

            transactions = response.json()
            return self._parse_helius_transactions(transactions, wallet_address)

        except Exception as e:
            print(f"[WhaleTracker] Helius exception: {e}")
            return []

    def _fetch_from_solscan(self, wallet_address: str) -> List[Dict]:
        """
        Fallback: Récupère les transactions depuis Solscan API.
        """
        try:
            url = f"{SOLSCAN_BASE_URL}/account/splTransfers"
            params = {
                "account": wallet_address,
                "limit": 50,
            }
            headers = {
                "Accept": "application/json",
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[WhaleTracker] Solscan error: {response.status_code}")
                return []

            data = response.json()
            return self._parse_solscan_transactions(data, wallet_address)

        except Exception as e:
            print(f"[WhaleTracker] Solscan exception: {e}")
            return []

    def _parse_helius_transactions(self, transactions: List, wallet_address: str) -> List[Dict]:
        """
        Parse les transactions Helius pour extraire les achats de tokens.
        """
        buys = []
        cutoff_time = datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)

        for tx in transactions:
            try:
                # Vérifier le timestamp
                timestamp = tx.get("timestamp", 0)
                tx_time = datetime.utcfromtimestamp(timestamp)
                if tx_time < cutoff_time:
                    continue

                # Extraire les token transfers
                token_transfers = tx.get("tokenTransfers", [])
                for transfer in token_transfers:
                    # C'est un achat si le wallet reçoit le token
                    if transfer.get("toUserAccount") == wallet_address:
                        buys.append({
                            "token_address": transfer.get("mint", ""),
                            "amount": transfer.get("tokenAmount", 0),
                            "timestamp": tx_time,
                            "signature": tx.get("signature", ""),
                            "type": "BUY"
                        })

            except Exception as e:
                continue

        return buys

    def _parse_solscan_transactions(self, data: Dict, wallet_address: str) -> List[Dict]:
        """
        Parse les transactions Solscan pour extraire les achats.
        """
        buys = []
        cutoff_time = datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)

        transfers = data.get("data", [])
        for transfer in transfers:
            try:
                # Vérifier le timestamp
                block_time = transfer.get("blockTime", 0)
                tx_time = datetime.utcfromtimestamp(block_time)
                if tx_time < cutoff_time:
                    continue

                # C'est un achat si le wallet est le destinataire
                if transfer.get("dst") == wallet_address:
                    buys.append({
                        "token_address": transfer.get("tokenAddress", ""),
                        "amount": transfer.get("amount", 0),
                        "timestamp": tx_time,
                        "signature": transfer.get("signature", ""),
                        "type": "BUY"
                    })

            except Exception as e:
                continue

        return buys

    def check_whale_activity_for_token(self, token_address: str) -> Dict:
        """
        Vérifie si des whales ont acheté un token spécifique.

        Args:
            token_address: Adresse du token à vérifier

        Returns:
            Dict avec:
                - whale_buyers: Liste des whales qui ont acheté
                - whale_count: Nombre de whales
                - is_strong_signal: True si >= 2 whales
                - signal_strength: Score de 0 à 100
                - details: Détails des achats
        """
        whale_buyers = []
        details = []

        for wallet_name, wallet_address in WHALE_WALLETS.items():
            try:
                buys = self.get_whale_recent_buys(wallet_address)

                # Chercher si ce wallet a acheté le token
                for buy in buys:
                    if buy.get("token_address", "").lower() == token_address.lower():
                        whale_buyers.append(wallet_name)
                        details.append({
                            "whale": wallet_name,
                            "wallet": wallet_address,
                            "amount": buy.get("amount", 0),
                            "timestamp": buy.get("timestamp"),
                            "signature": buy.get("signature", "")
                        })
                        break  # Un seul achat par whale suffit

            except Exception as e:
                print(f"[WhaleTracker] Error checking {wallet_name}: {e}")
                continue

        whale_count = len(whale_buyers)
        is_strong_signal = whale_count >= MIN_WHALES_FOR_STRONG_SIGNAL

        # Calculer signal strength (0-100)
        # 1 whale = 30 pts, 2 whales = 60 pts, 3+ = 80+ pts
        if whale_count == 0:
            signal_strength = 0
        elif whale_count == 1:
            signal_strength = 30
        elif whale_count == 2:
            signal_strength = 60
        elif whale_count == 3:
            signal_strength = 80
        else:
            signal_strength = min(100, 80 + (whale_count - 3) * 10)

        return {
            "whale_buyers": whale_buyers,
            "whale_count": whale_count,
            "is_strong_signal": is_strong_signal,
            "signal_strength": signal_strength,
            "details": details,
            "token_address": token_address,
            "checked_at": datetime.utcnow().isoformat()
        }

    def get_all_whale_recent_tokens(self) -> Dict[str, List[str]]:
        """
        Récupère tous les tokens achetés récemment par les whales.

        Returns:
            Dict {token_address: [list of whale names who bought]}
        """
        token_to_whales = {}

        for wallet_name, wallet_address in WHALE_WALLETS.items():
            try:
                buys = self.get_whale_recent_buys(wallet_address)

                for buy in buys:
                    token_addr = buy.get("token_address", "")
                    if token_addr:
                        if token_addr not in token_to_whales:
                            token_to_whales[token_addr] = []
                        if wallet_name not in token_to_whales[token_addr]:
                            token_to_whales[token_addr].append(wallet_name)

            except Exception as e:
                continue

        return token_to_whales

    def get_hot_tokens(self) -> List[Dict]:
        """
        Identifie les tokens "chauds" achetés par plusieurs whales.

        Returns:
            Liste de tokens triés par nombre de whale buyers
        """
        token_to_whales = self.get_all_whale_recent_tokens()

        hot_tokens = []
        for token_addr, whales in token_to_whales.items():
            if len(whales) >= MIN_WHALES_FOR_STRONG_SIGNAL:
                hot_tokens.append({
                    "token_address": token_addr,
                    "whale_count": len(whales),
                    "whale_buyers": whales,
                    "is_strong_signal": True
                })

        # Trier par nombre de whales (décroissant)
        hot_tokens.sort(key=lambda x: -x["whale_count"])

        return hot_tokens


# ============================================
# SINGLETON INSTANCE
# ============================================

_tracker_instance = None


def get_whale_tracker() -> WhaleTracker:
    """Retourne l'instance singleton du WhaleTracker."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = WhaleTracker()
    return _tracker_instance


def check_whale_signal(token_address: str) -> Dict:
    """
    Fonction utilitaire pour vérifier le signal whale d'un token.

    Args:
        token_address: Adresse du token

    Returns:
        Dict avec whale_count, is_strong_signal, signal_strength
    """
    tracker = get_whale_tracker()
    return tracker.check_whale_activity_for_token(token_address)


# ============================================
# INTEGRATION AVEC STRATEGY
# ============================================

def enhance_alert_with_whale_data(alert: Dict) -> Dict:
    """
    Enrichit une alerte avec les données de whale tracking.

    Args:
        alert: Alerte originale

    Returns:
        Alerte enrichie avec whale_tracker_* fields
    """
    token_address = alert.get("pool_address", "") or alert.get("token_address", "")

    if not token_address:
        return alert

    try:
        whale_data = check_whale_signal(token_address)

        alert["whale_tracker_count"] = whale_data["whale_count"]
        alert["whale_tracker_buyers"] = whale_data["whale_buyers"]
        alert["whale_tracker_strong_signal"] = whale_data["is_strong_signal"]
        alert["whale_tracker_strength"] = whale_data["signal_strength"]

        # Bonus au score si signal whale fort
        if whale_data["is_strong_signal"]:
            current_score = alert.get("score", 0)
            # Bonus: +20 pour 2 whales, +30 pour 3+
            whale_bonus = 20 if whale_data["whale_count"] == 2 else 30
            alert["whale_tracker_bonus"] = whale_bonus
            alert["score"] = current_score + whale_bonus

    except Exception as e:
        print(f"[WhaleTracker] Error enhancing alert: {e}")

    return alert
