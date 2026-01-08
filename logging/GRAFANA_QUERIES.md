# Grafana LogQL 查询示例

本文档提供在 Grafana 中查询和分析日志的 LogQL 查询示例。

## 请求时间统计

### 1. 每个问题的请求时间列表

显示所有聊天请求的问题和响应时间：

```logql
{service="backend"} |= "JSON:" 
| json 
| endpoint_type = "chat" 
| question != "" 
| line_format "问题: {{.question}} | 响应时间: {{.duration_ms}}ms | 状态: {{.status_code}}"
```

### 2. 平均响应时间（按时间范围）

计算最近 1 小时的平均响应时间：

```logql
avg_over_time(
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [1h]
)
```

### 3. P50/P95/P99 响应时间

**P50 (中位数):**
```logql
quantile_over_time(0.50, 
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [1h]
)
```

**P95:**
```logql
quantile_over_time(0.95, 
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [1h]
)
```

**P99:**
```logql
quantile_over_time(0.99, 
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [1h]
)
```

### 4. 响应时间分布（直方图）

按响应时间范围分组统计：

```logql
sum by (le) (
  rate(
    {service="backend"} |= "JSON:" 
    | json 
    | endpoint_type = "chat" 
    | duration_ms > 0 
    | duration_ms < 10000 [5m]
  )
)
```

### 5. 最慢的 10 个请求

```logql
topk(10,
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | question != "" 
  | sort_desc duration_ms
)
```

### 6. 按问题长度统计响应时间

```logql
avg_over_time(
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [1h]
) by (question_length)
```

## 创建 Grafana Dashboard

### Panel 1: 平均响应时间（时间序列）

**Query:**
```logql
avg_over_time(
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [5m]
)
```

**Visualization:** Time series
**Unit:** milliseconds (ms)
**Legend:** `Average Response Time`

### Panel 2: P95 响应时间（时间序列）

**Query:**
```logql
quantile_over_time(0.95, 
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | unwrap duration_ms [5m]
)
```

**Visualization:** Time series
**Unit:** milliseconds (ms)
**Legend:** `P95 Response Time`

### Panel 3: 请求总数（统计）

**Query:**
```logql
sum(count_over_time(
  {service="backend"} |= "endpoint_type=chat" [1h]
))
```

**Visualization:** Stat
**Unit:** requests

### Panel 4: 响应时间分布（直方图）

**Query:**
```logql
sum by (le) (
  rate(
    {service="backend"} |= "JSON:" 
    | json 
    | endpoint_type = "chat" 
    | duration_ms > 0 [5m]
  )
)
```

**Visualization:** Histogram
**Unit:** milliseconds (ms)

### Panel 5: 最慢的请求（表格）

**Query:**
```logql
topk(10,
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" 
  | question != "" 
  | sort_desc duration_ms
)
```

**Visualization:** Table
**Columns:**
- `question` - 问题
- `duration_ms` - 响应时间 (ms)
- `status` - HTTP 状态码
- `timestamp` - 时间戳

### Panel 6: 按状态码统计请求数

**Query:**
```logql
sum by (status_code) (
  count_over_time(
    {service="backend"} |= "JSON:" 
    | json [1h]
  )
)
```

**Visualization:** Pie chart
**Legend:** Status code

## RAG Pipeline Tracing

The RAG pipeline now includes structured tracing with trace_id for end-to-end observability.

### 1. Trace a Single Request

Find all logs for a specific trace:

```logql
{service="backend"} |= "RAG:abc12345"
```

### 2. View Complete Request Flow

```logql
{service="backend"} |= "RAG:" |= "JSON:" 
| json 
| line_format "{{.trace_id}} | {{.stage}} | {{.elapsed_ms}}ms"
```

### 3. P95 Total Latency

```logql
quantile_over_time(0.95,
  {service="backend"} |= "COMPLETE" |= "JSON:" 
  | json 
  | stage = "COMPLETE"
  | unwrap total_latency_ms [1h]
)
```

### 4. Average Latency by Stage

```logql
avg by (stage) (
  {service="backend"} |= "RAG:" |= "JSON:" 
  | json 
  | stage != "ENTRY" 
  | stage != "COMPLETE"
  | unwrap latency_ms [1h]
)
```

### 5. Intent Classification Distribution

```logql
sum by (intent_type) (
  count_over_time(
    {service="backend"} |= "INTENT" |= "JSON:" 
    | json [24h]
  )
)
```

### 6. Retrieval Quality - Similarity Distribution

```logql
{service="backend"} |= "RETRIEVE" |= "JSON:" 
| json 
| line_format "{{.trace_id}}: {{.docs_count}} docs, similarity={{.top_similarity}}"
```

### 7. Average Documents Retrieved

```logql
avg_over_time(
  {service="backend"} |= "RETRIEVE" |= "JSON:" 
  | json 
  | unwrap docs_count [1h]
)
```

### 8. Slow Requests (>5s)

```logql
{service="backend"} |= "COMPLETE" |= "JSON:" 
| json 
| total_latency_ms > 5000
| line_format "{{.trace_id}}: {{.query}} - {{.total_latency_ms}}ms"
```

### 9. Error Tracking

```logql
{service="backend"} |= "RAG:" |= "ERROR" 
| json 
| line_format "{{.trace_id}}: {{.error_type}} - {{.error_message}}"
```

### 10. Stage Latency Breakdown (Time Series)

Create separate panels for each stage:

**Transform Stage:**
```logql
avg_over_time(
  {service="backend"} |= "TRANSFORM" |= "JSON:" 
  | json 
  | unwrap latency_ms [5m]
)
```

**Retrieve Stage:**
```logql
avg_over_time(
  {service="backend"} |= "RETRIEVE" |= "JSON:" 
  | json 
  | unwrap latency_ms [5m]
)
```

**Generate Stage:**
```logql
avg_over_time(
  {service="backend"} |= "GENERATE" |= "JSON:" 
  | json 
  | unwrap latency_ms [5m]
)
```

### 11. Hybrid vs Vector Search Comparison

```logql
avg by (search_type) (
  {service="backend"} |= "RETRIEVE" |= "JSON:" 
  | json 
  | unwrap latency_ms [1h]
)
```

### 12. Request Volume with Intent Type

```logql
sum by (intent) (
  count_over_time(
    {service="backend"} |= "COMPLETE" |= "JSON:" 
    | json [1h]
  )
)
```

## Advanced Query Examples

### Find Requests with Low Similarity Scores

```logql
{service="backend"} |= "RETRIEVE" |= "JSON:" 
| json 
| top_similarity < 0.5
| line_format "Low similarity: {{.trace_id}} - {{.top_similarity}}"
```

### Requests Where Documents Were Filtered

```logql
{service="backend"} |= "GRADE" |= "JSON:" 
| json 
| filtered_count > 0
| line_format "{{.trace_id}}: filtered {{.filtered_count}} docs"
```

### Complete Pipeline Analysis

View the complete flow of a request type:

```logql
{service="backend"} |= "RAG:" |= "JSON:"
| json
| sort by timestamp
| line_format "[{{.elapsed_ms}}ms] {{.stage}}: {{if .docs_count}}docs={{.docs_count}}{{end}}{{if .intent_type}}intent={{.intent_type}}{{end}}{{if .latency_ms}}latency={{.latency_ms}}ms{{end}}"
```

## 高级查询

### 查找响应时间超过阈值的请求

```logql
{service="backend"} |= "JSON:" 
| json 
| endpoint_type = "chat" 
| duration_ms > 5000
| line_format "慢请求: {{.question}} - {{.duration_ms}}ms"
```

### 按环境过滤

```logql
{service="backend", environment="production"} 
|= "JSON:" 
| json 
| endpoint_type = "chat" 
| unwrap duration_ms
```

### 计算每分钟的请求速率

```logql
sum(rate(
  {service="backend"} |= "JSON:" 
  | json 
  | endpoint_type = "chat" [1m]
))
```

## 使用技巧

1. **时间范围选择**: 在 Grafana 右上角选择时间范围（如 Last 1 hour, Last 24 hours）

2. **刷新间隔**: 设置自动刷新（如 30s, 1m）以实时查看数据

3. **变量使用**: 创建 Dashboard 变量来动态过滤：
   - `$environment`: 环境选择（development, production）
   - `$service`: 服务选择（backend, frontend）

4. **告警设置**: 基于响应时间设置告警：
   - P95 > 5000ms 时告警
   - 错误率 > 5% 时告警

## 示例 Dashboard JSON

完整的 Dashboard JSON 配置请参考 `grafana-dashboard.json`（如果存在）。

