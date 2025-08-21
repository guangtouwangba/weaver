# RAG知识管理系统 - 完整测试框架

本目录包含RAG知识管理系统的完整测试框架，包括单元测试、集成测试、端到端测试和性能测试。

## 🎯 测试架构

### 测试层级结构
```
tests/
├── unit/                    # 单元测试
│   ├── schemas/            # Schema验证测试
│   ├── services/           # 业务逻辑测试  
│   ├── repositories/       # 数据访问测试
│   ├── api/               # API层测试
│   └── utils/             # 工具函数测试
├── integration/            # 集成测试
│   ├── api/               # API端点集成测试
│   ├── database/          # 数据库集成测试
│   └── workflows/         # 工作流集成测试
├── e2e/                   # 端到端测试
│   ├── scenarios/         # 完整业务场景测试
│   └── performance/       # 性能和负载测试
├── conftest.py            # 测试配置和fixtures
├── utils.py               # 测试工具和数据工厂
├── run_tests.py           # 综合测试运行器
├── run_integration_tests.py # 集成测试运行器
└── README.md              # 测试文档
```

## 🚀 快速开始

### 环境准备
```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov httpx faker

# 启动中间件服务
make start

# 初始化测试数据库
make db-init
```

### 运行测试

#### 使用综合测试运行器 (推荐)
```bash
# 运行所有测试
python tests/run_tests.py all --coverage --verbose

# 仅运行单元测试
python tests/run_tests.py unit --coverage

# 仅运行集成测试
python tests/run_tests.py integration --verbose

# 仅运行端到端测试
python tests/run_tests.py e2e

# 运行性能测试
python tests/run_tests.py performance

# 快速运行(跳过慢速测试)
python tests/run_tests.py all --fast

# 运行冒烟测试
python tests/run_tests.py smoke

# 自定义测试选择
python tests/run_tests.py custom --pattern "test_topic*" --markers "not slow"
```

## 📋 测试类型详解

### 1. 单元测试 (Unit Tests)
- **位置**: `tests/unit/`
- **标记**: `@pytest.mark.unit`
- **目标**: 测试单个组件的功能正确性
- **特点**: 快速执行、隔离测试、高覆盖率

### 2. 集成测试 (Integration Tests)
- **位置**: `tests/integration/`
- **标记**: `@pytest.mark.integration`
- **目标**: 测试组件间协作和真实环境交互
- **特点**: 使用真实数据库、无Mock策略、完整HTTP测试

### 3. 端到端测试 (End-to-End Tests)
- **位置**: `tests/e2e/`
- **标记**: `@pytest.mark.e2e`
- **目标**: 测试完整用户工作流和系统集成
- **特点**: 模拟真实用户场景、跨服务通信测试

### 4. 性能测试 (Performance Tests)
- **位置**: `tests/e2e/performance/`
- **标记**: `@pytest.mark.performance`
- **目标**: 验证系统性能和可扩展性
- **特点**: 响应时间基准、并发负载测试

## 📊 测试覆盖率

### 当前覆盖率目标
- **单元测试**: > 90%
- **集成测试**: > 80%
- **API端点**: 100%
- **核心业务逻辑**: > 95%

## 🚨 故障排除

### 常见问题
1. **数据库连接失败**: 检查PostgreSQL服务状态
2. **导入模块错误**: 确保在项目根目录运行
3. **测试超时**: 增加pytest超时时间
4. **内存不足**: 限制并发测试数量

## 📈 性能基准

### API性能基准
| 端点类型 | 目标响应时间 | 并发支持 |
|---------|-------------|----------|
| 健康检查 | < 100ms | 无限制 |
| 主题CRUD | < 500ms | 50并发 |
| 文件上传 | < 2s/MB | 20并发 |
| 文档搜索 | < 2s | 30并发 |

## 🔍 持续改进

### 计划中的测试增强
- [ ] 更大规模的性能测试
- [ ] 内存泄露检测
- [ ] 网络延迟模拟
- [ ] 数据库负载测试
- [ ] 安全性测试

测试框架的核心目标是验证RAG知识管理系统的真实可用性和性能表现。