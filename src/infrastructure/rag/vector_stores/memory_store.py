"""
内存向量存储实现
用于测试和小规模应用
"""

import math
from typing import List, Optional, Dict, Any, Tuple

from ..models import DocumentChunk
from .base import BaseVectorStore


class InMemoryVectorStore(BaseVectorStore):
    """内存向量存储实现（用于测试和小规模应用）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.chunks: Dict[str, DocumentChunk] = {}
        self.embeddings: Dict[str, List[float]] = {}
        # Index chunks by document ID
        self.document_chunks: Dict[str, List[str]] = {}  # document_id -> [chunk_ids]
    
    async def store_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """存储文档块到内存"""
        stored_ids = []
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            if chunk.embedding:
                self.embeddings[chunk.id] = chunk.embedding
            
            # Update document index
            if chunk.document_id not in self.document_chunks:
                self.document_chunks[chunk.document_id] = []
            if chunk.id not in self.document_chunks[chunk.document_id]:
                self.document_chunks[chunk.document_id].append(chunk.id)
            
            stored_ids.append(chunk.id)
        return stored_ids
    
    async def search_by_vector(self, query_embedding: List[float], 
                              top_k: int = 10, 
                              document_ids: Optional[List[str]] = None) -> List[Tuple[DocumentChunk, float]]:
        """内存中的向量相似度搜索"""
        results = []
        
        # Determine search scope
        search_chunk_ids = []
        if document_ids:
            for doc_id in document_ids:
                search_chunk_ids.extend(self.document_chunks.get(doc_id, []))
        else:
            search_chunk_ids = list(self.embeddings.keys())
        
        for chunk_id in search_chunk_ids:
            if chunk_id in self.embeddings and chunk_id in self.chunks:
                embedding = self.embeddings[chunk_id]
                similarity = self._cosine_similarity(query_embedding, embedding)
                chunk = self.chunks[chunk_id]
                results.append((chunk, similarity))
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    async def search_by_text(self, query_text: str, 
                            top_k: int = 10,
                            document_ids: Optional[List[str]] = None) -> List[Tuple[DocumentChunk, float]]:
        """简单的文本匹配搜索（实际应用中应该使用嵌入）"""
        results = []
        query_lower = query_text.lower()
        
        # Determine search scope
        search_chunks = []
        if document_ids:
            for doc_id in document_ids:
                chunk_ids = self.document_chunks.get(doc_id, [])
                for chunk_id in chunk_ids:
                    if chunk_id in self.chunks:
                        search_chunks.append(self.chunks[chunk_id])
        else:
            search_chunks = list(self.chunks.values())
        
        for chunk in search_chunks:
            # Simple text matching scoring
            content_lower = chunk.content.lower()
            score = 0.0
            
            # Exact match
            if query_lower in content_lower:
                score += 1.0
            
            # Word matching
            query_words = query_lower.split()
            content_words = content_lower.split()
            matched_words = sum(1 for word in query_words if word in content_words)
            score += matched_words / len(query_words) if query_words else 0
            
            if score > 0:
                results.append((chunk, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    async def get_chunks_by_document(self, document_id: str) -> List[DocumentChunk]:
        """获取指定文档的所有块"""
        chunk_ids = self.document_chunks.get(document_id, [])
        chunks = []
        for chunk_id in chunk_ids:
            if chunk_id in self.chunks:
                chunks.append(self.chunks[chunk_id])
        
        # Sort by chunk_index
        chunks.sort(key=lambda x: x.chunk_index)
        return chunks
    
    async def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """获取块"""
        return self.chunks.get(chunk_id)
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """删除指定块"""
        try:
            for chunk_id in chunk_ids:
                # Remove from main storage
                chunk = self.chunks.pop(chunk_id, None)
                self.embeddings.pop(chunk_id, None)
                
                # Remove from document index
                if chunk and chunk.document_id in self.document_chunks:
                    if chunk_id in self.document_chunks[chunk.document_id]:
                        self.document_chunks[chunk.document_id].remove(chunk_id)
                    
                    # If document has no chunks, delete document index
                    if not self.document_chunks[chunk.document_id]:
                        del self.document_chunks[chunk.document_id]
            return True
        except Exception:
            return False
    
    async def delete_by_document(self, document_id: str) -> int:
        """删除文档的所有块"""
        chunk_ids = self.document_chunks.get(document_id, []).copy()
        
        if chunk_ids:
            await self.delete_chunks(chunk_ids)
        
        return len(chunk_ids)
    
    async def update_chunk(self, chunk_id: str, chunk: DocumentChunk) -> bool:
        """更新块"""
        if chunk_id in self.chunks:
            old_chunk = self.chunks[chunk_id]
            
            # 更新主存储
            self.chunks[chunk_id] = chunk
            if chunk.embedding:
                self.embeddings[chunk_id] = chunk.embedding
            
            # 如果文档ID改变了，更新索引
            if old_chunk.document_id != chunk.document_id:
                # 从旧文档索引中删除
                if old_chunk.document_id in self.document_chunks:
                    if chunk_id in self.document_chunks[old_chunk.document_id]:
                        self.document_chunks[old_chunk.document_id].remove(chunk_id)
                    if not self.document_chunks[old_chunk.document_id]:
                        del self.document_chunks[old_chunk.document_id]
                
                # 添加到新文档索引
                if chunk.document_id not in self.document_chunks:
                    self.document_chunks[chunk.document_id] = []
                if chunk_id not in self.document_chunks[chunk.document_id]:
                    self.document_chunks[chunk.document_id].append(chunk_id)
            
            return True
        return False
    
    async def count_chunks(self, document_id: Optional[str] = None) -> int:
        """统计块数量"""
        if document_id is None:
            return len(self.chunks)
        
        return len(self.document_chunks.get(document_id, []))
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        return {
            'total_chunks': len(self.chunks),
            'total_embeddings': len(self.embeddings),
            'total_documents_with_chunks': len(self.document_chunks),
            'embedding_dimension': len(next(iter(self.embeddings.values()))) if self.embeddings else 0,
            'collection_name': self.collection_name
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)