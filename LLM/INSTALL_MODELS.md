# 在遠端 Ollama 上安裝模型

## 方法 1：使用 PowerShell 透過 API 安裝（推薦）

```powershell
# 設定遠端 Ollama URL
$OLLAMA_URL = "https://primehub.aic.ncku.edu.tw/console/apps/ollama-0-11-10-42wvn"

# 安裝 qwen2.5vl:7b（推薦用於圖片分析）
$body = @{name="qwen2.5vl:7b"} | ConvertTo-Json
Invoke-RestMethod -Uri "$OLLAMA_URL/api/pull" -Method Post -Body $body -ContentType "application/json"

# 安裝 llava:7b（快速視覺模型）
$body = @{name="llava:7b"} | ConvertTo-Json
Invoke-RestMethod -Uri "$OLLAMA_URL/api/pull" -Method Post -Body $body -ContentType "application/json"

# 安裝 moondream:1.8b（最快速的小型模型）
$body = @{name="moondream:1.8b"} | ConvertTo-Json
Invoke-RestMethod -Uri "$OLLAMA_URL/api/pull" -Method Post -Body $body -ContentType "application/json"

# 檢查已安裝的模型
Invoke-RestMethod -Uri "$OLLAMA_URL/api/tags" -Method Get
```

## 方法 2：如果有 SSH 訪問權限

```bash
# SSH 登入遠端伺服器後執行
ollama pull qwen2.5vl:7b
ollama pull llava:7b
ollama pull moondream:1.8b

# 列出已安裝的模型
ollama list
```

## 方法 3：使用 Python 腳本安裝

```python
import requests
import json

OLLAMA_URL = "https://primehub.aic.ncku.edu.tw/console/apps/ollama-0-11-10-42wvn"

def install_model(model_name):
    print(f"正在安裝 {model_name}...")
    response = requests.post(
        f"{OLLAMA_URL}/api/pull",
        json={"name": model_name},
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            if 'status' in data:
                print(f"  {data['status']}")
    
    print(f"✅ {model_name} 安裝完成！\n")

# 安裝推薦的模型
models_to_install = [
    "qwen2.5vl:7b",  # 最強大，支援圖片
    "llava:7b",       # 快速視覺模型
    "moondream:1.8b"  # 極快速小型模型
]

for model in models_to_install:
    install_model(model)
```

## 切換模型的方式

### 修改 .env 檔案
```env
OLLAMA_MODEL=qwen2.5vl:7b   # 改成你想用的模型
```

### 或在程式中動態切換
```python
from LLM.llm_handler import LLMHandler

handler = LLMHandler()

# 列出可用模型
models = handler.list_available_models()
for model in models:
    print(f"{model['name']}: {model['description']}")

# 切換模型
handler.switch_model("llava:7b")
```

## 推薦的模型選擇

| 模型 | 大小 | 速度 | 圖片支援 | 適合用途 |
|------|------|------|---------|---------|
| **qwen2.5vl:7b** | 6.0 GB | 中等 | ✅ | 最佳圖片分析品質 |
| **llava:7b** | 4.7 GB | 快 | ✅ | 平衡速度與品質 |
| **moondream:1.8b** | 1.7 GB | 極快 | ✅ | 快速回應，資源受限 |
| **llava:13b** | 8.0 GB | 慢 | ✅ | 最高精度（需要更多 GPU） |
| **qwen2.5:7b** | 4.7 GB | 快 | ❌ | 純文字對話 |

## 驗證安裝

```powershell
# 檢查已安裝的模型
Invoke-RestMethod -Uri "https://primehub.aic.ncku.edu.tw/console/apps/ollama-0-11-10-42wvn/api/tags" -Method Get

# 測試模型運行
$testBody = @{
    model = "qwen2.5vl:7b"
    prompt = "Hello, please respond briefly"
    stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://primehub.aic.ncku.edu.tw/console/apps/ollama-0-11-10-42wvn/api/generate" -Method Post -Body $testBody -ContentType "application/json"
```

## 注意事項

⚠️ **安裝時間**：模型下載可能需要 10-30 分鐘，取決於網路速度  
⚠️ **GPU 記憶體**：確保遠端 GPU 有足夠記憶體（至少 8GB）  
⚠️ **同時運行**：一次只能運行一個大型模型  

💡 **建議**：先安裝 `moondream:1.8b` 測試連線，再安裝大型模型
