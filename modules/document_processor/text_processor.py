"""
Text Document Processor

Basic implementation for processing text documents with cleaning and preprocessing.
"""

from datetime import datetime

from .interface import IDocumentProcessor, ChunkingStrategy
from .chunking_processor import ChunkingProcessor
from ..models import (
    Document, DocumentChunk, ProcessingResult, ModuleConfig, DocumentProcessorError
)


class TextProcessor(IDocumentProcessor):
    """Text-focused document processor with enhanced preprocessing."""
    
    def __init__(self, config: ModuleConfig = None, 
                 chunking_strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE_BASED):
        super().__init__(config or ModuleConfig())
        
        # Use ChunkingProcessor for actual chunking
        self.chunking_processor = ChunkingProcessor(config, chunking_strategy)
        
        # Text-specific preprocessing options
        text_defaults = {
            'remove_extra_whitespace': True,
            'normalize_unicode': True,
            'remove_empty_lines': True,
            'preserve_line_breaks': True,
            'min_line_length': 3
        }
        
        for key, value in text_defaults.items():
            if key not in self.config.custom_params:
                self.config.custom_params[key] = value
    
    def get_chunking_strategy(self) -> ChunkingStrategy:
        """Get the chunking strategy."""
        return self.chunking_processor.get_chunking_strategy()
    
    async def process_document(self, document: Document) -> ProcessingResult:
        """Process document with text-specific preprocessing."""
        start_time = datetime.now()
        
        try:
            # Validate document
            errors = self.validate_document(document)
            if errors:
                raise DocumentProcessorError(f"Document validation failed: {'; '.join(errors)}")
            
            # Enhanced text preprocessing
            processed_content = self.preprocess_text_content(document.content)
            
            # Create a processed document
            processed_document = Document(
                id=document.id,
                title=document.title,
                content=processed_content,
                content_type=document.content_type,
                file_path=document.file_path,
                file_size=len(processed_content),
                status=document.status,
                created_at=document.created_at,
                updated_at=document.updated_at,
                metadata=document.metadata.copy(),
                tags=document.tags.copy()
            )
            
            # Use chunking processor for actual chunking
            result = await self.chunking_processor.process_document(processed_document)
            
            # Add text processing metadata
            if result.success and result.metadata:
                result.metadata.update({
                    'text_preprocessing_applied': True,
                    'original_content_length': len(document.content),
                    'processed_content_length': len(processed_content),
                    'content_reduction_ratio': 1 - (len(processed_content) / len(document.content))
                })
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProcessingResult(
                success=False,
                document_id=document.id,
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    async def create_chunks(self, document: Document) -> list[DocumentChunk]:
        """Create chunks with text preprocessing."""
        # Preprocess content
        processed_content = self.preprocess_text_content(document.content)
        
        # Create processed document
        processed_document = Document(
            id=document.id,
            title=document.title,
            content=processed_content,
            content_type=document.content_type,
            metadata=document.metadata
        )
        
        # Use chunking processor
        return await self.chunking_processor.create_chunks(processed_document)
    
    def preprocess_text_content(self, content: str) -> str:
        """Enhanced text preprocessing."""
        if not content:
            return content
        
        processed = content
        
        # Unicode normalization
        if self.config.custom_params.get('normalize_unicode', True):
            import unicodedata
            processed = unicodedata.normalize('NFKC', processed)
        
        # Remove extra whitespace
        if self.config.custom_params.get('remove_extra_whitespace', True):
            import re
            # Normalize spaces but preserve intentional line breaks
            processed = re.sub(r'[ \t]+', ' ', processed)
            
            if self.config.custom_params.get('preserve_line_breaks', True):
                # Normalize multiple line breaks but keep paragraph structure
                processed = re.sub(r'\n{3,}', '\n\n', processed)
            else:
                # Collapse all whitespace
                processed = re.sub(r'\s+', ' ', processed)
        
        # Remove empty lines
        if self.config.custom_params.get('remove_empty_lines', True):
            lines = processed.split('\n')
            min_length = self.config.custom_params.get('min_line_length', 3)
            
            filtered_lines = []
            for line in lines:
                stripped_line = line.strip()
                if len(stripped_line) >= min_length or not stripped_line:
                    filtered_lines.append(line)
            
            processed = '\n'.join(filtered_lines)
        
        return processed.strip()
    
    def get_text_stats(self, content: str) -> dict:
        """Get statistics about text content."""
        if not content:
            return {'chars': 0, 'words': 0, 'lines': 0, 'paragraphs': 0}
        
        import re
        
        # Basic stats
        chars = len(content)
        words = len(re.findall(r'\w+', content))
        lines = len(content.split('\n'))
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        
        return {
            'chars': chars,
            'words': words,
            'lines': lines,
            'paragraphs': paragraphs,
            'avg_words_per_line': words / lines if lines > 0 else 0,
            'avg_chars_per_word': chars / words if words > 0 else 0
        }