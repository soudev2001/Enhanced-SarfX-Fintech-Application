@echo off
REM ============================================
REM SarfX - Demo Robot avec enregistrement
REM ============================================
echo.
echo  ____             __ __  __
echo / ___|  __ _ _ __/ _^\ ^\ / /
echo \___ \ / _` ^| '__^| ^|_ \ V /
echo  ___) ^| (_^| ^| ^|  ^|  _^| ^| ^|
echo ^|____/ \__,_^|_^|  ^|_^|   ^|_^|
echo.
echo ============================================
echo    Demo avec Screenshots
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

REM Créer les dossiers
set DEMO_DIR=robot_results\demo
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%

if not exist "%DEMO_DIR%" mkdir "%DEMO_DIR%"
if not exist "%DEMO_DIR%\screenshots" mkdir "%DEMO_DIR%\screenshots"

echo.
echo Demarrage de la demo...
echo Les screenshots seront sauvegardes dans: %DEMO_DIR%\screenshots
echo.

REM Vérifier ffmpeg pour l'enregistrement vidéo (optionnel)
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [INFO] FFmpeg non trouve - pas d'enregistrement video
    echo Pour installer: https://ffmpeg.org/download.html
    echo.
    set RECORD_VIDEO=0
) else (
    echo [INFO] FFmpeg trouve - enregistrement video active
    set RECORD_VIDEO=1
)

REM Lancer les tests demo
echo.
echo Execution des tests de demonstration...
robot --outputdir %DEMO_DIR% ^
    --variable SCREENSHOT_DIR:%DEMO_DIR%\screenshots ^
    --variable BASE_URL:http://localhost:5000 ^
    --log demo-log-%TIMESTAMP%.html ^
    --report demo-report-%TIMESTAMP%.html ^
    robot_tests/tests/test_full_demo.robot

echo.
echo ============================================
echo    Demo terminee!
echo ============================================
echo.
echo Screenshots: %DEMO_DIR%\screenshots\
echo Rapport: %DEMO_DIR%\demo-report-%TIMESTAMP%.html
echo.

REM Ouvrir le rapport automatiquement
start "" "%DEMO_DIR%\demo-report-%TIMESTAMP%.html"

pause
