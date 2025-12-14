# Self-Hosted Logging Infrastructure

This directory contains configuration files for the self-hosted Loki + Grafana logging stack.

## Components

- **Loki**: Log aggregation and storage system
- **Grafana**: Visualization and query interface

## Files

- `loki-config.yaml`: Loki server configuration
- `grafana-datasource.yaml`: Grafana data source configuration (auto-provisioning Loki)
- `docker-compose-logging.yml`: Local testing setup

## Deployment on Zeabur

### Option 1: Separate Logging Service

Create a new Zeabur service with a custom Dockerfile that includes both Loki and Grafana.

### Option 2: Manual Service Creation

1. Create Loki service from `grafana/loki:latest`
2. Create Grafana service from `grafana/grafana:latest`
3. Configure network connectivity between services

## Environment Variables

### Loki Service
- No special env vars required (uses mounted config)

### Grafana Service
- `GF_SECURITY_ADMIN_PASSWORD`: Admin dashboard password
- `GF_INSTALL_PLUGINS`: (optional) Additional plugins

## Volume Mounts

### Loki
- `/loki`: Data storage (chunks, indexes, compactor)

### Grafana
- `/var/lib/grafana`: Dashboard and settings storage
- `/etc/grafana/provisioning/datasources`: Auto-provision Loki datasource

## Accessing Logs

1. Open Grafana at `http://grafana-service-url:3000`
2. Login with username `admin` and configured password
3. Navigate to "Explore" → Select "Loki" data source
4. Use LogQL queries to search logs

Example queries:
```logql
# Basic queries
{service="backend"}
{service="frontend", level="error"}
{service="backend"} |= "database"

# Query request time statistics for chat endpoints
{service="backend"} |= "JSON:" | json | endpoint_type = "chat" | duration_ms > 0

# Average response time for chat requests (last 1 hour)
avg_over_time(
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [1h]
)

# P95 response time for chat requests
quantile_over_time(0.95, 
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [1h]
)

# List all questions with their response times
{service="backend"} |= "JSON:" 
| json 
| endpoint_type = "chat" 
| question != "" 
| line_format "{{.question}} - {{.duration_ms}}ms"

# Count requests by status code
sum by (status_code) (
  count_over_time(
    {service="backend"} |= "JSON:" 
    | json [1h]
  )
)
```

## 请求时间统计

详细的 Grafana 查询示例请参考 [GRAFANA_QUERIES.md](./GRAFANA_QUERIES.md)，包括：
- 每个问题的请求时间列表
- 平均/P50/P95/P99 响应时间
- 响应时间分布直方图
- 最慢的请求列表
- 完整的 Dashboard 配置示例

## Log Retention

Default retention: **7 days** (168 hours)

To adjust, modify `retention_period` in `loki-config.yaml`.

