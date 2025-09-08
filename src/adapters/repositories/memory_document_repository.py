"""
Memory document repository implementation.

Implements the DocumentRepository interface using in-memory storage.
Useful for development, testing, and lightweight deployments.
"""

from typing import List, Optional, Dict
import asyncio
from datetime import datetime

from ...core.entities.document import Document
from ...core.repositories.document_repository import DocumentRepository
from ...core.value_objects.document_chunk import DocumentChunk


class MemoryDocumentRepository(DocumentRepository):
    """In-memory implementation of DocumentRepository."""
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._chunks: Dict[str, List[DocumentChunk]] = {}  # document_id -> chunks
        self._lock = asyncio.Lock()
    
    async def save(self, document: Document) -> None:
        """Save a document."""
        async with self._lock:
            # Create a copy to avoid external modifications
            document_copy = Document(
                id=document.id,
                title=document.title,
                content=document.content,
                content_type=document.content_type,
                file_id=document.file_id,
                file_path=document.file_path,
                file_size=document.file_size,
                status=document.status,
                processing_status=document.processing_status,
                metadata=document.metadata.copy() if document.metadata else {},
                created_at=document.created_at,
                updated_at=datetime.utcnow()
            )
            self._documents[document.id] = document_copy
    
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        async with self._lock:
            document = self._documents.get(document_id)
            if document:
                # Return a copy to avoid external modifications
                return Document(
                    id=document.id,
                    title=document.title,
                    content=document.content,
                    content_type=document.content_type,
                    file_id=document.file_id,
                    file_path=document.file_path,
                    file_size=document.file_size,
                    status=document.status,
                    processing_status=document.processing_status,
                    metadata=document.metadata.copy() if document.metadata else {},
                    created_at=document.created_at,
                    updated_at=document.updated_at
                )
            return None
    
    async def get_by_file_id(self, file_id: str) -> List[Document]:
        """Get documents by file ID."""
        async with self._lock:
            results = []
            for document in self._documents.values():
                if document.file_id == file_id:
                    results.append(self._copy_document(document))
            return results
    
    async def search(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by content."""
        async with self._lock:
            results = []
            query_lower = query.lower()
            
            for document in self._documents.values():
                if (query_lower in (document.title or "").lower() or 
                    query_lower in (document.content or "").lower()):
                    results.append(self._copy_document(document))
                    if len(results) >= limit:
                        break
            
            return results
    
    async def list_by_status(self, status: str, limit: int = 100) -> List[Document]:
        """List documents by status."""
        async with self._lock:
            results = []
            for document in self._documents.values():
                if document.status == status:
                    results.append(self._copy_document(document))
                    if len(results) >= limit:
                        break
            return results
    
    async def update_status(self, document_id: str, status: str, processing_status: Optional[str] = None) -> bool:
        """Update document status."""
        async with self._lock:
            document = self._documents.get(document_id)
            if document:
                document.status = status
                if processing_status:
                    document.processing_status = processing_status
                document.updated_at = datetime.utcnow()
                return True
            return False
    
    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        async with self._lock:
            if document_id in self._documents:
                del self._documents[document_id]
                # Also delete associated chunks
                if document_id in self._chunks:
                    del self._chunks[document_id]
                return True
            return False
    
    async def count_by_status(self, status: str) -> int:
        """Count documents by status."""
        async with self._lock:
            count = 0
            for document in self._documents.values():
                if document.status == status:
                    count += 1
            return count
    
    # Document chunk operations
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Save document chunks."""
        async with self._lock:
            for chunk in chunks:
                if chunk.document_id not in self._chunks:
                    self._chunks[chunk.document_id] = []
                
                # Find and replace existing chunk or append new one
                existing_index = -1
                for i, existing_chunk in enumerate(self._chunks[chunk.document_id]):
                    if existing_chunk.id == chunk.id:
                        existing_index = i
                        break
                
                if existing_index >= 0:
                    self._chunks[chunk.document_id][existing_index] = chunk
                else:
                    self._chunks[chunk.document_id].append(chunk)
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """Get chunks for a document."""
        async with self._lock:
            chunks = self._chunks.get(document_id, [])
            # Sort by chunk_index
            return sorted(chunks, key=lambda x: x.chunk_index)
    
    async def delete_chunks_by_document_id(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        async with self._lock:
            if document_id in self._chunks:
                del self._chunks[document_id]
                return True
            return False
    
    async def search_chunks(self, query: str, limit: int = 10) -> List[DocumentChunk]:
        """Search document chunks."""
        async with self._lock:
            results = []
            query_lower = query.lower()
            
            for chunks in self._chunks.values():
                for chunk in chunks:
                    if query_lower in chunk.content.lower():
                        results.append(chunk)
                        if len(results) >= limit:
                            break
                if len(results) >= limit:
                    break
            
            return results
    
    def _copy_document(self, document: Document) -> Document:
        """Create a copy of a document."""
        return Document(
            id=document.id,
            title=document.title,
            content=document.content,
            content_type=document.content_type,
            file_id=document.file_id,
            file_path=document.file_path,
            file_size=document.file_size,
            status=document.status,
            processing_status=document.processing_status,
            metadata=document.metadata.copy() if document.metadata else {},
            created_at=document.created_at,
            updated_at=document.updated_at
        )
    
    # Utility methods for testing/debugging
    async def clear_all(self) -> None:
        """Clear all documents and chunks (for testing)."""
        async with self._lock:
            self._documents.clear()
            self._chunks.clear()
    
    async def get_all_documents(self) -> List[Document]:
        """Get all documents (for testing/debugging)."""
        async with self._lock:
            return [self._copy_document(doc) for doc in self._documents.values()]