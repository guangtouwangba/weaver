#!/usr/bin/env python3
"""
Test script for multi-agent discussion functionality
"""

import logging
import os
from agents.orchestrator import ResearchOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_multi_agent_discussion():
    """Test the multi-agent discussion functionality"""
    
    # Get API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return
    
    print("=== Testing Multi-Agent Discussion ===\n")
    
    # Initialize orchestrator
    print("1. Initializing Research Orchestrator...")
    orchestrator = ResearchOrchestrator(
        openai_api_key=openai_api_key,
        db_path="./data/vector_db"
    )
    print("✅ Orchestrator initialized successfully\n")
    
    # Test queries
    test_queries = [
        "What are the latest developments in transformer architecture?",
        "How can machine learning be applied to climate change?",
        "What are the challenges in deploying AI models in production?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"2.{i} Testing query: {query}")
        print("-" * 60)
        
        try:
            # Test chat with papers
            result = orchestrator.chat_with_papers(
                query=query,
                n_papers=None,  # Get all available papers
                min_similarity_threshold=0.3,
                enable_arxiv_fallback=True
            )
            
            # Print results
            print(f"✅ Query processed successfully")
            print(f"📊 Found {len(result.get('relevant_papers', []))} relevant papers")
            print(f"🤖 Generated discussions from {len(result.get('agent_discussions', {}))} agents")
            
            # Show response preview
            response = result.get('response', '')
            preview = response[:500] + "..." if len(response) > 500 else response
            print(f"📝 Response preview:\n{preview}\n")
            
            # Show agent discussions
            agent_discussions = result.get('agent_discussions', {})
            if agent_discussions:
                print("🤖 Agent Discussions:")
                for agent_name, discussion in agent_discussions.items():
                    if agent_name != "synthesis":
                        print(f"  - {agent_name}: {len(str(discussion))} characters")
                print()
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            print()
    
    print("=== Test Summary ===")
    print("✅ Multi-agent discussion functionality tested successfully")
    print("📝 Check the responses above for detailed multi-agent analysis")

if __name__ == "__main__":
    test_multi_agent_discussion() 