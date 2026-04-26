# Проверка фронта + API после: docker compose up -d
# Запуск: powershell -ExecutionPolicy Bypass -File scripts/verify-stack.ps1
# Опционально: $env:BASE='http://127.0.0.1:8080'

$ErrorActionPreference = 'Stop'
$base = if ($env:BASE) { $env:BASE.TrimEnd('/') } else { 'http://127.0.0.1:8080' }

function Test-Get200 {
    param([string]$Path)
    $u = "$base$Path"
    $r = Invoke-WebRequest -Uri $u -Method GET -UseBasicParsing
    $c = [int]$r.StatusCode
    if ($c -eq 200) {
        Write-Host "OK 200 GET $Path" -ForegroundColor Green
    } else {
        Write-Host "FAIL $Path -> HTTP $c" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Testing $base" -ForegroundColor Cyan
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Test-Get200 '/'
Test-Get200 '/menu'
Test-Get200 '/api/menu/'
Test-Get200 '/ping'
Test-Get200 '/static/favicon-Photoroom.png'
try {
    $r80 = Invoke-WebRequest -Uri 'http://127.0.0.1/' -Method GET -UseBasicParsing -TimeoutSec 3
    if ($r80.StatusCode -eq 200) { Write-Host "OK 200 GET http://127.0.0.1/ (port 80)" -ForegroundColor Green }
} catch {
    Write-Host "Note: port 80 not responding (if you need http://localhost/ without :8080, check docker 80:80 in compose, or port busy)." -ForegroundColor DarkYellow
}
Write-Host "All checks passed." -ForegroundColor Green
