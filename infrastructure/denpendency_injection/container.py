import asyncio
from enum import Enum
from typing import TypeVar, Optional, Callable, Any

T = TypeVar("T")


class ServiceScope(Enum):
    """服务作用域枚举"""
    SINGLETON = "singleton"  # 单例模式
    TRANSIENT = "transient"  # 瞬态模式
    SCOPED = "scoped"  # 作用域模式


class ServiceDescriptor:
    """服务描述符"""
    service_type: type
    implementation: Optional[type] = None
    factory: Optional[Callable] = None
    instance: Any = None
    scope: ServiceScope = ServiceScope.TRANSIENT
    dependencies: list = None


class DIContainer:

    def __init__(self):
        self._services: dict[type, ServiceDescriptor] = {}
        self._instances: dict[type, Any] = {}
        self._environment: Optional[str] = "development"  # 默认环境为开发环境

    def register_singleton(self, service_type: type, implementation: type = None, factory: Callable = None):
        """注册单例服务"""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            scope=ServiceScope.SINGLETON
        )
        return self

    def register_scoped(self, service_type: type, implementation: type = None, factory: Callable = None):
        """注册作用域服务"""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            scope=ServiceScope.SCOPED
        )
        return self

    def register_transient(self, service_type: type, implementation: type = None, factory: Callable = None):
        """注册临时服务"""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            scope=ServiceScope.TRANSIENT
        )
        return self

    async def get_service(self, service_type: type) -> T:
        """获取服务实例"""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} is not registered")

        descriptor = self._services[service_type]

        # 单例模式
        if descriptor.scope == ServiceScope.SINGLETON:
            if service_type not in self._instances:
                self._instances[service_type] = await self._create_instance(descriptor)
            return self._instances[service_type]

        # 其他情况创建新实例
        return await self._create_instance(descriptor)

    async def _create_instance(self, descriptor: ServiceDescriptor):
        """创建服务实例"""
        if descriptor.factory:
            if asyncio.iscoroutinefunction(descriptor.factory):
                return await descriptor.factory()
            else:
                return descriptor.factory()
        elif descriptor.implementation:
            return descriptor.implementation()
        else:
            return descriptor.service_type()


_container = DIContainer()


def get_container() -> DIContainer:
    """获取全局容器实例"""
    return _container
