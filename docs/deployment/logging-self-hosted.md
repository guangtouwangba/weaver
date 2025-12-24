# Self-Hosted Logging with Loki + Grafana

本文档介绍如何在 Zeabur 上部署自托管的 Loki + Grafana 日志系统，并将前后端应用集成到日志系统中。

## 目录

- [架构概览](#架构概览)
- [本地开发测试](#本地开发测试)
- [Zeabur 部署](#zeabur-部署)
- [配置应用](#配置应用)
- [使用 Grafana 查询日志](#使用-grafana-查询日志)
- [常见问题](#常见问题)

## 架构概览

```
┌──────────────┐     HTTP Push      ┌──────────┐
│   Backend    │ ─────────────────> │   Loki   │
│  (FastAPI)   │                    │  :3100   │
└──────────────┘                    └──────────┘
                                          │
┌──────────────┐     HTTP Push            │ Query
│   Frontend   │ ─────────────────────────┘
│  (Next.js)   │                          │
└──────────────┘                          ▼
                                    ┌──────────┐
                                    │ Grafana  │
                                    │  :3000   │
                                    └──────────┘
```

- **Loki**: 日志聚合和存储（类似 Prometheus 但专为日志设计）
- **Grafana**: 日志查询和可视化界面
- **应用直接推送**: 后端和前端通过 HTTP API 直接将日志推送到 Loki

## 本地开发测试

### 1. 启动日志服务

```bash
cd logging
./test-logging.sh
```

或手动启动：

```bash
cd logging
docker-compose -f docker-compose-logging.yml up -d
```

### 2. 访问 Grafana

- URL: http://localhost:3001
- 用户名: `admin`
- 密码: `admin123`

### 3. 配置本地应用

**后端 (.env)**:
```bash
LOKI_URL=http://localhost:3100/loki/api/v1/push
LOKI_ENABLED=true
LOG_LEVEL=INFO
```

**前端 (.env.local)**:
```bash
LOKI_URL=http://localhost:3100
LOKI_ENABLED=true
```

### 4. 测试日志发送

启动后端和前端应用后，访问任何页面或 API，日志会自动发送到 Loki。

在 Grafana 中查看：
1. 进入 "Explore" 页面
2. 选择 "Loki" 数据源
3. 使用查询：`{service="backend"}` 或 `{service="frontend"}`

## Zeabur 部署

### 方案 1：使用 Zeabur Marketplace（推荐）

检查 Zeabur Marketplace 是否有预置的 Loki 或 Grafana 模板。

### 方案 2：自定义 Docker 部署

#### Step 1: 创建 Loki 服务

1. 在 Zeabur 项目中点击 "Create Service"
2. 选择 "Docker Image"
3. 镜像: `grafana/loki:latest`
4. 端口: `3100`
5. 环境变量: 无需配置
6. Volume: 挂载 `/loki` 用于数据持久化

**配置文件**: 需要将 `logging/loki-config.yaml` 内容通过环境变量或挂载卷传入。

#### Step 2: 创建 Grafana 服务

1. 在同一项目中创建新服务
2. 镜像: `grafana/grafana:latest`
3. 端口: `3000`
4. 环境变量:
   - `GF_SECURITY_ADMIN_PASSWORD`: 设置管理员密码
   - `GF_USERS_ALLOW_SIGN_UP`: `false`
5. Volume: 挂载 `/var/lib/grafana` 用于持久化配置

#### Step 3: 配置网络连通性

确保 Loki 和 Grafana 在同一个 Zeabur 项目下，它们可以通过内部域名互相访问：
- `http://loki.zeabur.internal:3100`
- `http://grafana.zeabur.internal:3000`

#### Step 4: 在 Grafana 中添加 Loki 数据源

1. 登录 Grafana
2. Configuration → Data Sources → Add data source
3. 选择 "Loki"
4. URL: `http://loki.zeabur.internal:3100`
5. 点击 "Save & Test"

## 配置应用

### 后端配置

**Zeabur 环境变量 (Backend Service)**:
```
LOKI_URL=http://loki.zeabur.internal:3100/loki/api/v1/push
LOKI_ENABLED=true
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 前端配置

**Zeabur 环境变量 (Frontend Service)**:
```
LOKI_URL=http://loki.zeabur.internal:3100
LOKI_ENABLED=true
NODE_ENV=production
```

## 使用 Grafana 查询日志

### 基础查询

在 Grafana Explore 页面使用 LogQL 查询语言：

```logql
# 查看所有后端日志
{service="backend"}

# 查看所有前端日志
{service="frontend"}

# 查看错误日志
{service="backend", level="ERROR"}

# 搜索包含特定关键词的日志
{service="backend"} |= "database"

# 搜索特定时间范围
{service="backend"}[5m]
```

### 常用查询示例

```logql
# 所有错误和警告
{level=~"ERROR|WARNING"}

# 特定环境的日志
{environment="production"}

# API 请求日志
{service="backend"} |= "Request:"

# 慢查询（需要在代码中添加标签）
{service="backend", query_type="slow"}

# 按服务分组统计
sum(count_over_time({service="backend"}[1m])) by (level)
```

### 创建仪表板

1. Grafana → Dashboards → New Dashboard
2. Add Panel
3. 选择 Loki 数据源
4. 输入查询语句
5. 自定义可视化类型（Logs、Graph、Table）

## 日志管理

### 日志保留策略

默认保留 **7 天**（168小时）。

修改保留期：编辑 `logging/loki-config.yaml` 中的 `retention_period`。

### 清理旧日志

Loki 会自动清理超过保留期的日志，无需手动操作。

### 磁盘空间管理

监控 Loki 数据卷使用情况：
- 初始分配: 5GB
- 根据日志量增长情况调整

## 性能调优

### 后端日志优化

- 避免在高频循环中打印日志
- 使用合适的日志级别（INFO/WARNING/ERROR）
- 对敏感信息脱敏

### Loki 资源配置

默认配置适用于小到中等规模应用（<100GB/月）。

如果日志量大，可以：
1. 增加 Loki 内存限制
2. 使用对象存储（S3）替代本地文件存储
3. 部署多个 Loki 实例（分布式模式）

## 安全建议

1. **Grafana 访问控制**:
   - 设置强密码
   - 禁用注册功能
   - 使用 Zeabur 的域名保护功能

2. **Loki API 保护**:
   - 仅在内部网络暴露（使用 `.zeabur.internal` 域名）
   - 或配置 Basic Auth

3. **日志内容**:
   - 不要记录密码、API Key 等敏感信息
   - 对用户数据脱敏

## 常见问题

### Q: 日志没有出现在 Grafana？

**检查清单**:
1. Loki 服务是否正常运行？
2. 应用的 `LOKI_ENABLED` 是否设置为 `true`？
3. `LOKI_URL` 是否正确？
4. 网络是否互通（在应用容器内 `ping loki.zeabur.internal`）？
5. 查看应用日志是否有 Loki 连接错误？

### Q: 如何查看 Loki 本身的日志？

Zeabur 控制台 → Loki 服务 → Logs

### Q: Grafana 忘记密码怎么办？

重置 Grafana 数据卷或通过环境变量修改密码：
```
GF_SECURITY_ADMIN_PASSWORD=new-password
```

### Q: 能否在多个 Zeabur 项目间共享 Loki？

可以，但需要将 Loki 的端口暴露到公网，并配置 Basic Auth 保护。

### Q: 日志查询很慢？

1. 缩小时间范围
2. 使用标签过滤而不是全文搜索
3. 增加 Loki 内存配置

## 成本估算

**Zeabur 资源消耗**:
- Loki: ~200-500MB 内存，取决于日志量
- Grafana: ~100-200MB 内存
- 磁盘: 5-20GB（取决于日志量和保留期）

**预估月费用**（Zeabur 计费）:
- 小型应用（<10GB 日志/月）: ~$5-10
- 中型应用（10-100GB 日志/月）: ~$10-30

## 参考资源

- [Loki 官方文档](https://grafana.com/docs/loki/latest/)
- [Grafana 官方文档](https://grafana.com/docs/grafana/latest/)
- [LogQL 查询语言](https://grafana.com/docs/loki/latest/logql/)
- [Zeabur 文档](https://zeabur.com/docs)

## 下一步

- 配置日志告警（Grafana Alerting）
- 集成 Prometheus 指标监控
- 部署分布式 Loki 集群（适用于大规模应用）
























