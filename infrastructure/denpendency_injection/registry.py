"""
Dependency Registry - Lightweight dependency injection system

Designed for FastAPI with support for:
- Automatic dependency resolution
- Lifecycle management (singleton, scoped, transient)
- Type-safe dependency injection
- Circular dependency detection
"""

import logging
import inspect
import asyncio
from typing import TypeVar, Dict, Callable, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceScope(Enum):
    """Service lifecycle scopes"""
    SINGLETON = "singleton"    # Global singleton, application-level lifecycle
    SCOPED = "scoped"         # Request scope, request-level lifecycle
    TRANSIENT = "transient"   # Transient instance, new instance every time


class DependencyRegistry:
    """Lightweight dependency registry"""
    
    def __init__(self):
        # Service factory registry: service type -> factory function
        self._factories: Dict[type, Callable] = {}
        
        # Singleton instance cache
        self._singletons: Dict[type, Any] = {}
        
        # Scoped instance cache: scope ID -> service type -> instance
        self._scoped: Dict[str, Dict[type, Any]] = {}
        
        # Service scope configuration: service type -> scope type
        self._scopes: Dict[type, ServiceScope] = {}
        
        # Circular dependency detection: currently resolving service types
        self._resolving: Set[type] = set()
    
    def register_factory(self, service_type: type, factory: Callable) -> 'DependencyRegistry':
        """Register factory function (transient scope)"""
        self._factories[service_type] = factory
        self._scopes[service_type] = ServiceScope.TRANSIENT
        logger.debug(f"Registered transient factory for {service_type.__name__}")
        return self
    
    def register_singleton(self, service_type: type, factory: Callable) -> 'DependencyRegistry':
        """Register singleton factory function"""
        self._factories[service_type] = factory
        self._scopes[service_type] = ServiceScope.SINGLETON
        logger.debug(f"Registered singleton factory for {service_type.__name__}")
        return self
    
    def register_scoped(self, service_type: type, factory: Callable) -> 'DependencyRegistry':
        """Register scoped factory function (request-level)"""
        self._factories[service_type] = factory
        self._scopes[service_type] = ServiceScope.SCOPED
        logger.debug(f"Registered scoped factory for {service_type.__name__}")
        return self
    
    async def get(self, service_type: type, scope_id: Optional[str] = None) -> T:
        """Get service instance based on registered scope type"""
        if service_type not in self._factories:
            raise ValueError(f"Service {service_type.__name__} is not registered")
        
        # Circular dependency detection
        if service_type in self._resolving:
            dependency_chain = " -> ".join([t.__name__ for t in self._resolving])
            raise ValueError(f"Circular dependency detected: {dependency_chain} -> {service_type.__name__}")
        
        scope = self._scopes[service_type]
        
        # Singleton mode: global cache
        if scope == ServiceScope.SINGLETON:
            if service_type not in self._singletons:
                self._resolving.add(service_type)
                try:
                    instance = await self._create_instance(service_type, scope_id)
                    self._singletons[service_type] = instance
                    logger.debug(f"Created singleton instance of {service_type.__name__}")
                finally:
                    self._resolving.discard(service_type)
            
            return self._singletons[service_type]
        
        # Scoped mode: request-level cache
        elif scope == ServiceScope.SCOPED and scope_id:
            if scope_id not in self._scoped:
                self._scoped[scope_id] = {}
            
            if service_type not in self._scoped[scope_id]:
                self._resolving.add(service_type)
                try:
                    instance = await self._create_instance(service_type, scope_id)
                    self._scoped[scope_id][service_type] = instance
                    logger.debug(f"Created scoped instance of {service_type.__name__} for scope {scope_id}")
                finally:
                    self._resolving.discard(service_type)
            
            return self._scoped[scope_id][service_type]
        
        # Transient mode: create new instance every time
        else:
            self._resolving.add(service_type)
            try:
                instance = await self._create_instance(service_type, scope_id)
                logger.debug(f"Created transient instance of {service_type.__name__}")
                return instance
            finally:
                self._resolving.discard(service_type)
    
    async def _create_instance(self, service_type: type, scope_id: Optional[str] = None) -> Any:
        """Create service instance with automatic dependency injection"""
        factory = self._factories[service_type]
        
        # Get factory function signature
        sig = inspect.signature(factory)
        kwargs = {}
        
        # Automatically resolve each parameter's dependencies
        for param_name, param in sig.parameters.items():
            param_type = param.annotation
            
            # Skip parameters without type annotations
            if param_type == param.empty:
                continue
            
            # Skip basic types
            if param_type in (str, int, float, bool):
                continue
            
            # If parameter type is registered, recursively get dependency
            if param_type in self._factories:
                dependency = await self.get(param_type, scope_id)
                kwargs[param_name] = dependency
                logger.debug(f"Injected dependency {param_type.__name__} into {service_type.__name__}")
        
        # Call factory function
        if asyncio.iscoroutinefunction(factory):
            return await factory(**kwargs)
        else:
            return factory(**kwargs)
    
    def clear_scope(self, scope_id: str):
        """Clear all instances for the specified scope"""
        if scope_id in self._scoped:
            count = len(self._scoped[scope_id])
            del self._scoped[scope_id]
            logger.debug(f"Cleared scope {scope_id}, removed {count} instances")
    
    def clear_all_scopes(self):
        """Clear all scoped instances"""
        count = sum(len(instances) for instances in self._scoped.values())
        self._scoped.clear()
        logger.debug(f"Cleared all scopes, removed {count} instances")
    
    async def cleanup(self):
        """Clean up resources, close all singleton instances"""
        logger.info("Starting registry cleanup...")
        
        # Clear scoped instances
        self.clear_all_scopes()
        
        # Try to close singleton instances
        for service_type, instance in self._singletons.items():
            try:
                # Try calling close method if available
                if hasattr(instance, 'close'):
                    if asyncio.iscoroutinefunction(instance.close):
                        await instance.close()
                    else:
                        instance.close()
                    logger.debug(f"Closed {service_type.__name__} instance")
                        
                # Try calling cleanup method if available
                elif hasattr(instance, 'cleanup'):
                    if asyncio.iscoroutinefunction(instance.cleanup):
                        await instance.cleanup()
                    else:
                        instance.cleanup()
                    logger.debug(f"Cleaned up {service_type.__name__} instance")
                        
            except Exception as e:
                logger.warning(f"Error cleaning up {service_type.__name__}: {e}")
        
        # Clear all caches
        self._singletons.clear()
        logger.info("Registry cleanup completed")
    
    def get_registered_services(self) -> Dict[type, ServiceScope]:
        """Get information about all registered services"""
        return self._scopes.copy()
    
    def is_registered(self, service_type: type) -> bool:
        """Check if service is registered"""
        return service_type in self._factories


# Global registry instance
_registry = DependencyRegistry()


def get_registry() -> DependencyRegistry:
    """Get global registry instance"""
    return _registry


def reset_registry():
    """Reset global registry (mainly for testing)"""
    global _registry
    _registry = DependencyRegistry()
    logger.debug("Registry reset")