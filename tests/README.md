# RAG知识管理系统 - 集成测试

本目录包含RAG知识管理系统的全栈集成测试，测试所有API端点和服务层的真实功能。

## 🎯 测试目标

- **真实环境测试**: 使用真实的PostgreSQL数据库，拒绝任何mock数据
- **全栈覆盖**: 测试从API层到数据库层的每一层真实逻辑
- **完整工作流**: 测试端到端的业务流程
- **错误处理**: 验证系统的错误处理和恢复机制
- **性能验证**: 基本的并发和性能测试

## 🏗️ 测试架构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # pytest配置和fixtures
├── pytest.ini                 # pytest配置文件
├── run_integration_tests.py    # 测试运行脚本
└── integration/               # 集成测试
    ├── __init__.py
    ├── test_topics_api.py      # 主题API测试
    ├── test_files_api.py       # 文件API测试
    ├── test_documents_api.py   # 文档API测试
    ├── test_resources_api.py   # 资源API测试
    ├── test_database.py        # 数据库集成测试
    └── test_full_stack.py      # 全栈工作流测试
```

## 🚀 快速开始

### 前提条件

1. **PostgreSQL数据库**: 确保PostgreSQL运行在localhost:5432
   - 用户: `rag_user`
   - 密码: `rag_password`
   - 测试数据库: `rag_test_db`（会自动创建）

2. **Python依赖**: 安装测试依赖
   ```bash
   pip install pytest pytest-asyncio httpx fastapi sqlalchemy asyncpg
   ```

### 运行所有集成测试

```bash
# 使用测试运行脚本（推荐）
python tests/run_integration_tests.py

# 或直接使用pytest
pytest tests/integration/ -m integration -v
```

### 运行特定测试类别

```bash
# 只运行API测试
pytest tests/integration/ -m api -v

# 只运行数据库测试
pytest tests/integration/ -m database -v

# 只运行全栈测试
pytest tests/integration/ -m fullstack -v

# 运行特定文件
pytest tests/integration/test_topics_api.py -v
```

### 高级选项

```bash
# 详细输出和覆盖率报告
python tests/run_integration_tests.py --verbose --coverage

# 过滤特定测试
python tests/run_integration_tests.py --test-filter "test_create"

# 只设置环境不运行测试
python tests/run_integration_tests.py --setup-only

# 跳过环境检查
python tests/run_integration_tests.py --skip-checks
```

## 📋 测试清单

### ✅ 主题API测试 (Topics API)
- [x] 创建主题
- [x] 获取主题详情
- [x] 更新主题信息
- [x] 删除主题
- [x] 列出主题（分页）
- [x] 搜索主题
- [x] 向主题添加文件
- [x] 错误处理（404, 422）
- [x] 完整工作流测试

### ✅ 文件API测试 (Files API)
- [x] 生成签名上传URL
- [x] 确认文件上传
- [x] 获取文件详情
- [x] 更新文件元数据
- [x] 删除文件
- [x] 列出文件（分页）
- [x] 搜索文件
- [x] 直接文件上传
- [x] 文件验证错误
- [x] 完整工作流测试

### ✅ 文档API测试 (Documents API)
- [x] 创建文档记录
- [x] 获取文档详情
- [x] 更新文档内容
- [x] 删除文档
- [x] 列出文档（分页）
- [x] 处理文档（分块和向量化）
- [x] 获取文档分块
- [x] 搜索文档
- [x] 从文件创建文档
- [x] 验证错误处理
- [x] 完整工作流测试

### ✅ 资源API测试 (Resources API)
- [x] 创建资源
- [x] 获取资源详情
- [x] 更新资源信息
- [x] 删除资源
- [x] 列出资源（分页）
- [x] 搜索资源
- [x] 按主题获取资源
- [x] 验证错误处理
- [x] 完整工作流测试

### ✅ 数据库集成测试
- [x] 数据库连接测试
- [x] 主题模型CRUD操作
- [x] 文件模型CRUD操作
- [x] 文档模型CRUD操作
- [x] 模型关系和外键测试
- [x] 数据库约束验证
- [x] 复杂查询和过滤
- [x] 事务回滚测试
- [x] 批量操作测试

### ✅ 全栈集成测试
- [x] 完整知识管理工作流
  - 创建主题 → 上传文件 → 创建文档 → 处理文档 → 搜索验证
- [x] 多主题交叉引用工作流
  - 多主题创建 → 交叉引用内容 → 跨主题搜索
- [x] 错误处理和恢复工作流
  - 无效数据处理 → 约束违规 → 系统恢复验证
- [x] 基本性能和可扩展性测试
  - 并发操作 → 批量处理 → 数据一致性验证

## 🔧 测试配置

### 环境变量
```bash
# 测试数据库配置
TEST_DATABASE_URL="postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_test_db"

# 可选：覆盖默认配置
TEST_MINIO_ENDPOINT="localhost:9000"
TEST_REDIS_URL="redis://localhost:6379"
```

### 数据库设置
测试使用独立的测试数据库，每个测试函数都会：
1. 创建干净的数据库表结构
2. 执行测试逻辑
3. 完全清理所有数据

这确保了：
- 测试之间完全隔离
- 不影响开发或生产数据
- 可重复运行测试

## 📊 测试覆盖

### API端点覆盖
- **主题API**: 8个端点，100%覆盖
- **文件API**: 7个端点，100%覆盖
- **文档API**: 8个端点，100%覆盖
- **资源API**: 6个端点，100%覆盖

### 服务层覆盖
- **TopicService**: 所有主要方法
- **FileService**: 所有主要方法
- **DocumentService**: 所有主要方法
- **数据库操作**: CRUD + 复杂查询

### 错误场景覆盖
- HTTP 400/404/422错误
- 数据验证错误
- 数据库约束违规
- 并发操作冲突

## 🚨 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查PostgreSQL是否运行
   pg_isready -h localhost -p 5432
   
   # 检查用户权限
   psql -U rag_user -h localhost -d postgres
   ```

2. **导入模块错误**
   ```bash
   # 确保在项目根目录运行
   cd /path/to/research-agent-rag
   python tests/run_integration_tests.py
   ```

3. **测试超时**
   ```bash
   # 增加pytest超时时间
   pytest tests/integration/ --timeout=300
   ```

4. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :8000
   ```

### 调试测试

```bash
# 运行单个测试用于调试
pytest tests/integration/test_topics_api.py::TestTopicsAPI::test_create_topic -v -s

# 保留测试数据库用于检查
pytest tests/integration/ --keep-duplicates

# 显示详细的错误信息
pytest tests/integration/ -v --tb=long
```

## 📈 性能基准

基于基本性能测试的参考指标：

- **并发主题创建**: 10个主题 < 2秒
- **并发文件上传**: 5个文件 < 3秒  
- **并发文档处理**: 5个文档 < 5秒
- **并发搜索操作**: 5个搜索 < 2秒
- **数据一致性**: 100%在所有并发操作后

## 🔍 持续改进

### 计划中的测试增强
- [ ] 更大规模的性能测试
- [ ] 内存使用监控
- [ ] 网络延迟模拟
- [ ] 数据库负载测试
- [ ] 安全性测试

### 贡献指南
1. 所有新功能必须有对应的集成测试
2. 测试必须使用真实数据库，不使用mock
3. 测试必须能独立运行和并发运行
4. 测试应该包含错误场景验证
5. 性能关键的功能需要性能测试

## 📞 支持

如果遇到测试问题，请检查：
1. 数据库服务是否运行
2. 所有依赖是否已安装
3. 网络端口是否可用
4. 项目路径是否正确

更多问题请参考项目主README或提交issue。