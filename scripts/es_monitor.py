#!/usr/bin/env python3
"""
Elasticsearch监控和管理CLI工具

提供命令行界面来监控和管理Elasticsearch中的聊天数据
"""

import asyncio
import click
import json
from typing import Optional
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# 确保正确导入
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.services.elasticsearch_service import elasticsearch_chat_service

console = Console()


@click.group()
def cli():
    """Elasticsearch聊天数据监控和管理工具"""
    pass


@cli.command()
def health():
    """检查Elasticsearch集群健康状态"""
    async def check_health():
        try:
            # 初始化服务
            success = await elasticsearch_chat_service.initialize()
            
            if not success:
                console.print("❌ Elasticsearch初始化失败", style="red")
                return
            
            # 检查连接
            is_alive = await elasticsearch_chat_service.es_client.ping()
            
            if not is_alive:
                console.print("❌ Elasticsearch连接失败", style="red")
                return
            
            # 获取健康状态
            health_info = await elasticsearch_chat_service.es_client.cluster.health()
            info = await elasticsearch_chat_service.es_client.info()
            
            # 创建健康状态表格
            table = Table(title="Elasticsearch集群健康状态", box=box.ROUNDED)
            table.add_column("属性", style="cyan")
            table.add_column("值", style="white")
            
            # 状态颜色
            status_color = {
                "green": "green",
                "yellow": "yellow", 
                "red": "red"
            }.get(health_info.get("status", "unknown"), "white")
            
            table.add_row("集群名称", health_info.get("cluster_name", "unknown"))
            table.add_row("状态", Text(health_info.get("status", "unknown"), style=status_color))
            table.add_row("节点数量", str(health_info.get("number_of_nodes", 0)))
            table.add_row("数据节点数量", str(health_info.get("number_of_data_nodes", 0)))
            table.add_row("活跃主分片", str(health_info.get("active_primary_shards", 0)))
            table.add_row("活跃分片", str(health_info.get("active_shards", 0)))
            table.add_row("ES版本", info.get("version", {}).get("number", "unknown"))
            table.add_row("Lucene版本", info.get("version", {}).get("lucene_version", "unknown"))
            
            console.print(table)
            console.print("✅ Elasticsearch运行正常", style="green")
            
        except Exception as e:
            console.print(f"❌ 健康检查失败: {e}", style="red")
        finally:
            if elasticsearch_chat_service.es_client:
                await elasticsearch_chat_service.close()
    
    asyncio.run(check_health())


@cli.command()
def indices():
    """显示聊天索引信息"""
    async def show_indices():
        try:
            success = await elasticsearch_chat_service.initialize()
            
            if not success:
                console.print("❌ Elasticsearch初始化失败", style="red")
                return
            
            # 获取索引信息
            indices_info = await elasticsearch_chat_service.es_client.cat.indices(
                index="chat-*",
                format="json",
                h="index,docs.count,store.size,health,status"
            )
            
            if not indices_info:
                console.print("📭 没有找到聊天索引", style="yellow")
                return
            
            # 创建索引表格
            table = Table(title="聊天索引信息", box=box.ROUNDED)
            table.add_column("索引名称", style="cyan")
            table.add_column("文档数量", justify="right", style="white")
            table.add_column("存储大小", justify="right", style="white")
            table.add_column("健康状态", style="white")
            table.add_column("状态", style="white")
            
            total_docs = 0
            for idx in indices_info:
                docs_count = int(idx.get("docs.count", 0))
                total_docs += docs_count
                
                health_color = {
                    "green": "green",
                    "yellow": "yellow",
                    "red": "red"
                }.get(idx.get("health", "unknown"), "white")
                
                table.add_row(
                    idx.get("index", ""),
                    f"{docs_count:,}",
                    idx.get("store.size", "0b"),
                    Text(idx.get("health", "unknown"), style=health_color),
                    idx.get("status", "unknown")
                )
            
            console.print(table)
            console.print(f"📊 总计: {len(indices_info)} 个索引, {total_docs:,} 条消息", style="green")
            
        except Exception as e:
            console.print(f"❌ 获取索引信息失败: {e}", style="red")
        finally:
            if elasticsearch_chat_service.es_client:
                await elasticsearch_chat_service.close()
    
    asyncio.run(show_indices())


@cli.command()
@click.option("--days", default=7, help="统计天数 (默认7天)")
def stats(days: int):
    """显示聊天数据统计"""
    async def show_stats():
        try:
            success = await elasticsearch_chat_service.initialize()
            
            if not success:
                console.print("❌ Elasticsearch初始化失败", style="red")
                return
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 构建统计查询
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
                    }
                },
                "size": 0
            }
            
            # 执行查询
            response = await elasticsearch_chat_service.es_client.search(
                index="chat-*",
                body=query
            )
            
            total_messages = response["hits"]["total"]["value"]
            aggregations = response.get("aggregations", {})
            
            # 显示统计信息
            console.print(Panel(f"📊 近{days}天聊天数据统计", style="blue"))
            
            # 基本统计
            stats_table = Table(show_header=False, box=box.SIMPLE)
            stats_table.add_column("指标", style="cyan")
            stats_table.add_column("数值", style="white", justify="right")
            
            stats_table.add_row("总消息数", f"{total_messages:,}")
            stats_table.add_row("独立对话数", f"{aggregations.get('by_conversation', {}).get('value', 0):,}")
            stats_table.add_row("平均每天消息", f"{total_messages // days:,}")
            
            console.print(stats_table)
            
            # 按角色统计
            if aggregations.get("by_role", {}).get("buckets"):
                role_table = Table(title="按角色分布", box=box.ROUNDED)
                role_table.add_column("角色", style="cyan")
                role_table.add_column("消息数", justify="right", style="white")
                role_table.add_column("占比", justify="right", style="yellow")
                
                for bucket in aggregations["by_role"]["buckets"]:
                    count = bucket["doc_count"]
                    percentage = (count / total_messages * 100) if total_messages > 0 else 0
                    role_table.add_row(
                        bucket["key"],
                        f"{count:,}",
                        f"{percentage:.1f}%"
                    )
                
                console.print(role_table)
            
            # 日活跃度
            if aggregations.get("by_date", {}).get("buckets"):
                console.print("📈 每日活跃度:")
                for bucket in aggregations["by_date"]["buckets"][-7:]:  # 显示最近7天
                    date = bucket["key_as_string"][:10]
                    count = bucket["doc_count"]
                    bar = "█" * min(50, count // max(1, total_messages // 500))
                    console.print(f"  {date}: {count:>4} {bar}")
                    
        except Exception as e:
            console.print(f"❌ 获取统计信息失败: {e}", style="red")
        finally:
            if elasticsearch_chat_service.es_client:
                await elasticsearch_chat_service.close()
    
    asyncio.run(show_stats())


@cli.command()
@click.option("--limit", default=10, help="显示对话数量 (默认10)")
def conversations(limit: int):
    """显示最近的对话列表"""
    async def show_conversations():
        try:
            success = await elasticsearch_chat_service.initialize()
            
            if not success:
                console.print("❌ Elasticsearch初始化失败", style="red")
                return
            
            # 查询最近的对话
            query = {
                "query": {"match_all": {}},
                "aggs": {
                    "conversations": {
                        "terms": {
                            "field": "conversation_id.keyword",
                            "size": limit,
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
                                    "_source": ["user_message", "assistant_message"]
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
            
            if not conversations_agg:
                console.print("📭 没有找到对话记录", style="yellow")
                return
            
            # 显示对话列表
            table = Table(title=f"最近{limit}个对话", box=box.ROUNDED)
            table.add_column("对话ID", style="cyan", width=20)
            table.add_column("消息数", justify="right", style="white")
            table.add_column("最后活动", style="white")
            table.add_column("预览", style="dim", width=50)
            
            for conv in conversations_agg:
                sample = conv["sample_message"]["hits"]["hits"][0]["_source"]
                latest_time = datetime.fromisoformat(
                    conv["latest_message"]["value_as_string"].replace('Z', '+00:00')
                )
                
                # 截取预览
                user_preview = sample["user_message"][:40] + "..." if len(sample["user_message"]) > 40 else sample["user_message"]
                
                table.add_row(
                    conv["key"][:20] + "...",
                    str(conv["doc_count"]),
                    latest_time.strftime("%m-%d %H:%M"),
                    user_preview
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"❌ 获取对话列表失败: {e}", style="red")
        finally:
            if elasticsearch_chat_service.es_client:
                await elasticsearch_chat_service.close()
    
    asyncio.run(show_conversations())


@cli.command()
@click.argument("query")
@click.option("--limit", default=10, help="搜索结果数量 (默认10)")
def search(query: str, limit: int):
    """搜索聊天内容"""
    async def search_content():
        try:
            success = await elasticsearch_chat_service.initialize()
            
            if not success:
                console.print("❌ Elasticsearch初始化失败", style="red")
                return
            
            # 执行搜索
            results = await elasticsearch_chat_service.search_chat_content(
                query=query, limit=limit
            )
            
            if not results:
                console.print(f"🔍 没有找到包含 '{query}' 的内容", style="yellow")
                return
            
            console.print(f"🔍 搜索结果: '{query}' (找到{len(results)}条)")
            
            for i, result in enumerate(results, 1):
                console.print(f"\n[{i}] 对话ID: {result.conversation_id}")
                console.print(f"相关度: {result.score:.3f}")
                if result.timestamp:
                    console.print(f"时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 显示内容预览
                content_preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                console.print(Panel(content_preview, title="内容", border_style="dim"))
                
        except Exception as e:
            console.print(f"❌ 搜索失败: {e}", style="red")
        finally:
            if elasticsearch_chat_service.es_client:
                await elasticsearch_chat_service.close()
    
    asyncio.run(search_content())


@cli.command()
@click.argument("conversation_id")
@click.option("--limit", default=20, help="消息数量 (默认20)")
def show(conversation_id: str, limit: int):
    """显示指定对话的详细内容"""
    async def show_conversation():
        try:
            success = await elasticsearch_chat_service.initialize()
            
            if not success:
                console.print("❌ Elasticsearch初始化失败", style="red")
                return
            
            # 获取对话消息
            messages = await elasticsearch_chat_service.get_conversation_messages(
                conversation_id, limit=limit
            )
            
            if not messages:
                console.print(f"📭 没有找到对话 {conversation_id}", style="yellow")
                return
            
            console.print(f"💬 对话详情: {conversation_id} ({len(messages)}条消息)")
            
            for i, msg in enumerate(messages):
                # 角色颜色
                role_color = "blue" if msg.role == "user" else "green"
                role_text = Text(f"{msg.role.upper()}", style=role_color)
                
                # 时间戳
                timestamp = msg.timestamp.strftime("%H:%M:%S") if msg.timestamp else "未知时间"
                
                # 消息内容
                content_panel = Panel(
                    msg.content,
                    title=f"{role_text} - {timestamp}",
                    border_style=role_color,
                    width=80
                )
                console.print(content_panel)
                
        except Exception as e:
            console.print(f"❌ 显示对话失败: {e}", style="red")
        finally:
            if elasticsearch_chat_service.es_client:
                await elasticsearch_chat_service.close()
    
    asyncio.run(show_conversation())


if __name__ == "__main__":
    cli()