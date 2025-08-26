"""
Chat-related Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import Field, validator
from enum import Enum

from .base import BaseSchema
from .enums import SearchType


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"              # 用户消息
    ASSISTANT = "assistant"    # AI助手消息
    SYSTEM = "system"          # 系统消息


class SSEEventType(str, Enum):
    """SSE事件类型枚举"""
    START = "start"            # 开始处理
    PROGRESS = "progress"      # 进度更新
    CONTEXT = "context"        # 检索上下文
    DELTA = "delta"           # AI流式输出片段
    COMPLETE = "complete"      # 处理完成
    ERROR = "error"           # 错误事件


class RetrievedContext(BaseSchema):
    """检索到的上下文信息"""
    
    content: str = Field(description="上下文内容")
    document_id: str = Field(description="文档ID")
    chunk_index: int = Field(description="chunk索引")
    similarity_score: float = Field(description="相似度分数")
    document_title: Optional[str] = Field(default=None, description="文档标题")
    file_id: Optional[str] = Field(default=None, description="文件ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外元数据")


class ChatMessage(BaseSchema):
    """聊天消息"""
    
    id: str = Field(description="消息ID")
    conversation_id: str = Field(description="对话ID")
    role: MessageRole = Field(description="消息角色")
    content: str = Field(description="消息内容")
    timestamp: datetime = Field(description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="消息元数据")
    token_count: Optional[int] = Field(default=None, description="token数量")


class ChatRequest(BaseSchema):
    """聊天请求"""
    
    message: str = Field(description="用户消息内容", min_length=1, max_length=8000)
    topic_id: Optional[int] = Field(default=None, description="主题ID")
    conversation_id: Optional[str] = Field(default=None, description="对话ID，不提供则创建新对话")
    
    # RAG相关配置
    search_type: SearchType = Field(default=SearchType.SEMANTIC, description="搜索类型")
    max_results: int = Field(default=5, ge=1, le=20, description="最大检索结果数")
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="相似度阈值")
    include_context: bool = Field(default=True, description="是否包含检索上下文")
    
    # AI生成配置
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="最大token数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    
    # 对话历史配置
    context_window: int = Field(default=5, ge=0, le=20, description="对话历史窗口大小")


class AIMetadata(BaseSchema):
    """AI生成元数据"""
    
    model: str = Field(description="使用的AI模型")
    tokens_used: int = Field(description="使用的token数量")
    generation_time_ms: int = Field(description="生成耗时(毫秒)")
    search_time_ms: int = Field(description="搜索耗时(毫秒)")
    temperature: float = Field(description="生成温度")
    max_tokens: int = Field(description="最大token数")


class ChatResponse(BaseSchema):
    """聊天响应"""
    
    message_id: str = Field(description="消息ID")
    conversation_id: str = Field(description="对话ID")
    content: str = Field(description="AI回复内容")
    retrieved_contexts: List[RetrievedContext] = Field(default_factory=list, description="检索到的上下文")
    ai_metadata: AIMetadata = Field(description="AI生成元数据")
    timestamp: datetime = Field(description="响应时间戳")


# ==================== SSE事件相关schemas ====================

class SSEStartEvent(BaseSchema):
    """SSE开始事件"""
    
    message_id: str = Field(description="消息ID")
    conversation_id: str = Field(description="对话ID")


class SSEProgressEvent(BaseSchema):
    """SSE进度事件"""
    
    stage: str = Field(description="处理阶段：retrieving|generating|saving")
    message: str = Field(description="进度描述")
    progress: Optional[float] = Field(default=None, description="进度百分比(0-1)")


class SSEContextEvent(BaseSchema):
    """SSE上下文事件"""
    
    contexts: List[RetrievedContext] = Field(description="检索到的上下文")
    search_time_ms: int = Field(description="搜索耗时")
    total_results: int = Field(description="检索结果总数")


class SSEDeltaEvent(BaseSchema):
    """SSE增量内容事件"""
    
    content: str = Field(description="增量内容")
    message_id: str = Field(description="消息ID")
    token_count: Optional[int] = Field(default=None, description="当前token数")


class SSECompleteEvent(BaseSchema):
    """SSE完成事件"""
    
    conversation_id: str = Field(description="对话ID")
    message_id: str = Field(description="消息ID")
    total_tokens: int = Field(description="总token数")
    generation_time_ms: int = Field(description="总生成时间")
    search_time_ms: int = Field(description="搜索时间")


class SSEErrorEvent(BaseSchema):
    """SSE错误事件"""
    
    error: str = Field(description="错误信息")
    error_type: str = Field(description="错误类型")
    stage: Optional[str] = Field(default=None, description="出错阶段")


# ==================== 对话管理相关schemas ====================

class ConversationSummary(BaseSchema):
    """对话摘要信息"""
    
    conversation_id: str = Field(description="对话ID")
    topic_id: Optional[int] = Field(default=None, description="主题ID")
    title: str = Field(description="对话标题")
    last_message_time: datetime = Field(description="最后消息时间")
    message_count: int = Field(description="消息数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class ConversationListRequest(BaseSchema):
    """对话列表请求"""
    
    topic_id: Optional[int] = Field(default=None, description="主题ID过滤")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")
    offset: int = Field(default=0, ge=0, description="偏移量")
    order_by: str = Field(default="last_message_time", description="排序字段")
    order_direction: str = Field(default="desc", description="排序方向：asc|desc")
    
    @validator("order_by")
    def validate_order_by(cls, v):
        allowed_fields = ["created_at", "updated_at", "last_message_time", "message_count"]
        if v not in allowed_fields:
            raise ValueError(f"order_by must be one of {allowed_fields}")
        return v
    
    @validator("order_direction")
    def validate_order_direction(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("order_direction must be 'asc' or 'desc'")
        return v


class ConversationListResponse(BaseSchema):
    """对话列表响应"""
    
    conversations: List[ConversationSummary] = Field(description="对话列表")
    total: int = Field(description="总数量")
    has_more: bool = Field(description="是否有更多数据")


class MessageHistoryRequest(BaseSchema):
    """消息历史请求"""
    
    conversation_id: str = Field(description="对话ID")
    limit: int = Field(default=50, ge=1, le=200, description="消息数量")
    before: Optional[str] = Field(default=None, description="在此消息ID之前")
    include_context: bool = Field(default=False, description="是否包含检索上下文")


class MessageHistoryResponse(BaseSchema):
    """消息历史响应"""
    
    messages: List[ChatMessage] = Field(description="消息列表")
    conversation_id: str = Field(description="对话ID")
    has_more: bool = Field(description="是否有更多历史消息")


class ChatSearchRequest(BaseSchema):
    """聊天搜索请求"""
    
    query: str = Field(description="搜索关键词", min_length=1, max_length=200)
    topic_id: Optional[int] = Field(default=None, description="主题ID过滤")
    conversation_id: Optional[str] = Field(default=None, description="对话ID过滤")
    role: Optional[MessageRole] = Field(default=None, description="消息角色过滤")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    limit: int = Field(default=20, ge=1, le=100, description="结果数量")
    highlight: bool = Field(default=True, description="是否高亮搜索关键词")


class ChatSearchResult(BaseSchema):
    """聊天搜索结果"""
    
    message: ChatMessage = Field(description="匹配的消息")
    highlights: List[str] = Field(default_factory=list, description="高亮片段")
    score: float = Field(description="匹配分数")


class ChatSearchResponse(BaseSchema):
    """聊天搜索响应"""
    
    results: List[ChatSearchResult] = Field(description="搜索结果")
    total: int = Field(description="总匹配数")
    query_time_ms: int = Field(description="查询耗时")


class ChatStatisticsResponse(BaseSchema):
    """聊天统计响应"""
    
    total_conversations: int = Field(description="总对话数")
    total_messages: int = Field(description="总消息数")
    avg_messages_per_conversation: float = Field(description="平均每对话消息数")
    total_tokens_used: int = Field(description="总token使用量")
    top_topics: List[Dict[str, Any]] = Field(description="热门主题")
    daily_stats: List[Dict[str, Any]] = Field(description="每日统计")


# ==================== 导出 ====================

__all__ = [
    # Enums
    "MessageRole", 
    "SSEEventType",
    
    # Basic schemas
    "RetrievedContext",
    "ChatMessage",
    "ChatRequest", 
    "ChatResponse",
    "AIMetadata",
    
    # SSE event schemas
    "SSEStartEvent",
    "SSEProgressEvent", 
    "SSEContextEvent",
    "SSEDeltaEvent",
    "SSECompleteEvent",
    "SSEErrorEvent",
    
    # Conversation management
    "ConversationSummary",
    "ConversationListRequest",
    "ConversationListResponse",
    "MessageHistoryRequest",
    "MessageHistoryResponse",
    
    # Search functionality  
    "ChatSearchRequest",
    "ChatSearchResult",
    "ChatSearchResponse",
    
    # Statistics
    "ChatStatisticsResponse",
]
