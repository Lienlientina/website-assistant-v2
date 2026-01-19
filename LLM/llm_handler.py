import os
from typing import List, Optional, Dict
import asyncio
from dotenv import load_dotenv
import base64
import re
import json
from io import BytesIO
from PIL import Image

# 使用 ollama Python SDK
import ollama

# 導入知識庫管理器
from knowledge_base import KnowledgeBase

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
        
        # 載入模型配置
        self.models_config = self._load_models_config()
        
        # 初始化 Ollama 客戶端
        self.client = ollama.Client(host=self.base_url)
        
        print(f"🌐 連接到遠端 Ollama: {self.base_url}")
        print(f"🤖 使用模型: {self.model_name}")
        
        # 初始化知識庫
        self.knowledge_base = self._init_knowledge_base()
        
        # 載入系統提示詞
        self.system_prompt = self._load_system_prompt()
        print(f"📋 系統提示詞已載入")


    
    def _load_models_config(self) -> dict:
        """載入模型配置檔案"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'models_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  無法載入模型配置: {e}")
            return {"available_models": [], "current_model": self.model_name}
    
    def _load_system_prompt(self) -> str:
        """從文件載入系統提示詞"""
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'knowledge', 'system_rules.txt')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️  無法載入系統提示詞: {e}，使用預設值")
            return "你是一個有幫助的AI助理。"
    
    def _init_knowledge_base(self) -> Optional[KnowledgeBase]:
        """初始化知識庫"""
        try:
            kb = KnowledgeBase()
            
            # 如果知識庫是空的，載入資料
            if kb.collection.count() == 0:
                print("📚 知識庫為空，開始載入資料...")
                knowledge_path = os.path.join(
                    os.path.dirname(__file__), 
                    'knowledge', 
                    'qa_knowledge.json'
                )
                if os.path.exists(knowledge_path):
                    kb.load_knowledge_from_json(knowledge_path)
                else:
                    print(f"⚠️  找不到知識庫文件: {knowledge_path}")
                    return None
            
            stats = kb.get_stats()
            print(f"✅ 知識庫已就緒: {stats['total_documents']} 條文檔")
            return kb
        except Exception as e:
            print(f"❌ 知識庫初始化失敗: {e}")
            return None
    
    def list_available_models(self) -> List[Dict]:
        """列出所有可用的模型"""
        return self.models_config.get("available_models", [])
    
    def switch_model(self, model_name: str):
        """切換使用的模型"""
        self.model_name = model_name
        print(f"🔄 已切換到模型: {model_name}")
    
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
            # RAG: 檢索相關知識
            relevant_knowledge = ""
            if self.knowledge_base and message:
                search_results = self.knowledge_base.search(message, top_k=3)
                if search_results:
                    relevant_knowledge = "\n\n## 相關知識參考：\n"
                    for i, result in enumerate(search_results, 1):
                        relevant_knowledge += f"\n{i}. [{result['category']}] {result['content']}\n"
            
            # 構建系統提示詞（包含檢索到的知識）
            system_content = self.system_prompt
            if relevant_knowledge:
                system_content += relevant_knowledge
            
            # 構建訊息列表
            messages = [
                {
                    "role": "system",
                    "content": system_content
                }
            ]
            
            # 添加對話歷史
            if history:
                for msg in history[-20:]:  # 取最近 20 條訊息（約 10 輪對話）
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
            max_size = 1280  # 提高到 1280px 以保持文字清晰度
            if img.width > max_size or img.height > max_size:
                # 計算縮放比例
                ratio = min(max_size / img.width, max_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                
                # 縮放圖片
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 轉換為 JPEG 並壓縮
                buffer = BytesIO()
                img.convert('RGB').save(buffer, format='JPEG', quality=85, optimize=True)  # 提高質量到 85
                
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
