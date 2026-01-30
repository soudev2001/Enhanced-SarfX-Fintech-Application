@echo off
REM ============================================
REM Installation FFmpeg pour SarfX Video Demo
REM ============================================
echo.
echo ============================================
echo    Installation FFmpeg
echo ============================================
echo.

echo FFmpeg est necessaire pour l'enregistrement video.
echo.
echo Methodes d'installation disponibles:
echo   1. Winget (recommande - automatique)
echo   2. Chocolatey (automatique)
echo   3. Manuel (telechargement depuis ffmpeg.org)
echo.

set /p METHOD="Choisissez une methode (1-3): "

if "%METHOD%"=="1" goto install_winget
if "%METHOD%"=="2" goto install_choco
if "%METHOD%"=="3" goto install_manual
goto install_winget

:install_winget
echo.
echo [WINGET] Installation de FFmpeg...
winget install --id Gyan.FFmpeg -e --silent
if errorlevel 1 (
    echo [ERREUR] Installation echouee
    goto install_choco
)
echo [OK] Installation reussie avec winget!
goto verify

:install_choco
echo.
echo [CHOCOLATEY] Installation de FFmpeg...
choco install ffmpeg -y
if errorlevel 1 (
    echo [ERREUR] Installation echouee
    goto install_manual
)
echo [OK] Installation reussie avec chocolatey!
goto verify

:install_manual
echo.
echo [MANUEL] Telechargez FFmpeg depuis:
echo https://www.gyan.dev/ffmpeg/builds/
echo.
echo 1. Telechargez "ffmpeg-release-essentials.zip"
echo 2. Extraire dans C:\ffmpeg
echo 3. Ajouter C:\ffmpeg\bin au PATH
echo.
echo Voulez-vous ouvrir le site maintenant? (O/N)
set /p OPEN_SITE="Reponse: "
if /i "%OPEN_SITE%"=="O" start https://www.gyan.dev/ffmpeg/builds/
echo.
echo Appuyez sur une touche une fois l'installation terminee...
pause
goto verify

:verify
echo.
echo ============================================
echo    Verification de l'installation
echo ============================================
echo.

REM Rafraichir les variables d'environnement
call refreshenv 2>nul

REM Tester FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] FFmpeg n'est pas trouve dans le PATH
    echo.
    echo Solutions:
    echo   1. Redemarrez votre terminal/PowerShell
    echo   2. Ajoutez manuellement FFmpeg au PATH
    echo   3. Relancez ce script
    echo.
) else (
    echo [OK] FFmpeg est installe!
    ffmpeg -version | findstr "version"
    echo.
    echo ============================================
    echo    Installation reussie!
    echo ============================================
    echo.
    echo Vous pouvez maintenant lancer:
    echo   run_video_demo_windows.bat
    echo.
)

pause
