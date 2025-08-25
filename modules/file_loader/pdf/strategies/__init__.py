"""
PDF loading strategies package.

This package contains different strategies for loading and processing PDF files.
Each strategy implements the IPDFLoadStrategy interface and provides specific
capabilities for different PDF processing libraries and use cases.
"""

from modules.file_loader.pdf.strategies.pymupdf_strategy import PyMuPDFStrategy
from modules.file_loader.pdf.strategies.unstructured_strategy import UnstructuredStrategy
from modules.file_loader.pdf.strategies.ocr_enhanced_strategy import OCREnhancedStrategy

__all__ = ["UnstructuredStrategy", "PyMuPDFStrategy", "OCREnhancedStrategy"]