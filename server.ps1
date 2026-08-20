param(
    [ValidateSet("start", "stop", "restart", "status", "run")]
    [string]$Action = "start"
)

$Port = 60001
$HostAddress = "127.0.0.1"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "C:\Python\Python312\python.exe"
$ServerScript = Join-Path $Root "learning_server.py"
$PidFile = Join-Path $Root ".server-60001.pid"
$Url = "http://${HostAddress}:${Port}/index.html"
$Guard = Join-Path $Root "tools\vocab_guard.py"

function Get-PortProcessIds {
    $lines = netstat -ano | Select-String "${HostAddress}:$Port"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split "\s+") | Where-Object { $_ }
        if ($parts.Count -ge 5 -and $parts[3] -eq "LISTENING") {
            [int]$parts[4]
        }
    }
}

function Stop-LearningServer {
    $processIds = @(Get-PortProcessIds | Select-Object -Unique)

    if ($processIds.Count -eq 0) {
        Write-Host "Port $Port is not listening."
        if (Test-Path -LiteralPath $PidFile) {
            Remove-Item -LiteralPath $PidFile -Force
        }
        return
    }

    foreach ($processId in $processIds) {
        try {
            Stop-Process -Id $processId -Force
            Write-Host "Stopped process $processId on port $Port."
        } catch {
            Write-Host "Failed to stop process ${processId}: $($_.Exception.Message)"
        }
    }

    if (Test-Path -LiteralPath $PidFile) {
        Remove-Item -LiteralPath $PidFile -Force
    }
}

function Start-LearningServer {
    if (-not (Test-Path -LiteralPath $Python)) {
        Write-Host "Python was not found at $Python"
        Write-Host "Please edit `$Python in this script or install Python."
        exit 1
    }
    if (Test-Path -LiteralPath (Join-Path $Root ".git")) {
        & git -C $Root config core.hooksPath .githooks 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Host "Warning: could not set Git core.hooksPath." }
    }
    if (-not (Test-Path -LiteralPath $Guard)) {
        Write-Host "Vocabulary guard was not found: $Guard"
        exit 1
    }
    & $Python $Guard check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Vocabulary check failed; refusing to start the server."
        exit 1
    }
    $processIds = @(Get-PortProcessIds | Select-Object -Unique)
    if ($processIds.Count -gt 0) {
        Write-Host "Port $Port is already in use by process: $($processIds -join ', ')"
        Write-Host "URL: $Url"
        return
    }

    if (-not (Test-Path -LiteralPath $ServerScript)) {
        Write-Host "Server script was not found: $ServerScript"
        exit 1
    }

    $arguments = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "`"$PSCommandPath`"",
        "run"
    )

    $process = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList $arguments `
        -WorkingDirectory $Root `
        -WindowStyle Normal `
        -PassThru

    Set-Content -LiteralPath $PidFile -Value $process.Id -Encoding ASCII
    Start-Sleep -Seconds 1

    $startedIds = @(Get-PortProcessIds | Select-Object -Unique)
    if ($startedIds.Count -gt 0) {
        Write-Host "English learning server started."
        Write-Host "Port: $Port"
        Write-Host "Root: $Root"
        Write-Host "URL: $Url"
    } else {
        Write-Host "Server process started, but port $Port is not listening yet."
        Write-Host "Process ID: $($process.Id)"
    }
}

function Show-LearningServerStatus {
    $processIds = @(Get-PortProcessIds | Select-Object -Unique)
    if ($processIds.Count -gt 0) {
        Write-Host "Running on port $Port."
        Write-Host "Process: $($processIds -join ', ')"
        Write-Host "URL: $Url"
    } else {
        Write-Host "Not running on port $Port."
    }
}

function Run-LearningServer {
    if (-not (Test-Path -LiteralPath $Python)) {
        Write-Host "Python was not found at $Python"
        exit 1
    }

    Set-Location -LiteralPath $Root
    & $Python $ServerScript
}

switch ($Action) {
    "start" {
        Start-LearningServer
    }
    "stop" {
        Stop-LearningServer
    }
    "restart" {
        Stop-LearningServer
        Start-LearningServer
    }
    "status" {
        Show-LearningServerStatus
    }
    "run" {
        Run-LearningServer
    }
}
