import os
from typing import List, Optional, Dict
import asyncio
from dotenv import load_dotenv
import base64
import re
from io import BytesIO
from PIL import Image

# 使用 ollama Python SDK
import ollama

# 載入環境變數
load_dotenv()


class LLMHandler:
    """處理 LLM 對話的主要類別"""
    
    def __init__(self):
        """初始化 LLM Handler"""
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        
        # 初始化 Ollama 客戶端
        self.client = ollama.Client(host=self.base_url)
        
        # 系統提示詞
        self.system_prompt = """你是一個友善且專業的 AI 助理，專門幫助用戶理解和分析網頁內容。

你的能力包括：
1. 回答關於網頁內容的問題
2. 分析用戶提供的截圖
3. 提供清晰、有幫助的解釋
4. 記住對話上下文，避免重複詢問

回答時請：
- 保持簡潔明瞭
- 使用繁體中文回答
- 如果看到截圖，請詳細分析其內容
- 對不確定的內容要誠實說明
- 回答要自然流暢，避免過於制式化
"""
    
    async def generate_response(
        self, 
        message: str, 
        image: Optional[str] = None,
        history: Optional[List[Dict]] = None
    ) -> str:
        """
        生成 AI 回應
        
        Args:
            message: 用戶輸入的文字訊息
            image: Base64 編碼的圖片（可選）
            history: 對話歷史（可選）
        
        Returns:
            AI 的回應文字
        """
        try:
            # 構建訊息列表
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                }
            ]
            
            # 添加對話歷史
            if history:
                for msg in history[-6:]:  # 只取最近 3 輪對話
                    if msg["role"] == "user":
                        messages.append({
                            "role": "user",
                            "content": msg["content"],
                            "images": [self._clean_base64(msg.get("image"))] if msg.get("image") else None
                        })
                    elif msg["role"] == "assistant":
                        messages.append({
                            "role": "assistant",
                            "content": msg["content"]
                        })
            
            # 添加當前訊息
            current_message = {
                "role": "user",
                "content": message or "請分析這張圖片"
            }
            
            if image:
                current_message["images"] = [self._clean_base64(image)]
            
            messages.append(current_message)
            
            # 調用 Ollama (在線程池中運行同步調用)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.model_name,
                    messages=messages,
                    options={
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                )
            )
            
            return response['message']['content']
        
        except Exception as e:
            print(f"LLM 生成錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"抱歉，處理您的請求時發生錯誤: {str(e)}"
    
    def _clean_base64(self, image: str) -> str:
        """清理並壓縮 base64 圖片"""
        if not image:
            return ""
        
        # 移除 data URL 前綴
        if image.startswith('data:image'):
            image = re.sub(r'^data:image/\w+;base64,', '', image)
        
        # 壓縮大圖片
        try:
            # 解碼 base64
            img_data = base64.b64decode(image)
            img = Image.open(BytesIO(img_data))
            
            # 如果圖片很大，進行壓縮
            max_size = 768  # 最大邊長（從 1024 降到 768）
            if img.width > max_size or img.height > max_size:
                # 計算縮放比例
                ratio = min(max_size / img.width, max_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                
                # 縮放圖片
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 轉換為 JPEG 並壓縮
                buffer = BytesIO()
                img.convert('RGB').save(buffer, format='JPEG', quality=60, optimize=True)
                
                # 重新編碼為 base64
                compressed_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                print(f"📊 圖片已壓縮：原始大小 {len(image)} -> 壓縮後 {len(compressed_data)} (節省 {100 - len(compressed_data)*100//len(image)}%)")
                
                return compressed_data
        except Exception as e:
            print(f"⚠️  圖片壓縮失敗: {e}，使用原始圖片")
        
        return image
    
    def clear_memory(self):
        """清除對話記憶（保留方法以保持 API 兼容性）"""
        pass
    
    def get_memory_variables(self):
        """獲取記憶中的變數（保留方法以保持 API 兼容性）"""
        return {}
