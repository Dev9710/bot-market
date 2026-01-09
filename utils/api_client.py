"""
API Client GeckoTerminal - Appels API et parsing

Gère toutes les interactions avec l'API GeckoTerminal:
- Récupération pools trending et nouveaux
- Récupération pool par adresse
- Parsing complet des données de pool
"""

import time
import requests
from datetime import datetime
from typing import Dict, List, Optional

from config.settings import GECKOTERMINAL_API
from utils.helpers import log, extract_base_token


def get_trending_pools(network: str, page: int = 1) -> Optional[List[Dict]]:
    """Récupère pools trending sur un réseau."""
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/trending_pools"
        params = {"page": page}
        headers = {"Accept": "application/json"}
        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 429:
            log(f"⚠️ Rate limit atteint, pause 60s...")
            time.sleep(60)
            return None
        if response.status_code != 200:
            log(f"⚠️ Erreur {network}: {response.status_code}")
            return None

        data = response.json()
        pools = data.get("data", [])

        # DEBUG: Log premier pool brut pour diagnostic
        if pools and page == 1 and not hasattr(get_trending_pools, '_logged_raw'):
            import json as json_lib
            log(f"   [DEBUG-RAW-POOL] Premier trending pool {network}:")
            log(f"      {json_lib.dumps(pools[0], indent=2)[:800]}")  # 800 premiers caractères
            get_trending_pools._logged_raw = True

        return pools
    except Exception as e:
        log(f"❌ Erreur get_trending_pools {network}: {e}")
        return None


def get_new_pools(network: str, page: int = 1) -> Optional[List[Dict]]:
    """Récupère nouveaux pools sur un réseau."""
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/new_pools"
        params = {"page": page}
        headers = {"Accept": "application/json"}
        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 429:
            log(f"⚠️ Rate limit atteint, pause 60s...")
            time.sleep(60)
            return None
        if response.status_code != 200:
            return None

        data = response.json()
        pools = data.get("data", [])

        # DEBUG: Logger structure du premier NEW pool (une seule fois)
        if pools and not hasattr(get_new_pools, '_logged_structure'):
            log(f"   [DEBUG-NEW-POOL] Premier NEW pool {network}:")
            first_pool = pools[0]
            attrs = first_pool.get("attributes", {})
            log(f"      Name: {attrs.get('name', 'N/A')}")
            log(f"      reserve_in_usd: {attrs.get('reserve_in_usd', 'MISSING')}")
            log(f"      fdv_usd: {attrs.get('fdv_usd', 'MISSING')}")
            log(f"      market_cap_usd: {attrs.get('market_cap_usd', 'MISSING')}")
            get_new_pools._logged_structure = True

        return pools
    except Exception as e:
        log(f"❌ Erreur get_new_pools {network}: {e}")
        return None


def get_pool_by_address(network: str, pool_address: str) -> Optional[Dict]:
    """
    Récupère les données d'un pool spécifique via son adresse.
    Utilisé pour le tracking actif des alertes.

    Args:
        network: Réseau (eth, bsc, solana, etc.)
        pool_address: Adresse du pool

    Returns:
        Dict avec les données du pool, ou None si erreur
    """
    try:
        url = f"{GECKOTERMINAL_API}/networks/{network}/pools/{pool_address}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 429:
            log(f"⚠️ Rate limit atteint pour pool {pool_address[:8]}...")
            time.sleep(60)
            return None
        if response.status_code != 200:
            log(f"⚠️ Pool {pool_address[:8]} non trouvé (status {response.status_code})")
            return None

        data = response.json()
        pool_data = data.get("data")

        if pool_data:
            return parse_pool_data(pool_data, network)
        return None

    except Exception as e:
        log(f"❌ Erreur get_pool_by_address {pool_address[:8]}: {e}")
        return None


def parse_pool_data(pool: Dict, network: str = "unknown", liquidity_stats: Dict = None) -> Optional[Dict]:
    """Parse données pool GeckoTerminal avec enrichissements."""
    try:
        attrs = pool.get("attributes", {})

        # DEBUG: Log structure du premier pool pour diagnostiquer
        if not hasattr(parse_pool_data, '_logged_structure'):
            log(f"   [DEBUG-STRUCTURE] Premier pool reçu:")
            log(f"      Pool keys: {list(pool.keys())}")
            log(f"      Attributes keys: {list(attrs.keys())[:10]}")  # Premiers 10 keys
            if 'reserve_in_usd' in attrs:
                log(f"      reserve_in_usd found: {attrs['reserve_in_usd']}")
            else:
                log(f"      reserve_in_usd NOT FOUND in attributes!")
            parse_pool_data._logged_structure = True

        # Infos de base
        name = attrs.get("name", "Unknown")
        base_token_name = extract_base_token(name)
        base_token_price = attrs.get("base_token_price_usd")
        price_usd = float(base_token_price) if base_token_price else 0

        # Volume et liquidité (protéger contre None)
        volume_usd_data = attrs.get("volume_usd", {}) or {}
        volume_24h = float(volume_usd_data.get("h24") or 0)
        volume_6h = float(volume_usd_data.get("h6") or 0)
        volume_1h = float(volume_usd_data.get("h1") or 0)

        # Liquidity - avec fallback sur FDV, Market Cap et Volume
        reserve_value = attrs.get("reserve_in_usd")
        liquidity = 0
        liquidity_source = "none"

        # DEBUG SYSTEMATIQUE: Logger TOUTES les valeurs brutes (premiers pools seulement)
        if not hasattr(parse_pool_data, '_debug_count'):
            parse_pool_data._debug_count = 0
        if parse_pool_data._debug_count < 5:  # Log 5 premiers pools
            log(f"   [DEBUG-VALUES] {name[:30]}: reserve={reserve_value}, fdv={attrs.get('fdv_usd')}, mcap={attrs.get('market_cap_usd')}, vol={volume_24h}")
            parse_pool_data._debug_count += 1

        # Essayer reserve_in_usd d'abord - ACCEPTER "0.0" pour tester après conversion
        if reserve_value not in [None, "", "null"]:
            try:
                liquidity = float(reserve_value)
                if liquidity > 0:
                    liquidity_source = "reserve_in_usd"
            except (ValueError, TypeError):
                pass  # Continue vers fallbacks

        # FALLBACK 1: Si reserve_in_usd est 0, essayer fdv_usd (25% du FDV)
        if liquidity == 0:
            fdv_value = attrs.get("fdv_usd")
            if fdv_value not in [None, "", "null"]:
                try:
                    fdv = float(fdv_value)
                    if fdv > 0:
                        # FIXED: Estimer liquidité à 25% du FDV (plus réaliste pour meme coins)
                        # Anciennement 10% était trop conservateur
                        liquidity = fdv * 0.25
                        liquidity_source = "fdv_usd(25%)"
                    else:
                        # DEBUG: FDV est 0
                        if parse_pool_data._debug_count < 10:
                            log(f"   [DEBUG-FDV] {name[:30]}: fdv_value={fdv_value}, fdv_float={fdv}, result=0")
                except (ValueError, TypeError) as e:
                    if parse_pool_data._debug_count < 10:
                        log(f"   [DEBUG-FDV-ERROR] {name[:30]}: fdv_value={fdv_value}, error={e}")

        # FALLBACK 2: Si toujours 0, essayer market_cap_usd (30% du market cap)
        if liquidity == 0:
            mcap_value = attrs.get("market_cap_usd")
            if mcap_value not in [None, "", "null"]:
                try:
                    mcap = float(mcap_value)
                    if mcap > 0:
                        # FIXED: Estimer liquidité à 30% du market cap (plus réaliste)
                        # Anciennement 15% était trop conservateur
                        liquidity = mcap * 0.30
                        liquidity_source = "market_cap(30%)"
                except (ValueError, TypeError):
                    pass

        # FALLBACK 3: Si TOUJOURS 0, estimer depuis volume_24h (ratio plus généreux)
        if liquidity == 0 and volume_24h > 0:
            # FIXED: Ratio plus réaliste pour ETH/BSC: liquidité = 8-10x le volume 24h
            # (Sur Solana c'est ~5x, mais sur ETH/BSC les pools sont plus profonds)
            if network in ['eth', 'bsc', 'base']:
                liquidity = volume_24h * 10  # Ratio plus élevé pour L1/BSC
            else:
                liquidity = volume_24h * 6   # Ratio modéré pour autres réseaux
            liquidity_source = f"volume_24h(x{10 if network in ['eth', 'bsc', 'base'] else 6})"

        # Log PERMANENT de la source de liquidité (CRITIQUE pour vérifier qualité données)
        if liquidity == 0:
            log(f"   ⚠️ [LIQ=0] {name} ({network.upper()}): reserve={reserve_value}, fdv={attrs.get('fdv_usd')}, mcap={attrs.get('market_cap_usd')}, vol24h={volume_24h}")
        elif liquidity_source != "reserve_in_usd":
            # ALERTE: Utilisation d'estimation au lieu de donnée réelle!
            log(f"   📊 [LIQ-ESTIMATE] {name} ({network.upper()}): ${liquidity:,.0f} from {liquidity_source}")

        # Mettre à jour les statistiques de sources de liquidité
        if liquidity_stats is not None:
            liquidity_stats[liquidity_source] = liquidity_stats.get(liquidity_source, 0) + 1

        # Transactions (protéger contre None)
        transactions_data = attrs.get("transactions", {}) or {}
        txns_24h = transactions_data.get("h24", {}) or {}
        txns_6h = transactions_data.get("h6", {}) or {}
        txns_1h = transactions_data.get("h1", {}) or {}

        buys_24h = txns_24h.get("buys", 0)
        sells_24h = txns_24h.get("sells", 0)
        buys_6h = txns_6h.get("buys", 0)
        sells_6h = txns_6h.get("sells", 0)
        buys_1h = txns_1h.get("buys", 0)
        sells_1h = txns_1h.get("sells", 0)

        # NOUVEAU: Wallets uniques (buyers/sellers) - FEATURE WHALE DETECTION
        buyers_24h = txns_24h.get("buyers", 0)
        sellers_24h = txns_24h.get("sellers", 0)
        buyers_6h = txns_6h.get("buyers", 0)
        sellers_6h = txns_6h.get("sellers", 0)
        buyers_1h = txns_1h.get("buyers", 0)
        sellers_1h = txns_1h.get("sellers", 0)

        total_txns = buys_24h + sells_24h

        # Variations prix (multi-timeframe depuis API) - Protéger contre None
        price_changes = attrs.get("price_change_percentage", {}) or {}
        price_change_24h = float(price_changes.get("h24") or 0)
        price_change_6h = float(price_changes.get("h6") or 0)
        price_change_3h = float(price_changes.get("h3") or 0)
        price_change_1h = float(price_changes.get("h1") or 0)

        # Age du pool
        pool_created = attrs.get("pool_created_at")
        if pool_created:
            created_dt = datetime.fromisoformat(pool_created.replace('Z', '+00:00'))
            age_hours = (datetime.now().astimezone() - created_dt).total_seconds() / 3600
        else:
            age_hours = 999999

        # Réseau et adresse - Utiliser le paramètre network passé directement
        # On garde le network passé en paramètre (fourni lors de l'appel de l'API)
        # Si ce n'était pas fourni, on essaie de l'extraire des relationships
        if network == "unknown":
            relationships = pool.get("relationships", {}) or {}
            network_data = relationships.get("network", {}) or {}
            network_inner = network_data.get("data", {}) or {}
            network = network_inner.get("id", "unknown")

            # Si network toujours unknown, essayer de l'extraire du type
            if network == "unknown":
                pool_type = pool.get("type", "")
                # Format peut être "pool" ou "network-name-pool"
                if "-" in pool_type:
                    network = pool_type.split("-")[0]

        pool_address = attrs.get("address", "")

        # FDV et Market Cap (protéger contre None)
        fdv_usd = float(attrs.get("fdv_usd") or 0)
        market_cap_usd = float(attrs.get("market_cap_usd") or 0)

        # Calculer l'accélération du volume (NOUVEAU)
        vol_24h_avg = volume_24h / 24 if volume_24h > 0 else 0
        vol_6h_avg = volume_6h / 6 if volume_6h > 0 else 0

        volume_acceleration_1h_vs_6h = (volume_1h / vol_6h_avg) if vol_6h_avg > 0 else 0
        volume_acceleration_6h_vs_24h = (vol_6h_avg / vol_24h_avg) if vol_24h_avg > 0 else 0

        # ===== V3: CALCULER VELOCITE ET TYPE PUMP (depuis price_change_1h) =====
        # Utiliser price_change_1h comme proxy de vélocité (% par heure)
        velocite_pump = abs(price_change_1h) if price_change_1h else 0

        # Déterminer type de pump basé sur vélocité
        if velocite_pump > 100:
            type_pump = "PARABOLIQUE"
        elif velocite_pump > 50:
            type_pump = "TRES_RAPIDE"
        elif velocite_pump > 20:
            type_pump = "RAPIDE"
        elif velocite_pump > 5:
            type_pump = "NORMAL"
        else:
            type_pump = "LENT"

        # Ajouter token_name et token_symbol pour watchlist check
        token_name = base_token_name  # Déjà extrait
        token_symbol = base_token_name  # On utilise le nom de base comme symbole

        return {
            "name": name,
            "base_token_name": base_token_name,
            "token_name": token_name,  # V3: Pour watchlist
            "token_symbol": token_symbol,  # V3: Pour watchlist
            "price_usd": price_usd,
            "volume_24h": volume_24h,
            "volume_6h": volume_6h,
            "volume_1h": volume_1h,
            "liquidity": liquidity,
            "total_txns": total_txns,
            "buys_24h": buys_24h,
            "sells_24h": sells_24h,
            "buys_6h": buys_6h,
            "sells_6h": sells_6h,
            "buys_1h": buys_1h,
            "sells_1h": sells_1h,
            "buyers_24h": buyers_24h,
            "sellers_24h": sellers_24h,
            "buyers_6h": buyers_6h,
            "sellers_6h": sellers_6h,
            "buyers_1h": buyers_1h,
            "sellers_1h": sellers_1h,
            "price_change_24h": price_change_24h,
            "price_change_6h": price_change_6h,
            "price_change_3h": price_change_3h,
            "price_change_1h": price_change_1h,
            "age_hours": age_hours,
            "network": network,
            "pool_address": pool_address,
            "fdv_usd": fdv_usd,
            "market_cap_usd": market_cap_usd,
            "volume_acceleration_1h_vs_6h": volume_acceleration_1h_vs_6h,
            "volume_acceleration_6h_vs_24h": volume_acceleration_6h_vs_24h,
            "velocite_pump": velocite_pump,  # V3: Pour filtres backtest
            "type_pump": type_pump,  # V3: Pour filtres backtest
        }
    except Exception as e:
        log(f"⚠️ Erreur parse pool: {e}")
        return None
