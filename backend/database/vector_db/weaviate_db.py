"""
Weaviate vector database implementation
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

from .base import BaseVectorDB, VectorSearchResult, VectorDBStats, VectorDBFactory
from retrieval.arxiv_client import Paper

logger = logging.getLogger(__name__)

class WeaviateVectorDB(BaseVectorDB):
    """Weaviate implementation of vector database"""
    
    def __init__(self, config: Dict[str, Any]):
        if not WEAVIATE_AVAILABLE:
            raise ImportError("Weaviate is not installed. Install with: pip install weaviate-client")
        
        super().__init__(config)
        
        # Extract configuration
        self.url = config.get('url', 'http://localhost:8080')
        self.api_key = config.get('api_key')
        self.class_name = config.get('class_name', 'ResearchPaper')
        
        # Initialize Weaviate client
        auth_config = None
        if self.api_key:
            auth_config = weaviate.AuthApiKey(api_key=self.api_key)
        
        self.client = weaviate.Client(
            url=self.url,
            auth_client_secret=auth_config
        )
        
        # Ensure schema exists
        self._ensure_schema_exists()
        
        logger.info(f"Connected to Weaviate at {self.url}")
    
    def _ensure_schema_exists(self):
        """Create schema if it doesn't exist"""
        try:
            # Check if class exists
            existing_classes = self.client.schema.get()['classes']
            class_names = [cls['class'] for cls in existing_classes]
            
            if self.class_name not in class_names:
                logger.info(f"Creating Weaviate class: {self.class_name}")
                
                # Define schema
                schema = {
                    "class": self.class_name,
                    "description": "Research papers with semantic embeddings",
                    "properties": [
                        {
                            "name": "paperId",
                            "dataType": ["string"],
                            "description": "Unique paper identifier"
                        },
                        {
                            "name": "arxivId",
                            "dataType": ["string"],
                            "description": "ArXiv identifier"
                        },
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Paper title"
                        },
                        {
                            "name": "authors",
                            "dataType": ["string"],
                            "description": "Paper authors"
                        },
                        {
                            "name": "categories",
                            "dataType": ["string"],
                            "description": "Paper categories"
                        },
                        {
                            "name": "published",
                            "dataType": ["string"],
                            "description": "Publication date"
                        },
                        {
                            "name": "document",
                            "dataType": ["text"],
                            "description": "Paper content or chunk"
                        },
                        {
                            "name": "documentType",
                            "dataType": ["string"],
                            "description": "Type of document (paper or chunk)"
                        },
                        {
                            "name": "chunkIndex",
                            "dataType": ["int"],
                            "description": "Index of chunk within paper"
                        },
                        {
                            "name": "pdfUrl",
                            "dataType": ["string"],
                            "description": "PDF URL"
                        },
                        {
                            "name": "entryId",
                            "dataType": ["string"],
                            "description": "Entry ID"
                        },
                        {
                            "name": "doi",
                            "dataType": ["string"],
                            "description": "DOI"
                        }
                    ],
                    "vectorizer": "none"  # We provide our own vectors
                }
                
                self.client.schema.create_class(schema)
                logger.info(f"Weaviate class created: {self.class_name}")
            else:
                logger.info(f"Using existing Weaviate class: {self.class_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring Weaviate schema exists: {e}")
            raise
    
    def add_papers(self, papers: List[Paper], embeddings: List[List[float]]) -> List[str]:
        """Add papers with their embeddings"""
        if len(papers) != len(embeddings):
            raise ValueError("Number of papers must match number of embeddings")
        
        doc_ids = []
        
        try:
            # Start batch
            with self.client.batch as batch:
                batch.batch_size = 100
                
                for paper, embedding in zip(papers, embeddings):
                    doc_id = f"{paper.id}"
                    doc_ids.append(doc_id)
                    
                    # Create properties
                    properties = {
                        "paperId": paper.id,
                        "arxivId": paper.arxiv_id,
                        "title": paper.title,
                        "authors": ", ".join(paper.authors),
                        "categories": ", ".join(paper.categories),
                        "published": paper.published.isoformat(),
                        "document": paper.abstract or paper.summary or paper.title,
                        "documentType": "paper",
                        "chunkIndex": 0,
                        "pdfUrl": paper.pdf_url or "",
                        "entryId": paper.entry_id or "",
                        "doi": paper.doi or ""
                    }
                    
                    # Add to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.class_name,
                        uuid=doc_id,
                        vector=embedding
                    )
            
            logger.info(f"Added {len(papers)} papers to Weaviate")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding papers to Weaviate: {e}")
            raise
    
    def add_paper_chunks(self, paper: Paper, chunks: List[str], embeddings: List[List[float]]) -> List[str]:
        """Add paper chunks with their embeddings"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        doc_ids = []
        
        try:
            # Start batch
            with self.client.batch as batch:
                batch.batch_size = 100
                
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    doc_id = f"{paper.id}_chunk_{i}"
                    doc_ids.append(doc_id)
                    
                    # Create properties
                    properties = {
                        "paperId": paper.id,
                        "arxivId": paper.arxiv_id,
                        "title": paper.title,
                        "authors": ", ".join(paper.authors),
                        "categories": ", ".join(paper.categories),
                        "published": paper.published.isoformat(),
                        "document": chunk,
                        "documentType": "chunk",
                        "chunkIndex": i,
                        "pdfUrl": paper.pdf_url or "",
                        "entryId": paper.entry_id or "",
                        "doi": paper.doi or ""
                    }
                    
                    # Add to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.class_name,
                        uuid=doc_id,
                        vector=embedding
                    )
            
            logger.info(f"Added {len(chunks)} chunks for paper {paper.id} to Weaviate")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding paper chunks to Weaviate: {e}")
            raise
    
    def search_papers(self, query_embedding: List[float], limit: int = 10, 
                     filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """Search for similar papers using vector similarity"""
        try:
            # Build query
            query = (
                self.client.query
                .get(self.class_name)
                .with_near_vector({"vector": query_embedding})
                .with_limit(limit)
                .with_additional(["certainty"])
                .with_properties([
                    "paperId", "arxivId", "title", "authors", "categories", 
                    "published", "document", "documentType", "chunkIndex",
                    "pdfUrl", "entryId", "doi"
                ])
            )
            
            # Add filters if provided
            if filters:
                where_filter = {}
                for key, value in filters.items():
                    if isinstance(value, dict) and '$contains' in value:
                        where_filter["path"] = [key]
                        where_filter["operator"] = "Like"
                        where_filter["valueText"] = f"*{value['$contains']}*"
                    else:
                        where_filter["path"] = [key]
                        where_filter["operator"] = "Equal"
                        where_filter["valueText"] = str(value)
                
                query = query.with_where(where_filter)
            
            # Execute query
            result = query.do()
            
            # Format results
            formatted_results = []
            if "data" in result and "Get" in result["data"] and self.class_name in result["data"]["Get"]:
                for item in result["data"]["Get"][self.class_name]:
                    # Extract metadata
                    metadata = {
                        "paper_id": item.get("paperId", ""),
                        "arxiv_id": item.get("arxivId", ""),
                        "title": item.get("title", ""),
                        "authors": item.get("authors", ""),
                        "categories": item.get("categories", ""),
                        "published": item.get("published", ""),
                        "type": item.get("documentType", ""),
                        "chunk_index": item.get("chunkIndex", 0),
                        "pdf_url": item.get("pdfUrl", ""),
                        "entry_id": item.get("entryId", ""),
                        "doi": item.get("doi", "")
                    }
                    
                    result_obj = VectorSearchResult(
                        id=f"{item.get('paperId', '')}_{item.get('chunkIndex', 0)}",
                        document=item.get("document", ""),
                        metadata=metadata,
                        similarity_score=item.get("_additional", {}).get("certainty", 0.0)
                    )
                    formatted_results.append(result_obj)
            
            logger.info(f"Found {len(formatted_results)} results in Weaviate")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Weaviate: {e}")
            return []
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper and all its chunks by paper ID"""
        try:
            # Query for all documents with this paper_id
            result = (
                self.client.query
                .get(self.class_name)
                .with_where({
                    "path": ["paperId"],
                    "operator": "Equal",
                    "valueText": paper_id
                })
                .with_properties([
                    "paperId", "arxivId", "title", "authors", "categories", 
                    "published", "document", "documentType", "chunkIndex",
                    "pdfUrl", "entryId", "doi"
                ])
                .do()
            )
            
            if not result.get("data", {}).get("Get", {}).get(self.class_name):
                return None
            
            # Separate paper documents from chunks
            paper_doc = None
            chunks = []
            metadata = None
            
            for item in result["data"]["Get"][self.class_name]:
                document = item.get("document", "")
                doc_type = item.get("documentType", "")
                
                if doc_type == "paper":
                    paper_doc = document
                    metadata = {
                        "paper_id": item.get("paperId", ""),
                        "arxiv_id": item.get("arxivId", ""),
                        "title": item.get("title", ""),
                        "authors": item.get("authors", ""),
                        "categories": item.get("categories", ""),
                        "published": item.get("published", ""),
                        "pdf_url": item.get("pdfUrl", ""),
                        "entry_id": item.get("entryId", ""),
                        "doi": item.get("doi", "")
                    }
                elif doc_type == "chunk":
                    chunks.append({
                        'text': document,
                        'chunk_index': item.get("chunkIndex", 0)
                    })
                    if metadata is None:
                        metadata = {
                            "paper_id": item.get("paperId", ""),
                            "arxiv_id": item.get("arxivId", ""),
                            "title": item.get("title", ""),
                            "authors": item.get("authors", ""),
                            "categories": item.get("categories", ""),
                            "published": item.get("published", ""),
                            "pdf_url": item.get("pdfUrl", ""),
                            "entry_id": item.get("entryId", ""),
                            "doi": item.get("doi", "")
                        }
            
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
            logger.error(f"Error retrieving paper {paper_id} from Weaviate: {e}")
            return None
    
    def delete_papers(self, paper_ids: List[str]) -> bool:
        """Delete papers from the database"""
        try:
            for paper_id in paper_ids:
                # Delete by paper_id
                self.client.batch.delete_objects(
                    class_name=self.class_name,
                    where={
                        "path": ["paperId"],
                        "operator": "Equal",
                        "valueText": paper_id
                    }
                )
                logger.info(f"Deleted paper {paper_id} from Weaviate")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting papers from Weaviate: {e}")
            return False
    
    def get_stats(self) -> VectorDBStats:
        """Get database statistics"""
        try:
            # Get total count
            result = (
                self.client.query
                .aggregate(self.class_name)
                .with_meta_count()
                .do()
            )
            
            total_count = result.get("data", {}).get("Aggregate", {}).get(self.class_name, [{}])[0].get("meta", {}).get("count", 0)
            
            # Get unique papers count
            unique_papers_result = (
                self.client.query
                .aggregate(self.class_name)
                .with_group_by(["paperId"])
                .with_meta_count()
                .do()
            )
            
            unique_papers = len(unique_papers_result.get("data", {}).get("Aggregate", {}).get(self.class_name, []))
            
            return VectorDBStats(
                total_documents=total_count,
                unique_papers=unique_papers,
                provider='weaviate',
                collection_name=self.class_name,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting Weaviate stats: {e}")
            return VectorDBStats(
                total_documents=0,
                unique_papers=0,
                provider='weaviate',
                collection_name=self.class_name
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Test basic operations
            ready = self.client.is_ready()
            live = self.client.is_live()
            
            return {
                'status': 'healthy' if ready and live else 'unhealthy',
                'provider': 'weaviate',
                'collection_name': self.class_name,
                'ready': ready,
                'live': live,
                'connection': 'active',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'weaviate',
                'collection_name': self.class_name,
                'error': str(e),
                'connection': 'failed',
                'timestamp': datetime.now().isoformat()
            }

# Register Weaviate provider if available
if WEAVIATE_AVAILABLE:
    VectorDBFactory.register_provider('weaviate', WeaviateVectorDB)
else:
    logger.warning("Weaviate client not available. Install with: pip install weaviate-client")