"""
PDF File Loader

Complete implementation for loading PDF files using pymupdf (fitz).
Supports text extraction, metadata extraction, and error handling.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from modules.file_loader.factory import register_file_loader
from modules.schemas import ContentType, Document, create_document_from_path
from modules.schemas.document import Document
from modules.file_loader.base import FileLoaderError, IFileLoader

logger = logging.getLogger(__name__)


try:
    from unstructured.partition.pdf import partition_pdf

    HAS_UNSTRUCTURED = True
except ImportError:
    HAS_UNSTRUCTURED = False
    partition_pdf = None

try:
    import fitz  # pymupdf

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    fitz = None

try:
    import PyPDF2

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PyPDF2 = None




@register_file_loader(content_type=ContentType.PDF)
class PDFFileLoader(IFileLoader):
    """PDF file loader implementation."""

    def __init__(self, max_file_size: int = 100 * 1024 * 1024, 
                 parsing_strategy: str = "hi_res",
                 ocr_languages: List[str] = None):
        """
        Initialize PDF file loader

        Args:
            max_file_size: Maximum file size (bytes), default 100MB
            parsing_strategy: Parsing strategy for Unstructured ("hi_res", "auto", "fast", "ocr_only")
            ocr_languages: OCR language codes (default: ["eng"])
        """
        self.max_file_size = max_file_size
        self.parsing_strategy = parsing_strategy
        self.ocr_languages = ocr_languages or ["eng"]
        self._supported_formats = [".pdf"]

        # Check available PDF processing libraries and set priority
        if HAS_UNSTRUCTURED:
            logger.info("PDFFileLoader uses Unstructured for advanced PDF processing (primary)")
        elif HAS_PYMUPDF:
            logger.info("PDFFileLoader uses pymupdf (fitz) for PDF processing (fallback)")
        elif HAS_PYPDF2:
            logger.info("PDFFileLoader uses PyPDF2 for PDF processing (fallback)")
        else:
            logger.warning(
                "No PDF processing library installed. Recommended installation: pip install unstructured[pdf]"
            )

    @property
    def loader_name(self) -> str:
        """Get loader name"""
        return "PDFFileLoader"

    def supported_formats(self) -> List[str]:
        """Get supported PDF formats"""
        return self._supported_formats.copy()

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Check if specified content type is supported"""
        return content_type == ContentType.PDF
    
    def _validate_language_codes(self, languages: List[str]) -> List[str]:
        """
        validate and fix language codes
        """

        valid_languages = []
        language_mapping = {
            'c': 'chi_sim',        
            'chinese': 'chi_sim',   # chinese simple
            'zh': 'chi_sim',       # chinses simple
            'zh-cn': 'chi_sim',    # chinese simple
            'zh-tw': 'chi_tra',    # chinese traditional
            'english': 'eng',      # english
            'en': 'eng'           # english
        }
        
        for lang in languages:
            if lang in language_mapping:
                corrected = language_mapping[lang]
                logger.info(f"OCR language code corrected: '{lang}' -> '{corrected}'")
                valid_languages.append(corrected)
            elif lang in ['eng', 'chi_sim', 'chi_tra', 'jpn', 'kor']:
                valid_languages.append(lang)
            else:
                logger.warning(f"Unknown OCR language code: {lang}, skip")
        
        return valid_languages
    
    async def _detect_scanned_pdf(self, path: Path) -> bool:
        """detect if the pdf is scanned"""
        if not HAS_UNSTRUCTURED:
            return False
    
        try:
            def quick_check():
                # use fast strategy to quickly check
                elements = partition_pdf(str(path), strategy="fast")
                
                # calculate text density
                text_elements = [e for e in elements if hasattr(e, 'category') 
                            and e.category in ['NarrativeText', 'Title', 'Header']]
                text_content = " ".join([str(e) for e in text_elements])
                
                # if the text is less, it may be scanned
                return len(text_content.strip()) < 100
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, quick_check)
            
        except Exception as e:
            logger.debug(f"Scan detection failed: {e}")
            return False
        
    async def _select_optimal_strategy(self, path: Path) -> str:
        """select the optimal strategy based on the pdf features"""
        
        # user specified strategy priority
        if hasattr(self, 'parsing_strategy') and self.parsing_strategy != "auto":
            return self.parsing_strategy
        
        file_size = path.stat().st_size
        
        # detect if the pdf is scanned
        is_likely_scanned = await self._detect_scanned_pdf(path)
        
        if is_likely_scanned:
            logger.info(f"Detected scanned PDF, using OCR strategy: {path.name}")
            if hasattr(self, 'enable_chinese_ocr') and self.enable_chinese_ocr:
                return "hi_res"  # high quality OCR for chinese
            else:
                return "ocr_only"  # pure OCR
        else:
            # select strategy based on file size
            if file_size < 5 * 1024 * 1024:  # < 5MB
                return "hi_res"
            elif file_size < 20 * 1024 * 1024:  # 5-20MB
                return "auto"
            else:  # > 20MB
                return "fast"

    async def validate_file(self, file_path: str) -> bool:
        """Validate if PDF file can be loaded"""
        try:
            path = Path(file_path)

            # 检查文件是否存在
            if not path.exists():
                logger.error(f"PDF file does not exist: {file_path}")
                return False

            # 检查文件大小
            if path.stat().st_size > self.max_file_size:
                logger.error(
                    f"PDF file too large: {path.stat().st_size} bytes > {self.max_file_size} bytes"
                )
                return False

            # 检查文件扩展名
            if path.suffix.lower() not in self._supported_formats:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False

            # Try to open PDF file to validate format
            if HAS_UNSTRUCTURED:
                try:
                    # Quick validation using Unstructured with fast strategy
                    elements = partition_pdf(file_path, strategy="fast")
                    page_count = len([e for e in elements if hasattr(e, 'metadata') and 
                                    e.metadata.get('page_number')]) or 1
                    logger.debug(
                        f"PDF validation successful (Unstructured): {file_path} ({page_count} pages)"
                    )
                    return True
                except Exception as e:
                    logger.error(f"PDF format validation failed (Unstructured): {e}")
                    # Fallback to PyMuPDF validation
                    if HAS_PYMUPDF:
                        try:
                            doc = fitz.open(file_path)
                            page_count = len(doc)
                            doc.close()
                            logger.debug(f"PDF validation successful (fallback pymupdf): {file_path} ({page_count} pages)")
                            return True
                        except Exception as e2:
                            logger.error(f"PDF format validation failed (fallback pymupdf): {e2}")
                            return False
                    return False
            elif HAS_PYMUPDF:
                try:
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                    logger.debug(
                        f"PDF validation successful: {file_path} ({page_count} pages)"
                    )
                    return True
                except Exception as e:
                    logger.error(f"PDF format validation failed (pymupdf): {e}")
                    return False
            elif HAS_PYPDF2:
                try:
                    with open(file_path, "rb") as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        page_count = len(pdf_reader.pages)
                        logger.debug(
                            f"PDF validation successful: {file_path} ({page_count} pages)"
                        )
                        return True
                except Exception as e:
                    logger.error(f"PDF format validation failed (PyPDF2): {e}")
                    return False
            else:
                logger.warning(
                    "No available PDF processing library, skip PDF format validation"
                )
                return True

        except Exception as e:
            logger.error(f"PDF file validation failed: {e}")
            return False

    async def load_document(self, request) -> Document:
        """Load PDF document"""
        from modules.models import FileLoadRequest

        # Handle different types of input parameters
        if isinstance(request, str):
            file_path = request
            metadata = {}
        elif isinstance(request, FileLoadRequest):
            file_path = request.file_path
            metadata = request.metadata or {}
        else:
            file_path = request
            metadata = {}

        # Validate file
        if not await self.validate_file(file_path):
            raise FileLoaderError(f"PDF file validation failed: {file_path}")

        try:
            path = Path(file_path)

            # Extract PDF content
            content = await self._extract_pdf_content(path)

            # Extract PDF metadata
            pdf_metadata = await self._extract_pdf_metadata(path)

            # Create document object
            document = create_document_from_path(file_path, content)

            # Update metadata
            document.metadata.update(
                {
                    "loader": self.loader_name,
                    "file_size": path.stat().st_size,
                    "extraction_method": (
                        "pymupdf"
                        if HAS_PYMUPDF
                        else ("PyPDF2" if HAS_PYPDF2 else "placeholder")
                    ),
                    **pdf_metadata,
                    **(metadata or {}),
                }
            )

            logger.info(
                f"Successfully loaded PDF document: {file_path} (page count: {pdf_metadata.get('pdf_pages', 'unknown')}, character count: {len(content)})"
            )
            return document

        except FileLoaderError:
            raise
        except Exception as e:
            logger.error(f"Failed to load PDF document {file_path}: {e}")
            raise FileLoaderError(f"Failed to load PDF document: {str(e)}")

    async def load_documents_batch(self, requests: List) -> List[Document]:
        """Batch load PDF documents"""
        documents = []

        for request in requests:
            try:
                document = await self.load_document(request)
                documents.append(document)

            except FileLoaderError as e:
                logger.error(f"Batch load PDF failed: {e}")
                # Continue processing other documents, do not interrupt entire batch
                continue

        logger.info(
            f"PDF batch loading completed: {len(documents)}/{len(requests)} successful"
        )
        return documents

    async def _extract_pdf_content(self, path: Path) -> str:
        """
        Extract text content from PDF file

        Prioritize Unstructured for advanced layout detection, fallback to pymupdf, then PyPDF2
        """
        # Determine strategy based on file size for performance optimization
        file_size = path.stat().st_size
        strategy = self._select_parsing_strategy(file_size)
        
        if HAS_UNSTRUCTURED:
            logger.info(f"Extracting text content with Unstructured ({strategy} strategy) from PDF file: {path.name}")
            try:
                return await self._extract_content_with_unstructured(path, strategy)
            except Exception as e:
                logger.warning(f"Unstructured extraction failed: {e}, falling back to pymupdf")
                if HAS_PYMUPDF:
                    return await self._extract_content_with_pymupdf(path)
                elif HAS_PYPDF2:
                    return await self._extract_content_with_pypdf2(path)
                else:
                    raise
        elif HAS_PYMUPDF:
            logger.info(f"Extracting text content with pymupdf from PDF file: {path.name}")
            return await self._extract_content_with_pymupdf(path)
        elif HAS_PYPDF2:
            logger.info(f"Extracting text content with PyPDF2: {path.name}")
            return await self._extract_content_with_pypdf2(path)
        else:
            logger.warning(
                "No PDF processing library installed, return placeholder content"
            )
            return f"[PDF content placeholder: {path.name}]\n\nThis PDF file requires PDF processing library to extract content. Please install: pip install unstructured[pdf]"

    def _select_parsing_strategy(self, file_size: int) -> str:
        """
        Select parsing strategy based on file size and configuration
        
        Args:
            file_size: File size in bytes
            
        Returns:
            Strategy string for Unstructured
        """
        if hasattr(self, 'parsing_strategy') and self.parsing_strategy != "auto":
            return self.parsing_strategy
        
        # Auto-select strategy based on file size
        if file_size < 5 * 1024 * 1024:  # < 5MB: Use high-resolution parsing
            return "hi_res"
        elif file_size < 20 * 1024 * 1024:  # 5-20MB: Use auto strategy
            return "auto"
        else:  # > 20MB: Use fast strategy to avoid timeouts
            return "fast"
    
    @staticmethod
    def _format_unstructured_elements(elements) -> str:
        """
        Format Unstructured elements into readable text

        Args:
            elements: List of Unstructured document elements

        Returns:
            Formatted text content
        """
        formatted_parts = []
        current_page = 1

        for element in elements:
            # Handle page breaks
            if hasattr(element, 'category') and element.category == "PageBreak":
                current_page += 1
                formatted_parts.append(f"\n--- Page {current_page} ---\n")
                continue

            # Get text content
            text = str(element) if hasattr(element, '__str__') else getattr(element, 'text', '')

            if not text.strip():
                continue

            # Format different element types
            if hasattr(element, 'category'):
                if element.category == "Title":
                    formatted_parts.append(f"# {text}\n")
                elif element.category == "NarrativeText":
                    formatted_parts.append(f"{text}\n")
                elif element.category == "ListItem":
                    formatted_parts.append(f"• {text}\n")
                elif element.category == "Table":
                    formatted_parts.append(f"[Table: {text}]\n")
                elif element.category == "Header":
                    formatted_parts.append(f"## {text}\n")
                else:
                    formatted_parts.append(f"{text}\n")
            else:
                formatted_parts.append(f"{text}\n")

        return "\n".join(formatted_parts)
    
    async def _extract_content_with_unstructured(self, path: Path, strategy: str = "hi_res") -> str:
        """Enhanced Unstructured extraction with OCR support"""
        try:
            def extract_elements():
                logger.debug(f"Unstructured参数: strategy={strategy}, languages={self.ocr_languages}")

                extracted_elements = partition_pdf(
                    str(path),
                    strategy=strategy,
                    include_page_breaks=True,
                    extract_images_in_pdf=False,
                    languages=self._validate_language_codes(self.ocr_languages),
                    # add OCR related parameters
                    infer_table_structure=True,
                )
                return extracted_elements

            loop = asyncio.get_event_loop()
            elements = await loop.run_in_executor(None, extract_elements)

            content = self._format_unstructured_elements(elements)

            if not content.strip():
                # if the content is empty, try OCR strategy
                if strategy != "ocr_only" and hasattr(self, 'enable_chinese_ocr') and self.enable_chinese_ocr:
                    logger.warning(f"Text extraction is empty, trying OCR mode: {path.name}")
                    return await self._extract_content_with_unstructured(path, "ocr_only")
                else:
                    logger.warning(f"PDF content extraction is empty: {path.name}")
                    return f"[PDF file {path.name} cannot extract text content, maybe scanned document needs OCR processing]"

            return content

        except Exception as e:
            logger.error(f"Unstructured extraction failed: {e}")
            raise FileLoaderError(f"Unstructured PDF extraction failed: {e}")

    async def _extract_content_with_pymupdf(self, path: Path) -> str:
        """Extract PDF content using pymupdf (fitz)"""
        try:
            # Run CPU-intensive task in async function
            def extract_text() -> str:
                doc = fitz.open(str(path))
                text_parts = []

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():  # Only add non-empty pages
                        text_parts.append(f"--- Page {page_num + 1} pages ---\n{text}")

                doc.close()
                return "\n\n".join(text_parts)

            # Use thread pool executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, extract_text)

            if not content.strip():
                logger.warning(
                    f"PDF file appears to have no extractable text content: {path}"
                )
                return f"[PDF file {path.name} has no extractable text content]"

            return content

        except Exception as e:
            logger.error(f"Failed to extract PDF content using pymupdf: {e}")
            raise FileLoaderError(f"PDF content extraction failed: {e}")

    async def _extract_content_with_pypdf2(self, path: Path) -> str:
        """Extract PDF content using PyPDF2"""
        try:

            def extract_text():
                text_parts = []
                with open(path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)

                    for page_num, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text.strip():  # Only add non-empty pages
                            text_parts.append(
                                f"--- Page {page_num + 1} pages ---\n{text}"
                            )

                return "\n\n".join(text_parts)

            # Use thread pool executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, extract_text)

            if not content.strip():
                logger.warning(
                    f"PDF file appears to have no extractable text content: {path}"
                )
                return f"[PDF file {path.name} has no extractable text content]"

            return content

        except Exception as e:
            logger.error(f"Failed to extract PDF content using PyPDF2: {e}")
            raise FileLoaderError(f"PDF content extraction failed: {e}")

    async def _extract_pdf_metadata(self, path: Path) -> Dict[str, Any]:
        """
        Extract PDF metadata

        Prioritize Unstructured, then pymupdf (fitz), fallback to PyPDF2
        """
        if HAS_UNSTRUCTURED:
            return await self._extract_metadata_with_unstructured(path)
        elif HAS_PYMUPDF:
            return await self._extract_metadata_with_pymupdf(path)
        elif HAS_PYPDF2:
            return await self._extract_metadata_with_pypdf2(path)
        else:
            # Basic metadata
            return {
                "pdf_pages": "unknown",
                "pdf_author": "unknown",
                "pdf_title": path.stem,
                "pdf_subject": "unknown",
                "pdf_creator": "unknown",
                "pdf_producer": "unknown",
                "extraction_method": "no_library",
            }

    async def _extract_metadata_with_unstructured(self, path: Path) -> Dict[str, Any]:
        """
        Extract PDF metadata using Unstructured library
        
        Leverages document structure analysis to provide enhanced metadata
        """
        try:
            def extract_metadata() -> Dict[str, Any]:
                # Use fast strategy for metadata extraction to optimize performance
                elements = partition_pdf(
                    str(path),
                    strategy="fast",
                    include_page_breaks=True,
                    extract_images_in_pdf=False,
                )
                
                # Count pages by counting page breaks + 1
                page_breaks = sum(1 for e in elements if hasattr(e, 'category') and e.category == "PageBreak")
                page_count = page_breaks + 1 if page_breaks > 0 else 1
                
                # Extract titles and headers for document analysis
                titles = [str(e) for e in elements if hasattr(e, 'category') and e.category == "Title"]
                headers = [str(e) for e in elements if hasattr(e, 'category') and e.category == "Header"]
                
                # Infer title from document structure
                inferred_title = titles[0] if titles else (headers[0] if headers else path.stem)
                
                # Extract text elements for analysis
                text_elements = [str(e) for e in elements if hasattr(e, 'category') and 
                               e.category in ["NarrativeText", "Title", "Header"]]
                
                # Calculate document statistics
                total_chars = sum(len(text) for text in text_elements)
                
                return {
                    "pdf_pages": page_count,
                    "pdf_title": inferred_title,
                    "pdf_author": "unknown",  # Unstructured doesn't extract document properties
                    "pdf_subject": "unknown",
                    "pdf_creator": "unknown", 
                    "pdf_producer": "unknown",
                    "extraction_method": "unstructured",
                    "document_structure": {
                        "title_count": len(titles),
                        "header_count": len(headers),
                        "total_elements": len(elements),
                        "content_length": total_chars,
                    }
                }
            
            # Use thread pool executor for CPU-intensive operation
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_metadata)
            
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata using Unstructured: {e}")
            # Fallback to basic metadata
            return {
                "pdf_pages": "unknown",
                "pdf_title": path.stem,
                "pdf_author": "unknown",
                "pdf_subject": "unknown",
                "pdf_creator": "unknown",
                "pdf_producer": "unknown",
                "extraction_method": "unstructured_fallback",
                "error": str(e)
            }

    async def _extract_metadata_with_pymupdf(self, path: Path) -> Dict[str, Any]:
        """Extract PDF metadata using pymupdf (fitz)"""
        try:

            def extract_metadata():
                doc = fitz.open(str(path))
                metadata = doc.metadata
                page_count = len(doc)
                doc.close()

                return {
                    "pdf_pages": page_count,
                    "pdf_title": metadata.get("title", path.stem),
                    "pdf_author": metadata.get("author", "unknown"),
                    "pdf_subject": metadata.get("subject", "unknown"),
                    "pdf_creator": metadata.get("creator", "unknown"),
                    "pdf_producer": metadata.get("producer", "unknown"),
                    "pdf_creation_date": metadata.get("creationDate", "unknown"),
                    "pdf_modification_date": metadata.get("modDate", "unknown"),
                    "extraction_method": "pymupdf",
                }

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_metadata)

        except Exception as e:
            logger.error(f"Failed to extract PDF metadata using pymupdf: {e}")
            return {
                "pdf_pages": "error",
                "pdf_author": "error",
                "pdf_title": path.stem,
                "extraction_method": "pymupdf_error",
                "error": str(e),
            }

    async def _extract_metadata_with_pypdf2(self, path: Path) -> Dict[str, Any]:
        """Extract PDF metadata using PyPDF2"""
        try:

            def extract_metadata():
                with open(path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata = pdf_reader.metadata
                    page_count = len(pdf_reader.pages)

                    return {
                        "pdf_pages": page_count,
                        "pdf_title": (
                            str(metadata.get("/Title", path.stem))
                            if metadata
                            else path.stem
                        ),
                        "pdf_author": (
                            str(metadata.get("/Author", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_subject": (
                            str(metadata.get("/Subject", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_creator": (
                            str(metadata.get("/Creator", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_producer": (
                            str(metadata.get("/Producer", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_creation_date": (
                            str(metadata.get("/CreationDate", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_modification_date": (
                            str(metadata.get("/ModDate", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "extraction_method": "PyPDF2",
                    }

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_metadata)

        except Exception as e:
            logger.error(f"Failed to extract PDF metadata using PyPDF2: {e}")
        return {
            "pdf_pages": "error",
            "pdf_author": "error",
            "pdf_title": path.stem,
            "extraction_method": "PyPDF2_error",
            "error": str(e),
        }
