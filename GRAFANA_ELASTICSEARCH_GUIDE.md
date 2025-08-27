# 📊 在Grafana中查看Elasticsearch数据完整指南

## 🎯 快速开始

### 1. 一键设置和打开
```bash
# 设置Grafana Elasticsearch集成
make grafana-setup

# 打开Grafana界面
make grafana-open
```

### 2. 登录Grafana
- **地址**: http://localhost:3000
- **用户名**: `admin`
- **密码**: `admin123`

## 📈 查看聊天数据的步骤

### 方法一：使用自动创建的Dashboard

1. **登录Grafana**后，在左侧导航栏点击 **"Dashboards"**
2. 查找名为 **"Chat Messages Dashboard"** 的面板
3. 点击进入，你将看到：
   - **总消息数**: 实时统计
   - **时间线图表**: 消息数量随时间变化
   - **最近消息表格**: 最新的聊天记录

### 方法二：手动创建可视化

1. **创建新Dashboard**:
   - 点击左侧的 "+" → "Dashboard"
   - 点击 "Add visualization"

2. **选择数据源**:
   - 在数据源下拉菜单中选择 **"elasticsearch-chat-manual"**

3. **配置查询**:
   - Index pattern: `chat-messages-*`
   - Time field: `timestamp`
   - Query: `*` (显示所有数据)

4. **选择可视化类型**:
   - **Stat**: 显示总数
   - **Time series**: 时间线图表
   - **Table**: 表格显示详细数据
   - **Logs**: 日志格式显示

## 🔧 常见配置示例

### 📊 统计面板配置
```json
{
  "targets": [
    {
      "refId": "A",
      "query": "*",
      "metrics": [{"id": "1", "type": "count"}],
      "timeField": "timestamp"
    }
  ]
}
```

### 📈 时间序列图表配置
```json
{
  "targets": [
    {
      "refId": "A", 
      "query": "*",
      "metrics": [{"id": "1", "type": "count"}],
      "bucketAggs": [
        {
          "id": "2",
          "type": "date_histogram", 
          "field": "timestamp",
          "settings": {"interval": "1h"}
        }
      ]
    }
  ]
}
```

### 📋 表格配置
```json
{
  "targets": [
    {
      "refId": "A",
      "query": "*", 
      "metrics": [
        {
          "id": "1", 
          "type": "raw_data",
          "settings": {"size": 10}
        }
      ]
    }
  ]
}
```

## 🎨 高级查询示例

### 按对话ID过滤
```
conversation_id:"test-conversation-001"
```

### 搜索特定内容
```
user_message:"AI" OR assistant_message:"AI"
```

### 时间范围过滤
```
timestamp:[now-1d TO now]
```

### 组合查询
```
conversation_id:"conv-001" AND user_message:"neural networks"
```

## 🛠️ 维护命令

### 检查服务状态
```bash
make grafana-check
```

### 添加测试数据
```bash
make grafana-test-data
```

### 重启服务
```bash
docker-compose -f docker-compose.middleware.yaml restart grafana
```

## 📊 可视化字段说明

### 主要字段
- **conversation_id**: 对话唯一标识
- **user_message**: 用户输入的消息
- **assistant_message**: AI助手的回复
- **timestamp**: 消息时间戳
- **ai_metadata**: AI模型相关元数据

### 聚合查询
- **count**: 消息总数
- **cardinality**: 唯一值计数（如不同对话数）
- **avg**: 平均值（如消息长度）
- **terms**: 分组统计

## 🔍 故障排除

### 1. 数据源连接失败
```bash
# 检查Elasticsearch服务状态
curl http://localhost:9200/_cluster/health

# 重启Elasticsearch
docker-compose -f docker-compose.middleware.yaml restart elasticsearch
```

### 2. 没有显示数据
```bash
# 检查索引是否存在
curl "http://localhost:9200/_cat/indices/chat-*"

# 添加测试数据
make grafana-test-data
```

### 3. 时间字段问题
确保在数据源配置中：
- Time field 设置为 `timestamp`
- ES version 设置为 `8.0.0`

### 4. 权限问题
确保：
- Grafana能访问Elasticsearch (URL: `http://elasticsearch:9200`)
- 没有防火墙阻止连接

## 💡 最佳实践

1. **使用变量**: 创建Dashboard变量来动态过滤数据
2. **设置刷新频率**: 根据需要设置30s-5m的自动刷新
3. **添加告警**: 为重要指标设置阈值告警
4. **分组展示**: 使用Row面板组织相关图表
5. **权限控制**: 为不同用户设置适当的查看权限

## 🎯 完整工作流

1. **启动服务**: `make start`
2. **检查状态**: `make grafana-check`
3. **设置数据源**: `make grafana-setup`  
4. **添加测试数据**: `make grafana-test-data`
5. **打开界面**: `make grafana-open`
6. **创建可视化**: 手动或使用自动Dashboard

现在你可以在Grafana中实时监控和分析你的RAG系统中的所有聊天数据了！ 🎉