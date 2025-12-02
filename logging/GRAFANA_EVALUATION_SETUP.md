# Grafana 评估指标配置指南

## 前置条件

1. ✅ Loki 和 Grafana 已在 Zeabur 部署
2. ✅ 后端已配置并启用评估功能
3. ✅ 评估日志正在发送到 Loki

## 第一步：验证评估日志是否到达 Loki

### 1.1 访问 Grafana Explore

1. 打开 Grafana: `https://your-grafana-domain.zeabur.app`
2. 登录（默认用户名/密码：`admin/admin`）
3. 点击左侧菜单 **Explore** (罗盘图标)

### 1.2 查询评估日志

在 LogQL 查询框中输入：

```logql
{service="rag-evaluation"}
```

点击 **Run query** 按钮。

**期望结果：**
- 如果看到日志输出，说明评估数据正在正常发送 ✅
- 如果没有数据，检查下面的故障排查部分 ❌

### 1.3 查看日志结构

日志应该包含以下 JSON 字段：

```json
{
  "service": "rag-evaluation",
  "evaluation_type": "realtime",
  "project_id": "uuid",
  "question_preview": "What is...",
  "chunking_strategy": "recursive_1000",
  "retrieval_mode": "hybrid",
  "metrics": {
    "faithfulness": 0.95,
    "answer_relevancy": 0.88,
    "context_precision": 0.92
  },
  "timestamp": "2024-12-02T10:00:00Z"
}
```

## 第二步：导入评估仪表板

### 方法 1：使用预配置的仪表板 JSON（推荐）

1. 在 Grafana 左侧菜单点击 **Dashboards** (四个方块图标)
2. 点击右上角 **New** → **Import**
3. 点击 **Upload JSON file**
4. 选择项目中的文件：`logging/grafana-dashboards/rag-evaluation-dashboard.json`
5. 选择 Loki 数据源
6. 点击 **Import**

**注意：** 如果导入失败，尝试方法 2 手动创建。

### 方法 2：手动创建仪表板

如果 JSON 导入不兼容，可以手动创建以下面板。

## 第三步：创建关键指标面板

### 面板 1：平均 Faithfulness（24小时）

**面板类型：** Stat

**查询（LogQL）：**
```logql
avg_over_time(
  {service="rag-evaluation"} 
  | json 
  | unwrap metrics_faithfulness 
  [24h]
)
```

**配置：**
- **Min:** 0
- **Max:** 1
- **Thresholds:**
  - Red: 0 - 0.8
  - Yellow: 0.8 - 0.9
  - Green: 0.9 - 1.0

### 面板 2：平均 Answer Relevancy（24小时）

**面板类型：** Stat

**查询：**
```logql
avg_over_time(
  {service="rag-evaluation"} 
  | json 
  | unwrap metrics_answer_relevancy 
  [24h]
)
```

**Thresholds:**
- Red: 0 - 0.7
- Yellow: 0.7 - 0.85
- Green: 0.85 - 1.0

### 面板 3：平均 Context Precision（24小时）

**面板类型：** Stat

**查询：**
```logql
avg_over_time(
  {service="rag-evaluation"} 
  | json 
  | unwrap metrics_context_precision 
  [24h]
)
```

**Thresholds:**
- Red: 0 - 0.8
- Yellow: 0.8 - 0.9
- Green: 0.9 - 1.0

### 面板 4：评估次数（24小时）

**面板类型：** Stat

**查询：**
```logql
count_over_time(
  {service="rag-evaluation"} 
  [24h]
)
```

### 面板 5：Faithfulness 趋势

**面板类型：** Time series

**查询：**
```logql
{service="rag-evaluation"} 
| json 
| unwrap metrics_faithfulness
```

### 面板 6：按分块策略对比

**面板类型：** Bar gauge

**查询：**
```logql
avg by (chunking_strategy) (
  {service="rag-evaluation"} 
  | json 
  | unwrap metrics_faithfulness
)
```

### 面板 7：低 Faithfulness 告警

**面板类型：** Logs

**查询：**
```logql
{service="rag-evaluation"} 
| json 
| metrics_faithfulness < 0.8 
| line_format "🚨 {{.question_preview}} - Faithfulness: {{.metrics_faithfulness}}"
```

### 面板 8：最近评估详情表

**面板类型：** Table

**查询：**
```logql
{service="rag-evaluation"} 
| json
```

**列配置（Transformation）：**
- question_preview
- chunking_strategy
- retrieval_mode
- metrics_faithfulness
- metrics_answer_relevancy
- metrics_context_precision

## 第四步：创建告警规则

### 告警：Faithfulness 过低

1. 进入 **Alerting** → **Alert rules**
2. 点击 **New alert rule**

**查询：**
```logql
avg_over_time(
  {service="rag-evaluation"} 
  | json 
  | unwrap metrics_faithfulness 
  [5m]
) < 0.8
```

**条件：**
- Threshold: < 0.8
- For: 5 minutes

**通知渠道：** 配置邮件或 Slack 通知

## 第五步：验证数据流

### 5.1 触发一次评估

在你的应用中：

```bash
# 确保评估已启用
export EVALUATION_ENABLED=true
export EVALUATION_SAMPLE_RATE=1.0  # 临时设置为100%用于测试

# 发送一个查询
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your-project-id",
    "message": "What is a Transformer?"
  }'
```

### 5.2 检查日志

1. 查看后端日志：
   ```bash
   # 应该看到类似这样的日志
   [Auto-Eval] Starting evaluation for: What is a Transformer?...
   [Auto-Eval] Metrics: {'faithfulness': 0.95, 'answer_relevancy': 0.88, ...}
   [Auto-Eval] Evaluation logged successfully
   ```

2. 在 Grafana Explore 中查询：
   ```logql
   {service="rag-evaluation"} | json
   ```

3. 等待 30 秒 - 1 分钟，刷新仪表板

## 故障排查

### 问题 1：Grafana 中看不到评估日志

**可能原因和解决方案：**

1. **评估功能未启用**
   ```bash
   # 检查 .env 配置
   grep EVALUATION_ENABLED .env
   # 应该是: EVALUATION_ENABLED=true
   ```

2. **采样率太低，还没触发评估**
   ```bash
   # 临时设置为 100% 测试
   EVALUATION_SAMPLE_RATE=1.0
   ```

3. **Loki 配置错误**
   ```bash
   # 检查 Loki URL
   grep LOKI_URL .env
   grep LOKI_ENABLED .env
   ```

4. **后端未重启**
   ```bash
   # 修改 .env 后需要重启后端
   # 在 Zeabur 上重新部署
   ```

### 问题 2：仪表板查询返回空数据

**检查步骤：**

1. 先在 Explore 中验证原始日志存在：
   ```logql
   {service="rag-evaluation"}
   ```

2. 检查时间范围（右上角）
   - 设置为 "Last 24 hours"
   - 或自定义范围

3. 验证 JSON 解析：
   ```logql
   {service="rag-evaluation"} | json | line_format "{{.metrics_faithfulness}}"
   ```

4. 检查字段名是否正确：
   ```logql
   # 查看所有可用字段
   {service="rag-evaluation"} | json
   ```

### 问题 3：指标值不正确或为空

**检查日志格式：**

后端日志应该输出结构化 JSON：

```python
# 在 evaluation_logger.py 中
log_data = {
    "service": "rag-evaluation",
    "evaluation_type": "realtime",
    "metrics": metrics,  # 这应该是一个 dict
    ...
}
```

**验证 JSON 结构：**
```logql
{service="rag-evaluation"} 
| json 
| line_format "Faithfulness: {{.metrics_faithfulness}}"
```

## 常用 LogQL 查询

### 查询最近 10 条评估

```logql
{service="rag-evaluation"} | json | limit 10
```

### 查询特定项目的评估

```logql
{service="rag-evaluation"} 
| json 
| project_id="your-project-uuid"
```

### 查询低质量答案（Faithfulness < 0.8）

```logql
{service="rag-evaluation"} 
| json 
| metrics_faithfulness < 0.8
```

### 按策略分组统计

```logql
sum by (chunking_strategy) (
  count_over_time({service="rag-evaluation"}[24h])
)
```

### 计算平均指标

```logql
# Faithfulness
avg_over_time({service="rag-evaluation"} | json | unwrap metrics_faithfulness [24h])

# Answer Relevancy  
avg_over_time({service="rag-evaluation"} | json | unwrap metrics_answer_relevancy [24h])

# Context Precision
avg_over_time({service="rag-evaluation"} | json | unwrap metrics_context_precision [24h])
```

## 高级：数据库查询对比

如果 Grafana 中看不到数据，但想验证评估是否在运行，可以直接查询数据库：

```sql
-- 查看最近 10 条评估记录
SELECT 
    question,
    metrics->>'faithfulness' as faithfulness,
    metrics->>'answer_relevancy' as answer_relevancy,
    chunking_strategy,
    retrieval_mode,
    created_at
FROM evaluation_logs
ORDER BY created_at DESC
LIMIT 10;

-- 统计评估数量
SELECT COUNT(*) FROM evaluation_logs;

-- 按策略统计平均指标
SELECT 
    chunking_strategy,
    AVG((metrics->>'faithfulness')::float) as avg_faithfulness,
    AVG((metrics->>'answer_relevancy')::float) as avg_relevancy,
    COUNT(*) as count
FROM evaluation_logs
GROUP BY chunking_strategy;
```

## 推荐仪表板布局

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Faithfulness│ Answer Rel. │ Context Pre.│ Total Evals │
│   (Stat)    │   (Stat)    │   (Stat)    │   (Stat)    │
├─────────────────────────────┬─────────────────────────┤
│   Faithfulness Over Time    │   Answer Rel. Over Time │
│       (Time Series)         │      (Time Series)      │
├─────────────────────────────┴─────────────────────────┤
│        Metrics by Chunking Strategy (Bar Gauge)       │
├───────────────────────────────────────────────────────┤
│        Low Faithfulness Alerts (< 0.8) (Logs)         │
├───────────────────────────────────────────────────────┤
│           Recent Evaluations Detail (Table)           │
└───────────────────────────────────────────────────────┘
```

## 下一步

1. ✅ 配置完成后，保存仪表板
2. 📊 设置自动刷新（如每 30 秒）
3. 🔔 配置告警通知渠道
4. 📈 观察一段时间后分析趋势
5. 🎯 根据指标优化 RAG 系统

## 支持

如果遇到问题：
1. 检查后端日志中的 `[Auto-Eval]` 相关日志
2. 在 Grafana Explore 中测试基础查询
3. 验证数据库中是否有评估记录
4. 查看完整文档：`app/backend/docs/RAG_EVALUATION.md`

