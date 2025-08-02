# Elasticsearch 集成设置

本文档说明如何设置和配置Elasticsearch来存储job日志。

## 🚀 快速开始

### 方法一：使用Middleware Docker Compose（推荐）

使用统一的middleware docker-compose启动所有中间件服务，包括Elasticsearch：

```bash
cd infra/docker
docker-compose -f docker-compose.middleware.yml up -d
```

这将启动：
- PostgreSQL: http://localhost:5432
- Redis: http://localhost:6379
- Weaviate: http://localhost:8080
- **Elasticsearch: http://localhost:9200**
- **Kibana: http://localhost:5601**

### 方法二：单独启动Elasticsearch

如果只需要Elasticsearch服务：

```bash
cd infra/docker
docker-compose -f docker-compose.elasticsearch.yml up -d
```

### 2. 配置环境变量

在 `backend/.env` 文件中添加以下配置：

```env
# Elasticsearch Configuration
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_INDEX_PREFIX=job-logs
```

### 3. 安装依赖

```bash
cd backend
pip install elasticsearch>=8.0.0
```

### 4. 运行数据库迁移

```bash
cd backend
python run_migration.py
```

## 📊 功能特性

### 日志存储
- 结构化日志存储到Elasticsearch
- 按job分区的索引
- 支持日志级别、步骤、错误代码等字段
- 自动索引模板管理

### 搜索和分析
- 全文搜索日志内容
- 按时间范围、级别、步骤过滤
- 实时日志流
- 聚合统计

### 性能监控
- 执行步骤时间统计
- 错误分析和统计
- 性能指标收集

## 🔧 API接口

### 日志搜索
```bash
# 搜索日志
GET /api/elasticsearch/search/logs?job_run_id=xxx&level=ERROR

# 搜索状态历史
GET /api/elasticsearch/search/status-history?job_id=xxx
```

### 分析接口
```bash
# 日志统计
GET /api/elasticsearch/analytics/log-statistics

# 错误分析
GET /api/elasticsearch/analytics/error-analysis?days=7

# 性能指标
GET /api/elasticsearch/analytics/performance-metrics?days=30
```

### 管理接口
```bash
# 健康检查
GET /api/elasticsearch/health

# 列出索引
GET /api/elasticsearch/indices

# 删除索引
DELETE /api/elasticsearch/indices/job-logs-*
```

## 🎯 使用示例

### 在代码中使用Elasticsearch日志

```python
from utils.job_logger import JobLoggerFactory

# 创建带Elasticsearch的logger
job_logger = JobLoggerFactory.create_logger(
    job_run_id="job-run-id",
    es_hosts=["http://localhost:9200"]
)

# 记录日志（自动存储到数据库和Elasticsearch）
job_logger.info("Starting job execution")
job_logger.error("An error occurred", error_code="EXECUTION_ERROR")

# 记录指标
job_logger.record_metric("papers_found", 10)
job_logger.record_metric("papers_processed", 8)

# 更新状态
job_logger.update_status("running", reason="Job started")
```

### 前端使用Elasticsearch日志

```tsx
import { ElasticsearchLogViewer } from '@/components/job-logs/elasticsearch-log-viewer'

// 在组件中使用
<ElasticsearchLogViewer 
  jobRunId="job-run-id"
  autoRefresh={true}
  refreshInterval={5000}
/>
```

## 📈 Kibana可视化

### 1. 访问Kibana
打开 http://localhost:5601

### 2. 创建索引模式
1. 进入 Stack Management > Index Patterns
2. 创建索引模式：`job-logs-*`
3. 选择时间字段：`timestamp`

### 3. 创建可视化
- **日志级别分布**：饼图显示不同级别的日志数量
- **执行时间趋势**：线图显示各步骤的执行时间
- **错误分析**：柱状图显示错误代码分布
- **实时日志流**：实时显示最新的日志

### 4. 创建仪表板
组合多个可视化创建监控仪表板。

## 🔍 索引结构

### 日志索引 (job-logs-*)
```json
{
  "job_run_id": "uuid",
  "job_id": "uuid", 
  "job_name": "string",
  "timestamp": "datetime",
  "level": "DEBUG|INFO|WARNING|ERROR|CRITICAL",
  "message": "text",
  "step": "string",
  "paper_id": "string",
  "error_code": "string",
  "duration_ms": "long",
  "details": "object"
}
```

### 状态历史索引 (job-logs-status-history-*)
```json
{
  "job_run_id": "uuid",
  "job_id": "uuid",
  "from_status": "string",
  "to_status": "string", 
  "timestamp": "datetime",
  "reason": "text",
  "details": "object"
}
```

### 指标索引 (job-logs-metrics-*)
```json
{
  "job_run_id": "uuid",
  "job_id": "uuid",
  "timestamp": "datetime",
  "metric_name": "string",
  "metric_value": "long",
  "metric_type": "counter|gauge|histogram",
  "labels": "object"
}
```

## 🛠️ 配置选项

### 环境变量
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| ELASTICSEARCH_ENABLED | true | 是否启用Elasticsearch |
| ELASTICSEARCH_HOSTS | http://localhost:9200 | Elasticsearch主机列表 |
| ELASTICSEARCH_USERNAME | | 用户名（可选） |
| ELASTICSEARCH_PASSWORD | | 密码（可选） |
| ELASTICSEARCH_INDEX_PREFIX | job-logs | 索引前缀 |

### Docker环境变量
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| ELASTICSEARCH_PORT | 9200 | Elasticsearch端口 |
| ELASTICSEARCH_TRANSPORT_PORT | 9300 | 传输端口 |
| KIBANA_PORT | 5601 | Kibana端口 |

### 高级配置
```python
# 自定义Elasticsearch配置
es_logger = ElasticsearchLoggerFactory.create_logger(
    hosts=["http://elasticsearch:9200"],
    username="elastic",
    password="password",
    index_prefix="custom-prefix"
)
```

## 🐳 Docker Compose服务

### Middleware服务
```yaml
# 启动所有中间件服务
docker-compose -f docker-compose.middleware.yml up -d

# 服务列表：
# - postgres: 数据库
# - redis: 缓存
# - weaviate: 向量数据库
# - elasticsearch: 日志存储
# - kibana: 日志可视化
# - prometheus: 监控（可选）
# - pgadmin: 数据库管理（可选）
# - redis-commander: Redis管理（可选）
```

### 单独Elasticsearch服务
```yaml
# 只启动Elasticsearch和Kibana
docker-compose -f docker-compose.elasticsearch.yml up -d
```

## 🔧 故障排除

### 连接问题
1. 检查Elasticsearch是否运行：`curl http://localhost:9200`
2. 检查网络连接和防火墙设置
3. 验证环境变量配置

### 索引问题
1. 检查索引模板是否正确创建
2. 验证索引权限设置
3. 查看Elasticsearch日志

### 性能问题
1. 调整Elasticsearch内存设置
2. 优化索引分片和副本设置
3. 定期清理旧索引

### Docker相关问题
1. 检查容器状态：`docker ps`
2. 查看容器日志：`docker logs research-agent-elasticsearch`
3. 检查网络连接：`docker network ls`

## 📚 相关文档

- [Elasticsearch官方文档](https://www.elastic.co/guide/index.html)
- [Python Elasticsearch客户端](https://elasticsearch-py.readthedocs.io/)
- [Kibana用户指南](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Docker Compose文档](https://docs.docker.com/compose/) 