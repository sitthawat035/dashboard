@echo off
REM Extract Links + Open Chrome (Windows Batch)
REM Usage: run_extract_and_chrome.bat [date]
REM Example: run_extract_and_chrome.bat 2026-02-21

setlocal enabledelayedexpansion

REM Get date parameter or use today
if "%~1"=="" (
    for /f "tokens=1-3 delims=/" %%a in ('date /t') do (
        set "DATE=%%c-%%a-%%b"
    )
) else (
    set "DATE=%~1"
)

echo ============================================================
echo shopee_affiliate - Extract Links + Open Chrome
echo ============================================================
echo.
echo Date: %DATE%
echo.

REM Step 1: Open Chrome with debugging port
echo ^[1/2^] Opening Chrome on port 9222...
echo       This will run in the background
echo.
start chrome.exe --remote-debugging-port=9222

REM Wait a bit for Chrome to start
timeout /t 3 /nobreak

REM Step 2: Extract links
echo.
echo ^[2/2^] Extracting links from captions...
echo.
python tools/extract_links_from_captions.py %DATE%

echo.
echo ============================================================
echo ✅ Done! Next steps:
echo ============================================================
echo.
echo 1. Make sure Chrome is running on port 9222
echo 2. Login to https://affiliate.shopee.co.th in Chrome
echo 3. Run: python tools/link_conversion_workflow.py %DATE%
echo.
echo ============================================================
pause
