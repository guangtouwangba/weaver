# 🤖 Chat API 接口文档

> 基于 SSE (Server-Sent Events) + HTTP 混合架构的智能聊天系统API

## 📖 目录

- [快速开始](#-快速开始)
- [SSE流式聊天接口](#-sse流式聊天接口)
- [传统HTTP接口](#-传统http接口)
- [对话管理接口](#-对话管理接口)
- [搜索和统计接口](#-搜索和统计接口)
- [前端集成指南](#-前端集成指南)
- [错误处理](#-错误处理)
- [最佳实践](#-最佳实践)

---

## 🚀 快速开始

### 基础信息

- **基础URL**: `http://localhost:8000/api/v1/chat`
- **内容类型**: `application/json`
- **编码**: `UTF-8`

### 认证方式

目前API无需认证，生产环境需要配置JWT或API Key认证。

### 核心概念

- **Conversation**: 对话，包含多轮问答
- **Message**: 消息，单次用户输入或AI回复
- **Topic**: 主题，用于组织和过滤对话
- **Context**: 上下文，RAG检索到的相关文档内容

---

## 🌊 SSE流式聊天接口

### POST `/stream` - 流式聊天

**最佳体验的聊天接口，推荐用于所有交互场景。**

#### 请求格式

```http
POST /api/v1/chat/stream
Content-Type: application/json

{
    "message": "什么是机器学习？",
    "topic_id": 123,
    "conversation_id": "conv-uuid-123",
    "search_type": "semantic",
    "max_results": 5,
    "score_threshold": 0.5,
    "include_context": true,
    "max_tokens": 1000,
    "temperature": 0.7,
    "context_window": 5
}
```

#### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `message` | string | ✅ | - | 用户消息内容 (1-8000字符) |
| `topic_id` | integer | ❌ | null | 主题ID，用于过滤相关文档 |
| `conversation_id` | string | ❌ | auto | 对话ID，不提供则创建新对话 |
| `search_type` | enum | ❌ | "semantic" | 搜索类型: semantic/keyword/hybrid |
| `max_results` | integer | ❌ | 5 | RAG检索结果数量 (1-20) |
| `score_threshold` | float | ❌ | 0.5 | 相似度阈值 (0.0-1.0) |
| `include_context` | boolean | ❌ | true | 是否在提示词中包含检索上下文 |
| `max_tokens` | integer | ❌ | 1000 | AI生成最大token数 (1-4000) |
| `temperature` | float | ❌ | 0.7 | 生成温度 (0.0-2.0) |
| `context_window` | integer | ❌ | 5 | 对话历史窗口大小 (0-20) |

#### SSE事件流

**响应格式**: `text/event-stream`

##### 1. 开始事件 (`start`)

```
event: start
data: {
    "message_id": "msg-uuid-456",
    "conversation_id": "conv-uuid-123"
}
```

##### 2. 进度事件 (`progress`)

```
event: progress
data: {
    "stage": "retrieving",
    "message": "正在检索相关文档...",
    "progress": 0.2
}
```

**stage取值**:
- `retrieving`: 检索文档阶段
- `generating`: AI生成阶段  
- `saving`: 保存对话阶段

##### 3. 上下文事件 (`context`)

```
event: context
data: {
    "contexts": [
        {
            "content": "机器学习是人工智能的分支...",
            "document_id": "doc-123",
            "chunk_index": 5,
            "similarity_score": 0.85,
            "document_title": "AI基础教程",
            "file_id": "file-456",
            "metadata": {}
        }
    ],
    "search_time_ms": 150,
    "total_results": 3
}
```

##### 4. 增量内容事件 (`delta`)

```
event: delta
data: {
    "content": "机器学习",
    "message_id": "msg-uuid-456",
    "token_count": 2
}
```

##### 5. 完成事件 (`complete`)

```
event: complete
data: {
    "conversation_id": "conv-uuid-123",
    "message_id": "msg-uuid-456", 
    "total_tokens": 150,
    "generation_time_ms": 3000,
    "search_time_ms": 150
}
```

##### 6. 错误事件 (`error`)

```
event: error
data: {
    "error": "API rate limit exceeded",
    "error_type": "RateLimitError",
    "stage": "generating"
}
```

#### 前端实现示例

```javascript
async function streamChat(request) {
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // 保留不完整的行

        let currentEvent = '';
        for (const line of lines) {
            if (line.startsWith('event:')) {
                currentEvent = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
                const data = JSON.parse(line.substring(5).trim());
                handleSSEEvent(currentEvent, data);
            }
        }
    }
}

function handleSSEEvent(eventType, data) {
    switch (eventType) {
        case 'start':
            console.log('开始处理:', data);
            showTypingIndicator();
            break;
        case 'progress':
            updateProgress(data.stage, data.message);
            break;
        case 'context':
            showRetrievedContexts(data.contexts);
            break;
        case 'delta':
            appendMessage(data.content);
            break;
        case 'complete':
            hideTypingIndicator();
            showMetadata(data);
            break;
        case 'error':
            showError(data.error);
            break;
    }
}
```

---

## 💬 传统HTTP接口

### POST `/` - 同步聊天

**适用于API集成和不需要流式体验的场景。**

#### 请求格式

```http
POST /api/v1/chat
Content-Type: application/json

{
    "message": "什么是机器学习？",
    "topic_id": 123,
    "conversation_id": "conv-uuid-123"
}
```

#### 响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "message_id": "msg-uuid-456",
        "conversation_id": "conv-uuid-123",
        "content": "机器学习是人工智能的一个重要分支...",
        "retrieved_contexts": [
            {
                "content": "相关文档内容...",
                "document_id": "doc-123",
                "similarity_score": 0.85
            }
        ],
        "ai_metadata": {
            "model": "gpt-3.5-turbo",
            "tokens_used": 150,
            "generation_time_ms": 3000,
            "search_time_ms": 150,
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

---

## 📋 对话管理接口

### GET `/conversations` - 获取对话列表

#### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `topic_id` | integer | ❌ | null | 主题ID过滤 |
| `limit` | integer | ❌ | 20 | 每页数量 (1-100) |
| `offset` | integer | ❌ | 0 | 偏移量 |
| `order_by` | string | ❌ | "last_message_time" | 排序字段 |
| `order_direction` | string | ❌ | "desc" | 排序方向 (asc/desc) |

#### 响应示例

```json
{
    "success": true,
    "data": {
        "conversations": [
            {
                "conversation_id": "conv-uuid-123",
                "topic_id": 123,
                "title": "机器学习讨论",
                "last_message_time": "2024-01-01T12:00:00Z",
                "message_count": 8,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        ],
        "total": 42,
        "has_more": true
    }
}
```

### GET `/conversations/{conversation_id}/messages` - 获取对话消息

#### 路径参数

- `conversation_id`: 对话ID

#### 查询参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `limit` | integer | ❌ | 50 | 消息数量 (1-200) |
| `before` | string | ❌ | null | 在此消息ID之前 |
| `include_context` | boolean | ❌ | false | 是否包含检索上下文 |

#### 响应示例

```json
{
    "success": true,
    "data": {
        "messages": [
            {
                "id": "msg-uuid-001",
                "conversation_id": "conv-uuid-123",
                "role": "user",
                "content": "什么是机器学习？",
                "timestamp": "2024-01-01T12:00:00Z",
                "metadata": {},
                "token_count": null
            },
            {
                "id": "msg-uuid-002",
                "conversation_id": "conv-uuid-123", 
                "role": "assistant",
                "content": "机器学习是...",
                "timestamp": "2024-01-01T12:00:05Z",
                "metadata": {
                    "model": "gpt-3.5-turbo",
                    "tokens_used": 150
                },
                "token_count": 150
            }
        ],
        "conversation_id": "conv-uuid-123",
        "has_more": false
    }
}
```

### DELETE `/conversations/{conversation_id}` - 删除对话

#### 路径参数

- `conversation_id`: 对话ID

#### 响应示例

```json
{
    "success": true,
    "data": {
        "deleted": true,
        "conversation_id": "conv-uuid-123"
    }
}
```

---

## 🔍 搜索和统计接口

### GET `/search` - 搜索聊天内容

#### 查询参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | ✅ | - | 搜索关键词 (1-200字符) |
| `topic_id` | integer | ❌ | null | 主题ID过滤 |
| `conversation_id` | string | ❌ | null | 对话ID过滤 |
| `role` | enum | ❌ | null | 消息角色过滤 (user/assistant/system) |
| `limit` | integer | ❌ | 20 | 结果数量 (1-100) |
| `highlight` | boolean | ❌ | true | 是否高亮关键词 |

#### 响应示例

```json
{
    "success": true,
    "data": {
        "results": [
            {
                "message": {
                    "id": "msg-uuid-123",
                    "conversation_id": "conv-uuid-456",
                    "role": "user",
                    "content": "机器学习的原理是什么？",
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                "highlights": [
                    "<em>机器学习</em>的原理是什么？"
                ],
                "score": 0.95
            }
        ],
        "total": 15,
        "query_time_ms": 25
    }
}
```

### GET `/statistics` - 获取聊天统计

#### 查询参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `topic_id` | integer | ❌ | null | 主题ID过滤 |

#### 响应示例

```json
{
    "success": true,
    "data": {
        "total_conversations": 1250,
        "total_messages": 8900,
        "avg_messages_per_conversation": 7.12,
        "total_tokens_used": 245000,
        "top_topics": [
            {
                "topic_id": 123,
                "topic_name": "机器学习",
                "conversation_count": 89,
                "message_count": 634
            }
        ],
        "daily_stats": [
            {
                "date": "2024-01-01",
                "conversations": 25,
                "tokens": 3500
            }
        ]
    }
}
```

---

## 🛠️ 前端集成指南

### React Hook 示例

```typescript
import { useState, useCallback } from 'react';

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

interface UseChatReturn {
    messages: ChatMessage[];
    isLoading: boolean;
    sendMessage: (message: string) => Promise<void>;
    error: string | null;
}

export function useChat(conversationId?: string): UseChatReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const sendMessage = useCallback(async (message: string) => {
        setIsLoading(true);
        setError(null);

        // 添加用户消息
        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMessage]);

        try {
            const response = await fetch('/api/v1/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    conversation_id: conversationId,
                    topic_id: null,
                    max_tokens: 1000,
                    temperature: 0.7
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            let assistantMessage: ChatMessage = {
                id: '',
                role: 'assistant',
                content: '',
                timestamp: new Date().toISOString()
            };

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (reader) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                let currentEvent = '';
                for (const line of lines) {
                    if (line.startsWith('event:')) {
                        currentEvent = line.substring(6).trim();
                    } else if (line.startsWith('data:')) {
                        const data = JSON.parse(line.substring(5).trim());
                        
                        if (currentEvent === 'start') {
                            assistantMessage.id = data.message_id;
                            setMessages(prev => [...prev, assistantMessage]);
                        } else if (currentEvent === 'delta') {
                            assistantMessage.content += data.content;
                            setMessages(prev => 
                                prev.map(msg => 
                                    msg.id === assistantMessage.id 
                                        ? { ...msg, content: assistantMessage.content }
                                        : msg
                                )
                            );
                        } else if (currentEvent === 'error') {
                            throw new Error(data.error);
                        }
                    }
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    }, [conversationId]);

    return { messages, isLoading, sendMessage, error };
}
```

### Vue 3 Composition API 示例

```typescript
import { ref, reactive } from 'vue';

export function useChat(conversationId?: string) {
    const messages = ref<ChatMessage[]>([]);
    const isLoading = ref(false);
    const error = ref<string | null>(null);

    const sendMessage = async (message: string) => {
        isLoading.value = true;
        error.value = null;

        // 添加用户消息
        messages.value.push({
            id: `user-${Date.now()}`,
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });

        try {
            const response = await fetch('/api/v1/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    conversation_id: conversationId
                })
            });

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            
            let assistantMessage = {
                id: '',
                role: 'assistant' as const,
                content: '',
                timestamp: new Date().toISOString()
            };

            while (reader) {
                const { done, value } = await reader.read();
                if (done) break;

                // SSE解析逻辑...
            }
        } catch (err) {
            error.value = err instanceof Error ? err.message : 'Unknown error';
        } finally {
            isLoading.value = false;
        }
    };

    return {
        messages: readonly(messages),
        isLoading: readonly(isLoading),
        error: readonly(error),
        sendMessage
    };
}
```

---

## ⚠️ 错误处理

### 常见错误代码

| 状态码 | 错误类型 | 说明 | 解决方案 |
|--------|----------|------|----------|
| 400 | Bad Request | 请求参数错误 | 检查参数格式和范围 |
| 422 | Validation Error | 数据验证失败 | 检查必需字段和数据类型 |
| 429 | Rate Limit | 请求频率过高 | 降低请求频率，增加重试间隔 |
| 500 | Internal Error | 服务器内部错误 | 联系技术支持 |
| 503 | Service Unavailable | 服务不可用 | 检查依赖服务状态 |

### 错误响应格式

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "The 'message' field is required",
        "details": {
            "field": "message",
            "constraint": "required"
        }
    }
}
```

### SSE错误处理

SSE连接中的错误通过 `error` 事件传递：

```javascript
function handleSSEEvent(eventType, data) {
    if (eventType === 'error') {
        console.error('Chat error:', data.error);
        
        // 根据错误类型处理
        switch (data.error_type) {
            case 'RateLimitError':
                showMessage('请求过于频繁，请稍后再试');
                break;
            case 'OpenAIError':
                showMessage('AI服务暂时不可用');
                break;
            default:
                showMessage('处理失败，请重试');
        }
    }
}
```

---

## ✨ 最佳实践

### 1. 连接管理

- **自动重连**: SSE连接断开时自动重连
- **心跳检测**: 定期发送ping保持连接活跃
- **连接池**: 复用连接，避免频繁创建

```javascript
class ChatClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    async connectSSE(request, callbacks) {
        try {
            // SSE连接逻辑
        } catch (error) {
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                const delay = Math.pow(2, this.retryCount) * 1000;
                setTimeout(() => this.connectSSE(request, callbacks), delay);
            }
        }
    }
}
```

### 2. 性能优化

- **分页加载**: 对话历史采用分页加载
- **虚拟滚动**: 大量消息使用虚拟滚动
- **缓存策略**: 缓存对话列表和消息内容

### 3. 用户体验

- **输入防抖**: 用户输入时防抖处理
- **加载状态**: 显示清晰的加载和进度状态
- **错误提示**: 友好的错误信息和重试按钮

### 4. 安全考虑

- **输入验证**: 前端和后端双重验证
- **内容过滤**: 过滤敏感内容
- **速率限制**: 防止滥用API

### 5. 监控和日志

- **请求追踪**: 记录每个请求的唯一ID
- **性能监控**: 监控响应时间和成功率
- **用户行为**: 记录用户交互数据

---

## 📞 技术支持

### 健康检查

检查服务状态：

```http
GET /api/v1/chat/health
```

### 开发环境

- **本地调试**: `http://localhost:8000`
- **API文档**: `http://localhost:8000/docs`
- **Swagger UI**: 交互式API文档

### 联系方式

- **文档更新**: 2024年1月
- **API版本**: v1.0
- **技术栈**: FastAPI + SSE + Elasticsearch + Weaviate

---

*本文档持续更新，如有疑问请联系开发团队。*
