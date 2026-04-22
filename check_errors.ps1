# Check Windows Error Reporting for Python/Node crashes
Write-Host "=== Recent Windows Error Reports ==="
Get-WinEvent -FilterHashtable @{LogName="Application";StartTime=(Get-Date).AddHours(-3)} -MaxEvents 30 -ErrorAction SilentlyContinue | 
    Where-Object { $_.LevelDisplayName -eq "Error" } |
    Select-Object TimeCreated, ProviderName, Message | Format-List

Write-Host ""
Write-Host "=== Check for Crash Dumps ==="
$crashPaths = @(
    "$env:LOCALAPPDATA\CrashDumps",
    "$env:TEMP",
    "C:\Users\User\Joepv\dashboard"
)
foreach ($path in $crashPaths) {
    if (Test-Path $path) {
        Write-Host "Checking $path..."
        Get-ChildItem $path -Filter "*.dmp" -ErrorAction SilentlyContinue | 
            Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-3) } |
            Select-Object Name, LastWriteTime
    }
}
