@echo off
REM ============================================
REM SarfX - Demo avec Video et Screenshots
REM ============================================
echo.
echo ============================================
echo     SarfX Demo VIDEO + SCREENSHOTS
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
set DEMO_DIR=robot_results\video_demo
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%

if not exist "%DEMO_DIR%" mkdir "%DEMO_DIR%"
if not exist "%DEMO_DIR%\screenshots" mkdir "%DEMO_DIR%\screenshots"
if not exist "%DEMO_DIR%\videos" mkdir "%DEMO_DIR%\videos"

echo.
echo Verification de FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] FFmpeg n'est pas installe!
    echo.
    echo Voulez-vous installer FFmpeg maintenant? (O/N^)
    set /p INSTALL_FFMPEG="Reponse: "

    if /i "%INSTALL_FFMPEG%"=="O" (
        echo Installation de FFmpeg avec winget...
        winget install --id Gyan.FFmpeg -e --silent
        echo.
        echo FFmpeg installe! Relancez ce script.
        pause
        exit /b 0
    ) else (
        echo.
        echo [INFO] Demo sans enregistrement video
        echo.
        set USE_VIDEO=0
    )
) else (
    echo [OK] FFmpeg trouve - Enregistrement video active!
    ffmpeg -version | findstr "version"
    set USE_VIDEO=1
)

echo.
echo ============================================
echo   DEMARRAGE DE LA DEMO AVEC VIDEO
echo ============================================
echo.
echo Mode: Navigateur VISIBLE (pour capture video)
echo Screenshots: %DEMO_DIR%\screenshots
echo Videos: %DEMO_DIR%\videos
echo.

if "%USE_VIDEO%"=="1" (
    echo [VIDEO] L'enregistrement video va demarrer
    echo [VIDEO] Le navigateur Chrome sera visible
    echo.
)

pause

REM Lancer les tests demo avec video
echo.
echo Execution de la demonstration...
echo.

robot --outputdir %DEMO_DIR% ^
    --variable SCREENSHOT_DIR:%DEMO_DIR%\screenshots ^
    --variable VIDEO_DIR:%DEMO_DIR%\videos ^
    --variable BASE_URL:http://localhost:5000 ^
    --variable USE_VIDEO:%USE_VIDEO% ^
    --log video-demo-log-%TIMESTAMP%.html ^
    --report video-demo-report-%TIMESTAMP%.html ^
    --name "SarfX Video Demo Complete" ^
    robot_tests/tests/test_video_demo_complete.robot

echo.
echo ============================================
echo    Demo terminee!
echo ============================================
echo.
echo Screenshots: %DEMO_DIR%\screenshots\
if "%USE_VIDEO%"=="1" (
    echo Videos: %DEMO_DIR%\videos\
)
echo Rapport: %DEMO_DIR%\video-demo-report-%TIMESTAMP%.html
echo.

REM Ouvrir le dossier des résultats
explorer "%DEMO_DIR%"

REM Ouvrir le rapport
start "" "%DEMO_DIR%\video-demo-report-%TIMESTAMP%.html"

pause
