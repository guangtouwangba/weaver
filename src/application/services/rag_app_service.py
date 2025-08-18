"""RAG application service for orchestrating RAG workflows."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.knowledge_base import KnowledgeBase, Knowledge
from ...domain.services.rag_domain_service import RAGDomainService
from ...domain.repositories.document_repository import DocumentRepository
from ...domain.value_objects.search_criteria import SearchCriteria
from ..dtos.requests.document_requests import DocumentIngestionRequest
from ..dtos.requests.search_requests import KnowledgeSearchRequest
from ..dtos.responses.document_responses import DocumentIngestionResponse
from ..dtos.responses.search_responses import KnowledgeSearchResponse


class RAGApplicationService:
    """
    RAG application service for orchestrating RAG workflows.
    
    This service coordinates between domain services and infrastructure
    to implement complete RAG use cases.
    """
    
    def __init__(
        self,
        rag_domain_service: RAGDomainService,
        document_repository: DocumentRepository,
        vector_store,  # Infrastructure interface
        embedding_service,  # Infrastructure interface
        event_bus  # Infrastructure interface
    ):
        self.rag_domain_service = rag_domain_service
        self.document_repository = document_repository
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.event_bus = event_bus
    
    async def ingest_document(
        self, 
        request: DocumentIngestionRequest
    ) -> DocumentIngestionResponse:
        """
        Complete document ingestion workflow.
        
        This orchestrates the entire process of ingesting a document
        into the RAG system, including validation, processing, and indexing.
        
        Args:
            request: Document ingestion request
            
        Returns:
            DocumentIngestionResponse: Ingestion result
        """
        try:
            # 1. Validate request
            self._validate_ingestion_request(request)
            
            # 2. Create document entity
            document = Document(
                title=request.title or request.filename,
                content=request.content,
                file_path=request.file_path,
                file_size=request.file_size,
                content_type=request.content_type,
                topic_id=request.topic_id,
                owner_id=request.owner_id,
                tags=request.tags or [],
                metadata=request.metadata or {}
            )
            
            # 3. Save document (initial state)
            document_id = await self.document_repository.save(document)
            
            # 4. Update status to processing
            await self.document_repository.update_status(
                document_id, 
                DocumentStatus.PROCESSING
            )
            
            # 5. Process document content (split into chunks)
            chunks = await self._process_document_content(document)
            
            # 6. Generate embeddings for chunks
            embeddings = await self._generate_embeddings(chunks)
            
            # 7. Store embeddings in vector store
            await self._store_embeddings(document_id, chunks, embeddings)
            
            # 8. Update document processing results
            await self.document_repository.update_processing_results(
                document_id,
                chunk_count=len(chunks),
                embedding_count=len(embeddings)
            )
            
            # 9. Mark document as completed
            await self.document_repository.update_status(
                document_id,
                DocumentStatus.COMPLETED
            )
            
            # 10. Publish domain event
            await self._publish_document_processed_event(document_id, chunks)
            
            return DocumentIngestionResponse(
                document_id=document_id,
                status="completed",
                chunk_count=len(chunks),
                embedding_count=len(embeddings),
                processing_time_ms=0,  # Would be calculated in real implementation
                message="Document ingested successfully"
            )
            
        except Exception as e:
            # Handle failure
            if 'document_id' in locals():
                await self.document_repository.update_status(
                    document_id,
                    DocumentStatus.FAILED,
                    str(e)
                )
            
            return DocumentIngestionResponse(
                document_id=locals().get('document_id'),
                status="failed",
                chunk_count=0,
                embedding_count=0,
                processing_time_ms=0,
                message=f"Document ingestion failed: {str(e)}",
                error=str(e)
            )
    
    async def search_knowledge(
        self, 
        request: KnowledgeSearchRequest
    ) -> KnowledgeSearchResponse:
        """
        Knowledge search workflow.
        
        This orchestrates the complete knowledge search process including
        semantic search, filtering, and result ranking.
        
        Args:
            request: Knowledge search request
            
        Returns:
            KnowledgeSearchResponse: Search results
        """
        try:
            # 1. Build search criteria from request
            criteria = self._build_search_criteria(request)
            
            # 2. Perform vector search if semantic search is enabled
            vector_results = []
            if criteria.is_semantic_only or criteria.is_hybrid_search:
                query_embedding = await self.embedding_service.embed_text(request.query)
                vector_results = await self.vector_store.similarity_search(
                    query_embedding,
                    top_k=criteria.limit * 2,  # Get more for reranking
                    filters=self._build_vector_filters(criteria)
                )
            
            # 3. Perform keyword search if hybrid search is enabled
            keyword_results = []
            if criteria.is_hybrid_search:
                keyword_results = await self._perform_keyword_search(criteria)
            
            # 4. Merge and rank results
            merged_results = await self._merge_search_results(
                vector_results, 
                keyword_results, 
                criteria
            )
            
            # 5. Apply post-processing filters
            filtered_results = await self._apply_post_search_filters(
                merged_results, 
                criteria
            )
            
            # 6. Convert to response format
            return KnowledgeSearchResponse(
                query=request.query,
                results=filtered_results[:criteria.limit],
                total_count=len(filtered_results),
                search_time_ms=0,  # Would be calculated in real implementation
                search_strategy="semantic" if criteria.is_semantic_only else "hybrid"
            )
            
        except Exception as e:
            return KnowledgeSearchResponse(
                query=request.query,
                results=[],
                total_count=0,
                search_time_ms=0,
                search_strategy="failed",
                error=str(e)
            )
    
    async def extract_knowledge_from_document(
        self, 
        document_id: str
    ) -> List[Knowledge]:
        """
        Extract knowledge from a processed document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List[Knowledge]: Extracted knowledge items
        """
        # 1. Get document
        document = await self.document_repository.find_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # 2. Ensure document is processed
        if not document.is_processed:
            raise ValueError(f"Document {document_id} is not processed")
        
        # 3. Create or get knowledge base
        knowledge_base = await self._get_or_create_knowledge_base(document.topic_id)
        
        # 4. Use domain service to extract knowledge
        knowledge_items = await self.rag_domain_service.process_document_for_knowledge_base(
            document,
            knowledge_base
        )
        
        # 5. Publish knowledge extracted event
        await self._publish_knowledge_extracted_event(document_id, knowledge_items)
        
        return knowledge_items
    
    async def find_related_content(
        self, 
        content: str, 
        content_type: str = "text",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find content related to the given content.
        
        Args:
            content: Source content
            content_type: Type of content
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Related content items
        """
        # 1. Generate embedding for the content
        content_embedding = await self.embedding_service.embed_text(content)
        
        # 2. Search for similar content
        similar_results = await self.vector_store.similarity_search(
            content_embedding,
            top_k=limit,
            filters={"content_type": content_type} if content_type != "text" else {}
        )
        
        # 3. Format results
        related_items = []
        for result in similar_results:
            related_items.append({
                "content": result.content,
                "similarity_score": result.score,
                "source_document_id": result.metadata.get("document_id"),
                "chunk_id": result.metadata.get("chunk_id"),
                "metadata": result.metadata
            })
        
        return related_items
    
    def _validate_ingestion_request(self, request: DocumentIngestionRequest) -> None:
        """Validate document ingestion request."""
        if not request.content and not request.file_path:
            raise ValueError("Either content or file_path must be provided")
        
        if request.file_size and request.file_size > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError("File size exceeds maximum limit")
    
    async def _process_document_content(self, document: Document) -> List[Dict[str, Any]]:
        """Process document content into chunks."""
        # This would use infrastructure services for document processing
        # For now, return a simplified chunk structure
        chunks = []
        
        # Simple text splitting (in real implementation, use proper text splitters)
        if document.content:
            words = document.content.split()
            chunk_size = 500  # words per chunk
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_content = " ".join(chunk_words)
                
                chunks.append({
                    "content": chunk_content,
                    "chunk_index": i // chunk_size,
                    "start_char": 0,  # Would be calculated properly
                    "end_char": len(chunk_content),
                    "metadata": {
                        "document_id": document.id,
                        "source": "text_splitting"
                    }
                })
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """Generate embeddings for chunks."""
        embeddings = []
        for chunk in chunks:
            embedding = await self.embedding_service.embed_text(chunk["content"])
            embeddings.append(embedding)
        return embeddings
    
    async def _store_embeddings(
        self, 
        document_id: str, 
        chunks: List[Dict[str, Any]], 
        embeddings: List[List[float]]
    ) -> None:
        """Store embeddings in vector store."""
        for chunk, embedding in zip(chunks, embeddings):
            await self.vector_store.store_embedding(
                id=f"{document_id}_{chunk['chunk_index']}",
                content=chunk["content"],
                embedding=embedding,
                metadata={
                    **chunk["metadata"],
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"]
                }
            )
    
    def _build_search_criteria(self, request: KnowledgeSearchRequest) -> SearchCriteria:
        """Build search criteria from request."""
        return SearchCriteria(
            query=request.query,
            semantic_search=request.semantic_search,
            hybrid_search=request.hybrid_search,
            document_ids=request.document_ids,
            topic_ids=request.topic_ids,
            tags=request.tags,
            similarity_threshold=request.similarity_threshold,
            limit=request.limit,
            offset=request.offset,
            include_content=request.include_content,
            include_metadata=request.include_metadata
        )
    
    def _build_vector_filters(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """Build filters for vector search."""
        filters = {}
        
        if criteria.document_ids:
            filters["document_id"] = {"$in": criteria.document_ids}
        
        if criteria.topic_ids:
            filters["topic_id"] = {"$in": criteria.topic_ids}
        
        return filters
    
    async def _perform_keyword_search(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Perform keyword search."""
        # This would use infrastructure services for keyword search
        # For now, return empty list
        return []
    
    async def _merge_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        criteria: SearchCriteria
    ) -> List[Dict[str, Any]]:
        """Merge vector and keyword search results."""
        # Simple merging strategy (in real implementation, use sophisticated algorithms)
        all_results = vector_results + keyword_results
        
        # Remove duplicates based on content
        seen_content = set()
        merged_results = []
        
        for result in all_results:
            content_key = result.get("content", "")[:100]  # First 100 chars as key
            if content_key not in seen_content:
                seen_content.add(content_key)
                merged_results.append(result)
        
        return merged_results
    
    async def _apply_post_search_filters(
        self,
        results: List[Dict[str, Any]],
        criteria: SearchCriteria
    ) -> List[Dict[str, Any]]:
        """Apply post-search filters."""
        filtered = results
        
        # Apply similarity threshold
        if criteria.similarity_threshold > 0:
            filtered = [
                r for r in filtered 
                if r.get("score", 0) >= criteria.similarity_threshold
            ]
        
        return filtered
    
    async def _get_or_create_knowledge_base(self, topic_id: Optional[str]) -> KnowledgeBase:
        """Get or create knowledge base for topic."""
        # This would interact with knowledge base repository
        # For now, create a simple knowledge base
        return KnowledgeBase(
            name=f"Knowledge Base for Topic {topic_id}" if topic_id else "Default Knowledge Base",
            topics=[topic_id] if topic_id else []
        )
    
    async def _publish_document_processed_event(
        self, 
        document_id: str, 
        chunks: List[Dict[str, Any]]
    ) -> None:
        """Publish document processed event."""
        event = {
            "event_type": "document_processed",
            "document_id": document_id,
            "chunk_count": len(chunks),
            "timestamp": datetime.now().isoformat()
        }
        await self.event_bus.publish("document.processed", event)
    
    async def _publish_knowledge_extracted_event(
        self, 
        document_id: str, 
        knowledge_items: List[Knowledge]
    ) -> None:
        """Publish knowledge extracted event."""
        event = {
            "event_type": "knowledge_extracted",
            "document_id": document_id,
            "knowledge_count": len(knowledge_items),
            "knowledge_ids": [k.id for k in knowledge_items],
            "timestamp": datetime.now().isoformat()
        }
        await self.event_bus.publish("knowledge.extracted", event)
