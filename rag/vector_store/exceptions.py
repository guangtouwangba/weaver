"""
Vector store exception classes.
"""


class VectorStoreError(Exception):
    """Base vector store exception."""
    
    def __init__(self, message: str = "Vector store operation failed", details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class EmbeddingDimensionError(VectorStoreError):
    """Embedding dimension mismatch error."""
    
    def __init__(self, expected_dim: int, actual_dim: int, details: str = None):
        message = f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}"
        super().__init__(message, details)
        self.expected_dim = expected_dim
        self.actual_dim = actual_dim


class VectorNotFoundError(VectorStoreError):
    """Vector not found error."""
    
    def __init__(self, vector_id: str, details: str = None):
        message = f"Vector not found: {vector_id}"
        super().__init__(message, details)
        self.vector_id = vector_id


class CollectionNotFoundError(VectorStoreError):
    """Collection not found error."""
    
    def __init__(self, collection_name: str, details: str = None):
        message = f"Collection not found: {collection_name}"
        super().__init__(message, details)
        self.collection_name = collection_name


class VectorStorageConnectionError(VectorStoreError):
    """Vector storage connection error."""
    
    def __init__(self, storage_type: str, details: str = None):
        message = f"Vector storage connection failed: {storage_type}"
        super().__init__(message, details)
        self.storage_type = storage_type


class VectorStorageOperationError(VectorStoreError):
    """Vector storage operation error."""
    
    def __init__(self, operation: str, details: str = None):
        message = f"Vector storage operation failed: {operation}"
        super().__init__(message, details)
        self.operation = operation


class InvalidEmbeddingError(VectorStoreError):
    """Invalid embedding error."""
    
    def __init__(self, reason: str, details: str = None):
        message = f"Invalid embedding: {reason}"
        super().__init__(message, details)
        self.reason = reason