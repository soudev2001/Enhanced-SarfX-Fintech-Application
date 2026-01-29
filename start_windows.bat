@echo off
REM ============================================
REM SarfX - Demarrage rapide Windows
REM ============================================
echo.
echo  ____             __ __  __
echo / ___|  __ _ _ __/ _^\ ^\ / /
echo \___ \ / _` ^| '__^| ^|_ \ V /
echo  ___) ^| (_^| ^| ^|  ^|  _^| ^| ^|
echo ^|____/ \__,_^|_^|  ^|_^|   ^|_^|
echo.

REM Activer le venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERREUR] Environnement virtuel non trouve!
    echo Executez d'abord: setup_windows.bat
    pause
    exit /b 1
)

REM Vérifier si .env existe
if not exist ".env" (
    echo [ATTENTION] Fichier .env non trouve, utilisation des valeurs par defaut.
)

echo.
echo Demarrage de SarfX sur http://localhost:5000
echo Appuyez sur Ctrl+C pour arreter le serveur.
echo.

REM Lancer Flask
set FLASK_APP=run.py
set FLASK_ENV=development
set FLASK_DEBUG=1
python run.py

pause
