@echo off
title JOEPV Unified Launcher v3.1 (Silent Mode)
cd /d "%~dp0"

echo  ==============================================
echo   JOEPV SYSTEM v3.1 - Unified Silent Launcher
echo  ==============================================

:: Create logs directory if not exists
if not exist "logs" mkdir "logs"

:: 1. Check & Kill Port 5050 (Joepv Dashboard)
echo [1/3] Clearing Joepv Dashboard on 5050...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5050 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: 2. Check & Kill Port 5000 (MultiContentApp)
echo [2/3] Clearing MultiContentApp on 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 >nul

:: 3. Start Joepv Dashboard Server (Background)
echo [3/3] Starting Dashboard ^& MultiContentApp in Background...
echo       (Logs can be found in /logs directory)

:: Launch Dashboard Server
start /b python server.py > logs\dashboard.log 2>&1

:: Launch MultiContentApp Server
pushd "C:\DriveD_MultiContentApp"
start /b python dashboard/server.py > "%~dp0logs\multicontent.log" 2>&1
popd

echo.
echo [WAIT] Waiting for servers to initialize...
timeout /t 3 >nul

:: Open Browser
echo [OPEN] Launching Command Center...
start http://localhost:5050

echo.
echo  ----------------------------------------------
echo  [-] Dashboard and MultiContent are now running.
echo  [-] Close this window when you're done.
echo  ----------------------------------------------
echo.
pause