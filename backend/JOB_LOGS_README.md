# Job实时日志功能

这个文档介绍了research-agent-rag系统中完整的job实时日志功能实现。

## 功能特性

### ✅ 已实现的功能

1. **结构化日志存储**
   - 数据库存储：使用PostgreSQL/SQLite存储结构化日志
   - Elasticsearch存储：支持高级搜索和聚合分析
   - 自动日志清理：防止数据库膨胀

2. **REST API接口**
   - `GET /api/cronjobs/{job_id}/logs` - 获取job历史日志
   - `GET /api/cronjobs/{job_id}/logs/realtime` - 获取实时日志更新
   - 支持分页、级别过滤、时间范围过滤、文本搜索

3. **实时日志流**
   - WebSocket支持：`ws://localhost:8000/api/cronjobs/{job_id}/logs/ws`
   - Server-Sent Events支持
   - 自动重连和错误处理

4. **高级功能**
   - 日志聚合和统计
   - 多级别过滤（DEBUG, INFO, WARNING, ERROR, CRITICAL）
   - 执行步骤跟踪
   - 性能指标记录
   - 状态变更历史

## API接口文档

### 1. 获取Job日志

```http
GET /api/cronjobs/{job_id}/logs
```

**查询参数:**
- `level` (string, optional): 日志级别过滤
- `step` (string, optional): 执行步骤过滤
- `start_time` (string, optional): 开始时间 (ISO格式)
- `end_time` (string, optional): 结束时间 (ISO格式)
- `search` (string, optional): 文本搜索
- `skip` (int, optional): 跳过条数，默认0
- `limit` (int, optional): 返回条数，默认100

**响应示例:**
```json
{
  "logs": [
    {
      "id": "log_123",
      "job_run_id": "run_456",
      "timestamp": "2025-01-31T10:30:00Z",
      "level": "INFO",
      "message": "开始处理论文搜索",
      "details": {"step": "paper_search", "keywords": ["ML", "AI"]},
      "step": "paper_search",
      "duration_ms": 1500
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100,
  "has_more": true,
  "search_time_ms": 25
}
```

### 2. 获取实时日志

```http
GET /api/cronjobs/{job_id}/logs/realtime
```

**查询参数:**
- `since_timestamp` (string, optional): 获取此时间后的日志
- `level` (string, optional): 日志级别过滤
- `limit` (int, optional): 返回条数，默认50

### 3. WebSocket实时日志流

```javascript
const ws = new WebSocket('ws://localhost:8000/api/cronjobs/{job_id}/logs/ws');

// 订阅日志流
ws.send(JSON.stringify({
  type: "subscribe",
  types: ["log", "status", "metric"],
  filters: {
    level: "INFO"
  }
}));

// 接收日志消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到日志:', data);
};
```

## 使用示例

### 1. Python客户端示例

```python
import requests
import asyncio
import websockets
import json

# 获取历史日志
response = requests.get(
    'http://localhost:8000/api/cronjobs/job123/logs',
    params={
        'level': 'INFO',
        'limit': 50,
        'search': 'error'
    }
)
logs = response.json()

# WebSocket实时日志
async def stream_logs():
    uri = 'ws://localhost:8000/api/cronjobs/job123/logs/ws'
    async with websockets.connect(uri) as ws:
        # 订阅
        await ws.send(json.dumps({
            "type": "subscribe",
            "types": ["log"],
            "filters": {"level": "ERROR"}
        }))
        
        # 接收消息
        async for message in ws:
            data = json.loads(message)
            print(f"日志: {data}")

asyncio.run(stream_logs())
```

### 2. JavaScript前端示例

```javascript
// 获取历史日志
async function getJobLogs(jobId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`/api/cronjobs/${jobId}/logs?${params}`);
  return await response.json();
}

// WebSocket实时日志
function streamJobLogs(jobId, onLog) {
  const ws = new WebSocket(`ws://localhost:8000/api/cronjobs/${jobId}/logs/ws`);
  
  ws.onopen = () => {
    ws.send(JSON.stringify({
      type: "subscribe",
      types: ["log", "status"],
      filters: {}
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'log') {
      onLog(data.data);
    }
  };
}

// 使用示例
streamJobLogs('job123', (log) => {
  console.log(`[${log.level}] ${log.message}`);
});
```

## 配置

### Elasticsearch配置

在环境变量中设置:

```bash
# Elasticsearch设置
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your_password
ELASTICSEARCH_INDEX_PREFIX=job-logs

# 数据库设置
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### 日志清理配置

```python
# 自动清理90天前的日志
from services.job_log_service import JobLogService

service = JobLogService(db_session)
deleted_count = service.cleanup_old_logs(days=90)
```

## 测试和演示

### 运行测试脚本

```bash
# 基本API测试
python test_job_logs_api.py

# WebSocket测试  
python test_websocket_logs.py

# 完整功能演示
python demo_job_logs.py
```

### 手动测试流程

1. **启动服务器**
   ```bash
   python main.py --port 8000
   ```

2. **创建测试job**
   ```bash
   curl -X POST http://localhost:8000/api/cronjobs \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Job",
       "keywords": ["test"],
       "cron_expression": "0 0 * * *",
       "enabled": true
     }'
   ```

3. **触发job执行**
   ```bash
   curl -X POST http://localhost:8000/api/cronjobs/{job_id}/trigger \
     -H "Content-Type: application/json" \
     -d '{"force_reprocess": false}'
   ```

4. **查看日志**
   ```bash
   curl http://localhost:8000/api/cronjobs/{job_id}/logs
   ```

## 架构设计

### 组件结构

```
├── utils/
│   ├── elasticsearch_logger.py    # Elasticsearch日志记录器
│   ├── job_logger.py              # 结构化job日志记录器
│   └── websocket_manager.py       # WebSocket连接管理
├── services/
│   └── job_log_service.py         # 日志服务层
├── routes/
│   └── job_log_routes.py          # API路由
├── models/schemas/
│   └── job_log.py                 # 数据模型
└── repositories/
    └── job_log_repository.py      # 数据访问层
```

### 日志流程

1. **任务执行** → JobLogger记录日志
2. **双重存储** → 数据库 + Elasticsearch
3. **实时推送** → WebSocket广播
4. **API查询** → 支持多种过滤条件
5. **自动清理** → 定期清理历史日志

## 故障排除

### 常见问题

1. **WebSocket连接失败**
   - 检查服务器是否运行在正确端口
   - 确认WebSocket路由已正确注册
   - 查看服务器日志获取详细错误信息

2. **日志不显示**
   - 确认job正在执行
   - 检查Elasticsearch连接状态
   - 验证数据库连接

3. **性能问题**
   - 调整日志级别，减少DEBUG日志
   - 增加日志清理频率
   - 优化Elasticsearch索引设置

### 日志级别

- `DEBUG`: 详细调试信息
- `INFO`: 常规信息日志
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

## 扩展功能

可以通过以下方式扩展功能：

1. **自定义过滤器** - 在LogSearchFilters中添加新字段
2. **新的存储后端** - 实现新的日志存储适配器
3. **告警集成** - 基于日志触发告警通知
4. **日志分析** - 集成更多分析和可视化工具

## 相关文件

- `utils/elasticsearch_logger.py` - Elasticsearch集成
- `utils/job_logger.py` - 结构化日志记录
- `services/job_log_service.py` - 核心日志服务
- `routes/job_log_routes.py` - API端点定义
- `test_job_logs_api.py` - API测试脚本
- `demo_job_logs.py` - 完整演示脚本