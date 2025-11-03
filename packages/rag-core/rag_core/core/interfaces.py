"""Core interfaces for RAG system components."""

from abc import ABC, abstractmethod

from rag_core.core.models import Document


class RetrieverInterface(ABC):
    """Abstract interface for document retrievers.

    All retriever implementations must inherit from this interface and
    implement the required methods.
    """

    @abstractmethod
    async def retrieve(self, query: str, top_k: int | None = None) -> list[Document]:
        """Retrieve relevant documents for a given query.

        Args:
            query: The search query string.
            top_k: Number of top documents to return. If None, uses default from config.

        Returns:
            List of Document objects sorted by relevance score (highest first).

        Raises:
            RetrieverException: If retrieval fails.
        """
        pass

    @abstractmethod
    def get_config(self) -> dict:
        """Get the current configuration of the retriever.

        Returns:
            Dictionary containing retriever configuration.
        """
        pass

    def retrieve_sync(self, query: str, top_k: int | None = None) -> list[Document]:
        """Synchronous version of retrieve (optional, for backward compatibility).

        Args:
            query: The search query string.
            top_k: Number of top documents to return.

        Returns:
            List of Document objects.
        """
        import asyncio

        return asyncio.run(self.retrieve(query, top_k))


class GeneratorInterface(ABC):
    """Abstract interface for answer generators.

    All generator implementations must inherit from this interface and
    implement the required methods.
    """

    @abstractmethod
    async def generate(
        self, query: str, context: list[Document], stream: bool = False
    ) -> str | list[str]:
        """Generate an answer based on query and context documents.

        Args:
            query: The user's question or query.
            context: List of relevant documents to use as context.
            stream: If True, return generator for streaming response.

        Returns:
            Generated answer as string, or list of chunks if streaming.

        Raises:
            GeneratorException: If generation fails.
        """
        pass

    @abstractmethod
    def get_config(self) -> dict:
        """Get the current configuration of the generator.

        Returns:
            Dictionary containing generator configuration.
        """
        pass

    def generate_sync(
        self, query: str, context: list[Document], stream: bool = False
    ) -> str | list[str]:
        """Synchronous version of generate (optional).

        Args:
            query: The user's question.
            context: List of relevant documents.
            stream: Whether to stream the response.

        Returns:
            Generated answer.
        """
        import asyncio

        return asyncio.run(self.generate(query, context, stream))


class RerankerInterface(ABC):
    """Abstract interface for document rerankers (optional).

    Rerankers take an initial set of retrieved documents and reorder them
    based on more sophisticated relevance scoring.
    """

    @abstractmethod
    async def rerank(self, query: str, documents: list[Document]) -> list[Document]:
        """Rerank documents based on relevance to the query.

        Args:
            query: The search query.
            documents: List of documents to rerank.

        Returns:
            Reranked list of documents (highest relevance first).
        """
        pass

    @abstractmethod
    def get_config(self) -> dict:
        """Get the current configuration of the reranker.

        Returns:
            Dictionary containing reranker configuration.
        """
        pass


class MemoryInterface(ABC):
    """Abstract interface for conversation memory (optional).

    Memory implementations manage conversation history and context
    for multi-turn interactions.
    """

    @abstractmethod
    async def save_context(self, inputs: dict, outputs: dict) -> None:
        """Save conversation context to memory.

        Args:
            inputs: Dictionary containing user inputs (e.g., {"query": "..."}).
            outputs: Dictionary containing system outputs (e.g., {"answer": "..."}).
        """
        pass

    @abstractmethod
    async def load_memory(self, session_id: str | None = None) -> list[dict]:
        """Load conversation history from memory.

        Args:
            session_id: Optional session identifier for multi-user scenarios.

        Returns:
            List of conversation turns as dictionaries.
        """
        pass

    @abstractmethod
    async def clear_memory(self, session_id: str | None = None) -> None:
        """Clear conversation memory.

        Args:
            session_id: Optional session identifier to clear specific session.
        """
        pass

