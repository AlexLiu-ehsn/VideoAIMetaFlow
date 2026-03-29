# 後端開發伺服器啟動腳本
# 使用方式: .\start.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 確認 .env 存在
if (-not (Test-Path ".env")) {
    Copy-Item "../.env.example" ".env"
    Write-Host "[!] 已建立 .env，請填入 GEMINI_API_KEY 後重新執行" -ForegroundColor Yellow
    exit 1
}

# 啟動虛擬環境
if (-not (Test-Path ".venv")) {
    Write-Host "建立虛擬環境..." -ForegroundColor Cyan
    python -m venv .venv
    .\.venv\Scripts\pip install -e ".[dev]" -q
}

.\.venv\Scripts\Activate.ps1

# 確認 storage 目錄
New-Item -ItemType Directory -Force -Path "storage/videos", "storage/thumbnails" | Out-Null

# 執行 migration
Write-Host "執行 DB migration..." -ForegroundColor Cyan
alembic upgrade head

# 啟動（使用 run.py 確保 ProactorEventLoop 在 uvicorn 建立 event loop 前生效）
Write-Host "後端: http://localhost:8000  |  Docs: http://localhost:8000/docs" -ForegroundColor Green
python run.py
