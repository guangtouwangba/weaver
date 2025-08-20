"""
Text File Loader

Simple implementation for loading text-based files.
"""

import uuid
from typing import List, AsyncIterator
from pathlib import Path
from datetime import datetime

from .interface import IFileLoader
from ..models import (
    Document, ProcessingResult, ContentType, ModuleConfig, FileLoaderError
)


class TextFileLoader(IFileLoader):
    """Text file loader implementation."""
    
    def __init__(self, config: ModuleConfig = None):
        super().__init__(config or ModuleConfig())
        self._supported_formats = ['.txt', '.md', '.markdown']
    
    def supported_formats(self) -> List[str]:
        """Get supported text file formats."""
        return self._supported_formats.copy()
    
    async def load_document(self, file_path: str) -> Document:
        """Load a single text document."""
        # Validate file
        errors = self.validate_file(file_path)
        if errors:
            raise FileLoaderError(f"File validation failed: {'; '.join(errors)}")
        
        try:
            path = Path(file_path)
            
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = await self.extract_metadata(file_path)
            
            # Create document
            document = Document(
                id=str(uuid.uuid4()),
                title=path.stem,
                content=content,
                content_type=self.detect_content_type(file_path),
                file_path=file_path,
                file_size=path.stat().st_size,
                metadata=metadata
            )
            
            return document
            
        except UnicodeDecodeError as e:
            raise FileLoaderError(f"Failed to decode text file {file_path}: {e}")
        except IOError as e:
            raise FileLoaderError(f"Failed to read file {file_path}: {e}")
        except Exception as e:
            raise FileLoaderError(f"Unexpected error loading {file_path}: {e}")
    
    async def load_documents_batch(self, file_paths: List[str]) -> AsyncIterator[ProcessingResult]:
        """Load multiple text documents in batch."""
        for file_path in file_paths:
            start_time = datetime.now()
            
            try:
                document = await self.load_document(file_path)
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                yield ProcessingResult(
                    success=True,
                    document_id=document.id,
                    processing_time_ms=processing_time,
                    metadata={'file_path': file_path, 'content_length': len(document.content)}
                )
                
            except FileLoaderError as e:
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                yield ProcessingResult(
                    success=False,
                    processing_time_ms=processing_time,
                    error_message=str(e),
                    metadata={'file_path': file_path}
                )