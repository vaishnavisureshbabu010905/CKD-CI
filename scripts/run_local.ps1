<#
Run both API and Streamlit locally and capture logs.

Usage:
  powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1

This script will:
- Activate the repo venv if available
- Start the API (uvicorn) in background, logging to `api.log` and `api.err`
- Start Streamlit in background, logging to `streamlit.log` and `streamlit.err`
- Open the dashboard in your default browser

If something fails, paste the contents of `api.log` and `streamlit.log` here.
#>

Set-StrictMode -Version Latest
Push-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)

function Start-ProcLog {
    param(
        [string]$Exe,
        [string]$Args,
        [string]$OutLog,
        [string]$ErrLog
    )
    if (-not (Test-Path $Exe)) {
        Write-Host "Executable not found: $Exe" -ForegroundColor Yellow
        return $null
    }
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Exe
    $startInfo.Arguments = $Args
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $startInfo
    $proc.Start() | Out-Null

    # async copy output to files
    $stdOut = $proc.StandardOutput
    $stdErr = $proc.StandardError

    Start-Job -ScriptBlock {
        param($reader, $path)
        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            Add-Content -Path $path -Value $line
        }
    } -ArgumentList $stdOut, $OutLog | Out-Null

    Start-Job -ScriptBlock {
        param($reader, $path)
        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            Add-Content -Path $path -Value $line
        }
    } -ArgumentList $stdErr, $ErrLog | Out-Null

    return $proc.Id
}

Write-Host "Starting local services and streaming logs to files..."

# determine python executable inside venv if exists
$venvPython = Join-Path -Path (Get-Location) -ChildPath ".venv312\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    # fallback to python on PATH
    $venvPython = "python"
}

# cleanup old logs
Remove-Item -Path api.log, api.err, streamlit.log, streamlit.err -ErrorAction SilentlyContinue

# Start API
$apiArgs = "-m uvicorn main:app --host 127.0.0.1 --port 8000"
$apiPid = Start-ProcLog -Exe $venvPython -Args $apiArgs -OutLog "api.log" -ErrLog "api.err"
if ($apiPid) { Write-Host "API started (pid $apiPid); logs: api.log / api.err" }

# Start Streamlit
$stArgs = "-m streamlit run dashboard.py --server.port 8501"
$stPid = Start-ProcLog -Exe $venvPython -Args $stArgs -OutLog "streamlit.log" -ErrLog "streamlit.err"
if ($stPid) { Write-Host "Streamlit started (pid $stPid); logs: streamlit.log / streamlit.err" }

# Open browser to Streamlit
Start-Sleep -Seconds 2
try { Start-Process "http://localhost:8501" } catch {}

Write-Host "Tailing last 50 lines of api.log and streamlit.log (press Ctrl+C to stop)" -ForegroundColor Green
Write-Host "API log:" -ForegroundColor Cyan
Get-Content api.log -Tail 50 -Wait

Pop-Location
