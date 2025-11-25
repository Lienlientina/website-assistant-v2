from typing import List, Dict, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage


class MemoryManager:
    """管理對話記憶的類別"""
    
    def __init__(self, window_size: int = 6):
        """
        初始化記憶管理器
        
        Args:
            window_size: 記憶視窗大小（預設保留 3 輪對話，即 6 條訊息）
        """
        self.memory = ConversationBufferWindowMemory(
            k=window_size,
            return_messages=True,
            memory_key="chat_history"
        )
    
    def add_user_message(self, content: str):
        """添加用戶訊息到記憶"""
        self.memory.chat_memory.add_user_message(content)
    
    def add_ai_message(self, content: str):
        """添加 AI 訊息到記憶"""
        self.memory.chat_memory.add_ai_message(content)
    
    def get_messages(self) -> List:
        """獲取所有記憶中的訊息"""
        return self.memory.load_memory_variables({}).get("chat_history", [])
    
    def clear(self):
        """清除所有記憶"""
        self.memory.clear()
    
    def get_conversation_context(self) -> str:
        """
        獲取對話上下文的文字表示
        
        Returns:
            格式化的對話歷史字符串
        """
        messages = self.get_messages()
        context = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                context.append(f"用戶: {msg.content}")
            elif isinstance(msg, AIMessage):
                context.append(f"助理: {msg.content}")
        
        return "\n".join(context)
    
    def add_exchange(self, user_message: str, ai_message: str):
        """
        添加一輪完整的對話交換
        
        Args:
            user_message: 用戶訊息
            ai_message: AI 回應
        """
        self.add_user_message(user_message)
        self.add_ai_message(ai_message)
    
    def get_last_n_exchanges(self, n: int = 3) -> List[Dict]:
        """
        獲取最近 N 輪對話
        
        Args:
            n: 要獲取的對話輪數
        
        Returns:
            對話列表，每個元素包含 user 和 assistant 的訊息
        """
        messages = self.get_messages()
        exchanges = []
        
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                exchanges.append({
                    "user": messages[i].content if isinstance(messages[i], HumanMessage) else "",
                    "assistant": messages[i + 1].content if isinstance(messages[i + 1], AIMessage) else ""
                })
        
        return exchanges[-n:] if exchanges else []
    
    def has_context(self) -> bool:
        """檢查是否有對話上下文"""
        return len(self.get_messages()) > 0
