"""
Document API controller.

Handles HTTP requests for document management operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...shared.di.container import Container
from ...use_cases.document.create_document import CreateDocumentUseCase, CreateDocumentRequest
from ...use_cases.document.get_document import GetDocumentUseCase
from ...use_cases.document.search_documents import SearchDocumentsUseCase, SearchDocumentsRequest
from ..schemas.document_schemas import (
    DocumentResponse,
    CreateDocumentRequestSchema,
    SearchDocumentsRequestSchema,
    SearchResultsResponse
)


class DocumentController:
    """Controller for document-related API endpoints."""
    
    def __init__(self, container: Container):
        self.container = container
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.router.post("/", response_model=DocumentResponse)
        async def create_document(
            request: CreateDocumentRequestSchema,
            create_use_case: CreateDocumentUseCase = Depends(self._get_create_use_case)
        ):
            """Create a new document."""
            use_case_request = CreateDocumentRequest(
                title=request.title,
                content=request.content,
                content_type=request.content_type,
                file_id=request.file_id,
                file_path=request.file_path,
                metadata=request.metadata
            )
            
            document = await create_use_case.execute(use_case_request)
            return DocumentResponse.from_entity(document)
        
        @self.router.get("/{document_id}", response_model=DocumentResponse)
        async def get_document(
            document_id: str,
            get_use_case: GetDocumentUseCase = Depends(self._get_get_use_case)
        ):
            """Get a document by ID."""
            document = await get_use_case.execute(document_id)
            return DocumentResponse.from_entity(document)
        
        @self.router.post("/search", response_model=SearchResultsResponse)
        async def search_documents(
            request: SearchDocumentsRequestSchema,
            search_use_case: SearchDocumentsUseCase = Depends(self._get_search_use_case)
        ):
            """Search documents."""
            use_case_request = SearchDocumentsRequest(
                query=request.query,
                limit=request.limit,
                use_semantic_search=request.use_semantic_search,
                filters=request.filters,
                threshold=request.threshold
            )
            
            results = await search_use_case.execute(use_case_request)
            return SearchResultsResponse.from_search_results(results, request.query)
    
    def _get_create_use_case(self) -> CreateDocumentUseCase:
        """Get create document use case."""
        return self.container.create_document_use_case()
    
    def _get_get_use_case(self) -> GetDocumentUseCase:
        """Get get document use case."""
        return self.container.get_document_use_case()
    
    def _get_search_use_case(self) -> SearchDocumentsUseCase:
        """Get search documents use case."""
        return self.container.search_documents_use_case()