"""
内存文档仓储实现
用于测试和小规模应用
"""

from typing import List, Optional, Dict, Any

from ..models import Document, DocumentStatus, SearchFilter
from .base import BaseDocumentRepository


class InMemoryDocumentRepository(BaseDocumentRepository):
    """内存文档仓储实现"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.documents: Dict[str, Document] = {}
    
    async def save(self, document: Document) -> str:
        """保存文档到内存"""
        self.documents[document.id] = document
        return document.id
    
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """从内存查找文档"""
        return self.documents.get(document_id)
    
    async def find_by_status(self, status: DocumentStatus) -> List[Document]:
        """根据状态查找文档"""
        return [doc for doc in self.documents.values() if doc.status == status]
    
    async def search(self, 
                    query: str = "",
                    filters: Optional[SearchFilter] = None,
                    limit: int = 10,
                    offset: int = 0) -> List[Document]:
        """在内存中搜索文档"""
        results = list(self.documents.values())
        
        # 应用文本查询过滤
        if query:
            query_lower = query.lower()
            filtered_results = []
            for doc in results:
                if (query_lower in doc.title.lower() or 
                    query_lower in str(doc.metadata).lower()):
                    filtered_results.append(doc)
            results = filtered_results
        
        # 应用其他过滤器
        if filters:
            if filters.document_ids:
                results = [doc for doc in results if doc.id in filters.document_ids]
            
            if filters.file_types:
                results = [doc for doc in results if doc.file_type in filters.file_types]
            
            if filters.created_after:
                results = [doc for doc in results if doc.created_at >= filters.created_after]
            
            if filters.created_before:
                results = [doc for doc in results if doc.created_at <= filters.created_before]
        
        # 分页
        return results[offset:offset + limit]
    
    async def update_status(self, document_id: str, status: DocumentStatus) -> bool:
        """更新文档状态"""
        if document_id in self.documents:
            self.documents[document_id].update_status(status)
            return True
        return False
    
    async def delete(self, document_id: str) -> bool:
        """删除文档"""
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    async def exists(self, document_id: str) -> bool:
        """检查文档是否存在"""
        return document_id in self.documents
    
    async def count(self, filters: Optional[SearchFilter] = None) -> int:
        """统计文档数量"""
        if filters is None:
            return len(self.documents)
        
        results = await self.search("", filters, limit=1000000)  # 大数值获取所有结果
        return len(results)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        total_docs = len(self.documents)
        status_counts = {}
        file_type_counts = {}
        total_size = 0
        
        for doc in self.documents.values():
            # 状态统计
            status_counts[doc.status.value] = status_counts.get(doc.status.value, 0) + 1
            
            # 文件类型统计
            file_type_counts[doc.file_type] = file_type_counts.get(doc.file_type, 0) + 1
            
            # 文件大小统计
            total_size += doc.file_size
        
        return {
            'total_documents': total_docs,
            'status_distribution': status_counts,
            'file_type_distribution': file_type_counts,
            'total_size_bytes': total_size,
            'average_size_bytes': total_size / total_docs if total_docs > 0 else 0
        }