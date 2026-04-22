#!/usr/bin/env pwsh
<#
.SYNOPSIS
Extract Links + Open Chrome (PowerShell Script)

.DESCRIPTION
Runs Chrome on port 9222 and extracts links from captions in one command

.PARAMETER Date
Date folder (YYYY-MM-DD), default: today

.EXAMPLE
.\run_extract_and_chrome.ps1 -Date 2026-02-21
.\run_extract_and_chrome.ps1  # Uses today's date
#>

param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "shopee_affiliate - Extract Links + Open Chrome" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Date: $Date" -ForegroundColor Yellow
Write-Host ""

# Step 1: Open Chrome
Write-Host "[1/2] Opening Chrome on port 9222..." -ForegroundColor Green
Write-Host "      (Running in background)" -ForegroundColor DarkGray
Write-Host ""

$chromePath = "chrome.exe"
if (-not (Get-Command $chromePath -ErrorAction SilentlyContinue)) {
    # Try common Chrome locations
    $possiblePaths = @(
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $chromePath = $path
            break
        }
    }
}

# Start Chrome with debugging port
Start-Process -FilePath $chromePath -ArgumentList "--remote-debugging-port=9222" -WindowStyle Minimized

# Wait for Chrome to start
Write-Host "Waiting for Chrome to start..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3

# Step 2: Extract links
Write-Host ""
Write-Host "[2/2] Extracting links from captions..." -ForegroundColor Green
Write-Host ""

python tools/extract_links_from_captions.py $Date

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Done! Next steps:" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Make sure Chrome is running on port 9222" -ForegroundColor White
Write-Host "2. Login to https://affiliate.shopee.co.th in Chrome" -ForegroundColor White
Write-Host "3. Run: python tools/link_conversion_workflow.py $Date" -ForegroundColor White
Write-Host ""
Write-Host "Or for full automation:" -ForegroundColor Yellow
Write-Host "   python tools/link_conversion_workflow.py $Date" -ForegroundColor Cyan
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor DarkGray
Read-Host
