"""
Base repository class providing common database operations.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Any, Type, Generic, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """Abstract base repository with common CRUD operations"""
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    def create(self, **kwargs) -> T:
        """Create a new entity"""
        entity = self.model_class(**kwargs)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """Get entity by ID"""
        return self.session.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        return self.session.query(self.model_class).offset(skip).limit(limit).all()
    
    def update(self, entity_id: Any, **kwargs) -> Optional[T]:
        """Update entity by ID"""
        entity = self.get_by_id(entity_id)
        if not entity:
            return None
        
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        
        self.session.commit()
        self.session.refresh(entity)
        return entity
    
    def delete(self, entity_id: Any) -> bool:
        """Delete entity by ID"""
        entity = self.get_by_id(entity_id)
        if not entity:
            return False
        
        self.session.delete(entity)
        self.session.commit()
        return True
    
    def count(self) -> int:
        """Count total entities"""
        return self.session.query(self.model_class).count()
    
    def exists(self, entity_id: Any) -> bool:
        """Check if entity exists"""
        return self.session.query(
            self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).exists()
        ).scalar()
    
    @abstractmethod
    def get_model_class(self) -> Type[T]:
        """Get the model class for this repository"""
        return self.model_class