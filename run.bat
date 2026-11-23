@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM OpenTab - 100% Free & Open-Source Autonomous Personal Assistant Launcher
REM Modeled after Tab (tab.bot)
REM ==============================================================================

cd /d "%~dp0"

echo =====================================================================
echo    OpenTab - Autonomous Agent Launcher (NVIDIA RTX 4050 / Windows)
echo =====================================================================
echo.
echo Choose an option to start:
echo [1] Interactive CLI Mode (Instant terminal chat, tests tools & browser)
echo [2] Start Telegram Bot Gateway (Telegram bot polling)
echo [3] Start WhatsApp Bridge (Launches Node.js QR connector + Python agent)
echo [4] Start All Gateways (Telegram + WhatsApp background daemon)
echo [5] Run Automated Test Suite (Playwright, Tools, Database)
echo [6] Deploy to Fly.io Cloud (24/7 Always-On, Zero GitHub Needed)
echo.

set /p CHOICE="Enter choice (1-6, Default 1): "
if "%CHOICE%"=="" set CHOICE=1

if "%CHOICE%"=="1" (
    echo.
    echo [*] Starting OpenTab CLI Mode...
    "%~dp0.venv\Scripts\python.exe" main.py --mode cli
) else if "%CHOICE%"=="2" (
    echo.
    echo [*] Starting OpenTab Telegram Gateway...
    "%~dp0.venv\Scripts\python.exe" main.py --mode telegram
) else if "%CHOICE%"=="3" (
    echo.
    echo [*] Installing Node dependencies if needed...
    if not exist "%~dp0node_modules" (
        call npm install
    )
    echo [*] Launching WhatsApp Baileys Connector in background...
    start "OpenTab WhatsApp Bridge" cmd /k "npm start"
    echo [*] Launching Python Agent Webhook...
    "%~dp0.venv\Scripts\python.exe" main.py --mode whatsapp
) else if "%CHOICE%"=="4" (
    echo.
    if not exist "%~dp0node_modules" (
        call npm install
    )
    start "OpenTab WhatsApp Bridge" cmd /k "npm start"
    "%~dp0.venv\Scripts\python.exe" main.py --mode all
) else if "%CHOICE%"=="5" (
    echo.
    echo [*] Running Pytest Suite...
    "%~dp0.venv\Scripts\python.exe" -m pytest tests/ -v
) else if "%CHOICE%"=="6" (
    call "%~dp0deploy_fly.bat"
)

pause
