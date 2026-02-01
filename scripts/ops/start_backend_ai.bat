@echo off
REM Script de démarrage Backend IA SarfX
REM Windows Batch

echo =========================================
echo   Backend IA SarfX v2.0 - Demarrage
echo =========================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo Installez Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detecte
echo.

REM Se déplacer dans le dossier Backend
cd "SarfX Backend"

echo [INFO] Verification des dependances...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Dependances manquantes
    echo Installation des packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERREUR] Installation echouee
        pause
        exit /b 1
    )
)

echo [OK] Dependances OK
echo.

echo =========================================
echo   Demarrage du serveur sur port 8087
echo =========================================
echo   Swagger Docs: http://localhost:8087/docs
echo   Health Check: http://localhost:8087/
echo.
echo   Appuyez sur Ctrl+C pour arreter
echo =========================================
echo.

REM Démarrer le serveur
python main.py

pause
