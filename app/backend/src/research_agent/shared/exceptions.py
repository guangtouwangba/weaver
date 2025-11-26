"""Custom exceptions for the application."""


class ResearchAgentError(Exception):
    """Base exception for the application."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(ResearchAgentError):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: str):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} with id '{resource_id}' not found")


class ValidationError(ResearchAgentError):
    """Validation error."""

    pass


class StorageError(ResearchAgentError):
    """Storage operation error."""

    pass


class LLMError(ResearchAgentError):
    """LLM service error."""

    pass


class EmbeddingError(ResearchAgentError):
    """Embedding service error."""

    pass


class PDFProcessingError(ResearchAgentError):
    """PDF processing error."""

    pass

