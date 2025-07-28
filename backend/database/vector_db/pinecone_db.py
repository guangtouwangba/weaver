"""
Pinecone vector database implementation
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from .base import BaseVectorDB, VectorSearchResult, VectorDBStats, VectorDBFactory
from retrieval.arxiv_client import Paper

logger = logging.getLogger(__name__)

class PineconeVectorDB(BaseVectorDB):
    """Pinecone implementation of vector database"""
    
    def __init__(self, config: Dict[str, Any]):
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone is not installed. Install with: pip install pinecone-client")
        
        super().__init__(config)
        
        # Initialize Pinecone client
        api_key = config.get('api_key')
        if not api_key:
            raise ValueError("Pinecone API key is required")
        
        self.pc = Pinecone(api_key=api_key)
        
        # Extract configuration
        self.index_name = config.get('index_name', 'research-papers')
        self.dimension = config.get('dimension', 384)  # Default for all-MiniLM-L6-v2
        self.environment = config.get('environment', 'us-west1-gcp')
        
        # Create or get index
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)
        
        logger.info(f"Connected to Pinecone index: {self.index_name}")
    
    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            # Check if index exists
            indexes = self.pc.list_indexes()
            index_names = [idx['name'] for idx in indexes.get('indexes', [])]
            
            if self.index_name not in index_names:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=self.environment
                    )
                )
                logger.info(f"Pinecone index created: {self.index_name}")
            else:
                logger.info(f"Using existing Pinecone index: {self.index_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring Pinecone index exists: {e}")
            raise
    
    def add_papers(self, papers: List[Paper], embeddings: List[List[float]]) -> List[str]:
        """Add papers with their embeddings"""
        if len(papers) != len(embeddings):
            raise ValueError("Number of papers must match number of embeddings")
        
        vectors = []
        
        for paper, embedding in zip(papers, embeddings):
            doc_id = f"{paper.id}"
            
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
                "type": "paper",
                "document": paper.abstract or paper.summary or paper.title
            }
            
            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": metadata
            })
        
        try:
            # Batch upsert vectors
            self.index.upsert(vectors=vectors)
            logger.info(f"Added {len(papers)} papers to Pinecone")
            return [v["id"] for v in vectors]
            
        except Exception as e:
            logger.error(f"Error adding papers to Pinecone: {e}")
            raise
    
    def add_paper_chunks(self, paper: Paper, chunks: List[str], embeddings: List[List[float]]) -> List[str]:
        """Add paper chunks with their embeddings"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        vectors = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_id = f"{paper.id}_chunk_{i}"
            
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
                "type": "chunk",
                "document": chunk
            }
            
            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": metadata
            })
        
        try:
            # Batch upsert vectors
            self.index.upsert(vectors=vectors)
            logger.info(f"Added {len(chunks)} chunks for paper {paper.id} to Pinecone")
            return [v["id"] for v in vectors]
            
        except Exception as e:
            logger.error(f"Error adding paper chunks to Pinecone: {e}")
            raise
    
    def search_papers(self, query_embedding: List[float], limit: int = 10, 
                     filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """Search for similar papers using vector similarity"""
        try:
            # Convert filters to Pinecone format
            pinecone_filter = {}
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict) and '$contains' in value:
                        # Handle contains filter
                        pinecone_filter[key] = {"$in": [value['$contains']]}
                    else:
                        pinecone_filter[key] = value
            
            # Query Pinecone
            query_response = self.index.query(
                vector=query_embedding,
                top_k=limit,
                filter=pinecone_filter if pinecone_filter else None,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in query_response.get('matches', []):
                result = VectorSearchResult(
                    id=match['id'],
                    document=match['metadata'].get('document', ''),
                    metadata=match['metadata'],
                    similarity_score=match['score']
                )
                formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results in Pinecone")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            return []
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper and all its chunks by paper ID"""
        try:
            # Query for all documents with this paper_id
            query_response = self.index.query(
                vector=[0.0] * self.dimension,  # Dummy vector
                top_k=10000,  # Large number to get all chunks
                filter={"paper_id": paper_id},
                include_metadata=True
            )
            
            if not query_response.get('matches'):
                return None
            
            # Separate paper documents from chunks
            paper_doc = None
            chunks = []
            metadata = None
            
            for match in query_response['matches']:
                match_metadata = match['metadata']
                document = match_metadata.get('document', '')
                
                if match_metadata.get('type') == 'paper':
                    paper_doc = document
                    metadata = match_metadata.copy()
                elif match_metadata.get('type') == 'chunk':
                    chunks.append({
                        'text': document,
                        'chunk_index': match_metadata.get('chunk_index', 0)
                    })
                    if metadata is None:
                        metadata = match_metadata.copy()
                        metadata.pop('chunk_index', None)
                        metadata.pop('type', None)
                        metadata.pop('document', None)
            
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
            logger.error(f"Error retrieving paper {paper_id} from Pinecone: {e}")
            return None
    
    def delete_papers(self, paper_ids: List[str]) -> bool:
        """Delete papers from the database"""
        try:
            for paper_id in paper_ids:
                # Delete by filter (all documents with this paper_id)
                self.index.delete(filter={"paper_id": paper_id})
                logger.info(f"Deleted paper {paper_id} from Pinecone")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting papers from Pinecone: {e}")
            return False
    
    def get_stats(self) -> VectorDBStats:
        """Get database statistics"""
        try:
            # Get index stats
            stats = self.index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            
            # Estimate unique papers (this is approximate since we can't easily query all metadata)
            # Assuming average of 5 chunks per paper
            estimated_papers = max(1, total_vectors // 5)
            
            return VectorDBStats(
                total_documents=total_vectors,
                unique_papers=estimated_papers,
                provider='pinecone',
                collection_name=self.index_name,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {e}")
            return VectorDBStats(
                total_documents=0,
                unique_papers=0,
                provider='pinecone',
                collection_name=self.index_name
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Test basic operations
            stats = self.index.describe_index_stats()
            
            return {
                'status': 'healthy',
                'provider': 'pinecone',
                'collection_name': self.index_name,
                'document_count': stats.get('total_vector_count', 0),
                'connection': 'active',
                'timestamp': datetime.now().isoformat(),
                'index_fullness': stats.get('index_fullness', 0)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'pinecone',
                'collection_name': self.index_name,
                'error': str(e),
                'connection': 'failed',
                'timestamp': datetime.now().isoformat()
            }

# Register Pinecone provider if available
if PINECONE_AVAILABLE:
    VectorDBFactory.register_provider('pinecone', PineconeVectorDB)
else:
    logger.warning("Pinecone client not available. Install with: pip install pinecone-client")