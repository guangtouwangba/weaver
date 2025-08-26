"""
RAG处理服务实现

提供完整的RAG文档处理流程，包括分块、嵌入生成和向量存储。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from modules.schemas import Document, DocumentChunk
from modules.schemas.enums import ContentType, ProcessingStatus
from modules.rag.chunking.strategy_factory import get_global_factory
from modules.rag.chunking.base import ChunkingContext
from modules.rag.chunking.config import RuntimeChunkingConfig, ChunkingMode
from modules.rag.chunking.integration import initialize_chunking_integration
from modules.rag.embedding.base import IEmbeddingService, EmbeddingProvider
from modules.rag.vector_store.base import IVectorStore, VectorDocument, VectorStoreProvider
from modules.models import DocumentChunk as DocumentChunkModel

logger = logging.getLogger(__name__)


class RAGProcessingError(Exception):
    """RAG处理错误"""
    
    def __init__(self, message: str, stage: str = None, error_code: str = None):
        self.stage = stage
        self.error_code = error_code
        super().__init__(message)


class RAGProcessorConfig:
    """RAG处理器配置"""
    
    def __init__(
        self,
        embedding_provider: str = "openai",
        vector_store_provider: str = "weaviate",
        collection_name: str = "documents",
        batch_size: int = 100,
        max_concurrent_embeddings: int = 5,
        enable_quality_scoring: bool = True,
        retry_attempts: int = 3,
        timeout_seconds: int = 300,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store_provider = vector_store_provider
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.max_concurrent_embeddings = max_concurrent_embeddings
        self.enable_quality_scoring = enable_quality_scoring
        self.retry_attempts = retry_attempts
        self.timeout_seconds = timeout_seconds


class RAGProcessingResult:
    """RAG处理结果"""
    
    def __init__(
        self,
        document_id: str,
        status: ProcessingStatus,
        chunks_created: int = 0,
        embeddings_generated: int = 0,
        vectors_stored: int = 0,
        processing_time_ms: float = 0,
        strategy_used: str = None,
        quality_score: float = 0.0,
        error_message: str = None,
        stage_details: Dict[str, Any] = None,
    ):
        self.document_id = document_id
        self.status = status
        self.chunks_created = chunks_created
        self.embeddings_generated = embeddings_generated
        self.vectors_stored = vectors_stored
        self.processing_time_ms = processing_time_ms
        self.strategy_used = strategy_used
        self.quality_score = quality_score
        self.error_message = error_message
        self.stage_details = stage_details or {}


class RAGProcessor:
    """RAG处理器 - 提供完整的文档处理流程"""
    
    def __init__(
        self,
        config: Optional[RAGProcessorConfig] = None,
        embedding_service: Optional[IEmbeddingService] = None,
        vector_store: Optional[IVectorStore] = None,
    ):
        self.config = config or RAGProcessorConfig()
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
        # 使用全局分块工厂
        self.chunking_factory = None  # 将在 initialize() 中设置
        
        # 处理状态
        self._initialized = False
        self._processing_semaphore = asyncio.Semaphore(
            self.config.max_concurrent_embeddings
        )
        
        logger.info(f"RAG处理器初始化完成: {self.config.embedding_provider} + {self.config.vector_store_provider}")
    
    async def initialize(self) -> None:
        """初始化RAG处理器"""
        if self._initialized:
            return
        
        try:
            # 初始化chunking集成（这会自动注册所有策略）
            await initialize_chunking_integration()
            self.chunking_factory = get_global_factory()
            logger.info("分块系统初始化完成")
            
            # 初始化嵌入服务
            if self.embedding_service:
                await self.embedding_service.initialize()
                logger.info(f"嵌入服务初始化完成: {self.embedding_service.service_name}")
            
            # 初始化向量存储
            if self.vector_store:
                await self.vector_store.initialize()
                logger.info(f"向量存储初始化完成: {self.config.vector_store_provider}")
            
            self._initialized = True
            logger.info("RAG处理器初始化完成")
            
        except Exception as e:
            logger.error(f"RAG处理器初始化失败: {e}")
            raise RAGProcessingError(f"初始化失败: {e}", stage="initialization")
    
    async def process_document(
        self,
        document: Document,
        chunking_config: Optional[Dict[str, Any]] = None,
        topic_id: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> RAGProcessingResult:
        """
        处理单个文档的完整RAG流程
        
        Args:
            document: 要处理的文档
            chunking_config: 分块配置
            topic_id: 主题ID
            file_id: 文件ID
            
        Returns:
            RAGProcessingResult: 处理结果
        """
        start_time = time.time()
        
        # 确保初始化
        await self.initialize()
        
        try:
            # 阶段1: 智能分块
            logger.info(f"开始处理文档 {document.id}: 智能分块阶段")
            chunks, chunking_details = await self._process_chunking(
                document, chunking_config
            )
            
            if not chunks:
                raise RAGProcessingError("分块处理失败: 未生成任何文档块", stage="chunking")
            
            logger.info(f"分块完成: {len(chunks)} 个块，策略: {chunking_details.get('strategy_used')}")
            
            # 阶段2: 生成嵌入向量
            logger.info(f"开始嵌入生成阶段: {len(chunks)} 个块")
            embeddings = await self._generate_embeddings(chunks)
            
            if len(embeddings) != len(chunks):
                raise RAGProcessingError(
                    f"嵌入数量不匹配: 期望 {len(chunks)}, 实际 {len(embeddings)}",
                    stage="embedding"
                )
            
            logger.info(f"嵌入生成完成: {len(embeddings)} 个向量")
            
            # 阶段3: 存储向量
            logger.info(f"开始向量存储阶段")
            stored_count = await self._store_vectors(
                chunks, embeddings, document, topic_id, file_id
            )
            
            logger.info(f"向量存储完成: {stored_count} 个向量")
            
            # 计算处理时间和质量分数
            processing_time = (time.time() - start_time) * 1000
            quality_score = self._calculate_quality_score(chunks, chunking_details)
            
            result = RAGProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.COMPLETED,
                chunks_created=len(chunks),
                embeddings_generated=len(embeddings),
                vectors_stored=stored_count,
                processing_time_ms=processing_time,
                strategy_used=chunking_details.get('strategy_used'),
                quality_score=quality_score,
                stage_details={
                    'chunking': chunking_details,
                    'embedding_dimension': len(embeddings[0]) if embeddings else 0,
                    'vector_store_collection': self.config.collection_name,
                }
            )
            
            logger.info(
                f"文档 {document.id} RAG处理完成: "
                f"{result.chunks_created} 块, "
                f"{result.embeddings_generated} 嵌入, "
                f"{result.vectors_stored} 存储, "
                f"耗时 {result.processing_time_ms:.1f}ms"
            )
            
            return result
            
        except RAGProcessingError:
            raise
        except Exception as e:
            logger.error(f"文档 {document.id} RAG处理失败: {e}")
            return RAGProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.FAILED,
                processing_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
        finally:
            # 确保清理向量存储连接
            try:
                if hasattr(self.vector_store, 'cleanup'):
                    await self.vector_store.cleanup()
            except Exception as cleanup_error:
                logger.warning(f"向量存储清理失败: {cleanup_error}")
    
    async def _process_chunking(
        self, document: Document, chunking_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[DocumentChunk], Dict[str, Any]]:
        """处理文档分块"""
        try:
            # 解析分块配置
            config = self._parse_chunking_config(chunking_config)
            
            # 分析文档特征
            content = document.content
            words = content.split()
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            
            # 转换内容类型为MIME类型格式
            content_type_mapping = {
                ContentType.TEXT: "text/plain",
                ContentType.TXT: "text/plain", 
                ContentType.MD: "text/markdown",
                ContentType.HTML: "text/html",
                ContentType.PDF: "application/pdf",
                ContentType.JSON: "application/json",
                ContentType.CSV: "text/csv",
                ContentType.XML: "text/xml"
            }
            mime_content_type = content_type_mapping.get(document.content_type, "text/plain")
            
            # 创建分块上下文
            context = ChunkingContext(
                document=document,
                document_length=len(content),
                word_count=len(words),
                paragraph_count=len(paragraphs),
                sentence_count=len(sentences),
                avg_paragraph_length=sum(len(p) for p in paragraphs) / max(len(paragraphs), 1),
                avg_sentence_length=sum(len(s) for s in sentences) / max(len(sentences), 1),
                has_structure_markers=any(marker in content for marker in ['#', '##', '###', '-', '*', '1.', '2.']),
                content_type=mime_content_type,  # 使用转换后的MIME类型
                target_chunk_size=getattr(config, 'target_chunk_size', 1000),
                overlap_size=getattr(config, 'overlap_size', 200),
                metadata=chunking_config or {}
            )
            
            # 执行分块
            if config.mode == ChunkingMode.AUTO:
                # 自动选择最佳策略
                result = await self.chunking_factory.chunk_document(context)
            else:
                # 使用指定策略
                strategy_name = self._convert_mode_to_strategy_name(config.mode)
                result = await self.chunking_factory.chunk_document(context, strategy_name)
            
            # 转换为DocumentChunk对象
            document_chunks = []
            for i, chunk in enumerate(result.chunks):
                doc_chunk = DocumentChunk(
                    id=str(uuid4()),
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk.content,
                    metadata={
                        'start_char': chunk.start_char,
                        'end_char': chunk.end_char,
                        'token_count': getattr(chunk, 'token_count', len(chunk.content.split())),
                        'quality_score': getattr(chunk, 'quality_score', 0.0),
                        'strategy': result.strategy_used,
                    }
                )
                document_chunks.append(doc_chunk)
            
            details = {
                'strategy_used': result.strategy_used,
                'quality_score': result.quality_score,
                'processing_time_ms': result.processing_time_ms,
                'chunk_count': result.chunk_count,
                'average_chunk_size': sum(len(c.content) for c in document_chunks) / len(document_chunks) if document_chunks else 0,
            }
            
            return document_chunks, details
            
        except Exception as e:
            logger.error(f"分块处理失败: {e}")
            raise RAGProcessingError(f"分块处理失败: {e}", stage="chunking")
    
    async def _generate_embeddings(
        self, chunks: List[DocumentChunk]
    ) -> List[List[float]]:
        """生成嵌入向量"""
        if not self.embedding_service:
            raise RAGProcessingError("嵌入服务未配置", stage="embedding")
        
        try:
            # 提取文本内容
            texts = [chunk.content for chunk in chunks]
            
            # 批量生成嵌入
            embeddings = []
            batch_size = self.config.batch_size
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                async with self._processing_semaphore:
                    # 生成当前批次的嵌入
                    batch_result = await self.embedding_service.generate_embeddings(batch_texts)
                    embeddings.extend(batch_result.vectors)
                
                logger.debug(f"嵌入生成进度: {len(embeddings)}/{len(texts)}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"嵌入生成失败: {e}")
            raise RAGProcessingError(f"嵌入生成失败: {e}", stage="embedding")
    
    async def _store_vectors(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        document: Document,
        topic_id: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> int:
        """存储向量到向量数据库"""
        if not self.vector_store:
            raise RAGProcessingError("向量存储服务未配置", stage="vector_storage")
        
        try:
            # 创建向量文档
            vector_documents = []
            for chunk, embedding in zip(chunks, embeddings):
                vector_doc = VectorDocument(
                    id=chunk.id,
                    vector=embedding,
                    content=chunk.content,
                    metadata={
                        'document_id': document.id,
                        'chunk_index': chunk.chunk_index,
                        'content_type': document.content_type.value if hasattr(document.content_type, 'value') else str(document.content_type),
                        'topic_id': topic_id,
                        'file_id': file_id,
                        'title': document.title,
                        'chunk_metadata': chunk.metadata,
                        'created_at': document.created_at.isoformat() if hasattr(document, 'created_at') else None,
                        'collection_name': self.config.collection_name,  # 移到metadata中
                    },
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                )
                vector_documents.append(vector_doc)
            
            # 批量上传向量
            result = await self.vector_store.upsert_vectors(vector_documents)
            
            if result.failed_count > 0:
                logger.warning(f"向量存储部分失败: {result.failed_count}/{len(vector_documents)}")
            
            return result.success_count
            
        except Exception as e:
            logger.error(f"向量存储失败: {e}")
            raise RAGProcessingError(f"向量存储失败: {e}", stage="vector_storage")
    
    def _parse_chunking_config(
        self, chunking_config: Optional[Dict[str, Any]] = None
    ) -> RuntimeChunkingConfig:
        """解析分块配置"""
        if not chunking_config:
            return RuntimeChunkingConfig(mode=ChunkingMode.AUTO)
        
        # 解析推荐策略
        recommended_strategy = chunking_config.get('recommended_strategy', 'auto')
        
        # 转换为ChunkingMode
        mode_mapping = {
            'fixed_size': ChunkingMode.FIXED_SIZE,
            'semantic': ChunkingMode.SEMANTIC,
            'paragraph': ChunkingMode.PARAGRAPH,
            'sentence': ChunkingMode.SENTENCE,
            'adaptive': ChunkingMode.ADAPTIVE,
            'auto': ChunkingMode.AUTO,
        }
        
        mode = mode_mapping.get(recommended_strategy, ChunkingMode.AUTO)
        
        return RuntimeChunkingConfig(
            mode=mode,
            target_chunk_size=chunking_config.get('chunk_size', 1000),
            overlap_size=chunking_config.get('overlap', 200),
        )
    
    def _convert_mode_to_strategy_name(self, mode: ChunkingMode) -> str:
        """转换模式为策略名称"""
        mapping = {
            ChunkingMode.FIXED_SIZE: 'fixed_size',
            ChunkingMode.SEMANTIC: 'semantic', 
            ChunkingMode.PARAGRAPH: 'paragraph',
            ChunkingMode.SENTENCE: 'sentence',
            ChunkingMode.ADAPTIVE: 'adaptive',
        }
        return mapping.get(mode, 'fixed_size')
    
    def _calculate_quality_score(
        self, chunks: List[DocumentChunk], chunking_details: Dict[str, Any]
    ) -> float:
        """计算处理质量分数"""
        if not chunks:
            return 0.0
        
        # 基础质量分数（来自分块过程）
        base_score = chunking_details.get('quality_score', 0.5)
        
        # 块数量评分
        chunk_count_score = min(1.0, len(chunks) / 50)  # 假设50个块是理想数量
        
        # 块大小一致性评分
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
        size_consistency_score = max(0, 1 - (size_variance / (avg_size ** 2)))
        
        # 综合评分
        final_score = (base_score * 0.6 + chunk_count_score * 0.2 + size_consistency_score * 0.2)
        
        return min(1.0, max(0.0, final_score))
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            'rag_processor': 'healthy',
            'initialized': self._initialized,
            'config': {
                'embedding_provider': self.config.embedding_provider,
                'vector_store_provider': self.config.vector_store_provider,
                'collection_name': self.config.collection_name,
            }
        }
        
        # 检查嵌入服务
        if self.embedding_service:
            try:
                embedding_health = await self.embedding_service.health_check()
                status['embedding_service'] = embedding_health
            except Exception as e:
                status['embedding_service'] = {'status': 'unhealthy', 'error': str(e)}
        else:
            status['embedding_service'] = {'status': 'not_configured'}
        
        # 检查向量存储
        if self.vector_store:
            try:
                vector_store_health = await self.vector_store.health_check()
                status['vector_store'] = vector_store_health
            except Exception as e:
                status['vector_store'] = {'status': 'unhealthy', 'error': str(e)}
        else:
            status['vector_store'] = {'status': 'not_configured'}
        
        return status
