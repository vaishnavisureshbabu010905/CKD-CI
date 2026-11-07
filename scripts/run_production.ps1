<#
.SYNOPSIS
    Complete production-ready startup script for CKD-CI system.
    Runs migrations, creates admin, starts API + Streamlit, and monitors health.
    
.USAGE
    powershell -ExecutionPolicy Bypass -File .\scripts\run_production.ps1
#>

param(
    [string]$ApiPort = "8000",
    [string]$StreamlitPort = "8501",
    [switch]$NoStreamlit,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

function Write-Status {
    param([string]$Message, [string]$Type = "info")
    $timestamp = (Get-Date).ToString("HH:mm:ss")
    $prefix = switch ($Type) {
        "success" { "[OK]" }
        "error"   { "[ERROR]" }
        "warn"    { "[WARN]" }
        "info"    { "[INFO]" }
        default   { "[LOG]" }
    }
    Write-Host "[$timestamp] $prefix $Message"
}

function Check-Prerequisite {
    param([string]$Program)
    try {
        if (Get-Command $Program -ErrorAction SilentlyContinue) {
            return $true
        }
    } catch {}
    return $false
}

function Kill-PortProcess {
    param([int]$Port)
    Write-Status "Checking port $Port..." "info"
    try {
        $pids = @(netstat -ano | Select-String ":$Port" | ForEach-Object {
            $parts = ($_ -split '\s+')
            if ($parts.Length -ge 5 -and $parts[3] -eq "LISTENING") { $parts[4] }
        } | Where-Object { $_ -match '^[0-9]+$' -and $_ -ne '0' } | Select-Object -Unique)

        foreach ($pid in $pids) {
            Write-Status "Terminating process $pid on port $Port..." "warn"
            taskkill /PID $pid /F | Out-Null
            Start-Sleep -Milliseconds 300
        }
    } catch {}
}

function Test-ApiHealth {
    param([int]$Port, [int]$MaxAttempts = 30)
    $attempt = 0
    while ($attempt -lt $MaxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {}
        $attempt++
        Start-Sleep -Milliseconds 500
    }
    return $false
}

Write-Output ""
Write-Status "=========================================================" 
Write-Status "CKD-CI Production Startup Script"
Write-Status "Starting API Server & Streamlit Dashboard"
Write-Status "=========================================================" 
Write-Output ""

# 1. Check prerequisites
Write-Status "Step 1: Checking prerequisites..." "info"
if (-not (Check-Prerequisite "python")) {
    Write-Status "Python not found in PATH" "error"
    exit 1
}
Write-Status "Python found" "success"

# 2. Activate venv
Write-Status "Step 2: Activating Python environment..." "info"
$venvPath = ".\env\Scripts\Activate.ps1"
if (-not (Test-Path $venvPath)) {
    $venvPath = ".\.venv\Scripts\Activate.ps1"
}
if (-not (Test-Path $venvPath)) {
    Write-Status "Virtual environment not found at $venvPath" "error"
    exit 1
}
& $venvPath
Write-Status "Virtual environment activated" "success"

# 3. Kill processes on ports
Write-Status "Step 3: Clearing ports..." "info"
Kill-PortProcess -Port $ApiPort
Kill-PortProcess -Port $StreamlitPort
Write-Status "Ports cleared" "success"

# 4. Run migrations
Write-Status "Step 4: Running database migrations..." "info"
$migrationLog = ".\\logs\\migration.log"
$migrationErrLog = ".\\logs\\migration.err.log"
if (-not (Test-Path ".\\logs")) {
    New-Item -ItemType Directory -Path ".\\logs" | Out-Null
}
$migrationProc = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "alembic", "upgrade", "head") `
    -RedirectStandardOutput $migrationLog `
    -RedirectStandardError $migrationErrLog `
    -PassThru `
    -NoNewWindow
$migrationProc.WaitForExit()
if ($Debug -and (Test-Path $migrationLog)) {
    Get-Content $migrationLog | ForEach-Object { Write-Host "  $_" }
}
if ($Debug -and (Test-Path $migrationErrLog)) {
    Get-Content $migrationErrLog | ForEach-Object { Write-Host "  $_" }
}
if ($migrationProc.ExitCode -eq 0) {
    Write-Status "Migrations completed" "success"
} else {
    Write-Status "Migration returned non-zero exit code; continuing" "warn"
    if (Test-Path $migrationLog) {
        Get-Content $migrationLog | ForEach-Object { Write-Host "  $_" }
    }
    if (Test-Path $migrationErrLog) {
        Get-Content $migrationErrLog | ForEach-Object { Write-Host "  $_" }
    }
}

# 5. Create admin user
Write-Status "Step 5: Setting up admin user..." "info"
$env:ADMIN_EMAIL = 'admin@example.com'
$env:ADMIN_PASSWORD = 'change_me'
python scripts/create_admin.py 2>&1 | ForEach-Object { Write-Host "  $_" }
Write-Status "Admin user ready" "success"

# 6. Log file setup
$logDir = ".\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}
$apiLog = ".\logs\api.log"
$apiErrLog = ".\logs\api.err.log"
$streamlitLog = ".\logs\streamlit.log"
$streamlitErrLog = ".\logs\streamlit.err.log"

Write-Status "Step 6: Starting services..." "info"
Write-Output ""

# 7. Start API Server
Write-Status "Starting API Server on http://127.0.0.1:$ApiPort..." "info"
$apiProcess = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", $ApiPort) `
    -RedirectStandardOutput $apiLog `
    -RedirectStandardError $apiErrLog `
    -PassThru `
    -NoNewWindow

Write-Status "API process started (PID: $($apiProcess.Id))" "info"

# 8. Wait for API health
Write-Status "Waiting for API to be ready..." "info"
if (Test-ApiHealth -Port $ApiPort) {
    Write-Status "API is healthy and responding" "success"
} else {
    Write-Status "API health check timed out. Check logs at $apiLog" "error"
    Write-Output "=== API Log ===" 
    Get-Content $apiLog -Tail 20
    exit 1
}

Write-Output ""

# 9. Start Streamlit
if (-not $NoStreamlit) {
    Write-Status "Starting Streamlit Dashboard on http://127.0.0.1:$StreamlitPort..." "info"
    $streamlitProcess = Start-Process -FilePath "python" `
        -ArgumentList @("-m", "streamlit", "run", "dashboard.py", "--server.port", $StreamlitPort, "--logger.level=info") `
        -RedirectStandardOutput $streamlitLog `
        -RedirectStandardError $streamlitErrLog `
        -PassThru `
        -NoNewWindow

    Write-Status "Streamlit process started (PID: $($streamlitProcess.Id))" "info"
    
    Start-Sleep -Seconds 3
    Write-Status "Streamlit is starting (may take 30-60 seconds to be fully ready)" "warn"
}

Write-Output ""
Write-Status "=========================================================" -Type "success"
Write-Status "SYSTEM IS RUNNING" -Type "success"
Write-Status "=========================================================" -Type "success"
Write-Output ""

Write-Status "API Server:      http://127.0.0.1:$ApiPort" "success"
Write-Status "  - Health:      http://127.0.0.1:$ApiPort/health" "info"
Write-Status "  - Docs:        http://127.0.0.1:$ApiPort/docs" "info"
Write-Status "  - Redoc:       http://127.0.0.1:$ApiPort/redoc" "info"

if (-not $NoStreamlit) {
    Write-Status "Streamlit:       http://127.0.0.1:$StreamlitPort" "success"
}

Write-Output ""
Write-Status "Login Credentials:" "info"
Write-Output "  Email: admin@example.com"
Write-Output "  Password: change_me"
Write-Output ""

Write-Status "Log Files:" "info"
Write-Output "  API:       $apiLog"
Write-Output "  API ERR:   $apiErrLog"
Write-Output "  Streamlit: $streamlitLog"
Write-Output "  St ERR:    $streamlitErrLog"
Write-Output ""

Write-Status "To stop services, press Ctrl+C or run:" "warn"
Write-Output "  Stop-Process -Id $($apiProcess.Id)"
if ($streamlitProcess) {
    Write-Output "  Stop-Process -Id $($streamlitProcess.Id)"
}
Write-Output ""

Write-Status "Monitoring processes..." "info"
Write-Output ""

# 10. Monitor processes
try {
    while ($true) {
        if ($apiProcess.HasExited) {
            Write-Status "API Server crashed (exit code: $($apiProcess.ExitCode))" "error"
            Write-Output "=== Last 30 lines of API log ===" 
            Get-Content $apiLog -Tail 30
            break
        }
        
        if ($streamlitProcess -and $streamlitProcess.HasExited) {
            Write-Status "Streamlit crashed (exit code: $($streamlitProcess.ExitCode))" "error"
            Write-Output "=== Last 30 lines of Streamlit log ===" 
            Get-Content $streamlitLog -Tail 30
            break
        }
        
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Status "Cleaning up..." "warn"
    if ($apiProcess -and -not $apiProcess.HasExited) {
        Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($streamlitProcess -and -not $streamlitProcess.HasExited) {
        Stop-Process -Id $streamlitProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Status "Services stopped" "info"
}
