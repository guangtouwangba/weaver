"""
向量存储基础接口
支持文档块的向量化存储和相似度检索
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import asyncio

from ..models import DocumentChunk, QueryResult, SearchFilter


class BaseVectorStore(ABC):
    """向量存储基类"""
    
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
    async def search(self, query_embedding: List[float], 
                    top_k: int = 10, 
                    filter_criteria: Optional[SearchFilter] = None) -> List[Tuple[DocumentChunk, float]]:
        """
        向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回的结果数量
            filter_criteria: 过滤条件
            
        Returns:
            List[Tuple[DocumentChunk, float]]: (文档块, 相似度分数)的列表
        """
        pass
    
    @abstractmethod
    async def search_by_text(self, query_text: str, 
                            top_k: int = 10,
                            filter_criteria: Optional[SearchFilter] = None) -> List[Tuple[DocumentChunk, float]]:
        """
        基于文本查询的搜索
        
        Args:
            query_text: 查询文本
            top_k: 返回的结果数量
            filter_criteria: 过滤条件
            
        Returns:
            List[Tuple[DocumentChunk, float]]: (文档块, 相似度分数)的列表
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
    
    async def batch_search(self, queries: List[str], 
                          top_k: int = 10,
                          filter_criteria: Optional[SearchFilter] = None) -> List[List[Tuple[DocumentChunk, float]]]:
        """
        批量搜索
        
        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
            filter_criteria: 过滤条件
            
        Returns:
            List[List[Tuple[DocumentChunk, float]]]: 每个查询的结果列表
        """
        results = []
        for query in queries:
            result = await self.search_by_text(query, top_k, filter_criteria)
            results.append(result)
        return results
    
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
        
        # 检查维度一致性
        first_dim = len(embeddings[0]) if embeddings else 0
        for i, embedding in enumerate(embeddings):
            if len(embedding) != first_dim:
                errors.append(f"Embedding {i} has dimension {len(embedding)}, expected {first_dim}")
        
        # 检查数值有效性
        for i, embedding in enumerate(embeddings):
            for j, value in enumerate(embedding):
                if not isinstance(value, (int, float)):
                    errors.append(f"Embedding {i}, element {j} is not a number: {type(value)}")
                elif not (-1e10 < value < 1e10):  # 检查是否为合理的数值范围
                    errors.append(f"Embedding {i}, element {j} has invalid value: {value}")
        
        return errors


class InMemoryVectorStore(BaseVectorStore):
    """内存向量存储实现（用于测试和小规模应用）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.chunks: Dict[str, DocumentChunk] = {}
        self.embeddings: Dict[str, List[float]] = {}
    
    async def store_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """存储文档块到内存"""
        stored_ids = []
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            if chunk.embedding:
                self.embeddings[chunk.id] = chunk.embedding
            stored_ids.append(chunk.id)
        return stored_ids
    
    async def search(self, query_embedding: List[float], 
                    top_k: int = 10, 
                    filter_criteria: Optional[SearchFilter] = None) -> List[Tuple[DocumentChunk, float]]:
        """内存中的向量相似度搜索"""
        results = []
        
        for chunk_id, embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            chunk = self.chunks[chunk_id]
            results.append((chunk, similarity))
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 应用过滤器
        if filter_criteria:
            results = [(chunk, score) for chunk, score in results 
                      if chunk in filter_criteria.apply_to_chunks([chunk for chunk, _ in results])]
        
        return results[:top_k]
    
    async def search_by_text(self, query_text: str, 
                            top_k: int = 10,
                            filter_criteria: Optional[SearchFilter] = None) -> List[Tuple[DocumentChunk, float]]:
        """简单的文本匹配搜索（实际应用中应该使用嵌入）"""
        results = []
        query_lower = query_text.lower()
        
        for chunk in self.chunks.values():
            # 简单的文本匹配计分
            content_lower = chunk.content.lower()
            score = 0.0
            
            # 完全匹配
            if query_lower in content_lower:
                score += 1.0
            
            # 词语匹配
            query_words = query_lower.split()
            content_words = content_lower.split()
            matched_words = sum(1 for word in query_words if word in content_words)
            score += matched_words / len(query_words) if query_words else 0
            
            if score > 0:
                results.append((chunk, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 应用过滤器
        if filter_criteria:
            results = [(chunk, score) for chunk, score in results 
                      if chunk in filter_criteria.apply_to_chunks([chunk for chunk, _ in results])]
        
        return results[:top_k]
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """删除指定块"""
        try:
            for chunk_id in chunk_ids:
                self.chunks.pop(chunk_id, None)
                self.embeddings.pop(chunk_id, None)
            return True
        except Exception:
            return False
    
    async def delete_by_document(self, document_id: str) -> int:
        """删除文档的所有块"""
        chunks_to_delete = [chunk_id for chunk_id, chunk in self.chunks.items() 
                           if chunk.document_id == document_id]
        
        await self.delete_chunks(chunks_to_delete)
        return len(chunks_to_delete)
    
    async def update_chunk(self, chunk_id: str, chunk: DocumentChunk) -> bool:
        """更新块"""
        if chunk_id in self.chunks:
            self.chunks[chunk_id] = chunk
            if chunk.embedding:
                self.embeddings[chunk_id] = chunk.embedding
            return True
        return False
    
    async def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """获取块"""
        return self.chunks.get(chunk_id)
    
    async def count_chunks(self, document_id: Optional[str] = None) -> int:
        """统计块数量"""
        if document_id is None:
            return len(self.chunks)
        
        return sum(1 for chunk in self.chunks.values() 
                  if chunk.document_id == document_id)
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        return {
            'total_chunks': len(self.chunks),
            'total_embeddings': len(self.embeddings),
            'embedding_dimension': len(next(iter(self.embeddings.values()))) if self.embeddings else 0,
            'collection_name': self.collection_name
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import math
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


# 异常类定义
class VectorStoreError(Exception):
    """向量存储错误"""
    pass


class EmbeddingDimensionError(VectorStoreError):
    """嵌入维度错误"""
    pass