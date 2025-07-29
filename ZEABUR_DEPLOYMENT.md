# Zeabur 部署指南

本指南将帮助你将 Research Agent RAG 系统部署到 Zeabur 平台上。

## 📋 部署前准备

### 1. 环境变量配置

在 Zeabur 控制台中设置以下环境变量：

#### 后端服务环境变量
```bash
# API 配置
PORT=8000
HOST=0.0.0.0
WORKERS=1
LOG_LEVEL=INFO

# AI 提供商配置
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 默认提供商和模型
DEFAULT_PROVIDER=openai
OPENAI_MODEL=gpt-4
DEEPSEEK_MODEL=deepseek-chat
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# 向量数据库配置
VECTOR_DB_PROVIDER=chroma
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002

# ArXiv 配置
ARXIV_MAX_RESULTS=100
ARXIV_RATE_LIMIT_DELAY=1

# 缓存配置
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# 安全配置
CORS_ORIGINS=*
API_KEY=your_api_key_optional

# 监控配置
ENABLE_METRICS=true
HEALTH_CHECK_ENABLED=true
```

#### 前端服务环境变量
```bash
# Next.js 配置
PORT=3000
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1

# API 基础 URL (指向后端服务)
API_BASE_URL=https://your-backend-service.zeabur.app
```

### 2. 服务配置

根据 Zeabur 文档，我们使用以下命名约定：

- **后端服务**: `Dockerfile.backend` → 服务名: `backend`
- **前端服务**: `Dockerfile.frontend` → 服务名: `frontend`

## 🚀 部署步骤

### 方法一：使用 Zeabur 控制台

1. **创建项目**
   - 登录 [Zeabur 控制台](https://zeabur.com)
   - 点击 "Create Project"
   - 选择 "Deploy from Git"

2. **连接 Git 仓库**
   - 选择你的 GitHub 仓库
   - 授权 Zeabur 访问

3. **配置服务**
   - **后端服务**:
     - 服务名: `backend`
     - 根目录: `/` (项目根目录)
     - Dockerfile: `backend/Dockerfile`
   
   - **前端服务**:
     - 服务名: `frontend`
     - 根目录: `/` (项目根目录)
     - Dockerfile: `frontend/Dockerfile`

4. **设置环境变量**
   - 为每个服务设置相应的环境变量
   - 确保 `API_BASE_URL` 指向正确的后端服务地址

5. **部署**
   - 点击 "Deploy"
   - 等待构建完成

### 方法二：使用 Zeabur CLI

1. **安装 Zeabur CLI**
   ```bash
   npm install -g @zeabur/cli
   ```

2. **登录**
   ```bash
   zeabur login
   ```

3. **部署**
   ```bash
   # 部署后端
   zeabur deploy --service backend --dockerfile backend/Dockerfile
   
   # 部署前端
   zeabur deploy --service frontend --dockerfile frontend/Dockerfile
   ```

## 🔧 配置说明

### Dockerfile 特性

#### 后端 Dockerfile (`backend/Dockerfile`)
- **多阶段构建**: 优化镜像大小
- **安全**: 使用非 root 用户
- **健康检查**: 自动监控服务状态
- **端口暴露**: 自动适配 Zeabur 的 PORT 环境变量

#### 前端 Dockerfile (`frontend/Dockerfile`)
- **Next.js 优化**: 使用 standalone 输出
- **静态资源**: 优化静态文件服务
- **生产配置**: 禁用遥测，优化性能

### 环境变量管理

Zeabur 会自动注入以下环境变量：
- `PORT`: 服务端口
- `HOST`: 服务主机
- `NODE_ENV`: Node.js 环境 (前端)
- `PYTHONPATH`: Python 路径 (后端)

### 健康检查

每个服务都配置了健康检查：
- **后端**: `GET /health`
- **前端**: `GET /api/health`

## 📊 监控和日志

### 查看日志
```bash
# 在 Zeabur 控制台中查看实时日志
# 或使用 CLI
zeabur logs --service backend
zeabur logs --service frontend
```

### 监控指标
- 服务状态
- 响应时间
- 错误率
- 资源使用情况

## 🔄 更新部署

### 自动更新
- 推送到 Git 仓库的 main 分支会自动触发重新部署
- Zeabur 会检测代码变更并重新构建

### 手动更新
```bash
# 重新部署特定服务
zeabur redeploy --service backend
zeabur redeploy --service frontend
```

## 🛠️ 故障排除

### 常见问题

1. **构建失败**
   - 检查 Dockerfile 语法
   - 验证依赖项是否正确安装
   - 查看构建日志

2. **服务无法启动**
   - 检查环境变量配置
   - 验证端口配置
   - 查看启动日志

3. **健康检查失败**
   - 确认健康检查端点存在
   - 检查服务是否正常响应
   - 验证网络连接

### 调试命令

```bash
# 查看服务状态
zeabur status

# 查看详细日志
zeabur logs --service backend --follow

# 进入容器调试
zeabur exec --service backend --command "bash"
```

## 📝 注意事项

1. **资源限制**: Zeabur 对每个服务有资源限制，确保应用在限制内运行
2. **环境变量**: 敏感信息应通过环境变量传递，不要硬编码
3. **端口配置**: 使用 `PORT` 环境变量，不要硬编码端口号
4. **健康检查**: 确保健康检查端点正确实现
5. **日志**: 使用标准输出进行日志记录

## 🔗 相关链接

- [Zeabur 官方文档](https://zeabur.com/docs)
- [Dockerfile 部署指南](https://zeabur.com/docs/en-US/deploy/dockerfile)
- [环境变量配置](https://zeabur.com/docs/en-US/deploy/environment-variables)
- [CLI 工具](https://zeabur.com/docs/en-US/cli)

## 📞 支持

如果遇到部署问题，可以：
1. 查看 Zeabur 控制台的详细日志
2. 检查 [Zeabur 社区](https://community.zeabur.com)
3. 联系 Zeabur 支持团队 