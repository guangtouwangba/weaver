# Clean Architecture 重构设计

## 设计原则

### 1. 个人开发优先 (Personal Development First)
- **单体优先**：默认提供单体应用模式，降低开发复杂度
- **可选分布式**：支持分布式部署，但不强制要求
- **零配置启动**：提供开箱即用的开发环境
- **渐进式复杂度**：从简单开始，按需增加复杂功能

### 2. 清晰的依赖方向
- **内向依赖**：外层依赖内层，内层不依赖外层
- **接口隔离**：通过接口定义边界，减少耦合
- **依赖注入**：使用DI容器管理依赖关系

### 3. 功能内聚
- **领域驱动**：按业务领域组织代码
- **单一职责**：每个模块只负责一个业务领域
- **高内聚低耦合**：模块内部紧密相关，模块间松散耦合

## 新架构设计

### 目录结构

```
research-agent-rag/
├── src/                          # 源代码目录
│   ├── core/                     # 核心业务逻辑（最内层）
│   │   ├── entities/             # 实体类
│   │   ├── value_objects/        # 值对象
│   │   ├── domain_services/      # 领域服务
│   │   └── repositories/         # 仓储接口
│   ├── use_cases/                # 用例层（应用服务）
│   │   ├── document/             # 文档管理用例
│   │   ├── chat/                 # 聊天用例
│   │   ├── knowledge/            # 知识管理用例
│   │   └── common/               # 通用用例
│   ├── adapters/                 # 适配器层
│   │   ├── repositories/         # 仓储实现
│   │   ├── external_services/    # 外部服务适配器
│   │   ├── storage/              # 存储适配器
│   │   └── ai/                   # AI服务适配器
│   ├── infrastructure/           # 基础设施层
│   │   ├── database/             # 数据库配置
│   │   ├── cache/                # 缓存配置
│   │   ├── messaging/            # 消息队列
│   │   ├── monitoring/           # 监控配置
│   │   └── config/               # 配置管理
│   ├── presentation/             # 表现层
│   │   ├── api/                  # REST API
│   │   ├── cli/                  # 命令行接口
│   │   ├── web/                  # Web界面（可选）
│   │   └── schemas/              # API模式定义
│   └── shared/                   # 共享组件
│       ├── exceptions/           # 异常定义
│       ├── utils/                # 工具函数
│       ├── constants/            # 常量定义
│       └── types/                # 类型定义
├── config/                       # 配置文件
│   ├── environments/             # 环境配置
│   ├── development.yaml          # 开发环境
│   ├── production.yaml           # 生产环境
│   └── testing.yaml              # 测试环境
├── tests/                        # 测试代码
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   ├── e2e/                      # 端到端测试
│   └── fixtures/                 # 测试数据
├── docs/                         # 文档
│   ├── architecture/             # 架构文档
│   ├── api/                      # API文档
│   ├── deployment/               # 部署文档
│   └── development/              # 开发文档
├── scripts/                      # 脚本工具
│   ├── dev/                      # 开发脚本
│   ├── deployment/               # 部署脚本
│   └── maintenance/              # 维护脚本
├── docker/                       # Docker配置
│   ├── development/              # 开发环境
│   └── production/               # 生产环境
├── requirements/                 # 依赖管理
│   ├── base.txt                  # 基础依赖
│   ├── development.txt           # 开发依赖
│   └── production.txt            # 生产依赖
├── main.py                       # 应用入口
├── pyproject.toml                # 项目配置
└── README.md                     # 项目说明
```

## 核心架构层次

### 1. Core Layer (核心层)
**职责**：包含业务规则和实体，不依赖任何外部框架

```python
# src/core/entities/document.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Document:
    id: str
    title: str
    content: str
    topic_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def update_content(self, content: str) -> None:
        self.content = content
        self.updated_at = datetime.utcnow()
```

### 2. Use Cases Layer (用例层)
**职责**：应用业务规则，编排实体和仓储

```python
# src/use_cases/document/create_document.py
from src.core.entities.document import Document
from src.core.repositories.document_repository import DocumentRepository

class CreateDocumentUseCase:
    def __init__(self, document_repo: DocumentRepository):
        self._document_repo = document_repo
    
    async def execute(self, title: str, content: str, topic_id: str) -> Document:
        document = Document(
            id=self._generate_id(),
            title=title,
            content=content,
            topic_id=topic_id
        )
        await self._document_repo.save(document)
        return document
```

### 3. Adapters Layer (适配器层)
**职责**：实现接口，连接外部世界

```python
# src/adapters/repositories/sqlalchemy_document_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.entities.document import Document
from src.core.repositories.document_repository import DocumentRepository

class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, document: Document) -> None:
        # SQLAlchemy implementation
        pass
```

### 4. Infrastructure Layer (基础设施层)
**职责**：提供技术能力，如数据库、缓存、消息队列

### 5. Presentation Layer (表现层)
**职责**：处理用户交互，调用用例

## 开发模式设计

### 1. 单体模式 (Monolith Mode) - 默认
- **内存数据库**：SQLite for development
- **内存缓存**：Python dict-based cache
- **同步处理**：直接处理，无队列
- **嵌入式向量存储**：ChromaDB embedded mode

### 2. 增强模式 (Enhanced Mode)
- **外部数据库**：PostgreSQL
- **Redis缓存**：Redis for caching
- **异步任务**：Celery + Redis
- **向量数据库**：Weaviate or Qdrant

### 3. 分布式模式 (Distributed Mode)
- **微服务架构**：独立的服务实例
- **服务发现**：Consul or Kubernetes
- **负载均衡**：Nginx or HAProxy
- **监控告警**：Prometheus + Grafana

## 配置管理

### 环境配置
```yaml
# config/environments/development.yaml
mode: monolith  # monolith | enhanced | distributed

database:
  type: sqlite
  url: "sqlite:///./dev.db"

cache:
  type: memory
  
vector_store:
  type: chroma
  path: "./chroma_db"

ai:
  provider: openai
  model: gpt-3.5-turbo
```

## 依赖注入设计

### DI Container
```python
# src/shared/di/container.py
from dependency_injector import containers, providers
from src.use_cases.document.create_document import CreateDocumentUseCase
from src.adapters.repositories.memory_document_repository import MemoryDocumentRepository

class Container(containers.DeclarativeContainer):
    # Repositories
    document_repository = providers.Factory(MemoryDocumentRepository)
    
    # Use Cases
    create_document_use_case = providers.Factory(
        CreateDocumentUseCase,
        document_repo=document_repository
    )
```

## 测试策略

### 1. 单元测试
- 测试核心实体和值对象
- 测试用例逻辑
- Mock外部依赖

### 2. 集成测试
- 测试适配器实现
- 测试数据库集成
- 测试外部服务集成

### 3. 端到端测试
- 测试完整业务流程
- 测试API接口
- 测试用户场景

## 迁移策略

### 阶段1：重构准备
1. 创建新目录结构
2. 定义核心实体和接口
3. 实现基础用例

### 阶段2：逐步迁移
1. 迁移文档管理功能
2. 迁移聊天功能
3. 迁移知识管理功能

### 阶段3：优化完善
1. 性能优化
2. 测试覆盖
3. 文档完善

## 开发工具支持

### 1. 开发脚本
```bash
# 启动开发环境
./scripts/dev/start.sh

# 运行测试
./scripts/dev/test.sh

# 代码检查
./scripts/dev/lint.sh
```

### 2. IDE配置
- VSCode配置文件
- PyCharm配置
- 调试配置

### 3. Git Hooks
- Pre-commit检查
- 自动格式化
- 测试运行

## 预期收益

### 1. 开发体验提升
- 启动时间从30秒降低到3秒
- 零配置开发环境
- 清晰的代码结构

### 2. 维护性提升
- 模块间依赖清晰
- 测试覆盖率提升
- 代码复用性增强

### 3. 扩展性保持
- 支持渐进式扩展
- 保持分布式能力
- 便于新功能添加

这个设计在保持系统功能完整性的同时，大幅提升了个人开发的友好性和代码的可维护性。