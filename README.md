# AI Website Assistant v2

一個支援多模態對話的 Chrome Extension AI 助理，可以分析網頁截圖並回答問題。

## 專案結構

```
website assistant v2/
├── frontend/          # Chrome Extension 前端
├── api/              # FastAPI 後端服務
└── LLM/              # LangChain LLM 實作
```

## 功能特色

✅ 聊天式對話介面  
✅ 網頁截圖功能  
✅ 多模態支援（文字 + 圖片）  
✅ 對話記憶（保留 2-3 輪）  
✅ 歷史記錄持久化  
✅ 網頁重整自動清除記錄  

## 安裝步驟

### 1. 後端設置

#### 安裝 API 依賴
```powershell
cd api
pip install -r requirements.txt
```

#### 安裝 LLM 依賴
```powershell
cd ..\LLM
pip install -r requirements.txt
```

#### 配置環境變數
```powershell
# 複製環境變數範例文件
cd LLM
copy .env.example .env
```

編輯 `.env` 文件，填入你的 OpenAI API 金鑰：
```
OPENAI_API_KEY=sk-your-api-key-here
```

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

### LLM (LangChain)
- **llm_handler.py**: LLM 處理邏輯
- **memory_manager.py**: 對話記憶管理
- 支援 GPT-4 Vision 多模態
- 對話視窗記憶（k=6）

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

- ✅ OpenAI GPT-4 Vision Preview
- ✅ OpenAI GPT-4o (如有權限)
- 🔄 可擴展支援 Anthropic Claude

## 開發說明

### 修改 API 端點
編輯 `frontend/popup.js` 的 `API_BASE_URL` 變數

### 修改 LLM 模型
編輯 `LLM/llm_handler.py` 的模型配置

### 調整記憶視窗
編輯 `LLM/llm_handler.py` 的 `ConversationBufferWindowMemory(k=6)`

## 疑難排解

### Extension 無法載入
- 確認 `manifest.json` 格式正確
- 檢查是否開啟「開發人員模式」

### API 連接失敗
- 確認後端服務已啟動（`python main.py`）
- 檢查防火牆設置
- 確認 port 8000 未被佔用

### LLM 回應錯誤
- 檢查 `.env` 中的 API 金鑰是否正確
- 確認 OpenAI 帳戶有餘額
- 查看後端 console 的錯誤訊息

## 授權

MIT License

## 作者

Website Assistant Team
