#!/usr/bin/env python3
"""
Text chunking for RAG module
Handles intelligent splitting of PDF text into manageable chunks
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    chunk_id: str
    source_doc: str
    page_number: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class TextChunker:
    """Intelligently splits text into chunks for vector indexing"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, max_chunks_per_doc: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks_per_doc = max_chunks_per_doc
        
        # Initialize text splitter
        if LANGCHAIN_AVAILABLE:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\\n\\n", "\\n", ". ", " ", ""]
            )
            logger.info("Using LangChain RecursiveCharacterTextSplitter")
        else:
            self.splitter = None
            logger.info("Using custom text splitter (LangChain not available)")
    
    def chunk_document(self, text: str, source_doc: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """
        Split document text into chunks
        
        Args:
            text: Full document text
            source_doc: Source document identifier (e.g., arxiv_id)
            metadata: Additional metadata for the document
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            logger.warning(f"Empty text for document {source_doc}")
            return []
        
        try:
            # Use appropriate splitting method
            if self.splitter:
                chunks = self._chunk_with_langchain(text, source_doc, metadata)
            else:
                chunks = self._chunk_custom(text, source_doc, metadata)
            
            # Limit number of chunks per document
            if len(chunks) > self.max_chunks_per_doc:
                logger.warning(f"Document {source_doc} has {len(chunks)} chunks, limiting to {self.max_chunks_per_doc}")
                chunks = chunks[:self.max_chunks_per_doc]
            
            logger.info(f"Created {len(chunks)} chunks for document {source_doc}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {source_doc}: {e}")
            return []
    
    def _chunk_with_langchain(self, text: str, source_doc: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Chunk text using LangChain splitter"""
        text_chunks = self.splitter.split_text(text)
        
        chunks = []
        current_pos = 0
        
        for i, chunk_text in enumerate(text_chunks):
            # Find chunk position in original text
            chunk_start = text.find(chunk_text, current_pos)
            chunk_end = chunk_start + len(chunk_text) if chunk_start != -1 else None
            
            # Extract page number if available
            page_number = self._extract_page_number(chunk_text)
            
            chunk = TextChunk(
                content=chunk_text.strip(),
                chunk_id=f"{source_doc}_chunk_{i+1}",
                source_doc=source_doc,
                page_number=page_number,
                start_char=chunk_start if chunk_start != -1 else None,
                end_char=chunk_end,
                metadata=metadata or {}
            )
            
            chunks.append(chunk)
            current_pos = chunk_end if chunk_end else current_pos + len(chunk_text)
        
        return chunks
    
    def _chunk_custom(self, text: str, source_doc: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Custom text chunking when LangChain is not available"""
        chunks = []
        
        # Split text into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        current_chunk = ""
        chunk_num = 1
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk = self._create_chunk(current_chunk, source_doc, chunk_num, metadata)
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
                chunk_num += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\\n\\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk if not empty
        if current_chunk.strip():
            chunk = self._create_chunk(current_chunk, source_doc, chunk_num, metadata)
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        # Split by double newlines, but also handle page markers
        paragraphs = []
        
        # First split by page markers
        page_sections = re.split(r'\\[Page \\d+\\]', text)
        
        for section in page_sections:
            if not section.strip():
                continue
            
            # Split section into paragraphs
            section_paragraphs = [p.strip() for p in section.split('\\n\\n') if p.strip()]
            paragraphs.extend(section_paragraphs)
        
        return paragraphs
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to find a good break point (sentence ending)
        overlap_start = len(text) - self.chunk_overlap
        sentence_endings = ['. ', '! ', '? ', '\\n']
        
        best_start = overlap_start
        for ending in sentence_endings:
            pos = text.rfind(ending, overlap_start)
            if pos > best_start:
                best_start = pos + len(ending)
                break
        
        return text[best_start:]
    
    def _create_chunk(self, content: str, source_doc: str, chunk_num: int, metadata: Optional[Dict[str, Any]] = None) -> TextChunk:
        """Create a TextChunk object"""
        page_number = self._extract_page_number(content)
        
        return TextChunk(
            content=content.strip(),
            chunk_id=f"{source_doc}_chunk_{chunk_num}",
            source_doc=source_doc,
            page_number=page_number,
            metadata=metadata or {}
        )
    
    def _extract_page_number(self, text: str) -> Optional[int]:
        """Extract page number from text if available"""
        # Look for page markers like [Page 1]
        page_match = re.search(r'\\[Page (\\d+)\\]', text)
        if page_match:
            return int(page_match.group(1))
        return None
    
    def optimize_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """
        Optimize chunks by removing duplicates and very short chunks
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Optimized list of chunks
        """
        if not chunks:
            return chunks
        
        optimized = []
        seen_content = set()
        
        for chunk in chunks:
            # Skip very short chunks (less than 50 characters)
            if len(chunk.content) < 50:
                continue
            
            # Skip duplicate content
            content_hash = hash(chunk.content[:200])  # Use first 200 chars for deduplication
            if content_hash in seen_content:
                continue
            
            seen_content.add(content_hash)
            optimized.append(chunk)
        
        logger.info(f"Optimized {len(chunks)} chunks to {len(optimized)} chunks")
        return optimized
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Get statistics about the chunks
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_characters': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0
            }
        
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        total_chars = sum(chunk_sizes)
        
        return {
            'total_chunks': len(chunks),
            'total_characters': total_chars,
            'avg_chunk_size': total_chars // len(chunks),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'documents': len(set(chunk.source_doc for chunk in chunks))
        }