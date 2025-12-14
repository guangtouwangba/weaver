# 🐳 DevContainer 开发环境

使用 VS Code DevContainer 一键启动完整的开发环境，包括 PostgreSQL、Redis 和所有依赖。

## 🚀 快速开始

### 前提条件

1. **安装 VS Code**
   - 下载: https://code.visualstudio.com/

2. **安装 Docker Desktop**
   - macOS/Windows: https://www.docker.com/products/docker-desktop
   - Linux: https://docs.docker.com/engine/install/

3. **安装 Dev Containers 扩展**
   - 在 VS Code 中搜索 "Dev Containers"
   - 或访问: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers

### 启动步骤

1. **打开项目**
   ```bash
   code /path/to/research-agent-rag
   ```

2. **打开 DevContainer**
   - VS Code 会提示 "Reopen in Container"，点击确认
   - 或者按 `F1` → 输入 "Dev Containers: Reopen in Container"

3. **等待初始化**
   - 首次启动会构建容器（约 3-5 分钟）
   - 自动安装所有 Python 依赖
   - 启动 PostgreSQL 和 Redis
   - 运行数据库迁移

4. **开始开发！**
   - 所有服务已就绪
   - 终端已配置好虚拟环境
   - VS Code 扩展已自动安装

## 📋 容器内服务

### 数据库服务

| 服务 | 主机 | 端口 | 用户名 | 密码 |
|------|------|------|--------|------|
| PostgreSQL | `postgres` | 5432 | `postgres` | `password` |
| Redis | `redis` | 6379 | - | - |

### 应用端口

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI | 8000 | API 服务 |
| Vite | 5173 | 前端开发服务器 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |

## 🛠️ 常用命令

### 启动服务

```bash
# 启动 API
make run
# 或
python start_backend.py

# 启动前端（在另一个终端）
cd apps/web
npm run dev
```

### 开发工具

```bash
# 运行测试
make test

# 代码检查
make lint

# 代码格式化
make format

# 数据库迁移
python migrate_db.py

# 诊断配置
python diagnose_langextract_config.py
```

### 数据库操作

```bash
# 连接 PostgreSQL
psql -h postgres -U postgres -d knowledge_platform

# 查看数据库
psql -h postgres -U postgres -l

# Redis CLI
redis-cli -h redis
```

## 🔧 配置

### 环境变量

容器启动后会自动创建 `.env` 文件（从 `env.example` 复制）。

编辑 `.env` 文件，添加必要的配置：

```bash
# OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# LangExtract 配置
LANGEXTRACT_PROVIDER=openrouter
LANGEXTRACT_MODEL_ID=anthropic/claude-3-haiku
DOCUMENT_PARSER_TYPE=langextract
```

### 数据库连接

容器内的数据库连接字符串（已自动配置）：

```
DATABASE_URL=postgresql://postgres:password@postgres:5432/knowledge_platform
```

## 📦 已安装的工具

### Python 包
- ✅ 项目所有依赖（从 `pyproject.toml`）
- ✅ langextract
- ✅ 开发工具（pytest, ruff, black）
- ✅ IPython（交互式 Python）

### 系统工具
- ✅ git
- ✅ curl, wget
- ✅ PostgreSQL 客户端 (psql)
- ✅ Redis CLI
- ✅ vim, nano
- ✅ uv (快速包管理器)

### VS Code 扩展
- ✅ Python (Pylance, 调试)
- ✅ Ruff (代码检查)
- ✅ Docker
- ✅ SQLTools (数据库管理)
- ✅ GitLens
- ✅ ESLint, Prettier (前端)

## 🔄 重建容器

如果需要重建容器（例如更新了 Dockerfile）：

1. 按 `F1`
2. 输入 "Dev Containers: Rebuild Container"
3. 等待重建完成

## 🐛 故障排查

### 问题 1: 容器启动失败

```bash
# 检查 Docker 是否运行
docker ps

# 查看日志
docker-compose logs

# 重新构建
docker-compose build --no-cache
```

### 问题 2: PostgreSQL 连接失败

```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres

# 查看 PostgreSQL 日志
docker-compose logs postgres

# 重启 PostgreSQL
docker-compose restart postgres
```

### 问题 3: 端口冲突

如果端口已被占用，编辑 `docker-compose.yml` 修改端口映射：

```yaml
ports:
  - "8001:8000"  # 使用 8001 代替 8000
```

### 问题 4: 依赖安装失败

```bash
# 手动重新安装
source venv/bin/activate
uv pip install -e .
```

## 💡 提示

### 持久化数据

以下数据会持久化（容器删除后保留）：
- ✅ PostgreSQL 数据（`postgres_data` volume）
- ✅ Redis 数据（`redis_data` volume）
- ✅ Python 虚拟环境（`venv` volume）
- ✅ 项目文件（挂载到容器）

### 性能优化

容器使用 `cached` 一致性模式，提供最佳性能：
- 文件修改会立即反映在容器中
- Python 包缓存会持久化

### 多终端

VS Code 支持在容器内打开多个终端：
- Terminal 1: 运行 API
- Terminal 2: 运行前端
- Terminal 3: 交互式开发/测试

## 📚 更多信息

- [VS Code DevContainer 文档](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [项目 README](../README.md)
- [安装指南](../INSTALL.md)

## 🎯 优势

使用 DevContainer 的好处：

1. **一致的开发环境** - 所有开发者使用相同的环境
2. **快速启动** - 新成员几分钟内可以开始开发
3. **隔离** - 不污染本地系统
4. **完整服务** - PostgreSQL、Redis 自动配置
5. **预配置工具** - VS Code 扩展和设置自动安装
6. **跨平台** - 在 macOS、Windows、Linux 上一致

## 🚀 下一步

容器启动后：

1. ✅ 编辑 `.env` 文件配置 API Keys
2. ✅ 运行 `make run` 启动 API
3. ✅ 访问 http://localhost:8000 测试 API
4. ✅ 开始开发！

---

**Happy Coding!** 🎉

