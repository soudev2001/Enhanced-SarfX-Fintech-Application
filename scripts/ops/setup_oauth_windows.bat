@echo off
REM ============================================
REM SarfX - Google OAuth Windows Setup Script
REM ============================================
REM This script configures Google OAuth credentials and installs dependencies
REM Run: setup_oauth_windows.bat
REM ============================================

echo.
echo ==========================================
echo   SarfX OAuth ^& Production Setup (Windows)
echo ==========================================
echo.

REM Google OAuth Credentials - A CONFIGURER
REM Copiez ces valeurs depuis Google Cloud Console
REM Ou creez un fichier .oauth_credentials.bat avec:
REM   set GOOGLE_CLIENT_ID=votre-client-id
REM   set GOOGLE_CLIENT_SECRET=votre-client-secret

REM Check if credentials file exists
if exist "%~dp0.oauth_credentials.bat" (
    echo [INFO] Loading OAuth credentials from .oauth_credentials.bat
    call "%~dp0.oauth_credentials.bat"
) else (
    echo [WARNING] No .oauth_credentials.bat found!
    echo [WARNING] Please create .oauth_credentials.bat with your Google OAuth credentials
    set GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
    set GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
)
set OAUTH_REDIRECT_URI_LOCAL=http://localhost:5000/auth/login/google/callback

REM Get script directory
set SCRIPT_DIR=%~dp0
set ENV_FILE=%SCRIPT_DIR%.env

echo [Step 1] Installing Python dependencies...
pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo [Step 2] Generating SECRET_KEY...
for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set NEW_SECRET_KEY=%%i
echo [OK] SECRET_KEY generated: %NEW_SECRET_KEY:~0,16%...
echo.

echo [Step 3] Creating/Updating .env file...

REM Check if .env exists
if exist "%ENV_FILE%" (
    echo [INFO] Backing up existing .env to .env.backup
    copy "%ENV_FILE%" "%ENV_FILE%.backup" >nul
)

REM Append OAuth config to .env
echo. >> "%ENV_FILE%"
echo # =========================================== >> "%ENV_FILE%"
echo # GOOGLE OAUTH 2.0 - Auto-configured >> "%ENV_FILE%"
echo # =========================================== >> "%ENV_FILE%"
echo GOOGLE_CLIENT_ID=%GOOGLE_CLIENT_ID% >> "%ENV_FILE%"
echo GOOGLE_CLIENT_SECRET=%GOOGLE_CLIENT_SECRET% >> "%ENV_FILE%"
echo OAUTH_REDIRECT_URI=%OAUTH_REDIRECT_URI_LOCAL% >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # SECRET KEY >> "%ENV_FILE%"
echo SECRET_KEY=%NEW_SECRET_KEY% >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # CACHE (use simple for Windows dev) >> "%ENV_FILE%"
echo CACHE_TYPE=simple >> "%ENV_FILE%"

echo [OK] Google OAuth credentials added to .env
echo.

echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo Configuration Summary:
echo   - Google OAuth: Configured
echo   - SECRET_KEY: Generated
echo   - Dependencies: Installed
echo   - Cache: Simple (Windows dev mode)
echo.
echo Next steps:
echo   1. Run the application:
echo      python run.py
echo.
echo   2. Test Google OAuth:
echo      http://localhost:5000/auth/login
echo.
echo ==========================================
echo.
pause
