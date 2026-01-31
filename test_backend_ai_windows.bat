@echo off
REM Script de test Backend IA SarfX
REM Windows Batch

echo =========================================
echo   Test Backend IA SarfX v2.0
echo =========================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe
    pause
    exit /b 1
)

echo [INFO] Verification du package requests...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Installation du package requests...
    pip install requests
)

echo.
echo [INFO] Lancement des tests...
echo.

python test_backend_ai.py

echo.
pause
