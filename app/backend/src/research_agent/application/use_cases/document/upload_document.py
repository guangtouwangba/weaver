"""Upload document use case."""

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID

from research_agent.config import get_settings
from research_agent.domain.entities.document import Document
from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.entities.resource_chunk import ResourceChunk
from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.domain.repositories.document_repo import DocumentRepository
from research_agent.domain.services.chunking_service import ChunkingService
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.parser.factory import ParserFactory
from research_agent.infrastructure.storage.base import StorageService
from research_agent.infrastructure.thumbnail import ThumbnailFactory
from research_agent.shared.exceptions import DocumentProcessingError
from research_agent.shared.utils.logger import logger


def _get_mime_type(filename: str) -> str:
    """Detect MIME type from filename extension."""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    # Fallback for common types
    ext = Path(filename).suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    return mime_map.get(ext, "application/octet-stream")


@dataclass
class UploadDocumentInput:
    """Input for upload document use case."""

    project_id: UUID
    filename: str
    file_content: BinaryIO
    file_size: int
    user_id: str
    storage_path: Optional[str] = field(
        default=None
    )  # Supabase Storage path if using cloud storage


@dataclass
class UploadDocumentOutput:
    """Output for upload document use case."""

    id: UUID
    filename: str
    page_count: int
    status: str
    thumbnail_status: Optional[str] = None


class UploadDocumentUseCase:
    """Use case for uploading and processing documents (PDF, TXT, etc.)."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        storage: StorageService,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService | None = None,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._storage = storage
        self._embedding_service = embedding_service
        self._chunking_service = chunking_service or ChunkingService()

    async def execute(self, input: UploadDocumentInput) -> UploadDocumentOutput:
        """Execute the use case."""
        # Detect MIME type and file extension from filename
        mime_type = _get_mime_type(input.filename)
        file_extension = Path(input.filename).suffix.lower() or ".bin"

        # 1. Create document entity
        document = Document(
            project_id=input.project_id,
            user_id=input.user_id,
            filename=input.filename,
            original_filename=input.filename,  # Store original filename
            file_size=input.file_size,
            mime_type=mime_type,
        )
        document.mark_processing()

        # 2. Handle file storage (preserve original file extension)
        if input.storage_path:
            # File already uploaded to Supabase Storage
            document.file_path = input.storage_path
            # Save file content locally for processing (temp)
            # Use temp path for processing, doesn't need to match storage structure
            temp_path = f"temp/{input.project_id}/{document.id}{file_extension}"
            full_path = await self._storage.save(temp_path, input.file_content)
        else:
            # Traditional local storage
            # Use user-scoped path: {user_id}/projects/{project_id}/{document.id}{ext}
            file_path = f"{input.user_id}/projects/{input.project_id}/{document.id}{file_extension}"
            full_path = await self._storage.save(file_path, input.file_content)
            document.file_path = full_path

        # Generate thumbnail immediately (if supported)
        file_extension = Path(input.filename).suffix.lower()
        if ThumbnailFactory.is_supported(extension=file_extension):
            try:
                settings = get_settings()
                output_dir = (Path(settings.upload_dir) / "thumbnails").resolve()

                result = await ThumbnailFactory.generate(
                    file_path=full_path,
                    document_id=document.id,
                    output_dir=output_dir,
                    extension=file_extension,
                )

                if result.success and result.path:
                    document.thumbnail_path = result.path
                    document.thumbnail_status = "ready"
                    logger.info(f"✅ Thumbnail generated in use case for {document.id}")
            except Exception as e:
                logger.warning(f"⚠️ Thumbnail generation failed in use case: {e}")

        # Save document (processing status)
        await self._document_repo.save(document)

        try:
            # 3. Extract text from document using ParserFactory
            logger.info(f"Extracting text from document: {input.filename} (mime_type={mime_type})")
            parse_result = await ParserFactory.parse_with_mode(
                file_path=full_path,
                mode="standard",  # Auto-detect + OCR fallback for scanned PDFs
                mime_type=mime_type,
                extension=file_extension,
            )
            pages = parse_result.pages

            # 3.1 Store full document content for summary generation and other use cases
            full_text = "\n\n".join([page.content for page in pages if page.content])
            if full_text.strip():
                document.full_content = full_text
                logger.info(f"Stored full content: {len(full_text)} characters")

            # 4. Chunk the text
            logger.info(f"Chunking {len(pages)} pages")
            chunk_data = self._chunking_service.chunk_pages(pages)

            # 5. Create chunk entities using ResourceChunk
            chunks = [
                ResourceChunk(
                    resource_id=document.id,
                    resource_type=ResourceType.DOCUMENT,
                    project_id=input.project_id,
                    user_id=input.user_id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    metadata={
                        "page_number": c["page_number"],
                        "title": input.filename,
                    },
                )
                for c in chunk_data
            ]

            # 6. Generate embeddings
            if chunks:
                logger.info(f"Generating embeddings for {len(chunks)} chunks")
                contents = [c.content for c in chunks]
                embeddings = await self._embedding_service.embed_batch(contents)

                for chunk, embedding in zip(chunks, embeddings):
                    chunk.set_embedding(embedding)

                # 7. Save chunks
                await self._chunk_repo.save_batch(chunks)

            # 8. Update document status
            document.mark_ready(page_count=len(pages))
            await self._document_repo.save(document)

            logger.info(f"Document processed successfully: {document.id}")

            return UploadDocumentOutput(
                id=document.id,
                filename=document.filename,
                page_count=document.page_count,
                status=document.status.value,
                thumbnail_status=document.thumbnail_status,
            )

        except Exception as e:
            # Mark document as error
            document.mark_error()
            await self._document_repo.save(document)
            logger.error(f"Failed to process document: {e}")
            raise DocumentProcessingError(f"Failed to process document: {e}")
