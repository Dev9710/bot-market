"""
Lanceur pour tous les bots
- Binance Scanner (tokens etablis CEX)
- GeckoTerminal Scanner (nouveaux tokens DEX)
"""

import subprocess
import sys
import time
from datetime import datetime


def log(msg: str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")


def main():
    log("=" * 80)
    log("🚀 LANCEMENT DE TOUS LES BOTS")
    log("=" * 80)
    log("")
    log("📊 Bot 1: Binance Scanner (tokens etablis CEX)")
    log("   - DASH, XRP, SOL, etc.")
    log("   - Volume temps reel, liquidations, OI")
    log("")
    log("🦎 Bot 2: GeckoTerminal Scanner (nouveaux tokens DEX)")
    log("   - Nouveaux tokens Ethereum, BSC, Base, Arbitrum, Solana")
    log("   - Detection pumps recents avec liquidite suffisante")
    log("")
    log("=" * 80)
    log("")

    processes = []

    try:
        # Lancer Binance Scanner
        log("▶️  Demarrage Binance Scanner...")
        binance_process = subprocess.Popen(
            [sys.executable, "run_binance_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("Binance", binance_process))
        time.sleep(2)

        # Lancer GeckoTerminal Scanner
        log("▶️  Demarrage GeckoTerminal Scanner...")
        gecko_process = subprocess.Popen(
            [sys.executable, "geckoterminal_scanner.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("GeckoTerminal", gecko_process))
        time.sleep(2)

        log("")
        log("✅ Tous les bots sont demarres!")
        log("📡 Appuyez sur Ctrl+C pour arreter tous les bots")
        log("")

        # Surveiller les processus
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    log(f"⚠️ {name} s'est arrete! Code: {proc.returncode}")
                    log(f"🔄 Redemarrage {name}...")

                    if name == "Binance":
                        new_proc = subprocess.Popen(
                            [sys.executable, "run_binance_bot.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1
                        )
                    else:  # GeckoTerminal
                        new_proc = subprocess.Popen(
                            [sys.executable, "geckoterminal_scanner.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1
                        )

                    # Remplacer le processus dans la liste
                    processes = [(n, p if n != name else new_proc)
                                 for n, p in processes]
                    log(f"✅ {name} redemarre")

            time.sleep(10)

    except KeyboardInterrupt:
        log("")
        log("⏹️  Arret de tous les bots...")

        for name, proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                log(f"✅ {name} arrete")
            except:
                proc.kill()
                log(f"❌ {name} force d'arreter")

        log("")
        log("👋 Tous les bots sont arretes")


if __name__ == "__main__":
    main()
