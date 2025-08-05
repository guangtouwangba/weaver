#!/usr/bin/env python3
"""
Document indexer for RAG module
Handles the complete pipeline from documents to vector index
"""

import logging
import sys
import os
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# Add backend to path for importing storage manager
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from storage.storage_manager import create_storage_manager

from .pdf_extractor import PDFExtractor
from .text_chunker import TextChunker, TextChunk
from .embeddings import EmbeddingGenerator
from ..vector_db.chroma_client import ChromaVectorStore

logger = logging.getLogger(__name__)

class DocumentIndexer:
    """Handles the complete document indexing pipeline"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_config = config.get('rag', {})
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize all pipeline components"""
        try:
            # Initialize storage manager for PDF access
            storage_config = self.config.get('pdf_storage', {})
            self.storage_manager = create_storage_manager(storage_config)
            
            # Initialize PDF extractor
            self.pdf_extractor = PDFExtractor(storage_manager=self.storage_manager)
            
            # Initialize text chunker
            text_config = self.rag_config.get('text_processing', {})
            self.text_chunker = TextChunker(
                chunk_size=text_config.get('chunk_size', 1000),
                chunk_overlap=text_config.get('chunk_overlap', 200),
                max_chunks_per_doc=text_config.get('max_chunks_per_doc', 50)
            )
            
            # Initialize embedding generator
            embedding_config = self.rag_config.get('embeddings', {})
            provider = embedding_config.get('provider', 'sentence-transformers')
            model_name = embedding_config.get('model', 'sentence-transformers/all-MiniLM-L6-v2')
            device = embedding_config.get('device', 'cpu')
            
            self.embedding_generator = EmbeddingGenerator(
                provider=provider,
                model_name=model_name,
                device=device
            )
            
            # Initialize vector store
            vector_config = self.rag_config.get('vector_db', {})
            self.vector_store = ChromaVectorStore(
                persist_directory=vector_config.get('persist_directory', './rag_vector_db'),
                collection_name=vector_config.get('collection_name', 'arxiv_papers')
            )
            
            logger.info("Document indexer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize document indexer: {e}")
            raise
    
    def index_documents(self, papers: List[Dict[str, Any]], 
                       batch_size: int = 32, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Index a list of papers into the vector store
        
        Args:
            papers: List of paper dictionaries from database
            batch_size: Batch size for embeddings
            force_reindex: Whether to reindex existing documents
            
        Returns:
            Dictionary with indexing results
        """
        if not papers:
            logger.warning("No papers provided for indexing")
            return {'success': False, 'error': 'No papers provided'}
        
        logger.info(f"Starting indexing process for {len(papers)} papers")
        
        results = {
            'success': True,
            'total_papers': len(papers),
            'processed_papers': 0,
            'total_chunks': 0,
            'skipped_papers': 0,
            'failed_papers': 0,
            'errors': []
        }
        
        all_chunks = []
        
        # Process each paper
        for i, paper in enumerate(tqdm(papers, desc="Processing papers")):
            try:
                arxiv_id = paper.get('arxiv_id', f'unknown_{i}')
                
                # Check if already indexed (unless force_reindex)
                if not force_reindex and self._is_document_indexed(arxiv_id):
                    logger.debug(f"Skipping already indexed paper: {arxiv_id}")
                    results['skipped_papers'] += 1
                    continue
                
                # Process single paper
                paper_chunks = self._process_single_paper(paper)
                
                if paper_chunks:
                    all_chunks.extend(paper_chunks)
                    results['processed_papers'] += 1
                    results['total_chunks'] += len(paper_chunks)
                    logger.info(f"Processed paper {arxiv_id}: {len(paper_chunks)} chunks")
                else:
                    results['failed_papers'] += 1
                    logger.warning(f"Failed to process paper: {arxiv_id}")
                
            except Exception as e:
                error_msg = f"Error processing paper {paper.get('arxiv_id', 'unknown')}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed_papers'] += 1
        
        # Index all chunks into vector store
        if all_chunks:
            logger.info(f"Indexing {len(all_chunks)} chunks into vector store")
            success = self._index_chunks(all_chunks, batch_size)
            
            if not success:
                results['success'] = False
                results['errors'].append("Failed to index chunks into vector store")
        
        logger.info(f"Indexing complete: {results['processed_papers']}/{results['total_papers']} papers, "
                   f"{results['total_chunks']} chunks")
        
        return results
    
    def _process_single_paper(self, paper: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single paper through the complete pipeline"""
        arxiv_id = paper.get('arxiv_id', 'unknown')
        pdf_path = paper.get('pdf_path', '')
        
        if not pdf_path:
            logger.warning(f"No PDF path for paper {arxiv_id}")
            return []
        
        try:
            # Step 1: Extract text from PDF
            text = self.pdf_extractor.extract_text_from_path(pdf_path)
            
            if not text:
                logger.warning(f"No text extracted from {pdf_path}")
                return []
            
            # Step 2: Create document metadata
            doc_metadata = {
                'arxiv_id': arxiv_id,
                'title': paper.get('title', ''),
                'authors': paper.get('authors', ''),
                'abstract': paper.get('abstract', ''),
                'categories': paper.get('categories', ''),
                'published': paper.get('published', ''),
                'pdf_path': pdf_path
            }
            
            # Step 3: Chunk the text
            chunks = self.text_chunker.chunk_document(text, arxiv_id, doc_metadata)
            
            if not chunks:
                logger.warning(f"No chunks created for paper {arxiv_id}")
                return []
            
            # Step 4: Generate embeddings for chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_generator.encode_texts(chunk_texts, show_progress=False)
            
            # Step 5: Combine chunks with embeddings and metadata
            chunk_dicts = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_dict = {
                    'chunk_id': chunk.chunk_id,
                    'content': chunk.content,
                    'source_doc': chunk.source_doc,
                    'page_number': chunk.page_number,
                    'chunk_index': i,
                    'embedding': embedding,
                    'metadata': {
                        **doc_metadata,
                        'chunk_page': chunk.page_number,
                        'chunk_start': chunk.start_char,
                        'chunk_end': chunk.end_char
                    }
                }
                chunk_dicts.append(chunk_dict)
            
            logger.debug(f"Created {len(chunk_dicts)} indexed chunks for {arxiv_id}")
            return chunk_dicts
            
        except Exception as e:
            logger.error(f"Failed to process paper {arxiv_id}: {e}")
            return []
    
    def _index_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """Index chunks into the vector store"""
        try:
            return self.vector_store.add_documents(chunks, batch_size=batch_size)
        except Exception as e:
            logger.error(f"Failed to index chunks: {e}")
            return False
    
    def _is_document_indexed(self, arxiv_id: str) -> bool:
        """Check if a document is already indexed"""
        try:
            # Search for any chunks from this document
            results = self.vector_store.collection.get(
                where={"source_doc": arxiv_id},
                limit=1
            )
            return len(results['ids']) > 0
        except Exception as e:
            logger.debug(f"Error checking if document {arxiv_id} is indexed: {e}")
            return False
    
    def reindex_document(self, paper: Dict[str, Any]) -> bool:
        """
        Reindex a single document (remove old chunks and add new ones)
        
        Args:
            paper: Paper dictionary from database
            
        Returns:
            True if successful, False otherwise
        """
        arxiv_id = paper.get('arxiv_id', 'unknown')
        
        try:
            # Remove existing chunks for this document
            self.vector_store.delete_by_source(arxiv_id)
            
            # Process and index the document
            chunks = self._process_single_paper(paper)
            
            if chunks:
                success = self._index_chunks(chunks)
                if success:
                    logger.info(f"Successfully reindexed document {arxiv_id} with {len(chunks)} chunks")
                    return True
            
            logger.warning(f"Failed to reindex document {arxiv_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to reindex document {arxiv_id}: {e}")
            return False
    
    def get_indexing_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current index
        
        Returns:
            Dictionary with indexing statistics
        """
        try:
            vector_stats = self.vector_store.get_collection_stats()
            
            # Get embedding model info
            embedding_info = self.embedding_generator.get_model_info()
            
            return {
                'vector_store': vector_stats,
                'embedding_model': embedding_info,
                'text_chunker': {
                    'chunk_size': self.text_chunker.chunk_size,
                    'chunk_overlap': self.text_chunker.chunk_overlap,
                    'max_chunks_per_doc': self.text_chunker.max_chunks_per_doc
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get indexing statistics: {e}")
            return {}
    
    def cleanup_orphaned_chunks(self, valid_arxiv_ids: List[str]) -> int:
        """
        Remove chunks for documents that no longer exist in the database
        
        Args:
            valid_arxiv_ids: List of valid arxiv IDs from database
            
        Returns:
            Number of orphaned chunks removed
        """
        try:
            # Get all unique source documents in the vector store
            results = self.vector_store.collection.get(include=['metadatas'])
            
            if not results['metadatas']:
                return 0
            
            indexed_docs = set()
            for metadata in results['metadatas']:
                if 'source_doc' in metadata:
                    indexed_docs.add(metadata['source_doc'])
            
            # Find orphaned documents
            valid_set = set(valid_arxiv_ids)
            orphaned_docs = indexed_docs - valid_set
            
            if not orphaned_docs:
                logger.info("No orphaned chunks found")
                return 0
            
            # Remove orphaned chunks
            removed_count = 0
            for orphaned_doc in orphaned_docs:
                if self.vector_store.delete_by_source(orphaned_doc):
                    removed_count += 1
            
            logger.info(f"Removed chunks for {removed_count} orphaned documents")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned chunks: {e}")
            return 0