"""
File Loader Factory Usage Examples

Demonstrates the improved FileLoaderFactory design with simplified caller interface.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_loader import (
    # Simple convenience functions
    load_document,
    detect_content_type,
    get_supported_types,
    is_supported,
    # Advanced factory access
    FileLoaderFactory,
)
from modules.schemas.enums import ContentType


class MockRequest:
    """Mock request object for demonstration"""

    def __init__(self, file_path: str, content_type: str = None):
        self.file_path = file_path
        self.content_type = content_type


async def example_simple_usage():
    """Demonstrate the simplest way to use the file loader"""
    print("=== Simple Usage Example ===")

    # Example 1: Auto-detect and load with one line
    request = MockRequest("document.pdf")

    try:
        # This is all the caller needs to do!
        document = await load_document(request)
        print(f"✅ Loaded document: {document}")
    except Exception as e:
        print(f"❌ Failed to load: {e}")

    # Example 2: Check if file type is supported
    file_path = "example.pdf"
    content_type = detect_content_type(file_path)

    if content_type and is_supported(content_type):
        print(f"✅ {file_path} ({content_type}) is supported")
        request = MockRequest(file_path, content_type.value)
        # Load with detected type
        # document = await load_document(request)
    else:
        print(f"❌ {file_path} is not supported")


async def example_advanced_usage():
    """Demonstrate advanced usage with custom options"""
    print("\n=== Advanced Usage Example ===")

    # Example 1: Disable auto-detection
    request = MockRequest("unknown_file.xyz", ContentType.TXT.value)
    document = await load_document(
        request,
        auto_detect=False,  # Force use specified content type
        fallback_to_text=True,
    )
    print(f"✅ Loaded with forced type: {document}")

    # Example 2: Disable fallback for strict type checking
    try:
        request = MockRequest("corrupted.pdf", ContentType.PDF.value)
        document = await load_document(
            request, fallback_to_text=False  # Fail if PDF loader fails
        )
    except Exception as e:
        print(f"✅ Expected failure without fallback: {e}")


def example_factory_inspection():
    """Demonstrate factory inspection capabilities"""
    print("\n=== Factory Inspection Example ===")

    # Check what types are supported
    supported_types = get_supported_types()
    print(f"📋 Supported content types: {[t.value for t in supported_types]}")

    # Get detailed loader information
    loader_info = FileLoaderFactory.get_loader_info()
    print("📋 Registered loaders:")
    for content_type, info in loader_info.items():
        print(f"  - {content_type}: {info['loader_class']}")

    # Test various file extensions
    test_files = ["document.pdf", "text.txt", "data.csv", "page.html", "unknown.xyz"]

    print("\n📋 Content type detection:")
    for file_path in test_files:
        detected = detect_content_type(file_path)
        supported = is_supported(detected) if detected else False
        print(f"  - {file_path} → {detected} (supported: {supported})")


async def example_comparison():
    """Compare old vs new usage patterns"""
    print("\n=== Usage Pattern Comparison ===")

    print("❌ OLD WAY (complex, error-prone):")
    print(
        """
    try:
        loader = FileLoaderFactory.get_loader(content_type)
        document = await loader.load_document(request)
        
        # Add metadata manually
        document.metadata.update({
            "loader_type": loader.__class__.__name__,
            "content_type_used": content_type.value
        })
        
    except ValueError as e:
        # Fallback logic in every caller
        logger.warning(f"Primary loader failed: {e}")
        try:
            text_loader = FileLoaderFactory.get_loader(ContentType.TXT)
            request.content_type = ContentType.TXT.value
            document = await text_loader.load_document(request)
            # More manual metadata...
        except Exception as fallback_error:
            raise ValueError(f"Both loaders failed: {fallback_error}")
    """
    )

    print("✅ NEW WAY (simple, robust):")
    print(
        """
    # Just one line with auto-detection, fallback, and metadata!
    document = await load_document(request)
    """
    )


async def main():
    """Run all examples"""
    print("🚀 File Loader Factory Design Improvements\n")

    await example_simple_usage()
    await example_advanced_usage()
    example_factory_inspection()
    await example_comparison()

    print("\n✨ Design improvements summary:")
    print("1. 🎯 One-step loading: load_document() handles everything")
    print("2. 🔍 Auto-detection: Automatically detects file types")
    print("3. 🛡️ Smart fallback: Graceful degradation to text loader")
    print("4. 📊 Rich metadata: Automatic loader and detection info")
    print("5. 🔧 Flexible options: Control auto-detection and fallback")
    print("6. 📋 Inspection tools: Easy to check capabilities")
    print("7. 🎨 Convenience functions: Direct access without factory")


if __name__ == "__main__":
    asyncio.run(main())
