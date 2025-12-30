"""SQLAlchemy repository for comments."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import CommentModel


class SQLAlchemyCommentRepository:
    """Repository for managing comments in the database."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, comment: CommentModel) -> CommentModel:
        """Create a new comment."""
        self.session.add(comment)
        await self.session.flush()
        await self.session.refresh(comment)
        return comment

    async def find_by_id(self, comment_id: UUID) -> Optional[CommentModel]:
        """Find a comment by ID."""
        result = await self.session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def list_by_document(self, document_id: UUID) -> List[CommentModel]:
        """List all top-level comments for a document (excluding replies)."""
        result = await self.session.execute(
            select(CommentModel)
            .where(CommentModel.document_id == document_id)
            .where(CommentModel.parent_id.is_(None))
            .order_by(CommentModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_replies(self, parent_id: UUID) -> List[CommentModel]:
        """List all replies to a comment."""
        result = await self.session.execute(
            select(CommentModel)
            .where(CommentModel.parent_id == parent_id)
            .order_by(CommentModel.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_by_document(self, document_id: UUID) -> int:
        """Count total comments for a document."""
        result = await self.session.execute(
            select(CommentModel).where(CommentModel.document_id == document_id)
        )
        return len(result.scalars().all())

    async def update(self, comment: CommentModel) -> CommentModel:
        """Update a comment."""
        await self.session.flush()
        await self.session.refresh(comment)
        return comment

    async def delete(self, comment_id: UUID) -> None:
        """Delete a comment and all its replies (cascade)."""
        comment = await self.find_by_id(comment_id)
        if comment:
            await self.session.delete(comment)
            await self.session.flush()
