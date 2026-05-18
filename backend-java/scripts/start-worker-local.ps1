# 本机启动 Python Worker（Redis Stream 消费者，无 Web 端口）
# 用法：在 PowerShell 中执行
#   cd E:\code\watermarking\backend-java\scripts
#   .\start-worker-local.ps1
# 可选：-Python "E:\Conda\envs\myenv39\python.exe"

param(
    [string]$Python = "E:\Conda\envs\myenv39\python.exe",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$DbUser = "root",
    [string]$DbPassword = "123456"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $Python)) {
    Write-Error "Python not found: $Python. Pass -Python with your conda python path."
}

$instance = Join-Path $RepoRoot "instance"
if (-not (Test-Path -LiteralPath $instance)) {
    New-Item -ItemType Directory -Path $instance | Out-Null
}

$env:SQLALCHEMY_DATABASE_URI = "mysql+pymysql://${DbUser}:${DbPassword}@127.0.0.1:3306/watermark?charset=utf8mb4"
$env:WM_REDIS_HOST = "127.0.0.1"
$env:WM_REDIS_PORT = "6379"
$env:WM_STORAGE_BACKEND = "minio"
$env:WM_MINIO_ENDPOINT = "http://127.0.0.1:9000"
$env:WM_MINIO_ACCESS_KEY = "minioadmin"
$env:WM_MINIO_SECRET_KEY = "minioadmin"
$env:WM_MINIO_BUCKET = "watermark"
$env:WM_MINIO_REGION = "us-east-1"
$env:INSTANCE_PATH = $instance

Write-Host "Starting watermark worker (Ctrl+C to stop)..." -ForegroundColor Cyan
Write-Host "  Repo:     $RepoRoot"
Write-Host "  Instance: $instance"
Set-Location $RepoRoot
& $Python -m watermark.worker.redis_stream_worker
