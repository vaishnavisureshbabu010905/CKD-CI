$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Starting CKD-CI backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; & 'c:/Users/hp/OneDrive/Documents/Downloads/CKD-CI (2)/CKD-CI/.venv/Scripts/python.exe' -m uvicorn main:app --host 0.0.0.0 --port 8000"

Write-Host "Starting CKD-CI frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root/frontend'; npm run dev -- --hostname 0.0.0.0 --port 3000"

Write-Host "Starting CKD-CI desktop wrapper..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root/desktop'; npm run desktop:dev"

Write-Host "All services launched in separate terminals." -ForegroundColor Green
Write-Host "API: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Desktop: Electron window"
