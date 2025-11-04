"""TopicContent service layer for business logic."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain_models.topic_content import TopicContent, ContentStatus
from domain_models.topic_content_schemas import (
    TopicContentCreate,
    TopicContentUpdate,
    TopicContentStats,
)
from domain_models.topic import Topic


class TopicContentService:
    """Service class for TopicContent business logic."""

    @staticmethod
    def create_content(db: Session, topic_id: str | UUID, content_data: TopicContentCreate) -> TopicContent:
        """
        Create a new content for a topic.

        Args:
            db: Database session
            topic_id: Topic UUID
            content_data: Content creation data

        Returns:
            Created TopicContent instance
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        content = TopicContent(
            topic_id=topic_id,
            title=content_data.title,
            description=content_data.description,
            source_type=content_data.source_type.value,
            source_url=content_data.source_url,
            document_id=content_data.document_id,
            author=content_data.author,
            tags=content_data.tags,
        )
        db.add(content)
        
        # Update topic total_contents count
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if topic:
            topic.total_contents += 1
        
        db.commit()
        db.refresh(content)
        return content

    @staticmethod
    def get_content(db: Session, content_id: str | UUID) -> Optional[TopicContent]:
        """
        Get a content by ID.

        Args:
            db: Database session
            content_id: Content UUID

        Returns:
            TopicContent instance or None if not found
        """
        if isinstance(content_id, str):
            content_id = UUID(content_id)
        return db.query(TopicContent).filter(TopicContent.id == content_id).first()

    @staticmethod
    def list_contents(
        db: Session,
        topic_id: str | UUID,
        status: Optional[ContentStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TopicContent]:
        """
        List contents for a topic with optional filtering.

        Args:
            db: Database session
            topic_id: Topic UUID
            status: Filter by status (optional)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of TopicContent instances
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        query = db.query(TopicContent).filter(TopicContent.topic_id == topic_id)

        if status:
            query = query.filter(TopicContent.status == status.value)

        return query.order_by(TopicContent.added_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_content(
        db: Session, content_id: str | UUID, content_data: TopicContentUpdate
    ) -> Optional[TopicContent]:
        """
        Update a content.

        Args:
            db: Database session
            content_id: Content UUID
            content_data: Content update data

        Returns:
            Updated TopicContent instance or None if not found
        """
        if isinstance(content_id, str):
            content_id = UUID(content_id)

        content = db.query(TopicContent).filter(TopicContent.id == content_id).first()
        if not content:
            return None

        # Track status change for topic statistics
        old_status = content.status
        
        # Update only provided fields
        update_data = content_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "status" and value is not None:
                setattr(content, key, value.value)
            else:
                setattr(content, key, value)
        
        # Update topic statistics if status changed
        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"].value
            if old_status != new_status:
                topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
                if topic:
                    # Decrease old status count
                    if old_status == ContentStatus.UNDERSTOOD.value:
                        topic.understood_contents = max(0, topic.understood_contents - 1)
                    elif old_status == ContentStatus.PRACTICED.value:
                        topic.practiced_contents = max(0, topic.practiced_contents - 1)
                    
                    # Increase new status count
                    if new_status == ContentStatus.UNDERSTOOD.value:
                        topic.understood_contents += 1
                    elif new_status == ContentStatus.PRACTICED.value:
                        topic.practiced_contents += 1
                    
                    # Recalculate progress
                    topic.completion_progress = topic.calculate_progress()

        db.commit()
        db.refresh(content)
        return content

    @staticmethod
    def delete_content(db: Session, content_id: str | UUID) -> bool:
        """
        Delete a content.

        Args:
            db: Database session
            content_id: Content UUID

        Returns:
            True if deleted, False if not found
        """
        if isinstance(content_id, str):
            content_id = UUID(content_id)

        content = db.query(TopicContent).filter(TopicContent.id == content_id).first()
        if not content:
            return False

        # Update topic statistics
        topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
        if topic:
            topic.total_contents = max(0, topic.total_contents - 1)
            if content.status == ContentStatus.UNDERSTOOD.value:
                topic.understood_contents = max(0, topic.understood_contents - 1)
            elif content.status == ContentStatus.PRACTICED.value:
                topic.practiced_contents = max(0, topic.practiced_contents - 1)
            topic.completion_progress = topic.calculate_progress()

        db.delete(content)
        db.commit()
        return True

    @staticmethod
    def get_content_stats(db: Session, topic_id: str | UUID) -> TopicContentStats:
        """
        Get content statistics for a topic.

        Args:
            db: Database session
            topic_id: Topic UUID

        Returns:
            TopicContentStats with counts by status
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        total = db.query(func.count(TopicContent.id)).filter(TopicContent.topic_id == topic_id).scalar() or 0
        
        pending = (
            db.query(func.count(TopicContent.id))
            .filter(TopicContent.topic_id == topic_id, TopicContent.status == ContentStatus.PENDING.value)
            .scalar() or 0
        )
        
        reading = (
            db.query(func.count(TopicContent.id))
            .filter(TopicContent.topic_id == topic_id, TopicContent.status == ContentStatus.READING.value)
            .scalar() or 0
        )
        
        understood = (
            db.query(func.count(TopicContent.id))
            .filter(TopicContent.topic_id == topic_id, TopicContent.status == ContentStatus.UNDERSTOOD.value)
            .scalar() or 0
        )
        
        questioned = (
            db.query(func.count(TopicContent.id))
            .filter(TopicContent.topic_id == topic_id, TopicContent.status == ContentStatus.QUESTIONED.value)
            .scalar() or 0
        )
        
        practiced = (
            db.query(func.count(TopicContent.id))
            .filter(TopicContent.topic_id == topic_id, TopicContent.status == ContentStatus.PRACTICED.value)
            .scalar() or 0
        )
        
        avg_understanding_result = (
            db.query(func.avg(TopicContent.understanding_level))
            .filter(TopicContent.topic_id == topic_id)
            .scalar()
        )
        avg_understanding = float(avg_understanding_result) if avg_understanding_result is not None else 0.0

        return TopicContentStats(
            total=total,
            pending=pending,
            reading=reading,
            understood=understood,
            questioned=questioned,
            practiced=practiced,
            avg_understanding=avg_understanding,
        )

