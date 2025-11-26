"""Upload document use case."""

from dataclasses import dataclass
from typing import BinaryIO
from uuid import UUID

from research_agent.domain.entities.chunk import DocumentChunk
from research_agent.domain.entities.document import Document
from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.domain.repositories.document_repo import DocumentRepository
from research_agent.domain.services.chunking_service import ChunkingService
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.pdf.base import PDFParser
from research_agent.infrastructure.storage.base import StorageService
from research_agent.shared.exceptions import PDFProcessingError
from research_agent.shared.utils.logger import logger


@dataclass
class UploadDocumentInput:
    """Input for upload document use case."""

    project_id: UUID
    filename: str
    file_content: BinaryIO
    file_size: int


@dataclass
class UploadDocumentOutput:
    """Output for upload document use case."""

    id: UUID
    filename: str
    page_count: int
    status: str


class UploadDocumentUseCase:
    """Use case for uploading and processing a PDF document."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        storage: StorageService,
        pdf_parser: PDFParser,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService | None = None,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._storage = storage
        self._pdf_parser = pdf_parser
        self._embedding_service = embedding_service
        self._chunking_service = chunking_service or ChunkingService()

    async def execute(self, input: UploadDocumentInput) -> UploadDocumentOutput:
        """Execute the use case."""
        # 1. Create document entity
        document = Document(
            project_id=input.project_id,
            filename=input.filename,
            file_size=input.file_size,
        )
        document.mark_processing()

        # 2. Save file to storage
        file_path = f"projects/{input.project_id}/{document.id}.pdf"
        full_path = await self._storage.save(file_path, input.file_content)
        document.file_path = full_path

        # Save document (processing status)
        await self._document_repo.save(document)

        try:
            # 3. Extract text from PDF
            logger.info(f"Extracting text from PDF: {input.filename}")
            pages = await self._pdf_parser.extract_text(full_path)

            # 4. Chunk the text
            logger.info(f"Chunking {len(pages)} pages")
            chunk_data = self._chunking_service.chunk_pages(pages)

            # 5. Create chunk entities
            chunks = [
                DocumentChunk(
                    document_id=document.id,
                    project_id=input.project_id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    page_number=c["page_number"],
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
            )

        except Exception as e:
            # Mark document as error
            document.mark_error()
            await self._document_repo.save(document)
            logger.error(f"Failed to process document: {e}")
            raise PDFProcessingError(f"Failed to process document: {e}")

