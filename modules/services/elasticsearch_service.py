"""
Elasticsearch Chat Service

提供基于Elasticsearch的聊天记录存储和搜索功能。
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

try:
    from elasticsearch import AsyncElasticsearch
except ImportError:
    AsyncElasticsearch = None

from config.settings import get_config
from logging_system import get_logger
from modules.schemas.chat import (
    ChatMessage, 
    RetrievedContext, 
    ConversationSummary,
    ChatSearchResult,
    MessageRole
)

logger = get_logger(__name__)


class ElasticsearchChatService:
    """基于Elasticsearch的聊天服务"""
    
    def __init__(self):
        self.config = get_config()
        self.es_config = self.config.elasticsearch
        self.es_client: Optional[AsyncElasticsearch] = None
        
        # 索引命名模式 (使用配置中的值)
        self.chat_index_prefix = self.es_config.chat_index_prefix
        self.log_index_prefix = self.es_config.log_index_prefix
        
        # 索引模板
        self.chat_index_template = {
            "index_patterns": [f"{self.chat_index_prefix}-*"],
            "template": {
                "settings": {
                    "number_of_shards": self.es_config.default_shards,
                    "number_of_replicas": self.es_config.default_replicas,
                    "analysis": {
                        "analyzer": {
                            "chat_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "conversation_id": {"type": "keyword"},
                        "message_id": {"type": "keyword"},
                        "topic_id": {"type": "integer"},
                        "user_message": {
                            "type": "text",
                            "analyzer": "chat_analyzer",
                            "fields": {"keyword": {"type": "keyword"}}
                        },
                        "assistant_message": {
                            "type": "text", 
                            "analyzer": "chat_analyzer",
                            "fields": {"keyword": {"type": "keyword"}}
                        },
                        "retrieved_contexts": {"type": "nested"},
                        "ai_metadata": {"type": "object"},
                        "timestamp": {"type": "date"},
                        "generation_time_ms": {"type": "integer"},
                        "search_time_ms": {"type": "integer"},
                        "tokens_used": {"type": "integer"}
                    }
                }
            }
        }
    
    async def initialize(self) -> bool:
        """初始化Elasticsearch连接和索引"""
        if AsyncElasticsearch is None:
            logger.warning("Elasticsearch client not available, using mock implementation")
            return False
            
        try:
            # 使用配置创建连接
            connection_config = self.es_config.connection_config
            self.es_client = AsyncElasticsearch([connection_config])
            
            # 测试连接
            if await self.es_client.ping():
                logger.info(f"✅ Elasticsearch连接成功: {self.es_config.connection_url}")
                await self._create_index_templates()
                return True
            else:
                logger.error("❌ Elasticsearch连接失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ Elasticsearch初始化失败: {e}")
            return False
    
    async def _create_index_templates(self):
        """创建索引模板"""
        try:
            # 创建聊天消息索引模板
            await self.es_client.indices.put_index_template(
                name=f"{self.chat_index_prefix}-template",
                body=self.chat_index_template
            )
            logger.info("✅ 创建聊天索引模板成功")
            
        except Exception as e:
            logger.error(f"❌ 创建索引模板失败: {e}")
    
    def _get_chat_index_name(self, date: Optional[datetime] = None) -> str:
        """获取聊天索引名称（按月分割）"""
        if date is None:
            date = datetime.now(timezone.utc)
        return f"{self.chat_index_prefix}-{date.strftime('%Y-%m')}"
    
    async def save_conversation(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        topic_id: Optional[int] = None,
        retrieved_contexts: Optional[List[RetrievedContext]] = None,
        ai_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存对话记录到Elasticsearch"""
        
        if not self.es_client:
            logger.warning("Elasticsearch未初始化，跳过保存")
            return False
            
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)
            index_name = self._get_chat_index_name(timestamp)
            
            # 准备文档数据
            doc = {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "topic_id": topic_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "timestamp": timestamp.isoformat(),
                "ai_metadata": ai_metadata or {},
                "generation_time_ms": ai_metadata.get("generation_time_ms", 0) if ai_metadata else 0,
                "search_time_ms": ai_metadata.get("search_time_ms", 0) if ai_metadata else 0,
                "tokens_used": ai_metadata.get("tokens_used", 0) if ai_metadata else 0,
            }
            
            # 处理检索上下文
            if retrieved_contexts:
                doc["retrieved_contexts"] = [
                    {
                        "content": ctx.content,
                        "document_id": ctx.document_id,
                        "chunk_index": ctx.chunk_index,
                        "similarity_score": ctx.similarity_score,
                        "document_title": ctx.document_title,
                        "file_id": ctx.file_id,
                        "metadata": ctx.metadata
                    }
                    for ctx in retrieved_contexts
                ]
            else:
                doc["retrieved_contexts"] = []
            
            # 保存到Elasticsearch
            await self.es_client.index(
                index=index_name,
                id=message_id,
                body=doc
            )
            
            logger.info(f"✅ 对话记录保存成功: {conversation_id}/{message_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存对话记录失败: {e}")
            return False
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[ChatMessage]:
        """获取对话消息历史"""
        
        if not self.es_client:
            logger.warning("Elasticsearch未初始化，返回空列表")
            return []
            
        try:
            # 构建查询
            query = {
                "bool": {
                    "must": [
                        {"term": {"conversation_id": conversation_id}}
                    ]
                }
            }
            
            if before:
                query["bool"]["must"].append({
                    "range": {"timestamp": {"lt": before}}
                })
            
            # 搜索
            result = await self.es_client.search(
                index=f"{self.chat_index_prefix}-*",
                body={
                    "query": query,
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": limit * 2  # 每个对话包含用户和助手消息
                }
            )
            
            # 转换结果
            messages = []
            for hit in result["hits"]["hits"]:
                source = hit["_source"]
                
                # 添加用户消息
                if source.get("user_message"):
                    messages.append(ChatMessage(
                        id=f"{source['message_id']}-user",
                        conversation_id=source["conversation_id"],
                        role=MessageRole.USER,
                        content=source["user_message"],
                        timestamp=datetime.fromisoformat(source["timestamp"].replace('Z', '+00:00')),
                        metadata={}
                    ))
                
                # 添加助手消息
                if source.get("assistant_message"):
                    messages.append(ChatMessage(
                        id=f"{source['message_id']}-assistant",
                        conversation_id=source["conversation_id"],
                        role=MessageRole.ASSISTANT,
                        content=source["assistant_message"],
                        timestamp=datetime.fromisoformat(source["timestamp"].replace('Z', '+00:00')),
                        metadata=source.get("ai_metadata", {}),
                        token_count=source.get("tokens_used")
                    ))
            
            # 按时间排序
            messages.sort(key=lambda x: x.timestamp)
            return messages[:limit]
            
        except Exception as e:
            logger.error(f"❌ 获取对话消息失败: {e}")
            return []
    
    async def search_chat_content(
        self,
        query: str,
        topic_id: Optional[int] = None,
        limit: int = 20
    ) -> List[ChatSearchResult]:
        """搜索聊天内容"""
        
        if not self.es_client:
            logger.warning("Elasticsearch未初始化，返回空结果")
            return []
            
        try:
            # 构建查询
            must_queries = [
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["user_message^2", "assistant_message"],
                        "type": "best_fields"
                    }
                }
            ]
            
            if topic_id:
                must_queries.append({"term": {"topic_id": topic_id}})
            
            search_body = {
                "query": {"bool": {"must": must_queries}},
                "highlight": {
                    "fields": {
                        "user_message": {},
                        "assistant_message": {}
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": limit
            }
            
            result = await self.es_client.search(
                index=f"{self.chat_index_prefix}-*",
                body=search_body
            )
            
            # 转换结果
            search_results = []
            for hit in result["hits"]["hits"]:
                source = hit["_source"]
                highlights = hit.get("highlight", {})
                
                # 创建聊天消息对象
                message = ChatMessage(
                    id=source["message_id"],
                    conversation_id=source["conversation_id"],
                    role=MessageRole.USER,  # 可能需要根据实际情况调整
                    content=source.get("user_message", ""),
                    timestamp=datetime.fromisoformat(source["timestamp"].replace('Z', '+00:00')),
                    metadata=source.get("ai_metadata", {})
                )
                
                # 提取高亮片段
                highlight_fragments = []
                for field, fragments in highlights.items():
                    highlight_fragments.extend(fragments)
                
                search_results.append(ChatSearchResult(
                    message=message,
                    highlights=highlight_fragments,
                    score=hit["_score"]
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"❌ 搜索聊天内容失败: {e}")
            return []
    
    async def get_conversation_statistics(
        self,
        topic_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取聊天统计信息"""
        
        if not self.es_client:
            logger.warning("Elasticsearch未初始化，返回空统计")
            return {}
            
        try:
            # 构建查询
            query = {"match_all": {}}
            if topic_id:
                query = {"term": {"topic_id": topic_id}}
            
            # 聚合查询
            agg_body = {
                "query": query,
                "size": 0,
                "aggs": {
                    "total_conversations": {
                        "cardinality": {"field": "conversation_id"}
                    },
                    "total_tokens": {
                        "sum": {"field": "tokens_used"}
                    },
                    "avg_generation_time": {
                        "avg": {"field": "generation_time_ms"}
                    },
                    "daily_stats": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "day",
                            "order": {"_key": "desc"}
                        },
                        "aggs": {
                            "conversations": {
                                "cardinality": {"field": "conversation_id"}
                            },
                            "tokens": {
                                "sum": {"field": "tokens_used"}
                            }
                        }
                    }
                }
            }
            
            result = await self.es_client.search(
                index=f"{self.chat_index_prefix}-*",
                body=agg_body
            )
            
            aggs = result["aggregations"]
            return {
                "total_conversations": aggs["total_conversations"]["value"],
                "total_messages": result["hits"]["total"]["value"],
                "total_tokens_used": int(aggs["total_tokens"]["value"] or 0),
                "avg_generation_time_ms": aggs["avg_generation_time"]["value"],
                "daily_stats": [
                    {
                        "date": bucket["key_as_string"],
                        "conversations": bucket["conversations"]["value"],
                        "tokens": bucket["tokens"]["value"]
                    }
                    for bucket in aggs["daily_stats"]["buckets"][:7]  # 最近7天
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}
    
    async def close(self):
        """关闭Elasticsearch连接"""
        if self.es_client:
            await self.es_client.close()
            logger.info("✅ Elasticsearch连接已关闭")


# 全局实例
elasticsearch_chat_service = ElasticsearchChatService()
