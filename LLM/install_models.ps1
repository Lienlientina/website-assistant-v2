# 遠端 Ollama 模型安裝腳本
# 使用方法：在 PowerShell 中執行此腳本

$OLLAMA_URL = "https://primehub.aic.ncku.edu.tw/console/apps/ollama-0-11-10-42wvn"

Write-Host "=== 遠端 Ollama 模型安裝工具 ===" -ForegroundColor Cyan
Write-Host ""

# 檢查連線
Write-Host "1. 檢查 Ollama 連線..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "$OLLAMA_URL/" -Method Get
    Write-Host "   ✅ $status" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 無法連接到 Ollama" -ForegroundColor Red
    exit 1
}

# 列出當前已安裝的模型
Write-Host "`n2. 當前已安裝的模型：" -ForegroundColor Yellow
try {
    $tags = Invoke-RestMethod -Uri "$OLLAMA_URL/api/tags" -Method Get
    if ($tags.models.Count -eq 0) {
        Write-Host "   沒有已安裝的模型" -ForegroundColor Gray
    } else {
        $tags.models | ForEach-Object {
            Write-Host "   ✓ $($_.name) ($($_.size / 1GB) GB)" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "   ⚠️  無法列出模型" -ForegroundColor Yellow
}

# 詢問要安裝的模型
Write-Host "`n3. 選擇要安裝的模型：" -ForegroundColor Yellow
Write-Host "   1) qwen2.5vl:7b (6.0 GB) - 推薦，最佳圖片分析"
Write-Host "   2) llava:7b (4.7 GB) - 快速視覺模型"
Write-Host "   3) moondream:1.8b (1.7 GB) - 極快速小型模型"
Write-Host "   4) llava:13b (8.0 GB) - 最高精度"
Write-Host "   5) 全部安裝"
Write-Host "   0) 取消"

$choice = Read-Host "`n請輸入選項 (0-5)"

$models = @()
switch ($choice) {
    "1" { $models = @("qwen2.5vl:7b") }
    "2" { $models = @("llava:7b") }
    "3" { $models = @("moondream:1.8b") }
    "4" { $models = @("llava:13b") }
    "5" { $models = @("qwen2.5vl:7b", "llava:7b", "moondream:1.8b") }
    "0" { 
        Write-Host "`n已取消安裝" -ForegroundColor Gray
        exit 0
    }
    default {
        Write-Host "`n無效的選項" -ForegroundColor Red
        exit 1
    }
}

# 安裝模型
Write-Host "`n4. 開始安裝模型..." -ForegroundColor Yellow
foreach ($model in $models) {
    Write-Host "`n   📥 正在安裝 $model..." -ForegroundColor Cyan
    Write-Host "   ⏳ 這可能需要幾分鐘，請耐心等待..." -ForegroundColor Gray
    
    try {
        $body = @{name=$model} | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$OLLAMA_URL/api/pull" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 1800
        Write-Host "   ✅ $model 安裝完成！" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ $model 安裝失敗: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 最終檢查
Write-Host "`n5. 安裝完成！目前已安裝的模型：" -ForegroundColor Yellow
try {
    $tags = Invoke-RestMethod -Uri "$OLLAMA_URL/api/tags" -Method Get
    $tags.models | ForEach-Object {
        Write-Host "   ✓ $($_.name)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  無法列出模型" -ForegroundColor Yellow
}

Write-Host "`n✅ 完成！請修改 .env 檔案中的 OLLAMA_MODEL 來選擇使用的模型" -ForegroundColor Green
