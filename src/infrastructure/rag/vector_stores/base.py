"""
向量存储基础接口
专注于文档块的向量存储和相似度检索
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import asyncio

from ..models import DocumentChunk, SearchFilter


class BaseVectorStore(ABC):
    """向量存储基类 - 专注向量存储和检索"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化向量存储
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.collection_name = self.config.get('collection_name', 'default')
    
    @abstractmethod
    async def store_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """
        存储文档块的向量表示
        
        Args:
            chunks: 要存储的文档块列表
            
        Returns:
            List[str]: 存储的向量ID列表
            
        Raises:
            VectorStoreError: 存储错误
        """
        pass
    
    @abstractmethod
    async def search_by_vector(self, query_embedding: List[float], 
                              top_k: int = 10, 
                              document_ids: Optional[List[str]] = None) -> List[Tuple[DocumentChunk, float]]:
        """
        向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回的结果数量
            document_ids: 限制搜索的文档ID列表（可选）
            
        Returns:
            List[Tuple[DocumentChunk, float]]: (文档块, 相似度分数)的列表
        """
        pass
    
    @abstractmethod
    async def search_by_text(self, query_text: str, 
                            top_k: int = 10,
                            document_ids: Optional[List[str]] = None) -> List[Tuple[DocumentChunk, float]]:
        """
        基于文本查询的搜索（通过文本嵌入）
        
        Args:
            query_text: 查询文本
            top_k: 返回的结果数量
            document_ids: 限制搜索的文档ID列表（可选）
            
        Returns:
            List[Tuple[DocumentChunk, float]]: (文档块, 相似度分数)的列表
        """
        pass
    
    @abstractmethod
    async def get_chunks_by_document(self, document_id: str) -> List[DocumentChunk]:
        """
        获取指定文档的所有块
        
        Args:
            document_id: 文档ID
            
        Returns:
            List[DocumentChunk]: 文档块列表
        """
        pass
    
    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """
        根据ID获取文档块
        
        Args:
            chunk_id: 块ID
            
        Returns:
            Optional[DocumentChunk]: 文档块，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """
        删除指定的文档块
        
        Args:
            chunk_ids: 要删除的块ID列表
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def delete_by_document(self, document_id: str) -> int:
        """
        删除指定文档的所有块
        
        Args:
            document_id: 文档ID
            
        Returns:
            int: 删除的块数量
        """
        pass
    
    @abstractmethod
    async def update_chunk(self, chunk_id: str, chunk: DocumentChunk) -> bool:
        """
        更新文档块
        
        Args:
            chunk_id: 块ID
            chunk: 新的文档块数据
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def count_chunks(self, document_id: Optional[str] = None) -> int:
        """
        统计文档块数量
        
        Args:
            document_id: 文档ID，如果为None则统计所有块
            
        Returns:
            int: 块数量
        """
        pass
    
    @abstractmethod
    async def get_collection_info(self) -> Dict[str, Any]:
        """
        获取集合信息
        
        Returns:
            Dict[str, Any]: 集合信息（如大小、维度等）
        """
        pass
    
            # Batch operations
    async def batch_search_by_text(self, queries: List[str], 
                                  top_k: int = 10,
                                  document_ids: Optional[List[str]] = None) -> List[List[Tuple[DocumentChunk, float]]]:
        """
        批量文本搜索
        
        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
            document_ids: 限制搜索的文档ID列表（可选）
            
        Returns:
            List[List[Tuple[DocumentChunk, float]]]: 每个查询的结果列表
        """
        results = []
        for query in queries:
            result = await self.search_by_text(query, top_k, document_ids)
            results.append(result)
        return results
    
    async def get_chunks_by_documents(self, document_ids: List[str]) -> Dict[str, List[DocumentChunk]]:
        """
        获取多个文档的所有块
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            Dict[str, List[DocumentChunk]]: 文档ID到块列表的映射
        """
        result = {}
        for doc_id in document_ids:
            chunks = await self.get_chunks_by_document(doc_id)
            result[doc_id] = chunks
        return result
    
    # Utility methods
    def validate_embeddings(self, embeddings: List[List[float]]) -> List[str]:
        """
        验证嵌入向量
        
        Args:
            embeddings: 嵌入向量列表
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        if not embeddings:
            errors.append("Embeddings list is empty")
            return errors
        
        # Check dimension consistency
        first_dim = len(embeddings[0]) if embeddings else 0
        for i, embedding in enumerate(embeddings):
            if len(embedding) != first_dim:
                errors.append(f"Embedding {i} has dimension {len(embedding)}, expected {first_dim}")
        
        # Check numerical validity
        for i, embedding in enumerate(embeddings):
            for j, value in enumerate(embedding):
                if not isinstance(value, (int, float)):
                    errors.append(f"Embedding {i}, element {j} is not a number: {type(value)}")
                elif not (-1e10 < value < 1e10):  # Check if value is within reasonable range
                    errors.append(f"Embedding {i}, element {j} has invalid value: {value}")
        
        return errors


