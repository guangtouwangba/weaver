"""
文件处理相关任务处理器

包含文件系统操作的各种异步任务处理器：
- 文件上传完成后处理
- 文件内容分析
- 文件格式转换
- 文件清理
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import ITaskHandler, TaskConfig, TaskPriority
from ... import schemas
from ...services.task_service import task_handler, register_task_handler
from ...storage import IStorage, MinIOStorage, LocalStorage
from ...storage.base import create_storage_service
from ...database import get_db_session
from ...services.document_service import DocumentService
from ...file_loader.multi_format_loader import load_document_from_path
from ...models import Document
from ...schemas.document import DocumentCreate
from ...schemas.enums import ContentType

logger = logging.getLogger(__name__)


@task_handler(schemas.TaskName.FILE_UPLOAD_CONFIRM,
              priority=TaskPriority.HIGH,
              max_retries=3,
              timeout=300,
              queue="file_queue")
@register_task_handler
class FileUploadCompleteHandler(ITaskHandler):
    """文件上传完成处理器 - 触发后续RAG处理流程"""
    
    @property
    def task_name(self) -> str:
        return schemas.TaskName.FILE_UPLOAD_CONFIRM
    
    async def handle(self,
                    file_id: str,
                    file_path: str,
                    **metadata) -> Dict[str, Any]:
        """
        处理文件上传完成事件
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
            **metadata: 其他元数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            logger.info(f"处理文件上传完成: {file_id}, 文件存储键: {file_path}")
            
            # 创建存储服务实例
            storage = create_storage_service()
            
            # 使用存储服务检查文件是否存在
            file_exists = await storage.file_exists(file_path)
            if not file_exists:
                raise FileNotFoundError(f"文件在存储中不存在: {file_path}")
            
            # 获取文件信息
            file_info = await storage.get_file_info(file_path)
            if not file_info:
                logger.warning(f"无法获取文件信息: {file_path}")
                file_info = {"size": 0}
            
            file_size = file_info.get("size", 0)
            logger.info(f"文件大小: {file_size} bytes")
            
            # ===== 新增：文档处理和RAG流程 =====
            document_processing_result = await self._process_document_with_rag(
                file_id=file_id,
                file_path=file_path,
                file_size=file_size,
                storage=storage,
                **metadata
            )
            
            # 可以在这里触发其他任务，比如其他后处理
            tasks_triggered = []
            if document_processing_result.get("success"):
                tasks_triggered.append("document_processing_rag")
            
            result = {
                "success": True,
                "file_id": file_id,
                "file_path": file_path,
                "storage_provider": storage.__class__.__name__,
                "file_size": file_size,
                "file_info": file_info,
                "processed_at": datetime.utcnow().isoformat(),
                "tasks_triggered": tasks_triggered,
                "document_processing": document_processing_result
            }
            
            logger.info(f"文件上传完成处理成功: {file_id}")
            return result

        except Exception as e:
            logger.error(f"文件上传完成处理失败: {file_id}, {e}")
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def _process_document_with_rag(self, 
                                       file_id: str,
                                       file_path: str, 
                                       file_size: int,
                                       storage: IStorage,
                                       **metadata) -> Dict[str, Any]:
        """
        处理文档：读取、分片、创建embedding和存入vector database
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
            file_size: 文件大小
            storage: 存储服务
            **metadata: 其他元数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            logger.info(f"开始RAG文档处理: {file_id}")
            
            # 1. 从存储中下载文件到临时位置
            temp_file_path = await self._download_file_to_temp(storage, file_path, file_id)
            
            try:
                # 2. 使用文件加载器读取文档内容
                document = await self._load_document(temp_file_path, file_id, metadata)
                logger.info(f"文档加载成功: {document.title}, 内容长度: {len(document.content)}")
                
                # 3. 创建文档记录并触发RAG处理
                rag_result = await self._create_document_and_process_rag(
                    document=document,
                    file_id=file_id,
                    file_path=file_path,
                    file_size=file_size,
                    metadata=metadata
                )
                
                logger.info(f"RAG处理完成: {file_id}, request_id: {rag_result.get('rag_request_id')}")
                
                return {
                    "success": True,
                    "document_id": rag_result.get("document_id"),
                    "rag_request_id": rag_result.get("rag_request_id"),
                    "document_title": document.title,
                    "content_length": len(document.content),
                    "content_type": document.content_type.value if hasattr(document.content_type, 'value') else str(document.content_type),
                    "processed_at": datetime.utcnow().isoformat()
                }
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.debug(f"临时文件已删除: {temp_file_path}")
            
        except Exception as e:
            logger.error(f"RAG文档处理失败: {file_id}, {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def _download_file_to_temp(self, storage: IStorage, file_path: str, file_id: str) -> str:
        """从存储中下载文件到临时目录"""
        import tempfile
        import aiofiles
        
        # 创建临时文件
        suffix = os.path.splitext(file_path)[1] or '.tmp'
        temp_fd, temp_file_path = tempfile.mkstemp(suffix=suffix, prefix=f"rag_process_{file_id}_")
        os.close(temp_fd)
        
        try:
            # 从存储中读取文件内容
            file_content = await storage.read_file(file_path)
            
            # 写入临时文件
            async with aiofiles.open(temp_file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.debug(f"文件已下载到临时位置: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise Exception(f"下载文件到临时目录失败: {e}")
    
    async def _load_document(self, file_path: str, file_id: str, metadata: Dict[str, Any]) -> Document:
        """使用文件加载器加载文档"""
        try:
            # 使用多格式文件加载器
            document = await load_document_from_path(
                file_path=file_path,
                extract_metadata=True
            )
            
            # 补充元数据
            document.metadata.update({
                "file_id": file_id,
                "original_file_path": file_path,
                "processing_timestamp": datetime.utcnow().isoformat(),
                **metadata
            })
            
            return document
            
        except Exception as e:
            raise Exception(f"文档加载失败: {e}")
    
    async def _create_document_and_process_rag(self, 
                                             document: Document,
                                             file_id: str,
                                             file_path: str,
                                             file_size: int,
                                             metadata: Dict[str, Any]) -> Dict[str, Any]:
        """创建文档记录并触发RAG处理"""
        # 获取数据库会话
        async with get_db_session() as session:
            try:
                # 创建文档服务
                document_service = DocumentService(session=session, enable_rag=True)
                
                # 初始化RAG管道（如果还未初始化）
                try:
                    await document_service.initialize_rag_pipeline(
                        embedding_provider="openai",
                        vector_store_provider="weaviate"
                    )
                except Exception as e:
                    logger.warning(f"RAG管道初始化失败，将使用传统处理: {e}")
                
                # 创建文档创建请求
                document_create = DocumentCreate(
                    id=document.id,
                    title=document.title or f"Document from {file_id}",
                    content=document.content,
                    content_type=self._map_content_type(document.content_type),
                    file_id=file_id,
                    file_path=file_path,
                    file_size=file_size,
                    doc_metadata=document.metadata
                )
                
                # 创建文档并触发RAG处理
                topic_id = metadata.get("topic_id")
                document_response = await document_service.create_document_with_rag(
                    document_data=document_create,
                    trigger_rag_processing=True,
                    topic_id=topic_id
                )
                
                # 提交事务
                await session.commit()
                
                return {
                    "document_id": document_response.id,
                    "rag_request_id": document_response.doc_metadata.get("rag_request_id"),
                    "rag_processing_triggered": document_response.doc_metadata.get("rag_processing_triggered", False)
                }
                
            except Exception as e:
                await session.rollback()
                raise Exception(f"文档创建和RAG处理失败: {e}")
    
    def _map_content_type(self, content_type) -> str:
        """映射内容类型到字符串"""
        if hasattr(content_type, 'value'):
            return content_type.value
        elif isinstance(content_type, str):
            return content_type
        else:
            return "text"

@task_handler("file.analyze_content",
              priority=TaskPriority.NORMAL,
              max_retries=2,
              timeout=180,
              queue="file_queue")
@register_task_handler
class FileContentAnalysisHandler(ITaskHandler):
    """文件内容分析处理器"""
    
    @property
    def task_name(self) -> str:
        return "file.analyze_content"
    
    async def handle(self,
                    file_id: str,
                    file_path: str,
                    content_type: str,
                    original_name: str,
                    **config) -> Dict[str, Any]:
        """
        分析文件内容
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
            content_type: 内容类型
            original_name: 原始文件名
            **config: 其他配置
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            logger.info(f"开始分析文件内容: {file_id}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 基本文件信息
            file_stats = os.stat(file_path)
            
            analysis_result = {
                "success": True,
                "file_id": file_id,
                "file_path": file_path,
                "original_name": original_name,
                "content_type": content_type,
                "file_size": file_stats.st_size,
                "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            # 文件扩展名分析
            file_extension = os.path.splitext(original_name)[1].lower()
            analysis_result["file_extension"] = file_extension
            
            # 内容类型特定分析
            if content_type.startswith("text/"):
                # 文本文件分析
                text_analysis = await self._analyze_text_file(file_path)
                analysis_result.update(text_analysis)
                
            elif content_type == "application/pdf":
                # PDF文件分析
                pdf_analysis = await self._analyze_pdf_file(file_path)
                analysis_result.update(pdf_analysis)
                
            elif content_type.startswith("image/"):
                # 图片文件分析
                image_analysis = await self._analyze_image_file(file_path)
                analysis_result.update(image_analysis)
            
            # 安全性检查
            security_check = await self._security_check(file_path, content_type)
            analysis_result["security"] = security_check
            
            logger.info(f"文件内容分析完成: {file_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"文件内容分析失败: {file_id}, {e}")
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def _analyze_text_file(self, file_path: str) -> Dict[str, Any]:
        """分析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "content_length": len(content),
                "line_count": content.count('\n') + 1,
                "word_count": len(content.split()),
                "character_encoding": "utf-8",
                "is_empty": len(content.strip()) == 0
            }
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return {
                    "content_length": len(content),
                    "line_count": content.count('\n') + 1,
                    "word_count": len(content.split()),
                    "character_encoding": "gbk",
                    "is_empty": len(content.strip()) == 0
                }
            except:
                return {"text_analysis_error": "无法识别字符编码"}
        except Exception as e:
            return {"text_analysis_error": str(e)}
    
    async def _analyze_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """分析PDF文件"""
        try:
            # 这里可以使用PyPDF2或其他PDF库进行分析
            # 简化实现，只返回基本信息
            return {
                "is_pdf": True,
                "pdf_analysis": "PDF analysis requires additional dependencies"
            }
        except Exception as e:
            return {"pdf_analysis_error": str(e)}
    
    async def _analyze_image_file(self, file_path: str) -> Dict[str, Any]:
        """分析图片文件"""
        try:
            # 这里可以使用PIL或其他图像库进行分析
            # 简化实现，只返回基本信息
            return {
                "is_image": True,
                "image_analysis": "Image analysis requires additional dependencies"
            }
        except Exception as e:
            return {"image_analysis_error": str(e)}
    
    async def _security_check(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """安全性检查"""
        try:
            file_size = os.path.getsize(file_path)
            
            # 基本安全检查
            security_result = {
                "is_safe": True,
                "file_size_ok": file_size < 100 * 1024 * 1024,  # 100MB限制
                "content_type_safe": content_type not in ["application/x-executable"],
                "warnings": []
            }
            
            if file_size > 100 * 1024 * 1024:
                security_result["warnings"].append("文件大小超过100MB")
                security_result["is_safe"] = False
            
            if content_type == "application/x-executable":
                security_result["warnings"].append("可执行文件类型")
                security_result["is_safe"] = False
            
            return security_result
            
        except Exception as e:
            return {
                "is_safe": False,
                "security_check_error": str(e)
            }


@task_handler("file.cleanup_temp",
              priority=TaskPriority.LOW,
              max_retries=1,
              timeout=60,
              queue="cleanup_queue")
@register_task_handler
class TempFileCleanupHandler(ITaskHandler):
    """临时文件清理处理器"""
    
    @property
    def task_name(self) -> str:
        return "file.cleanup_temp"
    
    async def handle(self,
                    file_paths: List[str],
                    max_age_hours: int = 24,
                    **config) -> Dict[str, Any]:
        """
        清理临时文件
        
        Args:
            file_paths: 文件路径列表
            max_age_hours: 最大保留时间(小时)
            **config: 其他配置
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        try:
            logger.info(f"开始清理临时文件: {len(file_paths)} 个文件")
            
            deleted_files = []
            failed_files = []
            skipped_files = []
            
            current_time = datetime.utcnow().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in file_paths:
                try:
                    if not os.path.exists(file_path):
                        skipped_files.append({"path": file_path, "reason": "文件不存在"})
                        continue
                    
                    # 检查文件年龄
                    file_mtime = os.path.getmtime(file_path)
                    file_age = current_time - file_mtime
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        deleted_files.append({
                            "path": file_path,
                            "age_hours": file_age / 3600
                        })
                        logger.debug(f"已删除临时文件: {file_path}")
                    else:
                        skipped_files.append({
                            "path": file_path,
                            "reason": f"文件太新 ({file_age/3600:.1f}小时)"
                        })
                
                except Exception as e:
                    failed_files.append({
                        "path": file_path,
                        "error": str(e)
                    })
                    logger.error(f"删除文件失败: {file_path}, {e}")
            
            result = {
                "success": True,
                "total_files": len(file_paths),
                "deleted_count": len(deleted_files),
                "failed_count": len(failed_files),
                "skipped_count": len(skipped_files),
                "deleted_files": deleted_files,
                "failed_files": failed_files,
                "skipped_files": skipped_files,
                "cleaned_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"临时文件清理完成: 删除 {len(deleted_files)}, 失败 {len(failed_files)}, 跳过 {len(skipped_files)}")
            return result
            
        except Exception as e:
            logger.error(f"临时文件清理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat()
            }


@task_handler("file.convert_format",
              priority=TaskPriority.NORMAL,
              max_retries=2,
              timeout=300,
              queue="file_queue")
@register_task_handler  
class FileFormatConversionHandler(ITaskHandler):
    """文件格式转换处理器"""
    
    @property
    def task_name(self) -> str:
        return "file.convert_format"
    
    async def handle(self,
                    source_file: str,
                    target_format: str,
                    output_path: Optional[str] = None,
                    **config) -> Dict[str, Any]:
        """
        转换文件格式
        
        Args:
            source_file: 源文件路径
            target_format: 目标格式(如 'pdf', 'txt', 'html')
            output_path: 输出文件路径
            **config: 其他配置
            
        Returns:
            Dict[str, Any]: 转换结果
        """
        try:
            logger.info(f"开始文件格式转换: {source_file} -> {target_format}")
            
            if not os.path.exists(source_file):
                raise FileNotFoundError(f"源文件不存在: {source_file}")
            
            # 生成输出路径
            if not output_path:
                base_name = os.path.splitext(source_file)[0]
                output_path = f"{base_name}.{target_format}"
            
            # 根据目标格式进行转换
            conversion_result = await self._convert_file(source_file, target_format, output_path, config)
            
            if conversion_result["success"]:
                # 验证输出文件
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    conversion_result.update({
                        "output_path": output_path,
                        "output_size": output_size,
                        "converted_at": datetime.utcnow().isoformat()
                    })
                else:
                    conversion_result = {
                        "success": False,
                        "error": "转换完成但输出文件未生成"
                    }
            
            logger.info(f"文件格式转换完成: {source_file}")
            return conversion_result
            
        except Exception as e:
            logger.error(f"文件格式转换失败: {source_file}, {e}")
            return {
                "success": False,
                "source_file": source_file,
                "target_format": target_format,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def _convert_file(self, source_file: str, target_format: str, 
                          output_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件转换"""
        try:
            source_ext = os.path.splitext(source_file)[1].lower()
            
            # 简化实现 - 仅支持基本的文本转换
            if target_format == "txt" and source_ext in [".txt", ".md"]:
                # 直接复制文本文件
                with open(source_file, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(output_path, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                
                return {
                    "success": True,
                    "conversion_type": "text_copy",
                    "source_format": source_ext[1:],
                    "target_format": target_format
                }
            
            else:
                # 其他转换需要额外的库支持
                return {
                    "success": False,
                    "error": f"不支持的转换: {source_ext} -> {target_format}",
                    "supported_conversions": ["txt->txt", "md->txt"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"转换执行失败: {str(e)}"
            }


logger.info("文件任务处理器模块已加载")