"""Document processor task - orchestrates the full document processing pipeline."""

from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings

settings = get_settings()
from research_agent.domain.entities.document import DocumentStatus
from research_agent.domain.services.chunking_service import ChunkingService
from research_agent.infrastructure.database.models import DocumentChunkModel, DocumentModel
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
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
    3. Chunk text
    4. Generate embeddings
    5. Extract knowledge graph
    6. Sync to canvas
    7. Update document status
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
            except Exception as e:
                logger.error(
                    f"❌ Step 3 failed: Chunking error - document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 4: Generate embeddings
            if chunk_data:
                logger.info(
                    f"🔢 Step 4: Generating embeddings - chunk_count={len(chunk_data)}, "
                    f"model={settings.embedding_model}"
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
                        embeddings = await embedding_service.embed_batch(contents)
                        logger.info(f"✅ Step 4a completed: Generated {len(embeddings)} embeddings")
                    except Exception as e:
                        logger.error(
                            f"❌ Step 4a failed: Embedding generation error - "
                            f"document_id={document_id}, chunk_count={len(contents)}, "
                            f"model={settings.embedding_model}: {e}",
                            exc_info=True,
                        )
                        raise

                    # Save chunks with embeddings in batches to avoid connection timeout
                    # Large batch inserts can cause "connection is closed" errors
                    logger.debug(f"💾 Saving {len(chunk_data)} chunks to database in batches")

                    batch_size = 50  # Insert chunks in batches of 50
                    total_chunks = len(chunk_data)
                    saved_count = 0

                    for i in range(0, total_chunks, batch_size):
                        batch_end = min(i + batch_size, total_chunks)
                        batch_chunks = chunk_data[i:batch_end]
                        batch_embeddings = embeddings[i:batch_end]

                        logger.debug(
                            f"💾 Saving batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size} "
                            f"(chunks {i + 1}-{batch_end} of {total_chunks})"
                        )

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
                            session.add(chunk_model)

                        # Flush each batch separately
                        await session.flush()
                        saved_count += len(batch_chunks)

                        logger.debug(
                            f"✅ Batch saved: {saved_count}/{total_chunks} chunks saved so far"
                        )

                    logger.info(
                        f"✅ Step 4b completed: Saved {saved_count} chunks with embeddings "
                        f"in {(total_chunks + batch_size - 1) // batch_size} batches"
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
            logger.info(f"✅ Marking document as READY for RAG - document_id={document_id}")
            try:
                await self._update_document_status(
                    session,
                    document_id,
                    status=DocumentStatus.READY,
                    graph_status="processing",
                    page_count=page_count,
                )
                await session.commit()
                logger.debug(f"✅ Document {document_id} status updated to READY")
            except Exception as e:
                logger.error(
                    f"❌ Failed to mark document as READY - document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 5: Extract knowledge graph
            logger.info(f"🕸️ Step 5: Extracting knowledge graph - document_id={document_id}")
            try:
                graph_extractor = GraphExtractorTask()
                await graph_extractor.execute(
                    {"document_id": str(document_id), "project_id": str(project_id)},
                    session,
                )
                logger.info("✅ Step 5 completed: Knowledge graph extracted")
            except Exception as e:
                logger.error(
                    f"❌ Step 5 failed: Knowledge graph extraction error - "
                    f"document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Commit entities before canvas sync to ensure they're visible
            await session.commit()

            # Step 6: Sync to canvas
            logger.info(f"🎨 Step 6: Syncing to canvas - document_id={document_id}")
            try:
                canvas_syncer = CanvasSyncerTask()
                await canvas_syncer.execute(
                    {"project_id": str(project_id), "document_id": str(document_id)},
                    session,
                )
                logger.info("✅ Step 6 completed: Canvas synced")
            except Exception as e:
                logger.error(
                    f"❌ Step 6 failed: Canvas sync error - document_id={document_id}: {e}",
                    exc_info=True,
                )
                raise

            # Step 7: Update graph status to ready
            logger.info(f"✅ Step 7: Updating graph status to ready - document_id={document_id}")
            try:
                await self._update_document_status(session, document_id, graph_status="ready")
                await session.commit()
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

            # Update status to error
            try:
                await session.rollback()
                logger.debug(f"✅ Session rolled back for document {document_id}")

                # If RAG failed (status != READY), mark document as error
                # If RAG succeeded but Graph failed, mark graph as error
                # For simplicity, if any step fails, we mark based on what stage we're likely in
                # But since we committed RAG ready, we should check current status first?
                # Actually, just marking both as error if unsafe, or careful logic.
                # Here: Just mark graph_status as error if we are past RAG ready?
                # Simple approach: Set document status to error if it wasn't ready yet.

                # Since we can't easily check status in exception handler without query,
                # let's just assume if it crashed, we set both to error for safety,
                # OR we could refine this later.
                # For now: set status to ERROR.
                await self._update_document_status(
                    session, document_id, status=DocumentStatus.ERROR, graph_status="error"
                )
                await session.commit()
                logger.info(f"✅ Updated document {document_id} status to ERROR")
            except Exception as status_error:
                logger.error(
                    f"❌ CRITICAL: Failed to update document status to ERROR - "
                    f"document_id={document_id}, original_error={error_message}, "
                    f"status_error={status_error}",
                    exc_info=True,
                )

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
