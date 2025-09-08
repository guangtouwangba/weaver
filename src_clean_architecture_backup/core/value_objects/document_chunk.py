"""
Document chunk value object.

Represents an immutable document chunk with content and metadata.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from uuid import uuid4


@dataclass(frozen=True)
class DocumentChunk:
    """Immutable document chunk value object."""
    
    id: str
    document_id: str
    content: str
    chunk_index: int
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding_vector: Optional[List[float]] = None
    
    @classmethod
    def create(
        cls,
        document_id: str,
        content: str,
        chunk_index: int,
        start_char: Optional[int] = None,
        end_char: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_vector: Optional[List[float]] = None
    ) -> 'DocumentChunk':
        """Create a new document chunk."""
        return cls(
            id=str(uuid4()),
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            metadata=metadata,
            embedding_vector=embedding_vector
        )
    
    def get_word_count(self) -> int:
        """Get word count of the chunk content."""
        return len(self.content.split())
    
    def get_char_count(self) -> int:
        """Get character count of the chunk content."""
        return len(self.content)
    
    def has_embedding(self) -> bool:
        """Check if chunk has an embedding vector."""
        return self.embedding_vector is not None and len(self.embedding_vector) > 0
    
    def get_text_range(self) -> Optional[tuple[int, int]]:
        """Get the text range (start_char, end_char) if available."""
        if self.start_char is not None and self.end_char is not None:
            return (self.start_char, self.end_char)
        return None
    
    def with_embedding(self, embedding_vector: List[float]) -> 'DocumentChunk':
        """Create a new chunk with embedding vector."""
        return DocumentChunk(
            id=self.id,
            document_id=self.document_id,
            content=self.content,
            chunk_index=self.chunk_index,
            start_char=self.start_char,
            end_char=self.end_char,
            metadata=self.metadata,
            embedding_vector=embedding_vector
        )