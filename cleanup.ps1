# Nettoyage du projet bot-market
$projectRoot = "c:\Users\ludo_\Documents\projets\owner\bot-market"
Set-Location $projectRoot

# Fichiers a supprimer
$filesToDelete = @(
    "migrate_add_version.py",
    "migrate_add_version_postgresql.py",
    "migrate_railway_api.py",
    "migrate_railway_shell.ps1",
    "GUIDE_UTILISATION_VERSION_DB.md",
    "GUIDE_EXPORT_VOLUME_RAILWAY.md",
    "export_alerts_railway.py",
    "export_db.sh",
    "export_db_base64.py",
    "export_db_sql.sh",
    "export_errors.txt",
    "export_to_csv.py",
    "export_alerts_json.py",
    "railway_export.sh",
    "railway_export.ps1",
    "download_db.sh",
    "alerts_backup.db",
    "alerts_history_railway.db",
    "alerts_railway.db",
    "alerts_encoded.txt",
    "db_dump.sql",
    "db_base64.txt",
    "alerts_data.csv",
    "alerts_export.csv",
    "alerts_export_utf8.csv",
    "backtest_from_csv.py",
    "backtest_network_comparison.py",
    "backtest_analyzer.py",
    "backtest_analyzer_optimized.py",
    "backtest_cache.json",
    "backtest_results.json",
    "advanced_backtest_analysis.py",
    "generate_backtest_pdf.py",
    "test.py",
    "test_arbitrum_filter.py",
    "test_db_schema_regle5.py",
    "test_lp_lock.py",
    "test_network_thresholds.py",
    "test_output.txt",
    "test_platforms.py",
    "test_results.txt",
    "test_tp_logic.py",
    "test_tp_tracking.py",
    "test_tp_tracking_simple.py",
    "test_dashboard_local.bat",
    "simple_test.py",
    "validate_regle5_integration.py",
    "validate_regle5_simple.py",
    "calibrate_thresholds.py",
    "check_network_names.py",
    "check_tokens.py",
    "count_alerts_db.py",
    "serve_csv.py",
    "run_backtest.py",
    "consulter_db.py",
    "5_QUICK_WINS_STRATOSPHERIQUES.md",
    "ACCES_DB_RAILWAY.md",
    "ACCES_DB_RAILWAY_2025.md",
    "ALERTE_V2_MIGRATION.md",
    "ANALYSE_EXPERT_COMPLETE.md",
    "ANALYSE_TIMEFRAME_3H_EXPERT.md",
    "ARRETER_ANCIEN_BOT.md",
    "BUGFIXES_CRITICAL_6.md",
    "CONFIG_BACKTESTING_PHASE.md",
    "FEATURE_PRIX_MAX_TRACKING.md",
    "FIX_COHERENCE_TP.md",
    "FIX_HARMONISATION_TP.md",
    "FIX_PEU_ALERTES.md",
    "FONCTIONNEMENT_SAUVEGARDE.md",
    "GUIDE_DASHBOARD_STREAMLIT.md",
    "GUIDE_DB_BROWSER_SQLITE.md",
    "GUIDE_DEBUTANT_RAILWAY_CLI.md",
    "GUIDE_OFFICIEL_RAILWAY_VOLUMES.md",
    "HOTFIX_NONETYPE_WHALE.md",
    "HOTFIX_UNBOUNDLOCALERROR.md",
    "IMPLEMENTATION_SUMMARY.md",
    "INSTALLATION_RAILWAY_CLI_2025.md",
    "INSTRUCTIONS_BACKTEST.md",
    "INTEGRATION_COMPLETE.md",
    "LP_LOCK_DOCUMENTATION.md",
    "MIGRATION_BINANCE.md",
    "PROCEDURE_ACCES_DB_VOTRE_PROJET.md",
    "QUELLE_VERSION_UTILISER.md",
    "RAILWAY_NOUVELLE_INTERFACE_2025.md",
    "README_FR.md",
    "README_GECKOTERMINAL.md",
    "README_HYPERLIQUID.md",
    "README_RAILWAY.md",
    "RECAP_FINAL_COMPLET.md",
    "RECAP_FINAL_v3.txt",
    "REGLE5_INTEGRATION_COMPLETE.md",
    "REGLE5_RECAP_FINAL.md",
    "REGLE5_VELOCITE_EXEMPLES.md",
    "RESOLUTION_RATE_LIMIT.md",
    "RESUME_DEBUG_SESSION.md",
    "RESUME_FINAL.md",
    "RESUME_FINAL.txt",
    "RESUME_SESSION_2025-12-19.md",
    "RESUME_SESSION_2025-12-20.md",
    "SIMPLIFICATION_V2.md",
    "SUITE_INSTALLATION_RAILWAY.md",
    "SYSTEME_COMPLET.md",
    "TP_TRACKING_IMPLEMENTATION.md",
    "VALIDATION.txt",
    "VERIFICATION_FINALE.md",
    "VERIFICATION_POST_DEPLOY.md",
    "WHALE_DETECTION_FEATURE.md",
    "CHANGELOG_V2.md",
    "COMPLETE_SYSTEM_GUIDE.md",
    "integration_example.py",
    "complete_scanner_system.py",
    "geckoterminal_scanner.py",
    "run_all_bots.py",
    ".env.v3",
    "get_telegram_chat_id.py",
    "monitor_state.json",
    "monitor_state_binance.json",
    "cleanup_project.ps1"
)

Write-Host "Nettoyage du projet..."
$deletedCount = 0
$totalSize = 0

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        $totalSize += $size
        Remove-Item $file -Force
        Write-Host "Supprime: $file"
        $deletedCount++
    }
}

Write-Host ""
Write-Host "TERMINE!"
Write-Host "Fichiers supprimes: $deletedCount"
Write-Host "Espace libere: $([math]::Round($totalSize/1MB, 2)) MB"
Write-Host ""
Write-Host "Fichiers principaux conserves:"
Write-Host "  - alerte.py"
Write-Host "  - geckoterminal_scanner_v3.py"
Write-Host "  - geckoterminal_scanner_v2.py (backup)"
Write-Host "  - alert_tracker.py"
Write-Host "  - README_V3.md"
Write-Host "  - alerts_history.db"
