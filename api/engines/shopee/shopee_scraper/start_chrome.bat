@echo off
echo.
echo ========================================
echo   เปิด Chrome สำหรับ Data Scraping
echo ========================================
echo.
echo ** สำคัญ: ปิด Chrome ทั้งหมดก่อน! **
echo.
echo กดปุ่มใดๆ เพื่อเปิด Chrome...
pause >nul

set CHROME_PATH=""
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if %CHROME_PATH%=="" (
    echo ERROR: ไม่พบ Chrome!
    pause
    exit /b 1
)

echo เปิด Chrome ด้วย remote debugging (ใช้ profile จริง)...
start "" %CHROME_PATH% --remote-debugging-port=9222

echo.
echo Chrome เปิดแล้ว! ไป login Shopee แล้วรันสคริปต์ scrape ครับ
echo.
pause
