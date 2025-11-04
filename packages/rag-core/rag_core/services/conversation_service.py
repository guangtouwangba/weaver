"""ConversationService for managing conversation sessions."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain_models import Conversation, ConversationCreate, ConversationUpdate


class ConversationService:
    """Service class for Conversation business logic."""

    @staticmethod
    def create_conversation(db: Session, conversation_data: ConversationCreate) -> Conversation:
        """
        Create a new conversation.

        Args:
            db: Database session
            conversation_data: Conversation creation data

        Returns:
            Created Conversation instance
        """
        conversation = Conversation(
            topic_id=conversation_data.topic_id,
            title=conversation_data.title,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get_conversation(db: Session, conversation_id: str | UUID) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            Conversation instance or None
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def list_conversations(
        db: Session,
        topic_id: str | UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Conversation], int]:
        """
        List conversations for a topic with pagination.

        Args:
            db: Database session
            topic_id: Topic UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (conversations list, total count)
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        query = db.query(Conversation).filter(Conversation.topic_id == topic_id)
        
        total = query.count()
        conversations = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
        
        return conversations, total

    @staticmethod
    def update_conversation(
        db: Session,
        conversation_id: str | UUID,
        update_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """
        Update a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            update_data: Update data

        Returns:
            Updated Conversation or None
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return None

        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(conversation, key, value)

        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def delete_conversation(db: Session, conversation_id: str | UUID) -> bool:
        """
        Delete a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            True if deleted, False if not found
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return False

        db.delete(conversation)
        db.commit()
        return True

    @staticmethod
    def count_by_topic(db: Session, topic_id: str | UUID) -> int:
        """
        Count conversations for a topic.

        Args:
            db: Database session
            topic_id: Topic UUID

        Returns:
            Number of conversations
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        return db.query(func.count(Conversation.id)).filter(Conversation.topic_id == topic_id).scalar()

