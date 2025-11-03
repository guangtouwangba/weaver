"""Vector store helpers and graph nodes."""

from typing import Any, Dict, List

from langchain.vectorstores.base import VectorStoreRetriever
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from rag_core.chains.embeddings import build_embedding_function
from shared_config.settings import AppSettings
from rag_core.graphs.state import DocumentIngestState, QueryState

_VECTOR_INDEX: FAISS | None = None


def get_vector_store() -> FAISS | None:
    """Get existing vector store if initialized."""
    return _VECTOR_INDEX


def build_vector_store(settings: AppSettings) -> FAISS | None:
    """Return existing vector store or None if not yet initialized."""
    return _VECTOR_INDEX


def retrieve_documents(state: QueryState) -> QueryState:
    """Retrieve relevant documents for the given question."""
    global _VECTOR_INDEX
    if _VECTOR_INDEX is None:
        # No documents have been ingested yet
        return state.model_copy(update={"documents": []})
    
    retriever = _VECTOR_INDEX.as_retriever(search_kwargs={"k": state.retriever_top_k})
    docs = retriever.get_relevant_documents(state.question)
    formatted = [doc.dict() for doc in docs]
    return state.model_copy(update={"documents": formatted})


async def persist_embeddings(state: DocumentIngestState) -> DocumentIngestState:
    """Write vectors to the FAISS store."""
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
        # Initialize FAISS index with first batch of documents
        print(f"  ├─ 初始化 FAISS 索引...")
        _VECTOR_INDEX = FAISS.from_documents(docs, embedding=embedding_function)
        print(f"  ✓ FAISS 索引创建成功")
    else:
        # Add to existing index
        print(f"  ├─ 添加到现有 FAISS 索引...")
        _VECTOR_INDEX.add_documents(docs)
        print(f"  ✓ 向量添加成功")
    
    print(f"✅ 向量持久化完成!")
    print(f"  └─ 索引中总文档数: {_VECTOR_INDEX.index.ntotal if _VECTOR_INDEX else 0}")
    
    return state
