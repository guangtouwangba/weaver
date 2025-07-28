#!/usr/bin/env python3
"""
Debug script to test chat functionality without Streamlit
"""

import sys
import os
import logging

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import ResearchOrchestrator
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_orchestrator():
    """Test the orchestrator functionality"""
    print("🔬 Testing Research Orchestrator")
    print("=" * 50)
    
    try:
        # Check API keys
        print("Checking configuration...")
        Config.validate()
        print("✅ Configuration valid")
        
        # Initialize orchestrator
        print("Initializing orchestrator...")
        orchestrator = ResearchOrchestrator(
            openai_api_key=Config.OPENAI_API_KEY,
            db_path="./data/vector_db"
        )
        print("✅ Orchestrator initialized")
        
        # Test vector store
        print("Testing vector store...")
        stats = orchestrator.vector_store.get_collection_stats()
        print(f"✅ Vector store OK - {stats['unique_papers']} papers, {stats['total_chunks']} chunks")
        
        # Test search
        print("Testing vector search...")
        test_query = "machine learning"
        results = orchestrator.vector_store.search_papers(test_query, n_results=2)
        print(f"✅ Search OK - {len(results)} results for '{test_query}'")
        
        # Test chat function
        print("Testing chat function...")
        chat_response = orchestrator.chat_with_papers(
            query="What are transformers?",
            n_papers=3
        )
        print(f"✅ Chat OK - {len(chat_response.get('relevant_papers', []))} papers found")
        print(f"Response: {chat_response['response'][:200]}...")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test failure details:")
        return False

if __name__ == "__main__":
    success = test_orchestrator()
    sys.exit(0 if success else 1)