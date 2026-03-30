<#
.SYNOPSIS
    Health check and diagnostic script for CKD-CI system.
    Verifies all components are working correctly.
    
.USAGE
    powershell -ExecutionPolicy Bypass -File .\scripts\health_check.ps1
#>

$ErrorActionPreference = "Continue"

# Color codes
$Green = [char]27 + "[32m"
$Yellow = [char]27 + "[33m"
$Red = [char]27 + "[31m"
$Cyan = [char]27 + "[36m"
$Reset = [char]27 + "[0m"

function Write-Check {
    param([string]$Label, [bool]$Success, [string]$Message = "")
    if ($Success) {
        Write-Host "${Green}✓${Reset} $Label" -NoNewline
    } else {
        Write-Host "${Red}✗${Reset} $Label" -NoNewline
    }
    if ($Message) {
        Write-Host " - $Message"
    } else {
        Write-Host ""
    }
}

Write-Host ""
Write-Host "${Cyan}╔════════════════════════════════════════════════════════════╗${Reset}"
Write-Host "${Cyan}║         CKD-CI Health Check & Diagnostics                 ║${Reset}"
Write-Host "${Cyan}╚════════════════════════════════════════════════════════════╝${Reset}"
Write-Host ""

# 1. Python environment
Write-Host "${Cyan}Python Environment:${Reset}"
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath) {
    Write-Check "Python" $true $pythonPath
    $pythonVersion = python --version 2>&1
    Write-Check "Version" $true $pythonVersion
} else {
    Write-Check "Python" $false "Not found in PATH"
}
Write-Host ""

# 2. Virtual environment
Write-Host "${Cyan}Virtual Environment:${Reset}"
$venvPath = ".\.venv312"
if (Test-Path $venvPath) {
    Write-Check "Venv exists" $true $venvPath
} else {
    Write-Check "Venv exists" $false "Expected at $venvPath"
}
Write-Host ""

# 3. Dependencies
Write-Host "${Cyan}Key Dependencies:${Reset}"
$deps = @("fastapi", "uvicorn", "sqlalchemy", "streamlit", "pydantic", "slowapi")
foreach ($dep in $deps) {
    $installed = python -c "import $dep; print($dep.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Check $dep $true "installed ($installed)"
    } else {
        Write-Check $dep $false "not installed"
    }
}
Write-Host ""

# 4. Database
Write-Host "${Cyan}Database:${Reset}"
$dbCheck = @"
import sys
sys.path.insert(0, '.')
try:
    from db.session import SessionLocal
    from models.user import User
    db = SessionLocal()
    user_count = db.query(User).count()
    print(f"Connected. Users: {user_count}")
    db.close()
except Exception as e:
    print(f"Error: {e}")
"@
$dbResult = python -c $dbCheck 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Check "Database connection" $true $dbResult
} else {
    Write-Check "Database connection" $false $dbResult
}
Write-Host ""

# 5. Model files
Write-Host "${Cyan}Model Files:${Reset}"
$modelFiles = @(
    "main.py",
    "api_server.py",
    "dashboard.py",
    "api/routes/models.py",
    "api/routes/predictions.py",
    "models/model_registry.py"
)
foreach ($file in $modelFiles) {
    $exists = Test-Path $file
    Write-Check $file $exists
}
Write-Host ""

# 6. Logs
Write-Host "${Cyan}Logs:${Reset}"
$logDir = ".\logs"
if (Test-Path $logDir) {
    Write-Check "Log directory" $true $logDir
    Get-ChildItem $logDir -ErrorAction SilentlyContinue | ForEach-Object {
        $size = $_.Length / 1KB
        Write-Host "  - $($_.Name): $('{0:N0}' -f $size) KB"
    }
} else {
    Write-Check "Log directory" $false "Will be created on first run"
}
Write-Host ""

# 7. Ports
Write-Host "${Cyan}Ports:${Reset}"
$port8000Occupied = netstat -ano 2>&1 | Select-String ":8000"
$port8501Occupied = netstat -ano 2>&1 | Select-String ":8501"
Write-Check "Port 8000" (-not $port8000Occupied) $(if ($port8000Occupied) { "In use" } else { "Available" })
Write-Check "Port 8501" (-not $port8501Occupied) $(if ($port8501Occupied) { "In use" } else { "Available" })
Write-Host ""

# 8. API Health (if running)
Write-Host "${Cyan}API Server Health (if running):${Reset}"
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Check "API /health" $true "Responding"
    } else {
        Write-Check "API /health" $false "Status: $($response.StatusCode)"
    }
} catch {
    Write-Check "API /health" $false "Not running"
}
Write-Host ""

Write-Host "${Green}✓ Health check complete${Reset}"
Write-Host ""
Write-Host "To start the full system, run:"
Write-Host "  ${Cyan}powershell -ExecutionPolicy Bypass -File .\scripts\run_production.ps1${Reset}"
Write-Host ""
