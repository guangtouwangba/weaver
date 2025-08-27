"""
Elasticsearch Management API

提供Elasticsearch集群和聊天数据的管理接口
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime, timedelta

from modules.services.elasticsearch_service import elasticsearch_chat_service
from modules.schemas import APIResponse
from logging_system import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/elasticsearch", tags=["Elasticsearch Management"])


@router.get("/health", summary="Elasticsearch健康检查")
async def elasticsearch_health() -> APIResponse:
    """
    检查Elasticsearch集群健康状态
    
    Returns:
        APIResponse: 包含集群健康信息
    """
    try:
        if not elasticsearch_chat_service.es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch未初始化")
        
        # 检查连接
        is_alive = await elasticsearch_chat_service.es_client.ping()
        
        if not is_alive:
            raise HTTPException(status_code=503, detail="Elasticsearch连接失败")
        
        # 获取集群健康状态
        health = await elasticsearch_chat_service.es_client.cluster.health()
        
        # 获取集群信息
        info = await elasticsearch_chat_service.es_client.info()
        
        return APIResponse(
            success=True,
            message="Elasticsearch集群运行正常",
            data={
                "cluster_name": health.get("cluster_name"),
                "status": health.get("status"),
                "number_of_nodes": health.get("number_of_nodes"),
                "number_of_data_nodes": health.get("number_of_data_nodes"),
                "active_primary_shards": health.get("active_primary_shards"),
                "active_shards": health.get("active_shards"),
                "version": info.get("version", {}).get("number"),
                "lucene_version": info.get("version", {}).get("lucene_version")
            }
        )
        
    except Exception as e:
        logger.error(f"Elasticsearch健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/indices", summary="获取聊天索引信息")
async def get_chat_indices() -> APIResponse:
    """
    获取所有聊天相关索引的信息
    
    Returns:
        APIResponse: 包含索引列表和统计信息
    """
    try:
        if not elasticsearch_chat_service.es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch未初始化")
        
        # 获取聊天索引
        indices_info = await elasticsearch_chat_service.es_client.cat.indices(
            index="chat-*",
            format="json",
            h="index,docs.count,store.size,health,status"
        )
        
        return APIResponse(
            success=True,
            message="获取索引信息成功",
            data={
                "indices": indices_info,
                "total_indices": len(indices_info),
                "total_documents": sum(int(idx.get("docs.count", 0)) for idx in indices_info)
            }
        )
        
    except Exception as e:
        logger.error(f"获取索引信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取索引信息失败: {str(e)}")


@router.get("/stats", summary="获取聊天数据统计")
async def get_chat_statistics(
    days: int = Query(default=7, description="统计天数", ge=1, le=30)
) -> APIResponse:
    """
    获取聊天数据的详细统计信息
    
    Args:
        days: 统计的天数范围
        
    Returns:
        APIResponse: 包含聊天统计数据
    """
    try:
        if not elasticsearch_chat_service.es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch未初始化")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询
        query = {
            "query": {
                "range": {
                    "timestamp": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            },
            "aggs": {
                "by_role": {
                    "terms": {
                        "field": "role.keyword",
                        "size": 10
                    }
                },
                "by_date": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": "1d"
                    }
                },
                "by_conversation": {
                    "cardinality": {
                        "field": "conversation_id.keyword"
                    }
                },
                "message_length": {
                    "avg": {
                        "script": {
                            "source": "doc['user_message.keyword'].value.length() + doc['assistant_message.keyword'].value.length()"
                        }
                    }
                }
            },
            "size": 0
        }
        
        # 执行查询
        response = await elasticsearch_chat_service.es_client.search(
            index="chat-*",
            body=query
        )
        
        aggregations = response.get("aggregations", {})
        
        return APIResponse(
            success=True,
            message=f"获取{days}天聊天统计成功",
            data={
                "total_messages": response["hits"]["total"]["value"],
                "unique_conversations": aggregations.get("by_conversation", {}).get("value", 0),
                "messages_by_role": [
                    {"role": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in aggregations.get("by_role", {}).get("buckets", [])
                ],
                "daily_activity": [
                    {
                        "date": bucket["key_as_string"][:10],
                        "count": bucket["doc_count"]
                    }
                    for bucket in aggregations.get("by_date", {}).get("buckets", [])
                ],
                "average_message_length": round(aggregations.get("message_length", {}).get("value", 0), 2),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取聊天统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取聊天统计失败: {str(e)}")


@router.get("/conversations", summary="获取对话列表")
async def get_conversations(
    page: int = Query(default=1, description="页码", ge=1),
    size: int = Query(default=10, description="每页数量", ge=1, le=100)
) -> APIResponse:
    """
    获取分页的对话列表
    
    Args:
        page: 页码
        size: 每页数量
        
    Returns:
        APIResponse: 包含对话列表
    """
    try:
        if not elasticsearch_chat_service.es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch未初始化")
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 查询最近的对话
        query = {
            "query": {"match_all": {}},
            "aggs": {
                "conversations": {
                    "terms": {
                        "field": "conversation_id.keyword",
                        "size": 1000,
                        "order": {"latest_message": "desc"}
                    },
                    "aggs": {
                        "latest_message": {
                            "max": {
                                "field": "timestamp"
                            }
                        },
                        "message_count": {
                            "value_count": {
                                "field": "conversation_id.keyword"
                            }
                        },
                        "sample_message": {
                            "top_hits": {
                                "size": 1,
                                "sort": [{"timestamp": {"order": "desc"}}],
                                "_source": ["user_message", "assistant_message", "timestamp"]
                            }
                        }
                    }
                }
            },
            "size": 0
        }
        
        response = await elasticsearch_chat_service.es_client.search(
            index="chat-*",
            body=query
        )
        
        conversations_agg = response["aggregations"]["conversations"]["buckets"]
        
        # 分页处理
        total_conversations = len(conversations_agg)
        paginated_conversations = conversations_agg[offset:offset + size]
        
        # 格式化结果
        conversations = []
        for conv in paginated_conversations:
            sample = conv["sample_message"]["hits"]["hits"][0]["_source"]
            conversations.append({
                "conversation_id": conv["key"],
                "message_count": conv["doc_count"],
                "latest_timestamp": conv["latest_message"]["value_as_string"],
                "preview": {
                    "user_message": sample["user_message"][:100] + "..." if len(sample["user_message"]) > 100 else sample["user_message"],
                    "assistant_message": sample["assistant_message"][:100] + "..." if len(sample["assistant_message"]) > 100 else sample["assistant_message"]
                }
            })
        
        return APIResponse(
            success=True,
            message="获取对话列表成功",
            data={
                "conversations": conversations,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total_conversations,
                    "pages": (total_conversations + size - 1) // size
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@router.get("/conversations/{conversation_id}/messages", summary="获取对话详情")
async def get_conversation_detail(
    conversation_id: str = Path(description="对话ID"),
    limit: int = Query(default=50, description="消息数量限制", ge=1, le=200)
) -> APIResponse:
    """
    获取指定对话的详细消息
    
    Args:
        conversation_id: 对话ID
        limit: 返回消息数量限制
        
    Returns:
        APIResponse: 包含对话详细消息
    """
    try:
        messages = await elasticsearch_chat_service.get_conversation_messages(
            conversation_id, limit=limit
        )
        
        return APIResponse(
            success=True,
            message="获取对话详情成功",
            data={
                "conversation_id": conversation_id,
                "message_count": len(messages),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in messages
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"获取对话详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话详情失败: {str(e)}")


@router.post("/search", summary="搜索聊天内容")
async def search_chat_content(
    query: str = Query(description="搜索关键词"),
    limit: int = Query(default=20, description="结果数量限制", ge=1, le=100)
) -> APIResponse:
    """
    在聊天记录中搜索内容
    
    Args:
        query: 搜索关键词
        limit: 结果数量限制
        
    Returns:
        APIResponse: 包含搜索结果
    """
    try:
        results = await elasticsearch_chat_service.search_chat_content(
            query=query, limit=limit
        )
        
        return APIResponse(
            success=True,
            message=f"搜索到{len(results)}条结果",
            data={
                "query": query,
                "total_results": len(results),
                "results": [
                    {
                        "conversation_id": result.conversation_id,
                        "content": result.content,
                        "score": result.score,
                        "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                        "highlight": result.highlight
                    }
                    for result in results
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"搜索聊天内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.delete("/conversations/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: str = Path(description="对话ID")
) -> APIResponse:
    """
    删除指定的对话记录
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        APIResponse: 删除结果
    """
    try:
        if not elasticsearch_chat_service.es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch未初始化")
        
        # 删除查询
        delete_query = {
            "query": {
                "term": {
                    "conversation_id.keyword": conversation_id
                }
            }
        }
        
        # 执行删除
        result = await elasticsearch_chat_service.es_client.delete_by_query(
            index="chat-*",
            body=delete_query,
            refresh=True
        )
        
        deleted_count = result.get("deleted", 0)
        
        if deleted_count > 0:
            return APIResponse(
                success=True,
                message=f"成功删除对话 {conversation_id}",
                data={
                    "conversation_id": conversation_id,
                    "deleted_messages": deleted_count
                }
            )
        else:
            raise HTTPException(status_code=404, detail="对话不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")