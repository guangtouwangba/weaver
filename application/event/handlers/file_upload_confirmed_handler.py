"""
File Upload Confirmed Event Handler

文件上传确认事件处理器，负责：
1. 接收文件上传确认事件
2. 触发RAG文档处理流程
3. 管理处理状态和错误处理
4. 发布后续事件

这是一个应用级事件处理器，负责跨聚合的复杂业务编排。
"""

import logging
from typing import Optional
from datetime import datetime

# 应用层依赖
from application.event.event_handler import EventHandler
from application.dtos.knowledge.requests import DocumentIngestionRequest, DocumentProcessingRequest
from application.dtos.knowledge.responses import DocumentIngestionResponse

# 领域层依赖
from domain.shared.domain_event import DomainEvent
from domain.shared.event_types import EventType
from domain.file.event import FileUploadedConfirmEvent
from domain.knowledge import ProcessingStatus, ChunkingStrategy

# 服务层依赖
from services.knowledge_orchestration import KnowledgeOrchestrationService

# 事件总线
from application.event.event_bus import EventBus

logger = logging.getLogger(__name__)


class FileUploadConfirmedHandler(EventHandler):
    """
    文件上传确认事件处理器
    
    处理文件上传完成后的后续流程：
    1. 文档内容读取
    2. RAG处理和索引
    3. 状态更新
    4. 通知发送
    """
    
    def __init__(self, 
                 knowledge_orchestration_service: KnowledgeOrchestrationService,
                 event_bus: EventBus):
        """
        初始化事件处理器
        
        Args:
            knowledge_orchestration_service: 知识编排服务
            event_bus: 事件总线
        """
        self.knowledge_orchestration_service = knowledge_orchestration_service
        self.event_bus = event_bus
    
    @property
    def event_type(self) -> str:
        """处理的事件类型"""
        return EventType.FILE_CONFIRMED.value
    
    async def handle(self, event: DomainEvent) -> None:
        """
        处理文件上传确认事件
        
        Args:
            event: 文件上传确认事件
        """
        try:
            # 类型检查
            if not isinstance(event, FileUploadedConfirmEvent):
                logger.error(f"Expected FileUploadedConfirmEvent, got {type(event)}")
                return
            
            logger.info(f"Processing file upload confirmation for file {event.file_id}")
            
            # 1. 提取事件信息
            file_entity = event.file
            file_id = file_entity.id
            storage_location = file_entity.storage_location
            content_type = file_entity.content_type
            metadata = file_entity.metadata
            
            # 2. 创建文档摄取请求
            storage_location_str = storage_location.full_path if hasattr(storage_location, 'full_path') else str(storage_location)
            metadata_dict = metadata.get if hasattr(metadata, 'get') else metadata if isinstance(metadata, dict) else {}
            content_type_str = content_type if isinstance(content_type, str) else metadata_dict.get('content_type', 'application/octet-stream')
            
            ingestion_request = DocumentIngestionRequest(
                source_location=storage_location_str,
                title=metadata_dict.get('original_name', f"Document_{file_id}"),
                content_type=content_type_str,
                metadata={
                    'file_id': file_id,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                    'original_metadata': metadata_dict,
                    'auto_triggered': True
                },
                process_immediately=False  # 先摄取，再异步处理
            )
            
            # 3. 执行文档摄取
            ingestion_result = await self.knowledge_orchestration_service.ingest_document(
                ingestion_request
            )
            
            if not ingestion_result.success:
                logger.error(f"Document ingestion failed for file {file_id}: {ingestion_result.message}")
                await self._handle_ingestion_failure(file_id, ingestion_result.errors)
                return
            
            document_id = ingestion_result.document_id
            logger.info(f"Document ingested successfully: {document_id}")
            
            # 4. 创建文档处理请求
            processing_request = DocumentProcessingRequest(
                document_id=document_id,
                generate_embeddings=True,
                chunking_strategy=ChunkingStrategy.FIXED_SIZE,
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # 5. 异步启动文档处理
            await self._start_async_processing(processing_request, file_id)
            
            logger.info(f"File upload confirmation processing completed for file {file_id}")
            
        except Exception as e:
            logger.error(f"Error handling file upload confirmation: {e}", exc_info=True)
            await self._handle_processing_error(event, e)
    
    async def _start_async_processing(self, 
                                    processing_request: DocumentProcessingRequest, 
                                    file_id: str) -> None:
        """
        异步启动文档处理
        
        Args:
            processing_request: 文档处理请求
            file_id: 文件ID
        """
        try:
            logger.info(f"Starting async document processing for file {file_id}")
            
            # 执行文档处理
            processing_result = await self.knowledge_orchestration_service.process_document(
                processing_request
            )
            
            if processing_result.success:
                logger.info(f"Document processing completed successfully for file {file_id}")
                logger.info(f"Created {processing_result.chunks_created} chunks in {processing_result.processing_time_ms}ms")
                
                # 发布处理成功事件
                await self._publish_processing_success_event(
                    file_id, 
                    processing_result.document_id, 
                    processing_result.chunks_created
                )
            else:
                logger.error(f"Document processing failed for file {file_id}: {processing_result.message}")
                await self._publish_processing_failure_event(
                    file_id, 
                    processing_result.errors
                )
                
        except Exception as e:
            logger.error(f"Async document processing failed for file {file_id}: {e}", exc_info=True)
            await self._publish_processing_failure_event(file_id, [str(e)])
    
    async def _handle_ingestion_failure(self, file_id: str, errors: list) -> None:
        """
        处理文档摄取失败
        
        Args:
            file_id: 文件ID
            errors: 错误列表
        """
        logger.error(f"Document ingestion failed for file {file_id}")
        
        # 发布摄取失败事件
        from domain.knowledge import DocumentProcessingFailed
        
        failure_event = DocumentProcessingFailed(
            document_id=f"failed_{file_id}",
            error_message=f"Ingestion failed: {'; '.join(errors)}",
            occurred_at=datetime.utcnow()
        )
        
        await self.event_bus.publish(failure_event)
    
    async def _handle_processing_error(self, original_event: DomainEvent, error: Exception) -> None:
        """
        处理事件处理过程中的错误
        
        Args:
            original_event: 原始事件
            error: 错误信息
        """
        logger.error(f"File upload confirmation handler failed: {error}")
        
        try:
            # 记录错误详情
            error_details = {
                'event_id': original_event.event_id,
                'event_type': original_event.event_type,
                'error_message': str(error),
                'error_type': type(error).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 发布错误处理事件
            from domain.shared.domain_event import DomainEvent
            from domain.shared.event_types import EventType
            
            error_event = DomainEvent(
                event_type=EventType.FILE_FAILED,
                original_event_id=original_event.event_id,
                error_details=error_details
            )
            
            await self.event_bus.publish(error_event)
            logger.info(f"Published error event for failed processing: {original_event.event_id}")
            
        except Exception as publish_error:
            logger.error(f"Failed to publish error event: {publish_error}")
            
        # TODO: 实现重试机制
        # TODO: 记录到死信队列
        # TODO: 发送告警
    
    async def _publish_processing_success_event(self, 
                                              file_id: str, 
                                              document_id: str, 
                                              chunks_created: int) -> None:
        """
        发布处理成功事件
        
        Args:
            file_id: 文件ID
            document_id: 文档ID
            chunks_created: 创建的块数量
        """
        try:
            from domain.knowledge import DocumentProcessed
            
            success_event = DocumentProcessed(
                document_id=document_id,
                chunk_count=chunks_created,
                processing_time_ms=0,  # 可以从处理结果中获取
                occurred_at=datetime.utcnow()
            )
            
            await self.event_bus.publish(success_event)
            logger.debug(f"Published processing success event for file {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish processing success event: {e}")
    
    async def _publish_processing_failure_event(self, 
                                              file_id: str, 
                                              errors: list) -> None:
        """
        发布处理失败事件
        
        Args:
            file_id: 文件ID
            errors: 错误列表
        """
        try:
            from domain.knowledge import DocumentProcessingFailed
            
            failure_event = DocumentProcessingFailed(
                document_id=f"failed_{file_id}",
                error_message=f"Processing failed: {'; '.join(errors)}",
                occurred_at=datetime.utcnow()
            )
            
            await self.event_bus.publish(failure_event)
            logger.debug(f"Published processing failure event for file {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish processing failure event: {e}")


class FileProcessingStatusHandler(EventHandler):
    """
    文件处理状态事件处理器
    
    负责处理文档处理完成/失败的后续事件，如通知、清理等。
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    @property
    def event_type(self) -> str:
        """处理多种事件类型"""
        return "document_processing_status"  # 这是一个伪类型，实际注册时会针对具体事件类型
    
    async def handle_document_processed(self, event: DomainEvent) -> None:
        """处理文档处理完成事件"""
        logger.info(f"Document {event.document_id} processed successfully with {event.chunk_count} chunks")
        
        # TODO: 发送成功通知
        # TODO: 更新UI状态
        # TODO: 记录处理统计
    
    async def handle_document_processing_failed(self, event: DomainEvent) -> None:
        """处理文档处理失败事件"""
        logger.error(f"Document processing failed: {event.error_message}")
        
        # TODO: 发送失败通知
        # TODO: 记录错误统计
        # TODO: 触发人工干预流程