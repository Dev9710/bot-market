@echo off
REM Dashboard Server Startup Script
REM This script starts the Flask dashboard API server

echo ===================================
echo  Starting Dashboard Server
echo ===================================
echo.

REM Check if Flask is installed
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [!] Flask is not installed!
    echo [i] Installing required packages...
    pip install flask flask-cors
    echo.
)

echo [OK] Starting server on http://localhost:5000
echo.
echo Pages available:
echo   - Dashboard: http://localhost:5000/
echo   - Glossary:  http://localhost:5000/glossary
echo   - Compare:   http://localhost:5000/compare.html
echo.
echo Press CTRL+C to stop the server
echo.
echo ===================================
echo.

python dashboard_api.py
