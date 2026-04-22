$task = Get-ScheduledTask -TaskName 'OpenClaw Node'
$taskInfo = $task | Get-ScheduledTaskInfo
Write-Host "=== Task Info ==="
Write-Host "TaskName: $($taskInfo.TaskName)"
Write-Host "State: $($taskInfo.State)"
Write-Host "LastRunTime: $($taskInfo.LastRunTime)"
Write-Host "LastTaskResult: $($taskInfo.LastTaskResult)"
Write-Host "NumberOfMissedRuns: $($taskInfo.NumberOfMissedRuns)"

Write-Host ""
Write-Host "=== Task Actions ==="
$task.Actions | ForEach-Object {
    Write-Host "Execute: $($_.Execute)"
    Write-Host "Arguments: $($_.Arguments)"
}
