# 安裝依賴腳本 - Windows PowerShell

Write-Host "=== 安裝 AI Website Assistant 依賴 ===" -ForegroundColor Cyan
Write-Host ""

# 檢查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "錯誤: 未安裝 Python" -ForegroundColor Red
    Write-Host "請先安裝 Python 3.8 或以上版本" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python 版本:" -ForegroundColor Green
python --version
Write-Host ""

# 安裝 API 依賴
Write-Host "安裝 API 依賴..." -ForegroundColor Yellow
Set-Location api
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "API 依賴安裝失敗" -ForegroundColor Red
    exit 1
}

Write-Host "API 依賴安裝完成" -ForegroundColor Green
Write-Host ""

# 安裝 LLM 依賴
Write-Host "安裝 LLM 依賴..." -ForegroundColor Yellow
Set-Location ..\LLM
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "LLM 依賴安裝失敗" -ForegroundColor Red
    exit 1
}

Write-Host "LLM 依賴安裝完成" -ForegroundColor Green
Write-Host ""

# 創建 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "創建 .env 文件..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ".env 文件已創建，請編輯並填入你的 API 金鑰" -ForegroundColor Yellow
} else {
    Write-Host ".env 文件已存在" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "=== 安裝完成 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 編輯 LLM\.env 文件，填入 OPENAI_API_KEY" -ForegroundColor White
Write-Host "2. 執行 .\start.ps1 啟動服務" -ForegroundColor White
Write-Host "3. 在 Chrome 中載入 frontend 資料夾作為擴展程式" -ForegroundColor White
