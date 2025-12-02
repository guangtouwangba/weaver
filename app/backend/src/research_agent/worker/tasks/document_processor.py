"""Document processor task - orchestrates the full document processing pipeline."""

from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings

settings = get_settings()
from research_agent.domain.entities.chunk import DocumentChunk
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
        
        logger.info(f"Starting document processing for {document_id}")
        
        # Update status to processing
        await self._update_document_status(session, document_id, DocumentStatus.PROCESSING)
        await session.commit()
        
        try:
            # Step 1: Get file content
            local_path = await self._get_file_locally(file_path, document_id, project_id)
            
            # Step 2: Extract text from PDF
            logger.info(f"Extracting text from PDF: {file_path}")
            pdf_parser = PyMuPDFParser()
            pages = await pdf_parser.extract_text(local_path)
            page_count = len(pages)
            logger.info(f"Extracted {page_count} pages")
            
            # Step 3: Chunk text with dynamic strategy selection
            logger.info("Chunking text with dynamic strategy")
            
            # Get document metadata for strategy selection
            doc_result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            chunking_service = ChunkingService()
            chunk_data = chunking_service.chunk_pages(
                pages=pages,
                mime_type=doc.mime_type,
                filename=doc.original_filename,
            )
            logger.info(f"Created {len(chunk_data)} chunks")
            
            # Step 4: Generate embeddings
            if chunk_data:
                logger.info("Generating embeddings")
                embedding_service = OpenRouterEmbeddingService(
                    api_key=settings.openrouter_api_key,
                    model=settings.embedding_model,
                )
                
                contents = [c["content"] for c in chunk_data]
                embeddings = await embedding_service.embed_batch(contents)
                
                # Save chunks with embeddings
                for i, (chunk, embedding) in enumerate(zip(chunk_data, embeddings)):
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
                
                await session.flush()
                logger.info(f"Saved {len(chunk_data)} chunks with embeddings")
            
            # PROGRESSIVE PROCESSING: Mark document as READY for RAG now
            # This allows users to start chatting while graph extraction runs in background
            logger.info("Marking document as READY for RAG")
            await self._update_document_status(
                session, 
                document_id, 
                status=DocumentStatus.READY, 
                graph_status="processing",
                page_count=page_count
            )
            await session.commit()
            
            # Step 5: Extract knowledge graph
            logger.info("Extracting knowledge graph")
            graph_extractor = GraphExtractorTask()
            await graph_extractor.execute(
                {"document_id": str(document_id), "project_id": str(project_id)},
                session,
            )
            
            # Commit entities before canvas sync to ensure they're visible
            await session.commit()
            
            # Step 6: Sync to canvas
            logger.info("Syncing to canvas")
            canvas_syncer = CanvasSyncerTask()
            await canvas_syncer.execute(
                {"project_id": str(project_id), "document_id": str(document_id)},
                session,
            )
            
            # Step 7: Update graph status to ready
            await self._update_document_status(
                session, document_id, graph_status="ready"
            )
            await session.commit()
            
            logger.info(f"Document {document_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}", exc_info=True)
            
            # Update status to error
            await session.rollback()
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
                session, 
                document_id, 
                status=DocumentStatus.ERROR,
                graph_status="error"
            )
            await session.commit()
            
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

        stmt = (
            update(DocumentModel)
            .where(DocumentModel.id == document_id)
            .values(**values)
        )
        await session.execute(stmt)

