#!/usr/bin/env python3
"""
PDF text extraction for RAG module
Handles extraction of text content from PDF files (local or OSS)
"""

import logging
import tempfile
import os
from typing import Optional, Dict, Any
import sys

# Add backend to path for importing storage manager
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extracts text content from PDF files"""
    
    def __init__(self, storage_manager=None):
        self.storage_manager = storage_manager
        
        if not PYPDF2_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            raise ImportError("Neither PyPDF2 nor pdfplumber is available. Install with: pip install PyPDF2 pdfplumber")
        
        # Prefer pdfplumber for better text extraction
        self.preferred_method = 'pdfplumber' if PDFPLUMBER_AVAILABLE else 'pypdf2'
        
        logger.info(f"PDF extractor initialized with method: {self.preferred_method}")
    
    def extract_text_from_path(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF file path (local or OSS)
        
        Args:
            pdf_path: Path to PDF file (local path or OSS key)
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Check if it's an OSS path (starts with 'papers/')
            if pdf_path.startswith('papers/'):
                return self._extract_from_oss(pdf_path)
            else:
                return self._extract_from_local(pdf_path)
                
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return None
    
    def _extract_from_local(self, local_path: str) -> Optional[str]:
        """Extract text from local PDF file"""
        if not os.path.exists(local_path):
            logger.error(f"Local PDF file not found: {local_path}")
            return None
        
        if self.preferred_method == 'pdfplumber':
            return self._extract_with_pdfplumber(local_path)
        else:
            return self._extract_with_pypdf2(local_path)
    
    def _extract_from_oss(self, oss_key: str) -> Optional[str]:
        """Extract text from OSS-stored PDF file"""
        if not self.storage_manager:
            logger.error("Storage manager not available for OSS file access")
            return None
        
        try:
            # Download OSS file to temporary location
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Download from OSS
            success = self.storage_manager.oss_client.download_file(oss_key, temp_path)
            
            if not success:
                logger.error(f"Failed to download OSS file: {oss_key}")
                return None
            
            # Extract text from temporary file
            text = self._extract_from_local(temp_path)
            
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from OSS file {oss_key}: {e}")
            return None
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> Optional[str]:
        """Extract text using pdfplumber (preferred method)"""
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                logger.debug(f"Processing PDF with {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        
                        if page_text:
                            # Clean and add page text
                            cleaned_text = self._clean_text(page_text)
                            if cleaned_text.strip():
                                text_content.append(f"[Page {page_num}]\\n{cleaned_text}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        continue
            
            if text_content:
                full_text = "\\n\\n".join(text_content)
                logger.info(f"Extracted {len(full_text)} characters from PDF")
                return full_text
            else:
                logger.warning("No text content extracted from PDF")
                return None
                
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return None
    
    def _extract_with_pypdf2(self, pdf_path: str) -> Optional[str]:
        """Extract text using PyPDF2 (fallback method)"""
        try:
            text_content = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                logger.debug(f"Processing PDF with {len(pdf_reader.pages)} pages")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        
                        if page_text:
                            # Clean and add page text
                            cleaned_text = self._clean_text(page_text)
                            if cleaned_text.strip():
                                text_content.append(f"[Page {page_num}]\\n{cleaned_text}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        continue
            
            if text_content:
                full_text = "\\n\\n".join(text_content)
                logger.info(f"Extracted {len(full_text)} characters from PDF")
                return full_text
            else:
                logger.warning("No text content extracted from PDF")
                return None
                
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = []
        for line in text.split('\\n'):
            line = line.strip()
            if line:
                lines.append(line)
        
        # Join lines with single spaces, but preserve paragraph breaks
        cleaned_lines = []
        for i, line in enumerate(lines):
            cleaned_lines.append(line)
            
            # Add paragraph break if line ends with period and next line starts with capital
            if (i < len(lines) - 1 and 
                line.endswith('.') and 
                len(lines[i + 1]) > 0 and 
                lines[i + 1][0].isupper()):
                cleaned_lines.append("")
        
        return "\\n".join(cleaned_lines)
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        metadata = {
            'pages': 0,
            'title': None,
            'author': None,
            'subject': None,
            'creator': None,
            'creation_date': None
        }
        
        try:
            if pdf_path.startswith('papers/') and self.storage_manager:
                # Handle OSS file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                success = self.storage_manager.oss_client.download_file(pdf_path, temp_path)
                if success:
                    metadata = self._extract_metadata(temp_path)
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            else:
                # Handle local file
                metadata = self._extract_metadata(pdf_path)
                
        except Exception as e:
            logger.error(f"Failed to extract PDF metadata from {pdf_path}: {e}")
        
        return metadata
    
    def _extract_metadata(self, local_path: str) -> Dict[str, Any]:
        """Extract metadata from local PDF file"""
        metadata = {
            'pages': 0,
            'title': None,
            'author': None,
            'subject': None,
            'creator': None,
            'creation_date': None
        }
        
        try:
            if PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(local_path) as pdf:
                    metadata['pages'] = len(pdf.pages)
                    if pdf.metadata:
                        metadata.update({
                            'title': pdf.metadata.get('Title'),
                            'author': pdf.metadata.get('Author'),
                            'subject': pdf.metadata.get('Subject'),
                            'creator': pdf.metadata.get('Creator'),
                            'creation_date': pdf.metadata.get('CreationDate')
                        })
            
            elif PYPDF2_AVAILABLE:
                with open(local_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata['pages'] = len(pdf_reader.pages)
                    
                    if pdf_reader.metadata:
                        metadata.update({
                            'title': pdf_reader.metadata.get('/Title'),
                            'author': pdf_reader.metadata.get('/Author'),
                            'subject': pdf_reader.metadata.get('/Subject'),
                            'creator': pdf_reader.metadata.get('/Creator'),
                            'creation_date': pdf_reader.metadata.get('/CreationDate')
                        })
        
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
        
        return metadata