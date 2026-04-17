@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo [BAT] Starting Shopee Affiliate Pipeline...

REM Parse command line arguments
set "QUERY=%~1"
set "FILTER=%~2"

REM If filter starts with --, remove the --
if "%FILTER%"=="" goto skip_filter
if "%FILTER:~0,2%"=="--" set "FILTER=%FILTER:~2%"

:skip_filter
REM Create query file if query is provided
if not "%QUERY%"=="" (
    echo [BAT] Query: %QUERY%
    echo [BAT] Filter: %FILTER%
    
    REM Create query JSON file (using Python for proper UTF-8 support)
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2% %dt:~8,2%:%dt:~10,2%:%dt:~12,2%"
    C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe -c "import json; data = {'query': '%QUERY%', 'filter': '%FILTER%', 'timestamp': '%timestamp%'}; f = open(r'c:\\Users\\User\\.openclaw\\workspace\\shopee_affiliate\\data\\00_ScrapedData\\latest_query.json', 'w', encoding='utf-8'); json.dump(data, f, ensure_ascii=False, indent=2); f.close()"
    
    echo [BAT] Query file created: latest_query.json
)

C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe c:\Users\User\.openclaw\workspace\shopee_affiliate\scripts\run_affiliate_pipeline.py > c:\Users\User\.openclaw\workspace\shopee_affiliate\last_run.log 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [BAT] Python script failed with error level %ERRORLEVEL%.
    type c:\Users\User\.openclaw\workspace\shopee_affiliate\last_run.log
    exit /b %ERRORLEVEL%
)
echo [BAT] Success. Output log:
type c:\Users\User\.openclaw\workspace\shopee_affiliate\last_run.log
