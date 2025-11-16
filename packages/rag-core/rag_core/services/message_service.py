"""MessageService for managing conversation messages."""

from typing import List, Optional
from uuid import UUID
import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain_models import Message, MessageCreate


class MessageService:
    """Service class for Message business logic."""

    @staticmethod
    def create_message(
        db: Session,
        conversation_id: str | UUID,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
        embedding: Optional[List[float]] = None
    ) -> Message:
        """
        Create a new message.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            role: Message role ('user' or 'assistant')
            content: Message content
            sources: Source documents (for assistant messages)
            embedding: Embedding vector for semantic search (optional)

        Returns:
            Created Message instance
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        # Convert sources to JSON strings array for storage
        sources_array = None
        if sources:
            sources_array = [json.dumps(source) for source in sources]

        # pgvector's Vector type accepts Python list directly, no need to convert to string
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources_array,
            embedding=embedding,  # Pass list directly, pgvector handles conversion
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_message(db: Session, message_id: str | UUID) -> Optional[Message]:
        """
        Get a message by ID.

        Args:
            db: Database session
            message_id: Message UUID

        Returns:
            Message instance or None
        """
        if isinstance(message_id, str):
            message_id = UUID(message_id)

        return db.query(Message).filter(Message.id == message_id).first()

    @staticmethod
    def list_messages(
        db: Session,
        conversation_id: str | UUID,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Message], int]:
        """
        List messages for a conversation with pagination.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (messages list, total count)
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        query = db.query(Message).filter(Message.conversation_id == conversation_id)
        
        total = query.count()
        messages = query.order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
        
        return messages, total

    @staticmethod
    def get_recent_messages(
        db: Session,
        conversation_id: str | UUID,
        limit: int = 10
    ) -> List[Message]:
        """
        Get the most recent N messages from a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            limit: Maximum number of messages to return

        Returns:
            List of recent messages (ordered by created_at ascending)
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        
        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))

    @staticmethod
    def delete_message(db: Session, message_id: str | UUID) -> bool:
        """
        Delete a message.

        Args:
            db: Database session
            message_id: Message UUID

        Returns:
            True if deleted, False if not found
        """
        if isinstance(message_id, str):
            message_id = UUID(message_id)

        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return False

        db.delete(message)
        db.commit()
        return True

    @staticmethod
    def count_by_conversation(db: Session, conversation_id: str | UUID) -> int:
        """
        Count messages in a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            Number of messages
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        return db.query(func.count(Message.id)).filter(Message.conversation_id == conversation_id).scalar()

    @staticmethod
    def find_similar_messages(
        db: Session,
        conversation_id: str | UUID,
        query_embedding: List[float],
        limit: int = 3,
        similarity_threshold: float = 0.7
    ) -> List[Message]:
        """
        Find similar messages using vector similarity search within a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID to search within
            query_embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum cosine similarity (0-1)

        Returns:
            List of similar messages ordered by similarity (most similar first)
        """
        if isinstance(conversation_id, str):
            conversation_id = UUID(conversation_id)

        # Convert embedding to pgvector format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # Use cosine similarity: 1 - (embedding <=> query_embedding)
        # Higher values = more similar
        from sqlalchemy import text
        
        query = text(f"""
            SELECT id, conversation_id, role, content, sources, created_at,
                   1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM messages
            WHERE conversation_id = :conversation_id
              AND embedding IS NOT NULL
              AND 1 - (embedding <=> '{embedding_str}'::vector) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)

        result = db.execute(
            query,
            {
                "conversation_id": str(conversation_id),
                "threshold": similarity_threshold,
                "limit": limit
            }
        )
        rows = result.fetchall()

        # Convert rows to Message objects
        messages = []
        for row in rows:
            message = db.query(Message).filter(Message.id == row[0]).first()
            if message:
                messages.append(message)

        return messages

    @staticmethod
    def find_similar_messages_in_topic(
        db: Session,
        topic_id: str | UUID,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.7,
        exclude_conversation_id: Optional[str | UUID] = None
    ) -> List[Message]:
        """
        Find similar messages across all conversations in a topic.
        
        This enables cross-conversation memory retrieval, useful for:
        - Finding relevant answers from other conversations
        - Building topic-level knowledge base
        - Surfacing related discussions

        Args:
            db: Database session
            topic_id: Topic UUID to search within
            query_embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum cosine similarity (0-1)
            exclude_conversation_id: Optional conversation ID to exclude (e.g., current conversation)

        Returns:
            List of similar messages ordered by similarity (most similar first)
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)
        if isinstance(exclude_conversation_id, str):
            exclude_conversation_id = UUID(exclude_conversation_id)

        # Convert embedding to pgvector format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        from sqlalchemy import text
        
        # Join with conversations table to filter by topic_id
        exclude_clause = ""
        if exclude_conversation_id:
            exclude_clause = f"AND m.conversation_id != '{str(exclude_conversation_id)}'"
        
        query = text(f"""
            SELECT m.id, m.conversation_id, m.role, m.content, m.sources, m.created_at,
                   1 - (m.embedding <=> '{embedding_str}'::vector) as similarity
            FROM messages m
            INNER JOIN conversations c ON m.conversation_id = c.id
            WHERE c.topic_id = :topic_id
              AND m.embedding IS NOT NULL
              AND 1 - (m.embedding <=> '{embedding_str}'::vector) > :threshold
              {exclude_clause}
            ORDER BY similarity DESC
            LIMIT :limit
        """)

        result = db.execute(
            query,
            {
                "topic_id": str(topic_id),
                "threshold": similarity_threshold,
                "limit": limit
            }
        )
        rows = result.fetchall()

        # Convert rows to Message objects with similarity score
        from domain_models import Message as MessageModel
        messages = []
        for row in rows:
            message = db.query(MessageModel).filter(MessageModel.id == row[0]).first()
            if message:
                # Attach similarity score as a temporary attribute
                message.similarity = row[6]
                messages.append(message)

        return messages

