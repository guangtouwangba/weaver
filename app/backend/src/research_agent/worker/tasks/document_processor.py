"""Document processor task - orchestrates the full document processing pipeline."""

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
from research_agent.infrastructure.pdf.pymupdf import PyMuPDFParser
from research_agent.infrastructure.storage.local import LocalStorageService
from research_agent.infrastructure.storage.supabase_storage import SupabaseStorageService
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask
from research_agent.worker.tasks.canvas_syncer import CanvasSyncerTask
from research_agent.worker.tasks.graph_extractor import GraphExtractorTask


class DocumentProcessorTask(BaseTask):
    """
    Orchestrator task for processing uploaded documents.

    Pipeline:
    1. Download file (if from Supabase Storage)
    2. Extract text from PDF
    3. Generate summary and page mapping
    4. Chunk text
    5. Generate embeddings
    6. Extract knowledge graph
    7. Sync to canvas
    8. Update document status
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

            # Step 2: Extract text from PDF
            logger.info(f"📄 Step 2: Extracting text from PDF - local_path={local_path}")
            try:
                pdf_parser = PyMuPDFParser()
                pages = await pdf_parser.extract_text(local_path)
                page_count = len(pages)
                logger.info(f"✅ Step 2 completed: Extracted {page_count} pages from PDF")
            except Exception as e:
                logger.error(
                    f"❌ Step 2 failed: PDF extraction error - document_id={document_id}, "
                    f"local_path={local_path}: {e}",
                    exc_info=True,
                )
                raise

            # Step 2.5: Generate Summary and Page Map
            logger.info(f"📝 Step 2.5: Generating summary and page map - document_id={document_id}")
            try:
                # Calculate Page Map
                page_map = []
                current_idx = 0
                # Join logic matches step 3b full content generation: "\n\n".join()
                # We simulate the join process to get correct indices
                for i, page in enumerate(pages):
                    content_len = len(page.content)
                    start = current_idx
                    end = current_idx + content_len

                    page_map.append({"page": page.page_number, "start": start, "end": end})

                    # Add separator length for next iteration, unless it's the last page
                    if i < len(pages) - 1:
                        current_idx = end + 2  # len("\n\n")
                    else:
                        current_idx = end

                # Generate Summary
                # Combine first 20k chars for summary generation (to avoid context limits if very large)
                # or use LLM service's context window logic.
                # For now, simple truncation.
                full_content_preview = "\n\n".join([p.content for p in pages])
                summary_context = full_content_preview[:20000]

                summary = None
                if settings.openrouter_api_key:
                    llm = OpenRouterLLMService(
                        api_key=settings.openrouter_api_key,
                        model=settings.llm_model,  # Use primary model for high quality summary
                    )
                    summary = await self._generate_summary(llm, summary_context)
                    logger.info("✅ Generated document summary")
                else:
                    logger.warning("⚠️ Skipping summary generation: No API key")

                # Update document model immediately with summary and temp parsing metadata
                # Note: parsing_metadata will be updated again in step 3b, so we merge or just wait?
                # Step 3b updates `parsing_metadata` with page_count etc.
                # Let's persist summary now.
                stmt = (
                    update(DocumentModel)
                    .where(DocumentModel.id == document_id)
                    .values(summary=summary)
                )
                await session.execute(stmt)
                await session.commit()

            except Exception as e:
                logger.warning(
                    f"⚠️ Step 2.5 failed: Summary/PageMap generation error - document_id={document_id}: {e}",
                    exc_info=True,
                )
                # Don't fail the whole process for summary error

            # Step 3: Chunk text with dynamic strategy selection
            logger.info(f"✂️ Step 3: Chunking text with dynamic strategy - page_count={page_count}")
            try:
                # Get document metadata for strategy selection
                doc_result = await session.execute(
                    select(DocumentModel).where(DocumentModel.id == document_id)
                )
                doc = doc_result.scalar_one()
                logger.debug(
                    f"Document metadata - mime_type={doc.mime_type}, "
                    f"filename={doc.original_filename}"
                )

                chunking_service = ChunkingService()
                chunk_data = chunking_service.chunk_pages(
                    pages=pages,
                    mime_type=doc.mime_type,
                    filename=doc.original_filename,
                )
                logger.info(f"✅ Step 3 completed: Created {len(chunk_data)} chunks")

                # Step 3b: Prepare full content and metadata for long context mode
                logger.info("📝 Step 3b: Preparing full content and metadata for long context mode")
                try:
                    from research_agent.domain.services.token_estimator import TokenEstimator

                    # Combine all pages into full content
                    full_content = "\n\n".join([page.content for page in pages])

                    # Estimate token count
                    token_estimator = TokenEstimator()
                    token_count = token_estimator.estimate_tokens(full_content)

                    # Prepare parsing metadata
                    parsing_metadata = {
                        "layout_type": "single_column",
                        "page_count": page_count,
                        "total_chunks": len(chunk_data),
                        "page_map": page_map,  # Injected from Step 2.5 logic
                    }

                    # Update document with full content and metadata
                    doc.full_content = full_content
                    doc.content_token_count = token_count
                    doc.parsing_metadata = parsing_metadata
                    # summary is already updated or can be updated here if not persisted yet.
                    # Since we re-fetched doc in Step 3, it might be stale if we updated it in 2.5?
                    # Actually Step 3 re-selects doc. So if we committed in 2.5, doc has summary.
                    # But here we are updating doc object attributes.

                    await session.flush()
                    # Commit before long embedding operation to release the connection
                    await session.commit()
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
            except Exception as e:
                logger.error(
                    f"❌ Step 3 failed: Chunking error - document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 4: Generate embeddings (optional for long_context mode)
            # ✅ CRITICAL: This step uses fresh sessions to avoid connection timeout
            # Embedding generation can take 30-60+ seconds, which would cause the original
            # session's connection to timeout.
            if chunk_data:
                # Check if we can skip embedding generation for long_context mode
                should_skip_embedding = False
                skip_reason = ""

                if settings.rag_mode == "long_context":
                    # Check if document fits in context and we have full_content
                    if doc.full_content and doc.content_token_count:
                        from research_agent.infrastructure.llm.model_config import (
                            calculate_available_tokens,
                        )

                        max_tokens = calculate_available_tokens(
                            settings.llm_model, settings.long_context_safety_ratio
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

            # PROGRESSIVE PROCESSING: Mark document as READY for RAG now
            # This allows users to start chatting while graph extraction runs in background
            # ✅ Use fresh session for status update
            logger.info(f"✅ Marking document as READY for RAG - document_id={document_id}")
            try:
                async with get_async_session() as fresh_session:
                    await self._update_document_status(
                        fresh_session,
                        document_id,
                        status=DocumentStatus.READY,
                        graph_status="processing",
                        page_count=page_count,
                    )
                logger.debug(f"✅ Document {document_id} status updated to READY")
            except Exception as e:
                logger.error(
                    f"❌ Failed to mark document as READY - document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 5: Extract knowledge graph
            # ✅ Use fresh session for graph extraction
            logger.info(f"🕸️ Step 5: Extracting knowledge graph - document_id={document_id}")
            try:
                async with get_async_session() as fresh_session:
                    graph_extractor = GraphExtractorTask()
                    await graph_extractor.execute(
                        {"document_id": str(document_id), "project_id": str(project_id)},
                        fresh_session,
                    )
                logger.info("✅ Step 5 completed: Knowledge graph extracted")
            except Exception as e:
                logger.error(
                    f"❌ Step 5 failed: Knowledge graph extraction error - "
                    f"document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 6: Sync to canvas
            # ✅ Use fresh session for canvas sync
            logger.info(f"🎨 Step 6: Syncing to canvas - document_id={document_id}")
            try:
                async with get_async_session() as fresh_session:
                    canvas_syncer = CanvasSyncerTask()
                    await canvas_syncer.execute(
                        {"project_id": str(project_id), "document_id": str(document_id)},
                        fresh_session,
                    )
                logger.info("✅ Step 6 completed: Canvas synced")
            except Exception as e:
                logger.error(
                    f"❌ Step 6 failed: Canvas sync error - document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 7: Update graph status to ready
            # ✅ Use fresh session for final status update
            logger.info(f"✅ Step 7: Updating graph status to ready - document_id={document_id}")
            try:
                async with get_async_session() as fresh_session:
                    await self._update_document_status(
                        fresh_session, document_id, graph_status="ready"
                    )
                logger.info("✅ Step 7 completed: Graph status updated to ready")
            except Exception as e:
                logger.error(
                    f"❌ Step 7 failed: Failed to update graph status - "
                    f"document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

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
                        graph_status="error",
                    )
                logger.info(f"✅ Updated document {document_id} status to ERROR")
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

                # Save locally for processing
                local_storage = LocalStorageService(settings.upload_dir)
                local_path = f"temp/{project_id}/{document_id}.pdf"

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
        graph_status: str = None,
        page_count: int = None,
    ) -> None:
        """Update document status in database."""
        values = {}
        if status:
            values["status"] = status.value
        if graph_status:
            values["graph_status"] = graph_status
        if page_count is not None:
            values["page_count"] = page_count

        if not values:
            return

        stmt = update(DocumentModel).where(DocumentModel.id == document_id).values(**values)
        await session.execute(stmt)
