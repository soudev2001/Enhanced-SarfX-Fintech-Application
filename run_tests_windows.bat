@echo off
REM ============================================
REM SarfX - Tests Robot Framework Windows
REM ============================================
echo.
echo  ____             __ __  __
echo / ___|  __ _ _ __/ _^\ ^\ / /
echo \___ \ / _` ^| '__^| ^|_ \ V /
echo  ___) ^| (_^| ^| ^|  ^|  _^| ^| ^|
echo ^|____/ \__,_^|_^|  ^|_^|   ^|_^|
echo.
echo ============================================
echo    Tests Robot Framework
echo ============================================
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

REM Vérifier que Robot est installé
robot --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Robot Framework n'est pas installe!
    echo Installation...
    pip install robotframework robotframework-seleniumlibrary selenium webdriver-manager
)

REM Créer le dossier de résultats
if not exist "robot_results" mkdir robot_results

REM Demander le type de test
echo.
echo Choisissez le type de test:
echo   1. Tests API uniquement (rapide)
echo   2. Tests Selenium (necessite Chrome)
echo   3. Demo complete (video + screenshots)
echo   4. Tous les tests
echo.
set /p choice="Votre choix (1-4): "

if "%choice%"=="1" goto api_tests
if "%choice%"=="2" goto selenium_tests
if "%choice%"=="3" goto demo_tests
if "%choice%"=="4" goto all_tests
goto all_tests

:api_tests
echo.
echo Execution des tests API...
robot --outputdir robot_results --include api robot_tests/tests/
goto end

:selenium_tests
echo.
echo Execution des tests Selenium...
robot --outputdir robot_results --exclude api robot_tests/tests/
goto end

:demo_tests
echo.
echo Execution de la demo complete...
robot --outputdir robot_results/demo ^
    --log demo-log.html ^
    --report demo-report.html ^
    robot_tests/tests/test_full_demo.robot
goto end

:all_tests
echo.
echo Execution de tous les tests...
robot --outputdir robot_results robot_tests/tests/
goto end

:end
echo.
echo ============================================
echo    Tests termines!
echo ============================================
echo.
echo Resultats dans: robot_results\
echo Ouvrez robot_results\report.html pour voir le rapport.
echo.
pause
