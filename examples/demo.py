"""
Comprehensive demo script for the Research Agent RAG System

This script demonstrates all the key features:
1. Paper retrieval and storage
2. Multi-agent analysis
3. Chat interface functionality
4. Research session management
"""

import asyncio
import os
import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
from agents.orchestrator import ResearchOrchestrator
from retrieval.arxiv_client import ArxivClient
from database.vector_store import VectorStore
from config import Config

async def demo_paper_retrieval():
    """Demo 1: Paper retrieval functionality"""
    print("\n" + "="*50)
    print("DEMO 1: Paper Retrieval")
    print("="*50)
    
    # Initialize arXiv client
    arxiv_client = ArxivClient(max_results=5)
    
    # Search for papers on a topic
    topic = "large language models"
    print(f"Searching for papers on: {topic}")
    
    papers = arxiv_client.search_papers(topic, max_results=5)
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
        print(f"   Categories: {', '.join(paper.categories)}")
        print(f"   Published: {paper.published.strftime('%Y-%m-%d')}")
        print(f"   Abstract: {paper.abstract[:200]}...")
    
    return papers

async def demo_vector_storage(papers):
    """Demo 2: Vector database storage and search"""
    print("\n" + "="*50)
    print("DEMO 2: Vector Database Storage & Search")
    print("="*50)
    
    # Initialize vector store
    vector_store = VectorStore(db_path="./demo_data/vector_db")
    
    # Store papers
    print("Storing papers in vector database...")
    for paper in papers:
        try:
            vector_store.add_paper(paper)
            print(f"✓ Stored: {paper.title[:50]}...")
        except Exception as e:
            print(f"✗ Error storing paper: {e}")
    
    # Get database stats
    stats = vector_store.get_collection_stats()
    print(f"\nDatabase stats:")
    print(f"- Total papers: {stats['unique_papers']}")
    print(f"- Total chunks: {stats['total_chunks']}")
    
    # Demo semantic search
    print("\nTesting semantic search...")
    search_queries = [
        "attention mechanisms in transformers",
        "scaling laws for neural networks",
        "emergent capabilities"
    ]
    
    for query in search_queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.search_papers(query, n_results=2)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['metadata']['title'][:60]}...")
            print(f"     Similarity: {result['similarity_score']:.3f}")
    
    return vector_store

async def demo_single_agent_analysis(papers):
    """Demo 3: Single agent analysis"""
    print("\n" + "="*50)
    print("DEMO 3: Single Agent Analysis")
    print("="*50)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI API key not found. Skipping agent analysis demo.")
        print("   Set OPENAI_API_KEY environment variable to run this demo.")
        return
    
    # Import agents
    from agents.google_engineer_agent import GoogleEngineerAgent
    from agents.mit_researcher_agent import MITResearcherAgent
    
    # Initialize agents
    google_agent = GoogleEngineerAgent(api_key)
    mit_agent = MITResearcherAgent(api_key)
    
    # Analyze first paper with both agents
    paper = papers[0]
    print(f"Analyzing paper: {paper.title[:60]}...")
    
    try:
        # Google Engineer analysis
        print("\n🔧 Google Engineer Analysis:")
        google_analysis = google_agent.analyze_paper(paper)
        print(f"Confidence: {google_analysis.confidence_score:.2f}")
        print(f"Key insights: {len(google_analysis.key_insights)}")
        print(f"Breaking points: {len(google_analysis.breaking_points)}")
        print(f"Analysis preview: {google_analysis.analysis[:300]}...")
        
        # MIT Researcher analysis
        print("\n🎓 MIT Researcher Analysis:")
        mit_analysis = mit_agent.analyze_paper(paper)
        print(f"Confidence: {mit_analysis.confidence_score:.2f}")
        print(f"Key insights: {len(mit_analysis.key_insights)}")
        print(f"Breaking points: {len(mit_analysis.breaking_points)}")
        print(f"Analysis preview: {mit_analysis.analysis[:300]}...")
        
        return [google_analysis, mit_analysis]
        
    except Exception as e:
        print(f"✗ Error in agent analysis: {e}")
        return []

async def demo_orchestrator(papers):
    """Demo 4: Full orchestrator functionality"""
    print("\n" + "="*50)
    print("DEMO 4: Research Orchestrator")
    print("="*50)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI API key not found. Skipping orchestrator demo.")
        return None
    
    try:
        # Initialize orchestrator
        orchestrator = ResearchOrchestrator(
            openai_api_key=api_key,
            db_path="./demo_data/vector_db"
        )
        
        # Start a research session
        topic = "transformer attention mechanisms"
        print(f"Starting research session on: {topic}")
        
        # For demo purposes, we'll use a smaller subset
        session = await orchestrator.research_topic(
            topic=topic,
            max_papers=3,
            include_recent=True
        )
        
        print(f"\n✅ Research session completed!")
        print(f"Session ID: {session.session_id}")
        print(f"Papers analyzed: {len(session.papers)}")
        print(f"Agent analyses: {len(session.agent_analyses)}")
        
        # Show agent insights
        for agent_name, analyses in session.agent_analyses.items():
            print(f"\n{agent_name}: {len(analyses)} analyses")
            if analyses:
                avg_confidence = sum(a.confidence_score for a in analyses) / len(analyses)
                print(f"  Average confidence: {avg_confidence:.2f}")
        
        return orchestrator
        
    except Exception as e:
        print(f"✗ Error in orchestrator demo: {e}")
        return None

async def demo_chat_interface(orchestrator):
    """Demo 5: Chat functionality"""
    print("\n" + "="*50)
    print("DEMO 5: Chat Interface")
    print("="*50)
    
    if not orchestrator:
        print("⚠️  Orchestrator not available. Skipping chat demo.")
        return
    
    # Demo chat queries
    chat_queries = [
        "What are the main challenges with attention mechanisms?",
        "How do transformers scale with model size?",
        "What are the latest improvements in transformer efficiency?"
    ]
    
    for query in chat_queries:
        print(f"\n💬 User: {query}")
        
        try:
            response = orchestrator.chat_with_papers(query, n_papers=3)
            print(f"🤖 Assistant: {response['response'][:400]}...")
            
            if response['relevant_papers']:
                print(f"   Found {len(response['relevant_papers'])} relevant papers")
                
        except Exception as e:
            print(f"✗ Error in chat query: {e}")

def demo_configuration():
    """Demo 6: Configuration and setup"""
    print("\n" + "="*50)
    print("DEMO 6: Configuration")
    print("="*50)
    
    # Validate configuration
    try:
        config_valid = Config.validate()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"⚠️  Configuration issue: {e}")
    
    # Show configuration
    print(f"\nCurrent configuration:")
    print(f"- Default model: {Config.DEFAULT_MODEL}")
    print(f"- Max papers per query: {Config.MAX_PAPERS_PER_QUERY}")
    print(f"- Chunk size: {Config.CHUNK_SIZE}")
    print(f"- Chunk overlap: {Config.CHUNK_OVERLAP}")
    print(f"- Vector DB path: {Config.VECTOR_DB_PATH}")
    
    # Check API keys
    has_openai = bool(Config.OPENAI_API_KEY)
    has_anthropic = bool(Config.ANTHROPIC_API_KEY)
    
    print(f"\nAPI Keys:")
    print(f"- OpenAI: {'✅ Set' if has_openai else '❌ Not set'}")
    print(f"- Anthropic: {'✅ Set' if has_anthropic else '❌ Not set'}")

async def run_complete_demo():
    """Run the complete demo showcasing all features"""
    print("🔬 Research Agent RAG System - Complete Demo")
    print("=" * 50)
    print("This demo showcases a multi-agent research system that:")
    print("1. Retrieves papers from arXiv")
    print("2. Stores them in a vector database")
    print("3. Analyzes them with specialized AI agents")
    print("4. Provides chat interface for paper discussions")
    print("5. Orchestrates complex research workflows")
    
    # Check prerequisites
    demo_configuration()
    
    try:
        # Demo 1: Paper retrieval
        papers = await demo_paper_retrieval()
        
        if not papers:
            print("❌ No papers retrieved. Cannot continue demo.")
            return
        
        # Demo 2: Vector storage
        vector_store = await demo_vector_storage(papers)
        
        # Demo 3: Single agent analysis
        analyses = await demo_single_agent_analysis(papers)
        
        # Demo 4: Full orchestrator
        orchestrator = await demo_orchestrator(papers)
        
        # Demo 5: Chat interface
        await demo_chat_interface(orchestrator)
        
        print("\n" + "="*50)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\nNext steps:")
        print("1. Set up your API keys in .env file")
        print("2. Run 'streamlit run chat/chat_interface.py' for the web interface")
        print("3. Or use the orchestrator directly in your Python code")
        print("4. Explore the different agent perspectives on your research topics")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo error details:")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(run_complete_demo())