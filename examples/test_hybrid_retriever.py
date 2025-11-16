#!/usr/bin/env python3
"""
Example script demonstrating HybridRetriever usage.

This script shows how to:
1. Create a vector store with sample documents
2. Initialize VectorRetriever and HybridRetriever
3. Compare their retrieval results
4. Demonstrate the benefits of hybrid search

Usage:
    python examples/test_hybrid_retriever.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

from rag_core.retrievers import VectorRetriever, HybridRetriever, RetrieverFactory


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
]


def create_sample_vector_store():
    """Create a FAISS vector store with sample documents."""
    print("📚 Creating sample vector store...")
    
    # Use fake embeddings for testing (replace with real embeddings in production)
    embeddings = FakeEmbeddings(size=768)
    
    # Extract texts and metadatas
    texts = [doc["content"] for doc in SAMPLE_DOCUMENTS]
    metadatas = [doc["metadata"] for doc in SAMPLE_DOCUMENTS]
    
    # Create vector store
    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )
    
    print(f"✅ Vector store created with {len(SAMPLE_DOCUMENTS)} documents\n")
    return vector_store


async def test_vector_retriever(vector_store, query: str, top_k: int = 3):
    """Test VectorRetriever."""
    print(f"🔍 VectorRetriever (Semantic Search Only)")
    print(f"   Query: '{query}'")
    print(f"   Top-{top_k} results:\n")
    
    retriever = VectorRetriever(
        vector_store=vector_store,
        top_k=top_k,
        search_type="similarity"
    )
    
    results = await retriever.retrieve(query, top_k=top_k)
    
    for i, doc in enumerate(results, 1):
        print(f"   {i}. [Score: {doc.score:.4f}]")
        print(f"      {doc.page_content[:80]}...")
        print(f"      Source: {doc.metadata.get('source', 'unknown')}")
        print()
    
    return results


async def test_hybrid_retriever(vector_store, query: str, top_k: int = 3):
    """Test HybridRetriever."""
    print(f"🎯 HybridRetriever (BM25 + Semantic Search)")
    print(f"   Query: '{query}'")
    print(f"   Top-{top_k} results:\n")
    
    retriever = HybridRetriever(
        vector_store=vector_store,
        vector_weight=0.7,
        bm25_weight=0.3,
        top_k=top_k,
        rrf_k=60
    )
    
    results = await retriever.retrieve(query, top_k=top_k)
    
    for i, doc in enumerate(results, 1):
        print(f"   {i}. [RRF Score: {doc.score:.4f}]")
        print(f"      {doc.page_content[:80]}...")
        print(f"      Source: {doc.metadata.get('source', 'unknown')}")
        print()
    
    # Show config
    config = retriever.get_config()
    print(f"   Config: {config}\n")
    
    return results


async def test_factory(vector_store, query: str):
    """Test RetrieverFactory."""
    print(f"🏭 Using RetrieverFactory")
    print(f"   Query: '{query}'\n")
    
    # Create hybrid retriever via factory
    retriever = RetrieverFactory.create(
        retriever_type="hybrid",
        config={
            "top_k": 3,
            "vector_weight": 0.6,
            "bm25_weight": 0.4,
            "rrf_k": 60,
        },
        vector_store=vector_store
    )
    
    results = await retriever.retrieve(query)
    
    print(f"   Retrieved {len(results)} documents:")
    for i, doc in enumerate(results, 1):
        print(f"   {i}. {doc.metadata.get('source', 'unknown')}")
    print()


async def compare_retrievers(vector_store):
    """Compare VectorRetriever and HybridRetriever side by side."""
    print("\n" + "=" * 80)
    print("🆚 COMPARISON: Vector vs Hybrid Retrieval")
    print("=" * 80 + "\n")
    
    # Test queries that benefit from keyword matching
    test_queries = [
        "What is BM25?",  # Exact term match - hybrid should do better
        "neural networks deep learning",  # Semantic similarity - both should work
        "RAG retrieval augmented generation",  # Combination - hybrid should excel
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"Query: '{query}'")
        print(f"{'=' * 80}\n")
        
        # Vector retriever
        vector_results = await test_vector_retriever(vector_store, query, top_k=3)
        
        print("-" * 80 + "\n")
        
        # Hybrid retriever
        hybrid_results = await test_hybrid_retriever(vector_store, query, top_k=3)
        
        # Comparison
        print(f"📊 Comparison:")
        vector_sources = [doc.metadata['source'] for doc in vector_results]
        hybrid_sources = [doc.metadata['source'] for doc in hybrid_results]
        
        print(f"   Vector:  {vector_sources}")
        print(f"   Hybrid:  {hybrid_sources}")
        
        if vector_sources != hybrid_sources:
            print(f"   ⚠️  Different results! Hybrid retrieval found different relevant documents.")
        else:
            print(f"   ✅ Same results (both methods agree)")
        print()


async def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("🧪 Hybrid Retriever Test Script")
    print("=" * 80 + "\n")
    
    # Create sample vector store
    vector_store = create_sample_vector_store()
    
    # Test 1: Basic usage
    print("=" * 80)
    print("TEST 1: Basic Retrieval")
    print("=" * 80 + "\n")
    
    query = "machine learning algorithms"
    await test_vector_retriever(vector_store, query, top_k=3)
    print("-" * 80 + "\n")
    await test_hybrid_retriever(vector_store, query, top_k=3)
    
    # Test 2: Factory pattern
    print("=" * 80)
    print("TEST 2: Factory Pattern")
    print("=" * 80 + "\n")
    
    await test_factory(vector_store, "neural networks")
    
    # Test 3: Comparison
    await compare_retrievers(vector_store)
    
    print("=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
    print("\n💡 Key Takeaways:")
    print("   1. HybridRetriever combines BM25 (keyword) and vector (semantic) search")
    print("   2. It uses Reciprocal Rank Fusion (RRF) to merge results")
    print("   3. Better for queries with specific terms or technical jargon")
    print("   4. Configurable weights allow tuning for your use case")
    print("\n🚀 To use in production:")
    print("   1. Set RETRIEVER_TYPE=hybrid in your .env file")
    print("   2. Adjust RETRIEVER_VECTOR_WEIGHT and RETRIEVER_BM25_WEIGHT")
    print("   3. Install rank-bm25: pip install rank-bm25")
    print()


if __name__ == "__main__":
    asyncio.run(main())

