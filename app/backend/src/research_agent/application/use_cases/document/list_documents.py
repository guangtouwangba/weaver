"""List documents use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID

from research_agent.domain.repositories.document_repo import DocumentRepository


@dataclass
class DocumentItem:
    """Document item in list."""

    id: UUID
    project_id: UUID
    filename: str
    file_size: int
    page_count: int
    status: str
    created_at: datetime


@dataclass
class ListDocumentsInput:
    """Input for list documents use case."""

    project_id: UUID


@dataclass
class ListDocumentsOutput:
    """Output for list documents use case."""

    items: List[DocumentItem]
    total: int


class ListDocumentsUseCase:
    """Use case for listing documents in a project."""

    def __init__(self, document_repo: DocumentRepository):
        self._document_repo = document_repo

    async def execute(self, input: ListDocumentsInput) -> ListDocumentsOutput:
        """Execute the use case."""
        documents = await self._document_repo.find_by_project(input.project_id)

        items = [
            DocumentItem(
                id=d.id,
                project_id=d.project_id,
                filename=d.filename,
                file_size=d.file_size,
                page_count=d.page_count,
                status=d.status.value,
                created_at=d.created_at,
            )
            for d in documents
        ]

        return ListDocumentsOutput(
            items=items,
            total=len(items),
        )

