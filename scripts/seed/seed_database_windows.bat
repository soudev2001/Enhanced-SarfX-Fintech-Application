@echo off
REM ============================================
REM SarfX - Seeding de la base de données
REM ============================================
echo.
echo ============================================
echo       SarfX Database Initialization
echo ============================================
echo.
echo ============================================
echo    Initialisation Base de Donnees
echo ============================================
echo.

REM Activer le venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERREUR] Environnement virtuel non trouve!
    pause
    exit /b 1
)

echo Choisissez une option:
echo   1. Creer admin seulement
echo   2. Creer admin + utilisateurs demo
echo   3. Creer admin + users + banques
echo   4. Seed complet (tout)
echo   5. Reset et seed complet
echo.
set /p choice="Votre choix (1-5): "

if "%choice%"=="1" goto admin_only
if "%choice%"=="2" goto admin_users
if "%choice%"=="3" goto admin_users_banks
if "%choice%"=="4" goto full_seed
if "%choice%"=="5" goto reset_seed
goto admin_only

:admin_only
echo.
echo Creation de l'admin...
python seed_admin.py
goto end

:admin_users
echo.
echo Creation admin + utilisateurs demo...
python seed_admin.py
python seed_demo_users.py
goto end

:admin_users_banks
echo.
echo Creation admin + users + banques...
python seed_admin.py
python seed_demo_users.py
python seed_banks.py
goto end

:full_seed
echo.
echo Seed complet...
python seed_admin.py
python seed_demo_users.py
python seed_banks.py
python seed_beneficiaries.py
python seed_atm_data.py
goto end

:reset_seed
echo.
echo [ATTENTION] Cette action va supprimer toutes les donnees!
set /p confirm="Confirmez (oui/non): "
if not "%confirm%"=="oui" (
    echo Annule.
    goto end
)
echo.
echo Reset et seed...
if exist "sarfx_local.db" del sarfx_local.db
if exist "instance\sarfx.db" del instance\sarfx.db
python seed_admin.py
python seed_demo_users.py
python seed_banks.py
python seed_beneficiaries.py
python seed_atm_data.py
goto end

:end
echo.
echo ============================================
echo    Seed termine!
echo ============================================
echo.
echo Comptes crees:
echo   Admin: admin@sarfx.io / Admin123!
echo   User:  user@demo.com / Demo123!
echo   Bank:  bank.respo@boa.ma / Bank123!
echo.
pause
