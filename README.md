# Research Agent RAG System

一个基于多智能体的研究论文分析和讨论系统，支持多种 LLM 提供商（OpenAI、DeepSeek、Anthropic）。

## ✨ 产品功能亮点

### 🎯 AI协作研究台
- **智能论文检索**: 基于ArXiv API的实时论文搜索和相关性评分
- **多AI代理协作**: MIT研究员、Google工程师、行业专家、论文分析师四大专业AI助手
- **实时讨论分析**: AI代理间的协作讨论，展示不同视角的深度分析
- **研究工作流**: 从问题提出到报告生成的完整研究流程

### 📚 智能论文库
- **论文收藏管理**: 支持分类、标签、评分的个人论文库
- **AI深度分析**: 每篇论文的多维度AI分析和洞察
- **引用网络**: 论文间关系和引用分析可视化
- **批量导入**: 支持多种格式的论文批量导入

### 📊 研究项目管理
- **项目生命周期**: 从创建到完成的全流程项目跟踪
- **进度可视化**: 实时项目进度和AI代理工作状态
- **协作功能**: 支持团队协作和研究成果分享
- **版本控制**: 研究过程和结果的版本管理

### 📄 智能报告生成
- **自动化报告**: 基于AI分析结果的研究报告自动生成
- **多格式输出**: 支持Markdown、PDF、Word、LaTeX等格式
- **模板定制**: 可定制的报告模板和样式
- **一键分享**: 报告的在线发布和分享功能

### 🤖 AI代理管理
- **性能监控**: 实时监控AI代理的工作状态和性能指标
- **配置管理**: 灵活的AI模型参数和行为配置
- **协作分析**: AI代理间的协作模式和效果评估
- **多供应商支持**: OpenAI、DeepSeek、Anthropic等多种LLM提供商

## 🏗️ 项目结构

```
research-agent-rag/
├── backend/                    # 后端代码
│   ├── api/                   # API 服务器
│   ├── agents/                # AI 代理
│   ├── chat/                  # 聊天接口
│   ├── database/              # 数据库相关
│   ├── retrieval/             # 论文检索
│   ├── utils/                 # 工具函数
│   ├── config.py              # 配置
│   ├── main.py                # 主入口
│   └── requirements.txt       # 依赖
├── frontend/                  # 前端代码
│   └── ... (Next.js 应用)
├── infra/                     # 基础设施
│   ├── docker/                # Docker 配置
│   ├── k8s/                   # Kubernetes 配置
│   ├── nginx/                 # Nginx 配置
│   └── scripts/               # 部署脚本
├── docs/                      # 文档
├── tests/                     # 测试
└── Makefile                   # 构建脚本
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Node.js 18+ (for frontend)

### 1. Setup Project
```bash
# Clone the repository
git clone <repository-url>
cd research-agent-rag

# Install dependencies
make setup

# Configure environment
cp infra/docker/env.template .env
# Edit .env and add your API keys
```

### 2. Start Services

#### Option A: Start All Services (Recommended)
```bash
# Start all middleware services (PostgreSQL, Redis, Weaviate, Elasticsearch, Kibana)
make docker-start-middleware

# Start the API server
make run-api

# Start the frontend
make run-frontend
```

#### Option B: Quick Elasticsearch Setup
```bash
# Use the quick start script
./scripts/start-elasticsearch.sh middleware

# Or manually start services
cd infra/docker
docker-compose -f docker-compose.middleware.yml up -d
```

### 3. Access Services
- **API Server**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **Weaviate**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Test the System
```bash
# Run comprehensive tests
make test

# Test Elasticsearch integration
make test-elasticsearch

# Check service health
make docker-health
```

## 🛠️ 开发

### 代码质量

```bash
# 格式化代码
make format

# 代码检查
make lint

# 运行测试
make test
```

### 构建和部署

```bash
# 构建所有组件
make build

# Docker 部署
make docker-build
make docker-run

# Kubernetes 部署
make deploy-k8s
```

## 📚 功能特性

### 🤖 多智能体系统

- **Google Engineer Agent**: 工程实践和实现建议
- **MIT Researcher Agent**: 学术研究和理论分析
- **Industry Expert Agent**: 行业应用和商业价值
- **Paper Analyst Agent**: 论文深度分析

### 🔍 智能检索

- **ArXiv API 集成**: 实时论文检索
- **向量数据库**: 语义相似性搜索
- **查询扩展**: 智能查询优化
- **分页支持**: 大规模数据检索

### 💬 多提供商支持

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **DeepSeek**: DeepSeek-V3, DeepSeek-Coder
- **Anthropic**: Claude-3, Claude-2

### 🎨 现代化 UI

- **Streamlit**: 快速原型界面
- **Next.js**: 现代 React 应用
- **Tailwind CSS**: 响应式设计
- **实时更新**: 动态数据展示

## 🏗️ 架构设计

### 后端架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Research      │    │   Vector        │
│   Server        │◄──►│   Orchestrator  │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Multi-Agent   │    │   ArXiv Client  │    │   Embedding     │
│   System        │    │   & Retrieval   │    │   Models        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 前端架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   API Client    │    │   Backend       │
│   Frontend      │◄──►│   & Hooks       │◄──►│   FastAPI       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tailwind CSS  │    │   SWR Data      │    │   Multi-LLM     │
│   & Components  │    │   Fetching      │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 配置选项

### 环境变量

```bash
# API 密钥
OPENAI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# 默认提供商
DEFAULT_PROVIDER=deepseek

# 数据库配置
VECTOR_DB_PATH=./data/vector_db

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

### 智能体配置

每个智能体可以独立配置：

```python
# 在 config.py 中
AGENT_CONFIGS = {
    "google_engineer": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7
    },
    "mit_researcher": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "temperature": 0.8
    }
}
```

## 🐳 Docker 支持

### 开发环境

```bash
# 构建镜像
make docker-build

# 运行容器
make docker-run

# 停止容器
make docker-stop
```

### 生产部署

```bash
# 使用 Docker Compose
docker-compose -f infra/docker/docker-compose.yml up -d

# 使用 Kubernetes
make deploy-k8s
```

## 📊 监控和日志

```bash
# 查看日志
make logs

# 检查状态
make status

# 健康检查
curl http://localhost:8000/health
```

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 运行特定测试
cd backend && poetry run pytest tests/test_specific.py
```

## 📖 API 文档

启动服务器后，访问：
- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [ArXiv API](https://arxiv.org/help/api) - 论文检索
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Next.js](https://nextjs.org/) - React 框架
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架

## 📞 支持

如果您遇到问题或有建议，请：
1. 查看 [Issues](../../issues)
2. 创建新的 Issue
3. 联系维护者

---

**Happy Researching! 🚀**