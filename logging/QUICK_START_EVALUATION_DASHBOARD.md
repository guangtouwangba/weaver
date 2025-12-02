# 快速配置评估仪表板（5分钟）

## 步骤 1：启用评估功能 ⚙️

在后端 `.env` 文件中添加：

```bash
# 启用评估
EVALUATION_ENABLED=true

# 临时设置为100%用于测试（之后改回0.1）
EVALUATION_SAMPLE_RATE=1.0

# 确保 Loki 已配置
LOKI_ENABLED=true
LOKI_URL=https://your-loki-domain.zeabur.app/loki/api/v1/push
```

重启后端服务。

## 步骤 2：触发一次评估 🚀

发送一个测试查询：

```bash
curl -X POST http://your-backend/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your-project-id",
    "message": "What is a Transformer?"
  }'
```

检查后端日志，应该看到：
```
[Auto-Eval] Starting evaluation for: What is a Transformer?...
[Auto-Eval] Metrics: {'faithfulness': 0.95, ...}
[Auto-Eval] Evaluation logged successfully
```

## 步骤 3：在 Grafana 验证数据 📊

### 3.1 打开 Grafana Explore

1. 访问 `https://your-grafana-domain.zeabur.app`
2. 登录（admin/admin）
3. 点击左侧 **Explore** (罗盘图标)

### 3.2 执行测试查询

在查询框输入：

```logql
{service="rag-evaluation"}
```

点击 **Run query**。

**✅ 成功：** 看到评估日志（包含 faithfulness, answer_relevancy 等字段）
**❌ 失败：** 看不到数据，检查上面的配置

## 步骤 4：创建第一个面板 📈

### 方法 A：导入预配置仪表板（最简单）

1. 点击左侧 **Dashboards** → **New** → **Import**
2. 粘贴仪表板 JSON（见下方）或上传文件 `logging/grafana-dashboards/rag-evaluation-dashboard.json`
3. 选择 Loki 数据源
4. 点击 **Import**

### 方法 B：手动创建面板

1. 点击左侧 **Dashboards** → **New Dashboard**
2. 点击 **Add visualization**
3. 选择数据源：**Loki**
4. 输入查询：

```logql
avg_over_time(
  {service="rag-evaluation"} 
  | json 
  | unwrap metrics_faithfulness 
  [24h]
)
```

5. 选择可视化类型：**Stat**
6. 配置：
   - **Title:** Average Faithfulness (24h)
   - **Min:** 0
   - **Max:** 1
   - **Thresholds:** 0=红色, 0.8=黄色, 0.9=绿色

7. 点击 **Apply**

重复上述步骤创建其他指标面板。

## 步骤 5：关键查询速查表 📋

### 平均 Faithfulness（24小时）
```logql
avg_over_time({service="rag-evaluation"} | json | unwrap metrics_faithfulness [24h])
```

### 平均 Answer Relevancy（24小时）
```logql
avg_over_time({service="rag-evaluation"} | json | unwrap metrics_answer_relevancy [24h])
```

### 评估总数（24小时）
```logql
count_over_time({service="rag-evaluation"} [24h])
```

### Faithfulness 趋势图
```logql
{service="rag-evaluation"} | json | unwrap metrics_faithfulness
```

### 低质量告警（< 0.8）
```logql
{service="rag-evaluation"} | json | metrics_faithfulness < 0.8
```

### 按策略对比
```logql
avg by (chunking_strategy) (
  {service="rag-evaluation"} | json | unwrap metrics_faithfulness
)
```

## 常见问题 ❓

### Q: 看不到任何数据？

**检查清单：**

1. ✅ `EVALUATION_ENABLED=true`
2. ✅ `EVALUATION_SAMPLE_RATE=1.0` (测试时)
3. ✅ `LOKI_ENABLED=true`
4. ✅ `LOKI_URL` 配置正确
5. ✅ 后端已重启
6. ✅ 已发送测试查询
7. ✅ 后端日志显示 `[Auto-Eval]` 相关信息

### Q: 查询返回空结果？

1. 检查时间范围（右上角） - 设置为 "Last 24 hours"
2. 在 Explore 中先验证原始日志：`{service="rag-evaluation"}`
3. 确认字段名正确（使用 `| json` 查看所有字段）

### Q: 指标值显示为空或 NaN？

检查 JSON 日志格式是否正确：

```logql
{service="rag-evaluation"} | json | line_format "{{.metrics_faithfulness}}"
```

应该显示具体数值（如 0.95）而不是空白。

### Q: 如何临时禁用评估？

```bash
# 改为 false 并重启
EVALUATION_ENABLED=false
```

或者降低采样率：
```bash
# 只评估 1% 的查询
EVALUATION_SAMPLE_RATE=0.01
```

## 生产环境建议 🎯

1. **采样率：** 设置为 `0.1`（10%）平衡成本和监控需求
2. **自动刷新：** 仪表板设置为 30 秒自动刷新
3. **告警：** 配置 Faithfulness < 0.8 的告警通知
4. **时间范围：** 默认显示最近 24 小时数据
5. **保留策略：** 定期清理旧的评估记录（如保留 30 天）

## 下一步 📚

- 完整配置指南：`logging/GRAFANA_EVALUATION_SETUP.md`
- 评估功能文档：`app/backend/docs/RAG_EVALUATION.md`
- 离线策略对比：使用 `StrategyEvaluator` 测试不同配置

