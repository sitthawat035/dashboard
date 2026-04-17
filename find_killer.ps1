# Find Scheduled Tasks that might be killing processes
Write-Host "=== Scheduled Tasks with Kill/Stop Actions ==="
Get-ScheduledTask | Where-Object { $_.TaskName -like "*kill*" -or $_.TaskName -like "*stop*" -or $_.TaskName -like "*python*" -or $_.TaskName -like "*node*" } | Select-Object TaskName, State

Write-Host ""
Write-Host "=== Recent Process Kills (Event Log) ==="
Get-WinEvent -FilterHashtable @{LogName="Security";ID=4689} -MaxEvents 20 -ErrorAction SilentlyContinue | Where-Object { $_.Message -like "*python.exe*" -or $_.Message -like "*node.exe*" } | Select-Object TimeCreated, Message

Write-Host ""
Write-Host "=== Running Python/Node Processes ==="
Get-Process python*,node* -ErrorAction SilentlyContinue | Select-Object Name, Id, Path
