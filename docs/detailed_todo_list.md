# 详细 TODO 清单

## 立即执行 (High Priority)

### 1. 代码清理
- [x] 删除临时测试文件 (test_storage.txt, workflow_test.txt, rag_test.txt)
- [ ] 清理调试脚本
  - [ ] 评估 `tests/debug_task_system.py` 是否需要保留
  - [ ] 清理 `monitor_workers.py` 中的临时代码
  - [ ] 检查并清理其他调试文件
- [ ] 整理根目录文件
  - [ ] 移动 `cli.py` 到 `src/presentation/cli/`
  - [ ] 移动 `worker.py` 到 `src/infrastructure/workers/`
  - [ ] 整理配置文件到 `config/` 目录

### 2. 依赖管理优化
- [ ] 分析 `pyproject.toml` 中的依赖
  - [ ] 识别未使用的依赖
  - [ ] 分类核心依赖和可选依赖
  - [ ] 创建最小依赖集合
- [ ] 创建依赖层次
  - [ ] `requirements/base.txt` - 核心依赖
  - [ ] `requirements/development.txt` - 开发依赖
  - [ ] `requirements/optional.txt` - 可选功能依赖

### 3. 目录结构重组
- [ ] 创建新的源码目录结构
```bash
mkdir -p src/{core,use_cases,adapters,infrastructure,presentation,shared}
mkdir -p src/core/{entities,value_objects,domain_services,repositories}
mkdir -p src/use_cases/{document,chat,knowledge,common}
mkdir -p src/adapters/{repositories,external_services,storage,ai}
mkdir -p src/infrastructure/{database,cache,messaging,monitoring,config}
mkdir -p src/presentation/{api,cli,web,schemas}
mkdir -p src/shared/{exceptions,utils,constants,types}
```

## 第一阶段：核心重构 (Week 1-2)

### 核心实体定义
- [ ] **Document实体** (`src/core/entities/document.py`)
  ```python
  @dataclass
  class Document:
      id: str
      title: str
      content: str
      topic_id: Optional[str] = None
      metadata: Optional[Dict[str, Any]] = None
      created_at: datetime
      updated_at: datetime
      
      def update_content(self, content: str) -> None
      def add_metadata(self, key: str, value: Any) -> None
      def get_word_count(self) -> int
  ```

- [ ] **Topic实体** (`src/core/entities/topic.py`)
  ```python
  @dataclass
  class Topic:
      id: str
      name: str
      description: Optional[str] = None
      category: Optional[str] = None
      created_at: datetime
      updated_at: datetime
      
      def update_description(self, description: str) -> None
      def set_category(self, category: str) -> None
  ```

- [ ] **ChatSession实体** (`src/core/entities/chat_session.py`)
  ```python
  @dataclass
  class ChatSession:
      id: str
      topic_id: Optional[str] = None
      messages: List[ChatMessage] = field(default_factory=list)
      created_at: datetime
      updated_at: datetime
      
      def add_message(self, message: ChatMessage) -> None
      def get_message_count(self) -> int
  ```

- [ ] **ChatMessage值对象** (`src/core/value_objects/chat_message.py`)
  ```python
  @dataclass(frozen=True)
  class ChatMessage:
      content: str
      role: MessageRole  # user, assistant, system
      timestamp: datetime
      metadata: Optional[Dict[str, Any]] = None
  ```

### 仓储接口定义
- [ ] **DocumentRepository** (`src/core/repositories/document_repository.py`)
  ```python
  class DocumentRepository(ABC):
      @abstractmethod
      async def save(self, document: Document) -> None
      @abstractmethod
      async def get_by_id(self, document_id: str) -> Optional[Document]
      @abstractmethod
      async def get_by_topic(self, topic_id: str) -> List[Document]
      @abstractmethod
      async def search(self, query: str, limit: int = 10) -> List[Document]
      @abstractmethod
      async def delete(self, document_id: str) -> bool
  ```

- [ ] **TopicRepository** (`src/core/repositories/topic_repository.py`)
- [ ] **ChatRepository** (`src/core/repositories/chat_repository.py`)

### 领域服务定义
- [ ] **DocumentProcessingService** (`src/core/domain_services/document_processing.py`)
  ```python
  class DocumentProcessingService:
      def extract_text(self, file_path: str) -> str
      def chunk_content(self, content: str) -> List[str]
      def generate_summary(self, content: str) -> str
  ```

- [ ] **VectorSearchService** (`src/core/domain_services/vector_search.py`)
- [ ] **ChatService** (`src/core/domain_services/chat.py`)

## 第二阶段：用例层实现 (Week 3-4)

### 文档管理用例
- [ ] **CreateDocumentUseCase** (`src/use_cases/document/create_document.py`)
  ```python
  class CreateDocumentUseCase:
      def __init__(self, 
                   document_repo: DocumentRepository,
                   processing_service: DocumentProcessingService,
                   vector_store: VectorStoreAdapter):
          self._document_repo = document_repo
          self._processing_service = processing_service
          self._vector_store = vector_store
      
      async def execute(self, title: str, content: str, topic_id: str) -> Document:
          # 创建文档
          # 处理内容
          # 生成向量
          # 保存到仓储
  ```

- [ ] **GetDocumentUseCase** (`src/use_cases/document/get_document.py`)
- [ ] **UpdateDocumentUseCase** (`src/use_cases/document/update_document.py`)
- [ ] **DeleteDocumentUseCase** (`src/use_cases/document/delete_document.py`)
- [ ] **SearchDocumentsUseCase** (`src/use_cases/document/search_documents.py`)
- [ ] **ProcessFileUseCase** (`src/use_cases/document/process_file.py`)

### 主题管理用例
- [ ] **CreateTopicUseCase** (`src/use_cases/knowledge/create_topic.py`)
- [ ] **GetTopicUseCase** (`src/use_cases/knowledge/get_topic.py`)
- [ ] **ListTopicsUseCase** (`src/use_cases/knowledge/list_topics.py`)
- [ ] **DeleteTopicUseCase** (`src/use_cases/knowledge/delete_topic.py`)
- [ ] **GetTopicStatisticsUseCase** (`src/use_cases/knowledge/get_topic_statistics.py`)

### 聊天用例
- [ ] **StartChatSessionUseCase** (`src/use_cases/chat/start_chat_session.py`)
- [ ] **SendMessageUseCase** (`src/use_cases/chat/send_message.py`)
  ```python
  class SendMessageUseCase:
      def __init__(self,
                   chat_repo: ChatRepository,
                   document_repo: DocumentRepository,
                   ai_service: AIServiceAdapter,
                   vector_search: VectorSearchService):
          # 依赖注入
      
      async def execute(self, session_id: str, message: str) -> ChatMessage:
          # 检索相关文档
          # 构建上下文
          # 调用AI服务
          # 保存消息历史
  ```

- [ ] **GetChatHistoryUseCase** (`src/use_cases/chat/get_chat_history.py`)
- [ ] **DeleteChatSessionUseCase** (`src/use_cases/chat/delete_chat_session.py`)

## 第三阶段：适配器层实现 (Week 5-6)

### 仓储实现
- [ ] **SQLAlchemy仓储实现**
  - [ ] `SqlAlchemyDocumentRepository` (`src/adapters/repositories/sqlalchemy_document_repository.py`)
  - [ ] `SqlAlchemyTopicRepository` (`src/adapters/repositories/sqlalchemy_topic_repository.py`)
  - [ ] `SqlAlchemyChatRepository` (`src/adapters/repositories/sqlalchemy_chat_repository.py`)

- [ ] **内存仓储实现** (开发用)
  - [ ] `MemoryDocumentRepository` (`src/adapters/repositories/memory_document_repository.py`)
  - [ ] `MemoryTopicRepository` (`src/adapters/repositories/memory_topic_repository.py`)
  - [ ] `MemoryChatRepository` (`src/adapters/repositories/memory_chat_repository.py`)

### 存储适配器
- [ ] **文件存储适配器**
  - [ ] `LocalFileStorageAdapter` (`src/adapters/storage/local_file_storage.py`)
  - [ ] `MinIOStorageAdapter` (`src/adapters/storage/minio_storage.py`)
  - [ ] `StorageAdapterFactory` (`src/adapters/storage/factory.py`)

### AI服务适配器
- [ ] **OpenAI适配器** (`src/adapters/ai/openai_adapter.py`)
  ```python
  class OpenAIAdapter(AIServiceAdapter):
      def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
          self._client = OpenAI(api_key=api_key)
          self._model = model
      
      async def generate_response(self, messages: List[ChatMessage], context: str = "") -> str:
          # 实现OpenAI API调用
  ```

- [ ] **本地模型适配器** (`src/adapters/ai/local_model_adapter.py`)
- [ ] **AI服务工厂** (`src/adapters/ai/factory.py`)

### 向量存储适配器
- [ ] **Weaviate适配器** (`src/adapters/external_services/weaviate_adapter.py`)
- [ ] **ChromaDB适配器** (`src/adapters/external_services/chroma_adapter.py`)
- [ ] **内存向量存储** (`src/adapters/external_services/memory_vector_store.py`)

## 第四阶段：基础设施层 (Week 7-8)

### 配置管理
- [ ] **环境配置** (`src/infrastructure/config/`)
  - [ ] `development.yaml` - 开发环境配置
  - [ ] `testing.yaml` - 测试环境配置
  - [ ] `production.yaml` - 生产环境配置

- [ ] **配置管理器** (`src/infrastructure/config/config_manager.py`)
  ```python
  class ConfigManager:
      def __init__(self, env: str = "development"):
          self._env = env
          self._config = self._load_config()
      
      def get_database_config(self) -> DatabaseConfig
      def get_ai_config(self) -> AIConfig
      def get_storage_config(self) -> StorageConfig
  ```

### 数据库配置
- [ ] **数据库连接管理** (`src/infrastructure/database/connection.py`)
- [ ] **模型定义** (`src/infrastructure/database/models.py`)
- [ ] **迁移脚本** (`src/infrastructure/database/migrations/`)

### 缓存配置
- [ ] **Redis缓存** (`src/infrastructure/cache/redis_cache.py`)
- [ ] **内存缓存** (`src/infrastructure/cache/memory_cache.py`)
- [ ] **缓存工厂** (`src/infrastructure/cache/factory.py`)

### 监控配置
- [ ] **日志配置** (`src/infrastructure/monitoring/logging.py`)
- [ ] **指标收集** (`src/infrastructure/monitoring/metrics.py`)
- [ ] **健康检查** (`src/infrastructure/monitoring/health.py`)

## 第五阶段：表现层重构 (Week 9-10)

### API控制器
- [ ] **文档API** (`src/presentation/api/document_controller.py`)
  ```python
  class DocumentController:
      def __init__(self, container: Container):
          self._create_document = container.create_document_use_case()
          self._get_document = container.get_document_use_case()
          # 其他用例注入
      
      @router.post("/documents")
      async def create_document(self, request: CreateDocumentRequest) -> DocumentResponse:
          document = await self._create_document.execute(
              title=request.title,
              content=request.content,
              topic_id=request.topic_id
          )
          return DocumentResponse.from_entity(document)
  ```

- [ ] **主题API** (`src/presentation/api/topic_controller.py`)
- [ ] **聊天API** (`src/presentation/api/chat_controller.py`)
- [ ] **系统API** (`src/presentation/api/system_controller.py`)

### CLI界面
- [ ] **CLI重构** (`src/presentation/cli/main.py`)
- [ ] **命令处理器** (`src/presentation/cli/commands/`)
- [ ] **CLI配置** (`src/presentation/cli/config.py`)

### 数据传输对象
- [ ] **请求/响应模型** (`src/presentation/schemas/`)
  - [ ] `document_schemas.py`
  - [ ] `topic_schemas.py`
  - [ ] `chat_schemas.py`

## 第六阶段：依赖注入和测试 (Week 11-12)

### 依赖注入容器
- [ ] **主容器** (`src/shared/di/container.py`)
  ```python
  class Container(containers.DeclarativeContainer):
      # 配置
      config = providers.Configuration()
      
      # 基础设施
      database = providers.Singleton(DatabaseConnection, config=config.database)
      cache = providers.Factory(CacheFactory.create, config=config.cache)
      
      # 仓储
      document_repository = providers.Factory(
          RepositoryFactory.create_document_repository,
          session=database.provided.session
      )
      
      # 用例
      create_document_use_case = providers.Factory(
          CreateDocumentUseCase,
          document_repo=document_repository
      )
  ```

- [ ] **工厂类** (`src/shared/di/factories.py`)
- [ ] **容器配置** (`src/shared/di/config.py`)

### 测试框架
- [ ] **测试基类** (`tests/base.py`)
- [ ] **测试工厂** (`tests/factories/`)
- [ ] **Mock对象** (`tests/mocks/`)
- [ ] **测试数据** (`tests/fixtures/`)

### 单元测试
- [ ] **实体测试** (`tests/unit/core/entities/`)
- [ ] **用例测试** (`tests/unit/use_cases/`)
- [ ] **适配器测试** (`tests/unit/adapters/`)

### 集成测试
- [ ] **API测试** (`tests/integration/api/`)
- [ ] **数据库测试** (`tests/integration/database/`)
- [ ] **外部服务测试** (`tests/integration/external_services/`)

## 开发工具和脚本

### 开发脚本
- [ ] **启动脚本** (`scripts/dev/start.sh`)
  ```bash
  #!/bin/bash
  # 检查环境
  # 启动必要服务
  # 运行应用
  ```

- [ ] **测试脚本** (`scripts/dev/test.sh`)
- [ ] **代码检查脚本** (`scripts/dev/lint.sh`)
- [ ] **数据库迁移脚本** (`scripts/dev/migrate.sh`)

### 部署脚本
- [ ] **Docker配置** (`docker/`)
  - [ ] `Dockerfile.development`
  - [ ] `Dockerfile.production`
  - [ ] `docker-compose.dev.yml`
  - [ ] `docker-compose.prod.yml`

### IDE配置
- [ ] **VSCode配置** (`.vscode/`)
  - [ ] `settings.json`
  - [ ] `launch.json`
  - [ ] `tasks.json`

## 文档完善

### 技术文档
- [x] 当前架构分析
- [x] Clean Architecture设计
- [x] 重构计划
- [ ] API文档
- [ ] 数据库设计文档
- [ ] 部署指南

### 用户文档
- [ ] 快速开始指南
- [ ] 使用教程
- [ ] 常见问题解答
- [ ] 故障排除指南

### 开发文档
- [ ] 贡献指南
- [ ] 代码规范
- [ ] 测试指南
- [ ] 发布流程

## 质量保证

### 代码质量
- [ ] 设置pre-commit hooks
- [ ] 配置代码格式化工具 (black, isort)
- [ ] 配置代码检查工具 (flake8, mypy)
- [ ] 设置测试覆盖率要求 (>90%)

### 性能优化
- [ ] 数据库查询优化
- [ ] 缓存策略实现
- [ ] 异步处理优化
- [ ] 内存使用优化

### 安全加固
- [ ] 输入验证
- [ ] 认证授权
- [ ] 敏感数据加密
- [ ] API限流

## 发布准备

### 版本管理
- [ ] 语义化版本号
- [ ] 变更日志
- [ ] 发布说明
- [ ] 迁移指南

### 部署准备
- [ ] 生产环境配置
- [ ] 监控告警设置
- [ ] 备份恢复方案
- [ ] 回滚方案

## 持续改进

### 监控和反馈
- [ ] 用户反馈收集
- [ ] 性能指标监控
- [ ] 错误率追踪
- [ ] 使用情况分析

### 架构演进
- [ ] 架构健康度评估
- [ ] 技术债务管理
- [ ] 新技术评估
- [ ] 重构规划

---

**注意事项：**
1. 每个任务完成后都要更新测试
2. 重要变更需要进行代码审查
3. 保持向后兼容性
4. 及时更新文档
5. 定期进行架构评审

**优先级说明：**
- 🔴 高优先级：影响系统稳定性和开发效率
- 🟡 中优先级：改善代码质量和可维护性
- 🟢 低优先级：增强功能和用户体验

这个TODO清单提供了详细的实施路径，可以根据实际情况调整优先级和时间安排。