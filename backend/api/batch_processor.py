"""
Batch processing pipeline for paper embedding and vector storage
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from retrieval.arxiv_client import Paper
from database.embeddings import BaseEmbeddingModel
from database.vector_db import BaseVectorDB
from database.models import Paper as SQLPaper

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Handles batch processing of papers for embedding and vector storage"""
    
    def __init__(self, 
                 embedding_model: BaseEmbeddingModel,
                 vector_db: BaseVectorDB,
                 batch_size: int = 10,
                 max_workers: int = 3,
                 chunk_size: int = 500,
                 chunk_overlap: int = 50):
        """
        Initialize batch processor
        
        Args:
            embedding_model: Embedding model instance
            vector_db: Vector database instance
            batch_size: Number of papers to process in each batch
            max_workers: Maximum number of concurrent workers
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between text chunks
        """
        self.embedding_model = embedding_model
        self.vector_db = vector_db
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Processing statistics
        self.stats = {
            'papers_processed': 0,
            'papers_embedded': 0,
            'papers_stored': 0,
            'embedding_errors': 0,
            'storage_errors': 0,
            'total_chunks': 0,
            'processing_time': 0.0,
            'start_time': None,
            'end_time': None
        }
    
    async def process_papers_batch(self, papers: List[Paper]) -> Dict[str, Any]:
        """
        Process a batch of papers with embedding and vector storage
        
        Args:
            papers: List of Paper objects to process
            
        Returns:
            Dictionary with processing results and statistics
        """
        if not papers:
            return self.stats
        
        logger.info(f"Starting batch processing of {len(papers)} papers")
        self.stats['start_time'] = time.time()
        
        try:
            # Process papers in smaller batches to manage memory
            for i in range(0, len(papers), self.batch_size):
                batch = papers[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(papers) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")
                
                # Process single batch
                await self._process_single_batch(batch, batch_num)
                
                # Small delay between batches to prevent rate limiting
                if i + self.batch_size < len(papers):
                    await asyncio.sleep(0.5)
            
            self.stats['end_time'] = time.time()
            self.stats['processing_time'] = self.stats['end_time'] - self.stats['start_time']
            
            logger.info(f"Batch processing completed in {self.stats['processing_time']:.2f}s")
            logger.info(f"Results: {self.stats['papers_processed']} processed, "
                       f"{self.stats['papers_embedded']} embedded, {self.stats['papers_stored']} stored")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            self.stats['end_time'] = time.time()
            self.stats['processing_time'] = self.stats['end_time'] - self.stats['start_time']
            raise
    
    async def _process_single_batch(self, papers: List[Paper], batch_num: int):
        """Process a single batch of papers"""
        try:
            # Step 1: Prepare paper texts and chunks
            paper_data = []
            for paper in papers:
                chunks = self._chunk_paper_text(paper)
                paper_data.append({
                    'paper': paper,
                    'chunks': chunks,
                    'full_text': paper.abstract or paper.summary or paper.title
                })
            
            # Step 2: Generate embeddings (can be done in parallel for different papers)
            embedding_tasks = []
            for data in paper_data:
                task = self._embed_paper_chunks(data['paper'], data['chunks'])
                embedding_tasks.append(task)
            
            # Wait for all embedding tasks to complete
            embedding_results = await asyncio.gather(*embedding_tasks, return_exceptions=True)
            
            # Step 3: Store successful embeddings in vector database
            successful_embeddings = []
            for i, result in enumerate(embedding_results):
                if isinstance(result, Exception):
                    logger.error(f"Embedding failed for paper {papers[i].title}: {result}")
                    self.stats['embedding_errors'] += 1
                else:
                    successful_embeddings.append(result)
                    self.stats['papers_embedded'] += 1
            
            # Step 4: Batch store in vector database
            if successful_embeddings:
                await self._batch_store_embeddings(successful_embeddings)
            
            # Update processing count
            self.stats['papers_processed'] += len(papers)
            
            logger.info(f"Batch {batch_num} completed: {len(successful_embeddings)}/{len(papers)} papers embedded")
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            raise
    
    def _chunk_paper_text(self, paper: Paper) -> List[str]:
        """Split paper text into chunks for embedding"""
        # Get full text content
        text_parts = []
        
        # Add title
        if paper.title:
            text_parts.append(f"Title: {paper.title}")
        
        # Add authors
        if paper.authors:
            text_parts.append(f"Authors: {', '.join(paper.authors)}")
        
        # Add categories
        if paper.categories:
            text_parts.append(f"Categories: {', '.join(paper.categories)}")
        
        # Add abstract/summary
        main_text = paper.abstract or paper.summary or ""
        if main_text:
            text_parts.append(f"Abstract: {main_text}")
        
        # Combine all parts
        full_text = "\n\n".join(text_parts)
        
        # Split into chunks
        chunks = self._split_text_into_chunks(full_text)
        
        # If no chunks created, create one from title + abstract
        if not chunks:
            fallback_text = f"{paper.title}\n\n{paper.abstract or paper.summary or ''}"
            chunks = [fallback_text.strip()]
        
        logger.debug(f"Created {len(chunks)} chunks for paper: {paper.title}")
        return chunks
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If we're not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_breaks = ['.', '!', '?', '\n\n']
                best_break = -1
                
                # Search backwards from the end for a good break point
                for i in range(end, max(start + self.chunk_size // 2, start), -1):
                    if i < len(text) and text[i] in sentence_breaks:
                        best_break = i + 1
                        break
                
                if best_break > 0:
                    end = best_break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start point with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    async def _embed_paper_chunks(self, paper: Paper, chunks: List[str]) -> Dict[str, Any]:
        """Generate embeddings for paper chunks"""
        try:
            # Generate embeddings for all chunks
            embeddings = self.embedding_model.embed_texts(chunks)
            
            self.stats['total_chunks'] += len(chunks)
            
            return {
                'paper': paper,
                'chunks': chunks,
                'embeddings': embeddings,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error embedding paper {paper.title}: {e}")
            return {
                'paper': paper,
                'chunks': chunks,
                'embeddings': [],
                'success': False,
                'error': str(e)
            }
    
    async def _batch_store_embeddings(self, embedding_results: List[Dict[str, Any]]):
        """Store embeddings in vector database"""
        try:
            # Separate papers with successful embeddings
            papers_to_store = []
            chunk_data = []
            
            for result in embedding_results:
                if result['success'] and result['embeddings']:
                    paper = result['paper']
                    chunks = result['chunks']
                    embeddings = result['embeddings']
                    
                    # Store using chunks method for better granularity
                    try:
                        doc_ids = self.vector_db.add_paper_chunks(paper, chunks, embeddings)
                        papers_to_store.append(paper)
                        self.stats['papers_stored'] += 1
                        logger.debug(f"Stored {len(doc_ids)} chunks for paper: {paper.title}")
                        
                    except Exception as e:
                        logger.error(f"Error storing paper {paper.title} in vector DB: {e}")
                        self.stats['storage_errors'] += 1
            
            logger.info(f"Successfully stored {len(papers_to_store)} papers in vector database")
            
        except Exception as e:
            logger.error(f"Error in batch storage: {e}")
            self.stats['storage_errors'] += len(embedding_results)
            raise
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = self.stats.copy()
        
        # Calculate rates if processing is complete
        if stats['processing_time'] > 0:
            stats['papers_per_second'] = stats['papers_processed'] / stats['processing_time']
            stats['chunks_per_second'] = stats['total_chunks'] / stats['processing_time']
        
        # Calculate success rates
        if stats['papers_processed'] > 0:
            stats['embedding_success_rate'] = (stats['papers_embedded'] / stats['papers_processed']) * 100
            stats['storage_success_rate'] = (stats['papers_stored'] / stats['papers_processed']) * 100
        
        return stats
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.stats = {
            'papers_processed': 0,
            'papers_embedded': 0,
            'papers_stored': 0,
            'embedding_errors': 0,
            'storage_errors': 0,
            'total_chunks': 0,
            'processing_time': 0.0,
            'start_time': None,
            'end_time': None
        }

class BatchProcessorFactory:
    """Factory for creating batch processors with different configurations"""
    
    @staticmethod
    def create_fast_processor(embedding_model: BaseEmbeddingModel, 
                            vector_db: BaseVectorDB) -> BatchProcessor:
        """Create a processor optimized for speed"""
        return BatchProcessor(
            embedding_model=embedding_model,
            vector_db=vector_db,
            batch_size=20,
            max_workers=5,
            chunk_size=300,
            chunk_overlap=30
        )
    
    @staticmethod
    def create_quality_processor(embedding_model: BaseEmbeddingModel, 
                               vector_db: BaseVectorDB) -> BatchProcessor:
        """Create a processor optimized for quality"""
        return BatchProcessor(
            embedding_model=embedding_model,
            vector_db=vector_db,
            batch_size=5,
            max_workers=2,
            chunk_size=800,
            chunk_overlap=100
        )
    
    @staticmethod
    def create_balanced_processor(embedding_model: BaseEmbeddingModel, 
                                vector_db: BaseVectorDB) -> BatchProcessor:
        """Create a processor with balanced speed and quality"""
        return BatchProcessor(
            embedding_model=embedding_model,
            vector_db=vector_db,
            batch_size=10,
            max_workers=3,
            chunk_size=500,
            chunk_overlap=50
        )