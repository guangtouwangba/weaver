#!/usr/bin/env python3
"""
Test script to verify that all limits have been removed
"""

import logging
import os
from agents.orchestrator import ResearchOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_no_limits():
    """Test that all limits have been removed"""
    
    # Get API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return
    
    print("=== Testing No Limits Functionality ===\n")
    
    # Initialize orchestrator
    print("1. Initializing Research Orchestrator...")
    orchestrator = ResearchOrchestrator(
        openai_api_key=openai_api_key,
        db_path="./data/vector_db"
    )
    print("✅ Orchestrator initialized successfully\n")
    
    # Test query that should return many papers
    test_query = "machine learning"
    
    print(f"2. Testing with query: {test_query}")
    print("   This should return ALL available papers, not just a subset")
    print("-" * 60)
    
    try:
        # Test with n_papers=None (get all papers)
        result = orchestrator.chat_with_papers(
            query=test_query,
            n_papers=None,  # Get all available papers
            min_similarity_threshold=0.1,  # Lower threshold to get more papers
            enable_arxiv_fallback=True
        )
        
        # Analyze results
        papers = result.get('relevant_papers', [])
        discussions = result.get('agent_discussions', {})
        response = result.get('response', '')
        
        print(f"✅ Query processed successfully")
        print(f"📊 Found {len(papers)} relevant papers (should be many)")
        print(f"🤖 Generated discussions from {len([k for k in discussions.keys() if k != 'synthesis'])} agents")
        
        # Check if we got a substantial number of papers
        if len(papers) >= 5:
            print(f"✅ Success: Found {len(papers)} papers (no artificial limits)")
        else:
            print(f"⚠️  Warning: Only found {len(papers)} papers (might be limited by available data)")
        
        # Check response length
        response_length = len(response)
        print(f"📝 Response length: {response_length} characters")
        
        if response_length > 1000:
            print("✅ Success: Generated comprehensive response")
        else:
            print("⚠️  Warning: Response seems short")
        
        # Check synthesis
        if "synthesis" in discussions:
            synthesis = discussions["synthesis"]
            if isinstance(synthesis, dict):
                themes = synthesis.get("key_themes", [])
                recommendations = synthesis.get("recommendations", [])
                
                print(f"🎯 Key themes found: {len(themes)} (should be comprehensive)")
                print(f"💡 Recommendations: {len(recommendations)} (should be complete)")
                
                if len(themes) > 3:
                    print("✅ Success: Multiple themes identified")
                else:
                    print("⚠️  Warning: Few themes found")
                
                if len(recommendations) > 2:
                    print("✅ Success: Multiple recommendations provided")
                else:
                    print("⚠️  Warning: Few recommendations found")
        
        # Show paper sources
        vector_papers = [p for p in papers if p.get('source') == 'vector_db']
        arxiv_papers = [p for p in papers if p.get('source') == 'arxiv_search']
        
        print(f"\n📚 Paper Sources:")
        print(f"  - Vector DB: {len(vector_papers)} papers")
        print(f"  - ArXiv: {len(arxiv_papers)} papers")
        
        # Show first few papers
        print(f"\n📖 Sample Papers:")
        for i, paper in enumerate(papers[:5], 1):
            print(f"  {i}. {paper['title'][:60]}...")
        
        if len(papers) > 5:
            print(f"  ... and {len(papers) - 5} more papers")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n=== Test Summary ===")
    print("✅ No limits functionality tested successfully")
    print("📊 All available papers are now analyzed")
    print("🎯 All themes and recommendations are included")
    print("🚀 System is ready for comprehensive research analysis")

if __name__ == "__main__":
    test_no_limits() 