"""
Agentic RAG - 超級加強版
- 多步驟推理（先計算→檢索→判斷→回答）
- 真正的工具整合
- 強化的邏輯判斷
- 結構化思考過程
"""

import os
import re
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# ==================== 配置 ====================
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen3:4b"
EMBEDDING_MODEL = "nomic-embed-text"

DOCS_PATH = "D:\\projects\\Rag\\docs"
STORAGE_PATH = "./llamaindex_storage"

# ==================== 初始化 ====================
def test_ollama():
    """測試 Ollama 連線"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def init_settings():
    """初始化設定"""
    if not test_ollama():
        raise ConnectionError(f"無法連接到 Ollama ({OLLAMA_BASE_URL})")
    
    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=300.0,
        temperature=0.0
    )
    
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    
    Settings.chunk_size = 100
    Settings.chunk_overlap = 20
    
    print(f"✅ 設定初始化完成 (LLM: {LLM_MODEL})")

# ==================== 工具函數 ====================

def get_current_year() -> int:
    """獲取當前年份"""
    return datetime.now().year

def calculate_age(birth_year: int) -> int:
    """計算年齡"""
    current_year = get_current_year()
    return current_year - birth_year

def check_age_in_range(age: int, min_age: int, max_age: int) -> Tuple[bool, str]:
    """
    檢查年齡是否在範圍內
    
    Returns:
        (是否符合, 詳細說明)
    """
    if age < min_age:
        return False, f"{age}歲 < {min_age}歲（下限），不符合"
    elif age > max_age:
        return False, f"{age}歲 > {max_age}歲（上限），不符合"
    else:
        return True, f"{min_age}歲 <= {age}歲 <= {max_age}歲，符合"

def extract_age_range(text: str) -> Optional[Tuple[int, int]]:
    """
    從文本中提取年齡範圍
    
    例如："7足歲~80歲" → (7, 80)
    """
    patterns = [
        r'(\d+)足?歲?\s*[~～\-到至]\s*(\d+)足?歲?',
        r'(\d+)\s*[~～\-到至]\s*(\d+)\s*歲',
        r'年齡.*?(\d+).*?(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            min_age = int(match.group(1))
            max_age = int(match.group(2))
            return (min_age, max_age)
    
    return None

# ==================== 多步驟推理引擎 ====================

class MultiStepReasoner:
    """多步驟推理引擎"""
    
    def __init__(self, query_engine, llm):
        self.query_engine = query_engine
        self.llm = llm
    
    def step1_extract_question_info(self, question: str) -> Dict:
        """步驟1：從問題中提取資訊"""
        print("\n🔍 步驟1：分析問題")
        
        info = {
            'original_question': question,
            'has_birth_year': False,
            'birth_year': None,
            'has_age': False,
            'age': None,
            'calculated_age': None,
            'question_type': 'unknown',
            'key_entities': []
        }
        
        # 提取出生年份
        birth_year_match = re.search(r'(\d{4})年出生', question)
        if birth_year_match:
            info['has_birth_year'] = True
            info['birth_year'] = int(birth_year_match.group(1))
            info['calculated_age'] = calculate_age(info['birth_year'])
            info['question_type'] = 'age_eligibility'
            print(f"   ✓ 偵測到出生年份: {info['birth_year']}")
            print(f"   ✓ 計算年齡: {info['calculated_age']} 歲")
        
        # 提取年齡
        age_match = re.search(r'(\d+)歲', question)
        if age_match and not info['has_birth_year']:
            info['has_age'] = True
            info['age'] = int(age_match.group(1))
            info['question_type'] = 'age_eligibility'
            print(f"   ✓ 偵測到年齡: {info['age']} 歲")
        
        # 提取關鍵實體（保險商品名稱等）
        keywords = ['旅平險', '醫療險', '壽險', '意外險', '保險']
        for kw in keywords:
            if kw in question:
                info['key_entities'].append(kw)
        
        if info['key_entities']:
            print(f"   ✓ 關鍵實體: {', '.join(info['key_entities'])}")
        
        return info
    
    def step2_retrieve_rules(self, question: str, entities: List[str]) -> Dict:
        """步驟2：檢索相關規則"""
        print("\n📚 步驟2：檢索規則文檔")
        
        # 構建增強查詢
        if entities:
            enhanced_query = f"{question} {' '.join(entities)} 年齡限制 投保條件"
        else:
            enhanced_query = f"{question} 年齡限制 投保條件"
        
        print(f"   查詢: {enhanced_query}")
        
        nodes = self.query_engine.retrieve(enhanced_query)
        
        print(f"   ✓ 找到 {len(nodes)} 個相關文檔")
        
        # 提取規則
        rules = {
            'raw_texts': [],
            'age_ranges': [],
            'sources': []
        }
        
        for i, node in enumerate(nodes[:5]):  # 取前5個
            text = node.text
            rules['raw_texts'].append(text)
            rules['sources'].append(node.metadata.get('file_name', 'Unknown'))
            
            # 嘗試提取年齡範圍
            age_range = extract_age_range(text)
            if age_range:
                rules['age_ranges'].append(age_range)
                print(f"   ✓ 文檔 {i+1} 找到年齡範圍: {age_range[0]}-{age_range[1]} 歲")
        
        return rules
    
    def step3_logical_reasoning(self, question_info: Dict, rules: Dict) -> Dict:
        """步驟3：邏輯推理和判斷"""
        print("\n🧠 步驟3：邏輯推理")
        
        reasoning = {
            'can_answer': False,
            'conclusion': None,
            'reasoning_steps': [],
            'evidence': []
        }
        
        # 確定要判斷的年齡
        target_age = None
        if question_info['calculated_age'] is not None:
            target_age = question_info['calculated_age']
            reasoning['reasoning_steps'].append(
                f"目標年齡: {target_age} 歲（從 {question_info['birth_year']} 年出生計算）"
            )
        elif question_info['age'] is not None:
            target_age = question_info['age']
            reasoning['reasoning_steps'].append(f"目標年齡: {target_age} 歲")
        
        # 如果有找到年齡範圍規則
        if target_age is not None and rules['age_ranges']:
            # 使用第一個找到的年齡範圍（通常是最相關的）
            min_age, max_age = rules['age_ranges'][0]
            
            reasoning['reasoning_steps'].append(
                f"規則要求: {min_age} 歲 ~ {max_age} 歲"
            )
            
            # 執行判斷
            is_eligible, explanation = check_age_in_range(target_age, min_age, max_age)
            
            reasoning['reasoning_steps'].append(f"判斷: {explanation}")
            
            reasoning['can_answer'] = True
            reasoning['conclusion'] = "可以" if is_eligible else "不可以"
            
            print(f"   ✓ 年齡判斷: {target_age} 歲 vs {min_age}-{max_age} 歲")
            print(f"   ✓ 結論: {reasoning['conclusion']}")
            print(f"   ✓ 理由: {explanation}")
            
        else:
            print("   ⚠️ 無法找到明確的年齡範圍規則，需要 LLM 推理")
        
        return reasoning
    
    def step4_generate_answer(
        self, 
        question: str,
        question_info: Dict,
        rules: Dict,
        reasoning: Dict
    ) -> str:
        """步驟4：生成最終答案"""
        print("\n✍️ 步驟4：生成答案")
        
        # 如果已經有明確結論，直接生成結構化答案
        if reasoning['can_answer'] and reasoning['conclusion']:
            
            # 組合證據
            evidence_text = "\n".join([
                f"- {step}" for step in reasoning['reasoning_steps']
            ])
            
            # 取得文檔原文作為補充
            context_sample = rules['raw_texts'][0][:300] if rules['raw_texts'] else ""
            
            answer = f"""{reasoning['conclusion']}。

理由：
{evidence_text}

根據文檔規定：
{context_sample}

參考來源: {', '.join(set(rules['sources'][:3]))}
"""
            
            print("   ✓ 使用結構化推理結果生成答案")
            return answer
        
        # 如果沒有明確結論，使用 LLM 生成
        else:
            print("   ⚠️ 使用 LLM 生成答案")
            
            context = "\n\n---\n\n".join([
                f"文檔片段 {i+1}:\n{text}"
                for i, text in enumerate(rules['raw_texts'][:3])
            ])
            
            # 構建詳細的推理 prompt
            reasoning_context = ""
            if question_info['calculated_age']:
                reasoning_context = f"""
【已知資訊】
- {question_info['birth_year']} 年出生的人現在是 {question_info['calculated_age']} 歲
"""
            elif question_info['age']:
                reasoning_context = f"""
【已知資訊】
- 問題提到的年齡是 {question_info['age']} 歲
"""
            
            prompt = f"""請根據以下資訊回答問題。

{reasoning_context}

【文檔內容】
{context}

【問題】
{question}

【回答要求】
1. 第一句話直接回答：可以 或 不可以
2. 說明理由，包括：
   - 從文檔中找到的年齡限制規則
   - 數字比較過程（例如：6 < 7，所以不符合）
   - 是否符合條件
3. 補充相關資訊

【重要】
- 如果文檔說「7足歲~80歲」，意思是「7 <= 年齡 <= 80」
- 6歲 < 7歲，所以 6歲不符合
- 必須展示清楚的數字比較

請回答：
"""
            
            response = self.llm.complete(prompt)
            answer = str(response).strip()
            
            # 添加來源
            sources = list(set(rules['sources'][:3]))
            answer += f"\n\n📚 參考來源: {', '.join(sources)}"
            
            return answer
    
    def reason(self, question: str) -> str:
        """執行完整的多步驟推理"""
        print("\n" + "="*70)
        print("🤖 開始多步驟推理")
        print("="*70)
        
        try:
            # 步驟1：提取問題資訊
            question_info = self.step1_extract_question_info(question)
            
            # 步驟2：檢索規則
            rules = self.step2_retrieve_rules(
                question, 
                question_info['key_entities']
            )
            
            # 步驟3：邏輯推理
            reasoning = self.step3_logical_reasoning(question_info, rules)
            
            # 步驟4：生成答案
            answer = self.step4_generate_answer(
                question,
                question_info,
                rules,
                reasoning
            )
            
            print("\n" + "="*70)
            
            return answer
            
        except Exception as e:
            print(f"\n❌ 推理過程出錯: {e}")
            import traceback
            traceback.print_exc()
            return f"推理失敗: {e}"

# ==================== 超級 Agentic RAG ====================

class SuperAgenticRAG:
    """超級 Agentic RAG - 多步驟推理版本"""
    
    def __init__(self, index):
        self.index = index
        self.llm = Settings.llm
        
        # 建立查詢引擎
        self.query_engine = index.as_query_engine(
            similarity_top_k=8,  # 增加檢索數量
            llm=self.llm
        )
        
        # 建立多步驟推理器
        self.reasoner = MultiStepReasoner(self.query_engine, self.llm)
        
        print("✅ 超級 Agentic RAG 初始化完成")
    
    def query(self, question: str) -> str:
        """查詢"""
        print(f"\n💬 問題: {question}")
        
        try:
            # 使用多步驟推理
            answer = self.reasoner.reason(question)
            
            print(f"\n✅ 最終答案:\n")
            print(answer)
            print()
            
            return answer
            
        except Exception as e:
            error_msg = f"❌ 查詢失敗: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg

# ==================== 文件管理 ====================

class DocumentManager:
    """文件管理器"""
    
    def __init__(self, docs_path=DOCS_PATH, storage_path=STORAGE_PATH):
        self.docs_path = docs_path
        self.storage_path = storage_path
        init_settings()
    
    def load_or_build_index(self, force_rebuild=False):
        """載入或建立索引"""
        if os.path.exists(self.storage_path) and not force_rebuild:
            print("📂 載入現有索引...")
            try:
                storage_context = StorageContext.from_defaults(
                    persist_dir=self.storage_path
                )
                index = load_index_from_storage(storage_context)
                print("✅ 索引載入完成")
                return index
            except Exception as e:
                print(f"⚠️ 載入失敗: {e}，重新建立...")
        
        print("🔨 建立新索引...")
        
        if not os.path.exists(self.docs_path):
            print(f"❌ 文檔目錄不存在: {self.docs_path}")
            return None
        
        documents = SimpleDirectoryReader(
            input_dir=self.docs_path,
            required_exts=[".txt", ".md", ".pdf", ".docx"],
            recursive=True
        ).load_data()
        
        if not documents:
            print(f"❌ 未找到文檔")
            return None
        
        print(f"✅ 載入 {len(documents)} 個文件")
        
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        index.storage_context.persist(persist_dir=self.storage_path)
        
        print("✅ 索引建立完成")
        return index

# ==================== 互動模式 ====================

def interactive_mode():
    """互動模式"""
    print("\n" + "="*70)
    print("🚀 Agentic RAG 系統 - 超級加強版")
    print("="*70)
    print("\n特色:")
    print("  ✓ 多步驟推理（分析→檢索→判斷→回答）")
    print("  ✓ 自動提取年齡範圍規則")
    print("  ✓ 邏輯判斷工具（精確比較數字）")
    print("  ✓ 結構化推理過程（可視化）")
    print("  ✓ 更聰明的答案生成")
    print("\n指令:")
    print("  直接輸入問題")
    print("  quit / exit   → 離開")
    print("="*70)
    
    # 初始化
    try:
        doc_mgr = DocumentManager(DOCS_PATH, STORAGE_PATH)
        rebuild = input("\n重建索引? (y/n, 預設 n): ").lower() == 'y'
        
        index = doc_mgr.load_or_build_index(force_rebuild=rebuild)
        if not index:
            print("❌ 索引建立失敗")
            return
        
        rag = SuperAgenticRAG(index)
        
    except ConnectionError as e:
        print(f"\n❌ {e}")
        return
    except Exception as e:
        print(f"\n❌ 初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*70)
    print("💬 開始對話")
    print("="*70)
    print("\n💡 試試看這些問題:")
    print("  - 6歲可以保旅平險嗎？")
    print("  - 1880年出生的人可以投保旅平險嗎？")
    print("  - 25歲可以投保什麼保險？")
    print()
    
    # 互動迴圈
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再見!")
                break
            
            # 處理問題
            rag.query(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 再見!")
            break
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()

# ==================== 主程式 ====================

if __name__ == "__main__":
    try:
        interactive_mode()
    except Exception as e:
        print(f"\n❌ 程式錯誤: {e}")
        import traceback
        traceback.print_exc()
