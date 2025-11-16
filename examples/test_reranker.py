#!/usr/bin/env python3
"""
Example script demonstrating Cross-Encoder Reranker usage.

This script shows how to:
1. Retrieve documents using HybridRetriever
2. Rerank results using CrossEncoderReranker
3. Compare results before and after reranking
4. Demonstrate the complete retrieval + reranking pipeline

Usage:
    python examples/test_reranker.py
"""

# Fix OpenMP conflict on macOS (must be before any imports)
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

from rag_core.retrievers import HybridRetriever
from rag_core.rerankers import CrossEncoderReranker, RerankerFactory


# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
        "metadata": {"source": "ml_basics.txt", "topic": "machine_learning"}
    },
    {
        "content": "Deep learning uses neural networks with multiple layers to process complex patterns in data.",
        "metadata": {"source": "deep_learning.txt", "topic": "machine_learning"}
    },
    {
        "content": "Natural Language Processing (NLP) enables computers to understand and generate human language.",
        "metadata": {"source": "nlp_intro.txt", "topic": "nlp"}
    },
    {
        "content": "The transformer architecture revolutionized NLP with its attention mechanism.",
        "metadata": {"source": "transformers.txt", "topic": "nlp"}
    },
    {
        "content": "Python is a popular programming language for data science and machine learning.",
        "metadata": {"source": "python_intro.txt", "topic": "programming"}
    },
    {
        "content": "RAG (Retrieval-Augmented Generation) combines information retrieval with language generation.",
        "metadata": {"source": "rag_explained.txt", "topic": "rag"}
    },
    {
        "content": "Vector databases enable semantic search by storing and querying embeddings.",
        "metadata": {"source": "vector_db.txt", "topic": "databases"}
    },
    {
        "content": "BM25 is a probabilistic retrieval function that ranks documents based on query term frequency.",
        "metadata": {"source": "bm25_explained.txt", "topic": "information_retrieval"}
    },
    {
        "content": "Cross-encoders are BERT-based models that jointly encode query and document for relevance scoring.",
        "metadata": {"source": "cross_encoder_explained.txt", "topic": "information_retrieval"}
    },
    {
        "content": "Gradient descent is an optimization algorithm used to train machine learning models.",
        "metadata": {"source": "gradient_descent.txt", "topic": "machine_learning"}
    },
]


def create_sample_vector_store():
    """Create a FAISS vector store with sample documents."""
    print("📚 Creating sample vector store...")
    
    # Use fake embeddings for testing
    embeddings = FakeEmbeddings(size=768)
    
    texts = [doc["content"] for doc in SAMPLE_DOCUMENTS]
    metadatas = [doc["metadata"] for doc in SAMPLE_DOCUMENTS]
    
    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )
    
    print(f"✅ Vector store created with {len(SAMPLE_DOCUMENTS)} documents\n")
    return vector_store


async def test_basic_reranker():
    """Test basic reranker functionality."""
    print("=" * 80)
    print("TEST 1: Basic Cross-Encoder Reranker")
    print("=" * 80 + "\n")
    
    # Create vector store
    vector_store = create_sample_vector_store()
    
    # Query
    query = "How do neural networks learn?"
    
    # Step 1: Retrieve with HybridRetriever
    print(f"🔍 Step 1: Retrieving documents for '{query}'")
    print(f"   Using HybridRetriever (top-8)...\n")
    
    retriever = HybridRetriever(
        vector_store=vector_store,
        vector_weight=0.7,
        bm25_weight=0.3,
        top_k=8
    )
    
    retrieved_docs = await retriever.retrieve(query, top_k=8)
    
    print("   Retrieved documents (before reranking):")
    for i, doc in enumerate(retrieved_docs, 1):
        print(f"   {i}. [{doc.score:.4f}] {doc.metadata['source']}")
        print(f"      {doc.page_content[:70]}...")
    print()
    
    # Step 2: Rerank with CrossEncoder
    print(f"🎯 Step 2: Reranking with Cross-Encoder")
    print(f"   Model: cross-encoder/ms-marco-MiniLM-L-6-v2\n")
    
    reranker = CrossEncoderReranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=5
    )
    
    reranked_docs = await reranker.rerank(query, retrieved_docs, top_n=5)
    
    print("   Reranked documents (after reranking):")
    for i, doc in enumerate(reranked_docs, 1):
        print(f"   {i}. [{doc.score:.4f}] {doc.metadata['source']}")
        print(f"      {doc.page_content[:70]}...")
        print(f"      Original score: {doc.metadata['original_score']:.4f}, "
              f"Rerank score: {doc.metadata['rerank_score']:.4f}")
    print()
    
    # Show reranker config
    config = reranker.get_config()
    print(f"📊 Reranker Config: {config}\n")


async def test_comparison():
    """Compare retrieval with and without reranking."""
    print("=" * 80)
    print("TEST 2: Comparison - With vs Without Reranking")
    print("=" * 80 + "\n")
    
    vector_store = create_sample_vector_store()
    
    test_queries = [
        "What is deep learning?",
        "How do transformers work in NLP?",
        "Explain cross-encoder models",
    ]
    
    retriever = HybridRetriever(
        vector_store=vector_store,
        vector_weight=0.7,
        bm25_weight=0.3,
        top_k=10
    )
    
    reranker = CrossEncoderReranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=3
    )
    
    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 80)
        
        # Retrieve
        retrieved = await retriever.retrieve(query, top_k=10)
        
        # Rerank
        reranked = await reranker.rerank(query, retrieved, top_n=3)
        
        # Show top-3 from each
        print("   Without Reranking (top-3):")
        for i, doc in enumerate(retrieved[:3], 1):
            print(f"      {i}. {doc.metadata['source']}")
        
        print("\n   With Reranking (top-3):")
        for i, doc in enumerate(reranked, 1):
            print(f"      {i}. {doc.metadata['source']} "
                  f"(rerank_score: {doc.metadata['rerank_score']:.2f})")
        
        print()


async def test_factory():
    """Test RerankerFactory."""
    print("=" * 80)
    print("TEST 3: Using RerankerFactory")
    print("=" * 80 + "\n")
    
    print("Creating reranker via factory...\n")
    
    # Create via factory
    reranker = await RerankerFactory.create(
        reranker_type="cross_encoder",
        config={
            "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "top_n": 3,
            "batch_size": 16,
        }
    )
    
    print(f"✅ Reranker created: {reranker}")
    print(f"   Config: {reranker.get_config()}\n")
    
    # Create sample docs
    from rag_core.core.models import Document
    
    docs = [
        Document(
            page_content="Python is great for machine learning and data science.",
            metadata={"source": "doc1"},
            score=0.5
        ),
        Document(
            page_content="JavaScript is a popular web programming language.",
            metadata={"source": "doc2"},
            score=0.6
        ),
        Document(
            page_content="Machine learning uses algorithms to learn from data automatically.",
            metadata={"source": "doc3"},
            score=0.7
        ),
    ]
    
    query = "What is machine learning?"
    
    print(f"Query: '{query}'")
    print("Documents:")
    for doc in docs:
        print(f"   - [{doc.score:.2f}] {doc.metadata['source']}")
    print()
    
    # Rerank
    reranked = await reranker.rerank(query, docs, top_n=2)
    
    print("After reranking (top-2):")
    for i, doc in enumerate(reranked, 1):
        print(f"   {i}. [{doc.score:.4f}] {doc.metadata['source']}")
        print(f"      {doc.page_content[:60]}...")
    print()


async def test_complete_pipeline():
    """Test complete retrieval + reranking pipeline."""
    print("=" * 80)
    print("TEST 4: Complete Pipeline (Hybrid + Reranker)")
    print("=" * 80 + "\n")
    
    print("This simulates the recommended production setup:")
    print("   1. HybridRetriever (召回 top-20)")
    print("   2. CrossEncoderReranker (精排 top-5)")
    print()
    
    vector_store = create_sample_vector_store()
    query = "neural networks and deep learning"
    
    # Pipeline
    print(f"📝 Query: '{query}'\n")
    
    # Stage 1: Retrieval
    print("Stage 1️⃣: Retrieval (Hybrid: BM25 + Vector)")
    retriever = HybridRetriever(
        vector_store=vector_store,
        vector_weight=0.7,
        bm25_weight=0.3,
        top_k=20  # Retrieve more candidates
    )
    
    candidates = await retriever.retrieve(query, top_k=20)
    print(f"   Retrieved {len(candidates)} candidates")
    print(f"   Top-5:")
    for i, doc in enumerate(candidates[:5], 1):
        print(f"      {i}. {doc.metadata['source']}")
    print()
    
    # Stage 2: Reranking
    print("Stage 2️⃣: Reranking (Cross-Encoder)")
    reranker = CrossEncoderReranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=5  # Final top-5
    )
    
    final_results = await reranker.rerank(query, candidates, top_n=5)
    print(f"   Reranked to top-{len(final_results)}")
    print()
    
    print("🏆 Final Results:")
    for i, doc in enumerate(final_results, 1):
        print(f"   {i}. [{doc.score:.4f}] {doc.metadata['source']}")
        print(f"      {doc.page_content[:70]}...")
        print(f"      Original: {doc.metadata['original_score']:.4f}, "
              f"Rerank: {doc.metadata['rerank_score']:.4f}")
        print()


async def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("🧪 Cross-Encoder Reranker Test Script")
    print("=" * 80 + "\n")
    
    try:
        # Test 1: Basic functionality
        await test_basic_reranker()
        
        # Test 2: Comparison
        await test_comparison()
        
        # Test 3: Factory
        await test_factory()
        
        # Test 4: Complete pipeline
        await test_complete_pipeline()
        
        print("=" * 80)
        print("✅ All tests completed!")
        print("=" * 80)
        print("\n💡 Key Takeaways:")
        print("   1. Cross-Encoder reranking improves retrieval accuracy")
        print("   2. Recommended pipeline: Retrieval (top-20) → Reranking (top-5)")
        print("   3. Cross-Encoders are slower but more accurate than bi-encoders")
        print("   4. Best used as the final ranking stage after initial retrieval")
        print("\n🚀 To use in production:")
        print("   1. Set RERANKER_ENABLED=true in .env")
        print("   2. Choose RERANKER_TYPE=cross_encoder")
        print("   3. Set RERANKER_TOP_N to desired final count")
        print("   4. Increase VECTOR_TOP_K for more candidates")
        print("   5. Install: pip install sentence-transformers")
        print()
        
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Please install required dependencies:")
        print("   pip install sentence-transformers")
        print()


if __name__ == "__main__":
    asyncio.run(main())

