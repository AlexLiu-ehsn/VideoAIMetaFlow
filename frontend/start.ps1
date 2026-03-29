# 前端開發伺服器啟動腳本
# 使用方式: .\start.ps1

Set-Location $PSScriptRoot

if (-not (Test-Path "node_modules")) {
    Write-Host "安裝依賴..." -ForegroundColor Cyan
    npm install
}

Write-Host "前端: http://localhost:5173" -ForegroundColor Green
npm run dev
