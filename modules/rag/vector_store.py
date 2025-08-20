"""
Vector Store Management System

Provides unified interface for vector databases with support for multiple backends
including Weaviate, ChromaDB, and Qdrant.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStoreType(str, Enum):
    """Vector store backend types"""
    WEAVIATE = "weaviate"
    CHROMADB = "chromadb"
    QDRANT = "qdrant"

@dataclass
class VectorDocument:
    """Vector document representation"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    topic_id: Optional[int] = None
    document_id: Optional[str] = None
    chunk_index: Optional[int] = None

@dataclass
class SearchResult:
    """Search result from vector store"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    document_id: Optional[str] = None
    topic_id: Optional[int] = None

class IVectorStore(ABC):
    """Abstract vector store interface"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store"""
        pass
    
    @abstractmethod
    async def create_collection(self, collection_name: str, 
                              dimension: int = 1024) -> None:
        """Create a new collection"""
        pass
    
    @abstractmethod
    async def add_documents(self, collection_name: str, 
                          documents: List[VectorDocument]) -> None:
        """Add documents to collection"""
        pass
    
    @abstractmethod
    async def search(self, collection_name: str, query_vector: List[float],
                    limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    async def delete_documents(self, collection_name: str, 
                             document_ids: List[str]) -> None:
        """Delete documents from collection"""
        pass
    
    @abstractmethod
    async def update_document(self, collection_name: str, 
                            document: VectorDocument) -> None:
        """Update a document in collection"""
        pass

class WeaviateVectorStore(IVectorStore):
    """Weaviate vector store implementation"""
    
    def __init__(self, url: str = "http://localhost:8080", 
                 api_key: Optional[str] = None):
        self.url = url
        self.api_key = api_key
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Weaviate client"""
        try:
            import weaviate
            
            auth_config = None
            if self.api_key:
                auth_config = weaviate.AuthApiKey(api_key=self.api_key)
                
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config
            )
            
            # Test connection
            if self.client.is_ready():
                self._initialized = True
                logger.info("Weaviate client initialized successfully")
            else:
                raise ConnectionError("Weaviate server is not ready")
                
        except ImportError:
            raise ImportError("weaviate-client package is required for WeaviateVectorStore")
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate: {e}")
            raise
    
    async def create_collection(self, collection_name: str, 
                              dimension: int = 1024) -> None:
        """Create Weaviate class schema"""
        if not self._initialized:
            await self.initialize()
        
        class_obj = {
            "class": collection_name,
            "description": f"Collection for {collection_name} documents",
            "vectorizer": "none",  # We provide our own vectors
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "metadata",
                    "dataType": ["object"],
                    "description": "Document metadata"
                },
                {
                    "name": "topicId",
                    "dataType": ["int"],
                    "description": "Topic ID"
                },
                {
                    "name": "documentId",
                    "dataType": ["string"],
                    "description": "Source document ID"
                },
                {
                    "name": "chunkIndex",
                    "dataType": ["int"],
                    "description": "Chunk index"
                },
                {
                    "name": "timestamp",
                    "dataType": ["date"],
                    "description": "Creation timestamp"
                }
            ]
        }
        
        try:
            self.client.schema.create_class(class_obj)
            logger.info(f"Created Weaviate collection: {collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Collection {collection_name} already exists")
            else:
                logger.error(f"Failed to create collection {collection_name}: {e}")
                raise
    
    async def add_documents(self, collection_name: str, 
                          documents: List[VectorDocument]) -> None:
        """Add documents to Weaviate"""
        if not self._initialized:
            await self.initialize()
        
        try:
            with self.client.batch as batch:
                batch.batch_size = 100
                batch.dynamic = True
                
                for doc in documents:
                    data_object = {
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "topicId": doc.topic_id,
                        "documentId": doc.document_id,
                        "chunkIndex": doc.chunk_index,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    batch.add_data_object(
                        data_object=data_object,
                        class_name=collection_name,
                        uuid=doc.id,
                        vector=doc.embedding
                    )
            
            logger.info(f"Added {len(documents)} documents to {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            raise
    
    async def search(self, collection_name: str, query_vector: List[float],
                    limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search in Weaviate"""
        if not self._initialized:
            await self.initialize()
        
        try:
            query = self.client.query.get(collection_name, [
                "content", "metadata", "topicId", "documentId", "chunkIndex"
            ]).with_near_vector({
                "vector": query_vector
            }).with_limit(limit).with_additional(["certainty", "id"])
            
            # Add filters if provided
            if filters:
                where_filter = self._build_where_filter(filters)
                query = query.with_where(where_filter)
            
            result = query.do()
            
            if "errors" in result:
                raise Exception(f"Weaviate query error: {result['errors']}")
            
            search_results = []
            documents = result.get("data", {}).get("Get", {}).get(collection_name, [])
            
            for doc in documents:
                search_results.append(SearchResult(
                    id=doc["_additional"]["id"],
                    content=doc["content"],
                    score=doc["_additional"]["certainty"],
                    metadata=doc.get("metadata", {}),
                    document_id=doc.get("documentId"),
                    topic_id=doc.get("topicId")
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            raise
    
    def _build_where_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Weaviate where filter"""
        conditions = []
        
        for key, value in filters.items():
            if key == "topic_id":
                conditions.append({
                    "path": ["topicId"],
                    "operator": "Equal",
                    "valueInt": value
                })
            elif key == "document_id":
                conditions.append({
                    "path": ["documentId"],
                    "operator": "Equal",
                    "valueString": value
                })
        
        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return {
                "operator": "And",
                "operands": conditions
            }
        return {}
    
    async def delete_documents(self, collection_name: str, 
                             document_ids: List[str]) -> None:
        """Delete documents from Weaviate"""
        if not self._initialized:
            await self.initialize()
        
        try:
            for doc_id in document_ids:
                self.client.data_object.delete(
                    uuid=doc_id,
                    class_name=collection_name
                )
            
            logger.info(f"Deleted {len(document_ids)} documents from {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to delete documents from {collection_name}: {e}")
            raise
    
    async def update_document(self, collection_name: str, 
                            document: VectorDocument) -> None:
        """Update document in Weaviate"""
        if not self._initialized:
            await self.initialize()
        
        try:
            data_object = {
                "content": document.content,
                "metadata": document.metadata,
                "topicId": document.topic_id,
                "documentId": document.document_id,
                "chunkIndex": document.chunk_index,
                "timestamp": datetime.now().isoformat()
            }
            
            self.client.data_object.update(
                data_object=data_object,
                class_name=collection_name,
                uuid=document.id,
                vector=document.embedding
            )
            
            logger.info(f"Updated document {document.id} in {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to update document {document.id}: {e}")
            raise

class ChromaDBVectorStore(IVectorStore):
    """ChromaDB vector store implementation"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize ChromaDB client"""
        try:
            import chromadb
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory
            )
            self._initialized = True
            logger.info("ChromaDB client initialized successfully")
            
        except ImportError:
            raise ImportError("chromadb package is required for ChromaDBVectorStore")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def create_collection(self, collection_name: str, 
                              dimension: int = 1024) -> None:
        """Create ChromaDB collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={"dimension": dimension}
            )
            logger.info(f"Created ChromaDB collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    async def add_documents(self, collection_name: str, 
                          documents: List[VectorDocument]) -> None:
        """Add documents to ChromaDB"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = self.client.get_collection(collection_name)
            
            ids = [doc.id for doc in documents]
            embeddings = [doc.embedding for doc in documents]
            metadatas = []
            documents_content = []
            
            for doc in documents:
                metadatas.append({
                    **doc.metadata,
                    "topic_id": doc.topic_id,
                    "document_id": doc.document_id,
                    "chunk_index": doc.chunk_index,
                    "timestamp": datetime.now().isoformat()
                })
                documents_content.append(doc.content)
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_content
            )
            
            logger.info(f"Added {len(documents)} documents to {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            raise
    
    async def search(self, collection_name: str, query_vector: List[float],
                    limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search in ChromaDB"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = self.client.get_collection(collection_name)
            
            where_clause = None
            if filters:
                where_clause = {}
                if "topic_id" in filters:
                    where_clause["topic_id"] = {"$eq": filters["topic_id"]}
                if "document_id" in filters:
                    where_clause["document_id"] = {"$eq": filters["document_id"]}
            
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    search_results.append(SearchResult(
                        id=results["ids"][0][i],
                        content=doc,
                        score=1.0 - distance,  # Convert distance to similarity
                        metadata=metadata,
                        document_id=metadata.get("document_id"),
                        topic_id=metadata.get("topic_id")
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            raise
    
    async def delete_documents(self, collection_name: str, 
                             document_ids: List[str]) -> None:
        """Delete documents from ChromaDB"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = self.client.get_collection(collection_name)
            collection.delete(ids=document_ids)
            
            logger.info(f"Deleted {len(document_ids)} documents from {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to delete documents from {collection_name}: {e}")
            raise
    
    async def update_document(self, collection_name: str, 
                            document: VectorDocument) -> None:
        """Update document in ChromaDB"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # ChromaDB doesn't have direct update, so delete and add
            await self.delete_documents(collection_name, [document.id])
            await self.add_documents(collection_name, [document])
            
            logger.info(f"Updated document {document.id} in {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to update document {document.id}: {e}")
            raise

class VectorStoreManager:
    """Vector store manager with multiple backend support"""
    
    def __init__(self, store_type: VectorStoreType = VectorStoreType.WEAVIATE,
                 config: Optional[Dict[str, Any]] = None):
        self.store_type = store_type
        self.config = config or {}
        self.store = self._create_store()
    
    def _create_store(self) -> IVectorStore:
        """Create vector store instance based on type"""
        if self.store_type == VectorStoreType.WEAVIATE:
            return WeaviateVectorStore(
                url=self.config.get("url", "http://localhost:8080"),
                api_key=self.config.get("api_key")
            )
        elif self.store_type == VectorStoreType.CHROMADB:
            return ChromaDBVectorStore(
                persist_directory=self.config.get("persist_directory", "./chroma_db")
            )
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
    
    async def initialize(self) -> None:
        """Initialize the vector store"""
        await self.store.initialize()
    
    async def get_or_create_topic_collection(self, topic_id: int) -> str:
        """Get or create collection name for topic"""
        collection_name = f"topic_{topic_id}"
        try:
            await self.store.create_collection(collection_name)
        except Exception as e:
            if "already exists" not in str(e):
                logger.error(f"Failed to create collection for topic {topic_id}: {e}")
                raise
        return collection_name
    
    async def add_topic_documents(self, topic_id: int, 
                                documents: List[VectorDocument]) -> None:
        """Add documents to topic collection"""
        collection_name = await self.get_or_create_topic_collection(topic_id)
        
        # Set topic_id for all documents
        for doc in documents:
            doc.topic_id = topic_id
        
        await self.store.add_documents(collection_name, documents)
    
    async def search_topic(self, topic_id: int, query_vector: List[float],
                          limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search within a specific topic"""
        collection_name = f"topic_{topic_id}"
        
        # Add topic filter
        if filters is None:
            filters = {}
        filters["topic_id"] = topic_id
        
        return await self.store.search(collection_name, query_vector, limit, filters)
    
    async def delete_topic_documents(self, topic_id: int, 
                                   document_ids: List[str]) -> None:
        """Delete documents from topic"""
        collection_name = f"topic_{topic_id}"
        await self.store.delete_documents(collection_name, document_ids)
    
    async def update_topic_document(self, topic_id: int, 
                                  document: VectorDocument) -> None:
        """Update document in topic"""
        collection_name = f"topic_{topic_id}"
        document.topic_id = topic_id
        await self.store.update_document(collection_name, document)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on vector store"""
        try:
            if not hasattr(self.store, '_initialized') or not self.store._initialized:
                await self.store.initialize()
            
            return {
                "status": "healthy",
                "store_type": self.store_type.value,
                "initialized": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "store_type": self.store_type.value,
                "error": str(e),
                "initialized": False,
                "timestamp": datetime.now().isoformat()
            }