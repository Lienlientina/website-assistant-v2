# AI Website Assistant v2

一個支援多模態對話的 Chrome Extension AI 助理，可以分析網頁截圖並回答問題。整合 RAG (Retrieval-Augmented Generation) 向量資料庫，提供基於知識庫的智能問答。

## 專案結構

```
website assistant v2/
├── frontend/          # Chrome Extension 前端
├── api/              # FastAPI 後端服務
└── LLM/              # LangChain LLM 實作
    ├── knowledge_base.py      # 向量資料庫管理器
    ├── llm_handler.py         # LLM 處理器（整合 RAG）
    └── knowledge/
        ├── system_rules.txt   # 系統提示詞
        ├── qa_knowledge.json  # 知識庫（49條文檔）
        └── vectordb/          # ChromaDB 向量資料庫（自動生成）
```

## 功能特色

✅ 聊天式對話介面  
✅ 網頁截圖功能  
✅ 多模態支援（文字 + 圖片）  
✅ 對話記憶（保留 2-3 輪）  
✅ 歷史記錄持久化  
✅ 網頁重整自動清除記錄  
✅ **RAG 知識檢索** - 基於向量資料庫的智能問答  
✅ **口語化理解** - 支援同義詞和自然語言提問  

## 安裝步驟

### 1. 後端設置

#### 安裝依賴
```powershell
# 安裝 API 依賴
cd api
pip install -r requirements.txt

# 安裝 LLM 依賴（包含向量資料庫）
cd ..\LLM
pip install -r requirements.txt
```

#### 配置環境變數
```powershell
cd LLM
copy .env.example .env
```

編輯 `.env` 文件，配置 Ollama 連接：
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
TEMPERATURE=0.7
MAX_TOKENS=1000
```

#### 初始化向量資料庫（首次使用）
```powershell
python knowledge_base.py
```

這會：
- 載入 `knowledge/qa_knowledge.json` (49條知識文檔)
- 建立向量索引（使用 `paraphrase-multilingual-MiniLM-L12-v2`）
- 儲存到 `knowledge/vectordb/`
- 執行測試搜尋

### 2. 啟動後端服務

```powershell
cd ..\api
python main.py
```

服務將運行在 `http://localhost:8000`

### 3. 安裝 Chrome Extension

1. 打開 Chrome 瀏覽器
2. 進入 `chrome://extensions/`
3. 開啟右上角的「開發人員模式」
4. 點擊「載入未封裝項目」
5. 選擇 `frontend` 資料夾
6. 完成！Extension 圖標會出現在瀏覽器工具列

## 使用方法

### 基本對話
1. 點擊瀏覽器工具列的 Extension 圖標
2. 在輸入框輸入問題
3. 點擊「發送」按鈕
4. AI 會回應你的問題

### 截圖分析
1. 點擊 📷 截圖按鈕
2. 系統會截取當前網頁畫面
3. 輸入你想問的問題（或直接發送）
4. 點擊「發送」按鈕
5. AI 會分析截圖並回答

### 歷史記錄
- 對話記錄會自動保存
- 關閉 popup 不會清除記錄
- 重新整理網頁會自動清除該分頁的記錄
- 可手動點擊 🗑️ 按鈕清除記錄

## 技術架構

### 前端 (Chrome Extension)
- **manifest.json**: Extension 配置
- **popup.html/css/js**: 對話介面
- **background.js**: 背景服務（處理截圖）
- **content.js**: 內容腳本（注入網頁）

### 後端 (FastAPI)
- **main.py**: API 主服務
- **models/chat.py**: 數據模型
- 支援 CORS 跨域請求
- 健康檢查端點

### LLM (Ollama + RAG)
- **llm_handler.py**: LLM 處理邏輯（整合 RAG）
- **knowledge_base.py**: 向量資料庫管理器
- **knowledge/**: 知識庫文件
  - `system_rules.txt`: 系統提示詞
  - `qa_knowledge.json`: 知識文檔（49條）
  - `vectordb/`: ChromaDB 向量資料庫
- 支援 Ollama 本地/遠端模型
- RAG 檢索：自動搜尋 top-3 相關知識
- 智慧重排序：同義詞映射、問題類型識別

## RAG 工作流程

```
用戶問題
    ↓
同義詞擴展（生病→病假、生理期→生理假）
    ↓
向量化 (embedding)
    ↓
ChromaDB 相似度搜尋 + 智慧重排序
    ↓
取 top-3 最相關文檔
    ↓
注入到 system prompt
    ↓
LLM 生成回答（基於檢索到的知識）
```

### 支援的口語化問法
- "生病要附診斷書嗎" → 自動匹配病假規則
- "生理期可以請假嗎" → 自動匹配生理假規則
- "找不到公假選項" → 返回假單類型選擇指引
- "感冒請假要證明嗎" → 匹配病假證明規則

## API 端點

### `POST /api/chat`
發送聊天訊息

**請求體:**
```json
{
  "message": "你好",
  "image": "base64_encoded_image",
  "history": [...]
}
```

**回應:**
```json
{
  "response": "AI 的回應",
  "status": "success"
}
```

### `GET /health`
健康檢查

### `POST /api/clear_history`
清除對話歷史

## 支援的 LLM 模型

- ✅ Ollama 本地/遠端模型
  - qwen2.5:7b（推薦，支援中文和多模態）
  - llama3.2:3b（輕量快速）
  - 其他 Ollama 支援的模型
- 🔄 可擴展支援 OpenAI、Anthropic

## 開發說明

### 修改 LLM 模型
編輯 `LLM/.env`:
```
OLLAMA_MODEL=qwen2.5:7b
```

### 更新知識庫
1. 編輯 `LLM/knowledge/qa_knowledge.json`
2. 執行 `python knowledge_base.py` 重建向量索引

### 修改 System Prompt
編輯 `LLM/knowledge/system_rules.txt`

## 疑難排解

### Extension 無法載入
- 確認 `manifest.json` 格式正確
- 檢查是否開啟「開發人員模式」

### API 連接失敗
- 確認後端服務已啟動（`python main.py`）
- 檢查防火牆設置
- 確認 port 8000 未被佔用

### LLM 回應錯誤
- 檢查 Ollama 服務是否運行
- 確認 `.env` 中的 `OLLAMA_BASE_URL` 正確
- 確認模型已下載（`ollama pull qwen2.5:7b`）
- 查看後端 console 的錯誤訊息

### 向量資料庫初始化失敗
- 確認已安裝 `chromadb` 和 `sentence-transformers`
- 首次使用會下載 embedding 模型（約 420MB），需要網路連接
- 檢查 `LLM/knowledge/qa_knowledge.json` 格式是否正確

## 專案特色

### 知識庫內容
本專案整合了成功大學請假系統的完整規則知識庫，包含：
- 各類假別規定（病假、事假、生理假等）
- 證明文件要求
- 申請流程和時限
- 特殊情境處理
- 假單類型選擇指引

### 智慧檢索特性
- **同義詞映射**：理解"生病"→病假、"生理期"→生理假
- **問題類型識別**：自動識別證明、天數、流程類問題
- **UI問題處理**：識別"找不到選項"等界面問題
- **智慧重排序**：優先返回最相關的假別規則

## 授權

MIT License

## 作者

Website Assistant Team
