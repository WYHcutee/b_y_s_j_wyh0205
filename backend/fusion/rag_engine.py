import os
import json
import logging
from typing import List, Dict, Any
import threading
import glob
import datetime
import re

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_BASE_PATH = os.path.join(PROJECT_ROOT, "knowledge_base")

RAG_AVAILABLE = False
_embeddings = None
_text_splitter = None
_vector_store = None
_knowledge_base_path = None
_initialization_started = False
_initialization_complete = False
_knowledge_docs = []
_init_error = None

RAG_DISABLED = os.environ.get('RAG_DISABLED', '0') == '1'

def get_rag_status():
    """获取RAG状态信息"""
    return {
        "available": RAG_AVAILABLE,
        "disabled": RAG_DISABLED,
        "vector_store_loaded": _vector_store is not None,
        "embeddings_loaded": _embeddings is not None,
        "documents_count": len(_knowledge_docs),
        "init_error": _init_error,
        "init_complete": _initialization_complete
    }

def _load_knowledge_docs():
    global _knowledge_docs
    docs_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
    if os.path.exists(docs_path):
        for file_path in glob.glob(os.path.join(docs_path, "*.txt")):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if content.strip():
                    _knowledge_docs.append({
                        "content": content,
                        "source": os.path.basename(file_path)
                    })
            except Exception as e:
                logger.warning(f"加载知识文档失败 {file_path}: {e}")
    logger.info(f"加载了 {len(_knowledge_docs)} 个知识文档")

_load_knowledge_docs()

def _simple_keyword_search(query: str, k: int = 3) -> List[Dict[str, Any]]:
    if not _knowledge_docs:
        _load_knowledge_docs()
    
    if not _knowledge_docs:
        return []
    
    query_words = set(query.lower().split())
    scored_docs = []
    
    for doc in _knowledge_docs:
        content_lower = doc["content"].lower()
        score = sum(1 for word in query_words if word in content_lower)
        if score > 0:
            scored_docs.append({
                "content": doc["content"],
                "source": doc["source"],
                "score": score
            })
    
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    return scored_docs[:k]

def _save_to_documents_file(content: str, source: str):
    try:
        docs_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
        if not os.path.exists(docs_path):
            os.makedirs(docs_path)
        
        import re
        safe_source = re.sub(r'[^\w\u4e00-\u9fff]', '_', source)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_source}_{timestamp}.txt"
        filepath = os.path.join(docs_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        _knowledge_docs.append({
            "content": content,
            "source": filename
        })
        
        logger.info(f"知识已保存到文件: {filepath}")
        return True
    except Exception as e:
        logger.error(f"保存知识文件失败: {e}")
        return False

def _check_rag_dependencies():
    global RAG_AVAILABLE
    if RAG_DISABLED:
        logger.info("RAG 已禁用，使用关键词匹配模式")
        RAG_AVAILABLE = False
        return False
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        RAG_AVAILABLE = True
        logger.info("RAG 依赖已加载，知识库功能可用")
        return True
    except ImportError as e:
        logger.warning(f"RAG 依赖未安装，使用关键词匹配模式: {e}")
        return False

_check_rag_dependencies()

def _get_embeddings():
    global _embeddings, _init_error, RAG_AVAILABLE
    if not RAG_AVAILABLE:
        return None
    if _embeddings is None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            
            local_model_path = os.path.join(PROJECT_ROOT, "models", "all-MiniLM-L6-v2")
            
            if os.path.exists(local_model_path):
                logger.info(f"使用本地嵌入模型: {local_model_path}")
                _embeddings = HuggingFaceEmbeddings(
                    model_name=local_model_path,
                    model_kwargs={'local_files_only': True}
                )
                logger.info("本地嵌入模型加载成功")
            else:
                logger.info("正在加载 HuggingFace 嵌入模型（首次加载需要下载约90MB模型文件）...")
                logger.info("提示: 运行 python download_model.py 可提前下载模型到本地")
                logger.info("如果下载缓慢，可设置环境变量: HF_ENDPOINT=https://hf-mirror.com")
                _embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'local_files_only': False}
                )
                logger.info("HuggingFace 嵌入模型加载成功")
        except Exception as e:
            _init_error = f"嵌入模型加载失败: {str(e)}"
            logger.error(f"{_init_error}，将使用关键词匹配模式")
            RAG_AVAILABLE = False
            return None
    return _embeddings

def _get_text_splitter():
    global _text_splitter
    if not RAG_AVAILABLE:
        return None
    if _text_splitter is None:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            _text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
        except Exception as e:
            logger.error(f"加载文本分割器失败: {e}")
    return _text_splitter

def _get_vector_store(knowledge_base_path: str = None):
    global _vector_store, _knowledge_base_path
    
    if not RAG_AVAILABLE:
        return None
    
    if knowledge_base_path is None:
        knowledge_base_path = KNOWLEDGE_BASE_PATH
    
    if _vector_store is None or _knowledge_base_path != knowledge_base_path:
        _knowledge_base_path = knowledge_base_path
        try:
            from langchain_community.vectorstores import FAISS
            embeddings = _get_embeddings()
            if embeddings is None:
                return None
            
            if not os.path.exists(knowledge_base_path):
                os.makedirs(knowledge_base_path)
                logger.info(f"创建知识库目录: {knowledge_base_path}")
            
            index_path = os.path.join(knowledge_base_path, "faiss_index")
            if os.path.exists(index_path):
                try:
                    _vector_store = FAISS.load_local(
                        index_path,
                        embeddings,
                        allow_dangerous_deserialization=True
                    )
                    logger.info(f"加载已存在的知识库: {knowledge_base_path}")
                except Exception as e:
                    logger.error(f"加载知识库失败: {e}")
                    _vector_store = None
            
            if _vector_store is None:
                if not os.path.exists(index_path):
                    os.makedirs(index_path)
                    logger.info(f"创建索引目录: {index_path}")
                
                _vector_store = FAISS.from_texts(["知识库初始化"], embeddings)
                logger.info(f"创建新的知识库: {knowledge_base_path}")
                
                docs_path = os.path.join(knowledge_base_path, "documents")
                if os.path.exists(docs_path):
                    import glob as glob_module
                    txt_files = glob_module.glob(os.path.join(docs_path, "*.txt"))
                    if txt_files:
                        logger.info(f"自动加载 {len(txt_files)} 个知识文档...")
                        all_texts = []
                        for file_path in txt_files:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                if content.strip():
                                    all_texts.append(content)
                            except Exception as doc_e:
                                logger.warning(f"加载文档失败 {file_path}: {doc_e}")
                        
                        if all_texts:
                            _vector_store.add_texts(all_texts)
                            _vector_store.save_local(index_path)
                            logger.info(f"已自动加载 {len(all_texts)} 个文档并保存索引")
        except Exception as e:
            logger.error(f"初始化向量存储失败: {e}")
    return _vector_store

class RAGEngine:
    def __init__(self, knowledge_base_path: str = None):
        if knowledge_base_path is None:
            self.knowledge_base_path = KNOWLEDGE_BASE_PATH
        else:
            self.knowledge_base_path = knowledge_base_path
        logger.info(f"RAG 引擎使用知识库路径: {self.knowledge_base_path}")
    
    def is_available(self):
        return RAG_AVAILABLE and _vector_store is not None
    
    def add_document(self, content: str, metadata: Dict[str, Any] = None):
        if metadata is None:
            metadata = {}
        
        source = metadata.get("source", "手动添加")
        
        saved = _save_to_documents_file(content, source)
        if saved:
            logger.info(f"知识已保存到文件: {source}")
        
        if not RAG_AVAILABLE:
            logger.info("RAG向量存储不可用，已使用文件存储模式")
            return saved
        
        try:
            vector_store = _get_vector_store(self.knowledge_base_path)
            if vector_store is None:
                return saved
            
            text_splitter = _get_text_splitter()
            if text_splitter is None:
                return saved
            
            chunks = text_splitter.split_text(content)
            
            vector_store.add_texts(
                texts=chunks,
                metadatas=[metadata] * len(chunks)
            )
            
            index_path = os.path.join(self.knowledge_base_path, "faiss_index")
            vector_store.save_local(index_path)
            
            logger.info(f"成功添加文档到知识库，分割为 {len(chunks)} 个块")
            return True
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {e}")
            return saved
    
    def add_url(self, url: str):
        if not RAG_AVAILABLE:
            logger.warning("RAG 功能不可用，请先安装依赖")
            return False
        try:
            from langchain_community.document_loaders import WebBaseLoader
            loader = WebBaseLoader(url)
            documents = loader.load()
            
            for doc in documents:
                self.add_document(doc.page_content, {"source": url})
            
            logger.info(f"成功从 URL {url} 添加内容到知识库")
            return True
        except Exception as e:
            logger.error(f"从 URL 添加内容失败: {e}")
            return False
    
    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if not RAG_AVAILABLE:
            results = _simple_keyword_search(query, k)
            if results:
                logger.info(f"关键词匹配到 {len(results)} 个相关文档")
            return results
        try:
            vector_store = _get_vector_store(self.knowledge_base_path)
            if vector_store is None:
                results = _simple_keyword_search(query, k)
                if results:
                    logger.info(f"FAISS不可用，关键词匹配到 {len(results)} 个相关文档")
                return results
            
            results = vector_store.similarity_search_with_score(query, k=k)
            
            retrieved_docs = []
            for doc, score in results:
                if score < 0.5:
                    retrieved_docs.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score
                    })
            
            logger.info(f"检索到 {len(retrieved_docs)} 个相关文档")
            return retrieved_docs
        except Exception as e:
            logger.error(f"检索文档失败: {e}")
            results = _simple_keyword_search(query, k)
            if results:
                logger.info(f"异常后使用关键词匹配到 {len(results)} 个相关文档")
            return results
    
    def get_relevant_knowledge(self, query: str) -> str:
        try:
            retrieved_docs = self.retrieve(query)
            
            if not retrieved_docs:
                return ""
            
            knowledge = "【知识库检索结果】\n"
            for i, doc in enumerate(retrieved_docs, 1):
                content = doc.get('content', '')
                if not content:
                    content = doc.get('page_content', '')
                content = content[:500]
                source = doc.get('source', '')
                if not source:
                    source = doc.get('metadata', {}).get('source', '未知')
                knowledge += f"\n[{i}] 来源: {source}\n{content}...\n"
            
            return knowledge
        except Exception as e:
            logger.error(f"获取相关知识失败: {e}")
            return ""
    
    def delete_document(self, filename: str) -> bool:
        """
        删除指定文档
        Args:
            filename: 文档文件名
        Returns:
            bool: 是否删除成功
        """
        try:
            docs_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
            filepath = os.path.join(docs_path, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"文档不存在: {filename}")
                return False
            
            os.remove(filepath)
            
            global _knowledge_docs
            _knowledge_docs = [doc for doc in _knowledge_docs if doc["source"] != filename]
            
            logger.info(f"已删除文档: {filename}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def update_document(self, filename: str, new_content: str) -> bool:
        """
        更新指定文档内容
        Args:
            filename: 文档文件名
            new_content: 新内容
        Returns:
            bool: 是否更新成功
        """
        try:
            docs_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
            filepath = os.path.join(docs_path, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"文档不存在: {filename}")
                return False
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            global _knowledge_docs
            for doc in _knowledge_docs:
                if doc["source"] == filename:
                    doc["content"] = new_content
                    break
            
            logger.info(f"已更新文档: {filename}")
            return True
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    def get_document(self, filename: str) -> Dict[str, Any]:
        """
        获取指定文档内容
        Args:
            filename: 文档文件名
        Returns:
            dict: 文档信息
        """
        try:
            docs_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
            filepath = os.path.join(docs_path, filename)
            
            if not os.path.exists(filepath):
                return {"success": False, "error": "文档不存在"}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "filename": filename,
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        列出所有文档
        Returns:
            list: 文档列表
        """
        try:
            docs_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
            documents = []
            
            if os.path.exists(docs_path):
                for file_path in glob.glob(os.path.join(docs_path, "*.txt")):
                    filename = os.path.basename(file_path)
                    size = os.path.getsize(file_path)
                    mtime = os.path.getmtime(file_path)
                    documents.append({
                        "filename": filename,
                        "size": size,
                        "mtime": datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            return documents
        except Exception as e:
            logger.error(f"列出文档失败: {e}")
            return []

rag_engine = None

def get_rag_engine():
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine

def get_relevant_knowledge(query: str) -> str:
    if not RAG_AVAILABLE:
        results = _simple_keyword_search(query)
        if results:
            knowledge = "【知识库检索结果】\n"
            for i, doc in enumerate(results, 1):
                knowledge += f"\n[{i}] 来源: {doc['source']}\n{doc['content'][:500]}...\n"
            return knowledge
        return ""
    try:
        engine = get_rag_engine()
        return engine.get_relevant_knowledge(query)
    except Exception as e:
        logger.error(f"获取相关知识失败: {e}")
        return ""

def get_knowledge_status(query: str) -> dict:
    """
    获取知识库状态和检索结果
    返回: {
        "status": "available" | "no_match" | "disabled" | "error",
        "mode": "vector" | "keyword" | "none",
        "content": str,
        "sources": list
    }
    """
    result = {
        "status": "disabled",
        "mode": "none",
        "content": "",
        "sources": []
    }
    
    if RAG_DISABLED:
        result["status"] = "disabled"
        result["content"] = "知识库已禁用（RAG_DISABLED=1）"
        return result
    
    if not RAG_AVAILABLE:
        results = _simple_keyword_search(query)
        if results:
            result["status"] = "available"
            result["mode"] = "keyword"
            result["sources"] = [doc['source'] for doc in results]
            knowledge = "【关键词匹配模式】检索到相关知识：\n"
            for i, doc in enumerate(results, 1):
                knowledge += f"\n[{i}] 来源: {doc['source']}\n{doc['content'][:500]}...\n"
            result["content"] = knowledge
        else:
            result["status"] = "no_match"
            result["mode"] = "keyword"
            result["content"] = "知识库已启用（关键词匹配模式），但未找到相关内容"
        return result
    
    try:
        engine = get_rag_engine()
        retrieved = engine.retrieve(query)
        
        if retrieved:
            result["status"] = "available"
            result["mode"] = "vector"
            result["sources"] = [doc.get('source', doc.get('metadata', {}).get('source', '未知')) for doc in retrieved]
            knowledge = "【向量检索模式】检索到相关知识：\n"
            for i, doc in enumerate(retrieved, 1):
                content = doc.get('content', '')
                if not content:
                    content = doc.get('page_content', '')
                content = content[:500]
                source = doc.get('source', '')
                if not source:
                    source = doc.get('metadata', {}).get('source', '未知')
                knowledge += f"\n[{i}] 来源: {source}\n{content}...\n"
            result["content"] = knowledge
        else:
            result["status"] = "no_match"
            result["mode"] = "vector"
            result["content"] = "知识库已启用（向量检索模式），但未找到相关内容"
    except Exception as e:
        result["status"] = "error"
        result["content"] = f"知识库检索出错: {str(e)}"
        logger.error(f"获取相关知识失败: {e}")
    
    return result

def init_rag_async():
    global _initialization_started, _initialization_complete
    
    if _initialization_started:
        return
    
    _initialization_started = True
    
    def _init():
        global _initialization_complete
        try:
            logger.info("开始后台初始化 RAG 引擎...")
            _get_vector_store()
            _initialization_complete = True
            logger.info("RAG 引擎后台初始化完成")
        except Exception as e:
            logger.error(f"RAG 引擎初始化失败: {e}")
    
    thread = threading.Thread(target=_init, daemon=True)
    thread.start()

if not RAG_DISABLED and RAG_AVAILABLE:
    init_rag_async()