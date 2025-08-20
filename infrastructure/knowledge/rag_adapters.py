"""
RAG Engine Adapters

RAG引擎适配器，负责：
1. 将独立的RAG模块适配到DDD架构
2. 转换数据格式和接口
3. 保持RAG模块的独立性
4. 提供统一的访问接口

这个适配器层允许我们在不修改现有RAG代码的情况下，
将其集成到DDD架构中。
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Domain types
from domain.knowledge import (
    DocumentId, ChunkId, KnowledgeDocument, DocumentChunk,
    SearchResult, ProcessingStatus
)

# RAG engine imports
from rag.models import Document as RAGDocument, DocumentChunk as RAGChunk
from rag.file_loader.base import BaseFileLoader
from rag.document_spliter.base import BaseDocumentSplitter
from rag.vector_store.base import BaseVectorStore
from rag.retriever.base import BaseRetriever
from rag.knowledge_store.base import BaseKnowledgeStore

logger = logging.getLogger(__name__)


class DomainToRAGAdapter:
    """
    Domain对象到RAG引擎对象的适配器
    
    负责将Domain Layer的对象转换为RAG引擎可以理解的格式。
    """
    
    @staticmethod
    def document_to_rag(domain_doc: KnowledgeDocument) -> RAGDocument:
        """将Domain文档转换为RAG文档"""
        return RAGDocument(
            id=domain_doc.id.value,
            title=domain_doc.title,
            content=domain_doc.content,
            file_type=domain_doc.content_type,
            file_size=len(domain_doc.content.encode('utf-8')),
            file_path=domain_doc.source_location,
            status=DomainToRAGAdapter._convert_status_to_rag(domain_doc.status),
            created_at=domain_doc.created_at,
            updated_at=domain_doc.updated_at,
            metadata=domain_doc.metadata
        )
    
    @staticmethod
    def chunk_to_rag(domain_chunk: DocumentChunk) -> RAGChunk:
        """将Domain块转换为RAG块"""
        return RAGChunk(
            id=domain_chunk.id.value,
            document_id=domain_chunk.document_id.value,
            content=domain_chunk.content,
            chunk_index=domain_chunk.chunk_index,
            start_position=domain_chunk.start_position,
            end_position=domain_chunk.end_position,
            embedding=domain_chunk.embedding_vector,
            metadata=domain_chunk.metadata,
            created_at=domain_chunk.created_at
        )
    
    @staticmethod
    def _convert_status_to_rag(status: ProcessingStatus) -> str:
        """转换处理状态"""
        mapping = {
            ProcessingStatus.PENDING: "pending",
            ProcessingStatus.PROCESSING: "processing",
            ProcessingStatus.COMPLETED: "completed",
            ProcessingStatus.FAILED: "failed",
            ProcessingStatus.CANCELLED: "cancelled"
        }
        return mapping.get(status, "pending")


class RAGToDomainAdapter:
    """
    RAG引擎对象到Domain对象的适配器
    
    负责将RAG引擎的输出转换为Domain Layer的对象。
    """
    
    @staticmethod
    def rag_to_document(rag_doc: RAGDocument) -> KnowledgeDocument:
        """将RAG文档转换为Domain文档"""
        return KnowledgeDocument(
            id=DocumentId(rag_doc.id),
            title=rag_doc.title,
            content=rag_doc.content,
            content_type=rag_doc.file_type,
            source_location=rag_doc.file_path or "",
            status=RAGToDomainAdapter._convert_status_to_domain(rag_doc.status),
            created_at=rag_doc.created_at,
            updated_at=rag_doc.updated_at,
            metadata=rag_doc.metadata or {}
        )
    
    @staticmethod
    def rag_to_chunk(rag_chunk: RAGChunk) -> DocumentChunk:
        """将RAG块转换为Domain块"""
        return DocumentChunk(
            id=ChunkId(rag_chunk.id),
            document_id=DocumentId(rag_chunk.document_id),
            content=rag_chunk.content,
            chunk_index=rag_chunk.chunk_index,
            start_position=rag_chunk.start_position,
            end_position=rag_chunk.end_position,
            embedding_vector=rag_chunk.embedding,
            metadata=rag_chunk.metadata or {},
            created_at=rag_chunk.created_at
        )
    
    @staticmethod
    def _convert_status_to_domain(status: str) -> ProcessingStatus:
        """转换处理状态"""
        mapping = {
            "pending": ProcessingStatus.PENDING,
            "processing": ProcessingStatus.PROCESSING,
            "completed": ProcessingStatus.COMPLETED,
            "failed": ProcessingStatus.FAILED,
            "cancelled": ProcessingStatus.CANCELLED
        }
        return mapping.get(status, ProcessingStatus.PENDING)


class RAGEngineServiceAdapter:
    """
    RAG引擎服务适配器
    
    封装RAG引擎的各种服务，提供统一的接口。
    这个适配器隐藏了RAG引擎的复杂性，让上层只需要关心业务逻辑。
    """
    
    def __init__(self):
        self.file_loader = BaseFileLoader()
        self.document_splitter = BaseDocumentSplitter()
        self.vector_store = None  # 将在子类中初始化
        self.retriever = None     # 将在子类中初始化
        self.knowledge_store = None  # 将在子类中初始化
    
    async def load_document_from_source(self, source_path: str, content_type: str) -> RAGDocument:
        """从源加载文档"""
        try:
            # 使用RAG引擎的文件加载器
            document = await self.file_loader.load(source_path)
            return document
        except Exception as e:
            logger.error(f"Failed to load document from {source_path}: {e}")
            raise
    
    async def split_document_content(self, 
                                   content: str,
                                   chunk_size: int = 1000,
                                   overlap: int = 200) -> List[str]:
        """分割文档内容"""
        try:
            # 使用RAG引擎的文档分割器
            chunks = self.document_splitter.split_text(
                text=content,
                chunk_size=chunk_size,
                chunk_overlap=overlap
            )
            return chunks
        except Exception as e:
            logger.error(f"Failed to split document content: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            if not self.vector_store:
                raise RuntimeError("Vector store not initialized")
            
            # 使用RAG引擎的向量服务
            embeddings = []
            for text in texts:
                embedding = await self.vector_store.embed_text(text)
                embeddings.append(embedding)
            
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def store_document_vectors(self, rag_chunks: List[RAGChunk]) -> None:
        """存储文档向量"""
        try:
            if not self.vector_store:
                raise RuntimeError("Vector store not initialized")
            
            # 批量存储向量
            for chunk in rag_chunks:
                await self.vector_store.add_chunk(chunk)
                
            logger.debug(f"Stored {len(rag_chunks)} document vectors")
        except Exception as e:
            logger.error(f"Failed to store document vectors: {e}")
            raise
    
    async def search_similar_content(self, 
                                   query_embedding: List[float],
                                   top_k: int = 10,
                                   filters: Dict[str, Any] = None) -> List[RAGChunk]:
        """搜索相似内容"""
        try:
            if not self.retriever:
                raise RuntimeError("Retriever not initialized")
            
            # 使用RAG引擎的检索器
            results = await self.retriever.retrieve(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters or {}
            )
            
            return results
        except Exception as e:
            logger.error(f"Failed to search similar content: {e}")
            raise


class ConfigurableRAGEngineAdapter(RAGEngineServiceAdapter):
    """
    可配置的RAG引擎适配器
    
    根据配置初始化不同的RAG组件实现。
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self._initialize_components()
    
    def _initialize_components(self):
        """根据配置初始化组件"""
        try:
            # 初始化向量存储
            vector_store_type = self.config.get('vector_store', 'memory')
            if vector_store_type == 'memory':
                from rag.vector_store.memory import InMemoryVectorStore
                self.vector_store = InMemoryVectorStore()
            elif vector_store_type == 'weaviate':
                # TODO: 实现Weaviate适配器
                from rag.vector_store.memory import InMemoryVectorStore
                self.vector_store = InMemoryVectorStore()
            
            # 初始化检索器
            retriever_type = self.config.get('retriever', 'semantic')
            if retriever_type == 'semantic':
                from rag.retriever.semantic import SemanticRetriever
                self.retriever = SemanticRetriever(self.vector_store)
            elif retriever_type == 'hybrid':
                from rag.retriever.hybrid import HybridRetriever
                self.retriever = HybridRetriever(self.vector_store)
            
            # 初始化知识存储
            knowledge_store_type = self.config.get('knowledge_store', 'memory')
            if knowledge_store_type == 'memory':
                # TODO: 实现内存知识存储
                pass
            
            logger.info(f"RAG engine adapter initialized with config: {self.config}")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            raise


class BatchProcessingAdapter:
    """
    批处理适配器
    
    为RAG引擎提供批处理能力，提高处理效率。
    """
    
    def __init__(self, rag_adapter: RAGEngineServiceAdapter):
        self.rag_adapter = rag_adapter
    
    async def batch_process_documents(self, 
                                    domain_documents: List[KnowledgeDocument],
                                    batch_size: int = 10) -> List[List[DocumentChunk]]:
        """批量处理文档"""
        results = []
        
        # 分批处理
        for i in range(0, len(domain_documents), batch_size):
            batch = domain_documents[i:i + batch_size]
            batch_results = []
            
            for document in batch:
                try:
                    # 转换为RAG格式
                    rag_doc = DomainToRAGAdapter.document_to_rag(document)
                    
                    # 分割文档
                    chunk_texts = await self.rag_adapter.split_document_content(document.content)
                    
                    # 生成向量
                    embeddings = await self.rag_adapter.generate_embeddings_batch(chunk_texts)
                    
                    # 创建chunks
                    chunks = []
                    for j, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
                        chunk = DocumentChunk(
                            id=ChunkId(f"{document.id.value}_chunk_{j}"),
                            document_id=document.id,
                            content=chunk_text,
                            chunk_index=j,
                            start_position=j * 1000,  # 简化计算
                            end_position=(j + 1) * 1000,
                            embedding_vector=embedding,
                            metadata={'batch_processed': True}
                        )
                        chunks.append(chunk)
                    
                    batch_results.append(chunks)
                    
                except Exception as e:
                    logger.error(f"Failed to process document {document.id.value}: {e}")
                    batch_results.append([])
            
            results.extend(batch_results)
        
        return results
    
    async def batch_search_queries(self, 
                                 queries: List[str],
                                 max_results_per_query: int = 5) -> List[List[SearchResult]]:
        """批量搜索查询"""
        results = []
        
        # 批量生成查询向量
        query_embeddings = await self.rag_adapter.generate_embeddings_batch(queries)
        
        # 并行搜索
        import asyncio
        
        async def search_single_query(query_embedding: List[float]) -> List[SearchResult]:
            try:
                rag_chunks = await self.rag_adapter.search_similar_content(
                    query_embedding, max_results_per_query
                )
                
                # 转换为Domain搜索结果
                search_results = []
                for i, rag_chunk in enumerate(rag_chunks):
                    # 创建搜索结果（简化处理）
                    domain_chunk = RAGToDomainAdapter.rag_to_chunk(rag_chunk)
                    
                    # 创建模拟文档
                    mock_document = KnowledgeDocument(
                        id=domain_chunk.document_id,
                        title="Search Result Document",
                        content=domain_chunk.content,
                        content_type="text/plain",
                        source_location="search_result",
                        status=ProcessingStatus.COMPLETED,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        metadata={}
                    )
                    
                    search_result = SearchResult(
                        chunk=domain_chunk,
                        document=mock_document,
                        relevance_score=1.0 - i * 0.1,  # 模拟相关性评分
                        rank=i + 1
                    )
                    search_results.append(search_result)
                
                return search_results
                
            except Exception as e:
                logger.error(f"Failed to search query: {e}")
                return []
        
        # 并行执行搜索
        tasks = [search_single_query(embedding) for embedding in query_embeddings]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Search task failed: {result}")
                final_results.append([])
            else:
                final_results.append(result)
        
        return final_results


# 工厂函数
def create_rag_adapter(config: Dict[str, Any] = None) -> ConfigurableRAGEngineAdapter:
    """
    创建RAG适配器实例
    
    Args:
        config: RAG引擎配置
        
    Returns:
        配置好的RAG适配器
    """
    if config is None:
        config = {
            'vector_store': 'memory',
            'retriever': 'semantic',
            'knowledge_store': 'memory'
        }
    
    return ConfigurableRAGEngineAdapter(config)


def create_batch_processor(rag_adapter: RAGEngineServiceAdapter = None) -> BatchProcessingAdapter:
    """
    创建批处理适配器实例
    
    Args:
        rag_adapter: RAG引擎适配器
        
    Returns:
        批处理适配器
    """
    if rag_adapter is None:
        rag_adapter = create_rag_adapter()
    
    return BatchProcessingAdapter(rag_adapter)