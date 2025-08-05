#!/usr/bin/env python3
"""
ChromaDB client for RAG module
Handles vector storage and retrieval using ChromaDB
"""

import logging
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
import json

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    """ChromaDB vector store for RAG retrieval"""
    
    def __init__(self, persist_directory: str = "./rag_vector_db", 
                 collection_name: str = "arxiv_papers"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb is required. Install with: pip install chromadb")
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Ensure persist directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            # Get collection info
            count = self.collection.count()
            logger.info(f"Collection '{self.collection_name}' has {count} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def add_documents(self, chunks: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """
        Add document chunks to the vector store
        
        Args:
            chunks: List of chunk dictionaries with text, embeddings, and metadata
            batch_size: Batch size for insertion
            
        Returns:
            True if successful, False otherwise
        """
        if not chunks:
            logger.warning("No chunks provided for indexing")
            return True
        
        try:
            total_chunks = len(chunks)
            logger.info(f"Adding {total_chunks} chunks to vector store")
            
            # Process in batches
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i + batch_size]
                self._add_batch(batch)
                
                logger.info(f"Added batch {i//batch_size + 1}/{(total_chunks-1)//batch_size + 1}")
            
            logger.info(f"Successfully added {total_chunks} chunks to collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def _add_batch(self, batch: List[Dict[str, Any]]):
        """Add a batch of chunks to ChromaDB"""
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in batch:
            # Generate unique ID
            chunk_id = chunk.get('chunk_id', str(uuid.uuid4()))
            ids.append(chunk_id)
            
            # Get embedding
            embedding = chunk.get('embedding')
            if embedding is not None:
                embeddings.append(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
            else:
                logger.warning(f"No embedding found for chunk {chunk_id}")
                continue
            
            # Get document text
            documents.append(chunk.get('content', ''))
            
            # Prepare metadata
            metadata = {
                'source_doc': chunk.get('source_doc', ''),
                'page_number': chunk.get('page_number'),
                'chunk_index': chunk.get('chunk_index', 0),
                'char_count': len(chunk.get('content', '')),
            }
            
            # Add additional metadata if available
            if 'metadata' in chunk and chunk['metadata']:
                for key, value in chunk['metadata'].items():
                    # ChromaDB metadata values must be strings, ints, floats, or bools
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        metadata[f"meta_{key}"] = value
                    else:
                        metadata[f"meta_{key}"] = str(value)
            
            metadatas.append(metadata)
        
        # Add to collection
        if ids and embeddings:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
    
    def search(self, query_embedding: List[float], n_results: int = 5, 
               where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of search results with documents and metadata
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} similar documents")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    def search_by_text(self, query_text: str, embedding_generator, n_results: int = 5,
                      where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search using text query (will be embedded automatically)
        
        Args:
            query_text: Text query
            embedding_generator: EmbeddingGenerator instance
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of search results
        """
        try:
            # Generate embedding for query text
            query_embedding = embedding_generator.encode_single_text(query_text)
            
            # Search using embedding
            return self.search(
                query_embedding=query_embedding.tolist(),
                n_results=n_results,
                where=where
            )
            
        except Exception as e:
            logger.error(f"Failed to search by text: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=['documents', 'metadatas']
            )
            
            if results['ids'] and results['ids'][0]:
                return {
                    'id': results['ids'][0],
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete documents by IDs
        
        Args:
            doc_ids: List of document IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=doc_ids)
            logger.info(f"Deleted {len(doc_ids)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    def delete_by_source(self, source_doc: str) -> bool:
        """
        Delete all documents from a specific source
        
        Args:
            source_doc: Source document identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(where={"source_doc": source_doc})
            logger.info(f"Deleted all documents from source: {source_doc}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from source {source_doc}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_results = self.collection.get(limit=100, include=['metadatas'])
            
            sources = set()
            pages = []
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if 'source_doc' in metadata:
                        sources.add(metadata['source_doc'])
                    if 'page_number' in metadata and metadata['page_number']:
                        pages.append(metadata['page_number'])
            
            return {
                'total_documents': count,
                'unique_sources': len(sources),
                'sample_sources': list(sources)[:10],  # First 10 sources
                'avg_pages_per_doc': sum(pages) / len(pages) if pages else 0,
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                'total_documents': 0,
                'unique_sources': 0,
                'sample_sources': [],
                'avg_pages_per_doc': 0,
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
    
    def reset_collection(self) -> bool:
        """
        Reset (clear) the collection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False
    
    def export_collection(self, output_path: str) -> bool:
        """
        Export collection data to JSON file
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            results = self.collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            export_data = {
                'collection_name': self.collection_name,
                'total_documents': len(results['ids']),
                'documents': []
            }
            
            for i in range(len(results['ids'])):
                doc = {
                    'id': results['ids'][i],
                    'document': results['documents'][i],
                    'metadata': results['metadatas'][i],
                    'embedding': results['embeddings'][i] if results['embeddings'] else None
                }
                export_data['documents'].append(doc)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported collection to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export collection: {e}")
            return False