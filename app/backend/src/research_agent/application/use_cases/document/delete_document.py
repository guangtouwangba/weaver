"""Delete document use case."""

from dataclasses import dataclass
from uuid import UUID

from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.domain.repositories.document_repo import DocumentRepository
from research_agent.infrastructure.storage.base import StorageService
from research_agent.shared.exceptions import NotFoundError
from research_agent.shared.utils.logger import logger


@dataclass
class DeleteDocumentInput:
    """Input for delete document use case."""

    document_id: UUID


@dataclass
class DeleteDocumentOutput:
    """Output for delete document use case."""

    success: bool


class DeleteDocumentUseCase:
    """Use case for deleting a document."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        storage: StorageService,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._storage = storage

    async def execute(self, input: DeleteDocumentInput) -> DeleteDocumentOutput:
        """Execute the use case."""
        # Get document
        document = await self._document_repo.find_by_id(input.document_id)
        if not document:
            raise NotFoundError("Document", str(input.document_id))

        # Delete chunks (cascade should handle this, but explicit is better)
        deleted_chunks = await self._chunk_repo.delete_by_document(input.document_id)
        logger.info(f"Deleted {deleted_chunks} chunks for document {input.document_id}")

        # Delete file from storage
        if document.file_path:
            await self._storage.delete(document.file_path)

        # Delete document
        await self._document_repo.delete(input.document_id)

        return DeleteDocumentOutput(success=True)

