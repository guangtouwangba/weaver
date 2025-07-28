"""
Qdrant vector database implementation
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from .base import BaseVectorDB, VectorSearchResult, VectorDBStats, VectorDBFactory
from retrieval.arxiv_client import Paper

logger = logging.getLogger(__name__)

class QdrantVectorDB(BaseVectorDB):
    """Qdrant implementation of vector database"""
    
    def __init__(self, config: Dict[str, Any]):
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant is not installed. Install with: pip install qdrant-client")
        
        super().__init__(config)
        
        # Extract configuration
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6333)
        self.api_key = config.get('api_key')
        self.collection_name = config.get('collection_name', 'research-papers')
        self.vector_size = config.get('vector_size', 384)  # Default for all-MiniLM-L6-v2
        
        # Initialize Qdrant client
        if self.api_key:
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key
            )
        else:
            self.client = QdrantClient(
                host=self.host,
                port=self.port
            )
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
        
        logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Qdrant collection created: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection exists: {e}")
            raise
    
    def add_papers(self, papers: List[Paper], embeddings: List[List[float]]) -> List[str]:
        """Add papers with their embeddings"""
        if len(papers) != len(embeddings):
            raise ValueError("Number of papers must match number of embeddings")
        
        points = []
        doc_ids = []
        
        for i, (paper, embedding) in enumerate(zip(papers, embeddings)):
            doc_id = f"{paper.id}"
            doc_ids.append(doc_id)
            
            # Create payload (metadata)
            payload = {
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
            
            # Create point
            point = models.PointStruct(
                id=doc_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        try:
            # Batch upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(papers)} papers to Qdrant")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding papers to Qdrant: {e}")
            raise
    
    def add_paper_chunks(self, paper: Paper, chunks: List[str], embeddings: List[List[float]]) -> List[str]:
        """Add paper chunks with their embeddings"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        points = []
        doc_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_id = f"{paper.id}_chunk_{i}"
            doc_ids.append(doc_id)
            
            # Create payload (metadata)
            payload = {
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
            
            # Create point
            point = models.PointStruct(
                id=doc_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        try:
            # Batch upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(chunks)} chunks for paper {paper.id} to Qdrant")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding paper chunks to Qdrant: {e}")
            raise
    
    def search_papers(self, query_embedding: List[float], limit: int = 10, 
                     filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """Search for similar papers using vector similarity"""
        try:
            # Convert filters to Qdrant format
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, dict) and '$contains' in value:
                        # Handle contains filter
                        conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchText(text=value['$contains'])
                            )
                        )
                    else:
                        conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    if len(conditions) == 1:
                        qdrant_filter = models.Filter(must=conditions)
                    else:
                        qdrant_filter = models.Filter(must=conditions)
            
            # Search Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=qdrant_filter,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for scored_point in search_result:
                result = VectorSearchResult(
                    id=str(scored_point.id),
                    document=scored_point.payload.get('document', ''),
                    metadata=scored_point.payload,
                    similarity_score=scored_point.score
                )
                formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results in Qdrant")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper and all its chunks by paper ID"""
        try:
            # Search for all points with this paper_id
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="paper_id",
                            match=models.MatchValue(value=paper_id)
                        )
                    ]
                ),
                with_payload=True,
                limit=10000  # Large number to get all chunks
            )
            
            points = search_result[0]  # First element is the list of points
            
            if not points:
                return None
            
            # Separate paper documents from chunks
            paper_doc = None
            chunks = []
            metadata = None
            
            for point in points:
                payload = point.payload
                document = payload.get('document', '')
                
                if payload.get('type') == 'paper':
                    paper_doc = document
                    metadata = payload.copy()
                elif payload.get('type') == 'chunk':
                    chunks.append({
                        'text': document,
                        'chunk_index': payload.get('chunk_index', 0)
                    })
                    if metadata is None:
                        metadata = payload.copy()
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
            logger.error(f"Error retrieving paper {paper_id} from Qdrant: {e}")
            return None
    
    def delete_papers(self, paper_ids: List[str]) -> bool:
        """Delete papers from the database"""
        try:
            for paper_id in paper_ids:
                # Delete by filter (all points with this paper_id)
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="paper_id",
                                    match=models.MatchValue(value=paper_id)
                                )
                            ]
                        )
                    )
                )
                logger.info(f"Deleted paper {paper_id} from Qdrant")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting papers from Qdrant: {e}")
            return False
    
    def get_stats(self) -> VectorDBStats:
        """Get database statistics"""
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            total_vectors = collection_info.vectors_count
            
            # Get unique papers count by scrolling through all points
            unique_papers = set()
            offset = None
            
            while True:
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,
                    offset=offset,
                    with_payload=["paper_id"]
                )
                
                points, next_offset = scroll_result
                
                for point in points:
                    if "paper_id" in point.payload:
                        unique_papers.add(point.payload["paper_id"])
                
                if next_offset is None:
                    break
                offset = next_offset
            
            return VectorDBStats(
                total_documents=total_vectors or 0,
                unique_papers=len(unique_papers),
                provider='qdrant',
                collection_name=self.collection_name,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting Qdrant stats: {e}")
            return VectorDBStats(
                total_documents=0,
                unique_papers=0,
                provider='qdrant',
                collection_name=self.collection_name
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Test basic operations
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                'status': 'healthy',
                'provider': 'qdrant',
                'collection_name': self.collection_name,
                'document_count': collection_info.vectors_count or 0,
                'connection': 'active',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'qdrant',
                'collection_name': self.collection_name,
                'error': str(e),
                'connection': 'failed',
                'timestamp': datetime.now().isoformat()
            }

# Register Qdrant provider if available
if QDRANT_AVAILABLE:
    VectorDBFactory.register_provider('qdrant', QdrantVectorDB)
else:
    logger.warning("Qdrant client not available. Install with: pip install qdrant-client")