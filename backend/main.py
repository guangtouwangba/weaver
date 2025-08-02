#!/usr/bin/env python3
"""
Research Agent RAG System - Main Entry Point

This script provides multiple ways to run the system:
1. FastAPI server (Default)
2. Command-line interface 
3. Demo mode
"""

import argparse
import asyncio
import os
import sys
import logging
from typing import Optional

# Add backend directory to Python path for imports
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file)

# Add backend directory to path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# If running from project root (when main.py is in backend/), adjust path
project_root = os.path.dirname(backend_dir)
if os.path.basename(backend_dir) == 'backend':
    # We're in the backend directory, add it to path
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
elif os.path.basename(os.getcwd()).endswith('research-agent-rag'):
    # Running from project root, add backend to path
    backend_path = os.path.join(os.getcwd(), 'backend')
    if os.path.exists(backend_path) and backend_path not in sys.path:
        sys.path.insert(0, backend_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment and validate requirements"""
    try:
        # Check for .env file (optional for production deployments)
        env_file = ".env"
        if not os.path.exists(env_file):
            logger.info(f"{env_file} not found. Using environment variables only.")
            logger.info("For local development, copy .env.example to .env and configure it.")
        else:
            logger.info(f"Found {env_file} file")
        
        # Validate Python version
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8 or higher is required")
        
        # Try importing key dependencies
        try:
            import fastapi
            import uvicorn
            import openai
            import chromadb
            import arxiv
        except ImportError as e:
            raise RuntimeError(f"Missing dependency: {e}. Run 'pip install -r requirements.txt'")
        
        logger.info("Environment setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Environment setup failed: {e}")
        return False

def run_api_server(host="0.0.0.0", port=8000, workers=1, reload=False):
    """Run FastAPI server"""
    try:
        print(f"🚀 Starting FastAPI server on {host}:{port}...")
        
        # Import uvicorn and the FastAPI app
        import uvicorn
        from api.server import app
        
        # Run the server
        uvicorn.run(
            "api.server:app",
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"FastAPI server failed: {e}")
        print(f"❌ Failed to start FastAPI server: {e}")
        sys.exit(1)

def run_cli_mode():
    """Run in command-line interface mode"""
    print("🔬 Research Agent RAG System - CLI Mode")
    print("=" * 50)
    
    try:
        # Import required modules
        from agents.orchestrator import ResearchOrchestrator
        from config import Config
        
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            print("Please check your .env file configuration.")
            return
        
        # Initialize orchestrator with full configuration
        orchestrator = ResearchOrchestrator(
            openai_api_key=Config.OPENAI_API_KEY,
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            anthropic_api_key=Config.ANTHROPIC_API_KEY,
            default_provider=Config.DEFAULT_PROVIDER,
            agent_configs=Config.get_all_agent_configs(),
            db_path=Config.VECTOR_DB_PATH
        )
        
        print("✅ System initialized successfully!")
        print("\nAvailable commands:")
        print("  research <topic>  - Start research on a topic")
        print("  chat <query>      - Chat with papers")
        print("  status           - Show system status")
        print("  quit             - Exit")
        
        # Main CLI loop
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(" ", 1)
                command = parts[0].lower()
                
                if command == "quit":
                    print("Goodbye!")
                    break
                elif command == "research":
                    if len(parts) > 1:
                        topic = parts[1]
                        print(f"Starting research on: {topic}")
                        # Note: This would need to be async in a real implementation
                        print("Research functionality available in async mode. Use the Streamlit interface for full functionality.")
                    else:
                        print("Usage: research <topic>")
                elif command == "chat":
                    if len(parts) > 1:
                        query = parts[1]
                        print(f"Searching for: {query}")
                        response = orchestrator.chat_with_papers(query)
                        print(f"Response: {response['response']}")
                    else:
                        print("Usage: chat <query>")
                elif command == "status":
                    stats = orchestrator.vector_store.get_collection_stats()
                    print(f"System Status:")
                    print(f"  Papers in database: {stats.get('unique_papers', 0)}")
                    print(f"  Total chunks: {stats.get('total_chunks', 0)}")
                    print(f"  Active agents: {len(orchestrator.agents)}")
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        logger.error(f"CLI mode failed: {e}")
        print(f"❌ Failed to start CLI mode: {e}")

async def run_demo_mode():
    """Run demonstration mode"""
    try:
        from examples.demo import run_complete_demo
        await run_complete_demo()
    except Exception as e:
        logger.error(f"Demo mode failed: {e}")
        print(f"❌ Demo mode failed: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Research Agent RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start FastAPI server (default)
  python main.py --port 3001        # Start API server on port 3001
  python main.py --mode cli         # Command-line interface
  python main.py --mode demo        # Run demonstration
  python main.py --reload           # Start with auto-reload for development
  
For first-time setup:
  1. Copy .env.example to .env
  2. Add your API keys to .env
  3. Run: python main.py
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["api", "cli", "demo"],
        default="api",
        help="Run mode (default: api)"
    )
    
    # FastAPI server arguments
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of workers (default: 1)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Run appropriate mode
    try:
        if args.mode == "api":
            run_api_server(
                host=args.host,
                port=args.port,
                workers=args.workers,
                reload=args.reload
            )
        elif args.mode == "cli":
            run_cli_mode()
        elif args.mode == "demo":
            print("🎭 Running demonstration...")
            asyncio.run(run_demo_mode())
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        if args.debug:
            logger.exception("Detailed error information:")
        sys.exit(1)

if __name__ == "__main__":
    main()