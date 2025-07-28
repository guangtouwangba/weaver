import chromadb
import uuid
import logging
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
from chromadb.config import Settings
from retrieval.arxiv_client import Paper

# Disable tqdm progress bars and verbose output to prevent BrokenPipeError
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
# Force CPU usage to avoid PyTorch meta tensor issues
os.environ["CUDA_VISIBLE_DEVICES"] = ""

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector database for storing and retrieving research papers"""
    
    def __init__(self, db_path: str = "./data/vector_db", collection_name: str = "research_papers"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model without device specification to avoid meta tensor issues
        try:
            # Import torch to set device before SentenceTransformer initialization
            import torch
            
            # Set default device to CPU to avoid meta tensor issues
            torch.set_default_device('cpu')
            
            # Initialize without device parameter
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Successfully initialized SentenceTransformer on CPU")
            
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer: {e}")
            # Last resort: try with explicit CPU device but catch the error
            try:
                import torch
                torch.set_default_device('cpu')
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Fallback SentenceTransformer initialization succeeded")
            except Exception as e2:
                logger.error(f"All SentenceTransformer initialization attempts failed: {e2}")
                raise RuntimeError(f"Cannot initialize SentenceTransformer: {e2}") from e2
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except ValueError:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Research papers with semantic embeddings"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_paper(self, paper: Paper, chunks: Optional[List[str]] = None) -> str:
        """
        Add a paper to the vector store
        
        Args:
            paper: Paper object to add
            chunks: Optional list of text chunks, if None uses abstract
            
        Returns:
            Document ID
        """
        try:
            # Use chunks if provided, otherwise split abstract
            if chunks is None:
                chunks = self._chunk_text(paper.abstract or paper.summary, chunk_size=500)
            
            doc_ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            # Create embeddings for each chunk
            for i, chunk in enumerate(chunks):
                doc_id = f"{paper.id}_chunk_{i}"
                doc_ids.append(doc_id)
                
                # Generate embedding
                embedding = self.embedding_model.encode(chunk).tolist()
                embeddings.append(embedding)
                documents.append(chunk)
                
                # Create metadata
                metadata = {
                    "paper_id": paper.id,
                    "title": paper.title,
                    "authors": ", ".join(paper.authors),
                    "categories": ", ".join(paper.categories),
                    "published": paper.published.isoformat(),
                    "chunk_index": i,
                    "pdf_url": paper.pdf_url,
                    "entry_id": paper.entry_id
                }
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=doc_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added paper {paper.id} with {len(chunks)} chunks to vector store")
            return paper.id
            
        except Exception as e:
            logger.error(f"Error adding paper to vector store: {e}")
            raise
    
    def search_papers(self, 
                     query: str, 
                     n_results: int = 10,
                     filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for papers using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with papers and scores
        """
        try:
            logger.info(f"Starting vector search for query: {query[:100]}...")
            logger.debug(f"n_results: {n_results}, filter_dict: {filter_dict}")
            
            # Generate query embedding
            logger.info("Generating query embedding...")
            query_embedding = self.embedding_model.encode(query).tolist()
            logger.info(f"Query embedding generated, dimension: {len(query_embedding)}")
            
            # Search collection
            logger.info("Querying ChromaDB collection...")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict,
                include=["documents", "metadatas", "distances"]
            )
            logger.info("ChromaDB query completed")
            
            # Format results
            logger.info("Formatting search results...")
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                logger.debug(f"Processing {len(results['ids'][0])} raw results")
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    formatted_results.append(result)
                    logger.debug(f"Formatted result {i+1}: {result['metadata'].get('title', 'Unknown')[:50]}...")
            else:
                logger.warning("No results returned from ChromaDB")
            
            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            error_msg = f"Error searching vector store: {e}"
            logger.error(error_msg, exc_info=True)
            return []
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get all chunks for a specific paper ID
        
        Args:
            paper_id: Paper ID to retrieve
            
        Returns:
            Paper data with all chunks
        """
        try:
            results = self.collection.get(
                where={"paper_id": paper_id},
                include=["documents", "metadatas"]
            )
            
            if not results['ids']:
                return None
            
            # Combine all chunks for the paper
            chunks = []
            metadata = None
            
            for i, doc_id in enumerate(results['ids']):
                chunks.append(results['documents'][i])
                if metadata is None:
                    metadata = results['metadatas'][i].copy()
                    metadata.pop('chunk_index', None)
            
            return {
                'paper_id': paper_id,
                'chunks': chunks,
                'full_text': ' '.join(chunks),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id}: {e}")
            return None
    
    def delete_paper(self, paper_id: str) -> bool:
        """
        Delete a paper and all its chunks from the vector store
        
        Args:
            paper_id: Paper ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all chunks for the paper
            results = self.collection.get(
                where={"paper_id": paper_id},
                include=["documents", "metadatas"]
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted paper {paper_id} and {len(results['ids'])} chunks")
                return True
            else:
                logger.warning(f"Paper {paper_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting paper {paper_id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get unique papers count
            all_results = self.collection.get(include=["metadatas"])
            unique_papers = set()
            
            if all_results['metadatas']:
                for metadata in all_results['metadatas']:
                    unique_papers.add(metadata.get('paper_id', ''))
            
            return {
                'total_chunks': count,
                'unique_papers': len(unique_papers),
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'error': str(e)}
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into chunks for embedding
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def search_by_author(self, author_name: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search papers by author name"""
        return self.search_papers(
            query=f"author {author_name}",
            n_results=n_results,
            filter_dict={"authors": {"$contains": author_name}}
        )
    
    def search_by_category(self, category: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search papers by category"""
        return self.search_papers(
            query=f"category {category}",
            n_results=n_results,
            filter_dict={"categories": {"$contains": category}}
        )