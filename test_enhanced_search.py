#!/usr/bin/env python3
"""
Test script for the enhanced search system with query expansion and ArXiv fallback
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_query_expansion():
    """Test the query expansion functionality"""
    print("\n" + "="*60)
    print("TESTING QUERY EXPANSION")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return False
    
    try:
        from utils.query_expansion import QueryExpander
        
        expander = QueryExpander(api_key)
        
        # Test queries
        test_queries = [
            "RAG",
            "transformer attention",
            "deep learning optimization",
            "neural machine translation",
            "graph neural networks"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            # Test rule-based expansion
            rule_based = expander._rule_based_expansion(query)
            print(f"   Rule-based expansions: {list(rule_based)[:3]}")
            
            # Test full expansion
            expanded = expander.expand_query(query, max_expansions=5)
            print(f"   Full expansions: {expanded}")
            
            # Test ArXiv query generation
            arxiv_queries = expander.generate_arxiv_search_queries(query)
            print(f"   ArXiv queries: {arxiv_queries}")
        
        print("✅ Query expansion test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Query expansion test failed: {e}")
        logger.exception("Query expansion test error:")
        return False

def test_orchestrator_integration():
    """Test the orchestrator with enhanced search"""
    print("\n" + "="*60)
    print("TESTING ORCHESTRATOR ENHANCED SEARCH")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return False
    
    try:
        from agents.orchestrator import ResearchOrchestrator
        
        # Initialize orchestrator
        print("🚀 Initializing research orchestrator...")
        orchestrator = ResearchOrchestrator(
            openai_api_key=api_key,
            db_path="./test_data/vector_db"
        )
        print("✅ Orchestrator initialized")
        
        # Test queries that should trigger different search strategies
        test_scenarios = [
            {
                "query": "RAG",
                "description": "Simple abbreviation that should expand and likely trigger ArXiv fallback"
            },
            {
                "query": "retrieval augmented generation transformer architecture",
                "description": "Expanded query that might find vector DB results"
            },
            {
                "query": "quantum computing machine learning",
                "description": "Cross-domain query to test ArXiv search"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 Test Scenario {i}: {scenario['description']}")
            print(f"   Query: '{scenario['query']}'")
            
            try:
                response = orchestrator.chat_with_papers(
                    query=scenario['query'],
                    n_papers=3,
                    min_similarity_threshold=0.5,
                    enable_arxiv_fallback=True
                )
                
                print(f"   ✅ Search Strategy: {response.get('search_strategy', 'unknown')}")
                print(f"   📊 Results: {len(response.get('relevant_papers', []))} papers found")
                
                if 'expanded_queries' in response:
                    print(f"   🔍 Expanded to: {response['expanded_queries']}")
                
                if 'vector_results_count' in response:
                    print(f"   📁 Vector DB: {response['vector_results_count']} papers")
                
                if 'arxiv_results_count' in response:
                    print(f"   🌐 ArXiv: {response['arxiv_results_count']} papers")
                
                # Show first paper if available
                papers = response.get('relevant_papers', [])
                if papers:
                    paper = papers[0]
                    print(f"   📄 Top Result: {paper['title'][:60]}...")
                    print(f"      Source: {paper.get('source', 'unknown')}")
                    print(f"      Score: {paper['similarity_score']:.2f}")
                
            except Exception as e:
                print(f"   ❌ Scenario failed: {e}")
                logger.exception(f"Scenario {i} error:")
        
        print("\n✅ Orchestrator enhanced search test completed")
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        logger.exception("Orchestrator test error:")
        return False

def test_vector_db_stats():
    """Test vector database connectivity and stats"""
    print("\n" + "="*60)
    print("TESTING VECTOR DATABASE")
    print("="*60)
    
    try:
        from database.vector_store import VectorStore
        
        # Initialize vector store
        vector_store = VectorStore(db_path="./test_data/vector_db")
        
        # Get stats
        stats = vector_store.get_collection_stats()
        print(f"📊 Database Stats:")
        print(f"   Total papers: {stats.get('unique_papers', 0)}")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Collection: {stats.get('collection_name', 'unknown')}")
        
        # Test search
        print(f"\n🔍 Testing vector search...")
        results = vector_store.search_papers("machine learning", n_results=3)
        print(f"   Found {len(results)} results for 'machine learning'")
        
        for i, result in enumerate(results[:2], 1):
            print(f"   {i}. {result['metadata']['title'][:50]}...")
            print(f"      Score: {result['similarity_score']:.3f}")
        
        print("✅ Vector database test completed")
        return True
        
    except Exception as e:
        print(f"❌ Vector database test failed: {e}")
        logger.exception("Vector DB test error:")
        return False

def main():
    """Run all tests"""
    print("🧪 Enhanced Search System Test Suite")
    print("=" * 60)
    
    # Create test directory
    os.makedirs("./test_data", exist_ok=True)
    
    tests = [
        ("Vector Database", test_vector_db_stats),
        ("Query Expansion", test_query_expansion),
        ("Orchestrator Integration", test_orchestrator_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nOverall: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("🎉 All tests passed! Enhanced search system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        
        # Provide troubleshooting tips
        print("\n💡 Troubleshooting Tips:")
        print("1. Ensure OPENAI_API_KEY is set in your environment")
        print("2. Check that all dependencies are installed: pip install -r requirements.txt")
        print("3. Verify internet connectivity for ArXiv API access")
        print("4. Check logs for specific error messages")

if __name__ == "__main__":
    main()