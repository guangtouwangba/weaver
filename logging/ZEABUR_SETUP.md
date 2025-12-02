# Zeabur 部署配置指南

## 方式 1：通过 Zeabur 控制台部署（推荐）

### 步骤 1：部署 Loki 服务

1. 进入 Zeabur 项目：`rag-dev` (项目ID: 692e7f76d217691fb5295532)
2. 点击 "Add Service" 或 "创建服务"
3. 选择 "Git" → 绑定你的 GitHub 仓库
4. 配置如下：

```
Service Name: loki
Branch: master
Root Directory: logging
Dockerfile: Dockerfile.loki
Port: 3100
```

5. 环境变量（可选）：
   - 无需配置，使用默认配置即可

6. 存储卷（Volume）：
   - 路径: `/loki`
   - 大小: 5GB（根据需要调整）

7. 点击 "Deploy"

### 步骤 2：部署 Grafana 服务

1. 在同一项目中点击 "Add Service"
2. 选择 "Git" → 选择同一仓库
3. 配置如下：

```
Service Name: grafana
Branch: master
Root Directory: logging
Dockerfile: Dockerfile.grafana
Port: 3000
```

4. 环境变量（必需）：
```
GF_SECURITY_ADMIN_PASSWORD=your-secure-password-here
GF_USERS_ALLOW_SIGN_UP=false
```

5. 存储卷（Volume）：
   - 路径: `/var/lib/grafana`
   - 大小: 1GB

6. 点击 "Deploy"

### 步骤 3：配置网络

Zeabur 会自动为每个服务分配内部域名：
- Loki: `loki.zeabur.internal:3100`
- Grafana: `grafana.zeabur.internal:3000`

这些域名只在同一项目的服务间可访问。

### 步骤 4：验证 Grafana 数据源

1. 访问 Grafana 的公网域名（Zeabur 自动分配）
2. 使用设置的密码登录
3. 进入 Configuration → Data Sources
4. 应该能看到 "Loki" 数据源已自动配置
5. 点击 "Test" 验证连接

## 方式 2：通过 Zeabur CLI 部署

### 安装 CLI
```bash
npm install -g zeabur
zeabur auth login
```

### 部署 Loki
```bash
cd logging
zeabur deploy --project-id 692e7f76d217691fb5295532 --service-name loki
```

### 部署 Grafana
```bash
zeabur deploy --project-id 692e7f76d217691fb5295532 --service-name grafana
```

## 配置应用连接到日志系统

### Backend 环境变量（在 Zeabur 控制台配置）

进入你的 backend 服务 → Settings → Environment Variables：

```bash
LOKI_URL=http://loki.zeabur.internal:3100/loki/api/v1/push
LOKI_ENABLED=true
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Frontend 环境变量

进入你的 frontend 服务 → Settings → Environment Variables：

```bash
LOKI_URL=http://loki.zeabur.internal:3100
LOKI_ENABLED=true
NODE_ENV=production
```

## 访问 Grafana

1. 在 Zeabur 控制台找到 Grafana 服务
2. 点击 "Networking" → "Generate Domain"
3. 系统会生成一个公网域名，如 `grafana-abc123.zeabur.app`
4. 访问该域名并登录

## 查看日志

### 在 Grafana Explore 中查询

1. 点击左侧菜单 "Explore"（罗盘图标）
2. 选择 "Loki" 数据源
3. 输入查询语句：

```logql
# 查看所有后端日志
{service="backend"}

# 查看所有前端日志
{service="frontend"}

# 查看错误日志
{service="backend", level="ERROR"}

# 搜索特定内容
{service="backend"} |= "Request:"
```

## 常见问题

### Q: Grafana 无法连接到 Loki？

**检查清单**：
1. 确认两个服务在同一个 Zeabur 项目下
2. 检查 Loki 服务是否正常运行
3. 在 Grafana 数据源设置中，URL 应该是 `http://loki.zeabur.internal:3100`

### Q: 应用无法发送日志到 Loki？

**检查清单**：
1. 确认环境变量 `LOKI_ENABLED=true`
2. 确认 `LOKI_URL` 格式正确
3. 查看应用日志是否有 Loki 连接错误
4. 尝试在应用容器内 ping loki.zeabur.internal

### Q: 如何修改 Grafana 管理员密码？

在 Grafana 服务的环境变量中修改：
```
GF_SECURITY_ADMIN_PASSWORD=new-password
```
然后重启服务。

## 资源监控

在 Zeabur 控制台可以查看：
- CPU 使用率
- 内存使用率
- 网络流量
- 磁盘使用情况

建议监控指标：
- Loki 内存 < 500MB
- Grafana 内存 < 200MB
- 磁盘使用 < 80%

## 成本优化

1. **调整日志保留期**：默认 7 天，可在 `loki-config.yaml` 修改
2. **限制日志级别**：生产环境使用 INFO 或 WARNING
3. **按需扩容**：根据日志量调整磁盘大小

## 下一步

- [ ] 部署 Loki 服务
- [ ] 部署 Grafana 服务
- [ ] 配置 Backend 环境变量
- [ ] 配置 Frontend 环境变量
- [ ] 访问 Grafana 验证日志流
- [ ] 创建自定义仪表板

