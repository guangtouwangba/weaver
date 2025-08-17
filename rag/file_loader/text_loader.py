"""
文本文件加载器实现
支持TXT、MD等纯文本格式
"""

import time
from pathlib import Path
from typing import List, Iterator
import aiofiles

from .base import BaseFileLoader, DocumentLoadError, UnsupportedFormatError
from ..models import Document, ProcessingResult, DocumentStatus


class TextFileLoader(BaseFileLoader):
    """文本文件加载器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.encoding = self.config.get('encoding', 'utf-8')
        self.fallback_encodings = self.config.get('fallback_encodings', ['gbk', 'gb2312', 'latin1'])
    
    def supported_formats(self) -> List[str]:
        """支持的文件格式"""
        return ['.txt', '.md', '.markdown', '.text']
    
    async def load(self, file_path: str) -> Document:
        """
        加载文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Document: 文档对象
        """
        start_time = time.time()
        
        # Validate file
        errors = self.validate_file(file_path)
        if errors:
            raise DocumentLoadError(f"File validation failed: {'; '.join(errors)}")
        
        try:
            # Read file content
            content = await self._read_file_with_encoding(file_path)
            
            # Extract metadata
            metadata = await self.extract_metadata(file_path)
            
            # Create document object
            document = Document(
                title=Path(file_path).stem,
                content=content,
                source_path=file_path,
                file_type=Path(file_path).suffix.lower(),
                file_size=metadata['file_size'],
                metadata={
                    **metadata,
                    'encoding': self.encoding,
                    'loading_time_ms': (time.time() - start_time) * 1000,
                    'loader_type': self.__class__.__name__
                },
                status=DocumentStatus.COMPLETED
            )
            
            return document
            
        except Exception as e:
            raise DocumentLoadError(f"Failed to load file {file_path}: {str(e)}")
    
    async def load_batch(self, file_paths: List[str]) -> Iterator[ProcessingResult]:
        """批量加载文件"""
        for file_path in file_paths:
            start_time = time.time()
            
            try:
                document = await self.load(file_path)
                processing_time = (time.time() - start_time) * 1000
                
                yield ProcessingResult(
                    success=True,
                    message=f"Successfully loaded {file_path}",
                    document_id=document.id,
                    processing_time_ms=processing_time,
                    metadata={'document': document}
                )
                
            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                
                yield ProcessingResult(
                    success=False,
                    message=f"Failed to load {file_path}",
                    errors=[str(e)],
                    processing_time_ms=processing_time,
                    metadata={'file_path': file_path}
                )
    
    async def _read_file_with_encoding(self, file_path: str) -> str:
        """
        使用多种编码尝试读取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容
        """
                    # First try default encoding
        try:
            async with aiofiles.open(file_path, 'r', encoding=self.encoding) as f:
                return await f.read()
        except UnicodeDecodeError:
            pass
        
                    # Try alternative encodings
        for encoding in self.fallback_encodings:
            try:
                async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                    content = await f.read()
                    self.encoding = encoding  # Update current encoding
                    return content
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, raise exception
        raise DocumentLoadError(f"Could not decode file {file_path} with any supported encoding")
    
    def _extract_text_features(self, content: str) -> dict:
        """提取文本特征"""
        lines = content.split('\n')
        words = content.split()
        
        return {
            'line_count': len(lines),
            'word_count': len(words),
            'character_count': len(content),
            'paragraph_count': len([line for line in lines if line.strip()]),
            'average_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0,
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0
        }


class MarkdownLoader(TextFileLoader):
    """Markdown文件加载器"""
    
    def supported_formats(self) -> List[str]:
        """支持的文件格式"""
        return ['.md', '.markdown', '.mdown', '.mkd']
    
    async def load(self, file_path: str) -> Document:
        """加载Markdown文件并提取结构信息"""
        document = await super().load(file_path)
        
        # Extract Markdown-specific metadata
        md_metadata = self._extract_markdown_features(document.content)
        document.metadata.update(md_metadata)
        
        return document
    
    def _extract_markdown_features(self, content: str) -> dict:
        """提取Markdown文档特征"""
        lines = content.split('\n')
        
        features = {
            'headers': [],
            'code_blocks': 0,
            'links': 0,
            'images': 0,
            'tables': 0,
            'lists': 0
        }
        
        in_code_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detect headers
            if line_stripped.startswith('#'):
                level = len(line_stripped) - len(line_stripped.lstrip('#'))
                title = line_stripped.lstrip('#').strip()
                features['headers'].append({'level': level, 'title': title})
            
            # Detect code blocks
            if line_stripped.startswith('```'):
                if in_code_block:
                    features['code_blocks'] += 1
                in_code_block = not in_code_block
            
            # Detect links and images
            if '[' in line and ']' in line and '(' in line and ')' in line:
                if line_stripped.startswith('!['):
                    features['images'] += line.count('![')
                else:
                    features['links'] += line.count('[')
            
            # Detect tables
            if '|' in line and not in_code_block:
                features['tables'] += 1
            
            # Detect lists
            if line_stripped.startswith(('-', '*', '+')) or (line_stripped and line_stripped[0].isdigit() and '.' in line_stripped[:5]):
                features['lists'] += 1
        
        return features