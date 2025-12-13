@echo off
echo ========================================
echo Test Dashboard Streamlit - Local
echo ========================================
echo.

REM Vérifier que streamlit est installé
python -c "import streamlit" 2>nul
if %errorlevel% neq 0 (
    echo ERREUR: Streamlit n'est pas installe
    echo.
    echo Installation en cours...
    pip install streamlit plotly pandas
    echo.
)

echo Demarrage du dashboard...
echo.
echo Le dashboard sera accessible sur: http://localhost:8501
echo.
echo Appuyez sur Ctrl+C pour arreter
echo.

streamlit run dashboard.py

pause