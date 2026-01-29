@echo off
REM ============================================
REM SarfX - Script d'installation Windows
REM ============================================
echo.
echo  ____             __ __  __
echo / ___|  __ _ _ __/ _^\ ^\ / /
echo \___ \ / _` ^| '__^| ^|_ \ V /
echo  ___) ^| (_^| ^| ^|  ^|  _^| ^| ^|
echo ^|____/ \__,_^|_^|  ^|_^|   ^|_^|
echo.
echo ============================================
echo    Installation Developpement Local
echo ============================================
echo.

REM Vérifier Python
echo [1/6] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe!
    echo Telechargez Python depuis: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

REM Créer le virtual environment
echo.
echo [2/6] Creation de l'environnement virtuel...
if not exist "venv" (
    python -m venv venv
    echo Environnement virtuel cree!
) else (
    echo Environnement virtuel existe deja.
)

REM Activer le venv
echo.
echo [3/6] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances
echo.
echo [4/6] Installation des dependances Python...
pip install --upgrade pip
pip install -r requirements.txt

REM Installer les dépendances de test (optionnel)
echo.
echo [5/6] Installation des dependances de test...
pip install robotframework robotframework-seleniumlibrary selenium webdriver-manager pytest

REM Créer le fichier .env si nécessaire
echo.
echo [6/6] Configuration de l'environnement...
if not exist ".env" (
    echo Création du fichier .env...
    (
        echo # SarfX Configuration Locale
        echo FLASK_ENV=development
        echo FLASK_DEBUG=1
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo.
        echo # Base de données locale SQLite
        echo DATABASE_URL=sqlite:///sarfx_local.db
        echo.
        echo # API Keys ^(optionnel^)
        echo OPENAI_API_KEY=
        echo EXCHANGE_RATE_API_KEY=
        echo.
        echo # Email ^(optionnel^)
        echo MAIL_SERVER=smtp.gmail.com
        echo MAIL_PORT=587
        echo MAIL_USERNAME=
        echo MAIL_PASSWORD=
    ) > .env
    echo Fichier .env cree! Editez-le avec vos cles API.
) else (
    echo Fichier .env existe deja.
)

echo.
echo ============================================
echo    Installation terminee avec succes!
echo ============================================
echo.
echo Pour demarrer l'application:
echo   1. Activez le venv: venv\Scripts\activate
echo   2. Lancez: python run.py
echo   3. Ouvrez: http://localhost:5000
echo.
echo Pour les tests Robot:
echo   run_tests_windows.bat
echo.
pause
