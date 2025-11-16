"""Custom exceptions for RAG system."""


class RAGException(Exception):
    """Base exception for all RAG-related errors.

    All custom exceptions in the RAG system should inherit from this class.
    """

    def __init__(self, message: str, details: dict | None = None):
        """Initialize RAG exception.

        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class RetrieverException(RAGException):
    """Exception raised during document retrieval.

    Examples:
        - Vector store not initialized
        - Search query failed
        - Invalid search parameters
    """

    pass


class GeneratorException(RAGException):
    """Exception raised during answer generation.

    Examples:
        - LLM API call failed
        - Context too long
        - Invalid prompt template
    """

    pass


class ConfigurationException(RAGException):
    """Exception raised for configuration errors.

    Examples:
        - Missing required configuration
        - Invalid configuration values
        - Incompatible settings
    """

    pass


class EmbeddingException(RAGException):
    """Exception raised during embedding generation.

    Examples:
        - Embedding API call failed
        - Invalid text for embedding
        - Dimension mismatch
    """

    pass


class DocumentProcessingException(RAGException):
    """Exception raised during document processing.

    Examples:
        - Document parsing failed
        - Text chunking error
        - Invalid document format
    """

    pass


class RerankerException(RAGException):
    """Exception raised during document reranking.

    Examples:
        - Reranker model not loaded
        - Reranking inference failed
        - Invalid reranker configuration
    """

    pass

