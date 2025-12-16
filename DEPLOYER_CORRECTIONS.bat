@echo off
echo ========================================
echo Deploiement des Corrections sur Railway
echo ========================================
echo.

echo Etape 1/4: Verification du fichier corrige...
echo.

REM Verifier que le fichier existe
if not exist "geckoterminal_scanner_v2.py" (
    echo ERREUR: geckoterminal_scanner_v2.py introuvable
    pause
    exit /b 1
)

echo Fichier trouve: geckoterminal_scanner_v2.py
echo.

echo Etape 2/4: Ajout des fichiers au commit Git...
echo.

git add geckoterminal_scanner_v2.py
git add ERREURS_COURANTES.md
git add CORRECTIONS_APPLIQUEES.md
git add VERIFICATION_FINALE.md
git add requirements.txt

echo.
echo Etape 3/4: Creation du commit...
echo.

git commit -m "fix: correct pool_data keys integration - resolve KeyError base_token_address"

if %errorlevel% neq 0 (
    echo.
    echo ATTENTION: Aucun changement a commiter OU erreur git
    echo.
    echo Verifications:
    echo 1. Les fichiers ont-ils ete modifies ?
    echo 2. Git est-il configure ?
    echo.
    pause
)

echo.
echo Etape 4/4: Push vers le depot distant...
echo.

git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Code pousse vers GitHub!
    echo ========================================
    echo.
    echo Si Railway est connecte a GitHub:
    echo - Le deploiement automatique va demarrer
    echo - Allez sur https://railway.app/dashboard
    echo - Verifiez l'onglet "Deployments"
    echo - Attendez la fin du build (2-3 min)
    echo.
    echo Si Railway n'est PAS connecte a GitHub:
    echo - Executez: railway login
    echo - Puis: railway up
    echo.
) else (
    echo.
    echo ========================================
    echo ERREUR lors du push
    echo ========================================
    echo.
    echo Verifications:
    echo 1. Etes-vous connecte a GitHub ?
    echo 2. Le depot distant existe-t-il ?
    echo 3. Avez-vous les droits d'ecriture ?
    echo.
)

pause