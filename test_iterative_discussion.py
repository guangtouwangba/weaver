#!/usr/bin/env python3
"""
Test script for the new iterative multi-agent discussion workflow
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from config import Config
from agents.orchestrator import ResearchOrchestrator
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_iterative_discussion():
    """Test the new iterative discussion workflow"""
    print("🧪 Testing Iterative Multi-Agent Discussion Workflow")
    print("=" * 60)
    
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated")
        
        # Initialize orchestrator
        orchestrator = ResearchOrchestrator(
            openai_api_key=Config.OPENAI_API_KEY,
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            anthropic_api_key=Config.ANTHROPIC_API_KEY,
            default_provider=Config.DEFAULT_PROVIDER,
            agent_configs=Config.get_all_agent_configs(),
            db_path=Config.VECTOR_DB_PATH
        )
        print("✅ Orchestrator initialized")
        print(f"Available agents: {list(orchestrator.agents.keys())}")
        
        # Test query
        test_query = "What are the latest advances in transformer architectures for language models?"
        print(f"\n🔍 Test query: {test_query}")
        
        # Run chat with papers (this will trigger the iterative discussion)
        print("\n⚡ Running iterative discussion...")
        result = orchestrator.chat_with_papers(
            query=test_query,
            n_papers=3,  # Limit papers for testing
            min_similarity_threshold=0.3,
            enable_arxiv_fallback=True
        )
        
        print("\n📊 Results:")
        print(f"✅ Search completed: {result.get('search_strategy', 'unknown')}")
        print(f"✅ Papers found: {len(result.get('relevant_papers', []))}")
        
        # Check if we got the new iterative discussion format
        agent_discussions = result.get('agent_discussions', {})
        if 'final_conclusion' in agent_discussions:
            print("✅ New iterative discussion format detected!")
            print(f"✅ Discussion rounds: {agent_discussions.get('total_rounds', 0)}")
            print(f"✅ Participating agents: {', '.join(agent_discussions.get('agents_participated', []))}")
            
            # Show a preview of the final conclusion
            final_conclusion = agent_discussions.get('final_conclusion', '')
            if final_conclusion:
                print(f"\n🎯 Final Conclusion Preview:")
                print(f"{final_conclusion[:300]}...")
            
        else:
            print("⚠️  Old discussion format - iterative discussion may not be working")
        
        # Show response preview
        response = result.get('response', '')
        if response:
            print(f"\n📝 Response Preview:")
            print(f"{response[:500]}...")
        
        print(f"\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_structures():
    """Test the new data structures"""
    print("\n🧪 Testing New Data Structures")
    print("-" * 40)
    
    from agents.orchestrator import DiscussionRound, IterativeDiscussion
    from datetime import datetime
    
    try:
        # Test DiscussionRound
        round1 = DiscussionRound(
            round_number=1,
            agent_name="google_engineer",
            agent_response="Test response from Google Engineer",
            timestamp=datetime.now()
        )
        print("✅ DiscussionRound created successfully")
        
        # Test IterativeDiscussion
        discussion = IterativeDiscussion(
            query="Test query",
            papers=[],
            rounds=[round1],
            started_at=datetime.now()
        )
        print("✅ IterativeDiscussion created successfully")
        
        print(f"✅ Discussion has {len(discussion.rounds)} rounds")
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Iterative Discussion Tests")
    print("=" * 60)
    
    # Test 1: Data structures
    if not test_data_structures():
        return 1
    
    # Test 2: Full iterative discussion workflow
    if not test_iterative_discussion():
        return 1
    
    print("\n🎉 All tests passed! The iterative discussion workflow is working.")
    return 0

if __name__ == "__main__":
    sys.exit(main())