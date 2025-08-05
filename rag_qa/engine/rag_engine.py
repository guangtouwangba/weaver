#!/usr/bin/env python3
"""
RAG Engine - Core orchestrator for RAG question answering
Combines retrieval and generation for intelligent question answering
"""

import logging
import sys
import os
from typing import List, Dict, Any, Optional, Tuple

# Add backend and rag_qa to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.config_loader import RAGConfigLoader
from utils.keyword_manager import KeywordManager
from processing.indexer import DocumentIndexer
from processing.embeddings import EmbeddingGenerator
from vector_db.chroma_client import ChromaVectorStore
from llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

class RAGEngine:
    """Main RAG engine that orchestrates the entire question-answering pipeline"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        
        # Load configuration
        self.config_loader = RAGConfigLoader(config_path)
        self.config = self.config_loader.get_config()
        self.rag_config = self.config_loader.get_rag_config()
        
        # Validate configuration
        self._validate_configuration()
        
        # Initialize components
        self._init_components()
        
        logger.info("RAG Engine initialized successfully")
    
    def _validate_configuration(self):
        """Validate RAG configuration before initialization"""
        try:
            # Check OpenAI API key for embedding and LLM
            embedding_config = self.rag_config.get('embeddings', {})
            llm_config = self.rag_config.get('llm', {})
            
            if (embedding_config.get('provider') == 'openai' or 
                llm_config.get('provider') == 'openai'):
                
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError(
                        "OpenAI API key required but not found. "
                        "Please set OPENAI_API_KEY in your .env file or environment variables."
                    )
                
                if not api_key.startswith('sk-'):
                    logger.warning("OpenAI API key format may be incorrect. Keys typically start with 'sk-'")
            
            # Validate embedding provider and model
            embedding_provider = embedding_config.get('provider', 'sentence-transformers')
            if embedding_provider not in ['openai', 'sentence-transformers']:
                raise ValueError(f"Unsupported embedding provider: {embedding_provider}")
            
            # Validate LLM provider and model
            llm_provider = llm_config.get('provider', 'openai')
            if llm_provider not in ['openai', 'anthropic', 'local']:
                raise ValueError(f"Unsupported LLM provider: {llm_provider}")
            
            # Validate vector database config
            vector_config = self.rag_config.get('vector_db', {})
            if vector_config.get('type', 'chroma') not in ['chroma', 'faiss']:
                raise ValueError(f"Unsupported vector database type: {vector_config.get('type')}")
            
            # Validate retrieval parameters
            retrieval_config = self.rag_config.get('retrieval', {})
            top_k = retrieval_config.get('top_k', 5)
            if not isinstance(top_k, int) or top_k < 1:
                raise ValueError(f"Invalid top_k value: {top_k}. Must be a positive integer.")
            
            similarity_threshold = retrieval_config.get('similarity_threshold', 0.7)
            if not isinstance(similarity_threshold, (int, float)) or not 0 <= similarity_threshold <= 1:
                raise ValueError(f"Invalid similarity_threshold: {similarity_threshold}. Must be between 0 and 1.")
            
            logger.info("Configuration validation passed")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def _init_components(self):
        """Initialize all RAG components"""
        try:
            # Initialize keyword manager with full config for database adapter
            self.keyword_manager = KeywordManager(self.config)
            
            # Initialize document indexer
            self.document_indexer = DocumentIndexer(self.config)
            
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
            
            # Initialize LLM client
            llm_config = self.rag_config.get('llm', {})
            if llm_config.get('provider') == 'openai':
                self.llm_client = OpenAIClient(llm_config)
            else:
                raise ValueError(f"Unsupported LLM provider: {llm_config.get('provider')}")
            
            logger.info("All RAG components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            raise
    
    def get_available_keywords(self) -> List[Dict[str, Any]]:
        """
        Get available keywords from the papers database
        
        Returns:
            List of keyword dictionaries with counts and examples
        """
        try:
            return self.keyword_manager.get_available_keywords()
        except Exception as e:
            logger.error(f"Failed to get available keywords: {e}")
            return []
    
    def build_index_for_keywords(self, selected_keywords: List[str], 
                               force_reindex: bool = False) -> Dict[str, Any]:
        """
        Build vector index for papers matching selected keywords
        
        Args:
            selected_keywords: List of keywords to filter papers
            force_reindex: Whether to reindex existing documents
            
        Returns:
            Dictionary with indexing results
        """
        try:
            logger.info(f"Building index for keywords: {selected_keywords}")
            
            # Get papers matching keywords
            papers = self.keyword_manager.get_papers_by_keywords(selected_keywords)
            
            if not papers:
                return {
                    'success': False,
                    'error': f'No papers found for keywords: {selected_keywords}',
                    'papers_found': 0
                }
            
            logger.info(f"Found {len(papers)} papers for indexing")
            
            # Index the papers
            results = self.document_indexer.index_documents(
                papers, 
                batch_size=32, 
                force_reindex=force_reindex
            )
            
            results['papers_found'] = len(papers)
            results['selected_keywords'] = selected_keywords
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            return {
                'success': False,
                'error': str(e),
                'papers_found': 0
            }
    
    def ask_question(self, question: str, top_k: int = None, 
                    similarity_threshold: float = None) -> Dict[str, Any]:
        """
        Ask a question and get an AI-generated answer with sources
        
        Args:
            question: User's question
            top_k: Number of top similar chunks to retrieve
            similarity_threshold: Minimum similarity threshold for retrieval
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            logger.info(f"Processing question: {question[:100]}...")
            
            # Use config defaults if not specified
            retrieval_config = self.rag_config.get('retrieval', {})
            top_k = top_k or retrieval_config.get('top_k', 5)
            similarity_threshold = similarity_threshold or retrieval_config.get('similarity_threshold', 0.7)
            
            # Step 1: Retrieve relevant chunks
            retrieval_results = self._retrieve_relevant_chunks(
                question, top_k, similarity_threshold
            )
            
            if not retrieval_results['chunks']:
                return {
                    'success': False,
                    'answer': "I couldn't find relevant information in the indexed papers to answer your question.",
                    'sources': [],
                    'retrieval_info': retrieval_results
                }
            
            # Step 2: Check context length limits
            context_check = self.llm_client.check_context_limit(
                question, retrieval_results['chunks']
            )
            
            # Trim chunks if necessary
            if not context_check['within_limit']:
                max_chunks = context_check['suggested_max_chunks']
                retrieval_results['chunks'] = retrieval_results['chunks'][:max_chunks]
                logger.warning(f"Trimmed to {max_chunks} chunks due to context limit")
            
            # Step 3: Generate answer using LLM
            generation_results = self.llm_client.generate_answer(
                question, retrieval_results['chunks']
            )
            
            # Step 4: Combine results
            result = {
                'success': True,
                'question': question,
                'answer': generation_results['answer'],
                'sources': generation_results['sources'],
                'retrieval_info': {
                    'chunks_found': retrieval_results['total_chunks'],
                    'chunks_used': len(retrieval_results['chunks']),
                    'avg_similarity': retrieval_results['avg_similarity'],
                    'similarity_threshold': similarity_threshold
                },
                'generation_info': {
                    'model': generation_results['model'],
                    'tokens_used': generation_results.get('tokens_used', 0),
                    'context_length': generation_results.get('context_length', 0)
                }
            }
            
            logger.info(f"Successfully answered question using {len(retrieval_results['chunks'])} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {
                'success': False,
                'question': question,
                'answer': f"I apologize, but I encountered an error while processing your question: {str(e)}",
                'error': str(e),
                'sources': []
            }
    
    def _retrieve_relevant_chunks(self, question: str, top_k: int, 
                                similarity_threshold: float) -> Dict[str, Any]:
        """Retrieve relevant chunks from vector store"""
        try:
            # Search for relevant chunks
            search_results = self.vector_store.search_by_text(
                query_text=question,
                embedding_generator=self.embedding_generator,
                n_results=top_k
            )
            
            # Filter by similarity threshold
            filtered_chunks = [
                chunk for chunk in search_results 
                if chunk.get('similarity', 0) >= similarity_threshold
            ]
            
            # Calculate statistics
            similarities = [chunk.get('similarity', 0) for chunk in filtered_chunks]
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0
            
            return {
                'chunks': filtered_chunks,
                'total_chunks': len(search_results),
                'filtered_chunks': len(filtered_chunks),
                'avg_similarity': avg_similarity,
                'top_similarity': max(similarities) if similarities else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {e}")
            return {
                'chunks': [],
                'total_chunks': 0,
                'filtered_chunks': 0,
                'avg_similarity': 0,
                'top_similarity': 0
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            Dictionary with system status information
        """
        try:
            status = {
                'rag_engine': {'status': 'active'},
                'vector_store': {},
                'embedding_model': {},
                'llm_client': {},
                'keyword_stats': {}
            }
            
            # Vector store status
            try:
                vector_stats = self.vector_store.get_collection_stats()
                status['vector_store'] = {
                    'status': 'active',
                    'total_documents': vector_stats.get('total_documents', 0),
                    'unique_sources': vector_stats.get('unique_sources', 0),
                    'collection_name': vector_stats.get('collection_name', 'unknown')
                }
            except Exception as e:
                status['vector_store'] = {'status': 'error', 'error': str(e)}
            
            # Embedding model status
            try:
                embedding_info = self.embedding_generator.get_model_info()
                status['embedding_model'] = {
                    'status': 'active',
                    'model_name': embedding_info.get('model_name', 'unknown'),
                    'device': embedding_info.get('device', 'unknown'),
                    'embedding_dimension': embedding_info.get('embedding_dimension', 0)
                }
            except Exception as e:
                status['embedding_model'] = {'status': 'error', 'error': str(e)}
            
            # LLM client status
            try:
                api_valid = self.llm_client.validate_api_key()
                status['llm_client'] = {
                    'status': 'active' if api_valid else 'error',
                    'model': self.llm_client.model,
                    'api_key_valid': api_valid
                }
            except Exception as e:
                status['llm_client'] = {'status': 'error', 'error': str(e)}
            
            # Keyword statistics
            try:
                keyword_stats = self.keyword_manager.get_keyword_statistics()
                status['keyword_stats'] = {
                    'status': 'active',
                    **keyword_stats
                }
            except Exception as e:
                status['keyword_stats'] = {'status': 'error', 'error': str(e)}
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'rag_engine': {'status': 'error', 'error': str(e)}
            }
    
    def search_papers(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for papers similar to query (without generating answer)
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of similar paper chunks
        """
        try:
            search_results = self.vector_store.search_by_text(
                query_text=query,
                embedding_generator=self.embedding_generator,
                n_results=top_k
            )
            
            logger.info(f"Found {len(search_results)} results for search query")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search papers: {e}")
            return []
    
    def get_paper_summary(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of a specific paper by ArXiv ID
        
        Args:
            arxiv_id: ArXiv paper ID
            
        Returns:
            Paper summary or None if not found
        """
        try:
            # Search for chunks from this paper
            results = self.vector_store.collection.get(
                where={"source_doc": arxiv_id},
                include=['documents', 'metadatas'],
                limit=5  # Get first few chunks
            )
            
            if not results['ids']:
                return None
            
            # Extract paper info from first chunk metadata
            metadata = results['metadatas'][0]
            
            # Combine content from multiple chunks for summary
            content_parts = results['documents'][:3]  # Use first 3 chunks
            combined_content = "\\n\\n".join(content_parts)
            
            return {
                'arxiv_id': arxiv_id,
                'title': metadata.get('title', 'Unknown Title'),
                'authors': metadata.get('authors', 'Unknown Authors'),
                'abstract': metadata.get('abstract', ''),
                'categories': metadata.get('categories', ''),
                'published': metadata.get('published', ''),
                'pdf_path': metadata.get('pdf_path', ''),
                'sample_content': combined_content[:1000] + "..." if len(combined_content) > 1000 else combined_content,
                'total_chunks': len(results['ids'])
            }
            
        except Exception as e:
            logger.error(f"Failed to get paper summary for {arxiv_id}: {e}")
            return None