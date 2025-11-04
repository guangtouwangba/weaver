"""Vector store helpers and graph nodes."""

import os
from pathlib import Path

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS

from rag_core.chains.embeddings import build_embedding_function
from rag_core.core.models import Document as RAGDocument
from rag_core.graphs.state import DocumentIngestState, QueryState
from rag_core.retrievers.factory import RetrieverFactory
from rag_core.retrievers.vector_retriever import VectorRetriever
from shared_config.settings import AppSettings

_VECTOR_INDEX: FAISS | None = None
_RETRIEVER: VectorRetriever | None = None
_VECTOR_STORE_LOADED: bool = False  # Track if we've attempted to load from disk


def load_vector_store() -> FAISS | None:
    """Load vector store from disk if it exists.
    
    Returns:
        Loaded FAISS instance or None if no persisted store found.
    """
    global _VECTOR_INDEX, _VECTOR_STORE_LOADED
    
    if _VECTOR_STORE_LOADED:
        # Already attempted to load
        return _VECTOR_INDEX
    
    _VECTOR_STORE_LOADED = True
    settings = AppSettings()
    store_path = settings.vector_store_path
    
    # Check if the vector store directory exists
    if not os.path.exists(store_path):
        print(f"📂 向量库路径不存在: {store_path}")
        print(f"   将在首次添加文档时创建")
        return None
    
    # Check if the index file exists
    index_file = os.path.join(store_path, "index.faiss")
    if not os.path.exists(index_file):
        print(f"📂 向量库索引文件不存在: {index_file}")
        return None
    
    try:
        print(f"💾 正在从磁盘加载向量库...")
        print(f"   路径: {store_path}")
        
        embedding_function = build_embedding_function(settings)
        _VECTOR_INDEX = FAISS.load_local(
            store_path,
            embedding_function,
            allow_dangerous_deserialization=True  # Required for loading pickle files
        )
        
        total_docs = _VECTOR_INDEX.index.ntotal if _VECTOR_INDEX else 0
        print(f"✅ 向量库加载成功!")
        print(f"   └─ 已加载 {total_docs} 个向量")
        
        return _VECTOR_INDEX
        
    except Exception as e:
        print(f"❌ 加载向量库失败: {e}")
        print(f"   将创建新的向量库")
        _VECTOR_INDEX = None
        return None


def save_vector_store() -> None:
    """Save vector store to disk."""
    global _VECTOR_INDEX
    
    if _VECTOR_INDEX is None:
        print(f"⚠️  向量库为空，无需保存")
        return
    
    settings = AppSettings()
    store_path = settings.vector_store_path
    
    try:
        # Create directory if it doesn't exist
        Path(store_path).mkdir(parents=True, exist_ok=True)
        
        print(f"💾 正在保存向量库到磁盘...")
        print(f"   路径: {store_path}")
        
        _VECTOR_INDEX.save_local(store_path)
        
        total_docs = _VECTOR_INDEX.index.ntotal if _VECTOR_INDEX else 0
        print(f"✅ 向量库保存成功!")
        print(f"   └─ 已保存 {total_docs} 个向量")
        
    except Exception as e:
        print(f"❌ 保存向量库失败: {e}")
        raise


def get_vector_store() -> FAISS | None:
    """Get existing vector store, loading from disk if necessary."""
    global _VECTOR_INDEX, _VECTOR_STORE_LOADED
    
    # Try to load from disk if not yet loaded
    if not _VECTOR_STORE_LOADED:
        load_vector_store()
    
    return _VECTOR_INDEX


def build_vector_store(settings: AppSettings) -> FAISS | None:
    """Return existing vector store or load from disk if available."""
    return get_vector_store()


def get_retriever() -> VectorRetriever:
    """Get or create retriever instance.

    Returns:
        VectorRetriever instance with current vector store.
    """
    global _RETRIEVER, _VECTOR_INDEX

    if _RETRIEVER is None:
        # Create retriever using factory
        _RETRIEVER = RetrieverFactory.create_from_settings(vector_store=_VECTOR_INDEX)
    elif _RETRIEVER.get_vector_store() != _VECTOR_INDEX:
        # Update vector store if it changed
        _RETRIEVER.set_vector_store(_VECTOR_INDEX)

    return _RETRIEVER


def retrieve_documents(state: QueryState) -> QueryState:
    """Retrieve relevant documents for the given question using RetrieverInterface.

    This function uses the new RetrieverInterface for better abstraction and
    easier testing/mocking.
    
    Supports filtering by document_ids if provided in state.
    """
    global _VECTOR_INDEX

    print(f"\n🔍 开始检索文档...")
    print(f"  ├─ 问题: {state.question}")
    print(f"  ├─ Top-K: {state.retriever_top_k}")
    
    # Try to load vector store from disk if not already loaded
    if _VECTOR_INDEX is None:
        print(f"  ├─ 向量库未加载，尝试从磁盘加载...")
        get_vector_store()  # This will attempt to load from disk
    
    print(f"  └─ 向量库状态: {'已初始化' if _VECTOR_INDEX else '未初始化'}")
    
    if _VECTOR_INDEX is None:
        # No documents have been ingested yet
        print(f"  ⚠️  向量库为空，返回空结果")
        return state.model_copy(update={"documents": []})
    
    # 显示向量库统计信息
    total_vectors = _VECTOR_INDEX.index.ntotal if _VECTOR_INDEX else 0
    print(f"  ├─ 向量库中总文档数: {total_vectors}")
    
    # Perform synchronous retrieval using FAISS directly
    try:
        # Use FAISS similarity search with scores (synchronous)
        results = _VECTOR_INDEX.similarity_search_with_score(
            state.question, 
            k=state.retriever_top_k
        )
        
        # Convert to RAG Document format
        from rag_core.core.models import Document as RAGDocument
        rag_documents = []
        for doc, score in results:
            # FAISS returns distance, convert to similarity score (0-1)
            similarity_score = 1.0 / (1.0 + score)
            rag_documents.append(
                RAGDocument(
                    page_content=doc.page_content,
                    metadata=doc.metadata,
                    score=similarity_score,
                )
            )
        
        print(f"  ├─ 检索到 {len(rag_documents)} 个相关chunks")
    except Exception as e:
        print(f"  ❌ 检索失败: {e}")
        rag_documents = []
    
    # 显示检索到的文档信息
    if rag_documents:
        print(f"  ├─ 检索结果预览:")
        for i, doc in enumerate(rag_documents[:3], 1):
            doc_id = doc.metadata.get("document_id", "N/A")
            filename = doc.metadata.get("filename", "N/A")
            content_preview = doc.page_content[:50] + "..." if len(doc.page_content) > 50 else doc.page_content
            print(f"      [{i}] Doc ID: {doc_id[:8]}..., File: {filename}")
            print(f"          Content: {content_preview}")

    # Filter by document_ids if provided
    if state.document_ids:
        print(f"  ├─ 应用文档过滤: {len(state.document_ids)} 个指定文档")
        for doc_id in state.document_ids:
            print(f"      • {doc_id}")
        
        original_count = len(rag_documents)
        rag_documents = [
            doc for doc in rag_documents
            if doc.metadata.get("document_id") in state.document_ids
        ]
        print(f"  ├─ 过滤结果: {original_count} → {len(rag_documents)} 个chunks")
        
        if original_count > 0 and len(rag_documents) == 0:
            print(f"  ⚠️  警告: 过滤后没有结果！可能原因:")
            print(f"      • 指定的document_ids不存在")
            print(f"      • metadata中的document_id字段缺失")

    # Convert RAGDocument to dict format for state
    formatted = [doc.model_dump() for doc in rag_documents]
    
    print(f"  └─ 最终返回 {len(formatted)} 个文档\n")

    return state.model_copy(update={"documents": formatted})


async def persist_embeddings(state: DocumentIngestState) -> DocumentIngestState:
    """Write vectors to the FAISS store and save to disk."""
    global _VECTOR_INDEX
    
    if not state.chunks or not state.embeddings:
        raise ValueError("embed step must run before persistence")
    
    print(f"💾 开始持久化向量...")
    print(f"  ├─ Embeddings 数量: {len(state.embeddings)}")
    print(f"  ├─ Chunks 数量: {len(state.chunks)}")
    
    settings = AppSettings()  # type: ignore[arg-type]
    embedding_function = build_embedding_function(settings)
    docs = [Document(page_content=chunk, metadata=state.metadata) for chunk in state.chunks]
    
    if _VECTOR_INDEX is None:
        # Try to load existing index first
        load_vector_store()
    
    if _VECTOR_INDEX is None:
        # Initialize FAISS index with first batch of documents
        print(f"  ├─ 初始化新的 FAISS 索引...")
        _VECTOR_INDEX = FAISS.from_documents(docs, embedding=embedding_function)
        print(f"  ✓ FAISS 索引创建成功")
    else:
        # Add to existing index
        print(f"  ├─ 添加到现有 FAISS 索引...")
        _VECTOR_INDEX.add_documents(docs)
        print(f"  ✓ 向量添加成功")
    
    total_docs = _VECTOR_INDEX.index.ntotal if _VECTOR_INDEX else 0
    print(f"  ├─ 索引中总文档数: {total_docs}")
    
    # Save to disk
    print(f"  ├─ 保存向量库到磁盘...")
    save_vector_store()
    
    print(f"✅ 向量持久化完成!")
    
    return state
