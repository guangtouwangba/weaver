"""
RAG system main program
Demonstrates the complete process of basic RAG functionality
"""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

# Import base interfaces
from rag.document_repository.base import DocumentRepository
from rag.file_loader.base import FileLoader
from rag.document_spliter.base import DocumentSplitter
from rag.vector_store.base import VectorStore
from rag.retriever.base import Retriever
from rag.knowledge_store.base import KnowledgeStore

# Router functionality has been integrated into Retriever
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.semantic import SemanticRetriever
from rag.retriever.processors import QueryProcessor, ResultProcessor


class RAGSystem:
    """RAG system main class"""
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize RAG system
        
        Args:
            config: RAG configuration
        """
        self.config = config or RAGConfig()
        
        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            raise ValueError(f"Configuration errors: {'; '.join(config_errors)}")
        
        # Initialize components
        self.file_loaders = self._initialize_file_loaders()
        self.document_splitter = self._initialize_document_splitter()
        self.vector_store = self._initialize_vector_store()
        self.document_repository = self._initialize_document_repository()
        self.retriever = self._initialize_retriever()
        
        print(f"✅ RAG system initialized")
        print(f"   - Supported file types: {self.config.supported_file_types}")
        print(f"   - Chunk size: {self.config.chunk_size}")
        print(f"   - Chunk overlap: {self.config.chunk_overlap}")
        print(f"   - Top-K: {self.config.top_k}")
    
    def _initialize_file_loaders(self) -> dict:
        """Initialize file loaders"""
        loaders = {
            'text': TextFileLoader(),
            'markdown': MarkdownLoader()
        }
        return loaders
    
    def _initialize_document_splitter(self) -> BaseDocumentSplitter:
        """Initialize document splitter"""
        return SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
    
    def _initialize_vector_store(self) -> BaseVectorStore:
        """Initialize vector store"""
        return InMemoryVectorStore(self.config.vector_store_config.__dict__)
    
    def _initialize_document_repository(self) -> BaseDocumentRepository:
        """Initialize document repository"""
        return InMemoryDocumentRepository()
    
    def _initialize_retriever(self) -> BaseRetriever:
        """Initialize retriever"""
        retriever_config = {
            'top_k': self.config.top_k,
            'similarity_threshold': self.config.similarity_threshold,
            'enable_reranking': self.config.enable_reranking
        }
        
        return SemanticRetriever(
            vector_store=self.vector_store,
            document_repository=self.document_repository,
            config=retriever_config
        )
    
    
    def _get_appropriate_loader(self, file_path: str) -> BaseFileLoader:
        """Select appropriate loader based on file type"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.md', '.markdown']:
            return self.file_loaders['markdown']
        elif file_ext in ['.txt', '.text']:
            return self.file_loaders['text']
        else:
            # Default to text loader
            return self.file_loaders['text']
    
    async def process_document(self, file_path: str) -> str:
        """
        Process the complete workflow for a single document
        
        Args:
            file_path: File path
            
        Returns:
            str: Document ID
        """
        start_time = time.time()
        
        try:
            print(f"\n📄 Starting document processing: {file_path}")
            
            # 1. Select appropriate file loader
            loader = self._get_appropriate_loader(file_path)
            
            # 2. Load document
            print("   🔄 Loading document...")
            document = await loader.load(file_path)
            print(f"   ✅ Document loaded: {document.title}")
            print(f"      - File size: {document.file_size} bytes")
            print(f"      - Character count: {len(document.content)}")
            print(f"      - Status: {document.status.value}")
            
            # 3. Store document metadata
            print("   🔄 Storing document metadata...")
            doc_id = await self.document_repository.save(document)
            
            # 4. Split document
            print("   🔄 Splitting document...")
            chunks = await self.document_splitter.split(document)
            print(f"   ✅ Document split: {len(chunks)} chunks")
            
            if chunks:
                avg_chunk_size = sum(len(chunk.content) for chunk in chunks) / len(chunks)
                print(f"      - Average chunk size: {avg_chunk_size:.0f} characters")
            
            # 5. Store vectors (simplified, actual embedding vectors need to be generated)
            print("   🔄 Storing vectors...")
            # Generate simple placeholder vectors for each chunk (actual embedding model is needed)
            for chunk in chunks:
                chunk.embedding = [0.1] * 768  # Simple placeholder vector
            
            vector_ids = await self.vector_store.store_chunks(chunks)
            print(f"   ✅ Vector storage completed: {len(vector_ids)} vectors")
            
            # 6. Update document status
            await self.document_repository.update_status(doc_id, DocumentStatus.COMPLETED)
            
            processing_time = (time.time() - start_time) * 1000
            print(f"   ⏱️  Processing completed, time: {processing_time:.2f}ms")
            
            return doc_id
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            print(f"   ❌ Processing failed: {str(e)}")
            print(f"   ⏱️  Failed time: {processing_time:.2f}ms")
            
            # Update document status to error
            if 'document' in locals():
                await self.document_repository.update_status(document.id, DocumentStatus.ERROR)
            
            raise
    
    async def query(self, question: str) -> dict:
        """
        Execute query
        
        Args:
            question: Query question
            
        Returns:
            dict: Query result
        """
        start_time = time.time()
        
        try:
            print(f"\n🔍 Executing query: {question}")
            
            # 1. Execute intelligent retrieval (includes built-in routing decision)
            print("   🔄 Executing retrieval...")
            result = await self.retriever.retrieve(question, top_k=self.config.top_k)
            
            query_time = (time.time() - start_time) * 1000
            
            print(f"   ✅ Retrieval completed: Found {len(result.chunks)} relevant chunks")
            print(f"   🎯 Using strategy: {result.metadata.get('strategy', 'unknown')}")
            print(f"   ⏱️  Query time: {query_time:.2f}ms")
            
            # 2. Format result
            formatted_result = {
                'query': question,
                'answer_chunks': [],
                'total_found': len(result.chunks),
                'query_time_ms': query_time,
                'strategy_used': result.metadata.get('strategy', 'unknown'),
                'preprocessing': result.metadata.get('pre_processing', {}),
                'postprocessing': result.metadata.get('post_processing', {})
            }
            
            for i, (chunk, score) in enumerate(zip(result.chunks, result.relevance_scores)):
                formatted_result['answer_chunks'].append({
                    'rank': i + 1,
                    'content': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    'score': score,
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index
                })
            
            return formatted_result
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            print(f"   ❌ Query failed: {str(e)}")
            print(f"   ⏱️  Failed time: {query_time:.2f}ms")
            
            return {
                'query': question,
                'error': str(e),
                'query_time_ms': query_time
            }
    
    async def get_system_status(self) -> dict:
        """Get system status"""
        # Get status of each component
        vector_store_info = await self.vector_store.get_collection_info()
        document_repository_stats = await self.document_repository.get_statistics()
        
        return {
            'vector_store': vector_store_info,
            'document_repository': document_repository_stats,
            'config': {
                'chunk_size': self.config.chunk_size,
                'chunk_overlap': self.config.chunk_overlap,
                'top_k': self.config.top_k,
                'similarity_threshold': self.config.similarity_threshold
            }
        }


async def main():
    """Main program demonstration"""
    print("🚀 Starting RAG system demonstration")
    
    # Create RAG system
    config = RAGConfig(
        chunk_size=500,
        chunk_overlap=50,
        top_k=3,
        similarity_threshold=0.1  # Set a lower threshold for demonstration
    )
    
    rag_system = RAGSystem(config)
    
    # Create example document files
    test_files = []
    
    # Create test document 1
    test_file1 = "test_document1.txt"
    with open(test_file1, 'w', encoding='utf-8') as f:
        f.write("""
Artificial Intelligence Basics

Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of performing tasks that typically require human intelligence.
These tasks include learning, reasoning, problem-solving, perception, and language understanding.

Machine learning is an important subfield of AI, enabling computers to learn and improve without explicit programming.
Deep learning is a special form of machine learning that uses artificial neural networks to simulate the way the human brain works.

Natural Language Processing (NLP) is another important branch of AI, focusing on enabling computers to understand, interpret, and generate human language.
""")
    test_files.append(test_file1)
    
    # Create test document 2
    test_file2 = "test_document2.md"
    with open(test_file2, 'w', encoding='utf-8') as f:
        f.write("""
# RAG System Introduction

## What is RAG?

RAG (Retrieval-Augmented Generation) is an artificial intelligence method that combines retrieval and generation.
It first retrieves relevant information from a large knowledge base and then uses this information to generate an answer.

## RAG Advantages

- **Accuracy**: Generates answers based on factual information
- **Interpretability**: Information sources can be traced back
- **Timeliness**: Can obtain the latest information
- **Cost-effectiveness**: More economical than training large models

## Application Scenarios

RAG systems are widely used in:
1. Intelligent Question Answering Systems
2. Document Query and Analysis
3. Knowledge Management Systems
4. Customer Service Robots
""")
    test_files.append(test_file2)
    
    try:
        # Process documents
        for file_path in test_files:
            doc_id = await rag_system.process_document(file_path)
            print(f"📋 Document ID: {doc_id}")
        
        # Query demonstration
        queries = [
            "What is artificial intelligence?",
            "What are the advantages of RAG?",
            "What is the relationship between machine learning and deep learning?",
            "What are the application scenarios of RAG systems?"
        ]
        
        for query in queries:
            result = await rag_system.query(query)
            
            print("\n" + "="*60)
            print(f"❓ Question: {result['query']}")
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"📊 Found {result['total_found']} relevant results")
                print(f"🎯 Using strategy: {result['strategy_used']}")
                
                # Display preprocessing information
                if result['preprocessing']:
                    preprocessing = result['preprocessing']
                    if 'query_type' in preprocessing:
                        print(f"🧠 Query type: {preprocessing['query_type']}")
                
                # Display post-processing information
                if result['postprocessing']:
                    postprocessing = result['postprocessing']
                    if 'reranked' in postprocessing:
                        print(f"🔄 Reranking: {'Yes' if postprocessing['reranked'] else 'No'}")
                    if 'total_compressed' in postprocessing and postprocessing['total_compressed'] > 0:
                        print(f"📦 Compressed {postprocessing['total_compressed']} results")
                
                for chunk_info in result['answer_chunks']:
                    print(f"\n📄 Result {chunk_info['rank']} (Relevance: {chunk_info['score']:.3f}):")
                    print(f"   {chunk_info['content']}")
        
        # Display system status
        print("\n" + "="*60)
        print("📈 System Status:")
        status = await rag_system.get_system_status()
        
        print(f"    Vector store: {status['vector_store']['total_chunks']} chunks")
        print(f"    Document count: {status['document_repository']['total_documents']} documents")
        print(f"    Config info: Chunk size={status['config']['chunk_size']}, Top-K={status['config']['top_k']}")
        
    finally:
        # Clean up test files
        for file_path in test_files:
            try:
                Path(file_path).unlink()
                print(f"🗑️  Deleted test file: {file_path}")
            except:
                pass
    
    print("\n✅ RAG system demonstration completed!")


if __name__ == "__main__":
    asyncio.run(main())