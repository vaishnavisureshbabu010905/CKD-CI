$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
$venvPy312 = Join-Path $root ".venv312\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPy) { $venvPy } elseif (Test-Path $venvPy312) { $venvPy312 } else { "python" }

$backendDir = $root
$frontendDir = Join-Path $root "frontend"
$desktopDir = Join-Path $root "desktop"

function Test-PortListening {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        return $null -ne $conn
    }
    catch {
        return $false
    }
}

function Wait-UrlReady {
    param(
        [string]$Url,
        [int]$MaxWaitSeconds = 120,
        [int]$PollIntervalSeconds = 2
    )

    $elapsed = 0
    while ($elapsed -lt $MaxWaitSeconds) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
            # Wait for next poll
        }

        Start-Sleep -Seconds $PollIntervalSeconds
        $elapsed += $PollIntervalSeconds
    }

    return $false
}

if (-not (Test-PortListening -Port 8000)) {
    Write-Host "Starting backend API server on port 8000..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendDir'; & '$pythonExe' -m uvicorn main:app --host 0.0.0.0 --port 8000"
}
else {
    Write-Host "Backend already listening on port 8000. Skipping backend start." -ForegroundColor Yellow
}

Write-Host "Waiting for backend health at http://localhost:8000/health ..." -ForegroundColor Yellow
if (-not (Wait-UrlReady -Url "http://localhost:8000/health" -MaxWaitSeconds 120)) {
    Write-Host "Backend did not become ready in time. Aborting desktop launch." -ForegroundColor Red
    exit 1
}

if (-not (Test-PortListening -Port 3000)) {
    Write-Host "Starting frontend dev server on port 3000..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendDir'; npm run dev -- --hostname 0.0.0.0 --port 3000"
}
else {
    Write-Host "Frontend already listening on port 3000. Skipping frontend start." -ForegroundColor Yellow
}

Write-Host "Waiting for frontend readiness at http://localhost:3000 ..." -ForegroundColor Yellow
if (-not (Wait-UrlReady -Url "http://localhost:3000" -MaxWaitSeconds 120)) {
    Write-Host "Frontend was not ready within 120 seconds. Desktop launch aborted." -ForegroundColor Red
    exit 1
}

Write-Host "Frontend ready. Launching Electron desktop..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$desktopDir'; npm run desktop:dev"

Write-Host "Desktop development environment launched." -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Desktop: Electron window"
