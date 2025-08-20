"""
Knowledge Infrastructure Implementations

知识管理基础设施层实现，包含：
1. Repository的具体实现
2. Domain Service的具体实现  
3. 外部服务集成
4. 技术实现细节

这一层负责将Domain接口绑定到具体的技术实现。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib
import json

# Domain imports
from domain.knowledge import (
    DocumentId, ChunkId, KnowledgeDocument, DocumentChunk,
    SearchQuery, SearchResult, ProcessingStatus, ChunkingStrategy, SearchStrategy,
    IKnowledgeRepository, IDocumentProcessor, IVectorService, ISearchService
)

# Infrastructure dependencies
from infrastructure.database.repositories.file import FileRepository
from infrastructure.storage.interfaces import IObjectStorage

# RAG engine imports (existing independent module)
from rag.models import Document as RAGDocument, DocumentChunk as RAGChunk
from rag.file_loader.text_loader import TextFileLoader
from rag.document_spliter.base import BaseDocumentSplitter
from rag.vector_store.memory import InMemoryVectorStore
from rag.retriever.semantic import SemanticRetriever
from rag.retriever.hybrid import HybridRetriever

logger = logging.getLogger(__name__)


class DatabaseKnowledgeRepository(IKnowledgeRepository):
    """
    基于数据库的知识仓储实现
    
    将Domain的KnowledgeDocument映射到Infrastructure的数据库存储。
    """
    
    def __init__(self, file_repository: FileRepository, storage: IObjectStorage):
        self.file_repository = file_repository
        self.storage = storage
    
    async def save_document(self, document: KnowledgeDocument) -> None:
        """保存文档到数据库"""
        try:
            # 将Domain实体转换为Infrastructure实体
            db_file = self._domain_to_db_entity(document)
            
            # 保存到数据库
            if await self.file_repository.find_by_id(document.id.value):
                await self.file_repository.update(db_file)
            else:
                await self.file_repository.create(db_file)
                
            logger.debug(f"Saved document {document.id.value} to database")
            
        except Exception as e:
            logger.error(f"Failed to save document {document.id.value}: {e}")
            raise
    
    async def find_document_by_id(self, document_id: DocumentId) -> Optional[KnowledgeDocument]:
        """根据ID查找文档"""
        try:
            db_file = await self.file_repository.find_by_id(document_id.value)
            if not db_file:
                return None
            
            return self._db_to_domain_entity(db_file)
            
        except Exception as e:
            logger.error(f"Failed to find document {document_id.value}: {e}")
            return None
    
    async def find_documents_by_status(self, status: ProcessingStatus) -> List[KnowledgeDocument]:
        """根据状态查找文档"""
        try:
            # 将Domain状态转换为数据库状态
            db_status = self._domain_status_to_db_status(status)
            db_files = await self.file_repository.find_by_status(db_status)
            
            return [self._db_to_domain_entity(db_file) for db_file in db_files]
            
        except Exception as e:
            logger.error(f"Failed to find documents by status {status}: {e}")
            return []
    
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """保存文档块"""
        try:
            # 将chunks保存到对象存储或专门的向量数据库
            chunks_data = []
            for chunk in chunks:
                chunk_data = {
                    'id': chunk.id.value,
                    'document_id': chunk.document_id.value,
                    'content': chunk.content,
                    'chunk_index': chunk.chunk_index,
                    'start_position': chunk.start_position,
                    'end_position': chunk.end_position,
                    'metadata': chunk.metadata,
                    'embedding_vector': chunk.embedding_vector,
                    'created_at': chunk.created_at.isoformat()
                }
                chunks_data.append(chunk_data)
            
            # 保存到对象存储
            chunks_json = json.dumps(chunks_data, indent=2)
            document_id = chunks[0].document_id.value if chunks else "unknown"
            chunks_key = f"chunks/{document_id}/chunks.json"
            
            from infrastructure.storage.interfaces import UploadOptions
            upload_options = UploadOptions(content_type='application/json')
            
            await self.storage.upload_object(
                bucket='files',  # 使用默认bucket
                key=chunks_key,
                data=chunks_json.encode('utf-8'),
                options=upload_options
            )
            
            logger.debug(f"Saved {len(chunks)} chunks for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to save chunks: {e}")
            raise
    
    async def find_chunks_by_document_id(self, document_id: DocumentId) -> List[DocumentChunk]:
        """查找文档的所有块"""
        try:
            chunks_key = f"chunks/{document_id.value}/chunks.json"
            
            # 从对象存储读取
            try:
                storage_object = await self.storage.download_object('files', chunks_key)
                chunks_content = storage_object.content
                chunks_data = json.loads(chunks_content.decode('utf-8'))
                
                chunks = []
                for chunk_data in chunks_data:
                    chunk = DocumentChunk(
                        id=ChunkId(chunk_data['id']),
                        document_id=DocumentId(chunk_data['document_id']),
                        content=chunk_data['content'],
                        chunk_index=chunk_data['chunk_index'],
                        start_position=chunk_data['start_position'],
                        end_position=chunk_data['end_position'],
                        metadata=chunk_data['metadata'],
                        embedding_vector=chunk_data.get('embedding_vector'),
                        created_at=datetime.fromisoformat(chunk_data['created_at'])
                    )
                    chunks.append(chunk)
                
                return chunks
                
            except FileNotFoundError:
                return []
                
        except Exception as e:
            logger.error(f"Failed to find chunks for document {document_id.value}: {e}")
            return []
    
    def _domain_to_db_entity(self, document: KnowledgeDocument):
        """将Domain实体转换为数据库实体"""
        from infrastructure.database.models.file import FileUpload
        
        return FileUpload(
            id=document.id.value,
            filename=document.title,
            content_type=document.content_type,
            file_size=len(document.content.encode('utf-8')),
            storage_location=document.source_location,
            upload_status=self._domain_status_to_db_status(document.status),
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
    
    def _db_to_domain_entity(self, db_file) -> KnowledgeDocument:
        """将数据库实体转换为Domain实体"""
        return KnowledgeDocument(
            id=DocumentId(db_file.id),
            title=db_file.filename,
            content="",  # 内容需要从存储中读取
            content_type=db_file.content_type,
            source_location=db_file.storage_location,
            status=self._db_status_to_domain_status(db_file.upload_status),
            created_at=db_file.created_at,
            updated_at=db_file.updated_at,
            metadata=db_file.metadata or {}
        )
    
    def _domain_status_to_db_status(self, status: ProcessingStatus) -> str:
        """Domain状态转数据库状态"""
        mapping = {
            ProcessingStatus.PENDING: "pending",
            ProcessingStatus.PROCESSING: "processing", 
            ProcessingStatus.COMPLETED: "confirmed",
            ProcessingStatus.FAILED: "failed",
            ProcessingStatus.CANCELLED: "cancelled"
        }
        return mapping.get(status, "pending")
    
    def _db_status_to_domain_status(self, db_status: str) -> ProcessingStatus:
        """数据库状态转Domain状态"""
        mapping = {
            "pending": ProcessingStatus.PENDING,
            "processing": ProcessingStatus.PROCESSING,
            "confirmed": ProcessingStatus.COMPLETED,
            "failed": ProcessingStatus.FAILED,
            "cancelled": ProcessingStatus.CANCELLED
        }
        return mapping.get(db_status, ProcessingStatus.PENDING)


class RAGEngineDocumentProcessor(IDocumentProcessor):
    """
    基于RAG引擎的文档处理器实现
    
    集成现有的RAG模块来实现Domain接口。
    """
    
    def __init__(self, storage: IObjectStorage):
        self.storage = storage
        self.text_loader = TextFileLoader()
        self.document_splitter = BaseDocumentSplitter()
    
    async def extract_content(self, source_location: str, content_type: str) -> str:
        """从源位置提取内容"""
        try:
            logger.debug(f"Extracting content from {source_location}")
            
            # 解析存储位置 - 可能是URL格式或者简单的key
            if source_location.startswith('minio://') or source_location.startswith('s3://'):
                # 解析URL格式: minio://bucket/key
                parts = source_location.replace('minio://', '').replace('s3://', '').split('/', 1)
                bucket = parts[0] if len(parts) > 0 else 'files'
                key = parts[1] if len(parts) > 1 else source_location
            else:
                # 默认bucket
                bucket = 'files'
                key = source_location
            
            # 从存储中读取文件
            storage_object = await self.storage.download_object(bucket, key)
            file_content = storage_object.content
            
            # 根据内容类型处理
            if content_type.startswith('text/'):
                return file_content.decode('utf-8')
            elif content_type == 'application/pdf':
                # TODO: 集成PDF处理器
                return file_content.decode('utf-8', errors='ignore')
            else:
                # 默认按文本处理
                return file_content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Failed to extract content from {source_location}: {e}")
            raise
    
    async def chunk_document(self, 
                           document: KnowledgeDocument,
                           strategy: ChunkingStrategy,
                           chunk_size: int = 1000,
                           overlap: int = 200) -> List[DocumentChunk]:
        """将文档分块"""
        try:
            logger.debug(f"Chunking document {document.id.value} with strategy {strategy}")
            
            # 转换为RAG引擎的Document对象
            rag_document = RAGDocument(
                id=document.id.value,
                title=document.title,
                content=document.content,
                file_type=document.content_type,
                file_size=len(document.content.encode('utf-8')),
                metadata=document.metadata
            )
            
            # 使用RAG引擎分块
            if strategy == ChunkingStrategy.FIXED_SIZE:
                rag_chunks = self.document_splitter.split_text(
                    text=document.content,
                    chunk_size=chunk_size,
                    chunk_overlap=overlap
                )
            else:
                # 其他策略的实现
                rag_chunks = self.document_splitter.split_text(
                    text=document.content,
                    chunk_size=chunk_size,
                    chunk_overlap=overlap
                )
            
            # 转换为Domain的DocumentChunk对象
            chunks = []
            for i, chunk_text in enumerate(rag_chunks):
                chunk_id = self._generate_chunk_id(document.id.value, i)
                chunk = DocumentChunk(
                    id=ChunkId(chunk_id),
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i,
                    start_position=i * (chunk_size - overlap),
                    end_position=i * (chunk_size - overlap) + len(chunk_text),
                    metadata={'strategy': strategy.value}
                )
                chunks.append(chunk)
            
            logger.debug(f"Created {len(chunks)} chunks for document {document.id.value}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {document.id.value}: {e}")
            raise
    
    async def validate_document(self, document: KnowledgeDocument) -> bool:
        """验证文档"""
        try:
            # 基本验证
            if not document.content or len(document.content.strip()) == 0:
                return False
            
            if len(document.content) > 10_000_000:  # 10MB text limit
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Document validation failed: {e}")
            return False
    
    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """生成块ID"""
        content = f"{document_id}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()


class OpenAIVectorService(IVectorService):
    """
    基于OpenAI的向量服务实现
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # TODO: 初始化OpenAI客户端
        self.vector_store = InMemoryVectorStore()  # 临时使用内存存储
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本向量"""
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")
            
            # TODO: 集成真实的OpenAI API
            # 目前返回模拟向量
            embeddings = []
            for text in texts:
                # 生成固定维度的模拟向量
                mock_embedding = [0.1] * 1536  # OpenAI embedding维度
                embeddings.append(mock_embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def store_vectors(self, chunks: List[DocumentChunk]) -> None:
        """存储向量"""
        try:
            logger.debug(f"Storing vectors for {len(chunks)} chunks")
            
            for chunk in chunks:
                if chunk.embedding_vector:
                    # 转换为RAG引擎的格式并存储
                    rag_chunk = RAGChunk(
                        id=chunk.id.value,
                        document_id=chunk.document_id.value,
                        content=chunk.content,
                        embedding=chunk.embedding_vector,
                        metadata=chunk.metadata
                    )
                    await self.vector_store.add_chunk(rag_chunk)
            
        except Exception as e:
            logger.error(f"Failed to store vectors: {e}")
            raise
    
    async def search_similar(self, 
                           query_vector: List[float], 
                           max_results: int,
                           filters: Dict[str, Any] = None) -> List[ChunkId]:
        """向量相似性搜索"""
        try:
            logger.debug(f"Searching similar vectors, max_results={max_results}")
            
            # 使用RAG引擎进行搜索
            results = await self.vector_store.search_similar(
                query_vector, 
                top_k=max_results,
                filters=filters or {}
            )
            
            # 转换为ChunkId列表
            chunk_ids = [ChunkId(result.chunk_id) for result in results]
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise


class HybridSearchService(ISearchService):
    """
    混合搜索服务实现
    
    结合语义搜索和关键词搜索。
    """
    
    def __init__(self, 
                 vector_service: IVectorService,
                 knowledge_repository: IKnowledgeRepository):
        self.vector_service = vector_service
        self.knowledge_repository = knowledge_repository
        
        # 初始化RAG检索器
        self.semantic_retriever = SemanticRetriever()
        self.hybrid_retriever = HybridRetriever()
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """执行搜索"""
        try:
            if query.strategy == SearchStrategy.SEMANTIC:
                return await self.semantic_search(query.text, query.max_results, query.filters)
            elif query.strategy == SearchStrategy.KEYWORD:
                return await self.keyword_search(query.text, query.max_results, query.filters)
            elif query.strategy == SearchStrategy.HYBRID:
                return await self._hybrid_search(query.text, query.max_results, query.filters)
            else:
                return await self.semantic_search(query.text, query.max_results, query.filters)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def semantic_search(self, 
                            query_text: str, 
                            max_results: int,
                            filters: Dict[str, Any] = None) -> List[SearchResult]:
        """语义搜索"""
        try:
            # 生成查询向量
            query_embeddings = await self.vector_service.generate_embeddings([query_text])
            query_vector = query_embeddings[0]
            
            # 向量搜索
            chunk_ids = await self.vector_service.search_similar(
                query_vector, max_results, filters
            )
            
            # 构建搜索结果
            results = []
            for i, chunk_id in enumerate(chunk_ids):
                # TODO: 从仓储加载完整的chunk和document信息
                # 这里简化处理
                result = SearchResult(
                    chunk=DocumentChunk(
                        id=chunk_id,
                        document_id=DocumentId("mock_doc_id"),
                        content="Mock content",
                        chunk_index=0,
                        start_position=0,
                        end_position=100,
                        metadata={}
                    ),
                    document=KnowledgeDocument(
                        id=DocumentId("mock_doc_id"),
                        title="Mock Document",
                        content="Mock content",
                        content_type="text/plain",
                        source_location="mock_location",
                        status=ProcessingStatus.COMPLETED,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        metadata={}
                    ),
                    relevance_score=1.0 - i * 0.1,  # 模拟相关性评分
                    rank=i + 1
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    async def keyword_search(self, 
                           query_text: str, 
                           max_results: int,
                           filters: Dict[str, Any] = None) -> List[SearchResult]:
        """关键词搜索"""
        try:
            # TODO: 实现关键词搜索逻辑
            # 可以使用Elasticsearch或其他全文搜索引擎
            return []
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            raise
    
    async def _hybrid_search(self, 
                           query_text: str, 
                           max_results: int,
                           filters: Dict[str, Any] = None) -> List[SearchResult]:
        """混合搜索"""
        try:
            # 分别执行语义搜索和关键词搜索
            semantic_results = await self.semantic_search(query_text, max_results // 2, filters)
            keyword_results = await self.keyword_search(query_text, max_results // 2, filters)
            
            # 合并和重排序结果
            all_results = semantic_results + keyword_results
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # 重新分配排名
            for i, result in enumerate(all_results[:max_results]):
                result.rank = i + 1
            
            return all_results[:max_results]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise