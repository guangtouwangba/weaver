"""Vector-based retriever implementation using FAISS."""

from typing import Any

from langchain_community.vectorstores import FAISS

from rag_core.core.exceptions import RetrieverException
from rag_core.core.interfaces import RetrieverInterface
from rag_core.core.models import Document


class VectorRetriever(RetrieverInterface):
    """Vector similarity retriever using FAISS.

    This retriever uses vector embeddings to find semantically similar
    documents based on cosine similarity or other distance metrics.

    Attributes:
        vector_store: The FAISS vector store instance.
        top_k: Default number of documents to retrieve.
        search_type: Type of search ('similarity', 'mmr', etc.).
        search_kwargs: Additional search parameters.
    """

    def __init__(
        self,
        vector_store: FAISS | None = None,
        top_k: int = 4,
        search_type: str = "similarity",
        search_kwargs: dict[str, Any] | None = None,
    ):
        """Initialize vector retriever.

        Args:
            vector_store: FAISS vector store instance.
            top_k: Default number of documents to retrieve.
            search_type: Type of search to perform.
            search_kwargs: Additional search parameters.
        """
        self.vector_store = vector_store
        self.top_k = top_k
        self.search_type = search_type
        self.search_kwargs = search_kwargs or {}

    async def retrieve(self, query: str, top_k: int | None = None) -> list[Document]:
        """Retrieve relevant documents using vector similarity.

        Args:
            query: The search query string.
            top_k: Number of documents to return. If None, uses default.

        Returns:
            List of Document objects sorted by relevance score.

        Raises:
            RetrieverException: If vector store is not initialized or retrieval fails.
        """
        if self.vector_store is None:
            raise RetrieverException(
                "Vector store not initialized. Please ingest documents first.",
                details={"retriever_type": "vector"},
            )

        k = top_k if top_k is not None else self.top_k

        try:
            # Prepare search kwargs
            search_kwargs = {**self.search_kwargs, "k": k}

            # Perform similarity search with scores
            if self.search_type == "similarity":
                results = self.vector_store.similarity_search_with_score(query, k=k)

                # Convert to our Document model
                documents = []
                for doc, score in results:
                    # FAISS returns distance, convert to similarity score (0-1)
                    # Lower distance = higher similarity
                    similarity_score = 1.0 / (1.0 + score)

                    documents.append(
                        Document(
                            page_content=doc.page_content,
                            metadata=doc.metadata,
                            score=similarity_score,
                        )
                    )

                return documents

            elif self.search_type == "mmr":
                # Maximum Marginal Relevance for diversity
                results = self.vector_store.max_marginal_relevance_search(
                    query, k=k, fetch_k=k * 2, lambda_mult=self.search_kwargs.get("lambda_mult", 0.5)
                )

                # MMR doesn't return scores, use default
                documents = [
                    Document(
                        page_content=doc.page_content,
                        metadata=doc.metadata,
                        score=0.8,  # Default score for MMR results
                    )
                    for doc in results
                ]

                return documents

            else:
                raise RetrieverException(
                    f"Unsupported search type: {self.search_type}",
                    details={"supported_types": ["similarity", "mmr"]},
                )

        except RetrieverException:
            raise
        except Exception as e:
            raise RetrieverException(
                f"Vector retrieval failed: {str(e)}",
                details={"query": query, "top_k": k, "search_type": self.search_type},
            ) from e

    def get_config(self) -> dict:
        """Get retriever configuration.

        Returns:
            Dictionary with retriever settings.
        """
        return {
            "type": "vector",
            "top_k": self.top_k,
            "search_type": self.search_type,
            "search_kwargs": self.search_kwargs,
            "vector_store_initialized": self.vector_store is not None,
        }

    def set_vector_store(self, vector_store: FAISS) -> None:
        """Set or update the vector store.

        Args:
            vector_store: New FAISS vector store instance.
        """
        self.vector_store = vector_store

    def get_vector_store(self) -> FAISS | None:
        """Get the current vector store.

        Returns:
            FAISS vector store instance or None if not initialized.
        """
        return self.vector_store

