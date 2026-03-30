@echo off
REM CKD-CI Quick Start Script for Windows Command Prompt
REM This script sets up and launches the CKD-CI React Web Application

echo.
echo ========================================
echo    CKD-CI Web App Quick Start
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [FAILED] Node.js is not installed!
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js detected: %NODE_VERSION%
echo.

REM Navigate to web-app directory
cd /d "%~dp0web-app"
if errorlevel 1 (
    echo [FAILED] web-app directory not found!
    pause
    exit /b 1
)

echo [INFO] Current directory: %CD%
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    call npm install
    echo.
)

REM Start the app
echo [INFO] Starting CKD-CI React Application...
echo.
echo The app will open automatically in your browser.
echo If not, visit: http://localhost:3000
echo.
echo Default Login:
echo   Email: doctor@hospital.com
echo   Name: Dr. John Doe
echo.
echo Press Ctrl+C to stop the server
echo.

call npm start
pause
