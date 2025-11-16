"""Cross-Encoder reranker implementation using sentence-transformers."""

import logging
import os
from typing import Any, Dict, List

# Fix OpenMP conflict on macOS (common with PyTorch + scikit-learn)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from rag_core.core.exceptions import RerankerException
from rag_core.core.models import Document
from rag_core.rerankers.base import RerankerInterface

logger = logging.getLogger(__name__)


class CrossEncoderReranker(RerankerInterface):
    """
    Cross-Encoder based document reranker.

    Cross-Encoders are BERT-based models that jointly encode the query and document,
    producing a relevance score. They are more accurate than bi-encoders (used in
    retrieval) but slower, making them ideal for reranking a small set of candidates.

    Popular models:
    - cross-encoder/ms-marco-MiniLM-L-6-v2: Fast, good quality (default)
    - cross-encoder/ms-marco-MiniLM-L-12-v2: Better quality, slower
    - cross-encoder/ms-marco-TinyBERT-L-2-v2: Very fast, lower quality

    Attributes:
        model: Cross-encoder model instance
        model_name: Name of the model
        top_n: Default number of documents to return after reranking
        batch_size: Batch size for inference
        device: Device to run inference on ('cuda' or 'cpu')

    Example:
        ```python
        reranker = CrossEncoderReranker(
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            top_n=5
        )

        # Rerank documents
        reranked = await reranker.rerank(
            query="What is machine learning?",
            documents=retrieved_docs,
            top_n=3
        )
        ```
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n: int = 3,
        batch_size: int = 32,
        device: str | None = None,
        max_length: int = 512,
    ):
        """
        Initialize Cross-Encoder reranker.

        Args:
            model_name: Name of the cross-encoder model from sentence-transformers
            top_n: Default number of top documents to return
            batch_size: Batch size for model inference
            device: Device to use ('cuda', 'cpu', or None for auto-detection)
            max_length: Maximum sequence length for tokenization

        Raises:
            RerankerException: If model initialization fails
        """
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as e:
            raise RerankerException(
                "sentence-transformers is required for CrossEncoderReranker. "
                "Install with: pip install sentence-transformers"
            ) from e

        self.model_name = model_name
        self.top_n = top_n
        self.batch_size = batch_size
        self.max_length = max_length

        try:
            logger.info(f"Loading cross-encoder model: {model_name}")
            self.model = CrossEncoder(model_name, max_length=max_length, device=device)
            self.device = self.model.device
            logger.info(f"Cross-encoder loaded successfully on device: {self.device}")

        except Exception as e:
            logger.error(f"Failed to load cross-encoder model {model_name}: {e}")
            raise RerankerException(f"Failed to load cross-encoder model: {e}") from e

    async def rerank(self, query: str, documents: List[Document], top_n: int | None = None) -> List[Document]:
        """
        Rerank documents using cross-encoder model.

        Process:
        1. Create query-document pairs
        2. Score all pairs using cross-encoder
        3. Sort by score (descending)
        4. Return top-n documents

        Args:
            query: Search query
            documents: List of documents to rerank
            top_n: Number of top documents to return (overrides default)

        Returns:
            List of documents sorted by cross-encoder score

        Raises:
            RerankerException: If reranking fails
        """
        if not documents:
            logger.warning("No documents to rerank")
            return []

        n = top_n if top_n is not None else self.top_n

        try:
            # Prepare query-document pairs
            pairs = [(query, doc.page_content) for doc in documents]

            logger.debug(f"Reranking {len(documents)} documents with query: '{query[:50]}...'")

            # Score all pairs
            scores = self.model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
            )

            # Create scored documents
            scored_docs = []
            for doc, score in zip(documents, scores):
                # Normalize score to 0-1 range using sigmoid
                # Cross-encoder scores are typically in range [-10, 10]
                normalized_score = self._sigmoid(float(score))

                scored_docs.append(
                    Document(
                        page_content=doc.page_content,
                        metadata={
                            **doc.metadata,
                            "rerank_score": float(score),  # Original score
                            "original_score": doc.score,  # Score from retriever
                        },
                        score=normalized_score,  # Normalized score as main score
                        id=doc.id,
                    )
                )

            # Sort by score (descending)
            scored_docs.sort(key=lambda x: x.score, reverse=True)

            # Return top-n
            result = scored_docs[:n]

            logger.info(
                f"Reranked {len(documents)} → {len(result)} documents. "
                f"Top score: {result[0].score:.4f}, "
                f"Bottom score: {result[-1].score:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Reranking failed: {e}", exc_info=True)
            raise RerankerException(f"Reranking failed: {e}") from e

    def _sigmoid(self, x: float) -> float:
        """
        Apply sigmoid function to normalize scores to 0-1 range.

        Args:
            x: Input score

        Returns:
            Normalized score in range (0, 1)
        """
        import math

        try:
            return 1.0 / (1.0 + math.exp(-x))
        except OverflowError:
            # Handle extreme values
            return 0.0 if x < 0 else 1.0

    def get_config(self) -> Dict[str, Any]:
        """
        Get reranker configuration.

        Returns:
            Dictionary with reranker details
        """
        return {
            "type": "cross_encoder",
            "model_name": self.model_name,
            "top_n": self.top_n,
            "batch_size": self.batch_size,
            "device": str(self.device),
            "max_length": self.max_length,
        }

    def __repr__(self) -> str:
        """String representation of the reranker."""
        return f"CrossEncoderReranker(model={self.model_name}, top_n={self.top_n}, device={self.device})"
