# Registry依赖注入系统

轻量级的依赖注入系统，专为FastAPI设计，提供自动依赖解析、生命周期管理和类型安全的依赖注入。

## 🚀 快速开始

### 1. 在main.py中配置依赖注入

```python
from infrastructure.denpendency_injection import configure_all_services, setup_fastapi_integration

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时配置所有服务依赖
    logger.info("Configuring dependency injection...")
    await configure_all_services()
    
    yield
    
    # 关闭时清理资源
    from infrastructure.denpendency_injection import cleanup_services
    await cleanup_services()

# 创建FastAPI应用
app = FastAPI(lifespan=lifespan)

# 配置Registry与FastAPI集成
setup_fastapi_integration(app)
```

### 2. 在API路由中使用依赖注入

```python
from fastapi import Depends
from infrastructure.denpendency_injection import get_service
from application.topic.topic import TopicController

@app.get("/topics")
async def get_topics(
    controller: TopicController = Depends(get_service(TopicController))
):
    # controller已经包含了所有需要的依赖（数据库、存储、事件总线等）
    return await controller.get_all_topics()

@app.post("/topics")
async def create_topic(
    request: CreateTopicRequest,
    controller: TopicController = Depends(get_service(TopicController))
):
    return await controller.create_topic(request)
```

### 3. 使用便捷的预配置依赖

```python
from infrastructure.denpendency_injection import DependsTopicController, DependsEventBus

@app.post("/topics")
async def create_topic(
    request: CreateTopicRequest,
    controller: TopicController = DependsTopicController,  # 更简洁的写法
    event_bus: EventBus = DependsEventBus
):
    result = await controller.create_topic(request)
    await event_bus.publish(TopicCreatedEvent(topic_id=result.id))
    return result
```

## 🎯 核心特性

### 自动依赖解析

Registry通过类型注解自动识别和注入依赖：

```python
async def create_topic_controller(
    session: AsyncSession,    # 自动注入数据库会话
    event_bus: EventBus,      # 自动注入事件总线
    storage: IObjectStorage   # 自动注入存储服务
) -> TopicController:
    # Registry会自动创建这些依赖并传递给工厂函数
    return TopicController(TopicService(session, event_bus, storage))
```

### 生命周期管理

- **SINGLETON**: 全局单例，应用级生命周期（如EventBus、Storage）
- **SCOPED**: 请求作用域，每个HTTP请求独立实例（如Database Session）
- **TRANSIENT**: 临时实例，每次调用创建新实例（如Controllers）

```python
registry = get_registry()
registry.register_singleton(EventBus, create_event_bus)          # 全局共享
registry.register_scoped(AsyncSession, get_database_session)     # 请求级别
registry.register_factory(TopicController, create_controller)    # 每次新建
```

### 类型安全

完全支持Python类型系统和IDE智能提示：

```python
# 类型注解确保依赖注入的类型安全
controller: TopicController = Depends(get_service(TopicController))
#          ^^^^^^^^^^^^^^^^              ^^^^^^^^^^^^^^^
#          IDE智能提示               Registry类型检查
```

## 🔧 高级用法

### 自定义服务注册

```python
# 在services.py中添加新的服务配置
async def configure_custom_services():
    registry = get_registry()
    
    # 注册自定义服务
    registry.register_singleton(CustomService, create_custom_service)
    
    # 支持依赖注入的工厂函数
    async def create_custom_service(
        config: Config = Depends(get_config),
        redis: RedisClient = Depends(get_redis_client)
    ) -> CustomService:
        return CustomService(config, redis)
```

### 测试中使用Mock服务

```python
import pytest
from infrastructure.denpendency_injection import get_registry, reset_registry

@pytest.fixture
def test_registry():
    # 重置Registry并注册测试专用的Mock服务
    reset_registry()
    
    registry = get_registry()
    registry.register_singleton(EventBus, lambda: MockEventBus())
    registry.register_singleton(IObjectStorage, lambda: MockStorage())
    
    yield registry
    
    # 测试结束后清理
    reset_registry()

async def test_topic_creation(test_registry):
    # 使用Mock服务进行测试
    controller = await test_registry.get(TopicController)
    # controller使用的是Mock依赖，测试隔离且快速
```

### 监控服务状态

```python
from infrastructure.denpendency_injection import get_service_status

@app.get("/admin/services")
async def get_services_status():
    """获取所有已注册服务的状态"""
    return get_service_status()

# 返回格式：
# {
#   "total_services": 5,
#   "services": {
#     "EventBus": {"scope": "singleton", "module": "application.event.event_bus"},
#     "TopicController": {"scope": "transient", "module": "application.topic.topic"},
#     ...
#   }
# }
```

## 🚦 最佳实践

### 1. 服务注册原则
- **基础设施服务**（数据库、缓存、消息队列）→ SINGLETON
- **数据库会话**（需要事务隔离）→ SCOPED
- **业务控制器**（无状态）→ TRANSIENT

### 2. 工厂函数设计
```python
# ✅ 好的实践：清晰的类型注解
async def create_service(
    db: AsyncSession,     # 明确的依赖类型
    config: Config        # Registry可以自动解析
) -> MyService:
    return MyService(db, config)

# ❌ 避免的做法：缺少类型注解
def create_service(db, config):  # Registry无法自动解析依赖
    return MyService(db, config)
```

### 3. 错误处理
Registry提供详细的错误信息：
- 服务未注册错误
- 循环依赖检测
- 类型注解缺失警告

## 🎉 完成！

现在您的项目已经有了完整的依赖注入系统：

1. ✅ **统一的服务管理** - 所有服务在一个地方配置
2. ✅ **自动依赖解析** - 无需手动管理复杂的依赖关系
3. ✅ **生命周期控制** - 合理的资源管理和缓存策略
4. ✅ **类型安全** - 完整的类型检查和IDE支持
5. ✅ **FastAPI原生集成** - 与现有代码无缝配合
6. ✅ **测试友好** - 轻松mock和隔离测试

您现在可以享受现代依赖注入带来的便利，同时保持代码的简洁和可维护性！