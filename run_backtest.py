#!/usr/bin/env python3
"""
Wrapper pour lancer le backtest - À exécuter avec 'railway run python run_backtest.py'
Ou intégrer dans main.py avec variable d'env RUN_BACKTEST=true
"""
import os
import sys

# Ajouter le répertoire courant au path pour importer le module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtest_network_comparison

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 LANCEMENT BACKTEST SUR RAILWAY")
    print("="*80 + "\n")

    backtest_network_comparison.analyze_network_performance()

    print("\n" + "="*80)
    print("✅ BACKTEST TERMINÉ")
    print("="*80 + "\n")
