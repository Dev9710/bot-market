"""
Hyperliquid Scanner - Detection opportunites trading perpetuels
Detecte: nouveaux marches, whales, liquidations, funding rates, volume spikes
API Gratuite: 1200 weight/min (tres genereux)
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# UTF-8 pour emojis Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (ValueError, AttributeError):
            pass

# Configuration
HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7868518759:AAFxEXGz0DgMPYVKILJOEb5kNDwPy3N5W5c")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7994790177")

# Seuils de detection (configurables)
THRESHOLDS = {
    # Alertes Haute Priorite
    "new_market_volume_1h": 1_000_000,      # $1M volume en 1h
    "whale_position_size": 500_000,          # $500k position
    "liquidation_cascade": 1_000_000,        # $1M liquide en 5min
    "funding_rate_extreme": 0.001,           # 0.1% (en decimal)
    "volume_spike_ratio": 5.0,               # +500% = ratio 6x

    # Alertes Trading
    "breakout_volume_multiplier": 2.0,       # Volume 2x moyenne
    "long_short_squeeze": 0.85,              # 85% d'un cote
    "price_divergence_binance": 0.02,        # 2% divergence

    # Opportunites Long-Terme
    "volume_growth_days": 7,                 # Croissance sur 7j
    "institutional_wallet_size": 1_000_000,  # $1M+ = institutionnel
}

# Cache pour comparaisons
market_cache = {}
volume_history = defaultdict(list)
price_history = defaultdict(list)
known_markets = set()
alert_cooldown = {}

COOLDOWN_SECONDS = 1800  # 30 min entre alertes meme signal

# Logs
def log(msg: str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def send_telegram(message: str) -> bool:
    """Envoie alerte Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        log(f"❌ Erreur Telegram: {e}")
        return False

def api_request(endpoint_type: str, data: Dict) -> Optional[Dict]:
    """Requete API Hyperliquid generique."""
    try:
        payload = {"type": endpoint_type, **data}
        response = requests.post(HYPERLIQUID_API, json=payload, timeout=15)

        if response.status_code == 429:
            log(f"⚠️ Rate limit atteint, pause 60s...")
            time.sleep(60)
            return None

        if response.status_code != 200:
            log(f"⚠️ Erreur API: {response.status_code}")
            return None

        return response.json()

    except Exception as e:
        log(f"❌ Erreur api_request: {e}")
        return None

def get_all_mids() -> Optional[Dict]:
    """Recupere tous les prix mid actuels (weight: 2)."""
    return api_request("allMids", {})

def get_meta() -> Optional[Dict]:
    """Recupere metadata des marches (symbols, etc) (weight: 20)."""
    return api_request("meta", {})

def get_meta_and_asset_ctxs() -> Optional[Dict]:
    """Recupere metadata + contextes assets (funding, OI, volume) (weight: 20)."""
    return api_request("metaAndAssetCtxs", {})

def get_user_fills(user: str, start_time: int = None) -> Optional[List]:
    """Recupere trades recents d'un user (whale tracking) (weight: 20+)."""
    data = {"user": user}
    if start_time:
        data["startTime"] = start_time
    return api_request("userFills", data)

def get_funding_history(coin: str, start_time: int = None) -> Optional[List]:
    """Recupere historique funding rate (weight: 20+)."""
    data = {"coin": coin}
    if start_time:
        data["startTime"] = start_time
    return api_request("fundingHistory", data)

def get_recent_trades(coin: str) -> Optional[List]:
    """Recupere trades recents pour un marche (weight: 20+)."""
    return api_request("recentTrades", {"coin": coin})

def get_clearinghouse_state(user: str) -> Optional[Dict]:
    """Recupere positions ouvertes d'un user (weight: 2)."""
    return api_request("clearinghouseState", {"user": user})

def check_cooldown(alert_key: str) -> bool:
    """Verifie si alerte en cooldown."""
    now = time.time()
    if alert_key in alert_cooldown:
        elapsed = now - alert_cooldown[alert_key]
        if elapsed < COOLDOWN_SECONDS:
            return False
    alert_cooldown[alert_key] = now
    return True

# ============================================
# DETECTION 1: NOUVEAUX MARCHES PERPETUELS
# ============================================
def detect_new_markets(meta_data: Dict, asset_ctxs: List[Dict]) -> List[Dict]:
    """Detecte nouveaux marches avec volume >$1M en 1h."""
    global known_markets

    opportunities = []

    if not meta_data or not asset_ctxs:
        return opportunities

    universe = meta_data.get("universe", [])

    for i, asset_info in enumerate(universe):
        coin = asset_info.get("name", "")

        # Nouveau marche ?
        if coin not in known_markets:
            known_markets.add(coin)

            # Recuperer contexte (volume, OI, etc)
            if i < len(asset_ctxs):
                ctx = asset_ctxs[i]

                # Extraire volume 24h
                volume_24h = float(ctx.get("dayNtlVlm", 0))  # Volume notionnel USD
                funding = float(ctx.get("funding", 0))
                open_interest = float(ctx.get("openInterest", 0))

                # Check si volume significatif (>$1M sur extrapolation 1h)
                # dayNtlVlm = volume 24h, donc 1h = 1/24
                volume_1h_estimate = volume_24h / 24

                if volume_1h_estimate >= THRESHOLDS["new_market_volume_1h"]:
                    opportunities.append({
                        "type": "NEW_MARKET",
                        "coin": coin,
                        "volume_24h": volume_24h,
                        "volume_1h": volume_1h_estimate,
                        "funding_rate": funding,
                        "open_interest": open_interest,
                    })
                    log(f"🆕 Nouveau marche detecte: {coin} (Vol 1h: ${volume_1h_estimate:,.0f})")

    return opportunities

# ============================================
# DETECTION 2: WHALE ALERTS
# ============================================
def detect_whale_positions(asset_ctxs: List[Dict], universe: List[Dict]) -> List[Dict]:
    """Detecte positions whales >$500k (via Open Interest spike)."""
    opportunities = []

    for i, ctx in enumerate(asset_ctxs):
        if i >= len(universe):
            break

        coin = universe[i].get("name", "")
        open_interest = float(ctx.get("openInterest", 0))  # En tokens
        mark_px = float(ctx.get("markPx", 0))

        # Convertir OI en USD
        oi_usd = open_interest * mark_px

        # Check si spike de OI (nouvelle grosse position)
        if coin in market_cache:
            prev_oi = market_cache[coin].get("open_interest_usd", 0)
            oi_change = oi_usd - prev_oi

            # Grosse position ouverte (>$500k)
            if oi_change >= THRESHOLDS["whale_position_size"]:
                opportunities.append({
                    "type": "WHALE_POSITION",
                    "coin": coin,
                    "oi_change_usd": oi_change,
                    "total_oi_usd": oi_usd,
                    "price": mark_px,
                })
                log(f"🐋 Whale alert: {coin} - Position +${oi_change:,.0f}")

        # Mettre a jour cache
        if coin not in market_cache:
            market_cache[coin] = {}
        market_cache[coin]["open_interest_usd"] = oi_usd
        market_cache[coin]["mark_price"] = mark_px

    return opportunities

# ============================================
# DETECTION 3: LIQUIDATION CASCADE
# ============================================
def detect_liquidations(coin: str, recent_trades: List[Dict]) -> Optional[Dict]:
    """Detecte cascade de liquidations >$1M en 5min."""
    if not recent_trades:
        return None

    now = time.time() * 1000  # ms
    five_min_ago = now - (5 * 60 * 1000)

    liquidation_volume = 0
    liquidation_count = 0

    for trade in recent_trades:
        timestamp = trade.get("time", 0)
        if timestamp < five_min_ago:
            continue

        # Trade de liquidation ?
        side = trade.get("side", "")
        size = float(trade.get("sz", 0))
        price = float(trade.get("px", 0))

        # Liquidations ont flag special (si dispo) ou volume anormalement gros
        # On suppose que gros trades = potentielles liquidations
        trade_value = size * price

        if trade_value >= 50000:  # Trades >$50k = suspects
            liquidation_volume += trade_value
            liquidation_count += 1

    if liquidation_volume >= THRESHOLDS["liquidation_cascade"]:
        return {
            "type": "LIQUIDATION_CASCADE",
            "coin": coin,
            "liquidation_volume": liquidation_volume,
            "liquidation_count": liquidation_count,
        }

    return None

# ============================================
# DETECTION 4: FUNDING RATE EXTREME
# ============================================
def detect_extreme_funding(asset_ctxs: List[Dict], universe: List[Dict]) -> List[Dict]:
    """Detecte funding rates extremes >0.1% (arbitrage opportunity)."""
    opportunities = []

    for i, ctx in enumerate(asset_ctxs):
        if i >= len(universe):
            break

        coin = universe[i].get("name", "")
        funding = float(ctx.get("funding", 0))

        # Funding rate extreme ?
        if abs(funding) >= THRESHOLDS["funding_rate_extreme"]:
            opportunities.append({
                "type": "EXTREME_FUNDING",
                "coin": coin,
                "funding_rate": funding,
                "funding_rate_pct": funding * 100,
                "side": "LONG" if funding > 0 else "SHORT",
            })
            log(f"💰 Funding extreme: {coin} - {funding*100:.2f}%")

    return opportunities

# ============================================
# DETECTION 5: VOLUME SPIKE
# ============================================
def detect_volume_spike(asset_ctxs: List[Dict], universe: List[Dict]) -> List[Dict]:
    """Detecte volume spike +500% vs moyenne."""
    opportunities = []

    for i, ctx in enumerate(asset_ctxs):
        if i >= len(universe):
            break

        coin = universe[i].get("name", "")
        volume_24h = float(ctx.get("dayNtlVlm", 0))

        # Historique volume
        volume_history[coin].append(volume_24h)

        # Garder seulement 7 dernieres valeurs (7 scans)
        if len(volume_history[coin]) > 7:
            volume_history[coin].pop(0)

        # Calculer moyenne (si assez de donnees)
        if len(volume_history[coin]) >= 3:
            avg_volume = sum(volume_history[coin][:-1]) / len(volume_history[coin][:-1])

            # Spike detecte ?
            if avg_volume > 0:
                spike_ratio = volume_24h / avg_volume

                if spike_ratio >= THRESHOLDS["volume_spike_ratio"]:
                    opportunities.append({
                        "type": "VOLUME_SPIKE",
                        "coin": coin,
                        "volume_24h": volume_24h,
                        "avg_volume": avg_volume,
                        "spike_ratio": spike_ratio,
                        "spike_pct": (spike_ratio - 1) * 100,
                    })
                    log(f"📊 Volume spike: {coin} - +{(spike_ratio-1)*100:.0f}%")

    return opportunities

# ============================================
# DETECTION 6: BREAKOUT (Prix + Volume)
# ============================================
def detect_breakout(asset_ctxs: List[Dict], universe: List[Dict], all_mids: Dict) -> List[Dict]:
    """Detecte breakouts: prix casse resistance + volume eleve."""
    opportunities = []

    if not all_mids:
        return opportunities

    for i, ctx in enumerate(asset_ctxs):
        if i >= len(universe):
            break

        coin = universe[i].get("name", "")
        volume_24h = float(ctx.get("dayNtlVlm", 0))

        # Prix actuel
        current_price = float(all_mids.get(coin, 0))
        if current_price == 0:
            continue

        # Historique prix
        price_history[coin].append(current_price)

        if len(price_history[coin]) > 20:
            price_history[coin].pop(0)

        # Check breakout (si assez de donnees)
        if len(price_history[coin]) >= 10:
            recent_high = max(price_history[coin][:-1])
            avg_volume = sum(volume_history[coin]) / len(volume_history[coin]) if volume_history[coin] else 0

            # Breakout = prix actuel > recent high + volume 2x moyenne
            if current_price > recent_high * 1.02 and avg_volume > 0:  # +2% au dessus
                volume_ratio = volume_24h / avg_volume if avg_volume > 0 else 0

                if volume_ratio >= THRESHOLDS["breakout_volume_multiplier"]:
                    opportunities.append({
                        "type": "BREAKOUT",
                        "coin": coin,
                        "price": current_price,
                        "resistance": recent_high,
                        "breakout_pct": ((current_price / recent_high) - 1) * 100,
                        "volume_ratio": volume_ratio,
                    })
                    log(f"🚀 Breakout: {coin} - Prix ${current_price} > ${recent_high}")

    return opportunities

# ============================================
# DETECTION 7: LONG/SHORT SQUEEZE POTENTIAL
# ============================================
def detect_squeeze_potential(asset_ctxs: List[Dict], universe: List[Dict]) -> List[Dict]:
    """Detecte desequilibre Long/Short >85% (squeeze potential)."""
    opportunities = []

    # Note: Hyperliquid ne donne pas directement ratio long/short dans API publique
    # On peut l'estimer via funding rate (funding positif = plus de longs)
    # Alternative: analyser orderbook depth (pas implement ici pour rate limit)

    for i, ctx in enumerate(asset_ctxs):
        if i >= len(universe):
            break

        coin = universe[i].get("name", "")
        funding = float(ctx.get("funding", 0))

        # Funding tres positif = beaucoup de longs (squeeze short potential)
        # Funding tres negatif = beaucoup de shorts (squeeze long potential)

        if funding >= 0.0005:  # 0.05% = tres long-heavy
            opportunities.append({
                "type": "SQUEEZE_POTENTIAL",
                "coin": coin,
                "side": "SHORT_SQUEEZE",
                "funding_rate": funding,
                "funding_pct": funding * 100,
            })
            log(f"⚡ Short squeeze potential: {coin} - Funding {funding*100:.2f}%")

        elif funding <= -0.0005:  # -0.05% = tres short-heavy
            opportunities.append({
                "type": "SQUEEZE_POTENTIAL",
                "coin": coin,
                "side": "LONG_SQUEEZE",
                "funding_rate": funding,
                "funding_pct": funding * 100,
            })
            log(f"⚡ Long squeeze potential: {coin} - Funding {funding*100:.2f}%")

    return opportunities

# ============================================
# GENERATION ALERTES TELEGRAM
# ============================================
def generate_alert_message(opportunity: Dict) -> str:
    """Genere message alerte formaté selon type."""

    opp_type = opportunity["type"]
    coin = opportunity["coin"]

    if opp_type == "NEW_MARKET":
        txt = f"\n🆕 *NOUVEAU MARCHE PERPETUEL*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"📊 Volume 24h: ${opportunity['volume_24h']/1e6:.1f}M\n"
        txt += f"⚡ Volume 1h: ${opportunity['volume_1h']/1e3:.0f}K\n"
        txt += f"💰 Funding: {opportunity['funding_rate']*100:.3f}%\n"
        txt += f"📈 Open Interest: ${opportunity['open_interest']/1e6:.2f}M\n\n"
        txt += f"🔍 *ANALYSE:*\n"
        txt += f"✅ Nouveau marche avec volume immediat!\n"
        txt += f"⚡ Opportunite early entry\n\n"
        txt += f"⚠️ *ACTION:*\n"
        txt += f"👀 Surveiller momentum initial\n"
        txt += f"🎯 Entry si confirmation trend\n"

    elif opp_type == "WHALE_POSITION":
        txt = f"\n🐋 *WHALE ALERT*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"📈 Position ouverte: ${opportunity['oi_change_usd']/1e3:.0f}K\n"
        txt += f"💰 Prix: ${opportunity['price']:.4f}\n"
        txt += f"📊 OI Total: ${opportunity['total_oi_usd']/1e6:.2f}M\n\n"
        txt += f"🔍 *ANALYSE:*\n"
        txt += f"🐋 Grosse position institutionnelle\n"
        txt += f"📈 Potentiel mouvement directionnel\n\n"
        txt += f"⚠️ *ACTION:*\n"
        txt += f"👀 Suivre direction (long ou short)\n"
        txt += f"🎯 Possible trend suiveur\n"

    elif opp_type == "LIQUIDATION_CASCADE":
        txt = f"\n⚡ *LIQUIDATION CASCADE*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"💥 Volume liquide: ${opportunity['liquidation_volume']/1e6:.2f}M\n"
        txt += f"🔄 Nb liquidations: {opportunity['liquidation_count']}\n\n"
        txt += f"🔍 *ANALYSE:*\n"
        txt += f"⚡ Cascade de liquidations massive!\n"
        txt += f"📉 Possible bottom/top local\n\n"
        txt += f"⚠️ *ACTION:*\n"
        txt += f"🎯 Opportunite contre-tendance\n"
        txt += f"⚠️ Attendre stabilisation prix\n"

    elif opp_type == "EXTREME_FUNDING":
        txt = f"\n💰 *FUNDING RATE EXTREME*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"💸 Funding: {opportunity['funding_rate_pct']:.3f}%\n"
        txt += f"📊 Cote dominant: {opportunity['side']}\n\n"
        txt += f"🔍 *ANALYSE:*\n"
        txt += f"💰 Opportunite d'arbitrage!\n"
        txt += f"⚖️ Desequilibre long/short extreme\n\n"
        txt += f"⚠️ *ACTION:*\n"
        if opportunity['side'] == "LONG":
            txt += f"📉 Short + hedge spot = collect funding\n"
        else:
            txt += f"📈 Long + hedge spot = collect funding\n"
        txt += f"🎯 Strategie market neutral\n"

    elif opp_type == "VOLUME_SPIKE":
        txt = f"\n📊 *VOLUME SPIKE*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"🔥 Volume 24h: ${opportunity['volume_24h']/1e6:.2f}M\n"
        txt += f"📈 Moyenne: ${opportunity['avg_volume']/1e6:.2f}M\n"
        txt += f"⚡ Spike: +{opportunity['spike_pct']:.0f}%\n\n"
        txt += f"🔍 *ANALYSE:*\n"
        txt += f"🔥 Activite explosive!\n"
        txt += f"📈 Interet institutionnel potentiel\n\n"
        txt += f"⚠️ *ACTION:*\n"
        txt += f"👀 Confirmer direction trend\n"
        txt += f"🎯 Entry si momentum confirme\n"

    elif opp_type == "BREAKOUT":
        txt = f"\n🚀 *BREAKOUT DETECTE*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"💰 Prix: ${opportunity['price']:.4f}\n"
        txt += f"📊 Resistance: ${opportunity['resistance']:.4f}\n"
        txt += f"⚡ Breakout: +{opportunity['breakout_pct']:.1f}%\n"
        txt += f"📈 Volume ratio: {opportunity['volume_ratio']:.1f}x\n\n"
        txt += f"🔍 *ANALYSE:*\n"
        txt += f"🚀 Prix casse resistance!\n"
        txt += f"📊 Volume confirme le mouvement\n\n"
        txt += f"⚠️ *ACTION:*\n"
        txt += f"✅ Entry possible maintenant\n"
        txt += f"🎯 Stop: resistance (support)\n"
        txt += f"🎯 Target: +20-30% ou prochaine resistance\n"

    elif opp_type == "SQUEEZE_POTENTIAL":
        txt = f"\n⚡ *SQUEEZE POTENTIAL*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"📊 Type: {opportunity['side']}\n"
        txt += f"💸 Funding: {opportunity['funding_pct']:.3f}%\n\n"
        txt += f"🔍 *ANALYSE:*\n"
        if "SHORT" in opportunity['side']:
            txt += f"🟢 Trop de longs - short squeeze risk!\n"
            txt += f"⚡ Possible rallye violent si catalyseur\n"
        else:
            txt += f"🔴 Trop de shorts - long squeeze risk!\n"
            txt += f"⚡ Possible dump violent si catalyseur\n"
        txt += f"\n⚠️ *ACTION:*\n"
        txt += f"👀 Surveiller pour reversal\n"
        txt += f"🎯 Entry si confirmation squeeze\n"

    else:
        txt = f"\n🔔 *ALERTE HYPERLIQUID*\n"
        txt += f"━━━━━━━━━━━━━━━━\n"
        txt += f"💎 {coin}\n"
        txt += f"Type: {opp_type}\n"

    txt += f"\n🔗 https://app.hyperliquid.xyz/trade/{coin}\n"

    return txt

# ============================================
# SCANNER PRINCIPAL
# ============================================
def scan_hyperliquid():
    """Scan principal Hyperliquid."""

    log("=" * 80)
    log("⚡ HYPERLIQUID SCANNER - Detection Opportunites Perpetuels")
    log("=" * 80)

    all_opportunities = []

    # 1. Recuperer metadata + contextes (volume, funding, OI)
    log("📡 Recuperation metadata + asset contexts...")
    meta_data = get_meta()
    meta_and_ctxs = get_meta_and_asset_ctxs()

    if not meta_data or not meta_and_ctxs:
        log("❌ Erreur recuperation donnees de base")
        return

    universe = meta_data.get("universe", [])
    asset_ctxs = meta_and_ctxs[0].get("universe", []) if meta_and_ctxs else []

    log(f"✅ {len(universe)} marches trouves")

    # 2. Recuperer prix
    log("💰 Recuperation prix...")
    all_mids = get_all_mids()

    # 3. Detection nouveaux marches
    log("\n🔍 Detection nouveaux marches...")
    new_markets = detect_new_markets(meta_data, asset_ctxs)
    all_opportunities.extend(new_markets)

    # 4. Detection whale positions
    log("🐋 Detection whale positions...")
    whale_alerts = detect_whale_positions(asset_ctxs, universe)
    all_opportunities.extend(whale_alerts)

    # 5. Detection funding rates extremes
    log("💰 Detection funding rates extremes...")
    extreme_funding = detect_extreme_funding(asset_ctxs, universe)
    all_opportunities.extend(extreme_funding)

    # 6. Detection volume spikes
    log("📊 Detection volume spikes...")
    volume_spikes = detect_volume_spike(asset_ctxs, universe)
    all_opportunities.extend(volume_spikes)

    # 7. Detection breakouts
    log("🚀 Detection breakouts...")
    breakouts = detect_breakout(asset_ctxs, universe, all_mids)
    all_opportunities.extend(breakouts)

    # 8. Detection squeeze potentials
    log("⚡ Detection squeeze potentials...")
    squeezes = detect_squeeze_potential(asset_ctxs, universe)
    all_opportunities.extend(squeezes)

    # 9. Detection liquidations (pour top marches seulement, rate limit)
    log("⚡ Detection liquidations (top 5 marches)...")
    top_coins = sorted(asset_ctxs, key=lambda x: float(x.get("dayNtlVlm", 0)), reverse=True)[:5]

    for i, ctx in enumerate(top_coins):
        if i < len(universe):
            coin = universe[asset_ctxs.index(ctx)].get("name", "")
            recent_trades = get_recent_trades(coin)

            if recent_trades:
                liquidation = detect_liquidations(coin, recent_trades)
                if liquidation:
                    all_opportunities.append(liquidation)

            time.sleep(2)  # Rate limit protection

    # 10. Envoyer alertes
    log(f"\n📊 TOTAL: {len(all_opportunities)} opportunites detectees")

    alerts_sent = 0
    for opp in all_opportunities:
        alert_key = f"{opp['type']}_{opp['coin']}"

        if check_cooldown(alert_key):
            alert_msg = generate_alert_message(opp)

            if send_telegram(alert_msg):
                log(f"✅ Alerte envoyee: {opp['type']} - {opp['coin']}")
                alerts_sent += 1
            else:
                log(f"❌ Echec alerte: {opp['type']} - {opp['coin']}")

            # Limiter a 5 alertes max par scan
            if alerts_sent >= 5:
                log("⚠️ Limite 5 alertes atteinte")
                break

            time.sleep(1)

    log(f"\n✅ Scan termine: {alerts_sent} alertes envoyees")
    log("=" * 80)

def main():
    """Boucle principale."""
    log("🚀 Demarrage Hyperliquid Scanner...")
    log(f"⚡ API: {HYPERLIQUID_API}")
    log(f"📊 Seuils:")
    log(f"   - Nouveau marche: ${THRESHOLDS['new_market_volume_1h']:,} volume 1h")
    log(f"   - Whale position: ${THRESHOLDS['whale_position_size']:,}")
    log(f"   - Liquidation: ${THRESHOLDS['liquidation_cascade']:,} en 5min")
    log(f"   - Funding extreme: {THRESHOLDS['funding_rate_extreme']*100:.2f}%")
    log(f"   - Volume spike: +{(THRESHOLDS['volume_spike_ratio']-1)*100:.0f}%")
    log(f"🔄 Scan toutes les 2 minutes (rate limit: 1200/min)")

    while True:
        try:
            scan_hyperliquid()

            # Attendre 2 minutes avant prochain scan
            log("\n💤 Pause 2 min avant prochain scan...\n")
            time.sleep(120)

        except KeyboardInterrupt:
            log("\n⏹️  Arret du scanner")
            break

        except Exception as e:
            log(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            log("⏳ Pause 60s avant retry...")
            time.sleep(60)

if __name__ == "__main__":
    main()
