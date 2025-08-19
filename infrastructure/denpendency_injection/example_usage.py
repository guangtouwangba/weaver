"""
Registry使用示例

展示如何在实际项目中使用Registry进行依赖注入。
"""

import asyncio
import logging
from typing import Protocol

# 设置日志以便查看Registry的工作过程
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ========== 示例服务定义 ==========

class IDatabase(Protocol):
    """数据库接口"""
    async def query(self, sql: str) -> list:
        ...
    
    async def close(self):
        ...


class MockDatabase:
    """模拟数据库实现"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.is_connected = False
        logger.info(f"MockDatabase created with connection: {connection_string}")
    
    async def connect(self):
        self.is_connected = True
        logger.info("MockDatabase connected")
    
    async def query(self, sql: str) -> list:
        if not self.is_connected:
            await self.connect()
        logger.info(f"Executing query: {sql}")
        return [{"id": 1, "name": "test"}]
    
    async def close(self):
        self.is_connected = False
        logger.info("MockDatabase connection closed")


class UserService:
    """用户服务 - 依赖于数据库"""
    
    def __init__(self, database: IDatabase):
        self.database = database
        logger.info("UserService created with database dependency")
    
    async def get_users(self) -> list:
        return await self.database.query("SELECT * FROM users")
    
    async def get_user(self, user_id: int) -> dict:
        result = await self.database.query(f"SELECT * FROM users WHERE id = {user_id}")
        return result[0] if result else None


class NotificationService:
    """通知服务 - 独立服务"""
    
    def __init__(self):
        logger.info("NotificationService created")
    
    async def send_notification(self, message: str):
        logger.info(f"Sending notification: {message}")


class UserController:
    """用户控制器 - 依赖于UserService和NotificationService"""
    
    def __init__(self, user_service: UserService, notification_service: NotificationService):
        self.user_service = user_service
        self.notification_service = notification_service
        logger.info("UserController created with all dependencies")
    
    async def create_user(self, name: str) -> dict:
        # 模拟创建用户
        user = {"id": 123, "name": name}
        
        # 发送通知
        await self.notification_service.send_notification(f"User {name} created")
        
        return user
    
    async def get_user(self, user_id: int) -> dict:
        return await self.user_service.get_user(user_id)


# ========== 工厂函数（支持依赖注入） ==========

async def create_database() -> IDatabase:
    """创建数据库实例"""
    db = MockDatabase("postgresql://localhost:5432/test")
    await db.connect()
    return db


def create_user_service(database: IDatabase) -> UserService:
    """创建用户服务，自动注入数据库依赖"""
    return UserService(database)


def create_notification_service() -> NotificationService:
    """创建通知服务"""
    return NotificationService()


def create_user_controller(
    user_service: UserService,           # 自动注入
    notification_service: NotificationService  # 自动注入
) -> UserController:
    """创建用户控制器，自动注入所有依赖"""
    return UserController(user_service, notification_service)


# ========== Registry配置和使用示例 ==========

async def demo_basic_usage():
    """基本使用示例"""
    print("=== Registry基本使用示例 ===")
    
    from .registry import DependencyRegistry
    
    # 创建Registry实例
    registry = DependencyRegistry()
    
    # 注册服务
    registry.register_singleton(IDatabase, create_database)
    registry.register_transient(UserService, create_user_service) 
    registry.register_transient(NotificationService, create_notification_service)
    registry.register_transient(UserController, create_user_controller)
    
    # 获取服务实例 - Registry会自动解析依赖
    controller = await registry.get(UserController)
    
    # 使用服务
    user = await controller.create_user("Alice")
    print(f"Created user: {user}")
    
    retrieved_user = await controller.get_user(123)
    print(f"Retrieved user: {retrieved_user}")
    
    # 清理资源
    await registry.cleanup()


async def demo_scoped_services():
    """作用域服务示例"""
    print("\n=== Registry作用域服务示例 ===")
    
    from .registry import DependencyRegistry
    
    registry = DependencyRegistry()
    
    # 注册不同作用域的服务
    registry.register_singleton(NotificationService, create_notification_service)  # 单例
    registry.register_scoped(IDatabase, create_database)                          # 作用域
    registry.register_transient(UserService, create_user_service)                # 临时
    
    # 模拟两个不同的请求作用域
    scope_1 = "request_1"
    scope_2 = "request_2"
    
    # 请求1
    print(f"\n--- 处理请求 {scope_1} ---")
    db1 = await registry.get(IDatabase, scope_id=scope_1)
    service1 = await registry.get(UserService, scope_id=scope_1)
    notification1 = await registry.get(NotificationService, scope_id=scope_1)
    
    # 请求2  
    print(f"\n--- 处理请求 {scope_2} ---")
    db2 = await registry.get(IDatabase, scope_id=scope_2)
    service2 = await registry.get(UserService, scope_id=scope_2)
    notification2 = await registry.get(NotificationService, scope_id=scope_2)
    
    # 验证作用域隔离
    print(f"\n--- 作用域验证 ---")
    print(f"数据库实例隔离: {db1 is not db2}")              # True - 不同作用域有不同实例
    print(f"用户服务实例隔离: {service1 is not service2}")    # True - 每次创建新实例
    print(f"通知服务单例共享: {notification1 is notification2}")  # True - 单例在所有作用域共享
    
    # 清理作用域
    registry.clear_scope(scope_1)
    registry.clear_scope(scope_2)
    await registry.cleanup()


async def demo_fastapi_integration():
    """FastAPI集成示例"""
    print("\n=== FastAPI集成使用示例 ===")
    
    from fastapi import FastAPI, Depends
    from .fastapi_integration import get_service, setup_fastapi_integration
    from .services import configure_all_services
    
    # 创建FastAPI应用
    app = FastAPI(title="Registry Demo API")
    
    # 配置Registry集成
    setup_fastapi_integration(app)
    
    # 配置所有服务（在实际项目中应该在启动时调用）
    await configure_all_services()
    
    # 定义API路由，使用Registry自动依赖注入
    @app.get("/users/{user_id}")
    async def get_user_endpoint(
        user_id: int,
        controller: UserController = Depends(get_service(UserController))  # 自动注入
    ):
        """获取用户API"""
        return await controller.get_user(user_id)
    
    @app.post("/users")
    async def create_user_endpoint(
        name: str,
        controller: UserController = Depends(get_service(UserController))  # 自动注入
    ):
        """创建用户API"""
        return await controller.create_user(name)
    
    print("FastAPI应用已配置Registry依赖注入")
    print("API路由：")
    print("  GET  /users/{user_id} - 获取用户")
    print("  POST /users?name=<name> - 创建用户")
    
    # 注意：在实际项目中，你会使用 uvicorn 运行这个应用：
    # uvicorn demo:app --reload


async def demo_error_handling():
    """错误处理示例"""
    print("\n=== Registry错误处理示例 ===")
    
    from .registry import DependencyRegistry
    
    registry = DependencyRegistry()
    
    # 1. 未注册服务错误
    try:
        await registry.get(UserController)
    except ValueError as e:
        print(f"未注册服务错误: {e}")
    
    # 2. 循环依赖错误
    def circular_a(b: 'CircularB') -> 'CircularA':
        return CircularA()
    
    def circular_b(a: 'CircularA') -> 'CircularB': 
        return CircularB()
    
    class CircularA:
        pass
    
    class CircularB:
        pass
    
    registry.register_transient(CircularA, circular_a)
    registry.register_transient(CircularB, circular_b)
    
    try:
        await registry.get(CircularA)
    except ValueError as e:
        print(f"循环依赖错误: {e}")


async def demo_service_status():
    """服务状态监控示例"""
    print("\n=== Registry服务状态监控 ===")
    
    from .services import configure_all_services, get_service_status
    
    # 配置服务
    await configure_all_services()
    
    # 获取服务状态
    status = get_service_status()
    
    print(f"已注册服务总数: {status['total_services']}")
    print("\n服务详情:")
    for service_name, service_info in status['services'].items():
        print(f"  {service_name}:")
        print(f"    作用域: {service_info['scope']}")
        print(f"    模块: {service_info['module']}")


async def main():
    """运行所有示例"""
    print("🚀 Registry依赖注入系统示例")
    print("=" * 50)
    
    try:
        await demo_basic_usage()
        await demo_scoped_services() 
        await demo_fastapi_integration()
        await demo_error_handling()
        await demo_service_status()
        
        print("\n✅ 所有示例运行完成!")
        
    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())