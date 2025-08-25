#!/usr/bin/env python3
"""
OCR Enhanced PDF Processing Usage Examples.

This example demonstrates how to use the OCR Enhanced strategy for 
processing scanned PDF documents with improved text extraction.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.file_loader.pdf.pdf_loader import PDFFileLoader
from modules.file_loader.pdf.strategies.ocr_enhanced_strategy import OCREnhancedStrategy
from config.file_loader_config import PDFLoaderConfig
from modules.models import FileLoadRequest


class OCRUsageExamples:
    """Examples for OCR Enhanced PDF processing."""
    
    def __init__(self):
        """Initialize examples with different configurations."""
        self.examples = {
            "basic_ocr": self._create_basic_config(),
            "high_accuracy": self._create_high_accuracy_config(),
            "multilingual": self._create_multilingual_config(),
            "performance_optimized": self._create_performance_config()
        }
    
    def _create_basic_config(self) -> Dict[str, Any]:
        """Basic OCR configuration for general use."""
        return {
            "default_strategy": "ocr_enhanced",
            "ocr_enhanced": {
                "preferred_engines": ["tesseract"],
                "languages": ["en"],
                "dpi": 200,
                "confidence_threshold": 0.6,
                "enhance_images": True,
                "auto_detect_scanned": True,
                "parallel_processing": True
            }
        }
    
    def _create_high_accuracy_config(self) -> Dict[str, Any]:
        """High accuracy configuration for critical documents."""
        return {
            "default_strategy": "ocr_enhanced",
            "ocr_enhanced": {
                "preferred_engines": ["paddleocr", "easyocr", "tesseract"],
                "languages": ["en", "zh"],
                "dpi": 300,
                "confidence_threshold": 0.8,
                "enhance_images": True,
                "contrast_factor": 1.3,
                "brightness_factor": 1.2,
                "auto_detect_scanned": True,
                "parallel_processing": False,  # Sequential for higher accuracy
                "timeout_per_page": 120
            }
        }
    
    def _create_multilingual_config(self) -> Dict[str, Any]:
        """Multilingual configuration for international documents."""
        return {
            "default_strategy": "ocr_enhanced",
            "ocr_enhanced": {
                "preferred_engines": ["easyocr", "paddleocr"],
                "languages": ["en", "zh", "ja", "ko"],
                "tesseract_lang": "eng+chi_sim+jpn+kor",
                "dpi": 250,
                "confidence_threshold": 0.7,
                "enhance_images": True,
                "auto_detect_scanned": True,
                "parallel_processing": True,
                "use_gpu": True  # Use GPU if available
            }
        }
    
    def _create_performance_config(self) -> Dict[str, Any]:
        """Performance-optimized configuration for batch processing."""
        return {
            "default_strategy": "ocr_enhanced",
            "ocr_enhanced": {
                "preferred_engines": ["tesseract"],  # Fastest engine
                "languages": ["en"],
                "dpi": 150,  # Lower DPI for speed
                "confidence_threshold": 0.5,
                "enhance_images": False,  # Skip enhancement for speed
                "auto_detect_scanned": True,
                "parallel_processing": True,
                "max_pages_parallel": 6,
                "timeout_per_page": 30
            }
        }
    
    async def example_basic_usage(self):
        """Basic OCR usage example."""
        logger.info("=== Basic OCR Usage Example ===")
        
        config = PDFLoaderConfig(**self.examples["basic_ocr"])
        loader = PDFFileLoader(config)
        
        # Example file path (replace with actual scanned PDF)
        test_file = "path/to/scanned_document.pdf"
        
        if not Path(test_file).exists():
            logger.warning(f"Test file not found: {test_file}")
            logger.info("Please provide a real scanned PDF file path")
            return
        
        try:
            # Load scanned document
            document = await loader.load_document(test_file)
            
            logger.info(f"Document loaded successfully:")
            logger.info(f"  - File: {document.source}")
            logger.info(f"  - Content length: {len(document.content)} characters")
            logger.info(f"  - Strategy used: {document.metadata.get('strategy_used')}")
            logger.info(f"  - OCR engines: {document.metadata.get('ocr_engines_available')}")
            
            # Display first 200 characters
            preview = document.content[:200].replace('\n', ' ')
            logger.info(f"  - Content preview: {preview}...")
            
        except Exception as e:
            logger.error(f"Failed to process document: {e}")
    
    async def example_batch_processing(self):
        """Batch processing example for multiple scanned documents."""
        logger.info("=== Batch Processing Example ===")
        
        config = PDFLoaderConfig(**self.examples["performance_optimized"])
        loader = PDFFileLoader(config)
        
        # Example file list (replace with actual files)
        test_files = [
            "path/to/scanned1.pdf",
            "path/to/scanned2.pdf",
            "path/to/scanned3.pdf"
        ]
        
        # Filter existing files
        existing_files = [f for f in test_files if Path(f).exists()]
        
        if not existing_files:
            logger.warning("No test files found - creating mock file requests")
            # Create mock requests for demonstration
            requests = [
                FileLoadRequest(
                    file_path=f"mock_file_{i}.pdf",
                    metadata={"source": "batch_example"}
                )
                for i in range(3)
            ]
        else:
            requests = existing_files
        
        try:
            # Process batch
            documents = await loader.load_documents_batch(requests)
            
            logger.info(f"Batch processing completed:")
            logger.info(f"  - Files processed: {len(documents)}")
            
            total_chars = sum(len(doc.content) for doc in documents)
            logger.info(f"  - Total content: {total_chars} characters")
            
            # Summary by strategy
            strategies = {}
            for doc in documents:
                strategy = doc.metadata.get('strategy_used', 'unknown')
                strategies[strategy] = strategies.get(strategy, 0) + 1
            
            logger.info(f"  - Strategies used: {strategies}")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
    
    async def example_advanced_configuration(self):
        """Advanced configuration example."""
        logger.info("=== Advanced Configuration Example ===")
        
        # Create custom OCR strategy directly
        ocr_config = {
            "preferred_engines": ["paddleocr", "easyocr"],
            "languages": ["en", "zh"],
            "dpi": 300,
            "confidence_threshold": 0.75,
            "enhance_images": True,
            "contrast_factor": 1.4,
            "brightness_factor": 1.3,
            "auto_detect_scanned": True,
            "text_density_threshold": 0.05,  # More sensitive scan detection
            "image_area_threshold": 0.7,
            "parallel_processing": True,
            "max_pages_parallel": 3,
            "timeout_per_page": 90
        }
        
        strategy = OCREnhancedStrategy(config=ocr_config)
        
        logger.info(f"OCR Strategy Configuration:")
        logger.info(f"  - Strategy: {strategy.strategy_name}")
        logger.info(f"  - Priority: {strategy.priority}")
        logger.info(f"  - Available engines: {list(strategy._ocr_engines.keys())}")
        logger.info(f"  - Configuration: {ocr_config}")
        
        # Test scan detection capability
        test_file = Path("path/to/test_document.pdf")
        if test_file.exists():
            can_handle = await strategy.can_handle(test_file)
            is_scanned = await strategy._detect_scanned_pdf(test_file)
            
            logger.info(f"File Analysis:")
            logger.info(f"  - Can handle: {can_handle}")
            logger.info(f"  - Detected as scanned: {is_scanned}")
        else:
            logger.info("No test file available for scan detection demo")
    
    async def example_error_handling(self):
        """Error handling and fallback example."""
        logger.info("=== Error Handling Example ===")
        
        # Configuration with fallback strategy
        config_with_fallback = {
            "default_strategy": "ocr_enhanced",
            "enable_fallback": True,
            "strategy_priorities": {
                "ocr_enhanced": 0,
                "unstructured": 1,
                "pymupdf": 2
            }
        }
        
        config = PDFLoaderConfig(**config_with_fallback)
        loader = PDFFileLoader(config)
        
        # Test with various file scenarios
        test_scenarios = [
            ("nonexistent_file.pdf", "File does not exist"),
            ("path/to/corrupted.pdf", "Corrupted PDF file"),
            ("path/to/password_protected.pdf", "Password-protected PDF"),
            ("path/to/normal_text.pdf", "Regular text PDF (not scanned)")
        ]
        
        for file_path, description in test_scenarios:
            logger.info(f"Testing: {description}")
            
            try:
                if Path(file_path).exists():
                    document = await loader.load_document(file_path)
                    logger.info(f"  ✓ Success: {document.metadata.get('strategy_used')}")
                else:
                    logger.info(f"  ⚠ Skipped: File not found")
                    
            except Exception as e:
                logger.info(f"  ✗ Failed: {e}")
    
    def print_configuration_guide(self):
        """Print configuration guidance."""
        logger.info("=== Configuration Guide ===")
        
        guide = """
OCR Enhanced Strategy Configuration Options:

📋 Core Settings:
  • preferred_engines: ["tesseract", "easyocr", "paddleocr"]
    - Order of OCR engines to try (first = preferred)
    - Available: tesseract, easyocr, paddleocr
  
  • languages: ["en", "zh", "ja", "ko"]
    - Languages for OCR recognition
    - Affects accuracy and processing time

🔧 Processing Settings:
  • dpi: 150-300 (default: 300)
    - Image resolution for PDF conversion
    - Higher = better accuracy, slower processing
  
  • confidence_threshold: 0.0-1.0 (default: 0.6)
    - Minimum confidence for text acceptance
    - Higher = more selective, potentially missing text

🎨 Image Enhancement:
  • enhance_images: true/false (default: true)
    - Apply preprocessing to improve OCR
  • contrast_factor: 1.0-2.0 (default: 1.2)
  • brightness_factor: 1.0-2.0 (default: 1.1)

🚀 Performance:
  • parallel_processing: true/false (default: true)
  • max_pages_parallel: 1-8 (default: 4)
  • timeout_per_page: seconds (default: 60)
  • use_gpu: true/false (default: false)

🔍 Auto-Detection:
  • auto_detect_scanned: true/false (default: true)
  • text_density_threshold: 0.0-1.0 (default: 0.1)
  • image_area_threshold: 0.0-1.0 (default: 0.8)

📊 Recommended Configurations:
  • Fast Processing: tesseract, dpi=150, enhance=false
  • High Accuracy: paddleocr+easyocr, dpi=300, sequential
  • Multilingual: easyocr+paddleocr, multiple languages
  • Batch Processing: tesseract, parallel=true, timeout=30
        """
        
        print(guide)


async def main():
    """Run all examples."""
    logger.info("🔍 OCR Enhanced PDF Processing Examples")
    logger.info("=" * 60)
    
    examples = OCRUsageExamples()
    
    # Print configuration guide
    examples.print_configuration_guide()
    
    # Run examples
    await examples.example_basic_usage()
    await examples.example_batch_processing()
    await examples.example_advanced_configuration()
    await examples.example_error_handling()
    
    logger.info("=" * 60)
    logger.info("✅ All examples completed!")
    logger.info("💡 Tip: Modify file paths to test with your own scanned PDFs")


if __name__ == "__main__":
    asyncio.run(main())