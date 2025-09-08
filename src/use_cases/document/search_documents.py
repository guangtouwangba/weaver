"""
Search documents use case.

Handles searching for documents based on various criteria.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from ...core.entities.document import Document
from ...core.repositories.document_repository import DocumentRepository
from ...core.domain_services.vector_search_service import VectorSearchService, SearchResult
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import ValidationError


@dataclass
class SearchDocumentsRequest:
    """Request model for searching documents."""
    query: str
    limit: int = 10
    use_semantic_search: bool = True
    filters: Optional[Dict[str, Any]] = None
    threshold: float = 0.7


@dataclass
class DocumentSearchResult:
    """Result model for document search."""
    document: Document
    score: float
    relevant_chunks: List[str]
    metadata: Dict[str, Any]


class SearchDocumentsUseCase(BaseUseCase):
    """Use case for searching documents."""
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        vector_search_service: VectorSearchService
    ):
        super().__init__()
        self._document_repository = document_repository
        self._vector_search_service = vector_search_service
    
    async def execute(self, request: SearchDocumentsRequest) -> List[DocumentSearchResult]:
        """Execute the search documents use case."""
        self.log_execution_start("search_documents", query=request.query, limit=request.limit)
        
        try:
            # Validate input
            self._validate_request(request)
            
            results = []
            
            if request.use_semantic_search:
                # Perform semantic search using vector search service
                search_results = await self._vector_search_service.search_similar_chunks(
                    query=request.query,
                    limit=request.limit * 3,  # Get more chunks to find unique documents
                    threshold=request.threshold,
                    filters=request.filters
                )
                
                # Group results by document and aggregate scores
                document_results = await self._aggregate_chunk_results(search_results, request.limit)
                results.extend(document_results)
            else:
                # Perform text-based search using document repository
                documents = await self._document_repository.search(request.query, request.limit)
                
                for doc in documents:
                    result = DocumentSearchResult(
                        document=doc,
                        score=1.0,  # Default score for text search
                        relevant_chunks=[],
                        metadata={}
                    )
                    results.append(result)
            
            self.log_execution_end("search_documents", query=request.query, results_count=len(results))
            return results
            
        except Exception as e:
            self.log_error("search_documents", e, query=request.query)
            raise
    
    def _validate_request(self, request: SearchDocumentsRequest) -> None:
        """Validate the search request."""
        if not request.query or not request.query.strip():
            raise ValidationError("Search query is required", "query")
        
        if request.limit <= 0 or request.limit > 100:
            raise ValidationError("Limit must be between 1 and 100", "limit")
        
        if request.threshold < 0 or request.threshold > 1:
            raise ValidationError("Threshold must be between 0 and 1", "threshold")
    
    async def _aggregate_chunk_results(
        self, 
        search_results: List[SearchResult], 
        limit: int
    ) -> List[DocumentSearchResult]:
        """Aggregate chunk search results by document."""
        document_scores = {}
        document_chunks = {}
        
        # Group results by document_id
        for result in search_results:
            doc_id = result.chunk.document_id
            
            if doc_id not in document_scores:
                document_scores[doc_id] = []
                document_chunks[doc_id] = []
            
            document_scores[doc_id].append(result.score)
            document_chunks[doc_id].append(result.chunk.content[:200])  # First 200 chars
        
        # Calculate aggregate scores and fetch documents
        aggregated_results = []
        
        for doc_id, scores in document_scores.items():
            # Calculate aggregate score (max score with boost for multiple matches)
            max_score = max(scores)
            match_count_boost = min(len(scores) * 0.1, 0.3)  # Up to 30% boost
            aggregate_score = min(max_score + match_count_boost, 1.0)
            
            # Get document
            document = await self._document_repository.get_by_id(doc_id)
            if document:
                result = DocumentSearchResult(
                    document=document,
                    score=aggregate_score,
                    relevant_chunks=document_chunks[doc_id][:3],  # Top 3 relevant chunks
                    metadata={
                        "match_count": len(scores),
                        "max_chunk_score": max_score,
                        "avg_chunk_score": sum(scores) / len(scores)
                    }
                )
                aggregated_results.append(result)
        
        # Sort by score and return top results
        aggregated_results.sort(key=lambda x: x.score, reverse=True)
        return aggregated_results[:limit]