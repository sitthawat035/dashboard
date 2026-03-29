# เปิดไฟล์ profile (ไฟล์นี้จะรันทุกครั้งที่เปิด PowerShell)
# notepad $PROFILE

# ================================
# 🔹 OpenClaw Profile Manager
# ================================

# ตัวแปร global เอาไว้จำว่าเรากำลังใช้ profile ไหนอยู่
$Global:CurrentOCProfile = "None (Default)"

# ================================
# 🔹 ดูสถานะปัจจุบัน
# ================================
function opstatus {

    # แสดงกรอบสวยๆ
    Write-Host "----------------------------------" -ForegroundColor Yellow

    # แสดงชื่อ profile ปัจจุบัน
    Write-Host "Current OpenClaw Profile: " -NoNewline
    Write-Host "$Global:CurrentOCProfile" -ForegroundColor Green

    # แสดง path ที่กำลังใช้จริง
    Write-Host "State Directory: " -NoNewline
    Write-Host "$env:OPENCLAW_STATE_DIR" -ForegroundColor Gray

    Write-Host "----------------------------------" -ForegroundColor Yellow
}

# ================================
# 🔹 Profile 1
# ================================
function op1 {

    # ตั้งค่า state (เลือก “สมอง” ของ agent)
    $env:OPENCLAW_STATE_DIR="C:/Users/User/openclaw/.openclaw"

    # จำว่าใช้ profile ไหน
    $Global:CurrentOCProfile = "Profile 1"

    # เปลี่ยนชื่อ tab/window ให้รู้ว่าเราอยู่ profile ไหน
    $Host.UI.RawUI.WindowTitle = "OpenClaw: Profile 1"

    # แสดงสถานะ
    opstatus
}

# ================================
# 🔹 Profile 2
# ================================
function op2 {
    $env:OPENCLAW_STATE_DIR="C:/Users/User/openclaw/.openclaw-2"
    $Global:CurrentOCProfile = "Profile 2"
    $Host.UI.RawUI.WindowTitle = "OpenClaw: Profile 2"
    opstatus
}

# ================================
# 🔹 Profile 3
# ================================
function op3 {
    $env:OPENCLAW_STATE_DIR="C:/Users/User/openclaw/.openclaw-3"
    $Global:CurrentOCProfile = "Profile 3"
    $Host.UI.RawUI.WindowTitle = "OpenClaw: Profile 3"
    opstatus
}

# ================================
# 🔹 Profile 4
# ================================
function op4 {
    $env:OPENCLAW_STATE_DIR="C:/Users/User/Joepv/.openclaw-4"
    $Global:CurrentOCProfile = "Profile 4"
    $Host.UI.RawUI.WindowTitle = "OpenClaw: Profile 4"
    opstatus
}


# ================================
# 🔹 Profile 5
# ================================
function op5 {
    $env:OPENCLAW_STATE_DIR="C:/Users/User/Joepv/Fah"
    $Global:CurrentOCProfile = "Profile 5"
    $Host.UI.RawUI.WindowTitle = "OpenClaw: Profile 5"
    opstatus
}

# ================================
# 🔹 เปิด Gateway
# ================================
function opgate ($port="10000") {
    $env:Path += ";C:/Users/User/AppData/Roaming/npm"
    Write-Host "Starting Gateway on Port $port using $Global:CurrentOCProfile..." -ForegroundColor Magenta
    openclaw gateway --port $port
}

# ================================
# 🔹 Kill process ที่ใช้ port นั้น (แทน --force บน Windows)
# ================================
function opkill ($port="10000") {
    $pidNum = (netstat -ano | Select-String ":$port\s" | Select-Object -First 1).ToString().Trim().Split()[-1]
    if ($pidNum) {
        Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue
        Write-Host "Killed PID $pidNum on port $port" -ForegroundColor Red
    } else {
        Write-Host "No process found on port $port" -ForegroundColor Yellow
    }
}


# ================================
# 🔹 Reset ทุกอย่าง
# ================================
function opreset {

    # ล้าง state (เหมือน reset สมอง agent)
    $env:OPENCLAW_STATE_DIR = $null

    # reset ตัวแปร tracking
    $Global:CurrentOCProfile = "None (Cleared)"

    # reset ชื่อหน้าต่าง
    $Host.UI.RawUI.WindowTitle = "Windows PowerShell"

    # แจ้งผล
    Write-Host "----------------------------------" -ForegroundColor Red
    Write-Host "OpenClaw Profile has been RESET." -ForegroundColor White
    Write-Host "State Directory is now empty."
    Write-Host "----------------------------------" -ForegroundColor Red
}

function ophelp {
    Clear-Host
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "   OpenClaw Quick Command Menu" -ForegroundColor White -Bold
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  op1, op2, op3, op4, op5  " -NoNewline; Write-Host "-> Switch Profiles" -ForegroundColor Gray
    Write-Host "  opstatus            " -NoNewline; Write-Host "-> Show current active profile" -ForegroundColor Gray
    Write-Host "  opgate [port]       " -NoNewline; Write-Host "-> Start Gateway (Default 8080)" -ForegroundColor Gray
    Write-Host "  opreset             " -NoNewline; Write-Host "-> Clear all OC variables" -ForegroundColor Gray
    Write-Host "  ophelp              " -NoNewline; Write-Host "-> Show this menu" -ForegroundColor Gray
    Write-Host "==========================================" -ForegroundColor Cyan
}

# This makes the menu appear every time you open a new PowerShell window!
ophelp
