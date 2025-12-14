# Zeabur 部署指南

## 环境架构

| 环境 | 项目名 | 用途 |
|------|--------|------|
| Development | `research-rag-dev` | 开发测试 |
| Production | `research-rag-prod` | 正式上线 |

## 服务列表

每个环境包含以下服务：

| 服务 | Root Directory | 端口 | 说明 |
|------|----------------|------|------|
| `api` | `app/backend` | 8000 | FastAPI 后端 |
| `frontend` | `app/frontend` | 3000 | Next.js 前端 (开发版) |
| `web` | `web` | 3000 | Next.js 原型 (仅 prod) |

## 部署步骤

### 1. 安装 Zeabur CLI

```bash
# 使用 npx 直接运行（推荐）
npx zeabur@latest --help

# 或全局安装
npm install -g zeabur
```

### 2. 登录

```bash
npx zeabur@latest auth login
```

### 3. 部署开发环境 (Dev)

```bash
# 部署 API
cd app/backend
npx zeabur@latest deploy
# 选择 "Create a new project"
# 项目名: research-rag-dev
# 服务名: api

# 部署前端
cd ../frontend
npx zeabur@latest deploy
# 选择项目: research-rag-dev
# 服务名: frontend
```

### 4. 部署生产环境 (Prod)

```bash
# 部署 API
cd app/backend
npx zeabur@latest deploy
# 选择 "Create a new project"
# 项目名: research-rag-prod
# 服务名: api

# 部署前端
cd ../frontend
npx zeabur@latest deploy
# 选择项目: research-rag-prod
# 服务名: frontend

# 部署原型展示 (可选)
cd ../../web
npx zeabur@latest deploy
# 选择项目: research-rag-prod
# 服务名: web
```

## 环境变量配置

在 Zeabur 控制台为每个服务配置环境变量。

### API 服务 (`api`)

| 变量名 | Dev 值 | Prod 值 |
|--------|--------|---------|
| `DATABASE_URL` | Supabase Dev 连接串 | Supabase Prod 连接串 |
| `OPENROUTER_API_KEY` | `sk-or-v1-xxx` | `sk-or-v1-xxx` |
| `ENVIRONMENT` | `development` | `production` |
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `CORS_ORIGINS` | `*` | `https://your-domain.com` |
| `UPLOAD_DIR` | `/data/uploads` | `/data/uploads` |

### Frontend 服务 (`frontend`)

| 变量名 | Dev 值 | Prod 值 |
|--------|--------|---------|
| `NEXT_PUBLIC_API_URL` | `https://api-dev.zeabur.app` | `https://api.your-domain.com` |
| `NODE_ENV` | `development` | `production` |

### Web 服务 (`web`) - 仅 Prod

| 变量名 | Prod 值 |
|--------|---------|
| `NODE_ENV` | `production` |

## Volume 配置

为 API 服务创建持久化存储：

1. 在 Zeabur 控制台选择 API 服务
2. 点击 "Storage" / "存储"
3. 创建 Volume，挂载路径: `/data/uploads`

## 域名配置

### 开发环境
- API: `research-rag-api-dev.zeabur.app`
- Frontend: `research-rag-dev.zeabur.app`

### 生产环境（自定义域名）
- API: `api.your-domain.com`
- Frontend: `app.your-domain.com`
- Web: `www.your-domain.com`

## 数据库配置

建议使用两个独立的 Supabase 项目：

1. **Dev 数据库**: 用于开发测试，可随时重置
2. **Prod 数据库**: 生产数据，需要备份策略

### Supabase 连接串格式

```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

## GitHub 自动部署

Zeabur 支持 GitHub 集成，推送代码后自动部署：

1. 在 Zeabur 控制台绑定 GitHub 仓库
2. 设置分支触发规则：
   - `develop` 分支 → Dev 环境
   - `main`/`master` 分支 → Prod 环境

## 监控和日志

- 在 Zeabur 控制台查看实时日志
- 使用 `/health` 端点进行健康检查
- 配置告警通知（如有需要）

## 成本估算

Zeabur 按量计费：
- 免费额度: $5/月
- 开发者计划: $5/月起

建议：
- Dev 环境使用免费额度
- Prod 环境根据流量选择合适的计划

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查 `DATABASE_URL` 格式
   - 确认 Supabase 项目状态
   - 检查 SSL 配置

2. **CORS 错误**
   - 检查 `CORS_ORIGINS` 配置
   - 确认前端域名已添加

3. **文件上传失败**
   - 检查 Volume 是否正确挂载
   - 确认 `UPLOAD_DIR` 路径

### 查看日志

```bash
npx zeabur@latest service list
npx zeabur@latest deployment list
```

