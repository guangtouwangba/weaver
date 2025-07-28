#!/usr/bin/env python3
"""
Demo script for multi-agent research discussion
"""

import logging
import os
from agents.orchestrator import ResearchOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def demo_multi_agent_discussion():
    """Demo the multi-agent discussion functionality"""
    
    # Get API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("🤖 Multi-Agent Research Discussion Demo")
    print("=" * 50)
    print()
    
    # Initialize orchestrator
    print("📡 Initializing Research Orchestrator...")
    orchestrator = ResearchOrchestrator(
        openai_api_key=openai_api_key,
        db_path="./data/vector_db"
    )
    print("✅ Ready for multi-agent discussions!\n")
    
    # Interactive demo
    while True:
        print("\n" + "="*50)
        print("🎯 Enter your research question (or 'quit' to exit):")
        print("Examples:")
        print("- What are the latest developments in transformer architecture?")
        print("- How can machine learning be applied to climate change?")
        print("- What are the challenges in deploying AI models in production?")
        print("- What's new in reinforcement learning?")
        print()
        
        query = input("Your question: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Thanks for using the Multi-Agent Research Discussion!")
            break
        
        if not query:
            print("❌ Please enter a question.")
            continue
        
        print(f"\n🔍 Searching for papers related to: {query}")
        print("🤖 Generating multi-agent discussion...")
        print()
        
        try:
            # Get multi-agent discussion
            result = orchestrator.chat_with_papers(
                query=query,
                n_papers=None,  # Get all available papers
                min_similarity_threshold=0.3,
                enable_arxiv_fallback=True
            )
            
            # Display results
            print("📊 RESULTS")
            print("=" * 50)
            
            # Show response
            response = result.get('response', '')
            print(response)
            
            # Show statistics
            papers = result.get('relevant_papers', [])
            discussions = result.get('agent_discussions', {})
            
            print(f"\n📈 Statistics:")
            print(f"  - Papers analyzed: {len(papers)}")
            print(f"  - Agents involved: {len([k for k in discussions.keys() if k != 'synthesis'])}")
            print(f"  - Vector DB results: {result.get('vector_results_count', 0)}")
            print(f"  - ArXiv results: {result.get('arxiv_results_count', 0)}")
            
            # Show agent discussions summary
            if discussions:
                print(f"\n🤖 Agent Perspectives:")
                for agent_name, discussion in discussions.items():
                    if agent_name != "synthesis":
                        agent_emoji = orchestrator._get_agent_emoji(agent_name)
                        agent_title = orchestrator._get_agent_title(agent_name)
                        print(f"  {agent_emoji} {agent_title}")
            
            print("\n" + "="*50)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try a different question.")

if __name__ == "__main__":
    demo_multi_agent_discussion() 