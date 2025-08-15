"""
SQLAlchemy 数据库仓储实现
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Document as DBDocument, DocumentChunk as DBDocumentChunk, QueryHistory as DBQueryHistory
from ..rag.models import Document, DocumentChunk, DocumentStatus, SearchFilter
from ..rag.document_repository.base import BaseDocumentRepository
from ..rag.document_repository.exceptions import DocumentRepositoryError, DocumentNotFoundError


class SQLAlchemyDocumentRepository(BaseDocumentRepository):
    """基于SQLAlchemy的文档仓储实现"""
    
    def __init__(self, session: Session, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session = session
    
    def _db_to_domain(self, db_doc: DBDocument) -> Document:
        """将数据库模型转换为领域模型"""
        return Document(
            id=db_doc.id,
            title=db_doc.title,
            content=db_doc.content or "",
            file_path=db_doc.file_path or "",
            file_type=db_doc.file_type or "unknown",
            file_size=db_doc.file_size or 0,
            status=DocumentStatus(db_doc.status),
            metadata=db_doc.metadata or {},
            created_at=db_doc.created_at,
            updated_at=db_doc.updated_at
        )
    
    def _domain_to_db(self, domain_doc: Document) -> DBDocument:
        """将领域模型转换为数据库模型"""
        return DBDocument(
            id=domain_doc.id,
            title=domain_doc.title,
            content=domain_doc.content,
            file_path=domain_doc.file_path,
            file_type=domain_doc.file_type,
            file_size=domain_doc.file_size,
            status=domain_doc.status.value,
            metadata=domain_doc.metadata,
            created_at=domain_doc.created_at,
            updated_at=domain_doc.updated_at
        )
    
    async def save(self, document: Document) -> str:
        """保存文档"""
        try:
            # 检查是否已存在
            existing = self.session.query(DBDocument).filter(DBDocument.id == document.id).first()
            
            if existing:
                # 更新现有文档
                for key, value in self._domain_to_db(document).__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
                db_doc = existing
            else:
                # 创建新文档
                db_doc = self._domain_to_db(document)
                self.session.add(db_doc)
            
            self.session.commit()
            return db_doc.id
            
        except Exception as e:
            self.session.rollback()
            raise DocumentRepositoryError(f"Failed to save document: {str(e)}")
    
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """根据ID查找文档"""
        try:
            db_doc = self.session.query(DBDocument).filter(DBDocument.id == document_id).first()
            return self._db_to_domain(db_doc) if db_doc else None
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to find document by ID: {str(e)}")
    
    async def find_by_status(self, status: DocumentStatus) -> List[Document]:
        """根据状态查找文档"""
        try:
            db_docs = self.session.query(DBDocument).filter(DBDocument.status == status.value).all()
            return [self._db_to_domain(doc) for doc in db_docs]
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to find documents by status: {str(e)}")
    
    async def search(self, 
                    query: str = "",
                    filters: Optional[SearchFilter] = None,
                    limit: int = 10,
                    offset: int = 0) -> List[Document]:
        """搜索文档"""
        try:
            db_query = self.session.query(DBDocument)
            
            # 应用文本查询
            if query:
                db_query = db_query.filter(
                    or_(
                        DBDocument.title.ilike(f"%{query}%"),
                        DBDocument.content.ilike(f"%{query}%"),
                        DBDocument.metadata.astext.ilike(f"%{query}%")
                    )
                )
            
            # 应用过滤器
            if filters:
                if filters.document_ids:
                    db_query = db_query.filter(DBDocument.id.in_(filters.document_ids))
                
                if filters.file_types:
                    db_query = db_query.filter(DBDocument.file_type.in_(filters.file_types))
                
                if filters.created_after:
                    db_query = db_query.filter(DBDocument.created_at >= filters.created_after)
                
                if filters.created_before:
                    db_query = db_query.filter(DBDocument.created_at <= filters.created_before)
            
            # 分页和排序
            db_docs = db_query.order_by(desc(DBDocument.created_at)).offset(offset).limit(limit).all()
            
            return [self._db_to_domain(doc) for doc in db_docs]
            
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to search documents: {str(e)}")
    
    async def update_status(self, document_id: str, status: DocumentStatus) -> bool:
        """更新文档状态"""
        try:
            result = self.session.query(DBDocument).filter(DBDocument.id == document_id).update(
                {"status": status.value, "updated_at": datetime.utcnow()}
            )
            self.session.commit()
            return result > 0
        except Exception as e:
            self.session.rollback()
            raise DocumentRepositoryError(f"Failed to update document status: {str(e)}")
    
    async def delete(self, document_id: str) -> bool:
        """删除文档"""
        try:
            result = self.session.query(DBDocument).filter(DBDocument.id == document_id).delete()
            self.session.commit()
            return result > 0
        except Exception as e:
            self.session.rollback()
            raise DocumentRepositoryError(f"Failed to delete document: {str(e)}")
    
    async def exists(self, document_id: str) -> bool:
        """检查文档是否存在"""
        try:
            return self.session.query(DBDocument).filter(DBDocument.id == document_id).first() is not None
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to check document existence: {str(e)}")
    
    async def count(self, filters: Optional[SearchFilter] = None) -> int:
        """统计文档数量"""
        try:
            db_query = self.session.query(func.count(DBDocument.id))
            
            # 应用过滤器
            if filters:
                if filters.document_ids:
                    db_query = db_query.filter(DBDocument.id.in_(filters.document_ids))
                
                if filters.file_types:
                    db_query = db_query.filter(DBDocument.file_type.in_(filters.file_types))
                
                if filters.created_after:
                    db_query = db_query.filter(DBDocument.created_at >= filters.created_after)
                
                if filters.created_before:
                    db_query = db_query.filter(DBDocument.created_at <= filters.created_before)
            
            return db_query.scalar()
            
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to count documents: {str(e)}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            # 总文档数
            total_docs = self.session.query(func.count(DBDocument.id)).scalar()
            
            # 状态分布
            status_counts = self.session.query(
                DBDocument.status, func.count(DBDocument.id)
            ).group_by(DBDocument.status).all()
            
            status_distribution = {status: count for status, count in status_counts}
            
            # 文件类型分布
            type_counts = self.session.query(
                DBDocument.file_type, func.count(DBDocument.id)
            ).group_by(DBDocument.file_type).all()
            
            file_type_distribution = {file_type: count for file_type, count in type_counts}
            
            # 文件大小统计
            size_stats = self.session.query(
                func.sum(DBDocument.file_size),
                func.avg(DBDocument.file_size)
            ).first()
            
            total_size = size_stats[0] or 0
            avg_size = size_stats[1] or 0
            
            return {
                'total_documents': total_docs,
                'status_distribution': status_distribution,
                'file_type_distribution': file_type_distribution,
                'total_size_bytes': total_size,
                'average_size_bytes': float(avg_size)
            }
            
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to get statistics: {str(e)}")


class SQLAlchemyQueryHistoryRepository:
    """查询历史仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def save_query(self, 
                        query_text: str,
                        query_type: str = None,
                        strategy_used: str = None,
                        results_count: int = 0,
                        response_time_ms: int = 0,
                        metadata: Dict[str, Any] = None) -> int:
        """保存查询历史"""
        try:
            query_history = DBQueryHistory(
                query_text=query_text,
                query_type=query_type,
                strategy_used=strategy_used,
                results_count=results_count,
                response_time_ms=response_time_ms,
                metadata=metadata or {}
            )
            
            self.session.add(query_history)
            self.session.commit()
            
            return query_history.id
            
        except Exception as e:
            self.session.rollback()
            raise DocumentRepositoryError(f"Failed to save query history: {str(e)}")
    
    async def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的查询"""
        try:
            queries = self.session.query(DBQueryHistory).order_by(
                desc(DBQueryHistory.created_at)
            ).limit(limit).all()
            
            return [
                {
                    'id': q.id,
                    'query_text': q.query_text,
                    'query_type': q.query_type,
                    'strategy_used': q.strategy_used,
                    'results_count': q.results_count,
                    'response_time_ms': q.response_time_ms,
                    'created_at': q.created_at,
                    'metadata': q.metadata
                }
                for q in queries
            ]
            
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to get recent queries: {str(e)}")
    
    async def get_query_statistics(self) -> Dict[str, Any]:
        """获取查询统计"""
        try:
            # 总查询数
            total_queries = self.session.query(func.count(DBQueryHistory.id)).scalar()
            
            # 查询类型分布
            type_counts = self.session.query(
                DBQueryHistory.query_type, func.count(DBQueryHistory.id)
            ).group_by(DBQueryHistory.query_type).all()
            
            # 策略使用分布
            strategy_counts = self.session.query(
                DBQueryHistory.strategy_used, func.count(DBQueryHistory.id)
            ).group_by(DBQueryHistory.strategy_used).all()
            
            # 平均响应时间
            avg_response_time = self.session.query(
                func.avg(DBQueryHistory.response_time_ms)
            ).scalar()
            
            return {
                'total_queries': total_queries,
                'query_type_distribution': {qtype: count for qtype, count in type_counts},
                'strategy_distribution': {strategy: count for strategy, count in strategy_counts},
                'average_response_time_ms': float(avg_response_time or 0)
            }
            
        except Exception as e:
            raise DocumentRepositoryError(f"Failed to get query statistics: {str(e)}")