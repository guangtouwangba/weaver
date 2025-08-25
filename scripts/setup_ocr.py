#!/usr/bin/env python3
"""
Setup script for OCR dependencies.

This script helps install and configure OCR dependencies for enhanced
scanned document processing capabilities.
"""

import subprocess
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command: str, description: str) -> bool:
    """
    Run a shell command and return success status.
    
    Args:
        command: Shell command to execute
        description: Human-readable description
        
    Returns:
        bool: True if command succeeded
    """
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False


def install_system_dependencies():
    """Install system-level OCR dependencies."""
    logger.info("=== Installing System Dependencies ===")
    
    # Detect OS and install Tesseract
    import platform
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        logger.info("Detected macOS - using Homebrew")
        commands = [
            ("brew install tesseract", "Install Tesseract OCR"),
            ("brew install tesseract-lang", "Install Tesseract language packs"),
            ("brew install poppler", "Install Poppler for PDF processing")
        ]
    elif system == "linux":
        logger.info("Detected Linux - using apt")
        commands = [
            ("sudo apt-get update", "Update package list"),
            ("sudo apt-get install -y tesseract-ocr", "Install Tesseract OCR"),
            ("sudo apt-get install -y tesseract-ocr-chi-sim tesseract-ocr-chi-tra", "Install Chinese language packs"),
            ("sudo apt-get install -y libtesseract-dev", "Install Tesseract development headers"),
            ("sudo apt-get install -y poppler-utils", "Install Poppler utilities")
        ]
    else:
        logger.warning(f"Unsupported system: {system}")
        logger.info("Please install Tesseract manually:")
        logger.info("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        logger.info("  Linux: sudo apt-get install tesseract-ocr")
        logger.info("  macOS: brew install tesseract")
        return False
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    return success


def install_python_dependencies():
    """Install Python OCR libraries."""
    logger.info("=== Installing Python Dependencies ===")
    
    # Core OCR packages
    packages = [
        "pytesseract",           # Tesseract Python wrapper
        "Pillow",                # Image processing
        "opencv-python",         # Computer vision (for image preprocessing)
        "pdf2image",             # PDF to image conversion
        "easyocr",               # EasyOCR engine
        "paddlepaddle",          # PaddleOCR backend
        "paddleocr",             # PaddleOCR engine
        "numpy",                 # Numerical computing
        "scipy",                 # Scientific computing
    ]
    
    success = True
    for package in packages:
        if not run_command(f"uv add {package}", f"Install {package}"):
            logger.warning(f"Failed to install {package} - continuing...")
            # Don't fail entirely for optional packages
    
    return success


def test_ocr_installation():
    """Test OCR installation by importing libraries."""
    logger.info("=== Testing OCR Installation ===")
    
    tests = [
        ("pytesseract", "Tesseract Python wrapper"),
        ("PIL", "Pillow (PIL)"),
        ("cv2", "OpenCV"),
        ("easyocr", "EasyOCR"),
        ("paddleocr", "PaddleOCR")
    ]
    
    results = {}
    for module, description in tests:
        try:
            __import__(module)
            logger.info(f"✓ {description} - OK")
            results[module] = True
        except ImportError as e:
            logger.warning(f"✗ {description} - Failed: {e}")
            results[module] = False
    
    # Test Tesseract executable
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        logger.info(f"✓ Tesseract executable - Version {version}")
        results["tesseract_exe"] = True
    except Exception as e:
        logger.error(f"✗ Tesseract executable - Failed: {e}")
        results["tesseract_exe"] = False
    
    return results


def create_test_script():
    """Create a test script for OCR functionality."""
    logger.info("=== Creating Test Script ===")
    
    test_script = '''#!/usr/bin/env python3
"""
Test script for OCR Enhanced PDF strategy.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.file_loader.pdf.strategies.ocr_enhanced_strategy import OCREnhancedStrategy
from config.file_loader_config import PDFLoaderConfig


async def test_ocr_strategy():
    """Test OCR strategy functionality."""
    print("Testing OCR Enhanced Strategy...")
    
    # Create strategy with test configuration
    config = {
        "preferred_engines": ["tesseract", "easyocr", "paddleocr"],
        "languages": ["en", "zh"],
        "dpi": 200,  # Lower DPI for faster testing
        "confidence_threshold": 0.5,
        "auto_detect_scanned": True
    }
    
    strategy = OCREnhancedStrategy(config=config)
    
    print(f"Strategy name: {strategy.strategy_name}")
    print(f"Priority: {strategy.priority}")
    print(f"Available OCR engines: {strategy._ocr_engines.keys()}")
    
    # Test if strategy can handle files
    print("\\nStrategy capability test:")
    test_files = [
        "/path/to/test.pdf",  # Replace with actual test file
        Path("nonexistent.pdf")
    ]
    
    for test_file in test_files:
        can_handle = await strategy.can_handle(Path(test_file))
        print(f"  {test_file}: {'✓' if can_handle else '✗'}")
    
    print("\\nOCR strategy test completed!")


if __name__ == "__main__":
    asyncio.run(test_ocr_strategy())
'''
    
    test_file = Path("scripts/test_ocr.py")
    test_file.write_text(test_script)
    test_file.chmod(0o755)
    
    logger.info(f"✓ Created test script: {test_file}")
    return True


def main():
    """Main setup function."""
    logger.info("🔧 OCR Dependencies Setup")
    logger.info("=" * 50)
    
    # Install system dependencies
    if not install_system_dependencies():
        logger.error("System dependency installation failed")
        return False
    
    # Install Python packages
    if not install_python_dependencies():
        logger.error("Python dependency installation failed")
        return False
    
    # Test installation
    results = test_ocr_installation()
    
    # Create test script
    create_test_script()
    
    # Summary
    logger.info("=" * 50)
    logger.info("🎯 Setup Summary:")
    
    successful = sum(results.values())
    total = len(results)
    
    if successful == total:
        logger.info(f"✅ All {total} components installed successfully!")
        logger.info("Your system is ready for enhanced OCR processing.")
    else:
        logger.warning(f"⚠️  {successful}/{total} components installed successfully.")
        logger.info("Some optional components may not be available.")
    
    logger.info("\\n📖 Next Steps:")
    logger.info("1. Update your PDF loader config to use 'ocr_enhanced' strategy")
    logger.info("2. Test with: python scripts/test_ocr.py")
    logger.info("3. Process scanned PDFs with improved text extraction")
    
    return successful > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)