# 新架构总结

## 架构概述

成功将数据库模型抽象成独立的Schema层，并按领域拆分Repository和Service，在API层使用Service进行编排。

## 架构分层

### 1. Schema层 (`modules/schemas/`)
- **职责**: 统一数据定义，使用Pydantic提供类型安全和序列化
- **文件结构**:
  ```
  schemas/
  ├── __init__.py          # 统一导出
  ├── base.py              # 基础Schema类
  ├── enums.py             # 枚举定义
  ├── topic.py             # 主题相关Schema
  ├── file.py              # 文件相关Schema
  ├── document.py          # 文档相关Schema
  ├── requests.py          # 请求Schema
  ├── responses.py         # 响应Schema
  └── converters.py        # SQLAlchemy<->Pydantic转换器
  ```
- **优势**:
  - 全局统一的数据定义
  - 强类型验证
  - 减少数据分层冗余
  - 支持序列化/反序列化

### 2. Repository层 (`modules/repository/`)
- **职责**: 数据访问抽象，遵循Repository模式
- **文件结构**:
  ```
  repository/
  ├── __init__.py           # 统一导出
  ├── interfaces.py         # Repository接口定义
  ├── base_repository.py    # 基础Repository实现
  ├── topic_repository.py   # 主题Repository
  ├── file_repository.py    # 文件Repository
  └── document_repository.py # 文档Repository
  ```
- **优势**:
  - 接口与实现分离
  - 支持依赖注入
  - 易于单元测试
  - 遵循SOLID原则

### 3. Service层 (`modules/services/`)
- **职责**: 业务逻辑编排，事务管理
- **文件结构**:
  ```
  services/
  ├── __init__.py          # 统一导出
  ├── base_service.py      # 基础Service类
  ├── topic_service.py     # 主题业务服务
  ├── file_service.py      # 文件业务服务
  └── document_service.py  # 文档业务服务
  ```
- **优势**:
  - 业务逻辑集中管理
  - 事务边界清晰
  - 跨Repository编排
  - 业务规则验证

### 4. API层 (`modules/api/`)
- **职责**: REST API接口，使用Service编排
- **文件结构**:
  ```
  api/
  ├── __init__.py          # 统一路由导出
  ├── topic_api.py         # 主题API
  ├── file_api.py          # 文件API
  └── document_api.py      # 文档API
  ```
- **优势**:
  - 薄API层，逻辑在Service
  - 统一错误处理
  - 依赖注入Service
  - RESTful设计

## 数据流

```
API层 -> Service层 -> Repository层 -> Database层
  ↑         ↑          ↑           ↑
Schema   Schema    Converter   SQLAlchemy
```

## 关键特性

### 1. 统一Schema定义
- 使用Pydantic定义所有数据结构
- 从API请求到数据库模型的一致性
- 强类型验证和自动文档生成

### 2. 依赖注入
```python
async def get_topic_service(session: AsyncSession = Depends(get_session)) -> TopicService:
    return TopicService(session)

@router.post("/topics")
async def create_topic(
    topic_data: TopicCreate,
    service: TopicService = Depends(get_topic_service)
):
    async with service:
        return await service.create_topic(topic_data)
```

### 3. 事务管理
```python
class BaseService:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
```

### 4. 类型安全转换
```python
def topic_to_response(topic_model: TopicModel) -> TopicResponse:
    return TopicResponse(
        id=topic_model.id,
        name=topic_model.name,
        # ... 其他字段
    )
```

## API端点

### 主题API (`/api/v1/topics`)
- `POST /` - 创建主题
- `GET /{id}` - 获取主题详情
- `PUT /{id}` - 更新主题
- `DELETE /{id}` - 删除主题
- `GET /` - 获取主题列表
- `GET /search` - 搜索主题

### 文件API (`/api/v1/files`)
- `POST /upload/signed-url` - 生成上传URL
- `POST /confirm` - 确认上传
- `GET /{id}` - 获取文件详情
- `PUT /{id}` - 更新文件
- `DELETE /{id}` - 删除文件
- `GET /` - 获取文件列表
- `GET /search` - 搜索文件

### 文档API (`/api/v1/documents`)
- `POST /` - 创建文档
- `GET /{id}` - 获取文档详情
- `PUT /{id}` - 更新文档
- `DELETE /{id}` - 删除文档
- `GET /` - 获取文档列表
- `POST /{id}/process` - 处理文档
- `POST /search` - 搜索文档

## 使用方式

### 启动服务器
```bash
python main_with_service.py
```

### 架构演示
```bash
python architecture_demo.py
```

## 架构优势

1. **分层清晰**: 每层职责明确，依赖方向单向
2. **类型安全**: Pydantic提供强类型验证
3. **易于测试**: 接口抽象支持Mock测试
4. **可维护性**: 按领域拆分，便于维护
5. **可扩展性**: 支持依赖注入和插件化
6. **业务编排**: Service层集中处理复杂业务逻辑
7. **数据一致性**: 全局统一的Schema定义

## 与传统架构对比

### 旧架构
```
FastAPI -> 直接数据库操作
```

### 新架构
```
FastAPI -> API -> Service -> Repository -> Database
       ↑    ↑        ↑         ↑
   Pydantic Schema  Business   Data Access
   Validation      Logic      Abstraction
```

## 总结

新架构实现了完整的分层设计：
- **Schema层**: 统一数据定义，减少冗余
- **Repository层**: 按领域拆分，接口抽象
- **Service层**: 业务逻辑编排，事务管理
- **API层**: 薄接口层，Service编排

这种架构提供了更好的可维护性、可测试性和可扩展性，符合企业级应用开发的最佳实践。
