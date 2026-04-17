# Check for scheduled tasks that might be killing processes
Write-Host "=== Checking Scheduled Tasks ==="
$tasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "*openclaw*" -or $_.TaskName -like "*kall*" -or $_.TaskName -like "*kill*" -or $_.TaskName -like "*cleanup*" }
if ($tasks) {
    $tasks | Select-Object TaskName, State | Format-Table
} else {
    Write-Host "No matching tasks found"
}

Write-Host ""
Write-Host "=== Check PowerShell Background Jobs ==="
Get-Job -ErrorAction SilentlyContinue | Select-Object Name, State, PSBeginTime | Format-Table

Write-Host ""
Write-Host "=== Recent Security Events (Process Termination) ==="
Get-WinEvent -FilterHashtable @{LogName="Security";ID=4689} -MaxEvents 10 -ErrorAction SilentlyContinue | 
    Select-Object TimeCreated, Message | Format-List