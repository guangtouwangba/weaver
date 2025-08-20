"""
Modular RAG System Demo

This example demonstrates the simplicity and power of the new modular architecture
compared to the complex DDD structure.

Key advantages shown:
1. Clear module responsibilities
2. Simple interfaces
3. Easy orchestration
4. Minimal dependencies
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.router import DocumentRouter
from modules.models import SearchQuery, ContentType, ModuleConfig


async def demo_document_ingestion():
    """Demonstrate document ingestion workflow."""
    print("🔄 Document Ingestion Demo")
    print("=" * 50)
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample documents
        test_files = []
        
        # Create a text file
        text_file = Path(temp_dir) / "sample.txt"
        text_file.write_text("""
        This is a sample document about artificial intelligence.
        
        Machine learning is a subset of artificial intelligence (AI) that provides systems 
        the ability to automatically learn and improve from experience without being 
        explicitly programmed.
        
        Deep learning is part of a broader family of machine learning methods based on 
        artificial neural networks with representation learning.
        
        Natural language processing (NLP) is a subfield of linguistics, computer science, 
        and artificial intelligence concerned with the interactions between computers and 
        human language.
        """)
        test_files.append(str(text_file))
        
        # Create a markdown file
        md_file = Path(temp_dir) / "readme.md"
        md_file.write_text("""
        # RAG System Overview
        
        ## What is RAG?
        
        Retrieval-Augmented Generation (RAG) is an AI framework that combines:
        - Information retrieval systems
        - Large language models
        - Knowledge bases
        
        ## Benefits
        
        1. **Accuracy**: Access to external knowledge
        2. **Timeliness**: Up-to-date information  
        3. **Transparency**: Traceable sources
        4. **Efficiency**: Focused generation
        
        ## Components
        
        - Vector databases
        - Document loaders
        - Text splitters
        - Embedding models
        """)
        test_files.append(str(md_file))
        
        # Initialize document router
        config = ModuleConfig(
            custom_params={
                'chunk_size': 500,
                'chunk_overlap': 50
            }
        )
        
        router = DocumentRouter(config)
        await router.initialize()
        
        try:
            # Ingest documents
            print(f"📄 Ingesting {len(test_files)} documents...")
            
            success_count = 0
            total_chunks = 0
            
            async for result in router.ingest_documents_batch(test_files):
                if result.success:
                    print(f"✅ {result.metadata.get('file_path', 'Unknown')}: "
                          f"{result.chunks_created} chunks "
                          f"({result.processing_time_ms:.1f}ms)")
                    success_count += 1
                    total_chunks += result.chunks_created
                else:
                    print(f"❌ {result.metadata.get('file_path', 'Unknown')}: "
                          f"{result.error_message}")
            
            print(f"\n📊 Results: {success_count}/{len(test_files)} files processed, "
                  f"{total_chunks} chunks created")
            
            return router
            
        except Exception as e:
            print(f"❌ Error during ingestion: {e}")
            await router.cleanup()
            return None


async def demo_search_functionality(router: DocumentRouter):
    """Demonstrate search functionality."""
    print("\n🔍 Search Functionality Demo")
    print("=" * 50)
    
    search_queries = [
        "machine learning",
        "artificial intelligence", 
        "RAG benefits",
        "vector databases",
        "natural language processing"
    ]
    
    for query_text in search_queries:
        print(f"\n🔎 Searching for: '{query_text}'")
        
        query = SearchQuery(
            query=query_text,
            max_results=3
        )
        
        try:
            response = await router.search_documents(query)
            
            if response.total_results > 0:
                print(f"   Found {response.total_results} results "
                      f"({response.processing_time_ms:.1f}ms)")
                
                for result in response.results:
                    preview = result.chunk.content[:100].replace('\n', ' ')
                    print(f"   📄 Score: {result.score:.3f} | {preview}...")
            else:
                print("   No results found")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")


async def demo_system_status(router: DocumentRouter):
    """Demonstrate system status reporting."""
    print("\n📊 System Status Demo")
    print("=" * 50)
    
    try:
        status = router.get_status()
        
        print(f"System Status: {'✅ Initialized' if status['initialized'] else '❌ Not Ready'}")
        print(f"Total Documents: {status['total_documents']}")
        print(f"Total Chunks: {status['total_chunks']}")
        print(f"Supported Formats: {', '.join(status['supported_formats'])}")
        
        print("\n📦 Component Status:")
        components = {
            'File Loader': status['file_loader_status'],
            'Document Processor': status['document_processor_status']
        }
        
        for name, comp_status in components.items():
            if isinstance(comp_status, dict):
                initialized = comp_status.get('initialized', False)
                enabled = comp_status.get('enabled', False)
                status_icon = '✅' if initialized and enabled else '❌'
                print(f"  {status_icon} {name}: {comp_status.get('module_type', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error getting system status: {e}")


async def demo_modular_architecture_benefits():
    """Demonstrate the benefits of the modular architecture."""
    print("\n🏗️ Modular Architecture Benefits")
    print("=" * 50)
    
    print("""
    ✅ BEFORE (DDD): Complex layered architecture
       domain/ -> application/ -> services/ -> infrastructure/ -> api/
       - High coupling between layers
       - Complex dependency injection
       - Hard to test individual components
       - Difficult to understand data flow
    
    ✅ AFTER (Modular): Simple modular architecture
       modules/ -> file_loader, document_processor, router
       - Clear single responsibilities
       - Minimal dependencies
       - Easy to test and mock
       - Straightforward orchestration
    
    🎯 Key Improvements:
    1. **Simplicity**: Each module has one clear purpose
    2. **Testability**: Modules can be tested independently
    3. **Maintainability**: Easy to modify or replace modules
    4. **Understanding**: Clear data flow and interfaces
    5. **Flexibility**: Easy to add new modules or strategies
    """)


async def main():
    """Run the complete demo."""
    print("🚀 Modular RAG System Demo")
    print("=" * 80)
    
    # Show architecture benefits
    await demo_modular_architecture_benefits()
    
    # Demonstrate document ingestion
    router = await demo_document_ingestion()
    
    if router:
        # Demonstrate search functionality
        await demo_search_functionality(router)
        
        # Demonstrate system status
        await demo_system_status(router)
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        await router.cleanup()
        print("✅ Demo completed successfully!")
    else:
        print("❌ Demo failed during document ingestion")


if __name__ == "__main__":
    asyncio.run(main())