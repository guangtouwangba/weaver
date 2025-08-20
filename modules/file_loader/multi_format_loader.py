"""
Multi-Format File Loader

Provides a unified interface for loading multiple file formats
by delegating to appropriate specialized loaders.
"""

from typing import List, AsyncIterator, Dict
from pathlib import Path

from .interface import IFileLoader
from .text_loader import TextFileLoader
from .pdf_loader import PDFFileLoader
from ..models import (
    Document, ProcessingResult, ModuleConfig, FileLoaderError
)


class MultiFormatLoader(IFileLoader):
    """Multi-format file loader that delegates to specialized loaders."""
    
    def __init__(self, config: ModuleConfig = None):
        super().__init__(config or ModuleConfig())
        
        # Initialize specialized loaders
        self._loaders: Dict[str, IFileLoader] = {}
        self._register_loaders()
    
    def _register_loaders(self):
        """Register specialized loaders for different formats."""
        # Text loader
        text_loader = TextFileLoader(self.config)
        for fmt in text_loader.supported_formats():
            self._loaders[fmt] = text_loader
        
        # PDF loader
        pdf_loader = PDFFileLoader(self.config)
        for fmt in pdf_loader.supported_formats():
            self._loaders[fmt] = pdf_loader
    
    def supported_formats(self) -> List[str]:
        """Get all supported formats from registered loaders."""
        return list(self._loaders.keys())
    
    def _get_loader_for_file(self, file_path: str) -> IFileLoader:
        """Get appropriate loader for file format."""
        ext = Path(file_path).suffix.lower()
        loader = self._loaders.get(ext)
        
        if not loader:
            raise FileLoaderError(f"No loader available for format: {ext}")
        
        return loader
    
    async def load_document(self, file_path: str) -> Document:
        """Load document using appropriate specialized loader."""
        loader = self._get_loader_for_file(file_path)
        return await loader.load_document(file_path)
    
    async def load_documents_batch(self, file_paths: List[str]) -> AsyncIterator[ProcessingResult]:
        """Load multiple documents using appropriate loaders."""
        # Group files by loader type for efficient processing
        loader_groups: Dict[IFileLoader, List[str]] = {}
        
        for file_path in file_paths:
            try:
                loader = self._get_loader_for_file(file_path)
                if loader not in loader_groups:
                    loader_groups[loader] = []
                loader_groups[loader].append(file_path)
            except FileLoaderError as e:
                # Yield error result for unsupported files
                yield ProcessingResult(
                    success=False,
                    error_message=str(e),
                    metadata={'file_path': file_path}
                )
        
        # Process each group with its specialized loader
        for loader, paths in loader_groups.items():
            async for result in loader.load_documents_batch(paths):
                yield result
    
    async def initialize(self):
        """Initialize the multi-format loader and all sub-loaders."""
        await super().initialize()
        
        # Initialize all registered loaders
        initialized_loaders = set()
        for loader in self._loaders.values():
            if loader not in initialized_loaders:
                await loader.initialize()
                initialized_loaders.add(loader)
    
    async def cleanup(self):
        """Cleanup all sub-loaders."""
        # Cleanup all registered loaders
        cleaned_loaders = set()
        for loader in self._loaders.values():
            if loader not in cleaned_loaders:
                await loader.cleanup()
                cleaned_loaders.add(loader)
        
        await super().cleanup()
    
    def get_status(self) -> dict:
        """Get status of multi-format loader and all sub-loaders."""
        status = super().get_status()
        
        # Add sub-loader statuses
        loader_statuses = {}
        checked_loaders = set()
        
        for format_ext, loader in self._loaders.items():
            loader_id = id(loader)
            if loader_id not in checked_loaders:
                loader_statuses[loader.__class__.__name__] = {
                    'status': loader.get_status(),
                    'formats': [ext for ext, l in self._loaders.items() if l == loader]
                }
                checked_loaders.add(loader_id)
        
        status['sub_loaders'] = loader_statuses
        status['total_formats_supported'] = len(self.supported_formats())
        
        return status