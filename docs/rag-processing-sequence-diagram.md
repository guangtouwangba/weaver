# RAG处理流程时序图

## 完整的文件上传后RAG处理时序图

以下是详细的时序图，展示了从文件上传到RAG处理完成的完整流程：

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as 文件上传API
    participant FileHandler as 文件处理器
    participant Storage as 文件存储
    participant DocLoader as 文档加载器
    participant DB as 数据库
    participant RAGHandler as RAG处理器
    participant Chunker as 分块处理器
    participant Embedder as 嵌入服务
    participant VectorDB as 向量数据库
    participant Queue as 任务队列
    
    %% 文件上传阶段
    User->>API: 上传文件
    API->>Storage: 存储文件
    Storage-->>API: 返回存储路径
    API->>DB: 创建文件记录
    API->>Queue: 触发上传完成任务
    API-->>User: 返回文件ID和状态
    
    %% 文件处理阶段
    Queue->>FileHandler: 执行上传完成处理
    FileHandler->>Storage: 验证文件存在
    Storage-->>FileHandler: 确认文件存在
    FileHandler->>Storage: 下载到临时目录
    Storage-->>FileHandler: 返回文件内容
    
    %% 文档加载阶段
    FileHandler->>DocLoader: 加载文档
    DocLoader->>DocLoader: 检测文件格式
    DocLoader->>DocLoader: 解析文档内容
    DocLoader-->>FileHandler: 返回Document对象
    
    %% 创建文档记录
    FileHandler->>DB: 创建Document记录
    DB-->>FileHandler: 返回文档ID
    FileHandler->>Queue: 触发RAG处理任务
    FileHandler->>FileHandler: 清理临时文件
    
    %% RAG处理阶段
    Queue->>RAGHandler: 执行RAG处理
    RAGHandler->>DB: 更新文件状态为"处理中"
    RAGHandler->>Chunker: 文档分块
    
    %% 分块处理
    Chunker->>Chunker: 智能分块
    Chunker->>Chunker: 质量评分
    Chunker->>DB: 保存文档块
    Chunker-->>RAGHandler: 返回分块结果
    
    %% 嵌入生成
    RAGHandler->>Queue: 触发嵌入生成任务
    Queue->>Embedder: 生成嵌入向量
    Embedder->>Embedder: 批量向量化
    Embedder-->>RAGHandler: 返回嵌入向量
    
    %% 向量存储
    RAGHandler->>Queue: 触发向量存储任务
    Queue->>VectorDB: 存储向量
    VectorDB->>VectorDB: 批量插入向量
    VectorDB->>VectorDB: 构建索引
    VectorDB-->>RAGHandler: 返回存储结果
    
    %% 完成处理
    RAGHandler->>DB: 更新处理状态为"完成"
    RAGHandler->>DB: 更新统计信息
    
    %% 用户查询状态
    User->>API: 查询处理状态
    API->>DB: 获取处理状态
    DB-->>API: 返回状态信息
    API-->>User: 返回处理结果
```

## 错误处理流程

```mermaid
sequenceDiagram
    participant Handler as 任务处理器
    participant Queue as 任务队列
    participant Monitor as 监控系统
    participant DB as 数据库
    participant Alert as 告警系统
    
    Handler->>Handler: 处理任务
    Handler->>Handler: 发生错误
    Handler->>DB: 记录错误信息
    Handler->>Monitor: 报告错误指标
    
    alt 可重试错误
        Handler->>Queue: 安排重试任务
        Queue->>Handler: 延迟后重新执行
    else 致命错误
        Handler->>DB: 标记任务失败
        Handler->>Alert: 触发告警
        Alert->>Alert: 发送通知
    end
    
    Monitor->>Monitor: 分析错误趋势
    Monitor->>Alert: 达到阈值时告警
```

## 并发处理流程

```mermaid
sequenceDiagram
    participant Queue as 任务队列
    participant Worker1 as 工作器1
    participant Worker2 as 工作器2
    participant Worker3 as 工作器3
    participant Embedder as 嵌入服务
    participant VectorDB as 向量数据库
    
    Queue->>Worker1: 分配任务A
    Queue->>Worker2: 分配任务B
    Queue->>Worker3: 分配任务C
    
    par 并行处理
        Worker1->>Embedder: 生成嵌入A
        Worker2->>Embedder: 生成嵌入B
        Worker3->>Embedder: 生成嵌入C
    end
    
    par 并行存储
        Worker1->>VectorDB: 存储向量A
        Worker2->>VectorDB: 存储向量B  
        Worker3->>VectorDB: 存储向量C
    end
    
    Worker1-->>Queue: 完成任务A
    Worker2-->>Queue: 完成任务B
    Worker3-->>Queue: 完成任务C
```

## 状态流转图

```mermaid
stateDiagram-v2
    [*] --> UPLOADING: 开始上传
    UPLOADING --> AVAILABLE: 上传完成
    AVAILABLE --> PROCESSING: 开始RAG处理
    
    state PROCESSING {
        [*] --> PARSING: 解析文档
        PARSING --> CHUNKING: 文档分块
        CHUNKING --> EMBEDDING: 生成嵌入
        EMBEDDING --> STORING: 存储向量
        STORING --> INDEXING: 构建索引
        INDEXING --> [*]: 处理完成
    }
    
    PROCESSING --> COMPLETED: 处理成功
    PROCESSING --> FAILED: 处理失败
    
    FAILED --> PROCESSING: 重试处理
    FAILED --> ABANDONED: 放弃处理
    
    COMPLETED --> [*]: 结束
    ABANDONED --> [*]: 结束
    
    note right of PROCESSING
        各个子状态可以
        独立失败和重试
    end note
    
    note right of FAILED
        根据错误类型决定
        是否可以重试
    end note
```

## 性能监控流程

```mermaid
sequenceDiagram
    participant System as 系统组件
    participant Metrics as 指标收集器
    participant Prometheus as Prometheus
    participant Grafana as Grafana
    participant AlertManager as 告警管理器
    participant Admin as 管理员
    
    loop 持续监控
        System->>Metrics: 上报性能指标
        Metrics->>Prometheus: 存储指标数据
        Prometheus->>Grafana: 提供查询接口
        Grafana->>Grafana: 渲染监控面板
        
        Prometheus->>Prometheus: 检查告警规则
        alt 指标异常
            Prometheus->>AlertManager: 触发告警
            AlertManager->>Admin: 发送通知
        end
    end
```

这些图表展示了RAG处理系统的完整工作流程，包括正常处理流程、错误处理、并发处理、状态管理和监控等各个方面。通过这些可视化图表，可以更好地理解系统的设计和运行机制。


