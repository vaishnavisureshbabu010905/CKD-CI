#!/usr/bin/env pwsh
param(
    [ValidateSet('menu','quick','full','advanced','dashboard','api','all')]
    [string]$Mode = 'menu'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pythonExe = Join-Path $root 'env\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
    $pythonExe = Join-Path $root '.venv\Scripts\python.exe'
}
if (-not (Test-Path $pythonExe)) {
    $pythonExe = 'python'
}

function Invoke-Step {
    param(
        [string]$Title,
        [string]$Script
    )
    Write-Host "`n[RUN] $Title" -ForegroundColor Cyan
    & $pythonExe $Script
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAILED] $Title" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

function Invoke-Dashboard {
    Write-Host "`n[RUN] Streamlit dashboard" -ForegroundColor Cyan
    & $pythonExe -m streamlit run dashboard.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAILED] Dashboard launch" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

function Invoke-ApiServer {
    Write-Host "`n[RUN] FastAPI server" -ForegroundColor Cyan
    & $pythonExe -m uvicorn main:app --host 0.0.0.0 --port 8000
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAILED] API server launch" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

function Invoke-Mode {
    param([string]$Selected)

    switch ($Selected) {
        'quick' {
            Invoke-Step -Title 'quick_test.py' -Script 'quick_test.py'
        }
        'full' {
            Invoke-Step -Title 'run_complete_pipeline.py' -Script 'run_complete_pipeline.py'
        }
        'advanced' {
            Invoke-Step -Title 'run_advanced_models.py' -Script 'run_advanced_models.py'
        }
        'dashboard' {
            Invoke-Dashboard
        }
        'api' {
            Invoke-ApiServer
        }
        'all' {
            Invoke-Step -Title 'quick_test.py' -Script 'quick_test.py'
            Invoke-Step -Title 'run_complete_pipeline.py' -Script 'run_complete_pipeline.py'
            Invoke-Step -Title 'run_advanced_models.py' -Script 'run_advanced_models.py'
        }
        default {
            Write-Host "Unknown mode: $Selected" -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "`n[SUCCESS] Mode '$Selected' completed." -ForegroundColor Green
}

if ($Mode -eq 'menu') {
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host " CKD-CI PowerShell Runner" -ForegroundColor Cyan
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "1) quick_test.py"
    Write-Host "2) run_complete_pipeline.py"
    Write-Host "3) run_advanced_models.py"
    Write-Host "4) dashboard (streamlit UI)"
    Write-Host "5) api (FastAPI service)"
    Write-Host "6) all (quick + full + advanced)"
    Write-Host "7) exit"

    $choice = Read-Host "Enter choice (1-7)"
    switch ($choice) {
        '1' { Invoke-Mode -Selected 'quick' }
        '2' { Invoke-Mode -Selected 'full' }
        '3' { Invoke-Mode -Selected 'advanced' }
        '4' { Invoke-Mode -Selected 'dashboard' }
        '5' { Invoke-Mode -Selected 'api' }
        '6' { Invoke-Mode -Selected 'all' }
        '7' { exit 0 }
        default {
            Write-Host "Invalid selection." -ForegroundColor Red
            exit 1
        }
    }
} else {
    Invoke-Mode -Selected $Mode
}
