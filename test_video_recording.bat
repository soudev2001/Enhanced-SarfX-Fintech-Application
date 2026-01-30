@echo off
REM Test rapide de la capture video
echo.
echo ============================================
echo    Test Video (5 secondes)
echo ============================================
echo.

echo Verification FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] FFmpeg non trouve!
    echo Installez-le avec: install_ffmpeg_windows.bat
    pause
    exit /b 1
)

echo [OK] FFmpeg trouve!
echo.
echo Test d'enregistrement (5 secondes)...
echo Votre ecran va etre enregistre maintenant!
echo.

set OUTPUT=test_video_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%.mp4
set OUTPUT=%OUTPUT: =0%

timeout /t 2 /nobreak >nul

echo Enregistrement...
ffmpeg -f gdigrab -framerate 30 -i desktop -t 5 -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p -y %OUTPUT% 2>nul

if exist %OUTPUT% (
    echo.
    echo [OK] Video cree: %OUTPUT%
    echo.
    echo Voulez-vous lire la video? (O/N^)
    set /p PLAY="Reponse: "
    if /i "%PLAY%"=="O" start %OUTPUT%
) else (
    echo [ERREUR] Echec de l'enregistrement
)

echo.
pause
