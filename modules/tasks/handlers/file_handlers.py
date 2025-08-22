"""
File processing task handlers

Contains various async task handlers for file system operations:
- Post-upload file processing
- File content analysis
- File format conversion
- File cleanup
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from modules import schemas
from modules.file_loader.factory import FileLoaderFactory
from modules.models import Document, FileLoadRequest
from modules.schemas.enums import ContentType

from ...services.task_service import register_task_handler, task_handler
from ...storage.base import create_storage_service

logger = logging.getLogger(__name__)


async def load_document_from_path_with_factory(file_path: str, **kwargs) -> Document:
    """
    Factory pattern implementation for loading documents from file path

    Args:
        file_path: File path
        **kwargs: Additional parameters

    Returns:
        Document: Loaded document
    """
    # Build metadata including all additional parameters
    metadata = kwargs.get("metadata", {})
    metadata.update(
        {
            "encoding": kwargs.get("encoding", "utf-8"),
            "max_file_size_mb": kwargs.get("max_file_size_mb", 100),
            "extract_metadata": kwargs.get("extract_metadata", True),
            "custom_params": kwargs.get("custom_params", {}),
        }
    )

    # Determine content type
    content_type = kwargs.get("content_type")
    if content_type is None:
        # Infer content type from file extension
        import os

        ext = os.path.splitext(file_path)[1].lower()
        content_type_mapping = {
            ".pdf": ContentType.PDF,
            ".txt": ContentType.TXT,
            ".doc": ContentType.DOC,
            ".docx": ContentType.DOCX,
            ".html": ContentType.HTML,
            ".md": ContentType.MD,
            ".json": ContentType.JSON,
            ".csv": ContentType.CSV,
        }
        content_type = content_type_mapping.get(ext, ContentType.TXT)

    # Convert content_type to ContentType enum if it's a string
    if isinstance(content_type, str):
        try:
            content_type = ContentType(content_type)
        except ValueError:
            content_type = ContentType.TXT

    # Build file load request
    request = FileLoadRequest(
        file_path=file_path,
        content_type=(
            content_type.value if hasattr(content_type, "value") else str(content_type)
        ),
        metadata=metadata,
    )

    # Use factory pattern to get loader and load document
    try:
        loader = FileLoaderFactory.get_loader(content_type)
        document = await loader.load_document(request)

        # Add factory pattern metadata
        document.metadata.update(
            {
                "factory_loader": True,
                "delegate_loader": loader.loader_name,
                "detected_type": (
                    content_type.value
                    if hasattr(content_type, "value")
                    else str(content_type)
                ),
            }
        )

        logger.info(
            f"Loading document using factory pattern {loader.loader_name}: {file_path}"
        )
        return document

    except ValueError as e:
        # If no corresponding loader found, try using text loader as fallback
        logger.warning(
            f"No loader found for content type {content_type}, trying text loader: {e}"
        )
        try:
            text_loader = FileLoaderFactory.get_loader(ContentType.TXT)
            request.content_type = ContentType.TXT.value
            document = await text_loader.load_document(request)
            document.metadata.update(
                {
                    "factory_loader": True,
                    "delegate_loader": text_loader.loader_name,
                    "fallback_loader": True,
                    "original_type": (
                        content_type.value
                        if hasattr(content_type, "value")
                        else str(content_type)
                    ),
                    "detected_type": ContentType.TXT.value,
                }
            )
            return document
        except Exception as fallback_error:
            raise Exception(
                f"Document loading failed, unable to find suitable loader: {e}, text loader fallback also failed: {fallback_error}"
            )
    except Exception as e:
        logger.error(f"Factory pattern document loading failed {file_path}: {e}")
        raise Exception(f"Factory pattern document loading failed: {str(e)}")


@task_handler(
    schemas.TaskName.FILE_UPLOAD_CONFIRM,
    priority=TaskPriority.HIGH,
    max_retries=3,
    timeout=300,
    queue="file_queue",
)
@register_task_handler
class FileUploadCompleteHandler(ITaskHandler):
    """File upload completion handler - triggers subsequent RAG processing pipeline"""

    @property
    def task_name(self) -> str:
        return schemas.TaskName.FILE_UPLOAD_CONFIRM

    async def handle(self, file_id: str, file_path: str, **metadata) -> Dict[str, Any]:
        """
        Handle file upload completion event

        Args:
            file_id: File ID
            file_path: File path
            **metadata: Additional metadata

        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            logger.info(
                f"Processing file upload completion: {file_id}, file storage key: {file_path}"
            )

            # Create storage service instance
            storage = create_storage_service()

            # Use storage service to check if file exists
            file_exists = await storage.file_exists(file_path)
            if not file_exists:
                raise FileNotFoundError(f"File does not exist in storage: {file_path}")

            # Get file information
            file_info = await storage.get_file_info(file_path)
            if not file_info:
                logger.warning(f"Unable to get file information: {file_path}")
                file_info = {"size": 0}

            file_size = file_info.get("size", 0)
            logger.info(f"File size: {file_size} bytes")

            # ===== Added: Document processing and RAG pipeline =====
            document_processing_result = await self._process_document_with_rag(
                file_id=file_id,
                file_path=file_path,
                file_size=file_size,
                storage=storage,
                **metadata,
            )

            # Can trigger other tasks here, such as other post-processing
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
                "document_processing": document_processing_result,
            }

            logger.info(f"File upload completion processing successful: {file_id}")
            return result

        except Exception as e:
            logger.error(f"File upload completion processing failed: {file_id}, {e}")
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat(),
            }

    async def _process_document_with_rag(
        self,
        file_id: str,
        file_path: str,
        file_size: int,
        storage: IStorage,
        **metadata,
    ) -> Dict[str, Any]:
        """
        Process document: read, chunk, create embeddings and store in vector database

        Args:
            file_id: File ID
            file_path: File path
            file_size: File size
            storage: Storage service
            **metadata: Additional metadata

        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            logger.info(f"Starting RAG document processing: {file_id}")

            # 1. Download file from storage to temporary location
            temp_file_path = await self._download_file_to_temp(
                storage, file_path, file_id
            )

            try:
                # 2. Use file loader to read document content
                document = await self._load_document(temp_file_path, file_id, metadata)
                logger.info(
                    f"Document loaded successfully: {document.title}, content length: {len(document.content)}"
                )

                # 3. Create document record and trigger RAG processing
                rag_result = await self._create_document_and_process_rag(
                    document=document,
                    file_id=file_id,
                    file_path=file_path,
                    file_size=file_size,
                    metadata=metadata,
                )

                logger.info(
                    f"RAG processing completed: {file_id}, request_id: {rag_result.get('rag_request_id')}"
                )

                return {
                    "success": True,
                    "document_id": rag_result.get("document_id"),
                    "rag_request_id": rag_result.get("rag_request_id"),
                    "document_title": document.title,
                    "content_length": len(document.content),
                    "content_type": (
                        document.content_type.value
                        if hasattr(document.content_type, "value")
                        else str(document.content_type)
                    ),
                    "processed_at": datetime.utcnow().isoformat(),
                }

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.debug(f"Temporary file deleted: {temp_file_path}")

        except Exception as e:
            logger.error(f"RAG document processing failed: {file_id}, {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat(),
            }

    async def _download_file_to_temp(
        self, storage: IStorage, file_path: str, file_id: str
    ) -> str:
        """Download file from storage to temporary directory"""
        import tempfile

        import aiofiles

        # Create temporary file
        suffix = os.path.splitext(file_path)[1] or ".tmp"
        temp_fd, temp_file_path = tempfile.mkstemp(
            suffix=suffix, prefix=f"rag_process_{file_id}_"
        )
        os.close(temp_fd)

        try:
            # Read file content from storage
            file_content = await storage.read_file(file_path)

            # Write to temporary file
            async with aiofiles.open(temp_file_path, "wb") as f:
                await f.write(file_content)

            logger.debug(f"File downloaded to temporary location: {temp_file_path}")
            return temp_file_path

        except Exception as e:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise Exception(f"Failed to download file to temporary directory: {e}")

    async def _load_document(
        self, file_path: str, file_id: str, metadata: Dict[str, Any]
    ) -> Document:
        """Load document using factory pattern file loader"""
        try:
            # Use factory pattern file loader
            document = await load_document_from_path_with_factory(
                file_path=file_path, extract_metadata=True
            )

            # Add metadata
            document.metadata.update(
                {
                    "file_id": file_id,
                    "original_file_path": file_path,
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    **metadata,
                }
            )

            return document

        except Exception as e:
            raise Exception(f"Document loading failed: {e}")

    async def _create_document_and_process_rag(
        self,
        document: Document,
        file_id: str,
        file_path: str,
        file_size: int,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create document record and trigger RAG processing"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # Create a new event loop for this task to avoid greenlet issues
        def run_sync_db_operations():
            """Run database operations in a new event loop to avoid greenlet spawn issues"""
            # Create a new event loop for this worker thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)

            try:
                return new_loop.run_until_complete(
                    self._create_document_with_new_loop(
                        document=document,
                        file_id=file_id,
                        file_path=file_path,
                        file_size=file_size,
                        metadata=metadata,
                    )
                )
            finally:
                # Clean up the event loop
                new_loop.close()

        # Execute in a thread pool to isolate from Celery's worker context
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_sync_db_operations)
            return future.result()

    async def _create_document_with_new_loop(
        self,
        document: Document,
        file_id: str,
        file_path: str,
        file_size: int,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Helper method to create document using synchronous SQLAlchemy in worker context"""
        import json

        import sqlalchemy as sa
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        from config import get_config
        from modules.database.models import Document as DocumentModel

        config = get_config()

        # Use synchronous SQLAlchemy to avoid async context issues in Celery
        sync_engine = create_engine(
            config.database.url.replace("postgresql+asyncpg", "postgresql+psycopg2"),
            echo=False,
        )

        SessionLocal = sessionmaker(bind=sync_engine)

        with SessionLocal() as session:
            try:
                # Create document record directly using synchronous SQLAlchemy
                doc_metadata = document.metadata or {}
                doc_metadata.update(
                    {
                        "rag_processing_pending": True,
                        "celery_processed": True,
                        "created_in_worker": True,
                    }
                )

                document_model = DocumentModel(
                    id=document.id,
                    title=document.title or f"Document from {file_id}",
                    content=document.content,
                    content_type=self._map_content_type(document.content_type),
                    file_id=file_id,
                    file_path=file_path,
                    file_size=file_size,
                    doc_metadata=doc_metadata,
                )

                session.add(document_model)
                session.commit()

                logger.info(
                    f"Document created using sync SQLAlchemy: {document_model.title} (ID: {document_model.id})"
                )

                # Trigger separate RAG processing task using Celery directly
                topic_id = metadata.get("topic_id")
                try:
                    from celery import current_app

                    # Use Celery directly to submit the RAG task
                    rag_task = current_app.send_task(
                        "rag.process_document_async",
                        args=[],
                        kwargs={
                            "file_id": file_id,
                            "document_id": str(document_model.id),
                            "file_path": file_path,
                            "content_type": self._map_content_type(
                                document.content_type
                            ),
                            "topic_id": topic_id,
                            "embedding_provider": "openai",
                            "vector_store_provider": "weaviate",
                        },
                        queue="rag_queue",
                        priority=1,
                    )
                    logger.info(
                        f"RAG processing task submitted for document {document_model.id}: {rag_task.id}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to submit RAG processing task: {e}")
                    logger.info(
                        f"Document {document_model.id} created but RAG processing will need to be manually triggered."
                    )

                return {
                    "document_id": str(document_model.id),
                    "rag_processing_pending": True,
                    "rag_processing_triggered": True,
                    "celery_processed": True,
                    "note": "Document created successfully using sync SQLAlchemy. Separate RAG processing task has been submitted.",
                }

            except Exception as e:
                session.rollback()
                raise Exception(f"Document creation failed: {e}")
            finally:
                session.close()
                sync_engine.dispose()

    def _map_content_type(self, content_type) -> str:
        """Map content type to string"""
        if hasattr(content_type, "value"):
            return content_type.value
        elif isinstance(content_type, str):
            return content_type
        else:
            return "text"


@task_handler(
    "file.analyze_content",
    priority=TaskPriority.NORMAL,
    max_retries=2,
    timeout=180,
    queue="file_queue",
)
@register_task_handler
class FileContentAnalysisHandler(ITaskHandler):
    """File content analysis handler"""

    @property
    def task_name(self) -> str:
        return "file.analyze_content"

    async def handle(
        self,
        file_id: str,
        file_path: str,
        content_type: str,
        original_name: str,
        **config,
    ) -> Dict[str, Any]:
        """
        Analyze file content

        Args:
            file_id: File ID
            file_path: File path
            content_type: Content type
            original_name: Original filename
            **config: Other configurations

        Returns:
            Dict[str, Any]: Analysis result
        """
        try:
            logger.info(f"Start analyzing file content: {file_id}")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File does not exist: {file_path}")

            # Basic file information
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
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            # File extension analysis
            file_extension = os.path.splitext(original_name)[1].lower()
            analysis_result["file_extension"] = file_extension

            # Content type specific analysis
            if content_type.startswith("text/"):
                # Text file analysis
                text_analysis = await self._analyze_text_file(file_path)
                analysis_result.update(text_analysis)

            elif content_type == "application/pdf":
                # PDF file analysis
                pdf_analysis = await self._analyze_pdf_file(file_path)
                analysis_result.update(pdf_analysis)

            elif content_type.startswith("image/"):
                # Image file analysis
                image_analysis = await self._analyze_image_file(file_path)
                analysis_result.update(image_analysis)

            # Security check
            security_check = await self._security_check(file_path, content_type)
            analysis_result["security"] = security_check

            logger.info(f"File content analysis completed: {file_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"File content analysis failed: {file_id}, {e}")
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat(),
            }

    async def _analyze_text_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze text file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "content_length": len(content),
                "line_count": content.count("\n") + 1,
                "word_count": len(content.split()),
                "character_encoding": "utf-8",
                "is_empty": len(content.strip()) == 0,
            }
        except UnicodeDecodeError:
            # Try other encoding
            try:
                with open(file_path, "r", encoding="gbk") as f:
                    content = f.read()
                return {
                    "content_length": len(content),
                    "line_count": content.count("\n") + 1,
                    "word_count": len(content.split()),
                    "character_encoding": "gbk",
                    "is_empty": len(content.strip()) == 0,
                }
            except:
                return {"text_analysis_error": "Unable to recognize character encoding"}
        except Exception as e:
            return {"text_analysis_error": str(e)}

    async def _analyze_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF file"""
        try:
            # Here you can use PyPDF2 or other PDF libraries for analysis
            # Simplified implementation, only returns basic information
            return {
                "is_pdf": True,
                "pdf_analysis": "PDF analysis requires additional dependencies",
            }
        except Exception as e:
            return {"pdf_analysis_error": str(e)}

    async def _analyze_image_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze image file"""
        try:
            # Here you can use PIL or other image libraries for analysis
            # Simplified implementation, only returns basic information
            return {
                "is_image": True,
                "image_analysis": "Image analysis requires additional dependencies",
            }
        except Exception as e:
            return {"image_analysis_error": str(e)}

    async def _security_check(
        self, file_path: str, content_type: str
    ) -> Dict[str, Any]:
        """Security check"""
        try:
            file_size = os.path.getsize(file_path)

            # Basic security check
            security_result = {
                "is_safe": True,
                "file_size_ok": file_size < 100 * 1024 * 1024,  # 100MB limit
                "content_type_safe": content_type not in ["application/x-executable"],
                "warnings": [],
            }

            if file_size > 100 * 1024 * 1024:
                security_result["warnings"].append("File size exceeds 100MB")
                security_result["is_safe"] = False

            if content_type == "application/x-executable":
                security_result["warnings"].append("Executable file type")
                security_result["is_safe"] = False

            return security_result

        except Exception as e:
            return {"is_safe": False, "security_check_error": str(e)}


@task_handler(
    "file.cleanup_temp",
    priority=TaskPriority.LOW,
    max_retries=1,
    timeout=60,
    queue="cleanup_queue",
)
@register_task_handler
class TempFileCleanupHandler(ITaskHandler):
    """Temporary file cleanup handler"""

    @property
    def task_name(self) -> str:
        return "file.cleanup_temp"

    async def handle(
        self, file_paths: List[str], max_age_hours: int = 24, **config
    ) -> Dict[str, Any]:
        """
        Clean up temporary file

        Args:
            file_paths: List of file paths
            max_age_hours: Maximum retention time (hours)
            **config: Other configurations

        Returns:
            Dict[str, Any]: Cleanup result
        """
        try:
            logger.info(f"Start cleaning temporary files: {len(file_paths)} files")

            deleted_files = []
            failed_files = []
            skipped_files = []

            current_time = datetime.utcnow().timestamp()
            max_age_seconds = max_age_hours * 3600

            for file_path in file_paths:
                try:
                    if not os.path.exists(file_path):
                        skipped_files.append(
                            {"path": file_path, "reason": "File does not exist"}
                        )
                        continue

                    # Check file age
                    file_mtime = os.path.getmtime(file_path)
                    file_age = current_time - file_mtime

                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        deleted_files.append(
                            {"path": file_path, "age_hours": file_age / 3600}
                        )
                        logger.debug(f"Temporary file deleted: {file_path}")
                    else:
                        skipped_files.append(
                            {
                                "path": file_path,
                                "reason": f"File too new ({file_age/3600:.1f} hours)",
                            }
                        )

                except Exception as e:
                    failed_files.append({"path": file_path, "error": str(e)})
                    logger.error(f"Failed to delete file: {file_path}, {e}")

            result = {
                "success": True,
                "total_files": len(file_paths),
                "deleted_count": len(deleted_files),
                "failed_count": len(failed_files),
                "skipped_count": len(skipped_files),
                "deleted_files": deleted_files,
                "failed_files": failed_files,
                "skipped_files": skipped_files,
                "cleaned_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Temporary file cleanup completed: deleted {len(deleted_files)}, failed {len(failed_files)}, skipped {len(skipped_files)}"
            )
            return result

        except Exception as e:
            logger.error(f"Temporary file cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat(),
            }


@task_handler(
    "file.convert_format",
    priority=TaskPriority.NORMAL,
    max_retries=2,
    timeout=300,
    queue="file_queue",
)
@register_task_handler
class FileFormatConversionHandler(ITaskHandler):
    """File format conversion handler"""

    @property
    def task_name(self) -> str:
        return "file.convert_format"

    async def handle(
        self,
        source_file: str,
        target_format: str,
        output_path: Optional[str] = None,
        **config,
    ) -> Dict[str, Any]:
        """
        Convert file format

        Args:
            source_file: Source file path
            target_format: Target format (such as 'pdf', 'txt', 'html')
            output_path: Output file path
            **config: Other configurations

        Returns:
            Dict[str, Any]: Conversion result
        """
        try:
            logger.info(
                f"Start file format conversion: {source_file} -> {target_format}"
            )

            if not os.path.exists(source_file):
                raise FileNotFoundError(f"Source file does not exist: {source_file}")

            # Generate output path
            if not output_path:
                base_name = os.path.splitext(source_file)[0]
                output_path = f"{base_name}.{target_format}"

            # Convert according to target format
            conversion_result = await self._convert_file(
                source_file, target_format, output_path, config
            )

            if conversion_result["success"]:
                # Verify output file
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    conversion_result.update(
                        {
                            "output_path": output_path,
                            "output_size": output_size,
                            "converted_at": datetime.utcnow().isoformat(),
                        }
                    )
                else:
                    conversion_result = {
                        "success": False,
                        "error": "Conversion completed but output file not generated",
                    }

            logger.info(f"File format conversion completed: {source_file}")
            return conversion_result

        except Exception as e:
            logger.error(f"File format conversion failed: {source_file}, {e}")
            return {
                "success": False,
                "source_file": source_file,
                "target_format": target_format,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat(),
            }

    async def _convert_file(
        self,
        source_file: str,
        target_format: str,
        output_path: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute file conversion"""
        try:
            source_ext = os.path.splitext(source_file)[1].lower()

            # Simplified implementation - only supports basic text conversion
            if target_format == "txt" and source_ext in [".txt", ".md"]:
                # Directly copy text file
                with open(source_file, "r", encoding="utf-8") as src:
                    content = src.read()
                with open(output_path, "w", encoding="utf-8") as dst:
                    dst.write(content)

                return {
                    "success": True,
                    "conversion_type": "text_copy",
                    "source_format": source_ext[1:],
                    "target_format": target_format,
                }

            else:
                # Other conversions require additional library support
                return {
                    "success": False,
                    "error": f"Unsupported conversion: {source_ext} -> {target_format}",
                    "supported_conversions": ["txt->txt", "md->txt"],
                }

        except Exception as e:
            return {"success": False, "error": f"Conversion execution failed: {str(e)}"}


logger.info("File task handler module loaded")
