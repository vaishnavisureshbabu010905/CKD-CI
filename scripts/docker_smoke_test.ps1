<#
PowerShell smoke test for CKD-CI Docker Compose stack

Usage:
  1) Start services: docker compose up --build -d
  2) Run this script:
     powershell -ExecutionPolicy Bypass -File .\scripts\docker_smoke_test.ps1

This script checks service readiness, DB tables, API endpoints, prediction flow,
dashboard and monitoring stack. It prints PASS/FAIL per step and exits non-zero
if any critical validation fails.
#>

Set-StrictMode -Version Latest

function Wait-ForHttp {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 90,
        [int]$IntervalSeconds = 3
    )
    $end = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $end) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400) {
                return $true
            }
        } catch {
            # ignore and retry
        }
        Start-Sleep -Seconds $IntervalSeconds
    }
    return $false
}

function Exec-Command {
    param([string]$Cmd)
    try {
        $out = & cmd /c $Cmd 2>&1
        return $out -join "`n"
    } catch {
        return $null
    }
}

function Check-Container-Running {
    param([string]$Name)
    $out = Exec-Command "docker ps --filter \"name=$Name\" --format \"{{.Names}}\""
    if ([string]::IsNullOrWhiteSpace($out)) { return $false }
    return $true
}

function Check-TableExists {
    param([string]$ContainerName, [string]$TableName)
    try {
        $cmd = "docker exec $ContainerName psql -U ckdci -d ckdci -tAc \"SELECT to_regclass('public.$TableName');\""
        $out = Exec-Command $cmd
        if (-not $out) { return $false }
        $val = $out.Trim()
        if ($val -and $val -ne "(0 rows)" -and $val -ne "null") { return $true }
        return $false
    } catch {
        return $false
    }
}

function Http-PostJson {
    param([string]$Url, [hashtable]$Body, [hashtable]$Headers = $null)
    $json = $Body | ConvertTo-Json -Depth 10
    try {
        if ($Headers) {
            return Invoke-RestMethod -Uri $Url -Method Post -Body $json -ContentType 'application/json' -Headers $Headers -ErrorAction Stop
        } else {
            return Invoke-RestMethod -Uri $Url -Method Post -Body $json -ContentType 'application/json' -ErrorAction Stop
        }
    } catch {
        throw $_.Exception
    }
}

# Summary state
$results = @{}
$criticalFail = $false

Write-Host "Starting CKD-CI Docker Compose smoke test..."

# 1) Wait for services
Write-Host "Checking service endpoints (up to 90s)..."
$services = @{
    api = 'http://127.0.0.1:8000/health'
    dashboard = 'http://127.0.0.1:8501'
    prometheus = 'http://127.0.0.1:9090'
    grafana = 'http://127.0.0.1:3000'
}

foreach ($k in $services.Keys) {
    $url = $services[$k]
    Write-Host "Waiting for $k -> $url"
    $ok = Wait-ForHttp -Url $url -TimeoutSeconds 90 -IntervalSeconds 3
    $results["service_$k"] = $ok
    Write-Host "$k : $(if ($ok) { 'PASS' } else { 'FAIL' })"
    if (-not $ok) { $criticalFail = $true }
}

if ($criticalFail) {
    Write-Host "One or more services failed to start. Aborting further checks." -ForegroundColor Red
}

# 2) Verify DB readiness and tables
Write-Host "\nVerifying PostgreSQL container and DB tables..."
$dbContainer = 'ckdci_db'
$dbRunning = Check-Container-Running -Name $dbContainer
$results['db_container_running'] = $dbRunning
Write-Host "Postgres container running: $(if ($dbRunning) { 'PASS' } else { 'FAIL' })"

if ($dbRunning) {
    $tables = @('users','predictions','model_registry')
    foreach ($t in $tables) {
        $exists = Check-TableExists -ContainerName $dbContainer -TableName $t
        $results["table_$t"] = $exists
        Write-Host "Table $t : $(if ($exists) { 'FOUND' } else { 'MISSING' })"
    }
} else {
    foreach ($t in @('users','predictions','model_registry')) { $results["table_$t"] = $false }
    $criticalFail = $true
}

if ($criticalFail) { Write-Host "Critical failures detected; API checks may fail." -ForegroundColor Yellow }

# 3) Verify API endpoints
Write-Host "\nTesting API endpoints..."
$base = 'http://127.0.0.1:8000'

function Safe-Get {
    param([string]$Path)
    try { Invoke-RestMethod -Uri ($base + $Path) -Method Get -TimeoutSec 10 -ErrorAction Stop } catch { return $null }
}

$endpoints = @{
    health = '/health'
    metrics = '/metrics'
    models_active = '/models/active'
    monitoring_drift = '/monitoring/drift'
}

foreach ($k in $endpoints.Keys) {
    $p = $endpoints[$k]
    Write-Host "GET $p ->"
    $resp = Safe-Get -Path $p
    $ok = $false
    if ($resp -ne $null) { $ok = $true }
    $results["api_$k"] = $ok
    Write-Host "  $k : $(if ($ok) { 'PASS' } else { 'FAIL' })"
}

# 4) Smoke prediction flow
Write-Host "\nSmoke prediction flow: login -> predict -> history -> explain"
$loginUrl = "$base/auth/login"
$credentials = @{ email = 'admin@example.com'; password = 'change_me' }
$token = $null
try {
    $loginResp = Http-PostJson -Url $loginUrl -Body $credentials
    if ($loginResp.access_token) {
        $token = $loginResp.access_token
        $results['auth_login'] = $true
        Write-Host "Login: PASS"
    } else {
        $results['auth_login'] = $false
        Write-Host "Login: FAIL" -ForegroundColor Red
    }
} catch {
    $results['auth_login'] = $false
    Write-Host "Login failed: $($_.Exception.Message)" -ForegroundColor Red
}

if ($token) {
    $hdr = @{ Authorization = "Bearer $token" }
    # sample features (must match server schema)
    $sample = @{ patient_identifier = "smoke-001"; features = @{ age=65; gender=1; bmi=27.0; egfr=60.0; creatinine=1.2; bun=20.0; uacr=150.0; hemoglobin=12.5; albumin=3.9; potassium=4.2; phosphorus=3.8; calcium=9.2; systolic_bp=135; diabetes=0; hypertension=1; cvd=0 } }
    try {
        $pred = Http-PostJson -Url "$base/predictions/predict" -Body $sample -Headers $hdr
        $results['predict_call'] = $true
        Write-Host "Predict call: PASS"
        $predictionId = $pred.prediction_id
    } catch {
        $results['predict_call'] = $false
        Write-Host "Predict call failed: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Check history
    try {
        $hist = Invoke-RestMethod -Uri "$base/predictions/history" -Headers $hdr -Method Get -TimeoutSec 10 -ErrorAction Stop
        if ($hist -and $hist.Count -ge 0) {
            $results['history'] = $true
            Write-Host "History: PASS (rows=$($hist.Count))"
        } else {
            $results['history'] = $false
            Write-Host "History: FAIL" -ForegroundColor Yellow
        }
    } catch {
        $results['history'] = $false
        Write-Host "History check failed: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Explain endpoint if predictionId available
    if ($predictionId) {
        try {
            $exp = Invoke-RestMethod -Uri "$base/prediction/explain/$predictionId" -Headers $hdr -Method Get -TimeoutSec 10 -ErrorAction Stop
            $results['explain'] = $true
            Write-Host "Explain: PASS"
        } catch {
            $results['explain'] = $false
            Write-Host "Explain failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        $results['explain'] = $false
        Write-Host "Explain: SKIPPED (no prediction id)"
    }

} else {
    Write-Host "Skipping prediction flow due to failed login." -ForegroundColor Yellow
    $results['predict_call'] = $false
    $results['history'] = $false
    $results['explain'] = $false
    $criticalFail = $true
}

# 5) Dashboard/API connectivity
Write-Host "\nChecking dashboard connectivity..."
$dashOk = Wait-ForHttp -Url 'http://127.0.0.1:8501' -TimeoutSeconds 30 -IntervalSeconds 3
$results['dashboard_http'] = $dashOk
Write-Host "Dashboard HTTP: $(if ($dashOk) { 'PASS' } else { 'FAIL' })"

# 6) Prometheus & Grafana
Write-Host "\nChecking monitoring stack..."
$promOk = Wait-ForHttp -Url 'http://127.0.0.1:9090' -TimeoutSeconds 30 -IntervalSeconds 3
$grafOk = Wait-ForHttp -Url 'http://127.0.0.1:3000' -TimeoutSeconds 30 -IntervalSeconds 3
$results['prometheus'] = $promOk
$results['grafana'] = $grafOk
Write-Host "Prometheus: $(if ($promOk) { 'PASS' } else { 'FAIL' })"
Write-Host "Grafana: $(if ($grafOk) { 'PASS' } else { 'FAIL' })"

# 7) Summary
Write-Host "\nSmoke test summary:" -ForegroundColor Cyan
foreach ($k in $results.Keys) {
    $v = $results[$k]
    Write-Host ("{0,-30} : {1}" -f $k, (if ($v) { 'PASS' } else { 'FAIL' }))
}

if ($criticalFail) {
    Write-Host "\nOne or more critical checks failed." -ForegroundColor Red
    exit 1
} else {
    Write-Host "\nAll critical checks passed." -ForegroundColor Green
    exit 0
}
