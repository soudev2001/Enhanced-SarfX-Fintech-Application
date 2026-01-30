@echo off
REM ============================================
REM Fusion Video + Sous-titres
REM ============================================
echo.
echo ============================================
echo   Fusion Video + Sous-titres
echo ============================================
echo.

if "%1"=="" (
    echo Usage: merge_video_subtitles.bat chemin_video.mp4
    echo.
    echo Exemple:
    echo   merge_video_subtitles.bat robot_results\video_demo\videos\demo_20260129_0700.mp4
    echo.
    pause
    exit /b 1
)

set VIDEO_FILE=%1
set SRT_FILE=%VIDEO_FILE:.mp4=.srt%
set OUTPUT_FILE=%VIDEO_FILE:.mp4=_with_subtitles.mp4%

echo Video: %VIDEO_FILE%
echo Sous-titres: %SRT_FILE%
echo Output: %OUTPUT_FILE%
echo.

REM Vérifier si les fichiers existent
if not exist "%VIDEO_FILE%" (
    echo [ERREUR] Video non trouvee: %VIDEO_FILE%
    pause
    exit /b 1
)

if not exist "%SRT_FILE%" (
    echo [ERREUR] Sous-titres non trouves: %SRT_FILE%
    pause
    exit /b 1
)

echo Fusion en cours...
echo.

REM Fusionner video + sous-titres
ffmpeg -i "%VIDEO_FILE%" -vf "subtitles=%SRT_FILE%:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2,Shadow=1'" -c:a copy "%OUTPUT_FILE%"

if exist "%OUTPUT_FILE%" (
    echo.
    echo ============================================
    echo   Fusion terminee!
    echo ============================================
    echo.
    echo Fichier cree: %OUTPUT_FILE%
    echo.
    echo Voulez-vous lire la video? (O/N^)
    set /p PLAY="Reponse: "
    if /i "%PLAY%"=="O" start "" "%OUTPUT_FILE%"
) else (
    echo.
    echo [ERREUR] Fusion echouee
)

echo.
pause
