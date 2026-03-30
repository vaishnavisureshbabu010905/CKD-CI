#!/usr/bin/env pwsh
# CKD-CI Quick Start Script
# This script sets up and launches the CKD-CI React Web Application

$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   🏥 CKD-CI Web App Quick Start" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
$nodeVersion = node --version 2>$null
if (-not $nodeVersion) {
    Write-Host "❌ Node.js is not installed!" -ForegroundColor Red
    Write-Host "Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Node.js detected: $nodeVersion" -ForegroundColor Green
Write-Host ""

# Navigate to web-app directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$webAppPath = Join-Path $scriptPath "web-app"

if (-not (Test-Path $webAppPath)) {
    Write-Host "❌ web-app directory not found!" -ForegroundColor Red
    exit 1
}

Set-Location $webAppPath
Write-Host "📁 Changed to: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host ""
}

# Start the app
Write-Host "🚀 Starting CKD-CI React Application..." -ForegroundColor Green
Write-Host ""
Write-Host "The app will open automatically in your browser." -ForegroundColor Cyan
Write-Host "If not, visit: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Default Login:" -ForegroundColor Yellow
Write-Host "  Email: doctor@hospital.com" -ForegroundColor White
Write-Host "  Name: Dr. John Doe" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm start
