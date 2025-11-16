"""Hybrid retriever combining BM25 and vector similarity search."""

from typing import Any, List, Dict
import logging

from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from rag_core.core.exceptions import RetrieverException
from rag_core.core.interfaces import RetrieverInterface
from rag_core.core.models import Document

logger = logging.getLogger(__name__)


class HybridRetriever(RetrieverInterface):
    """
    Hybrid retriever combining BM25 (keyword-based) and vector similarity search.
    
    This retriever leverages the strengths of both approaches:
    - BM25: Good for exact keyword matches, technical terms, proper nouns
    - Vector: Good for semantic understanding, intent matching
    
    Results are fused using Reciprocal Rank Fusion (RRF) algorithm.
    
    Attributes:
        vector_store: FAISS vector store for semantic search
        bm25_index: BM25 index for keyword search
        documents: Cached document corpus
        vector_weight: Weight for vector search results (0-1)
        bm25_weight: Weight for BM25 results (0-1)
        top_k: Default number of documents to retrieve
        rrf_k: RRF constant (default: 60)
    
    Example:
        ```python
        retriever = HybridRetriever(
            vector_store=vector_store,
            vector_weight=0.7,
            bm25_weight=0.3,
            top_k=5
        )
        results = await retriever.retrieve("What is machine learning?")
        ```
    """

    def __init__(
        self,
        vector_store: FAISS | None = None,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        top_k: int = 5,
        rrf_k: int = 60,
        search_kwargs: Dict[str, Any] | None = None,
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: FAISS vector store instance
            vector_weight: Weight for vector search (0-1), default 0.7
            bm25_weight: Weight for BM25 search (0-1), default 0.3
            top_k: Default number of documents to retrieve
            rrf_k: RRF constant for rank fusion (default: 60)
            search_kwargs: Additional search parameters
        
        Raises:
            RetrieverException: If vector_store is None or initialization fails
        """
        if vector_store is None:
            raise RetrieverException("Vector store is required for HybridRetriever")
        
        # Normalize weights
        total_weight = vector_weight + bm25_weight
        self.vector_weight = vector_weight / total_weight
        self.bm25_weight = bm25_weight / total_weight
        
        self.vector_store = vector_store
        self.top_k = top_k
        self.rrf_k = rrf_k
        self.search_kwargs = search_kwargs or {}
        
        # Initialize BM25 index
        self.bm25_index: BM25Okapi | None = None
        self.documents: List[Document] = []
        self._build_bm25_index()
        
        logger.info(
            f"HybridRetriever initialized: "
            f"vector_weight={self.vector_weight:.2f}, "
            f"bm25_weight={self.bm25_weight:.2f}, "
            f"top_k={self.top_k}, "
            f"documents={len(self.documents)}"
        )

    def _build_bm25_index(self) -> None:
        """
        Build BM25 index from vector store documents.
        
        Extracts all documents from the vector store and creates
        a BM25 index for keyword-based retrieval.
        """
        try:
            # Get all documents from vector store
            # FAISS doesn't have a direct way to get all docs, so we need to do a dummy search
            # with a large k value
            docstore = self.vector_store.docstore
            
            # Extract documents from docstore
            if hasattr(docstore, '_dict'):
                # InMemoryDocstore
                langchain_docs = list(docstore._dict.values())
            else:
                logger.warning("Cannot extract documents from docstore, BM25 will be empty")
                langchain_docs = []
            
            # Convert to our Document model
            self.documents = [
                Document(
                    page_content=doc.page_content,
                    metadata=doc.metadata,
                    score=0.0,
                )
                for doc in langchain_docs
            ]
            
            if not self.documents:
                logger.warning("No documents found for BM25 index")
                self.bm25_index = None
                return
            
            # Tokenize documents for BM25
            tokenized_corpus = [
                doc.page_content.lower().split()
                for doc in self.documents
            ]
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(tokenized_corpus)
            
            logger.info(f"BM25 index built with {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}", exc_info=True)
            self.bm25_index = None
            self.documents = []

    async def retrieve(self, query: str, top_k: int | None = None) -> List[Document]:
        """
        Retrieve documents using hybrid search (BM25 + Vector).
        
        Process:
        1. Perform BM25 keyword search
        2. Perform vector similarity search
        3. Fuse results using Reciprocal Rank Fusion (RRF)
        4. Return top-k documents sorted by fused score
        
        Args:
            query: Search query string
            top_k: Number of documents to return (overrides default)
        
        Returns:
            List of Document objects sorted by relevance score
        
        Raises:
            RetrieverException: If retrieval fails
        """
        k = top_k if top_k is not None else self.top_k
        
        try:
            # Retrieve more candidates from each method for better fusion
            candidate_k = k * 3
            
            # 1. BM25 retrieval
            bm25_docs = self._bm25_retrieve(query, candidate_k)
            
            # 2. Vector retrieval
            vector_docs = self._vector_retrieve(query, candidate_k)
            
            # 3. Fuse results using RRF
            fused_docs = self._reciprocal_rank_fusion(
                query=query,
                bm25_docs=bm25_docs,
                vector_docs=vector_docs,
                k=k
            )
            
            logger.info(
                f"Hybrid retrieval: query='{query[:50]}...', "
                f"bm25_results={len(bm25_docs)}, "
                f"vector_results={len(vector_docs)}, "
                f"fused_results={len(fused_docs)}"
            )
            
            return fused_docs[:k]
            
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}", exc_info=True)
            raise RetrieverException(f"Hybrid retrieval failed: {e}") from e

    def _bm25_retrieve(self, query: str, k: int) -> List[Document]:
        """
        Perform BM25 keyword-based retrieval.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
        
        Returns:
            List of documents with normalized BM25 scores (0-1)
        """
        if not self.bm25_index or not self.documents:
            logger.warning("BM25 index not available, returning empty results")
            return []
        
        try:
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(tokenized_query)
            
            # Normalize scores to 0-1 range
            # BM25 scores are unbounded, so we use min-max normalization
            max_score = scores.max() if len(scores) > 0 else 1.0
            min_score = scores.min() if len(scores) > 0 else 0.0
            
            if max_score > min_score:
                normalized_scores = (scores - min_score) / (max_score - min_score)
            else:
                normalized_scores = scores
            
            # Get top-k documents
            top_indices = scores.argsort()[-k:][::-1]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include documents with non-zero scores
                    doc = self.documents[idx]
                    results.append(
                        Document(
                            page_content=doc.page_content,
                            metadata=doc.metadata,
                            score=float(normalized_scores[idx]),
                        )
                    )
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 retrieval failed: {e}", exc_info=True)
            return []

    def _vector_retrieve(self, query: str, k: int) -> List[Document]:
        """
        Perform vector similarity search.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
        
        Returns:
            List of documents with similarity scores
        """
        try:
            # Perform similarity search with scores
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Convert to our Document model
            documents = []
            for doc, distance in results:
                # Convert distance to similarity score (0-1)
                # Lower distance = higher similarity
                similarity_score = 1.0 / (1.0 + distance)
                
                documents.append(
                    Document(
                        page_content=doc.page_content,
                        metadata=doc.metadata,
                        score=similarity_score,
                    )
                )
            
            return documents
            
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}", exc_info=True)
            return []

    def _reciprocal_rank_fusion(
        self,
        query: str,
        bm25_docs: List[Document],
        vector_docs: List[Document],
        k: int
    ) -> List[Document]:
        """
        Fuse BM25 and vector results using Reciprocal Rank Fusion.
        
        RRF formula: score(d) = sum(1 / (k + rank(d)))
        
        This method:
        1. Calculates RRF scores for each document
        2. Applies weights to BM25 and vector scores
        3. Combines scores and deduplicates documents
        4. Returns top-k documents sorted by fused score
        
        Args:
            query: Original query (for logging)
            bm25_docs: Documents from BM25 retrieval
            vector_docs: Documents from vector retrieval
            k: Number of documents to return
        
        Returns:
            List of documents sorted by fused RRF score
        """
        # Create document map: content -> Document
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}
        
        # Calculate RRF scores for BM25 results
        for rank, doc in enumerate(bm25_docs):
            content = doc.page_content
            rrf_score = self.bm25_weight / (self.rrf_k + rank + 1)
            
            if content not in doc_scores:
                doc_scores[content] = 0.0
                doc_map[content] = doc
            
            doc_scores[content] += rrf_score
        
        # Calculate RRF scores for vector results
        for rank, doc in enumerate(vector_docs):
            content = doc.page_content
            rrf_score = self.vector_weight / (self.rrf_k + rank + 1)
            
            if content not in doc_scores:
                doc_scores[content] = 0.0
                doc_map[content] = doc
            
            doc_scores[content] += rrf_score
        
        # Sort by fused score
        sorted_contents = sorted(
            doc_scores.keys(),
            key=lambda x: doc_scores[x],
            reverse=True
        )
        
        # Create result documents with fused scores
        results = []
        for content in sorted_contents[:k]:
            doc = doc_map[content]
            results.append(
                Document(
                    page_content=doc.page_content,
                    metadata=doc.metadata,
                    score=doc_scores[content],  # Fused RRF score
                )
            )
        
        return results

    def get_config(self) -> Dict[str, Any]:
        """
        Get retriever configuration.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            "type": "hybrid",
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
            "top_k": self.top_k,
            "rrf_k": self.rrf_k,
            "num_documents": len(self.documents),
            "bm25_enabled": self.bm25_index is not None,
        }

    def rebuild_index(self) -> None:
        """
        Rebuild BM25 index from current vector store.
        
        Call this method after adding new documents to the vector store
        to update the BM25 index.
        """
        logger.info("Rebuilding BM25 index...")
        self._build_bm25_index()
        logger.info(f"BM25 index rebuilt with {len(self.documents)} documents")

