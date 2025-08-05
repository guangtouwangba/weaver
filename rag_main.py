#!/usr/bin/env python3
"""
RAG Question Answering System - Main Entry Point

A terminal-based RAG (Retrieval-Augmented Generation) system for 
intelligent question answering based on ArXiv papers.

Usage:
    python rag_main.py [config_file]

Example:
    python rag_main.py
    python rag_main.py custom_config.yaml
"""

import sys
import os
import logging
import argparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # python-dotenv not installed, skip loading

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_qa.cli.terminal_ui import TerminalUI

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('rag_qa.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RAG Question Answering System for ArXiv Papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rag_main.py                    # Use default config.yaml
  python rag_main.py my_config.yaml     # Use custom config file
  python rag_main.py --check-deps       # Check system dependencies
  
The system will:
1. Load your collected ArXiv papers from the database
2. Allow you to select keywords for focused question answering
3. Build a vector index using OpenAI embeddings for semantic search
4. Provide GPT-powered answers with source citations

Setup Requirements:
1. Install dependencies: pip install -r requirements-rag.txt
2. Collect papers first: python simple_paper_fetcher.py
3. Set up OpenAI API key:
   Method 1 (Recommended): Copy .env.example to .env and set OPENAI_API_KEY
   Method 2: Export environment variable: export OPENAI_API_KEY="sk-your-key"

Features:
- Uses OpenAI text-embedding-3-small for high-quality embeddings
- GPT-3.5-turbo for intelligent question answering
- Terminal-based interactive interface
- ChromaDB vector storage for fast retrieval
        """
    )
    
    parser.add_argument(
        'config',
        nargs='?',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check if all required dependencies are installed'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    if args.check_deps:
        check_dependencies()
        return
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"❌ Configuration file not found: {args.config}")
        print("Please create a config.yaml file or specify a different config file.")
        print("You can use the existing config.yaml from the paper fetcher as a starting point.")
        sys.exit(1)
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key by either:")
        print("1. Setting environment variable: export OPENAI_API_KEY='your-api-key-here'")
        print("2. Adding it to .env file: OPENAI_API_KEY=your-api-key-here")
        print()
        if not input("Continue anyway? (y/N): ").lower().startswith('y'):
            sys.exit(1)
    
    try:
        # Initialize and run the terminal UI
        print("🚀 Starting RAG Question Answering System...")
        ui = TerminalUI(args.config)
        ui.run()
        
    except KeyboardInterrupt:
        print("\\nGoodbye! 👋")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error in main: {e}", exc_info=True)
        sys.exit(1)

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking RAG system dependencies...")
    
    missing_deps = []
    optional_deps = []
    
    # Core dependencies
    core_deps = [
        ('sentence_transformers', 'sentence-transformers'),
        ('chromadb', 'chromadb'),
        ('openai', 'openai'),
        ('rich', 'rich'),
        ('PyPDF2', 'PyPDF2'),
        ('pdfplumber', 'pdfplumber'),
    ]
    
    # Optional dependencies
    opt_deps = [
        ('torch', 'torch'),
        ('transformers', 'transformers'),
        ('langchain_text_splitters', 'langchain-text-splitters'),
    ]
    
    print("\\nCore dependencies:")
    for module, package in core_deps:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_deps.append(package)
    
    print("\\nOptional dependencies:")
    for module, package in opt_deps:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ⚠️  {package} (optional)")
            optional_deps.append(package)
    
    # System checks
    print("\\nSystem checks:")
    
    # Check config file
    if os.path.exists('config.yaml'):
        print("  ✅ config.yaml found")
    else:
        print("  ❌ config.yaml not found")
    
    # Check .env file
    if os.path.exists('.env'):
        print("  ✅ .env file found")
    else:
        print("  ⚠️  .env file not found (recommended for API key storage)")
    
    # Check .env.example
    if os.path.exists('.env.example'):
        print("  ✅ .env.example template available")
    else:
        print("  ⚠️  .env.example template missing")
    
    # Check database
    if os.path.exists('papers.db'):
        print("  ✅ papers.db found")
    else:
        print("  ⚠️  papers.db not found (run simple_paper_fetcher.py first)")
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        # Mask the key for security
        masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "***"
        print(f"  ✅ OPENAI_API_KEY set ({masked_key})")
        
        # Check key format
        if not api_key.startswith('sk-'):
            print("  ⚠️  API key format may be incorrect (should start with 'sk-')")
    else:
        print("  ❌ OPENAI_API_KEY not set")
    
    # Summary
    print("\\nSummary:")
    if missing_deps:
        print(f"❌ Missing {len(missing_deps)} required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\\nInstall missing dependencies with:")
        print("pip install -r requirements-rag.txt")
    else:
        print("✅ All required dependencies are installed!")
    
    if optional_deps:
        print(f"⚠️  {len(optional_deps)} optional dependencies missing (may impact performance)")
    
    # Setup guidance
    print("\\n📋 Setup Checklist:")
    if not os.path.exists('.env') and not os.getenv('OPENAI_API_KEY'):
        print("1. Create .env file: cp .env.example .env")
        print("2. Add your OpenAI API key to .env file")
    if not os.path.exists('papers.db'):
        print("3. Collect papers: python simple_paper_fetcher.py")
    print("4. Start RAG system: python rag_main.py")

if __name__ == "__main__":
    main()