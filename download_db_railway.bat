@echo off
echo ========================================
echo Telecharger la DB depuis Railway
echo ========================================
echo.

REM Verifier que Railway CLI est installe
railway --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Railway CLI n'est pas installe
    echo.
    echo Installation:
    echo 1. Via npm: npm install -g @railway/cli
    echo 2. Via PowerShell: iwr https://railway.app/install.ps1 ^| iex
    echo.
    pause
    exit /b 1
)

echo Railway CLI detecte ✓
echo.

REM Generer nom de fichier avec date
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%b%%a)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set datetime=%mydate%_%mytime%
set filename=alerts_railway_%datetime%.db

echo Telechargement de la base de donnees...
echo Fichier: %filename%
echo.

railway run cat /data/alerts_history.db > %filename%

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ Telechargement reussi!
    echo ========================================
    echo.
    echo Fichier cree: %filename%
    echo.
    echo Vous pouvez maintenant:
    echo 1. Ouvrir avec DB Browser for SQLite
    echo 2. Consulter avec: python consulter_db.py
    echo.
) else (
    echo.
    echo ========================================
    echo ✗ Erreur lors du telechargement
    echo ========================================
    echo.
    echo Verifications:
    echo 1. Etes-vous connecte? railway login
    echo 2. Le projet est-il lie? railway link
    echo 3. La DB existe-t-elle sur Railway?
    echo.
)

pause