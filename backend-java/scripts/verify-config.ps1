# One-shot deploy config check (PowerShell 5.1+ / pwsh). Usage mirrors verify-config.sh.
param(
    [string]$EnvFile = "",
    [string]$ApiUrl = "",
    [switch]$Strict
)

$ErrorActionPreference = "Stop"
$script:Errors = 0
$script:Warnings = 0

function Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow; $script:Warnings++ }
function Fail($msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; $script:Errors++ }

if ($EnvFile) {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        Fail ('Env file not found: {0}' -f $EnvFile)
        exit 1
    }
    Get-Content -LiteralPath $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }
        $i = $line.IndexOf('=')
        if ($i -lt 1) { return }
        $k = $line.Substring(0, $i).Trim()
        $v = $line.Substring($i + 1).Trim()
        [Environment]::SetEnvironmentVariable($k, $v, "Process")
    }
    Ok ('Loaded env file: {0}' -f $EnvFile)
}

function CheckNonempty([string] $name, [string] $val) {
    if ([string]::IsNullOrWhiteSpace($val)) {
        if ($Strict) { Fail ('Missing: {0}' -f $name) } else { Warn ('Unset (optional): {0}' -f $name) }
    }
    else { Ok ('Set: {0}' -f $name) }
}

function Test-Tcp([string] $TargetHost, [int] $TcpPort, [string] $label) {
    if ([string]::IsNullOrWhiteSpace($TargetHost) -or $TcpPort -le 0) {
        Warn ('Skip TCP {0}: invalid host or port' -f $label)
        return
    }
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        try {
            $ias = $c.BeginConnect($TargetHost, $TcpPort, $null, $null)
            if (-not $ias.AsyncWaitHandle.WaitOne(3000, $false)) {
                Fail ('TCP timeout: {0} ({1}:{2})' -f $label, $TargetHost, $TcpPort)
                return
            }
            $c.EndConnect($ias)
            Ok ('TCP ok: {0} ({1}:{2})' -f $label, $TargetHost, $TcpPort)
        }
        finally { $c.Close() }
    }
    catch {
        Fail ('TCP failed: {0} ({1}:{2})' -f $label, $TargetHost, $TcpPort)
    }
}

CheckNonempty "WM_PROFILE" $env:WM_PROFILE
CheckNonempty "WM_DATASOURCE_URL" $env:WM_DATASOURCE_URL
CheckNonempty "WM_DATASOURCE_USERNAME" $env:WM_DATASOURCE_USERNAME
CheckNonempty "WM_DATASOURCE_PASSWORD" $env:WM_DATASOURCE_PASSWORD
CheckNonempty "WM_REDIS_HOST" $(if ($env:WM_REDIS_HOST) { $env:WM_REDIS_HOST } else { "localhost" })
CheckNonempty "WM_REDIS_PORT" $(if ($env:WM_REDIS_PORT) { $env:WM_REDIS_PORT } else { "6379" })
CheckNonempty "WM_INSTANCE_PATH" $env:WM_INSTANCE_PATH

if ($env:WM_STORAGE_BACKEND) {
    Ok ('WM_STORAGE_BACKEND={0}' -f $env:WM_STORAGE_BACKEND)
    $sb = $env:WM_STORAGE_BACKEND.ToLowerInvariant()
    if ($sb -eq "minio") {
        CheckNonempty "WM_MINIO_ENDPOINT" $env:WM_MINIO_ENDPOINT
    }
    elseif ($sb -eq "cos") {
        CheckNonempty "WM_COS_SECRET_ID" $env:WM_COS_SECRET_ID
        CheckNonempty "WM_COS_SECRET_KEY" $env:WM_COS_SECRET_KEY
        CheckNonempty "WM_COS_BUCKET" $env:WM_COS_BUCKET
    }
}
else {
    Warn "WM_STORAGE_BACKEND unset (defaults from application.yml)"
}

if ($env:WM_CORS_ENABLED -and $env:WM_CORS_ENABLED.ToLowerInvariant() -eq "true") {
    CheckNonempty "WM_CORS_ALLOWED_ORIGINS" $env:WM_CORS_ALLOWED_ORIGINS
}

$mysqlHost = $null
$mysqlPort = 3306
$ds = $env:WM_DATASOURCE_URL
if ($ds) {
    if ($ds -match 'jdbc:mysql://([^/]+)/') {
        $hp = $Matches[1]
        if ($hp -match '^([^:]+):(\d+)$') {
            $mysqlHost = $Matches[1]
            $mysqlPort = [int]$($Matches[2])
        }
        else {
            $mysqlHost = $hp
        }
    }
    else {
        Warn "Could not parse WM_DATASOURCE_URL (expect jdbc:mysql://host:port/db)"
    }
}

if ($mysqlHost) { Test-Tcp $mysqlHost $mysqlPort "MySQL" }

$redisHost = if ($env:WM_REDIS_HOST) { $env:WM_REDIS_HOST } else { "localhost" }
$redisPort = if ($env:WM_REDIS_PORT) { [int]$($env:WM_REDIS_PORT) } else { 6379 }
Test-Tcp $redisHost $redisPort "Redis"

$sbLc = if ($env:WM_STORAGE_BACKEND) { $env:WM_STORAGE_BACKEND.ToLowerInvariant() } else { "minio" }
if ($env:WM_MINIO_ENDPOINT -and $sbLc -ne "cos") {
    $me = $env:WM_MINIO_ENDPOINT -replace "^https?://", ""
    $parts = $me -split ":", 2
    if ($parts.Length -eq 2) {
        $mh = $parts[0]
        $mp = ($parts[1] -split "/")[0]
        $pnum = 0
        if ([int]::TryParse($mp, [ref]$pnum)) {
            Test-Tcp $mh $pnum "MinIO(WM_MINIO_ENDPOINT)"
        }
        else { Warn ('Could not parse MinIO port from: {0}' -f $env:WM_MINIO_ENDPOINT) }
    }
    else { Warn ('Could not parse host:port from WM_MINIO_ENDPOINT: {0}' -f $env:WM_MINIO_ENDPOINT) }
}

if (Get-Command redis-cli -ErrorAction SilentlyContinue) {
    $redisArgs = @("-h", $redisHost, "-p", "$redisPort", "ping")
    if ($env:WM_REDIS_PASSWORD) { $redisArgs = @("-h", $redisHost, "-p", "$redisPort", "-a", $env:WM_REDIS_PASSWORD, "ping") }
    $out = & redis-cli @redisArgs 2>$null
    if ($out -match "PONG") { Ok ('Redis PING ok ({0}:{1})' -f $redisHost, $redisPort) }
    else { Fail ('Redis PING failed ({0}:{1})' -f $redisHost, $redisPort) }
}
else {
    Warn "redis-cli not installed; skip Redis PING"
}

if ($ApiUrl) {
    $base = $ApiUrl.TrimEnd('/')
    $uri = $base + '/actuator/health'
    try {
        $resp = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 15
        if ($resp.StatusCode -eq 200) {
            Ok ('HTTP {0}: {1}' -f $resp.StatusCode, $uri)
            $q = [char]34
            if ($resp.Content.Contains(($q + 'status' + $q + ':' + $q + 'UP' + $q))) { Ok 'Health body contains status=UP' }
            else { Warn 'HTTP 200 but UP marker not found; inspect body' }
        }
        else { Fail ('HTTP {0}: {1}' -f $resp.StatusCode, $uri) }
    }
    catch {
        Fail ('Request failed: {0} | {1}' -f $uri, $_.Exception.Message)
    }
}

Write-Host ""
if ($script:Errors -eq 0) {
    Write-Host ('Done: no blocking errors (warnings: {0})' -f $script:Warnings) -ForegroundColor Green
    exit 0
}
else {
    Write-Host ('Done: {0} error(s), warnings: {1}' -f $script:Errors, $script:Warnings) -ForegroundColor Red
    exit 1
}
