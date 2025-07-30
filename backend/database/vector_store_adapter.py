"""
Adapter to provide backward compatibility between old VectorStore interface and new multi-provider system
"""
import logging
from typing import List, Dict, Any, Optional
from retrieval.arxiv_client import Paper
from database.config_manager import get_config_manager
from database.embeddings.base import BaseEmbeddingModel
from database.vector_db.base import BaseVectorDB, VectorSearchResult

logger = logging.getLogger(__name__)

class VectorStoreAdapter:
    """
    Adapter class that provides the old VectorStore interface while using the new multi-provider system
    """
    
    def __init__(self, db_path: str = "./data/vector_db", collection_name: str = "research-papers"):
        """Initialize with configuration manager"""
        self.config_manager = get_config_manager()
        self.vector_db = self.config_manager.get_vector_db_instance()
        self.embedding_model = self.config_manager.get_embedding_model_instance()
        
        logger.info(f"VectorStoreAdapter initialized with {self.vector_db.provider} vector DB and {self.embedding_model.provider} embeddings")
    
    def add_paper(self, paper: Paper, chunks: Optional[List[str]] = None) -> str:
        """
        Add a paper to the vector database (backward compatibility method)
        
        Args:
            paper: Paper object to add
            chunks: Optional list of text chunks, if None, uses paper abstract/summary
            
        Returns:
            Document ID of the added paper
        """
        try:
            if chunks:
                # Generate embeddings for chunks
                embeddings = self.embedding_model.generate_embeddings(chunks)
                doc_ids = self.vector_db.add_paper_chunks(paper, chunks, embeddings)
                logger.info(f"Added paper {paper.id} with {len(chunks)} chunks")
                return doc_ids[0] if doc_ids else f"{paper.id}_chunk_0"
            else:
                # Use paper abstract/summary
                text = paper.abstract or paper.summary or paper.title
                embedding = self.embedding_model.generate_embeddings([text])
                doc_ids = self.vector_db.add_papers([paper], embedding)
                logger.info(f"Added paper {paper.id}")
                return doc_ids[0] if doc_ids else paper.id
                
        except Exception as e:
            logger.error(f"Error adding paper {paper.id}: {e}")
            return f"error_{paper.id}"
    
    def search_papers(self, 
                     query: str, 
                     n_results: int = 10, 
                     similarity_threshold: float = 0.5,
                     filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for papers using vector similarity (backward compatibility method)
        
        Args:
            query: Search query text
            n_results: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold
            filters: Optional filters to apply
            
        Returns:
            List of search results in old format
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.generate_embeddings([query])[0]
            
            # Search using vector database
            search_results = self.vector_db.search_papers(
                query_embedding=query_embedding,
                limit=n_results,
                filters=filters
            )
            
            # Convert to old format
            results = []
            for result in search_results:
                if result.similarity_score >= similarity_threshold:
                    results.append({
                        'id': result.id,
                        'document': result.document,
                        'metadata': result.metadata,
                        'similarity': result.similarity_score,
                        'paper_id': result.metadata.get('paper_id', result.id),
                        'title': result.metadata.get('title', ''),
                        'authors': result.metadata.get('authors', ''),
                        'abstract': result.document
                    })
            
            logger.info(f"Found {len(results)} papers for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get database statistics (backward compatibility method)"""
        try:
            stats = self.vector_db.get_stats()
            return {
                'total_chunks': stats.total_documents,
                'unique_papers': stats.unique_papers,
                'provider': stats.provider,
                'collection_name': stats.collection_name,
                'last_updated': stats.last_updated
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                'total_chunks': 0,
                'unique_papers': 0,
                'provider': 'unknown',
                'collection_name': 'unknown'
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the vector database"""
        try:
            return self.vector_db.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }