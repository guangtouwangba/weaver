"""
Base repository implementation with common CRUD operations.
"""

from typing import Type, TypeVar, Generic, List, Optional, Dict, Any, Union
from datetime import datetime
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, asc, func, select
from sqlalchemy.exc import SQLAlchemyError

from ..models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class RepositoryError(Exception):
    """Base repository error."""
    pass


class NotFoundError(RepositoryError):
    """Entity not found error."""
    pass


class ConflictError(RepositoryError):
    """Entity conflict error (e.g., unique constraint violation)."""
    pass


class BaseRepository(Generic[T], ABC):
    """
    Base repository with common CRUD operations.
    
    Provides standard database operations with proper error handling,
    soft delete support, and filtering capabilities.
    """
    
    def __init__(self, session: Union[Session, AsyncSession], model_class: Type[T]):
        self.session = session
        self.model_class = model_class
        self.is_async = isinstance(session, AsyncSession)
    
    async def create(self, entity_data: Dict[str, Any]) -> T:
        """Create a new entity."""
        try:
            entity = self.model_class(**entity_data)
            
            if self.is_async:
                self.session.add(entity)
                await self.session.commit()
                await self.session.refresh(entity)
            else:
                self.session.add(entity)
                self.session.commit()
                self.session.refresh(entity)
                
            return entity
            
        except SQLAlchemyError as e:
            if self.is_async:
                await self.session.rollback()
            else:
                self.session.rollback()
            raise RepositoryError(f"Failed to create {self.model_class.__name__}: {str(e)}")
    
    async def get_by_id(self, entity_id: Any, include_deleted: bool = False) -> Optional[T]:
        """Get entity by ID."""
        try:
            query = select(self.model_class).where(self.model_class.id == entity_id)
            
            if not include_deleted and hasattr(self.model_class, 'is_deleted'):
                query = query.where(self.model_class.is_deleted == False)
            
            if self.is_async:
                result = await self.session.execute(query)
                return result.scalar_one_or_none()
            else:
                result = self.session.execute(query)
                return result.scalar_one_or_none()
                
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get {self.model_class.__name__} by ID: {str(e)}")
    
    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all entities with optional filtering and pagination."""
        try:
            query = select(self.model_class)
            
            # Apply soft delete filter
            if not include_deleted and hasattr(self.model_class, 'is_deleted'):
                query = query.where(self.model_class.is_deleted == False)
            
            # Apply custom filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model_class, key).in_(value))
                        else:
                            query = query.where(getattr(self.model_class, key) == value)
            
            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                order_column = getattr(self.model_class, order_by)
                if order_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            if self.is_async:
                result = await self.session.execute(query)
                return result.scalars().all()
            else:
                result = self.session.execute(query)
                return result.scalars().all()
                
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get {self.model_class.__name__} list: {str(e)}")
    
    async def update(self, entity_id: Any, update_data: Dict[str, Any]) -> Optional[T]:
        """Update an entity by ID."""
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                raise NotFoundError(f"{self.model_class.__name__} with ID {entity_id} not found")
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(entity, key) and key not in {'id', 'created_at'}:
                    setattr(entity, key, value)
            
            # Update timestamp if available
            if hasattr(entity, 'updated_at'):
                entity.updated_at = datetime.utcnow()
            
            if self.is_async:
                await self.session.commit()
                await self.session.refresh(entity)
            else:
                self.session.commit()
                self.session.refresh(entity)
                
            return entity
            
        except SQLAlchemyError as e:
            if self.is_async:
                await self.session.rollback()
            else:
                self.session.rollback()
            raise RepositoryError(f"Failed to update {self.model_class.__name__}: {str(e)}")
    
    async def delete(self, entity_id: Any, soft_delete: bool = True) -> bool:
        """Delete an entity (soft delete by default)."""
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                return False
            
            if soft_delete and hasattr(entity, 'soft_delete'):
                entity.soft_delete()
                if self.is_async:
                    await self.session.commit()
                else:
                    self.session.commit()
            else:
                if self.is_async:
                    await self.session.delete(entity)
                    await self.session.commit()
                else:
                    self.session.delete(entity)
                    self.session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            if self.is_async:
                await self.session.rollback()
            else:
                self.session.rollback()
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}: {str(e)}")
    
    async def exists(self, entity_id: Any, include_deleted: bool = False) -> bool:
        """Check if entity exists by ID."""
        entity = await self.get_by_id(entity_id, include_deleted=include_deleted)
        return entity is not None
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """Count entities with optional filtering."""
        try:
            query = select(func.count(self.model_class.id))
            
            # Apply soft delete filter
            if not include_deleted and hasattr(self.model_class, 'is_deleted'):
                query = query.where(self.model_class.is_deleted == False)
            
            # Apply custom filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model_class, key).in_(value))
                        else:
                            query = query.where(getattr(self.model_class, key) == value)
            
            if self.is_async:
                result = await self.session.execute(query)
                return result.scalar()
            else:
                result = self.session.execute(query)
                return result.scalar()
                
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to count {self.model_class.__name__}: {str(e)}")
    
    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        limit: Optional[int] = None,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[T]:
        """Search entities by text fields."""
        try:
            query = select(self.model_class)
            
            # Apply soft delete filter
            if not include_deleted and hasattr(self.model_class, 'is_deleted'):
                query = query.where(self.model_class.is_deleted == False)
            
            # Build search conditions
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model_class, field):
                    field_attr = getattr(self.model_class, field)
                    search_conditions.append(field_attr.ilike(f"%{search_term}%"))
            
            if search_conditions:
                query = query.where(or_(*search_conditions))
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            if self.is_async:
                result = await self.session.execute(query)
                return result.scalars().all()
            else:
                result = self.session.execute(query)
                return result.scalars().all()
                
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to search {self.model_class.__name__}: {str(e)}")
    
    async def bulk_create(self, entities_data: List[Dict[str, Any]]) -> List[T]:
        """Create multiple entities in a single transaction."""
        try:
            entities = [self.model_class(**data) for data in entities_data]
            
            if self.is_async:
                self.session.add_all(entities)
                await self.session.commit()
                for entity in entities:
                    await self.session.refresh(entity)
            else:
                self.session.add_all(entities)
                self.session.commit()
                for entity in entities:
                    self.session.refresh(entity)
                    
            return entities
            
        except SQLAlchemyError as e:
            if self.is_async:
                await self.session.rollback()
            else:
                self.session.rollback()
            raise RepositoryError(f"Failed to bulk create {self.model_class.__name__}: {str(e)}")
    
    # Health check and utility methods
    async def health_check(self) -> bool:
        """Check if repository/database connection is healthy."""
        try:
            query = select(func.count()).select_from(self.model_class)
            if self.is_async:
                await self.session.execute(query)
            else:
                self.session.execute(query)
            return True
        except Exception:
            return False