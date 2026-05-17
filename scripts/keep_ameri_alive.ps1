# dashboard/scripts/keep_ameri_alive.ps1
# This script ensures Ameri's gateway is running and triggers her daily morning scan if needed.

$AMERI_DIR = "C:\Users\User\openclaw\.openclaw-2"
$LOG_PATH = Join-Path $AMERI_DIR "gateway.log"
$PORT = 18890
$PYTHON_EXE = "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
$BRIDGE_SCRIPT = "C:\Users\User\openclaw\dashboard\api\agent_bridge.py"

function Check-Port($port) {
    return (netstat -ano | Select-String ":$port\s")
}

Write-Host "[Fleet Manager] Checking Ameri status on port $port..." -ForegroundColor Cyan

if (-not (Check-Port $PORT)) {
    Write-Host "[Fleet Manager] Ameri is offline. Restarting gateway..." -ForegroundColor Yellow
    Start-Process -FilePath (Join-Path $AMERI_DIR "gateway.cmd") -WorkingDirectory $AMERI_DIR -WindowStyle Hidden
    Start-Sleep -Seconds 5
} else {
    Write-Host "[Fleet Manager] Ameri is online." -ForegroundColor Green
}

# Optional: Check if daily scan has run
$today = Get-Date -Format "yyyy-MM-dd"
$journal = Get-Content (Join-Path $AMERI_DIR "workspace\AUTO_JOURNAL.md") -Raw
if ($journal -notmatch "$today") {
    Write-Host "[Fleet Manager] No log for today found in Journal. Triggering Trend Scan..." -ForegroundColor Magenta
    & $PYTHON_EXE $BRIDGE_SCRIPT --run trend-scan
} else {
    Write-Host "[Fleet Manager] Ameri has already logged activity for today." -ForegroundColor Cyan
}

Write-Host "[Fleet Manager] Check Complete." -ForegroundColor Green
