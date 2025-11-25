from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import time

# 添加 LLM 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'LLM'))

from llm_handler import LLMHandler

app = FastAPI(title="AI Website Assistant API")

# CORS 設定 - 允許 Chrome Extension 訪問
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Chrome Extension 的 origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 LLM Handler
llm_handler = LLMHandler()


# 請求模型
class Message(BaseModel):
    role: str
    content: str
    image: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None
    history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


@app.get("/")
async def root():
    return {
        "message": "AI Website Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    處理聊天請求
    支援純文字對話和圖片+文字的多模態對話
    """
    try:
        start_time = time.time()
        
        # 驗證輸入
        if not request.message and not request.image:
            raise HTTPException(status_code=400, detail="訊息或圖片至少需要提供一個")
        
        # 準備對話歷史
        history = []
        if request.history:
            for msg in request.history[-6:]:  # 只取最近 3 輪對話（6 條訊息）
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "image": msg.image if hasattr(msg, 'image') else None
                })
        
        # 呼叫 LLM
        llm_start = time.time()
        response = await llm_handler.generate_response(
            message=request.message,
            image=request.image,
            history=history
        )
        llm_time = time.time() - llm_start
        total_time = time.time() - start_time
        
        print(f"⏱️  LLM 處理時間: {llm_time:.2f}秒 | 總請求時間: {total_time:.2f}秒")
        
        return ChatResponse(response=response, status="success")
    
    except Exception as e:
        print(f"錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


@app.post("/api/clear_history")
async def clear_history():
    """清除對話歷史"""
    try:
        llm_handler.clear_memory()
        return {"status": "success", "message": "歷史記錄已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
