"""
ChromaDB vector database implementation
"""
import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import chromadb
from chromadb.config import Settings

from .base import BaseVectorDB, VectorSearchResult, VectorDBStats, VectorDBFactory
from retrieval.arxiv_client import Paper

logger = logging.getLogger(__name__)

class ChromaVectorDB(BaseVectorDB):
    """ChromaDB implementation of vector database"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Extract configuration
        self.db_path = Path(config.get('db_path', './data/vector_db'))
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        if config.get('host') and config.get('port'):
            # HTTP client for remote ChromaDB
            self.client = chromadb.HttpClient(
                host=config.get('host', 'localhost'),
                port=config.get('port', 8000),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            # Persistent client for local ChromaDB
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing ChromaDB collection: {self.collection_name}")
        except Exception as e:
            # Collection doesn't exist, create it
            logger.info(f"Collection {self.collection_name} not found, creating new one: {e}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Research papers with semantic embeddings"}
            )
            logger.info(f"Created new ChromaDB collection: {self.collection_name}")
    
    def add_papers(self, papers: List[Paper], embeddings: List[List[float]]) -> List[str]:
        """Add papers with their embeddings"""
        if len(papers) != len(embeddings):
            raise ValueError("Number of papers must match number of embeddings")
        
        doc_ids = []
        documents = []
        metadatas = []
        
        for paper, embedding in zip(papers, embeddings):
            doc_id = f"{paper.id}"
            doc_ids.append(doc_id)
            
            # Use abstract or summary as document text
            document_text = paper.abstract or paper.summary or paper.title
            documents.append(document_text)
            
            # Create metadata
            metadata = {
                "paper_id": paper.id,
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": ", ".join(paper.authors),
                "categories": ", ".join(paper.categories),
                "published": paper.published.isoformat(),
                "pdf_url": paper.pdf_url or "",
                "entry_id": paper.entry_id or "",
                "doi": paper.doi or "",
                "type": "paper"
            }
            metadatas.append(metadata)
        
        try:
            self.collection.add(
                ids=doc_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Added {len(papers)} papers to ChromaDB")
            return doc_ids
        except Exception as e:
            logger.error(f"Error adding papers to ChromaDB: {e}")
            raise
    
    def add_paper_chunks(self, paper: Paper, chunks: List[str], embeddings: List[List[float]]) -> List[str]:
        """Add paper chunks with their embeddings"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        doc_ids = []
        documents = []
        metadatas = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_id = f"{paper.id}_chunk_{i}"
            doc_ids.append(doc_id)
            documents.append(chunk)
            
            # Create metadata
            metadata = {
                "paper_id": paper.id,
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": ", ".join(paper.authors),
                "categories": ", ".join(paper.categories),
                "published": paper.published.isoformat(),
                "chunk_index": i,
                "pdf_url": paper.pdf_url or "",
                "entry_id": paper.entry_id or "",
                "doi": paper.doi or "",
                "type": "chunk"
            }
            metadatas.append(metadata)
        
        try:
            self.collection.add(
                ids=doc_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Added {len(chunks)} chunks for paper {paper.id} to ChromaDB")
            return doc_ids
        except Exception as e:
            logger.error(f"Error adding paper chunks to ChromaDB: {e}")
            raise
    
    def search_papers(self, query_embedding: List[float], limit: int = 10, 
                     filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """Search for similar papers using vector similarity"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = VectorSearchResult(
                        id=results['ids'][0][i],
                        document=results['documents'][0][i],
                        metadata=results['metadatas'][0][i],
                        similarity_score=1 - results['distances'][0][i]  # Convert distance to similarity
                    )
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results in ChromaDB")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return []
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper and all its chunks by paper ID"""
        try:
            results = self.collection.get(
                where={"paper_id": paper_id},
                include=["documents", "metadatas"]
            )
            
            if not results['ids']:
                return None
            
            # Separate paper documents from chunks
            paper_doc = None
            chunks = []
            metadata = None
            
            for i, doc_id in enumerate(results['ids']):
                doc_metadata = results['metadatas'][i]
                document = results['documents'][i]
                
                if doc_metadata.get('type') == 'paper':
                    paper_doc = document
                    metadata = doc_metadata.copy()
                elif doc_metadata.get('type') == 'chunk':
                    chunks.append({
                        'text': document,
                        'chunk_index': doc_metadata.get('chunk_index', 0)
                    })
                    if metadata is None:
                        metadata = doc_metadata.copy()
                        metadata.pop('chunk_index', None)
                        metadata.pop('type', None)
            
            # Sort chunks by index
            chunks.sort(key=lambda x: x.get('chunk_index', 0))
            
            return {
                'paper_id': paper_id,
                'paper_document': paper_doc,
                'chunks': [chunk['text'] for chunk in chunks],
                'full_text': ' '.join([chunk['text'] for chunk in chunks]) if chunks else paper_doc,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id} from ChromaDB: {e}")
            return None
    
    def delete_papers(self, paper_ids: List[str]) -> bool:
        """Delete papers from the database"""
        try:
            for paper_id in paper_ids:
                # Get all documents for this paper
                results = self.collection.get(
                    where={"paper_id": paper_id},
                    include=["documents", "metadatas"]
                )
                
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
                    logger.info(f"Deleted paper {paper_id} and {len(results['ids'])} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting papers from ChromaDB: {e}")
            return False
    
    def get_stats(self) -> VectorDBStats:
        """Get database statistics"""
        try:
            count = self.collection.count()
            
            # Get unique papers count
            all_results = self.collection.get(include=["metadatas"])
            unique_papers = set()
            
            if all_results['metadatas']:
                for metadata in all_results['metadatas']:
                    unique_papers.add(metadata.get('paper_id', ''))
            
            return VectorDBStats(
                total_documents=count,
                unique_papers=len(unique_papers),
                provider='chroma',
                collection_name=self.collection_name,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting ChromaDB stats: {e}")
            return VectorDBStats(
                total_documents=0,
                unique_papers=0,
                provider='chroma',
                collection_name=self.collection_name
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Test basic operations
            count = self.collection.count()
            
            return {
                'status': 'healthy',
                'provider': 'chroma',
                'collection_name': self.collection_name,
                'document_count': count,
                'connection': 'active',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'chroma',
                'collection_name': self.collection_name,
                'error': str(e),
                'connection': 'failed',
                'timestamp': datetime.now().isoformat()
            }

# Register ChromaDB provider
VectorDBFactory.register_provider('chroma', ChromaVectorDB)