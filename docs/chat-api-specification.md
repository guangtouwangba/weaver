# Chat系统API接口规范

## 📋 概述

Chat系统API提供完整的聊天功能，包括会话管理、消息处理、流式响应和文档检索功能。所有API都遵循RESTful设计原则，支持JSON格式的请求和响应。

## 🔑 认证方式

### 1. Bearer Token认证

```http
Authorization: Bearer <your_access_token>
```

### 2. API Key认证 (可选)

```http
X-API-Key: <your_api_key>
```

## 📝 API规范

### 基础信息

- **Base URL**: `https://api.example.com/api/v1`
- **Content-Type**: `application/json`
- **Accept**: `application/json`
- **API Version**: `v1`

### 通用响应格式

```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "error": null,
    "meta": {
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "req_123456789",
        "version": "v1"
    }
}
```

### 错误响应格式

```json
{
    "success": false,
    "data": null,
    "message": "操作失败",
    "error": {
        "code": "VALIDATION_ERROR",
        "details": "请求参数验证失败",
        "field_errors": {
            "content": ["消息内容不能为空"]
        }
    },
    "meta": {
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "req_123456789",
        "version": "v1"
    }
}
```

## 🗂️ API接口详情

### 1. 会话管理

#### 1.1 创建聊天会话

**接口**: `POST /chat/sessions`

**请求参数**:
```json
{
    "title": "关于机器学习的讨论",
    "description": "探讨深度学习算法原理",
    "topic_id": 123,
    "model_config": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": true
    },
    "context_settings": {
        "max_context_length": 8000,
        "include_document_metadata": true,
        "context_window_strategy": "sliding",
        "relevance_threshold": 0.7
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": 1,
        "session_id": "sess_abc123def456",
        "user_id": 1001,
        "topic_id": 123,
        "title": "关于机器学习的讨论",
        "description": "探讨深度学习算法原理",
        "status": "active",
        "model_config": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": true
        },
        "context_settings": {
            "max_context_length": 8000,
            "include_document_metadata": true,
            "context_window_strategy": "sliding",
            "relevance_threshold": 0.7
        },
        "message_count": 0,
        "total_tokens": 0,
        "last_activity_at": null,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "message": "会话创建成功"
}
```

#### 1.2 获取会话列表

**接口**: `GET /chat/sessions`

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页大小 (默认: 20, 最大: 100)
- `topic_id`: 主题ID过滤
- `status`: 状态过滤 (active/archived/deleted)
- `search`: 标题搜索关键词

**请求示例**:
```http
GET /chat/sessions?page=1&page_size=20&topic_id=123&status=active
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "sessions": [
            {
                "id": 1,
                "session_id": "sess_abc123def456",
                "title": "关于机器学习的讨论",
                "description": "探讨深度学习算法原理",
                "status": "active",
                "message_count": 15,
                "total_tokens": 3500,
                "last_activity_at": "2024-01-15T09:45:00Z",
                "created_at": "2024-01-15T09:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 45,
            "total_pages": 3,
            "has_next": true,
            "has_prev": false
        }
    },
    "message": "获取会话列表成功"
}
```

#### 1.3 获取会话详情

**接口**: `GET /chat/sessions/{session_id}`

**路径参数**:
- `session_id`: 会话ID

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": 1,
        "session_id": "sess_abc123def456",
        "user_id": 1001,
        "topic_id": 123,
        "title": "关于机器学习的讨论",
        "description": "探讨深度学习算法原理",
        "status": "active",
        "model_config": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "context_settings": {
            "max_context_length": 8000,
            "include_document_metadata": true
        },
        "message_count": 15,
        "total_tokens": 3500,
        "last_activity_at": "2024-01-15T09:45:00Z",
        "created_at": "2024-01-15T09:00:00Z",
        "updated_at": "2024-01-15T09:45:00Z"
    },
    "message": "获取会话详情成功"
}
```

#### 1.4 更新会话

**接口**: `PUT /chat/sessions/{session_id}`

**请求参数**:
```json
{
    "title": "更新后的标题",
    "description": "更新后的描述",
    "status": "archived",
    "model_config": {
        "temperature": 0.5
    }
}
```

#### 1.5 删除会话

**接口**: `DELETE /chat/sessions/{session_id}`

**响应示例**:
```json
{
    "success": true,
    "data": null,
    "message": "会话删除成功"
}
```

### 2. 消息管理

#### 2.1 发送消息

**接口**: `POST /chat/sessions/{session_id}/messages`

**请求参数**:
```json
{
    "content": "请解释一下机器学习的基本概念",
    "content_type": "text",
    "metadata": {
        "user_context": "初学者",
        "preferred_language": "zh-CN",
        "include_examples": true
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": 1,
        "message_id": "msg_user_123456",
        "session_id": "sess_abc123def456",
        "parent_message_id": null,
        "role": "user",
        "content": "请解释一下机器学习的基本概念",
        "content_type": "text",
        "metadata": {
            "user_context": "初学者",
            "preferred_language": "zh-CN"
        },
        "tokens": 12,
        "status": "completed",
        "created_at": "2024-01-15T10:30:00Z",
        "assistant_response": {
            "id": 2,
            "message_id": "msg_assistant_123457",
            "role": "assistant",
            "content": "机器学习是人工智能的一个重要分支...",
            "tokens": 256,
            "status": "completed",
            "references": [
                {
                    "reference_id": "ref_123",
                    "document_id": "doc_456",
                    "excerpt": "机器学习定义...",
                    "relevance_score": 0.95
                }
            ]
        }
    },
    "message": "消息发送成功"
}
```

#### 2.2 获取消息历史

**接口**: `GET /chat/sessions/{session_id}/messages`

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页大小 (默认: 50, 最大: 100)
- `before_message_id`: 在指定消息之前的消息
- `after_message_id`: 在指定消息之后的消息
- `role`: 角色过滤 (user/assistant/system)

**请求示例**:
```http
GET /chat/sessions/sess_abc123def456/messages?page=1&page_size=20&role=user
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "messages": [
            {
                "id": 2,
                "message_id": "msg_assistant_123457",
                "session_id": "sess_abc123def456",
                "parent_message_id": "msg_user_123456",
                "role": "assistant",
                "content": "机器学习是人工智能的一个重要分支...",
                "content_type": "markdown",
                "tokens": 256,
                "model": "gpt-4",
                "status": "completed",
                "processing_time_ms": 1500,
                "created_at": "2024-01-15T10:30:15Z"
            },
            {
                "id": 1,
                "message_id": "msg_user_123456",
                "session_id": "sess_abc123def456",
                "role": "user",
                "content": "请解释一下机器学习的基本概念",
                "content_type": "text",
                "tokens": 12,
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 15,
            "has_next": false,
            "has_prev": false
        }
    },
    "message": "获取消息历史成功"
}
```

#### 2.3 获取消息详情

**接口**: `GET /chat/messages/{message_id}`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": 2,
        "message_id": "msg_assistant_123457",
        "session_id": "sess_abc123def456",
        "parent_message_id": "msg_user_123456",
        "role": "assistant",
        "content": "机器学习是人工智能的一个重要分支...",
        "content_type": "markdown",
        "metadata": {
            "model_config": {
                "model": "gpt-4",
                "temperature": 0.7
            }
        },
        "tokens": 256,
        "model": "gpt-4",
        "prompt_tokens": 150,
        "completion_tokens": 256,
        "status": "completed",
        "processing_time_ms": 1500,
        "retrieval_time_ms": 300,
        "generation_time_ms": 1200,
        "created_at": "2024-01-15T10:30:15Z",
        "updated_at": "2024-01-15T10:30:15Z"
    },
    "message": "获取消息详情成功"
}
```

#### 2.4 重新生成回复

**接口**: `POST /chat/messages/{message_id}/regenerate`

**请求参数**:
```json
{
    "model_config": {
        "temperature": 0.5,
        "max_tokens": 1500
    },
    "regenerate_reason": "用户不满意当前回复"
}
```

### 3. 流式对话 (WebSocket)

#### 3.1 建立WebSocket连接

**接口**: `WS /chat/sessions/{session_id}/stream`

**连接参数**:
- `session_id`: 会话ID
- `token`: 认证令牌 (查询参数)

**连接示例**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/sessions/sess_abc123def456/stream?token=your_token');

ws.onopen = function() {
    console.log('Connected to chat stream');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleStreamMessage(data);
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function() {
    console.log('WebSocket connection closed');
};
```

#### 3.2 发送流式消息

**客户端发送消息格式**:
```json
{
    "type": "send_message",
    "data": {
        "content": "什么是深度学习？",
        "content_type": "text",
        "metadata": {
            "stream_response": true
        }
    },
    "message_id": "client_msg_123"
}
```

#### 3.3 服务端流式响应格式

**开始流式响应**:
```json
{
    "type": "stream_start",
    "data": {
        "session_id": "sess_abc123def456",
        "message_id": "msg_assistant_123458",
        "user_message_id": "msg_user_123457"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

**内容流式数据**:
```json
{
    "type": "content_chunk",
    "data": {
        "session_id": "sess_abc123def456",
        "message_id": "msg_assistant_123458",
        "chunk_index": 1,
        "content": "深度学习是机器学习的一个",
        "is_final": false
    },
    "timestamp": "2024-01-15T10:30:01Z"
}
```

**文档引用数据**:
```json
{
    "type": "reference_chunk",
    "data": {
        "session_id": "sess_abc123def456",
        "message_id": "msg_assistant_123458",
        "reference": {
            "reference_id": "ref_456",
            "document_id": "doc_789",
            "chunk_id": "chunk_101",
            "excerpt": "深度学习是一种基于人工神经网络的机器学习方法...",
            "relevance_score": 0.92,
            "document_title": "深度学习入门指南"
        }
    },
    "timestamp": "2024-01-15T10:30:05Z"
}
```

**流式响应结束**:
```json
{
    "type": "stream_end",
    "data": {
        "session_id": "sess_abc123def456",
        "message_id": "msg_assistant_123458",
        "final_content": "深度学习是机器学习的一个重要分支...",
        "total_tokens": 180,
        "total_chunks": 25,
        "references_count": 3,
        "processing_time_ms": 2500
    },
    "timestamp": "2024-01-15T10:30:15Z"
}
```

**错误响应**:
```json
{
    "type": "error",
    "data": {
        "session_id": "sess_abc123def456",
        "error_code": "GENERATION_FAILED",
        "error_message": "LLM服务暂时不可用",
        "retry_after": 30
    },
    "timestamp": "2024-01-15T10:30:10Z"
}
```

### 4. 文档搜索

#### 4.1 搜索文档

**接口**: `POST /chat/search`

**请求参数**:
```json
{
    "query": "机器学习算法分类",
    "topic_id": 123,
    "search_type": "hybrid",
    "max_results": 10,
    "relevance_threshold": 0.6,
    "filters": {
        "content_type": ["pdf", "md"],
        "date_range": {
            "start": "2023-01-01",
            "end": "2024-01-01"
        }
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "document_id": "doc_123",
                "chunk_id": "chunk_456",
                "title": "机器学习算法详解",
                "content": "机器学习算法可以分为监督学习、无监督学习和强化学习三大类...",
                "relevance_score": 0.95,
                "metadata": {
                    "file_type": "pdf",
                    "page_number": 15,
                    "author": "张三",
                    "created_at": "2023-06-15T00:00:00Z"
                }
            }
        ],
        "total_results": 25,
        "search_time_ms": 150,
        "query_embedding_time_ms": 50
    },
    "message": "文档搜索成功"
}
```

#### 4.2 获取消息引用

**接口**: `GET /chat/messages/{message_id}/references`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "references": [
            {
                "id": 1,
                "reference_id": "ref_123",
                "message_id": "msg_assistant_123458",
                "document_id": "doc_456",
                "chunk_id": "chunk_789",
                "reference_type": "direct",
                "relevance_score": 0.95,
                "excerpt": "机器学习是一种人工智能技术...",
                "start_char": 150,
                "end_char": 280,
                "page_number": 5,
                "display_order": 1,
                "document_info": {
                    "title": "机器学习入门指南",
                    "file_type": "pdf",
                    "author": "李四"
                }
            }
        ],
        "total_references": 3
    },
    "message": "获取引用成功"
}
```

### 5. 上下文管理

#### 5.1 获取会话上下文

**接口**: `GET /chat/sessions/{session_id}/context`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "context": {
            "session_id": "sess_abc123def456",
            "total_context_length": 7500,
            "max_context_length": 8000,
            "context_chunks": [
                {
                    "context_type": "conversation",
                    "content": "用户: 什么是机器学习？\n助手: 机器学习是...",
                    "relevance_score": 1.0,
                    "weight": 1.0,
                    "context_order": 1
                },
                {
                    "context_type": "retrieval",
                    "content": "文档摘要: 机器学习算法分类...",
                    "relevance_score": 0.88,
                    "weight": 0.8,
                    "context_order": 2
                }
            ]
        }
    },
    "message": "获取上下文成功"
}
```

#### 5.2 更新上下文设置

**接口**: `PUT /chat/sessions/{session_id}/context`

**请求参数**:
```json
{
    "max_context_length": 10000,
    "include_document_metadata": true,
    "context_window_strategy": "sliding",
    "relevance_threshold": 0.75
}
```

## 📊 状态码和错误处理

### HTTP状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 正常请求处理 |
| 201 | 创建成功 | 资源创建 |
| 202 | 接受处理 | 异步任务提交 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未授权 | 认证失败 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 资源不存在 | 会话/消息不存在 |
| 409 | 冲突 | 资源状态冲突 |
| 422 | 参数错误 | 业务逻辑验证失败 |
| 429 | 请求过多 | 频率限制 |
| 500 | 服务器错误 | 内部错误 |
| 502 | 网关错误 | 上游服务错误 |
| 503 | 服务不可用 | 服务维护 |

### 错误代码

| 错误代码 | 描述 | 解决方案 |
|----------|------|----------|
| `VALIDATION_ERROR` | 参数验证失败 | 检查请求参数格式 |
| `AUTHENTICATION_FAILED` | 认证失败 | 检查认证令牌 |
| `PERMISSION_DENIED` | 权限不足 | 检查用户权限 |
| `SESSION_NOT_FOUND` | 会话不存在 | 检查会话ID |
| `MESSAGE_NOT_FOUND` | 消息不存在 | 检查消息ID |
| `RATE_LIMIT_EXCEEDED` | 频率限制 | 减少请求频率 |
| `LLM_SERVICE_ERROR` | LLM服务错误 | 稍后重试 |
| `RETRIEVAL_ERROR` | 检索服务错误 | 检查文档状态 |
| `CONTEXT_TOO_LONG` | 上下文过长 | 减少上下文长度 |
| `WEBSOCKET_ERROR` | WebSocket错误 | 重新建立连接 |

## 🔒 安全考虑

### 1. 认证和授权

- 所有API都需要有效的认证令牌
- WebSocket连接需要在查询参数中提供令牌
- 会话访问权限基于用户ID验证

### 2. 频率限制

| API类型 | 限制 | 时间窗口 |
|---------|------|----------|
| 消息发送 | 60次 | 每分钟 |
| 会话创建 | 10次 | 每小时 |
| 搜索请求 | 100次 | 每分钟 |
| WebSocket连接 | 5个 | 每用户 |

### 3. 数据保护

- 敏感信息自动过滤
- 消息内容可选择性加密存储
- 用户数据隔离访问

## 📈 性能指标

### 响应时间目标

| API类型 | 目标响应时间 |
|---------|-------------|
| 会话管理 | < 200ms |
| 消息发送 | < 500ms |
| 流式首包 | < 200ms |
| 文档搜索 | < 300ms |
| 消息历史 | < 100ms |

### 并发支持

- REST API: 1000+ QPS
- WebSocket: 1000+ 并发连接
- 流式响应: 100+ 并发流

这个API规范文档提供了Chat系统完整的接口定义，包括请求格式、响应格式、错误处理和性能要求，为前端开发和API集成提供了详细的参考。


