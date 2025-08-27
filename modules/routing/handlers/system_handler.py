"""
System Handler

系统命令处理器，处理系统配置、管理命令等。
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .base import BaseQueryHandler

logger = logging.getLogger(__name__)


class SystemHandler(BaseQueryHandler):
    """系统命令处理器"""
    
    def __init__(self, chat_service: Optional[Any] = None, routing_engine: Optional[Any] = None):
        super().__init__("system_handler")
        self.chat_service = chat_service
        self.routing_engine = routing_engine
        
        # 系统命令映射
        self.command_handlers = {
            # 对话管理
            "clear": self._handle_clear_history,
            "reset": self._handle_reset_conversation,
            "history": self._handle_show_history,
            
            # 帮助命令
            "help": self._handle_help,
            "status": self._handle_status,
            "stats": self._handle_statistics,
            
            # 配置命令
            "settings": self._handle_settings,
            "config": self._handle_config,
            
            # 系统控制
            "reload": self._handle_reload_config,
            "health": self._handle_health_check,
        }
        
    def set_dependencies(self, chat_service: Any = None, routing_engine: Any = None) -> None:
        """设置依赖服务"""
        if chat_service:
            self.chat_service = chat_service
        if routing_engine:
            self.routing_engine = routing_engine
        logger.info("SystemHandler 依赖服务已设置")
        
    def register_command(self, command: str, handler: Callable) -> None:
        """注册新的系统命令"""
        self.command_handlers[command] = handler
        logger.info(f"已注册系统命令: {command}")
        
    async def _handle_query(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理系统命令"""
        
        # 提取命令
        command = self._extract_command(query, route_metadata)
        
        if command in self.command_handlers:
            try:
                result = await self.command_handlers[command](query, context, route_metadata)
                return {
                    "content": result.get("message", "命令执行完成"),
                    "command": command,
                    "success": True,
                    "data": result.get("data", {}),
                    "response_type": "system_command"
                }
            except Exception as e:
                logger.error(f"系统命令执行失败 {command}: {e}")
                return {
                    "content": f"命令执行失败: {str(e)}",
                    "command": command,
                    "success": False,
                    "error": str(e),
                    "response_type": "system_error"
                }
        else:
            return await self._handle_unknown_command(query, context, command)
    
    def _extract_command(self, query: str, route_metadata: Dict[str, Any]) -> str:
        """提取系统命令"""
        query_lower = query.lower().strip()
        
        # 检查是否是斜杠命令
        if query_lower.startswith('/'):
            return query_lower[1:].split()[0]
        
        # 检查匹配的模式
        matched_patterns = route_metadata.get("matched_patterns", {}).get("matches", [])
        
        for pattern in matched_patterns:
            if pattern.startswith('/'):
                return pattern[1:]
            elif pattern in self.command_handlers:
                return pattern
        
        # 关键词匹配
        for cmd in self.command_handlers:
            if cmd in query_lower:
                return cmd
        
        return "unknown"
    
    async def _handle_clear_history(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """清除对话历史"""
        conversation_id = context.get("conversation_id")
        
        if not conversation_id:
            return {
                "message": "没有找到当前对话ID，无法清除历史记录。",
                "success": False
            }
        
        try:
            # 如果有聊天服务，调用删除对话方法
            if self.chat_service and hasattr(self.chat_service, 'delete_conversation'):
                result = await self.chat_service.delete_conversation(conversation_id)
                if result:
                    return {
                        "message": "✅ 对话历史已清除！",
                        "conversation_id": conversation_id,
                        "success": True
                    }
                else:
                    return {
                        "message": "清除对话历史失败，请稍后重试。",
                        "success": False
                    }
            else:
                return {
                    "message": "✅ 已标记清除对话历史（注：实际清除需要聊天服务支持）",
                    "success": True,
                    "note": "mock_operation"
                }
        except Exception as e:
            logger.error(f"清除对话历史失败: {e}")
            return {
                "message": f"清除对话历史时出现错误: {str(e)}",
                "success": False
            }
    
    async def _handle_reset_conversation(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """重置对话"""
        return {
            "message": "✅ 对话已重置！我们可以开始全新的对话了。",
            "action": "conversation_reset",
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    
    async def _handle_show_history(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """显示对话历史"""
        conversation_id = context.get("conversation_id")
        
        if not conversation_id:
            return {
                "message": "没有找到当前对话ID。",
                "success": False
            }
        
        try:
            if self.chat_service and hasattr(self.chat_service, 'get_conversation_messages'):
                messages = await self.chat_service.get_conversation_messages(conversation_id, limit=10)
                
                if not messages:
                    return {
                        "message": "当前对话还没有历史记录。",
                        "success": True
                    }
                
                history_text = "📋 **最近的对话历史:**\n\n"
                for msg in messages[-5:]:  # 显示最近5条
                    role = "👤 用户" if msg.role == "user" else "🤖 助手"
                    timestamp = msg.timestamp.strftime("%H:%M") if hasattr(msg, 'timestamp') else ""
                    history_text += f"{role} ({timestamp}): {msg.content[:100]}...\n\n"
                
                return {
                    "message": history_text,
                    "data": {"message_count": len(messages)},
                    "success": True
                }
            else:
                return {
                    "message": "📋 对话历史功能需要聊天服务支持。",
                    "success": False
                }
        except Exception as e:
            return {
                "message": f"获取对话历史时出现错误: {str(e)}",
                "success": False
            }
    
    async def _handle_help(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """显示帮助信息"""
        help_text = """
🔧 **系统命令帮助**

**对话管理:**
- `/clear` 或 "清除历史" - 清除当前对话历史
- `/reset` 或 "重置对话" - 重置对话状态
- `/history` 或 "显示历史" - 查看最近的对话记录

**系统信息:**
- `/help` 或 "帮助" - 显示此帮助信息
- `/status` 或 "状态" - 显示系统状态
- `/stats` 或 "统计" - 显示使用统计

**配置管理:**
- `/settings` 或 "设置" - 查看当前配置
- `/reload` 或 "重新加载" - 重新加载配置文件

**健康检查:**
- `/health` - 系统健康检查

💡 **提示:** 你可以直接说中文命令（如"帮助"、"清除历史"）或使用斜杠命令（如"/help"、"/clear"）。
        """
        
        return {
            "message": help_text.strip(),
            "available_commands": list(self.command_handlers.keys()),
            "success": True
        }
    
    async def _handle_status(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """显示系统状态"""
        status_info = {
            "timestamp": datetime.now().isoformat(),
            "system_handler": "运行中",
            "chat_service": "可用" if self.chat_service else "不可用",
            "routing_engine": "可用" if self.routing_engine else "不可用",
            "registered_commands": len(self.command_handlers)
        }
        
        if self.routing_engine:
            try:
                engine_stats = self.routing_engine.get_stats()
                status_info.update({
                    "total_routes": engine_stats.get("total_routes", 0),
                    "strategies": len(engine_stats.get("registered_strategies", [])),
                    "handlers": len(engine_stats.get("registered_handlers", []))
                })
            except Exception as e:
                status_info["routing_engine_error"] = str(e)
        
        status_text = "📊 **系统状态报告**\n\n"
        for key, value in status_info.items():
            if key != "timestamp":
                status_text += f"• {key}: {value}\n"
        
        return {
            "message": status_text,
            "data": status_info,
            "success": True
        }
    
    async def _handle_statistics(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """显示使用统计"""
        stats = {
            "system_handler_stats": {
                "total_processed": self.processing_count,
                "success_count": self.success_count,
                "error_count": self.error_count
            }
        }
        
        if self.routing_engine:
            engine_stats = self.routing_engine.get_stats()
            stats["routing_stats"] = {
                "total_routes": engine_stats.get("total_routes", 0),
                "average_confidence": engine_stats.get("average_confidence", 0.0),
                "strategy_usage": engine_stats.get("strategy_usage", {}),
                "handler_usage": engine_stats.get("handler_usage", {})
            }
        
        stats_text = "📈 **使用统计**\n\n"
        
        # 系统处理器统计
        sys_stats = stats["system_handler_stats"]
        stats_text += f"**系统命令处理:**\n"
        stats_text += f"• 总处理数: {sys_stats['total_processed']}\n"
        stats_text += f"• 成功数: {sys_stats['success_count']}\n"
        stats_text += f"• 错误数: {sys_stats['error_count']}\n\n"
        
        # 路由统计
        if "routing_stats" in stats:
            route_stats = stats["routing_stats"]
            stats_text += f"**路由引擎统计:**\n"
            stats_text += f"• 总路由数: {route_stats['total_routes']}\n"
            stats_text += f"• 平均置信度: {route_stats['average_confidence']:.3f}\n"
            
            if route_stats["handler_usage"]:
                stats_text += f"• 处理器使用分布:\n"
                for handler, count in route_stats["handler_usage"].items():
                    stats_text += f"  - {handler}: {count}\n"
        
        return {
            "message": stats_text,
            "data": stats,
            "success": True
        }
    
    async def _handle_settings(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """显示设置信息"""
        settings = {
            "user_id": context.get("user_id", "未知"),
            "conversation_id": context.get("conversation_id", "未知"),
            "topic_id": context.get("topic_id", "无"),
        }
        
        settings_text = "⚙️ **当前设置**\n\n"
        for key, value in settings.items():
            settings_text += f"• {key}: {value}\n"
        
        return {
            "message": settings_text,
            "data": settings,
            "success": True
        }
    
    async def _handle_config(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """显示配置信息"""
        return await self._handle_settings(query, context, route_metadata)
    
    async def _handle_reload_config(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """重新加载配置"""
        try:
            if self.routing_engine and hasattr(self.routing_engine, 'strategies'):
                # 尝试重新加载配置化关键词策略
                configurable_strategy = self.routing_engine.strategies.get("configurable_keyword")
                if configurable_strategy and hasattr(configurable_strategy, 'reload_config'):
                    await configurable_strategy.reload_config()
                    return {
                        "message": "✅ 配置已重新加载！",
                        "success": True
                    }
            
            return {
                "message": "⚠️ 配置重新加载功能需要路由引擎支持。",
                "success": False
            }
        except Exception as e:
            return {
                "message": f"重新加载配置时出现错误: {str(e)}",
                "success": False
            }
    
    async def _handle_health_check(self, query: str, context: Dict[str, Any], route_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """系统健康检查"""
        try:
            health_results = {}
            
            # 检查自身健康
            self_health = await self.health_check()
            health_results["system_handler"] = self_health
            
            # 检查路由引擎健康
            if self.routing_engine and hasattr(self.routing_engine, 'health_check'):
                engine_health = await self.routing_engine.health_check()
                health_results["routing_engine"] = engine_health
            
            # 检查聊天服务健康（如果可用）
            if self.chat_service and hasattr(self.chat_service, 'health_check'):
                chat_health = await self.chat_service.health_check()
                health_results["chat_service"] = chat_health
            
            # 生成健康报告
            healthy_components = 0
            total_components = len(health_results)
            
            health_text = "🏥 **系统健康检查报告**\n\n"
            
            for component, health in health_results.items():
                status = health.get("status", "unknown")
                if status == "healthy":
                    health_text += f"✅ {component}: 健康\n"
                    healthy_components += 1
                else:
                    health_text += f"❌ {component}: {status}\n"
            
            overall_status = "健康" if healthy_components == total_components else f"部分异常 ({healthy_components}/{total_components})"
            health_text += f"\n**总体状态:** {overall_status}"
            
            return {
                "message": health_text,
                "data": health_results,
                "overall_healthy": healthy_components == total_components,
                "success": True
            }
            
        except Exception as e:
            return {
                "message": f"健康检查时出现错误: {str(e)}",
                "success": False
            }
    
    async def _handle_unknown_command(self, query: str, context: Dict[str, Any], command: str) -> Dict[str, Any]:
        """处理未知命令"""
        return {
            "content": f"❓ 未知的系统命令: '{command}'\n\n请使用 '/help' 或说 '帮助' 查看可用命令列表。",
            "command": command,
            "success": False,
            "available_commands": list(self.command_handlers.keys()),
            "response_type": "unknown_command"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        base_health = await super().health_check()
        
        base_health.update({
            "available_commands": len(self.command_handlers),
            "chat_service_available": self.chat_service is not None,
            "routing_engine_available": self.routing_engine is not None
        })
        
        return base_health