# Research Agent RAG System

一个基于多智能体的研究论文分析和讨论系统，支持多种 LLM 提供商（OpenAI、DeepSeek、Anthropic）。

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

## 🚀 快速开始

### 1. 安装依赖

```bash
# 完整设置（推荐）
make setup

# 或者分步安装
make install-dev
make setup-env
```

### 2. 配置 API 密钥

编辑 `.env` 文件，添加您的 API 密钥：

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key
```

### 3. 运行应用

```bash
# 运行演示
make run-demo

# 运行 Web 界面
make run-web

# 运行现代 UI
make run-frontend

# 运行完整栈（后端 + 前端）
make run-fullstack
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