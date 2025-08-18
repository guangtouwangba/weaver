"""Search criteria value object."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


class SearchOperator(Enum):
    """Search operators for filtering."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class SortOrder(Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class SearchFilter:
    """Individual search filter."""
    field: str
    operator: SearchOperator
    value: Any
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.field.strip():
            raise ValueError("Filter field cannot be empty")


@dataclass(frozen=True)
class SearchCriteria:
    """Immutable search criteria value object."""
    
    # Query parameters
    query: Optional[str] = None
    semantic_search: bool = True
    hybrid_search: bool = False
    
    # Filtering
    filters: List[SearchFilter] = None
    document_ids: Optional[List[str]] = None
    topic_ids: Optional[List[str]] = None
    owner_id: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Content filtering
    content_types: Optional[List[str]] = None
    file_extensions: Optional[List[str]] = None
    min_file_size: Optional[int] = None
    max_file_size: Optional[int] = None
    
    # Date filtering
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    
    # Similarity threshold for semantic search
    similarity_threshold: float = 0.7
    
    # Pagination
    limit: int = 10
    offset: int = 0
    
    # Sorting
    sort_by: str = "relevance"
    sort_order: SortOrder = SortOrder.DESC
    
    # Result configuration
    include_content: bool = True
    include_metadata: bool = True
    include_embeddings: bool = False
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.filters is None:
            object.__setattr__(self, 'filters', [])
        
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
    
    @property
    def has_text_query(self) -> bool:
        """Check if criteria has text query."""
        return bool(self.query and self.query.strip())
    
    @property
    def has_filters(self) -> bool:
        """Check if criteria has filters."""
        return len(self.filters) > 0
    
    @property
    def has_date_filters(self) -> bool:
        """Check if criteria has date filters."""
        return any([
            self.created_after,
            self.created_before,
            self.updated_after,
            self.updated_before
        ])
    
    @property
    def is_semantic_only(self) -> bool:
        """Check if this is semantic search only."""
        return self.semantic_search and not self.hybrid_search
    
    @property
    def is_hybrid_search(self) -> bool:
        """Check if this is hybrid search."""
        return self.hybrid_search
    
    def with_query(self, query: str) -> 'SearchCriteria':
        """Create new instance with different query."""
        return SearchCriteria(
            query=query,
            semantic_search=self.semantic_search,
            hybrid_search=self.hybrid_search,
            filters=self.filters.copy(),
            document_ids=self.document_ids.copy() if self.document_ids else None,
            topic_ids=self.topic_ids.copy() if self.topic_ids else None,
            owner_id=self.owner_id,
            tags=self.tags.copy() if self.tags else None,
            content_types=self.content_types.copy() if self.content_types else None,
            file_extensions=self.file_extensions.copy() if self.file_extensions else None,
            min_file_size=self.min_file_size,
            max_file_size=self.max_file_size,
            created_after=self.created_after,
            created_before=self.created_before,
            updated_after=self.updated_after,
            updated_before=self.updated_before,
            similarity_threshold=self.similarity_threshold,
            limit=self.limit,
            offset=self.offset,
            sort_by=self.sort_by,
            sort_order=self.sort_order,
            include_content=self.include_content,
            include_metadata=self.include_metadata,
            include_embeddings=self.include_embeddings
        )
    
    def with_pagination(self, limit: int, offset: int) -> 'SearchCriteria':
        """Create new instance with different pagination."""
        return SearchCriteria(
            query=self.query,
            semantic_search=self.semantic_search,
            hybrid_search=self.hybrid_search,
            filters=self.filters.copy(),
            document_ids=self.document_ids.copy() if self.document_ids else None,
            topic_ids=self.topic_ids.copy() if self.topic_ids else None,
            owner_id=self.owner_id,
            tags=self.tags.copy() if self.tags else None,
            content_types=self.content_types.copy() if self.content_types else None,
            file_extensions=self.file_extensions.copy() if self.file_extensions else None,
            min_file_size=self.min_file_size,
            max_file_size=self.max_file_size,
            created_after=self.created_after,
            created_before=self.created_before,
            updated_after=self.updated_after,
            updated_before=self.updated_before,
            similarity_threshold=self.similarity_threshold,
            limit=limit,
            offset=offset,
            sort_by=self.sort_by,
            sort_order=self.sort_order,
            include_content=self.include_content,
            include_metadata=self.include_metadata,
            include_embeddings=self.include_embeddings
        )
    
    def with_filter(self, filter_item: SearchFilter) -> 'SearchCriteria':
        """Create new instance with additional filter."""
        new_filters = self.filters.copy()
        new_filters.append(filter_item)
        
        return SearchCriteria(
            query=self.query,
            semantic_search=self.semantic_search,
            hybrid_search=self.hybrid_search,
            filters=new_filters,
            document_ids=self.document_ids.copy() if self.document_ids else None,
            topic_ids=self.topic_ids.copy() if self.topic_ids else None,
            owner_id=self.owner_id,
            tags=self.tags.copy() if self.tags else None,
            content_types=self.content_types.copy() if self.content_types else None,
            file_extensions=self.file_extensions.copy() if self.file_extensions else None,
            min_file_size=self.min_file_size,
            max_file_size=self.max_file_size,
            created_after=self.created_after,
            created_before=self.created_before,
            updated_after=self.updated_after,
            updated_before=self.updated_before,
            similarity_threshold=self.similarity_threshold,
            limit=self.limit,
            offset=self.offset,
            sort_by=self.sort_by,
            sort_order=self.sort_order,
            include_content=self.include_content,
            include_metadata=self.include_metadata,
            include_embeddings=self.include_embeddings
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'query': self.query,
            'semantic_search': self.semantic_search,
            'hybrid_search': self.hybrid_search,
            'filters': [
                {
                    'field': f.field,
                    'operator': f.operator.value,
                    'value': f.value
                }
                for f in self.filters
            ],
            'document_ids': self.document_ids,
            'topic_ids': self.topic_ids,
            'owner_id': self.owner_id,
            'tags': self.tags,
            'content_types': self.content_types,
            'file_extensions': self.file_extensions,
            'min_file_size': self.min_file_size,
            'max_file_size': self.max_file_size,
            'created_after': self.created_after.isoformat() if self.created_after else None,
            'created_before': self.created_before.isoformat() if self.created_before else None,
            'updated_after': self.updated_after.isoformat() if self.updated_after else None,
            'updated_before': self.updated_before.isoformat() if self.updated_before else None,
            'similarity_threshold': self.similarity_threshold,
            'limit': self.limit,
            'offset': self.offset,
            'sort_by': self.sort_by,
            'sort_order': self.sort_order.value,
            'include_content': self.include_content,
            'include_metadata': self.include_metadata,
            'include_embeddings': self.include_embeddings,
            'has_text_query': self.has_text_query,
            'has_filters': self.has_filters,
            'has_date_filters': self.has_date_filters,
            'is_semantic_only': self.is_semantic_only,
            'is_hybrid_search': self.is_hybrid_search
        }
