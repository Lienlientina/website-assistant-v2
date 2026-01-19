"""
知識庫管理器 - 使用 ChromaDB 做向量儲存和檢索
"""
import os
import json
import shutil
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class KnowledgeBase:
    """知識庫向量資料庫管理器"""
    
    def __init__(self, persist_directory: str = None, auto_cleanup: bool = True):
        """
        初始化知識庫
        
        Args:
            persist_directory: ChromaDB 持久化儲存路徑
            auto_cleanup: 是否自動清理舊的向量資料庫
        """
        if persist_directory is None:
            persist_directory = os.path.join(
                os.path.dirname(__file__), 
                'knowledge', 
                'vectordb'
            )
        
        self.persist_directory = persist_directory
        
        # 自動清理舊版本
        if auto_cleanup:
            self._cleanup_old_versions()
        
        # 確保目錄存在
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化 ChromaDB 客戶端
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # 初始化 embedding 模型（使用支援中文的模型）
        print("📦 載入 embedding 模型...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("✅ Embedding 模型載入完成")
        
        # 取得或建立集合
        self.collection = self.client.get_or_create_collection(
            name="leave_system_knowledge",
            metadata={"description": "成大請假系統知識庫"}
        )
        
        print(f"📚 知識庫已初始化，共 {self.collection.count()} 條文檔")
    
    def _cleanup_old_versions(self):
        """清理舊的向量資料庫版本，保持目錄乾淨"""
        if not os.path.exists(self.persist_directory):
            return
        
        try:
            # 列出所有 UUID 資料夾
            uuid_folders = []
            for item in os.listdir(self.persist_directory):
                item_path = os.path.join(self.persist_directory, item)
                if os.path.isdir(item_path) and len(item) == 36:  # UUID 長度
                    uuid_folders.append(item_path)
            
            # 如果有多個舊版本，刪除所有（下次會重新生成一個乾淨的）
            if len(uuid_folders) > 1:
                print(f"🧹 清理 {len(uuid_folders)} 個舊的向量資料庫版本...")
                for folder in uuid_folders:
                    try:
                        shutil.rmtree(folder)
                    except Exception as e:
                        print(f"⚠️  無法刪除 {folder}: {e}")
                print("✅ 清理完成")
        except Exception as e:
            print(f"⚠️  清理過程發生錯誤: {e}")
    
    def load_knowledge_from_json(self, json_path: str):
        """
        從 JSON 文件載入知識並建立向量索引
        
        Args:
            json_path: JSON 知識庫文件路徑
        """
        print(f"📖 從 {json_path} 載入知識...")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
        
        # 檢查是否已有資料
        if self.collection.count() > 0:
            print("⚠️  知識庫已有資料，將清空後重新載入")
            # 清空現有資料
            self.client.delete_collection("leave_system_knowledge")
            self.collection = self.client.create_collection(
                name="leave_system_knowledge",
                metadata={"description": "成大請假系統知識庫"}
            )
        
        # 準備資料
        documents = []
        metadatas = []
        ids = []
        
        for idx, item in enumerate(knowledge_data):
            documents.append(item['content'])
            metadatas.append({
                'category': item['category'],
                'doc_id': idx
            })
            ids.append(f"doc_{idx}")
        
        # 建立 embeddings
        print(f"🔄 建立 {len(documents)} 個文檔的向量...")
        embeddings = self.embedding_model.encode(documents, show_progress_bar=True)
        
        # 加入到 ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings.tolist()
        )
        
        print(f"✅ 成功載入 {len(documents)} 條知識到向量資料庫")
    
    def search(self, query: str, top_k: int = 3, category: Optional[str] = None) -> List[Dict]:
        """
        搜尋相關知識（改進版：增加同義詞擴展和語義理解）
        
        Args:
            query: 查詢問題
            top_k: 返回前 k 個最相關的結果
            category: 可選的分類過濾
        
        Returns:
            相關知識列表
        """
        # 同義詞和口語化映射
        synonyms = {
            '生病': '病假',
            '身體不舒服': '病假',
            '感冒': '病假',
            '看醫生': '病假',
            '有事': '事假',
            '私事': '事假',
            '家裡有事': '事假',
            '親人過世': '喪假',
            '家人去世': '喪假',
            '葬禮': '喪假',
            '生理期': '生理假',
            '月經': '生理假',
            '經期': '生理假',
            '心理': '心理調適假',
            '壓力': '心理調適假',
            '情緒': '心理調適假',
            '期末考': '學期考試假',
            '考試': '學期考試假',
            '期中考': '學期考試假',
            '代表學校': '公假',
            '校隊': '公假',
            '比賽': '公假',
            '活動': '公假',
            '懷孕': '產假',
            '生小孩': '產假',
            '陪產': '產假',
        }
        
        # 關鍵詞擴展
        expanded_query = query
        for synonym, official_term in synonyms.items():
            if synonym in query:
                expanded_query = query.replace(synonym, f"{synonym} {official_term}")
                break
        
        # 證明文件相關詞彙映射
        proof_keywords = ['證明', '診斷書', '收據', '證明文件', '附證明', '要附', '需要附']
        has_proof_question = any(kw in query for kw in proof_keywords)
        
        # 天數相關詞彙
        day_keywords = ['幾天', '多久', '多少天', '天數', '上限', '限制']
        has_day_question = any(kw in query for kw in day_keywords)
        
        # 申請流程相關詞彙
        process_keywords = ['怎麼請', '如何申請', '怎麼辦', '流程', '步驟', '要找誰']
        has_process_question = any(kw in query for kw in process_keywords)
        
        # UI/選項相關詞彙（表示在找選項，不是問規則）
        ui_keywords = ['找不到', '沒有', '看不到', '沒看到', '哪裡', '選項', '在哪']
        has_ui_question = any(kw in query for kw in ui_keywords)
        
        # 提取查詢中的假別關鍵詞
        leave_types = ['病假', '事假', '喪假', '產假', '生理假', '器官捐贈假', 
                       '心理調適假', '學期考試假', '公假', '歲時祭儀假', '多元文化假']
        query_leave_type = None
        for leave_type in leave_types:
            if leave_type in expanded_query:
                query_leave_type = leave_type
                break
        
        # 建立查詢 embedding（使用擴展後的查詢）
        query_embedding = self.embedding_model.encode([expanded_query])[0]
        
        # 如果檢測到特定假別，且不是UI相關問題，先嘗試用分類過濾搜尋
        if query_leave_type and not category and not has_ui_question:
            # 先搜尋該分類
            category_results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k * 2,  # 取雙倍以便後續篩選
                where={"category": query_leave_type}
            )
            
            # 如果找到相關結果，優先使用
            if category_results['documents'] and len(category_results['documents'][0]) > 0:
                formatted_results = []
                for i in range(len(category_results['documents'][0])):
                    doc = category_results['documents'][0][i]
                    
                    # 根據問題類型過濾
                    if has_proof_question and '證明' not in doc:
                        continue  # 跳過不含證明資訊的文檔
                    if has_day_question and not any(d in doc for d in ['天', '上限', '限']):
                        continue  # 跳過不含天數資訊的文檔
                    
                    formatted_results.append({
                        'content': doc,
                        'category': category_results['metadatas'][0][i]['category'],
                        'distance': category_results['distances'][0][i] if 'distances' in category_results else None
                    })
                    
                    if len(formatted_results) >= top_k:
                        break
                
                if formatted_results:
                    return formatted_results[:top_k]
        
        # 準備過濾條件
        where_filter = {"category": category} if category else None
        
        # 查詢更多結果以便重排序
        search_k = min(top_k * 4, 12)  # 先取4倍結果
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=search_k,
            where=where_filter
        )
        
        # 格式化並重排序結果
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                cat = results['metadatas'][0][i]['category']
                dist = results['distances'][0][i] if 'distances' in results else 0
                
                # 計算相關性分數（距離越小越好）
                score = 1.0 / (1.0 + dist)  # 轉換為相似度分數
                
                # 如果問題中包含特定假別，調整分數
                if query_leave_type:
                    # 分類完全匹配，大幅提升
                    if cat == query_leave_type:
                        score *= 100.0
                    # 內容包含該假別
                    elif query_leave_type in doc:
                        score *= 10.0
                    # 包含其他假別但不是查詢的假別，降低分數
                    elif any(lt in cat or lt in doc for lt in leave_types if lt != query_leave_type):
                        score *= 0.1
                
                # 根據問題類型調整分數
                if has_proof_question and '證明' in doc:
                    score *= 2.0
                if has_day_question and any(d in doc for d in ['天', '上限', '限']):
                    score *= 2.0
                if has_process_question and any(p in doc for p in ['申請', '核准', '報備']):
                    score *= 1.5
                
                formatted_results.append({
                    'content': doc,
                    'category': cat,
                    'distance': dist,
                    'score': score
                })
            
            # 按分數排序並取前 top_k 個
            formatted_results.sort(key=lambda x: x['score'], reverse=True)
            formatted_results = formatted_results[:top_k]
            
            # 移除內部使用的 score 欄位
            for result in formatted_results:
                del result['score']
        
        return formatted_results
    
    def get_stats(self) -> Dict:
        """取得知識庫統計資訊"""
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection.name
        }


def initialize_knowledge_base():
    """初始化並載入知識庫（首次使用時執行）"""
    print("🚀 初始化知識庫...")
    
    # 建立知識庫實例
    kb = KnowledgeBase()
    
    # 載入知識
    knowledge_path = os.path.join(
        os.path.dirname(__file__), 
        'knowledge', 
        'qa_knowledge.json'
    )
    
    if os.path.exists(knowledge_path):
        kb.load_knowledge_from_json(knowledge_path)
    else:
        print(f"❌ 找不到知識庫文件: {knowledge_path}")
        return None
    
    # 顯示統計資訊
    stats = kb.get_stats()
    print(f"📊 知識庫統計: {stats}")
    
    return kb


if __name__ == "__main__":
    # 測試用：初始化知識庫
    kb = initialize_knowledge_base()
    
    if kb:
        # 測試搜尋（包含口語化問法）
        print("\n🔍 測試搜尋功能...")
        test_queries = [
            "病假需要證明嗎",
            "生理假每月可以請幾天",
            "請假超過時限怎麼辦",
            "生病要附診斷書嗎",  # 口語化
            "生理期可以請假嗎",  # 同義詞
            "感冒請假要證明嗎",  # 同義詞
            "心理壓力可以請假嗎",  # 同義詞
            "家裡有事怎麼請假",  # 口語化
            "找不到公假選項",
        ]
        
        for query in test_queries:
            print(f"\n問題: {query}")
            results = kb.search(query, top_k=2)
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result['category']}] {result['content'][:50]}...")
