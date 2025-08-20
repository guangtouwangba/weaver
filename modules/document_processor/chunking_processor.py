"""
Chunking Document Processor

Implementation that focuses on intelligent document chunking.
"""

import uuid
from typing import List
from datetime import datetime

from .interface import IDocumentProcessor, ChunkingStrategy
from ..models import (
    Document, DocumentChunk, ProcessingResult, ModuleConfig, DocumentProcessorError
)


class ChunkingProcessor(IDocumentProcessor):
    """Document processor focused on chunking strategies."""
    
    def __init__(self, config: ModuleConfig = None, 
                 chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE):
        super().__init__(config or ModuleConfig())
        self.chunking_strategy = chunking_strategy
        
        # Set default chunking parameters
        defaults = {
            'chunk_size': 1000,
            'chunk_overlap': 100,
            'min_chunk_size': 50,
            'sentence_separators': ['.', '!', '?', '。', '！', '？', '\n\n']
        }
        
        for key, value in defaults.items():
            if key not in self.config.custom_params:
                self.config.custom_params[key] = value
    
    def get_chunking_strategy(self) -> ChunkingStrategy:
        """Get the chunking strategy."""
        return self.chunking_strategy
    
    async def process_document(self, document: Document) -> ProcessingResult:
        """Process document and create chunks."""
        start_time = datetime.now()
        
        try:
            # Validate document
            errors = self.validate_document(document)
            if errors:
                raise DocumentProcessorError(f"Document validation failed: {'; '.join(errors)}")
            
            # Create chunks
            chunks = await self.create_chunks(document)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProcessingResult(
                success=True,
                document_id=document.id,
                chunks_created=len(chunks),
                processing_time_ms=processing_time,
                metadata={
                    'chunking_strategy': self.chunking_strategy.value,
                    'chunk_size': self.config.custom_params['chunk_size'],
                    'chunk_overlap': self.config.custom_params['chunk_overlap'],
                    'original_length': len(document.content),
                    'chunks': chunks  # Include chunks in result
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProcessingResult(
                success=False,
                document_id=document.id,
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    async def create_chunks(self, document: Document) -> List[DocumentChunk]:
        """Create chunks based on the configured strategy."""
        # Preprocess content
        processed_content = self.preprocess_content(document.content)
        
        if self.chunking_strategy == ChunkingStrategy.FIXED_SIZE:
            return self._create_fixed_size_chunks(document, processed_content)
        elif self.chunking_strategy == ChunkingStrategy.SENTENCE_BASED:
            return self._create_sentence_based_chunks(document, processed_content)
        elif self.chunking_strategy == ChunkingStrategy.PARAGRAPH_BASED:
            return self._create_paragraph_based_chunks(document, processed_content)
        else:
            # Default to fixed size
            return self._create_fixed_size_chunks(document, processed_content)
    
    def _create_fixed_size_chunks(self, document: Document, content: str) -> List[DocumentChunk]:
        """Create fixed-size chunks."""
        chunks = []
        chunk_size = self.config.custom_params['chunk_size']
        chunk_overlap = self.config.custom_params['chunk_overlap']
        min_chunk_size = self.config.custom_params['min_chunk_size']
        
        chunk_index = 0
        start = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # Try to break at word boundary if not at end
            if end < len(content):
                # Look for word boundary within last 100 characters
                for i in range(end, max(start, end - 100), -1):
                    if content[i] in ' \n\t':
                        end = i
                        break
            
            chunk_content = content[start:end].strip()
            
            # Only create chunk if it meets minimum size
            if len(chunk_content) >= min_chunk_size:
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_offset=start,
                    end_offset=end,
                    metadata={
                        'document_title': document.title,
                        'chunking_strategy': 'fixed_size',
                        'chunk_size': chunk_size,
                        'chunk_overlap': chunk_overlap
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move to next chunk with overlap
            start = max(start + 1, end - chunk_overlap)
        
        return chunks
    
    def _create_sentence_based_chunks(self, document: Document, content: str) -> List[DocumentChunk]:
        """Create sentence-based chunks."""
        sentences = self._split_into_sentences(content)
        chunks = []
        chunk_size = self.config.custom_params['chunk_size']
        chunk_overlap = self.config.custom_params['chunk_overlap']
        min_chunk_size = self.config.custom_params['min_chunk_size']
        
        current_chunk = ""
        chunk_index = 0
        start_offset = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed size
            if len(current_chunk) + len(sentence) > chunk_size and len(current_chunk) > 0:
                # Create current chunk if it meets minimum size
                if len(current_chunk.strip()) >= min_chunk_size:
                    chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        start_offset=start_offset,
                        end_offset=start_offset + len(current_chunk),
                        metadata={
                            'document_title': document.title,
                            'chunking_strategy': 'sentence_based',
                            'chunk_size': chunk_size,
                            'chunk_overlap': chunk_overlap
                        }
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk with overlap
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    overlap_content = current_chunk[-chunk_overlap:]
                    start_offset += len(current_chunk) - chunk_overlap
                    current_chunk = overlap_content + sentence
                else:
                    start_offset += len(current_chunk)
                    current_chunk = sentence
            else:
                current_chunk += sentence
        
        # Add final chunk
        if len(current_chunk.strip()) >= min_chunk_size:
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document.id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_offset=start_offset,
                end_offset=start_offset + len(current_chunk),
                metadata={
                    'document_title': document.title,
                    'chunking_strategy': 'sentence_based'
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_paragraph_based_chunks(self, document: Document, content: str) -> List[DocumentChunk]:
        """Create paragraph-based chunks."""
        paragraphs = content.split('\n\n')
        chunks = []
        chunk_size = self.config.custom_params['chunk_size']
        min_chunk_size = self.config.custom_params['min_chunk_size']
        
        chunk_index = 0
        start_offset = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(paragraph) >= min_chunk_size:
                # If paragraph is too long, split it
                if len(paragraph) > chunk_size:
                    # Fall back to fixed-size chunking for long paragraphs
                    para_chunks = self._split_long_paragraph(document, paragraph, chunk_index, start_offset)
                    chunks.extend(para_chunks)
                    chunk_index += len(para_chunks)
                else:
                    # Use paragraph as chunk
                    chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document.id,
                        content=paragraph,
                        chunk_index=chunk_index,
                        start_offset=start_offset,
                        end_offset=start_offset + len(paragraph),
                        metadata={
                            'document_title': document.title,
                            'chunking_strategy': 'paragraph_based'
                        }
                    )
                    chunks.append(chunk)
                    chunk_index += 1
            
            start_offset += len(paragraph) + 2  # +2 for \n\n
        
        return chunks
    
    def _split_long_paragraph(self, document: Document, paragraph: str, 
                             start_chunk_index: int, start_offset: int) -> List[DocumentChunk]:
        """Split a long paragraph using fixed-size strategy."""
        # Create a temporary document for the paragraph
        temp_doc = Document(
            id=document.id,
            title=document.title,
            content=paragraph,
            content_type=document.content_type
        )
        
        # Use fixed-size chunking
        chunks = self._create_fixed_size_chunks(temp_doc, paragraph)
        
        # Update chunk indices and offsets
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = start_chunk_index + i
            chunk.start_offset += start_offset
            chunk.end_offset += start_offset
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        separators = self.config.custom_params['sentence_separators']
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in separators:
                if current_sentence.strip():
                    sentences.append(current_sentence)
                current_sentence = ""
        
        # Add final sentence
        if current_sentence.strip():
            sentences.append(current_sentence)
        
        return sentences