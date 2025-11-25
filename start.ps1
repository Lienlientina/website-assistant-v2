# 快速啟動腳本 - Windows PowerShell

Write-Host "=== AI Website Assistant 啟動 ===" -ForegroundColor Cyan
Write-Host ""

# 檢查是否安裝依賴
Write-Host "檢查依賴..." -ForegroundColor Yellow

# 檢查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "錯誤: 未安裝 Python" -ForegroundColor Red
    exit 1
}

# 檢查 .env 文件
if (-not (Test-Path "LLM\.env")) {
    Write-Host "警告: 未找到 .env 文件" -ForegroundColor Yellow
    Write-Host "請複製 LLM\.env.example 到 LLM\.env 並填入 API 金鑰" -ForegroundColor Yellow
    exit 1
}

# 啟動 FastAPI 服務
Write-Host "啟動 FastAPI 服務..." -ForegroundColor Green
Write-Host "服務地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "請在 Chrome 中載入 frontend 資料夾作為擴展程式" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止服務" -ForegroundColor Yellow
Write-Host ""

Set-Location api
python main.py
