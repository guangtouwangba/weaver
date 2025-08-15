"""
文档分割器基础接口
支持多种分割策略的智能文档分块
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio

from ..models import Document, DocumentChunk


class BaseDocumentSplitter(ABC):
    """文档分割器基类"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100, **kwargs):
        """
        初始化文档分割器
        
        Args:
            chunk_size: 块大小（字符数）
            chunk_overlap: 重叠大小（字符数）
            **kwargs: 其他配置参数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.config = kwargs
        
        # 验证参数
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
    
    @abstractmethod
    async def split(self, document: Document) -> List[DocumentChunk]:
        """
        分割文档为块
        
        Args:
            document: 要分割的文档对象
            
        Returns:
            List[DocumentChunk]: 分割后的文档块列表
        """
        pass
    
    def estimate_chunk_count(self, document: Document) -> int:
        """
        估算分割后的块数量
        
        Args:
            document: 文档对象
            
        Returns:
            int: 估算的块数量
        """
        if not document.content:
            return 0
        
        content_length = len(document.content)
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        
        if effective_chunk_size <= 0:
            return 1
        
        return max(1, (content_length + effective_chunk_size - 1) // effective_chunk_size)
    
    def validate_document(self, document: Document) -> List[str]:
        """
        验证文档是否可以分割
        
        Args:
            document: 文档对象
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        if not document.content:
            errors.append("Document content is empty")
        
        if len(document.content) < self.chunk_size:
            errors.append(f"Document is too short for splitting (length: {len(document.content)}, chunk_size: {self.chunk_size})")
        
        return errors
    
    def create_chunk(self, document: Document, content: str, 
                    chunk_index: int, start_offset: int, end_offset: int) -> DocumentChunk:
        """
        创建文档块对象
        
        Args:
            document: 原始文档
            content: 块内容
            chunk_index: 块索引
            start_offset: 开始位置
            end_offset: 结束位置
            
        Returns:
            DocumentChunk: 文档块对象
        """
        return DocumentChunk(
            document_id=document.id,
            content=content.strip(),
            chunk_index=chunk_index,
            start_offset=start_offset,
            end_offset=end_offset,
            metadata={
                'document_title': document.title,
                'document_source': document.source_path,
                'splitter_type': self.__class__.__name__,
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
        )
    
    async def split_with_metadata(self, document: Document) -> Dict[str, Any]:
        """
        分割文档并返回详细信息
        
        Args:
            document: 文档对象
            
        Returns:
            Dict[str, Any]: 包含分割结果和元数据的字典
        """
        import time
        start_time = time.time()
        
        chunks = await self.split(document)
        
        processing_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        return {
            'chunks': chunks,
            'chunk_count': len(chunks),
            'processing_time_ms': processing_time,
            'original_length': len(document.content),
            'average_chunk_length': sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0,
            'split_strategy': self.__class__.__name__,
            'config': {
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                **self.config
            }
        }


class FixedSizeSplitter(BaseDocumentSplitter):
    """固定大小分割器"""
    
    async def split(self, document: Document) -> List[DocumentChunk]:
        """按固定大小分割文档"""
        if not document.content:
            return []
        
        chunks = []
        content = document.content
        chunk_index = 0
        
        start = 0
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            
            # 如果不是最后一块，尝试在合适的位置断开
            if end < len(content):
                # 寻找最近的句号、换行符或空格
                for i in range(end, max(start, end - 100), -1):
                    if content[i] in '.。\n ':
                        end = i + 1
                        break
            
            chunk_content = content[start:end]
            if chunk_content.strip():
                chunk = self.create_chunk(
                    document=document,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_offset=start,
                    end_offset=end
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # 计算下一个块的开始位置（考虑重叠）
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks


class SentenceSplitter(BaseDocumentSplitter):
    """句子边界分割器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100, **kwargs):
        super().__init__(chunk_size, chunk_overlap, **kwargs)
        self.sentence_separators = kwargs.get('sentence_separators', ['.', '。', '!', '！', '?', '？', '\n\n'])
    
    async def split(self, document: Document) -> List[DocumentChunk]:
        """按句子边界分割文档"""
        if not document.content:
            return []
        
        # 简单的句子分割实现
        sentences = self._split_into_sentences(document.content)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        start_offset = 0
        
        for sentence in sentences:
            # 检查添加这个句子是否会超过大小限制
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # 创建当前块
                chunk = self.create_chunk(
                    document=document,
                    content=current_chunk,
                    chunk_index=chunk_index,
                    start_offset=start_offset,
                    end_offset=start_offset + len(current_chunk)
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 处理重叠
                if self.chunk_overlap > 0:
                    overlap_content = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_content + sentence
                    start_offset += len(current_chunk) - len(overlap_content) - len(sentence)
                else:
                    current_chunk = sentence
                    start_offset += len(current_chunk) - len(sentence)
            else:
                current_chunk += sentence
        
        # 添加最后一个块
        if current_chunk.strip():
            chunk = self.create_chunk(
                document=document,
                content=current_chunk,
                chunk_index=chunk_index,
                start_offset=start_offset,
                end_offset=start_offset + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """简单的句子分割实现"""
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in self.sentence_separators:
                if current_sentence.strip():
                    sentences.append(current_sentence)
                current_sentence = ""
        
        # 添加最后一个句子
        if current_sentence.strip():
            sentences.append(current_sentence)
        
        return sentences