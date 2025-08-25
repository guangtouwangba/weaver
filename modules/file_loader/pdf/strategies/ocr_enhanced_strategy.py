"""
OCR Enhanced PDF loading strategy for scanned documents.

This module implements a specialized PDF loading strategy that combines multiple
OCR engines to extract text from scanned PDFs with high accuracy. It provides
intelligent scan detection, multi-language support, and fallback mechanisms.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import tempfile
import hashlib
import io

# 优化OCR相关日志
easyocr_logger = logging.getLogger('easyocr')
easyocr_logger.setLevel(logging.ERROR)
paddleocr_logger = logging.getLogger('paddleocr')  
paddleocr_logger.setLevel(logging.ERROR)

from modules.file_loader.pdf.base import BasePDFStrategy, PDFStrategyError
from modules.file_loader.pdf.factory import register_pdf_strategy

logger = logging.getLogger(__name__)

# Check available OCR libraries
try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF for image extraction
    HAS_TESSERACT = True
    logger.info("Tesseract OCR is available")
except ImportError as e:
    HAS_TESSERACT = False
    pytesseract = None
    Image = None
    fitz = None
    logger.warning(f"OCR dependencies not available: {e}")

try:
    import easyocr
    HAS_EASYOCR = True
    logger.info("EasyOCR is available")
except ImportError:
    HAS_EASYOCR = False
    easyocr = None
    logger.warning("EasyOCR is not available")

try:
    import paddleocr
    HAS_PADDLEOCR = True
    logger.info("PaddleOCR is available")
except ImportError:
    HAS_PADDLEOCR = False
    paddleocr = None
    logger.warning("PaddleOCR is not available")


@register_pdf_strategy("ocr_enhanced")
class OCREnhancedStrategy(BasePDFStrategy):
    """
    Enhanced OCR strategy for scanned PDF documents.
    
    This strategy provides advanced OCR capabilities with:
    - Multiple OCR engine support (Tesseract, EasyOCR, PaddleOCR)
    - Intelligent scan detection
    - Multi-language text recognition
    - Image preprocessing and enhancement
    - Confidence-based text selection
    - Fallback mechanisms between OCR engines
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OCR Enhanced PDF strategy.
        
        Args:
            config: Strategy-specific configuration options
        """
        super().__init__(config)
        self._setup_default_config()
        self._ocr_engines = self._initialize_ocr_engines()
        
        logger.info(f"OCREnhancedStrategy initialized with {len(self._ocr_engines)} OCR engines")
        logger.debug(f"Configuration: {self.config}")
    
    def _setup_default_config(self) -> None:
        """Setup default configuration values."""
        defaults = {
            # OCR engine preferences (in order of preference)
            "preferred_engines": ["paddleocr", "easyocr", "tesseract"],
            
            # Language support
            "languages": ["en", "zh"],  # English and Chinese
            "tesseract_lang": "eng+chi_sim",
            
            # Image preprocessing
            "enhance_images": True,
            "dpi": 300,  # DPI for PDF to image conversion
            "contrast_factor": 1.2,
            "brightness_factor": 1.1,
            
            # OCR parameters
            "confidence_threshold": 0.6,  # Minimum confidence for text acceptance
            "use_gpu": False,  # Use GPU acceleration when available
            "parallel_processing": True,  # Process pages in parallel
            
            # Scan detection
            "auto_detect_scanned": True,
            "text_density_threshold": 0.1,  # Ratio of extractable text
            "image_area_threshold": 0.8,  # Minimum image area to consider scanned
            
            # Performance
            "max_pages_parallel": 4,
            "timeout_per_page": 60,  # seconds
            "max_file_size": 200 * 1024 * 1024  # 200MB
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _initialize_ocr_engines(self) -> Dict[str, Any]:
        """Initialize available OCR engines."""
        engines = {}
        
        # Initialize Tesseract
        if HAS_TESSERACT:
            try:
                # Test Tesseract availability
                pytesseract.get_tesseract_version()
                engines["tesseract"] = {
                    "available": True,
                    "engine": pytesseract,
                    "priority": 3
                }
                logger.info("Tesseract OCR engine initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Tesseract: {e}")
        
        # Initialize EasyOCR
        if HAS_EASYOCR:
            try:
                engines["easyocr"] = {
                    "available": True,
                    "reader": None,  # Lazy initialization
                    "priority": 2
                }
                logger.info("EasyOCR engine available")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")
        
        # Initialize PaddleOCR
        if HAS_PADDLEOCR:
            try:
                engines["paddleocr"] = {
                    "available": True,
                    "reader": None,  # Lazy initialization
                    "priority": 1
                }
                logger.info("PaddleOCR engine available")
            except Exception as e:
                logger.warning(f"Failed to initialize PaddleOCR: {e}")
        
        return engines
    
    @property
    def strategy_name(self) -> str:
        """Get strategy name."""
        return "ocr_enhanced"
    
    @property
    def priority(self) -> int:
        """Get strategy priority (lower number = higher priority)."""
        # Higher priority than basic strategies for scanned documents
        return 0 if self._has_any_ocr_engine() else 999
    
    def _has_any_ocr_engine(self) -> bool:
        """Check if any OCR engine is available."""
        return any(engine["available"] for engine in self._ocr_engines.values())
    
    async def can_handle(self, file_path: Path) -> bool:
        """
        Check if this strategy can handle the given PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if strategy can handle the file
        """
        # Must have at least one OCR engine
        if not self._has_any_ocr_engine():
            logger.debug("No OCR engines available")
            return False
        
        # Basic file validation
        if not await self.validate_file(file_path):
            return False
        
        try:
            # Check if it's a scanned document (if auto-detection is enabled)
            if self.config.get("auto_detect_scanned", True):
                is_scanned = await self._detect_scanned_pdf(file_path)
                logger.debug(f"Scan detection for {file_path.name}: {is_scanned}")
                return is_scanned
            
            # Otherwise, assume we can handle it if OCR is available
            return True
            
        except Exception as e:
            logger.warning(f"OCREnhancedStrategy cannot handle {file_path}: {e}")
            return False
    
    async def validate_file(self, file_path: Path) -> bool:
        """
        Validate PDF file for OCR processing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if file is valid for processing
        """
        # Check file existence
        if not await self._check_file_exists(file_path):
            logger.debug(f"File does not exist: {file_path}")
            return False
        
        # Check file extension
        if not await self._check_pdf_extension(file_path):
            logger.debug(f"File is not a PDF: {file_path}")
            return False
        
        # Check file size
        max_size = self.config.get("max_file_size", 200 * 1024 * 1024)
        if not await self._check_file_size(file_path, max_size):
            logger.debug(f"File too large: {file_path}")
            return False
        
        # Check if we can open the PDF (basic validation)
        try:
            if fitz:  # PyMuPDF available for validation
                with fitz.open(str(file_path)) as doc:
                    # Just verify we can open it
                    page_count = len(doc)
                    if page_count == 0:
                        logger.debug(f"PDF has no pages: {file_path}")
                        return False
                return True
            else:
                # If PyMuPDF not available, assume valid if other checks passed
                return True
        except Exception as e:
            logger.debug(f"PDF validation failed for {file_path}: {e}")
            return False
    
    async def _detect_scanned_pdf(self, file_path: Path) -> bool:
        """
        Detect if PDF is primarily scanned content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if PDF appears to be scanned
        """
        try:
            with fitz.open(str(file_path)) as doc:
                total_pages = len(doc)
                sample_pages = min(3, total_pages)  # Sample first 3 pages
                
                text_dense_pages = 0
                total_image_area = 0
                total_page_area = 0
                
                for page_num in range(sample_pages):
                    page = doc[page_num]
                    
                    # Check text density
                    text = page.get_text().strip()
                    page_area = abs(page.rect.width * page.rect.height)
                    text_density = len(text) / max(page_area, 1)
                    
                    if text_density > self.config["text_density_threshold"]:
                        text_dense_pages += 1
                    
                    # Check image coverage
                    image_list = page.get_images()
                    page_image_area = 0
                    
                    for img in image_list:
                        try:
                            img_rect = page.get_image_rects(img[0])
                            for rect in img_rect:
                                page_image_area += abs(rect.width * rect.height)
                        except Exception:
                            continue
                    
                    total_image_area += page_image_area
                    total_page_area += page_area
                
                # Decision logic
                text_ratio = text_dense_pages / sample_pages
                image_ratio = total_image_area / max(total_page_area, 1)
                
                is_scanned = (
                    text_ratio < 0.3 and  # Low text density
                    image_ratio > self.config["image_area_threshold"]  # High image coverage
                )
                
                logger.debug(
                    f"Scan detection metrics - Text ratio: {text_ratio:.3f}, "
                    f"Image ratio: {image_ratio:.3f}, Is scanned: {is_scanned}"
                )
                
                return is_scanned
                
        except Exception as e:
            logger.warning(f"Scan detection failed for {file_path}: {e}")
            return True  # Assume scanned if detection fails
    
    async def extract_content(self, file_path: Path, **kwargs) -> str:
        """
        Extract text content from PDF using OCR.
        
        Args:
            file_path: Path to the PDF file
            **kwargs: Additional extraction options
            
        Returns:
            str: Extracted text content
            
        Raises:
            PDFStrategyError: If content extraction fails
        """
        if not self._has_any_ocr_engine():
            raise PDFStrategyError(
                "No OCR engines available for text extraction",
                strategy_name=self.strategy_name,
                file_path=str(file_path)
            )
        
        try:
            # Convert PDF to images
            images = await self._pdf_to_images(file_path)
            
            if not images:
                logger.warning(f"No images extracted from {file_path}")
                return ""
            
            # Process images with OCR
            if self.config.get("parallel_processing", True):
                content = await self._extract_content_parallel(images)
            else:
                content = await self._extract_content_sequential(images)
            
            # Clean up temporary images
            await self._cleanup_temp_files(images)
            
            if not content.strip():
                logger.warning(f"No content extracted from {file_path}")
                return ""
            
            logger.info(f"Successfully extracted {len(content)} characters from {file_path}")
            return content
            
        except Exception as e:
            error_msg = f"OCR processing failed: {str(e)}"
            logger.error(f"Failed to extract content from {file_path}: {error_msg}")
            raise PDFStrategyError(
                error_msg,
                strategy_name=self.strategy_name,
                file_path=str(file_path),
                original_error=e
            )
    
    async def _pdf_to_images(self, file_path: Path) -> List[str]:
        """
        Convert PDF pages to images.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List[str]: List of temporary image file paths
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(
                executor,
                self._pdf_to_images_sync,
                file_path
            )
    
    def _pdf_to_images_sync(self, file_path: Path) -> List[str]:
        """
        Synchronously convert PDF pages to images.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List[str]: List of temporary image file paths
        """
        image_paths = []
        
        with fitz.open(str(file_path)) as doc:
            for page_num, page in enumerate(doc):
                try:
                    # Create high-resolution image
                    mat = fitz.Matrix(self.config["dpi"] / 72, self.config["dpi"] / 72)
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(
                        suffix=f"_page_{page_num}.png",
                        delete=False
                    )
                    
                    if self.config.get("enhance_images", True):
                        # Convert to PIL Image for enhancement
                        img_data = pix.tobytes("png")
                        pil_img = Image.open(io.BytesIO(img_data))
                        
                        # Apply enhancements
                        enhanced_img = self._enhance_image(pil_img)
                        enhanced_img.save(temp_file.name)
                    else:
                        pix.save(temp_file.name)
                    
                    image_paths.append(temp_file.name)
                    temp_file.close()
                    
                except Exception as e:
                    logger.warning(f"Failed to convert page {page_num}: {e}")
                    continue
        
        return image_paths
    
    def _enhance_image(self, image: 'Image.Image') -> 'Image.Image':
        """
        Enhance image for better OCR results.
        
        Args:
            image: PIL Image object
            
        Returns:
            Image.Image: Enhanced image
        """
        from PIL import ImageEnhance
        
        try:
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            contrast_enhancer = ImageEnhance.Contrast(image)
            image = contrast_enhancer.enhance(self.config["contrast_factor"])
            
            # Enhance brightness
            brightness_enhancer = ImageEnhance.Brightness(image)
            image = brightness_enhancer.enhance(self.config["brightness_factor"])
            
            return image
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    async def _extract_content_parallel(self, image_paths: List[str]) -> str:
        """
        Extract text from images in parallel.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            str: Extracted text content
        """
        max_workers = min(
            self.config["max_pages_parallel"],
            len(image_paths)
        )
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    self._extract_text_from_image,
                    image_path
                )
                for image_path in image_paths
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        content_parts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"OCR failed for image {i}: {result}")
                continue
            
            if result and result.strip():
                content_parts.append(result.strip())
        
        return "\n\n".join(content_parts)
    
    async def _extract_content_sequential(self, image_paths: List[str]) -> str:
        """
        Extract text from images sequentially.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            str: Extracted text content
        """
        content_parts = []
        
        for image_path in image_paths:
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    text = await loop.run_in_executor(
                        executor,
                        self._extract_text_from_image,
                        image_path
                    )
                
                if text and text.strip():
                    content_parts.append(text.strip())
                    
            except Exception as e:
                logger.warning(f"OCR failed for {image_path}: {e}")
                continue
        
        return "\n\n".join(content_parts)
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from a single image using the best available OCR engine.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: Extracted text
        """
        # Try OCR engines in order of preference
        preferred_engines = self.config.get("preferred_engines", ["tesseract"])
        
        for engine_name in preferred_engines:
            if engine_name not in self._ocr_engines or not self._ocr_engines[engine_name]["available"]:
                continue
            
            try:
                text = self._run_ocr_engine(engine_name, image_path)
                if text and len(text.strip()) > 10:  # Minimum text threshold
                    logger.debug(f"OCR successful with {engine_name} for {image_path}")
                    return text
            except Exception as e:
                logger.debug(f"OCR engine {engine_name} failed for {image_path}: {e}")
                continue
        
        logger.warning(f"All OCR engines failed for {image_path}")
        return ""
    
    def _run_ocr_engine(self, engine_name: str, image_path: str) -> str:
        """
        Run specific OCR engine on image.
        
        Args:
            engine_name: Name of OCR engine to use
            image_path: Path to the image file
            
        Returns:
            str: Extracted text
        """
        if engine_name == "tesseract":
            return self._run_tesseract(image_path)
        elif engine_name == "easyocr":
            return self._run_easyocr(image_path)
        elif engine_name == "paddleocr":
            return self._run_paddleocr(image_path)
        else:
            raise ValueError(f"Unknown OCR engine: {engine_name}")
    
    def _run_tesseract(self, image_path: str) -> str:
        """Run Tesseract OCR on image."""
        config = f"--oem 3 --psm 6 -l {self.config['tesseract_lang']}"
        
        # Get text with confidence scores
        data = pytesseract.image_to_data(
            image_path,
            config=config,
            output_type=pytesseract.Output.DICT
        )
        
        # Filter by confidence
        threshold = int(self.config["confidence_threshold"] * 100)
        text_parts = []
        
        for i, confidence in enumerate(data['conf']):
            if confidence > threshold:
                text = data['text'][i].strip()
                if text:
                    text_parts.append(text)
        
        return " ".join(text_parts)
    
    def _run_easyocr(self, image_path: str) -> str:
        """Run EasyOCR on image."""
        # Lazy initialization
        if self._ocr_engines["easyocr"]["reader"] is None:
            languages = self.config.get("languages", ["en"])
            self._ocr_engines["easyocr"]["reader"] = easyocr.Reader(
                languages,
                gpu=self.config.get("use_gpu", False)
            )
        
        reader = self._ocr_engines["easyocr"]["reader"]
        results = reader.readtext(image_path)
        
        # Filter by confidence and combine text
        threshold = self.config["confidence_threshold"]
        text_parts = []
        
        for (bbox, text, confidence) in results:
            if confidence > threshold:
                text_parts.append(text.strip())
        
        return " ".join(text_parts)
    
    def _run_paddleocr(self, image_path: str) -> str:
        """Run PaddleOCR on image."""
        # Lazy initialization
        if self._ocr_engines["paddleocr"]["reader"] is None:
            self._ocr_engines["paddleocr"]["reader"] = paddleocr.PaddleOCR(
                use_angle_cls=True,
                lang='ch',  # Supports Chinese and English
                use_gpu=self.config.get("use_gpu", False),
                show_log=False
            )
        
        reader = self._ocr_engines["paddleocr"]["reader"]
        results = reader.ocr(image_path)
        
        # Extract text with confidence filtering
        threshold = self.config["confidence_threshold"]
        text_parts = []
        
        for line in results:
            for word_info in line:
                bbox, (text, confidence) = word_info
                if confidence > threshold:
                    text_parts.append(text.strip())
        
        return " ".join(text_parts)
    
    async def _cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files."""
        for file_path in file_paths:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        try:
            metadata = {
                "extraction_method": "ocr_enhanced",
                "ocr_engines_available": list(self._ocr_engines.keys()),
                "scan_detected": await self._detect_scanned_pdf(file_path),
                "dpi": self.config["dpi"],
                "enhanced_images": self.config["enhance_images"]
            }
            
            # Add basic PDF info
            try:
                with fitz.open(str(file_path)) as doc:
                    metadata.update({
                        "page_count": len(doc),
                        "title": doc.metadata.get("title"),
                        "author": doc.metadata.get("author"),
                        "encrypted": doc.needs_pass
                    })
            except Exception as e:
                logger.warning(f"Failed to extract basic metadata: {e}")
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata from {file_path}: {e}")
            return {
                "extraction_method": "ocr_enhanced_fallback",
                "error": str(e),
                "ocr_engines_available": list(self._ocr_engines.keys())
            }