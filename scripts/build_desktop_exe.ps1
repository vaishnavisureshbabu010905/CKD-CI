$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$desktopDir = Join-Path $root "desktop"
$distDir = Join-Path $desktopDir "dist"
$desktopPath = [Environment]::GetFolderPath("Desktop")

Write-Host "Building Electron Windows installer..." -ForegroundColor Cyan
Set-Location $desktopDir
npm run desktop:build

if (-not (Test-Path $distDir)) {
    Write-Host "Build finished but dist folder not found: $distDir" -ForegroundColor Red
    exit 1
}

$installer = Get-ChildItem -Path $distDir -Filter "*.exe" -File |
    Where-Object { $_.Name -notmatch "unins|uninstall" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $installer) {
    Write-Host "No installer exe found in $distDir" -ForegroundColor Red
    exit 1
}

$target = Join-Path $desktopPath $installer.Name
Copy-Item -Path $installer.FullName -Destination $target -Force

Write-Host "Installer copied to Desktop:" -ForegroundColor Green
Write-Host "  $target"
