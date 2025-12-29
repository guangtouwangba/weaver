"""Document processor task - orchestrates the full document processing pipeline."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings

settings = get_settings()
from research_agent.domain.entities.document import DocumentStatus
from research_agent.domain.services.chunking_service import ChunkingService
from research_agent.infrastructure.database.models import DocumentChunkModel, DocumentModel
from research_agent.infrastructure.database.session import get_async_session
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
from research_agent.infrastructure.llm.base import ChatMessage
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService
from research_agent.infrastructure.parser.factory import ParserFactory
from research_agent.infrastructure.storage.local import LocalStorageService
from research_agent.infrastructure.storage.supabase_storage import SupabaseStorageService
from research_agent.infrastructure.websocket.notification_service import (
    document_notification_service,
)
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


class DocumentProcessorTask(BaseTask):
    """
    Orchestrator task for processing uploaded documents.

    Pipeline:
    1. Download file (if from Supabase Storage)
    2. Extract text from PDF
    3. Generate summary and page mapping
    4. Chunk text
    5. Generate embeddings (optional for long_context mode)
    6. Update document status to READY
    """

    @property
    def task_type(self) -> str:
        return "process_document"

    async def execute(self, payload: Dict[str, Any], session: AsyncSession) -> None:
        """
        Process a document through the full pipeline.

        Payload:
            document_id: UUID of the document to process
            project_id: UUID of the project
            file_path: Path to the file (local or Supabase Storage)
        """
        document_id = UUID(payload["document_id"])
        project_id = UUID(payload["project_id"])
        file_path = payload["file_path"]

        logger.info(
            f"🚀 Starting document processing - document_id={document_id}, "
            f"project_id={project_id}, file_path={file_path}"
        )

        # Update status to processing
        try:
            await self._update_document_status(session, document_id, DocumentStatus.PROCESSING)
            await session.commit()
            logger.debug(f"✅ Updated document {document_id} status to PROCESSING")

            # Send WebSocket notification for processing status
            await document_notification_service.notify_document_status(
                project_id=str(project_id),
                document_id=str(document_id),
                status="processing",
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to update document status to PROCESSING - document_id={document_id}: {e}",
                exc_info=True,
            )
            raise

        try:
            # Step 1: Get file content
            logger.info(f"📥 Step 1: Getting file locally - file_path={file_path}")
            local_path = await self._get_file_locally(file_path, document_id, project_id)
            logger.info(f"✅ Step 1 completed: File available at {local_path}")

            # Step 2: Extract text from document using appropriate parser
            logger.info(f"📄 Step 2: Extracting text from document - local_path={local_path}")
            try:
                # Get document MIME type from database
                doc_result = await session.execute(
                    select(DocumentModel).where(DocumentModel.id == document_id)
                )
                doc = doc_result.scalar_one_or_none()

                # Handle case where document was deleted before processing started
                if doc is None:
                    logger.warning(
                        f"⚠️ Document not found in database, may have been deleted - "
                        f"document_id={document_id}, skipping processing"
                    )
                    return  # Exit gracefully, nothing to process

                mime_type = doc.mime_type
                file_extension = Path(local_path).suffix.lower()

                # Get document_processing_mode from user/project settings
                processing_mode = await self._get_processing_mode(project_id)
                logger.info(
                    f"📋 Document processing mode: {processing_mode} for mime_type={mime_type}"
                )

                # Parse document with the user's preferred processing mode
                parse_result = await ParserFactory.parse_with_mode(
                    file_path=local_path,
                    mode=processing_mode,
                    mime_type=mime_type,
                    extension=file_extension,
                )
                pages = parse_result.pages
                page_count = parse_result.page_count
                has_ocr = parse_result.has_ocr

                logger.info(
                    f"✅ Step 2 completed: Extracted {page_count} pages using {parse_result.parser_name}"
                    f"{' (OCR applied)' if has_ocr else ''}"
                )

                # Store parsing metadata for later use
                parsing_info = {
                    "parser_name": parse_result.parser_name,
                    "document_type": parse_result.document_type.value,
                    "has_ocr": has_ocr,
                    **parse_result.metadata,
                }
            except Exception as e:
                logger.error(
                    f"❌ Step 2 failed: Document extraction error - document_id={document_id}, "
                    f"local_path={local_path}: {e}",
                    exc_info=True,
                )
                raise

            # Get user settings early to determine processing strategy
            # ✅ Use retry logic since connection may have timed out during long PDF parsing
            user_rag_mode = settings.rag_mode  # Default to env setting
            user_safety_ratio = settings.long_context_safety_ratio  # Default to env setting
            user_fast_upload_mode = True  # Default to True for fast processing
            try:
                from uuid import UUID as UUIDType

                from research_agent.domain.services.settings_service import SettingsService
                from research_agent.infrastructure.database.repositories.sqlalchemy_settings_repo import (
                    SQLAlchemySettingsRepository,
                )

                DEFAULT_USER_ID = UUIDType("00000000-0000-0000-0000-000000000001")

                # ✅ Retry logic for settings query (connection may have timed out during PDF parsing)
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    try:
                        async with get_async_session(max_retries=1) as settings_session:
                            repo = SQLAlchemySettingsRepository(settings_session)
                            settings_service = SettingsService(repo)

                            # Get rag_mode
                            db_rag_mode = await settings_service.get_setting(
                                "rag_mode",
                                user_id=DEFAULT_USER_ID,
                                project_id=project_id,
                            )
                            if db_rag_mode:
                                user_rag_mode = db_rag_mode

                            # Get fast_upload_mode
                            db_fast_upload = await settings_service.get_setting(
                                "fast_upload_mode",
                                user_id=DEFAULT_USER_ID,
                                project_id=project_id,
                            )
                            if db_fast_upload is not None:
                                user_fast_upload_mode = bool(db_fast_upload)

                            # Get long_context_safety_ratio
                            db_safety_ratio = await settings_service.get_setting(
                                "long_context_safety_ratio",
                                user_id=DEFAULT_USER_ID,
                                project_id=project_id,
                            )
                            if db_safety_ratio is not None:
                                user_safety_ratio = float(db_safety_ratio)

                            logger.info(
                                f"📋 User settings: rag_mode={user_rag_mode}, "
                                f"fast_upload_mode={user_fast_upload_mode}, "
                                f"safety_ratio={user_safety_ratio}"
                            )
                        # Success, break out of retry loop
                        break
                    except Exception as retry_error:
                        error_str = str(retry_error)
                        if (
                            any(
                                keyword in error_str
                                for keyword in [
                                    "ConnectionDoesNotExistError",
                                    "connection was closed",
                                    "connection closed",
                                ]
                            )
                            and attempt < max_retries
                        ):
                            logger.warning(
                                f"⚠️ Settings query failed due to connection error (attempt {attempt}/{max_retries}), retrying..."
                            )
                            await asyncio.sleep(0.5 * attempt)  # Exponential backoff
                            continue
                        else:
                            # Non-connection error or max retries reached
                            raise
            except Exception as e:
                logger.warning(f"Failed to get user settings, using env defaults: {e}")

            # Step 2.5 & 3: Generate Summary/Page Map and Chunking (parallel processing)
            logger.info(
                f"📝 Step 2.5 & 3: Processing summary/page_map and chunking - document_id={document_id}"
            )
            summary = None
            page_map = []
            chunk_data = []

            async def calculate_page_map():
                """Calculate page map for citation purposes."""
                page_map_result = []
                current_idx = 0
                # Join logic matches step 3b full content generation: "\n\n".join()
                for i, page in enumerate(pages):
                    content_len = len(page.content)
                    start = current_idx
                    end = current_idx + content_len

                    page_map_result.append({"page": page.page_number, "start": start, "end": end})

                    # Add separator length for next iteration, unless it's the last page
                    if i < len(pages) - 1:
                        current_idx = end + 2  # len("\n\n")
                    else:
                        current_idx = end
                return page_map_result

            async def generate_summary_if_needed():
                """Generate summary only if not in fast_upload_mode or not long_context."""
                if user_rag_mode == "long_context" and user_fast_upload_mode:
                    logger.info("⏭️ Skipping summary generation (fast_upload_mode enabled)")
                    return None

                if not settings.openrouter_api_key:
                    logger.warning("⚠️ Skipping summary generation: No API key")
                    return None

                try:
                    # Combine first 20k chars for summary generation
                    full_content_preview = "\n\n".join([p.content for p in pages])
                    summary_context = full_content_preview[:20000]

                    llm = OpenRouterLLMService(
                        api_key=settings.openrouter_api_key,
                        model=settings.llm_model,
                    )
                    summary_result = await self._generate_summary(llm, summary_context)
                    logger.info("✅ Generated document summary")
                    return summary_result
                except Exception as e:
                    logger.warning(f"⚠️ Summary generation failed: {e}")
                    return None

            async def perform_chunking():
                """Perform text chunking using fresh session to avoid connection timeout."""
                # ✅ Use fresh session - original session may have timed out during long OCR
                async with get_async_session() as chunking_session:
                    # Get document metadata for strategy selection
                    doc_result = await chunking_session.execute(
                        select(DocumentModel).where(DocumentModel.id == document_id)
                    )
                    doc = doc_result.scalar_one()
                    logger.debug(
                        f"Document metadata - mime_type={doc.mime_type}, "
                        f"filename={doc.original_filename}"
                    )

                    chunking_service = ChunkingService()
                    chunk_data_result = chunking_service.chunk_pages(
                        pages=pages,
                        mime_type=doc.mime_type,
                        filename=doc.original_filename,
                    )
                    logger.info(f"✅ Chunking completed: Created {len(chunk_data_result)} chunks")
                    return chunk_data_result

            try:
                # Parallel execution: page_map calculation, summary generation, and chunking
                import asyncio

                page_map, summary, chunk_data = await asyncio.gather(
                    calculate_page_map(),
                    generate_summary_if_needed(),
                    perform_chunking(),
                )

                # Save summary if generated - use fresh session to avoid connection timeout
                if summary is not None:
                    async with get_async_session() as summary_session:
                        stmt = (
                            update(DocumentModel)
                            .where(DocumentModel.id == document_id)
                            .values(summary=summary)
                        )
                        await summary_session.execute(stmt)
                        await summary_session.commit()

            except Exception as e:
                logger.warning(
                    f"⚠️ Step 2.5 & 3 failed: Processing error - document_id={document_id}: {e}",
                    exc_info=True,
                )
                # Don't fail the whole process, but ensure we have at least page_map and chunk_data
                if not page_map:
                    page_map = await calculate_page_map()
                if not chunk_data:
                    chunk_data = await perform_chunking()

            # Step 3b: Prepare full content and metadata for long context mode
            # ✅ Use fresh session to avoid connection timeout after long OCR operation
            logger.info("📝 Step 3b: Preparing full content and metadata for long context mode")
            try:
                from research_agent.domain.services.token_estimator import TokenEstimator

                # Combine all pages into full content
                full_content = "\n\n".join([page.content for page in pages])

                # Estimate token count
                token_estimator = TokenEstimator()
                token_count = token_estimator.estimate_tokens(full_content)

                # Prepare parsing metadata (merge with parser info from Step 2)
                parsing_metadata = {
                    "layout_type": "single_column",
                    "page_count": page_count,
                    "total_chunks": len(chunk_data),
                    "page_map": page_map,  # From Step 2.5
                    **parsing_info,  # Include parser metadata from Step 2
                }

                # Update document with full content and metadata using fresh session
                async with get_async_session() as content_session:
                    stmt = (
                        update(DocumentModel)
                        .where(DocumentModel.id == document_id)
                        .values(
                            full_content=full_content,
                            content_token_count=token_count,
                            parsing_metadata=parsing_metadata,
                        )
                    )
                    await content_session.execute(stmt)
                    await content_session.commit()

                logger.info(
                    f"✅ Step 3b completed: Saved full content ({token_count} tokens) "
                    f"and metadata for document {document_id}"
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Step 3b failed: Failed to save full content - document_id={document_id}: {e}",
                    exc_info=True,
                )
                # Continue processing even if full content save fails

            # Step 4: Generate embeddings (optional for long_context mode)
            # ✅ CRITICAL: This step uses fresh sessions to avoid connection timeout
            # Embedding generation can take 30-60+ seconds, which would cause the original
            # session's connection to timeout.
            if chunk_data:
                # Check if we can skip embedding generation
                should_skip_embedding = False
                skip_reason = ""

                # Fast upload mode: skip embeddings in long_context mode
                if user_rag_mode == "long_context" and user_fast_upload_mode:
                    should_skip_embedding = True
                    skip_reason = (
                        f"Fast upload mode: skipping embeddings in long_context mode "
                        f"(embeddings can be generated on-demand if needed)"
                    )
                elif user_rag_mode == "long_context":
                    # Check if document fits in context and we have full_content
                    # ✅ Use fresh session to avoid connection timeout after long OCR
                    async with get_async_session() as check_session:
                        doc_result = await check_session.execute(
                            select(DocumentModel).where(DocumentModel.id == document_id)
                        )
                        doc = doc_result.scalar_one()

                    if doc.full_content and doc.content_token_count:
                        from research_agent.infrastructure.llm.model_config import (
                            calculate_available_tokens,
                        )

                        max_tokens = calculate_available_tokens(
                            settings.llm_model, user_safety_ratio
                        )
                        if doc.content_token_count <= max_tokens:
                            should_skip_embedding = True
                            skip_reason = (
                                f"Long context mode: document fits in context "
                                f"({doc.content_token_count} <= {max_tokens} tokens), "
                                f"embedding not needed for retrieval"
                            )

                if should_skip_embedding:
                    logger.info(f"⏭️ Step 4 skipped: {skip_reason}")
                    logger.info(
                        f"💾 Saving {len(chunk_data)} chunks without embeddings "
                        f"(for citation/reference purposes only)"
                    )

                    # Save chunks without embeddings using fresh session
                    await self._save_chunks_batch(
                        document_id=document_id,
                        project_id=project_id,
                        chunk_data=chunk_data,
                        embeddings=None,
                    )

                    logger.info(
                        f"✅ Step 4 completed: Saved {len(chunk_data)} chunks without embeddings"
                    )
                else:
                    # Generate embeddings (needed for traditional mode, hybrid mode, or document selection)
                    logger.info(
                        f"🔢 Step 4: Generating embeddings - chunk_count={len(chunk_data)}, "
                        f"model={settings.embedding_model}, rag_mode={settings.rag_mode}"
                    )
                    try:
                        # OpenRouter DOES support embedding API!
                        # The curl test confirmed it works.
                        embedding_service = OpenRouterEmbeddingService(
                            api_key=settings.openrouter_api_key,
                            model=settings.embedding_model,
                        )

                        contents = [c["content"] for c in chunk_data]
                        logger.debug(
                            f"First chunk preview: {contents[0][:100]}..."
                            if contents
                            else "No contents"
                        )

                        try:
                            # ✅ This is the long-running operation that was causing connection timeout
                            embeddings = await embedding_service.embed_batch(contents)
                            logger.info(
                                f"✅ Step 4a completed: Generated {len(embeddings)} embeddings"
                            )
                        except Exception as e:
                            logger.error(
                                f"❌ Step 4a failed: Embedding generation error - "
                                f"document_id={document_id}, chunk_count={len(contents)}, "
                                f"model={settings.embedding_model}: {e}",
                                exc_info=True,
                            )
                            raise

                        # ✅ CRITICAL FIX: Save chunks with embeddings using FRESH session
                        # The original session's connection may have timed out during embedding generation
                        logger.debug(f"💾 Saving {len(chunk_data)} chunks to database in batches")

                        await self._save_chunks_batch(
                            document_id=document_id,
                            project_id=project_id,
                            chunk_data=chunk_data,
                            embeddings=embeddings,
                        )

                        logger.info(
                            f"✅ Step 4b completed: Saved {len(chunk_data)} chunks with embeddings"
                        )
                    except Exception as e:
                        logger.error(
                            f"❌ Step 4 failed: Embedding or chunk saving error - "
                            f"document_id={document_id}: {e}",
                            exc_info=True,
                        )
                        raise
            else:
                logger.warning(
                    f"⚠️ Step 4 skipped: No chunks to process - document_id={document_id}"
                )

                # Step 5: Mark document as READY for RAG
            # ✅ Use fresh session for status update
            logger.info(f"✅ Step 5: Marking document as READY for RAG - document_id={document_id}")
            try:
                async with get_async_session() as fresh_session:
                    await self._update_document_status(
                        fresh_session,
                        document_id,
                        status=DocumentStatus.READY,
                        page_count=page_count,
                    )
                logger.debug(f"✅ Document {document_id} status updated to READY")

                # Send WebSocket notification for READY status
                await document_notification_service.notify_document_status(
                    project_id=str(project_id),
                    document_id=str(document_id),
                    status="ready",
                    summary=summary,
                    page_count=page_count,
                )
            except Exception as e:
                logger.error(
                    f"❌ Step 5 failed: Failed to mark document as READY - document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 6: Queue thumbnail generation for PDF documents
            logger.info(f"🖼️ Step 6: Queuing thumbnail generation - document_id={document_id}")
            try:
                from research_agent.domain.entities.task import TaskType
                from research_agent.worker.service import TaskQueueService

                async with get_async_session() as thumbnail_session:
                    # Update document thumbnail status to pending
                    stmt = (
                        update(DocumentModel)
                        .where(DocumentModel.id == document_id)
                        .values(thumbnail_status="pending")
                    )
                    await thumbnail_session.execute(stmt)

                    # Queue thumbnail generation task
                    task_service = TaskQueueService(thumbnail_session)
                    await task_service.push(
                        task_type=TaskType.GENERATE_THUMBNAIL,
                        payload={
                            "document_id": str(document_id),
                            "project_id": str(project_id),
                            "file_path": local_path,
                        },
                        priority=5,  # Lower priority than document processing
                    )
                    await thumbnail_session.commit()

                logger.info(f"✅ Step 6 completed: Thumbnail generation queued for {document_id}")
            except Exception as e:
                logger.warning(
                    f"⚠️ Step 6 failed (non-critical): Thumbnail task queuing error - "
                    f"document_id={document_id}: {e}",
                    exc_info=True,
                )
                # Non-critical failure - document is still READY, just no thumbnail

            logger.info(
                f"🎉 Document processing completed successfully - document_id={document_id}, "
                f"project_id={project_id}, page_count={page_count}"
            )

        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)

            logger.error(
                f"💥 CRITICAL: Document processing failed - document_id={document_id}, "
                f"project_id={project_id}, error_type={error_type}, error={error_message}",
                exc_info=True,
            )

            # Log additional context
            logger.error(
                f"📋 Error context - file_path={file_path}, "
                f"payload={payload}, exception_type={error_type}"
            )

            # Update status to error - use fresh session
            try:
                async with get_async_session() as fresh_session:
                    await self._update_document_status(
                        fresh_session,
                        document_id,
                        status=DocumentStatus.ERROR,
                    )
                logger.info(f"✅ Updated document {document_id} status to ERROR")

                # Send WebSocket notification for error status
                await document_notification_service.notify_document_status(
                    project_id=str(project_id),
                    document_id=str(document_id),
                    status="error",
                    error_message=error_message,
                )
            except Exception as status_error:
                logger.error(
                    f"❌ CRITICAL: Failed to update document status to ERROR - "
                    f"document_id={document_id}, original_error={error_message}, "
                    f"status_error={status_error}",
                    exc_info=True,
                )

            raise

    async def _save_chunks_batch(
        self,
        document_id: UUID,
        project_id: UUID,
        chunk_data: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """
        Save chunks to database in batches using a fresh session.

        This method creates its own session to avoid connection timeout issues
        that can occur when the caller's session has been idle during long operations
        like embedding generation.
        """
        batch_size = 50
        total_chunks = len(chunk_data)
        saved_count = 0

        for i in range(0, total_chunks, batch_size):
            batch_end = min(i + batch_size, total_chunks)
            batch_chunks = chunk_data[i:batch_end]
            batch_embeddings = embeddings[i:batch_end] if embeddings else [None] * len(batch_chunks)

            logger.debug(
                f"💾 Saving batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size} "
                f"(chunks {i + 1}-{batch_end} of {total_chunks})"
            )

            # ✅ Use fresh session for each batch to ensure connection is alive
            async with get_async_session() as batch_session:
                for chunk, embedding in zip(batch_chunks, batch_embeddings):
                    chunk_model = DocumentChunkModel(
                        document_id=document_id,
                        project_id=project_id,
                        chunk_index=chunk["chunk_index"],
                        content=chunk["content"],
                        page_number=chunk.get("page_number"),
                        embedding=embedding,
                        chunk_metadata=chunk.get("metadata", {}),
                    )
                    batch_session.add(chunk_model)

                # Flush and commit will happen automatically when context manager exits
                # But let's be explicit
                await batch_session.flush()

            saved_count += len(batch_chunks)
            logger.debug(f"✅ Batch saved: {saved_count}/{total_chunks} chunks saved so far")

        logger.info(f"✅ All {saved_count} chunks saved successfully")

    async def _generate_summary(self, llm: OpenRouterLLMService, text: str) -> str:
        """Generate a summary of the document text."""
        prompt = (
            "请仔细阅读以下文档片段，并生成一份结构清晰的中文摘要。\n"
            "要求：\n"
            "1. 概括核心观点、主要结论和关键数据。\n"
            "2. 语言简练专业，字数控制在300字以内。\n"
            "3. 使用 Markdown 格式（如使用列表项）。\n\n"
            f"文档内容：\n{text}"
        )

        messages = [ChatMessage(role="user", content=prompt)]

        try:
            response = await llm.chat(messages)
            return response.content
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise

    async def _get_processing_mode(self, project_id: UUID) -> str:
        """
        Get the document processing mode from user/project settings.

        Priority: User > Project > Global > Default ("standard")

        Args:
            project_id: Project UUID to check for project-level override

        Returns:
            Processing mode: "fast", "standard", or "quality"
        """
        from uuid import UUID as UUIDType

        from research_agent.domain.services.settings_service import SettingsService
        from research_agent.infrastructure.database.repositories.sqlalchemy_settings_repo import (
            SQLAlchemySettingsRepository,
        )

        DEFAULT_USER_ID = UUIDType("00000000-0000-0000-0000-000000000001")
        default_mode = "standard"

        try:
            async with get_async_session() as settings_session:
                repo = SQLAlchemySettingsRepository(settings_session)
                settings_service = SettingsService(repo)

                # Get document_processing_mode with priority resolution
                mode = await settings_service.get_setting(
                    "document_processing_mode",
                    user_id=DEFAULT_USER_ID,
                    project_id=project_id,
                )

                if mode and mode in ["fast", "standard", "quality"]:
                    return mode

                logger.debug(
                    f"No valid document_processing_mode found, using default: {default_mode}"
                )
                return default_mode

        except Exception as e:
            logger.warning(f"Failed to get document_processing_mode setting, using default: {e}")
            return default_mode

    async def _get_file_locally(
        self,
        file_path: str,
        document_id: UUID,
        project_id: UUID,
    ) -> str:
        """
        Ensure file is available locally for processing.

        If file is in Supabase Storage, download it.
        """
        # Preserve original file extension
        original_extension = Path(file_path).suffix or ".bin"

        # Check if it's a Supabase Storage path
        if file_path.startswith("projects/") and settings.supabase_url:
            # Download from Supabase
            logger.info(f"Downloading file from Supabase Storage: {file_path}")

            supabase_storage = SupabaseStorageService(
                supabase_url=settings.supabase_url,
                service_role_key=settings.supabase_service_role_key,
                bucket_name=settings.storage_bucket,
            )

            try:
                content = await supabase_storage.download_file(file_path)

                # Save locally for processing with correct extension
                local_storage = LocalStorageService(settings.upload_dir)
                local_path = f"temp/{project_id}/{document_id}{original_extension}"

                import io

                await local_storage.save(local_path, io.BytesIO(content))

                return f"{settings.upload_dir}/{local_path}"
            finally:
                await supabase_storage.close()
        else:
            # File is already local
            if file_path.startswith(settings.upload_dir):
                return file_path
            else:
                return f"{settings.upload_dir}/{file_path}"

    async def _update_document_status(
        self,
        session: AsyncSession,
        document_id: UUID,
        status: DocumentStatus = None,
        page_count: int = None,
    ) -> None:
        """Update document status in database."""
        values = {}
        if status:
            values["status"] = status.value
        if page_count is not None:
            values["page_count"] = page_count

        if not values:
            return

        stmt = update(DocumentModel).where(DocumentModel.id == document_id).values(**values)
        await session.execute(stmt)
