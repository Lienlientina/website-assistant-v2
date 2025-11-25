from pydantic import BaseModel
from typing import Optional, List


class Message(BaseModel):
    """對話訊息模型"""
    role: str  # 'user' 或 'assistant'
    content: str
    image: Optional[str] = None  # Base64 編碼的圖片


class ChatRequest(BaseModel):
    """聊天請求模型"""
    message: str
    image: Optional[str] = None
    history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    """聊天回應模型"""
    response: str
    status: str = "success"
