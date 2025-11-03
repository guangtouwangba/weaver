"""Core data models for RAG system."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """Universal document model for RAG system.

    This model represents a document chunk or passage that can be
    retrieved, processed, and used for generation.

    Attributes:
        page_content: The actual text content of the document.
        metadata: Additional information about the document (source, page number, etc.).
        score: Relevance score from retrieval (0.0 to 1.0).
        id: Optional unique identifier for the document.
    """

    page_content: str = Field(..., description="The text content of the document")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score")
    id: str | None = Field(default=None, description="Unique document identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page_content": "Python is a high-level programming language.",
                "metadata": {
                    "source": "python_docs.pdf",
                    "page": 1,
                    "section": "Introduction",
                },
                "score": 0.95,
                "id": "doc_123",
            }
        }
    )

    def __str__(self) -> str:
        """String representation of the document."""
        content_preview = (
            self.page_content[:100] + "..." if len(self.page_content) > 100 else self.page_content
        )
        return f"Document(score={self.score:.2f}, content='{content_preview}')"

    def __repr__(self) -> str:
        """Detailed representation of the document."""
        return (
            f"Document(id={self.id}, score={self.score:.2f}, "
            f"metadata={self.metadata}, content_length={len(self.page_content)})"
        )

