@echo off
echo ================================================================================
echo    DEMARRAGE DASHBOARD - Mode Local
echo ================================================================================
echo.

echo [1/3] Verification des dependances...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo    Installation Flask...
    pip install flask flask-cors
)
echo    OK - Flask installe
echo.

echo [2/3] Lancement de l'API...
echo    Port: 5000
echo    DB: alerts_history.db (ou alerts_tracker.db)
echo.
start "API Dashboard" cmd /k "python railway_db_api.py"
timeout /t 3 >nul

echo [3/3] Ouverture du dashboard...
echo    URL API: http://localhost:5000
echo.
start dashboard_frontend.html

echo.
echo ================================================================================
echo    Dashboard lance!
echo ================================================================================
echo.
echo    API:       http://localhost:5000/api/health
echo    Dashboard: Ouvert dans le navigateur
echo.
echo    Appuyez sur une touche pour arreter...
pause >nul
