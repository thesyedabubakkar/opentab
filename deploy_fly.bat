@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM OpenTab - 1-Click Fly.io Cloud Deployment (100% Free, Zero GitHub)
REM ==============================================================================

cd /d "%~dp0"
set PATH=%USERPROFILE%\.fly\bin;%PATH%

echo =====================================================================
echo    OpenTab - Fly.io 24/7 Cloud Deployment (No GitHub Required)
echo =====================================================================
echo.

fly.exe version >nul 2>&1
if errorlevel 1 (
    echo [!] Fly CLI not found in PATH. Checking %USERPROFILE%\.fly\bin...
    set FLY_BIN=%USERPROFILE%\.fly\bin\fly.exe
) else (
    set FLY_BIN=fly.exe
)

echo [*] Using Fly CLI: %FLY_BIN%
echo.

echo Step 1: Sign up or Login to Fly.io (Browser will open once)
"%FLY_BIN%" auth whoami >nul 2>&1
if errorlevel 1 (
    echo [*] Not logged in. Opening login page...
    "%FLY_BIN%" auth login
) else (
    echo [+] Already authenticated to Fly.io!
)

echo.
echo Step 2: Deploying OpenTab directly from local folder...
echo (Fly.io will upload local files, build the Docker container, and deploy)
echo.

"%FLY_BIN%" launch --now --copy-config --yes

echo.
echo =====================================================================
echo Optional: Set your secret Bot Tokens on Fly.io
echo =====================================================================
echo You can set your secrets right now (or press Enter to skip if already set):
set /p TG_TOKEN="Enter TELEGRAM_BOT_TOKEN (or press Enter to skip): "
if not "!TG_TOKEN!"=="" (
    "%FLY_BIN%" secrets set TELEGRAM_BOT_TOKEN="!TG_TOKEN!"
)

set /p GROQ_KEY="Enter GROQ_API_KEY (or press Enter to skip): "
if not "!GROQ_KEY!"=="" (
    "%FLY_BIN%" secrets set GROQ_API_KEY="!GROQ_KEY!"
)

echo.
echo =====================================================================
echo [+] OpenTab is now deployed and running 24/7 on Fly.io!
echo     Check status anytime with: fly status
echo     View live logs with:       fly logs
echo =====================================================================
pause
