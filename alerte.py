"""
Lanceur pour tous les bots
- Binance Scanner (tokens etablis CEX)
- GeckoTerminal Scanner V2 (nouveaux tokens DEX - avec améliorations LAVA)

NOUVEAU FORMAT D'ALERTE PEDAGOGIQUE
"""

import threading
import time
from datetime import datetime

# Import des fonctions des bots
import run_binance_bot
import geckoterminal_scanner_v3 as geckoterminal_scanner  # Utilise la V3 avec améliorations backtest


# =========================
# FONCTION ALERTE PEDAGOGIQUE
# =========================

def get_token_info(symbol):
    """Recupere nom complet du token."""
    token_names = {
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'BNB': 'Binance Coin',
        'SOL': 'Solana',
        'XRP': 'Ripple',
        'ADA': 'Cardano',
        'DOGE': 'Dogecoin',
        'AVAX': 'Avalanche',
        'SHIB': 'Shiba Inu',
        'DOT': 'Polkadot',
        'MATIC': 'Polygon',
        'LTC': 'Litecoin',
        'BCH': 'Bitcoin Cash',
        'UNI': 'Uniswap',
        'LINK': 'Chainlink',
        'XLM': 'Stellar',
        'ATOM': 'Cosmos',
        'FIL': 'Filecoin',
        'ENA': 'Ethena',
        'DASH': 'Dash',
        'XMR': 'Monero',
        'ZEC': 'Zcash',
        'AIXBT': 'AIXBT',
        'FDUSD': 'First Digital USD',
        'USD1': 'USD1'
    }

    base_symbol = symbol.replace('USDT', '')
    return token_names.get(base_symbol, base_symbol)


def generer_analyse(anomaly):
    """Genere analyse PEDAGOGIQUE avec emojis - NOUVEAU FORMAT."""
    v = anomaly['volume_data']
    liq = anomaly.get('liquidations')
    oi = anomaly.get('open_interest')

    symbol = anomaly['symbol']
    full_symbol = symbol + 'USDT'
    token_name = get_token_info(full_symbol)

    price = v['price']
    vol_1min = v['current_1min_volume']
    vol_avg = v['avg_1h_volume']
    ratio = v['ratio']
    vol_increase_pct = ((vol_1min - vol_avg) / vol_avg * 100) if vol_avg > 0 else 0
    vol_diff = vol_1min - vol_avg

    # Prix adaptatif (2 decimales pour > $1)
    if price >= 1:
        prix_fmt = f"${price:.2f}"
    elif price >= 0.01:
        prix_fmt = f"${price:.4f}"
    else:
        prix_fmt = f"${price:.6f}"

    txt = f"\n🔥 *{symbol}*"
    if token_name != symbol:
        txt += f" ({token_name})"
    txt += f"\n━━━━━━━━━━━━━━━━\n"
    txt += f"💰 Prix: {prix_fmt}\n"
    txt += f"📊 Vol 1min: ${vol_1min/1000:.0f}K (+{vol_increase_pct:.0f}% vs moy 1h)\n"
    txt += f"📈 Ratio: x{ratio:.1f}\n"

    if oi and oi['open_interest_usd'] > 0:
        txt += f"💼 OI: ${oi['open_interest_usd']/1_000_000:.1f}M (positions futures)\n"

    txt += f"\n🔍 *QUE SE PASSE-T-IL?*\n\n"

    # SECTION VOLUME DETAILLEE
    txt += f"💵 INJECTION DE VOLUME x{ratio:.1f}!\n"
    txt += f"   ↳ Volume normal: ${vol_avg/1000:.0f}K/min\n"
    txt += f"   ↳ Volume actuel: ${vol_1min/1000:.0f}K/min\n"
    txt += f"   ↳ Difference: +${vol_diff/1000:.0f}K en 1 minute!\n"
    txt += f"   ↳ Quelqu'un vient d'acheter MASSIVEMENT\n\n"

    # EXPLICATION POURQUOI VOLUME IMPORTANT
    txt += f"📊 POURQUOI LE VOLUME COMPTE?\n"
    txt += f"   • Volume eleve = Gros acheteurs entrent\n"
    if ratio >= 10:
        txt += f"   • Spike x{ratio:.0f} = Info privilegiee possible\n"
        txt += f"   • Pas un achat retail normal\n"
        txt += f"   • Probable: Institution, whale, ou insider\n\n"
    elif ratio >= 5:
        txt += f"   • Spike x{ratio:.1f} = Activite anormale\n"
        txt += f"   • Acheteurs importants actifs\n\n"

    # LIQUIDATIONS
    if liq and liq['total_liquidated_usd'] > 0:
        total_liq = liq['total_liquidated_usd']
        long_liq = liq['long_liquidated']
        short_liq = liq['short_liquidated']

        txt += f"⚡ LIQUIDATIONS (5 dernieres minutes):\n"
        txt += f"   📉 Shorts liquides: ${short_liq/1000:.0f}K ({short_liq/total_liq*100:.0f}%)\n"
        txt += f"   📈 Longs liquides: ${long_liq/1000:.0f}K ({long_liq/total_liq*100:.0f}%)\n\n"

        # EXPLICATION PEDAGOGIQUE SHORT/LONG SQUEEZE
        if short_liq > long_liq * 3:
            txt += f"🔥 SITUATION: Short Squeeze!\n\n"
            txt += f"   📚 C'EST QUOI?\n"
            txt += f"   • Des traders avaient parie sur la BAISSE (short)\n"
            txt += f"   • Le prix a MONTE au lieu de baisser\n"
            txt += f"   • Leurs positions fermees de FORCE\n"
            txt += f"   • Pour fermer un short = ACHETER le token\n"
            txt += f"   • ${short_liq/1000:.0f}K de shorts obliges d'ACHETER\n\n"
            txt += f"   💡 CONSEQUENCE:\n"
            txt += f"   • Ces achats forces font monter le prix ENCORE PLUS\n"
            txt += f"   • Effet BOULE DE NEIGE!\n"
            txt += f"   • Court terme (30min-2h): Prix continue monter\n\n"

        elif long_liq > short_liq * 3:
            txt += f"🔴 SITUATION: Long Squeeze!\n\n"
            txt += f"   📚 C'EST QUOI?\n"
            txt += f"   • Des traders avaient parie sur la HAUSSE (long)\n"
            txt += f"   • Le prix a BAISSE au lieu de monter\n"
            txt += f"   • Leurs positions fermees de FORCE\n"
            txt += f"   • Pour fermer un long = VENDRE le token\n"
            txt += f"   • ${long_liq/1000:.0f}K de longs obliges de VENDRE\n\n"
            txt += f"   💡 CONSEQUENCE:\n"
            txt += f"   • Ces ventes forcees font baisser le prix ENCORE PLUS\n"
            txt += f"   • Effet DOMINO!\n"
            txt += f"   • Court terme: Prix continue baisser\n\n"

    txt += f"⚡ *ACTION SUGGEREE:*\n"

    # CALCULER STOP LOSS ET TARGETS (TOUJOURS!)
    stop_loss = price * 0.97
    target1 = price * 1.05
    target2 = price * 1.10

    # Format adaptatif pour stop/targets
    if price >= 1:
        sl_fmt = f"${stop_loss:.2f}"
        t1_fmt = f"${target1:.2f}"
        t2_fmt = f"${target2:.2f}"
    elif price >= 0.01:
        sl_fmt = f"${stop_loss:.4f}"
        t1_fmt = f"${target1:.4f}"
        t2_fmt = f"${target2:.4f}"
    else:
        sl_fmt = f"${stop_loss:.6f}"
        t1_fmt = f"${target1:.6f}"
        t2_fmt = f"${target2:.6f}"

    # RECOMMANDATIONS
    if liq and liq['total_liquidated_usd'] > 0:
        total_liq = liq['total_liquidated_usd']
        long_liq = liq['long_liquidated']
        short_liq = liq['short_liquidated']

        if short_liq > long_liq * 3 and total_liq > 1_000_000:
            txt += f"✅ ACHETER position courte (30min-2h)\n"
            txt += f"   💡 Short Squeeze = Prix va monter\n"
            txt += f"🎯 Entree: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"
            txt += f"⚠️ RISQUE ELEVE! Reste vigilant!\n"
        elif long_liq > short_liq * 3 and total_liq > 1_000_000:
            txt += f"❌ NE PAS ACHETER (baisse en cours)\n"
            txt += f"   💡 Long Squeeze = Prix va baisser\n"
            txt += f"⏰ Attends 1-2h que ca se stabilise\n"
        else:
            # Liquidations equilibrees
            txt += f"👀 SURVEILLER de pres\n"
            txt += f"🎯 Entree possible: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"
    else:
        # Pas de liquidations
        if ratio >= 10:
            txt += f"👀 SURVEILLER de pres:\n"
            txt += f"🔎 Cherche news Twitter/Reddit\n"
            txt += f"📊 Surveille 10-20min evolution\n\n"
            txt += f"💰 Si tu achetes:\n"
            txt += f"🎯 Entree: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"
        else:
            txt += f"👀 Surveille evolution\n\n"
            txt += f"💰 Si tu achetes:\n"
            txt += f"🎯 Entree: {prix_fmt}\n"
            txt += f"⛔ Stop Loss: {sl_fmt} (-3%)\n"
            txt += f"🎯 Target 1: {t1_fmt} (+5%)\n"
            txt += f"🎯 Target 2: {t2_fmt} (+10%)\n"

    txt += f"\n📍 Binance: https://binance.com/en/trade/{full_symbol}\n"

    return txt


# =========================
# LANCEUR
# =========================

def log(msg: str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")


def run_binance_scanner():
    """Lance le scanner Binance dans un thread."""
    try:
        log("🔵 Thread Binance Scanner démarré")
        run_binance_bot.boucle()
    except Exception as e:
        log(f"❌ Erreur Binance Scanner: {e}")


def run_gecko_scanner():
    """Lance le scanner GeckoTerminal dans un thread."""
    try:
        log("🦎 Thread GeckoTerminal Scanner démarré")
        geckoterminal_scanner.main()
    except Exception as e:
        log(f"❌ Erreur GeckoTerminal Scanner: {e}")


def main():
    log("=" * 80)
    log("🚀 LANCEMENT DE TOUS LES BOTS")
    log("=" * 80)
    log("")
    log("📊 Bot 1: Binance Scanner (tokens etablis CEX)")
    log("   - DASH, XRP, SOL, etc.")
    log("   - Volume temps reel, liquidations, OI")
    log("")
    log("🦎 Bot 2: GeckoTerminal Scanner V3 (nouveaux tokens DEX)")
    log("   - Nouveaux tokens Ethereum, BSC, Base, Arbitrum, Solana")
    log("   - Detection pumps recents avec liquidite suffisante")
    log("   - Score min 60/100, optimisations backtest 35-50% WR")
    log("")
    log("=" * 80)
    log("")

    # Créer les threads pour chaque bot
    binance_thread = threading.Thread(target=run_binance_scanner, daemon=True, name="BinanceScanner")
    gecko_thread = threading.Thread(target=run_gecko_scanner, daemon=True, name="GeckoScanner")

    # Démarrer les threads
    log("▶️  Demarrage Binance Scanner...")
    binance_thread.start()
    time.sleep(2)

    log("▶️  Demarrage GeckoTerminal Scanner...")
    gecko_thread.start()
    time.sleep(2)

    log("")
    log("✅ Tous les bots sont demarres!")
    log("📡 Appuyez sur Ctrl+C pour arreter tous les bots")
    log("")

    try:
        # Garder le programme actif
        while True:
            # Vérifier si les threads sont toujours vivants
            if not binance_thread.is_alive():
                log("⚠️ Binance Scanner s'est arrete! Redemarrage...")
                binance_thread = threading.Thread(target=run_binance_scanner, daemon=True, name="BinanceScanner")
                binance_thread.start()

            if not gecko_thread.is_alive():
                log("⚠️ GeckoTerminal Scanner s'est arrete! Redemarrage...")
                gecko_thread = threading.Thread(target=run_gecko_scanner, daemon=True, name="GeckoScanner")
                gecko_thread.start()

            time.sleep(30)

    except KeyboardInterrupt:
        log("")
        log("⏹️  Arret de tous les bots...")
        log("👋 Tous les bots sont arretes")


if __name__ == "__main__":
    main()
