"""
Configuration management for file loader components.

This module centralizes all configuration settings for file loading strategies,
providing type-safe configuration with validation and default values.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field, validator


class PDFLoaderConfig(BaseModel):
    """
    Configuration for PDF file loader and strategies.
    
    This class manages all PDF-related settings including strategy selection,
    parsing parameters, performance tuning options, and auto-selection rules.
    
    All configurations can be overridden via environment variables using
    the pattern: PDF_LOADER__SETTING_NAME (double underscore for nesting).
    """
    
    # General PDF loader settings
    max_file_size: int = Field(
        default=100 * 1024 * 1024, 
        description="Maximum PDF file size in bytes (default: 100MB)",
        ge=1024  # At least 1KB
    )
    
    default_strategy: str = Field(
        default="pymupdf",  # 改为轻量级策略
        description="Default strategy to use for PDF processing"
    )
    
    enable_fallback: bool = Field(
        default=True, 
        description="Enable fallback to alternative strategies on failure"
    )
    
    # Strategy-specific configurations
    unstructured: Dict[str, Any] = Field(
        default_factory=lambda: {
            "parsing_strategy": "hi_res",          # High resolution parsing for better accuracy
            "ocr_languages": ["eng", "chi_sim"],   # OCR language support
            "extract_images": False,               # Whether to extract images
            "infer_table_structure": True,         # Infer table structures
            "timeout": 300,                        # Processing timeout in seconds
            "include_page_breaks": True,           # Include page break markers
            "extract_images_in_pdf": False,        # Extract embedded images
            "chunking_strategy": "by_title"        # How to chunk the content
        },
        description="Unstructured library specific configuration"
    )
    
    pymupdf: Dict[str, Any] = Field(
        default_factory=lambda: {
            "extract_images": False,               # Whether to extract images
            "password": None,                      # PDF password if required
            "text_sort": True,                     # Sort text by reading order
            "flags": 0,                            # Additional PyMuPDF flags
            "clip": None,                          # Clipping rectangle
            "textpage_flags": 0                    # Text page creation flags
        },
        description="PyMuPDF (fitz) library specific configuration"
    )
    
    pypdf2: Dict[str, Any] = Field(
        default_factory=lambda: {
            "strict": False,                       # Strict mode for PDF parsing
            "password": None,                      # PDF password if required
            "decrypt": True,                       # Auto decrypt if possible
            "flatten": False                       # Flatten form fields
        },
        description="PyPDF2 library specific configuration"
    )
    
    ocr_enhanced: Dict[str, Any] = Field(
        default_factory=lambda: {
            # OCR engine preferences (in order of preference)
            "preferred_engines": ["paddleocr", "easyocr", "tesseract"],
            
            # Language support
            "languages": ["en", "zh"],             # English and Chinese
            "tesseract_lang": "eng+chi_sim",       # Tesseract language codes
            
            # Image processing
            "enhance_images": True,                # Apply image enhancement
            "dpi": 300,                           # PDF to image conversion DPI
            "contrast_factor": 1.2,               # Image contrast enhancement
            "brightness_factor": 1.1,             # Image brightness enhancement
            
            # OCR parameters
            "confidence_threshold": 0.6,          # Minimum confidence threshold
            "use_gpu": False,                     # Use GPU acceleration
            "parallel_processing": True,          # Process pages in parallel
            
            # Scan detection
            "auto_detect_scanned": True,          # Auto-detect scanned documents
            "text_density_threshold": 0.1,       # Text density for scan detection
            "image_area_threshold": 0.8,         # Image area threshold
            
            # Performance
            "max_pages_parallel": 4,             # Max parallel page processing
            "timeout_per_page": 60,              # Timeout per page (seconds)
            "max_file_size": 200 * 1024 * 1024  # Max file size (200MB)
        },
        description="OCR Enhanced strategy for scanned documents"
    )
    
    # Strategy priority mapping (lower number = higher priority)
    strategy_priorities: Dict[str, int] = Field(
        default_factory=lambda: {
            "pymupdf": 0,                          # 最高优先级 - 轻量级且有效
            "unstructured": 1,                     # High priority for accuracy
            "pypdf2": 2,                           # Basic fallback option
            "ocr_enhanced": 3,                     # 降低OCR策略优先级
        },
        description="Strategy priority mapping for auto-selection"
    )
    
    # Auto strategy selection rules
    auto_selection: Dict[str, Any] = Field(
        default_factory=lambda: {
            "small_file_threshold": 5 * 1024 * 1024,    # 5MB threshold for small files
            "large_file_threshold": 50 * 1024 * 1024,   # 50MB threshold for large files
            "prefer_ocr_for_scanned": True,              # Use OCR-capable strategy for scanned PDFs
            "performance_mode": False,                   # Prioritize speed over accuracy
            "enable_scan_detection": True,               # Detect scanned PDFs automatically
            "scan_detection_strategy": "fast",           # Strategy for scan detection
            "max_concurrent_processes": 1                # 减少并发处理避免内存问题
        },
        description="Auto strategy selection configuration"
    )
    
    # Performance and monitoring settings
    performance: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enable_caching": True,                      # Enable processing result caching
            "cache_ttl": 3600,                          # Cache time-to-live in seconds
            "enable_metrics": True,                     # Enable performance metrics collection
            "log_processing_time": True,                # Log processing times
            "memory_limit_mb": 256,                     # 降低内存限制
            "processing_timeout": 600                   # Global processing timeout in seconds
        },
        description="Performance and monitoring configuration"
    )
    
    @validator("max_file_size")
    def validate_max_file_size(cls, v):
        """Validate maximum file size is reasonable."""
        if v < 1024:  # Less than 1KB
            raise ValueError("max_file_size must be at least 1024 bytes (1KB)")
        if v > 10 * 1024 * 1024 * 1024:  # More than 10GB
            raise ValueError("max_file_size cannot exceed 10GB")
        return v
    
    @validator("strategy_priorities")
    def validate_strategy_priorities(cls, v):
        """Validate strategy priorities are positive integers."""
        for strategy, priority in v.items():
            if not isinstance(priority, int) or priority < 1:
                raise ValueError(f"Priority for strategy '{strategy}' must be a positive integer")
        return v
    
    @validator("auto_selection")
    def validate_auto_selection_thresholds(cls, v):
        """Validate auto selection thresholds are logical."""
        small_threshold = v.get("small_file_threshold", 0)
        large_threshold = v.get("large_file_threshold", 0)
        
        if small_threshold >= large_threshold:
            raise ValueError("small_file_threshold must be less than large_file_threshold")
            
        return v
    
    def get_strategy_by_priority(self) -> List[str]:
        """
        Get strategies ordered by priority (highest first).
        
        Returns:
            List[str]: Strategy names ordered by priority
        """
        return [
            strategy for strategy, _ in sorted(
                self.strategy_priorities.items(), 
                key=lambda x: x[1]
            )
        ]
    
    def is_small_file(self, file_size: int) -> bool:
        """
        Check if file size is considered small.
        
        Args:
            file_size: File size in bytes
            
        Returns:
            bool: True if file is small
        """
        return file_size <= self.auto_selection["small_file_threshold"]
    
    def is_large_file(self, file_size: int) -> bool:
        """
        Check if file size is considered large.
        
        Args:
            file_size: File size in bytes
            
        Returns:
            bool: True if file is large
        """
        return file_size >= self.auto_selection["large_file_threshold"]
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dict[str, Any]: Strategy-specific configuration
            
        Raises:
            ValueError: If strategy is not configured
        """
        strategy_configs = {
            "unstructured": self.unstructured,
            "pymupdf": self.pymupdf,
            "pypdf2": self.pypdf2,
            "ocr_enhanced": self.ocr_enhanced
        }
        
        if strategy_name not in strategy_configs:
            raise ValueError(f"No configuration found for strategy: {strategy_name}")
            
        return strategy_configs[strategy_name].copy()
    
    class Config:
        """Pydantic model configuration."""
        env_prefix = "PDF_LOADER__"
        env_nested_delimiter = "__"
        case_sensitive = False


class FileLoaderConfig(BaseModel):
    """
    Root configuration for all file loader components.
    
    This class serves as the main configuration container for different
    file type loaders, with PDF being the first implemented.
    """
    
    pdf: PDFLoaderConfig = Field(
        default_factory=PDFLoaderConfig,
        description="PDF file loader configuration"
    )
    
    # Future file type configurations can be added here
    # text: TextLoaderConfig = Field(...)
    # office: OfficeLoaderConfig = Field(...)
    # image: ImageLoaderConfig = Field(...)
    
    class Config:
        """Pydantic model configuration."""
        env_prefix = "FILE_LOADER__"
        env_nested_delimiter = "__"