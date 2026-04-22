# Check OpenClaw scheduled task details
$taskNames = @("OpenClaw Gateway", "OpenClaw Gateway (2)", "OpenClaw Bot", "OpenClaw Node", "CleanupTemporaryState")

foreach ($name in $taskNames) {
    Write-Host "=== $name ===" -ForegroundColor Cyan
    try {
        $task = Get-ScheduledTask -TaskName $name -ErrorAction Stop
        $taskInfo = $task | Get-ScheduledTaskInfo -ErrorAction Stop
        Write-Host "State: $($taskInfo.State)"
        Write-Host "LastRunTime: $($taskInfo.LastRunTime)"
        Write-Host "LastTaskResult: $($taskInfo.LastTaskResult)"
        Write-Host "Actions:"
        $task.Actions | ForEach-Object {
            Write-Host "  Execute: $($_.Execute)"
            Write-Host "  Arguments: $($_.Arguments)"
            Write-Host "  WorkingDir: $($_.WorkingDirectory)"
        }
    } catch {
        Write-Host "Error: $_"
    }
    Write-Host ""
}