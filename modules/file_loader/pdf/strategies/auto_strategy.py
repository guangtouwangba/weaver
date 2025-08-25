"""
Automatic PDF loading strategy selector.

This module implements an automatic strategy selection mechanism that chooses
the best available PDF processing strategy based on file characteristics,
system capabilities, and configuration preferences.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from modules.file_loader.pdf.base import IPDFLoadStrategy, PDFStrategyError
from modules.file_loader.pdf.factory import register_pdf_strategy, get_pdf_strategy_factory

logger = logging.getLogger(__name__)


@register_pdf_strategy("auto")
class AutoStrategy(IPDFLoadStrategy):
    """
    Automatic PDF loading strategy selector.
    
    This strategy automatically selects and uses the best available PDF
    processing strategy based on:
    - Strategy availability and capabilities
    - File characteristics and requirements
    - Configuration preferences and priorities
    - Fallback options when primary strategies fail
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize automatic strategy selector.
        
        Args:
            config: Strategy-specific configuration options
        """
        self.config = config or {}
        self._setup_default_config()
        
        logger.debug(f"AutoStrategy initialized with config: {self.config}")
    
    def _setup_default_config(self) -> None:
        """Setup default configuration values."""
        defaults = {
            "preferred_strategies": ["unstructured", "pymupdf", "pypdf2"],
            "fallback_enabled": True,
            "timeout": 60.0,
            "max_file_size": 100 * 1024 * 1024  # 100MB
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        # Ensure preferred_strategies is a list
        if not isinstance(self.config["preferred_strategies"], list):
            self.config["preferred_strategies"] = defaults["preferred_strategies"]
    
    @property
    def strategy_name(self) -> str:
        """Get strategy name."""
        return "auto"
    
    @property
    def priority(self) -> int:
        """Get strategy priority (lower number = higher priority)."""
        return 999  # Lowest priority since it's a meta-strategy
    
    async def can_handle(self, file_path: Path) -> bool:
        """
        Check if this strategy can handle the given PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if any strategy can handle the file
        """
        # Basic file validation
        if not await self.validate_file(file_path):
            return False
        
        # Auto strategy can handle any PDF that at least one strategy can handle
        try:
            factory = get_pdf_strategy_factory()
            await factory.select_best_strategy(file_path)
            return True
        except PDFStrategyError:
            logger.debug(f"No strategy can handle file: {file_path}")
            return False
        except Exception as e:
            logger.warning(f"Error checking strategy availability for {file_path}: {e}")
            return False
    
    async def validate_file(self, file_path: Path) -> bool:
        """
        Validate PDF file for processing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if file is valid for processing
        """
        # Check file existence
        if not file_path.exists():
            return False
        
        # Check file extension
        if file_path.suffix.lower() != ".pdf":
            return False
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            max_size = self.config.get("max_file_size", 100 * 1024 * 1024)
            if file_size > max_size:
                logger.warning(f"File {file_path} exceeds maximum size limit: {file_size} > {max_size}")
                return False
        except OSError as e:
            logger.error(f"Failed to get file stats for {file_path}: {e}")
            return False
        
        return True
    
    async def extract_content(self, file_path: Path, **kwargs) -> str:
        """
        Extract text content from PDF using the best available strategy.
        
        Args:
            file_path: Path to the PDF file
            **kwargs: Additional extraction options
            
        Returns:
            str: Extracted text content
            
        Raises:
            PDFStrategyError: If content extraction fails with all strategies
        """
        factory = get_pdf_strategy_factory()
        timeout = self.config.get("timeout", 60.0)
        
        try:
            if self.config.get("fallback_enabled", True):
                # Get strategy with fallback options
                strategies = await factory.select_strategy_with_fallback(file_path)
                
                # Try each strategy in order
                errors = []
                for strategy in strategies:
                    try:
                        logger.info(f"Attempting content extraction with strategy: {strategy.strategy_name}")
                        
                        # Apply timeout to the extraction
                        content = await asyncio.wait_for(
                            strategy.extract_content(file_path, **kwargs),
                            timeout=timeout
                        )
                        
                        logger.info(f"Successfully extracted content using strategy: {strategy.strategy_name}")
                        return content
                        
                    except asyncio.TimeoutError:
                        error_msg = f"Strategy '{strategy.strategy_name}' timed out after {timeout}s"
                        logger.warning(error_msg)
                        errors.append(f"{strategy.strategy_name}: {error_msg}")
                    except Exception as e:
                        error_msg = f"Strategy '{strategy.strategy_name}' failed: {str(e)}"
                        logger.warning(error_msg)
                        errors.append(f"{strategy.strategy_name}: {str(e)}")
                
                # All strategies failed
                raise PDFStrategyError(
                    f"All PDF strategies failed for file: {file_path}. Errors: {'; '.join(errors)}",
                    strategy_name=self.strategy_name,
                    file_path=str(file_path)
                )
            else:
                # Use only the best strategy without fallback
                strategy = await factory.select_best_strategy(file_path)
                logger.info(f"Using single strategy: {strategy.strategy_name}")
                
                try:
                    content = await asyncio.wait_for(
                        strategy.extract_content(file_path, **kwargs),
                        timeout=timeout
                    )
                    return content
                except asyncio.TimeoutError:
                    raise PDFStrategyError(
                        f"Content extraction timed out after {timeout}s",
                        strategy_name=strategy.strategy_name,
                        file_path=str(file_path)
                    )
                
        except PDFStrategyError:
            raise
        except Exception as e:
            error_msg = f"Auto strategy selection failed: {str(e)}"
            logger.error(f"Failed to extract content from {file_path}: {error_msg}")
            raise PDFStrategyError(
                error_msg,
                strategy_name=self.strategy_name,
                file_path=str(file_path),
                original_error=e
            )
    
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from PDF using the best available strategy.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        factory = get_pdf_strategy_factory()
        timeout = self.config.get("timeout", 60.0)
        
        try:
            if self.config.get("fallback_enabled", True):
                # Get strategy with fallback options
                strategies = await factory.select_strategy_with_fallback(file_path)
                
                # Try each strategy in order
                errors = []
                for strategy in strategies:
                    try:
                        logger.info(f"Attempting metadata extraction with strategy: {strategy.strategy_name}")
                        
                        # Apply timeout to the extraction
                        metadata = await asyncio.wait_for(
                            strategy.extract_metadata(file_path),
                            timeout=timeout
                        )
                        
                        # Add auto strategy information
                        metadata["selected_strategy"] = strategy.strategy_name
                        metadata["auto_strategy_used"] = True
                        
                        logger.info(f"Successfully extracted metadata using strategy: {strategy.strategy_name}")
                        return metadata
                        
                    except asyncio.TimeoutError:
                        error_msg = f"Strategy '{strategy.strategy_name}' timed out after {timeout}s"
                        logger.warning(error_msg)
                        errors.append(f"{strategy.strategy_name}: {error_msg}")
                    except Exception as e:
                        error_msg = f"Strategy '{strategy.strategy_name}' failed: {str(e)}"
                        logger.warning(error_msg)
                        errors.append(f"{strategy.strategy_name}: {str(e)}")
                
                # All strategies failed - return fallback metadata
                logger.warning(f"All strategies failed for metadata extraction: {'; '.join(errors)}")
                return self._get_fallback_metadata(file_path, errors)
                
            else:
                # Use only the best strategy without fallback
                strategy = await factory.select_best_strategy(file_path)
                logger.info(f"Using single strategy for metadata: {strategy.strategy_name}")
                
                try:
                    metadata = await asyncio.wait_for(
                        strategy.extract_metadata(file_path),
                        timeout=timeout
                    )
                    
                    # Add auto strategy information
                    metadata["selected_strategy"] = strategy.strategy_name
                    metadata["auto_strategy_used"] = True
                    
                    return metadata
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Metadata extraction timed out after {timeout}s")
                    return self._get_fallback_metadata(file_path, [f"Timeout after {timeout}s"])
                
        except Exception as e:
            logger.warning(f"Auto strategy selection failed for metadata: {e}")
            return self._get_fallback_metadata(file_path, [str(e)])
    
    def _get_fallback_metadata(self, file_path: Path, errors: List[str]) -> Dict[str, Any]:
        """
        Generate fallback metadata when all strategies fail.
        
        Args:
            file_path: Path to the PDF file
            errors: List of error messages from failed strategies
            
        Returns:
            Dict[str, Any]: Fallback metadata
        """
        metadata = {
            "extraction_method": "auto_fallback",
            "selected_strategy": "none",
            "auto_strategy_used": True,
            "error": f"All strategies failed: {'; '.join(errors)}",
            "page_count": 0,
            "title": None,
            "author": None,
            "subject": None,
            "creator": None
        }
        
        # Add basic file information if possible
        try:
            file_stats = file_path.stat()
            metadata.update({
                "file_size": file_stats.st_size,
                "file_modified": file_stats.st_mtime,
                "file_name": file_path.name
            })
        except OSError:
            pass
        
        return metadata
    
    def _get_strategy_summary(self) -> str:
        """
        Get a summary of the auto strategy configuration.
        
        Returns:
            str: Strategy configuration summary
        """
        preferred = ", ".join(self.config.get("preferred_strategies", []))
        fallback_enabled = self.config.get("fallback_enabled", True)
        timeout = self.config.get("timeout", 60.0)
        
        return (
            f"Strategy: {self.strategy_name}\n"
            f"Preferred strategies: {preferred}\n" 
            f"Fallback enabled: {fallback_enabled}\n"
            f"Timeout: {timeout}s"
        )