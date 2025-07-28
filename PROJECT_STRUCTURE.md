# 项目结构文档

## 📁 目录结构

```
research-agent-rag/
├── backend/                    # 后端代码
│   ├── api/                   # API 服务器文件
│   │   ├── simple_server.py   # 简化的 FastAPI 服务器
│   │   ├── server.py          # 完整的 API 服务器
│   │   ├── server_backup.py   # 服务器备份
│   │   ├── cronjob_service.py # 定时任务服务
│   │   ├── batch_processor.py # 批处理器
│   │   └── cronjob_routes.py  # 定时任务路由
│   ├── agents/                # AI 智能体
│   │   ├── base_agent.py      # 基础智能体类
│   │   ├── google_engineer_agent.py
│   │   ├── mit_researcher_agent.py
│   │   ├── industry_expert_agent.py
│   │   ├── paper_analyst_agent.py
│   │   └── orchestrator.py    # 智能体编排器
│   ├── chat/                  # 聊天接口
│   │   └── chat_interface.py  # Streamlit 聊天界面
│   ├── database/              # 数据库相关
│   │   └── vector_store.py    # 向量数据库存储
│   ├── retrieval/             # 论文检索
│   │   └── arxiv_client.py    # ArXiv API 客户端
│   ├── utils/                 # 工具函数
│   │   ├── ai_client.py       # AI 客户端抽象
│   │   └── query_expansion.py # 查询扩展
│   ├── config.py              # 配置管理
│   ├── main.py                # 主入口
│   ├── config_manager.py      # 配置管理器
│   ├── requirements.txt       # Python 依赖
│   └── requirements.serverless.txt # 无服务器依赖
├── frontend/                  # 前端代码
│   ├── app/                   # Next.js 应用
│   │   ├── (dashboard)/       # 仪表板页面
│   │   ├── globals.css        # 全局样式
│   │   └── layout.tsx         # 根布局
│   ├── components/            # React 组件
│   │   └── ui/                # UI 组件
│   ├── lib/                   # 工具库
│   │   ├── api.ts             # API 客户端
│   │   ├── hooks/             # React Hooks
│   │   └── utils.ts           # 工具函数
│   ├── package.json           # Node.js 依赖
│   ├── next.config.js         # Next.js 配置
│   ├── tailwind.config.ts     # Tailwind CSS 配置
│   └── postcss.config.js      # PostCSS 配置
├── infra/                     # 基础设施
│   ├── docker/                # Docker 配置
│   │   ├── Dockerfile         # 主 Dockerfile
│   │   ├── Dockerfile.serverless # 无服务器 Dockerfile
│   │   ├── Dockerfile.scheduler # 调度器 Dockerfile
│   │   ├── docker-compose.yml # Docker Compose
│   │   ├── docker-compose.cronjobs.yml # 定时任务 Compose
│   │   └── .dockerignore      # Docker 忽略文件
│   ├── k8s/                   # Kubernetes 配置
│   │   └── ...                # K8s 部署文件
│   ├── nginx/                 # Nginx 配置
│   │   └── nginx.conf         # Nginx 配置文件
│   ├── scripts/               # 部署脚本
│   │   └── build.sh           # 构建脚本
│   ├── scheduler/             # 调度器
│   │   └── ...                # 定时任务相关
│   ├── .env.development       # 开发环境配置
│   └── .env.production        # 生产环境配置
├── docs/                      # 文档
│   ├── conf.py                # Sphinx 配置
│   ├── index.rst              # 文档首页
│   └── Makefile               # 文档构建
├── tests/                     # 测试
│   ├── test_basic.py          # 基础测试
│   └── ...                    # 其他测试文件
├── data/                      # 数据目录
│   └── vector_db/             # 向量数据库文件
├── logs/                      # 日志文件
├── examples/                  # 示例代码
│   └── demo.py                # 演示脚本
├── Makefile                   # 构建脚本
├── README.md                  # 项目说明
├── PROJECT_STRUCTURE.md       # 项目结构文档
├── pyproject.toml             # Poetry 配置
├── poetry.lock                # Poetry 锁定文件
└── .pre-commit-config.yaml    # Pre-commit 配置
```

## 🔧 关键文件说明

### 后端核心文件

- **`backend/config.py`**: 配置管理，支持多 LLM 提供商
- **`backend/main.py`**: 主入口点，支持 CLI 和 API 模式
- **`backend/agents/orchestrator.py`**: 多智能体编排器
- **`backend/api/simple_server.py`**: 简化的 FastAPI 服务器
- **`backend/utils/ai_client.py`**: AI 客户端抽象层

### 前端核心文件

- **`frontend/app/(dashboard)/page.tsx`**: 仪表板页面
- **`frontend/lib/api.ts`**: API 客户端
- **`frontend/lib/hooks/api-hooks.ts`**: React Hooks
- **`frontend/next.config.js`**: Next.js 配置

### 基础设施文件

- **`infra/docker/Dockerfile`**: 主 Docker 镜像
- **`infra/docker/docker-compose.yml`**: Docker Compose 配置
- **`infra/k8s/`**: Kubernetes 部署文件
- **`infra/nginx/nginx.conf`**: Nginx 配置

## 🚀 开发工作流

### 1. 后端开发

```bash
# 进入后端目录
cd backend

# 安装依赖
poetry install

# 运行开发服务器
poetry run python simple_server.py

# 运行测试
poetry run pytest

# 代码格式化
poetry run black .
poetry run isort .
```

### 2. 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 3. 全栈开发

```bash
# 使用 Makefile 命令
make run-fullstack  # 同时启动前后端
make run-api        # 只启动后端
make run-frontend   # 只启动前端
```

## 📦 部署选项

### 1. Docker 部署

```bash
# 构建镜像
make docker-build

# 运行容器
make docker-run

# 使用 Docker Compose
docker-compose -f infra/docker/docker-compose.yml up -d
```

### 2. Kubernetes 部署

```bash
# 部署到 K8s
make deploy-k8s

# 或者手动部署
kubectl apply -f infra/k8s/
```

### 3. 无服务器部署

```bash
# 使用无服务器 Dockerfile
docker build -f infra/docker/Dockerfile.serverless .
```

## 🔄 迁移指南

### 从旧结构迁移

如果您从旧的项目结构迁移，需要注意：

1. **后端路径变化**: 所有后端代码现在在 `backend/` 目录
2. **基础设施整合**: Docker 和 K8s 配置现在在 `infra/` 目录
3. **导入路径更新**: Python 导入路径已更新以适应新结构

### 更新导入路径

```python
# 旧路径
from config import Config
from agents.orchestrator import ResearchOrchestrator

# 新路径 (在 backend/ 目录中)
from config import Config
from agents.orchestrator import ResearchOrchestrator
```

## 📊 监控和日志

### 日志位置

- **应用日志**: `logs/` 目录
- **Docker 日志**: `docker logs <container_name>`
- **K8s 日志**: `kubectl logs <pod_name>`

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 前端健康检查
curl http://localhost:3000

# 使用 Makefile
make status
```

## 🛠️ 维护命令

```bash
# 清理构建文件
make clean

# 更新依赖
make update-deps

# 安全检查
make security-check

# 查看日志
make logs
```

## 📝 注意事项

1. **环境变量**: 确保 `.env` 文件在项目根目录
2. **端口配置**: 后端默认端口 8000，前端默认端口 3000
3. **依赖管理**: 后端使用 Poetry，前端使用 npm
4. **开发模式**: 使用 `make dev` 快速启动开发环境

---

这个新的项目结构提供了更好的组织性和可维护性，同时保持了所有现有功能的完整性。 