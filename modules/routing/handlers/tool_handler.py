"""
Tool Handler

工具调用处理器，处理计算、翻译、天气查询等工具请求。
"""

import re
import logging
from typing import Dict, Any, Optional, Callable

from .base import BaseQueryHandler

logger = logging.getLogger(__name__)


class ToolHandler(BaseQueryHandler):
    """工具调用处理器"""
    
    def __init__(self):
        super().__init__("tool_handler")
        
        # 工具处理器映射
        self.tool_handlers = {
            "calc": self._handle_calculator,
            "calculate": self._handle_calculator,
            "weather": self._handle_weather,
            "translate": self._handle_translation,
            "remind": self._handle_reminder,
            "timer": self._handle_timer,
        }
        
        # 工具识别模式
        self.tool_patterns = {
            "calculator": [
                r"计算\s*(.+)",
                r"算一下\s*(.+)",
                r"\d+\s*[+\-*/]\s*\d+",
                r"^/calc\s*(.+)",
                r"帮我算\s*(.+)"
            ],
            "weather": [
                r"天气\s*(.+)",
                r"今天天气",
                r"明天天气",
                r"^/weather\s*(.+)",
                r"查询天气\s*(.+)"
            ],
            "translation": [
                r"翻译\s*(.+)",
                r"^/translate\s*(.+)",
                r"帮我翻译\s*(.+)",
                r"把\s*(.+)\s*翻译"
            ],
            "reminder": [
                r"提醒\s*(.+)",
                r"^/remind\s*(.+)",
                r"设置提醒\s*(.+)",
                r"记得\s*(.+)"
            ]
        }
        
    def register_tool(self, tool_name: str, handler: Callable, patterns: list = None) -> None:
        """注册新工具"""
        self.tool_handlers[tool_name] = handler
        if patterns:
            self.tool_patterns[tool_name] = patterns
        logger.info(f"已注册工具: {tool_name}")
        
    async def _handle_query(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理工具调用"""
        
        # 识别工具类型和参数
        tool_info = self._identify_tool(query, route_metadata)
        
        if not tool_info:
            return await self._handle_unknown_tool(query, context)
        
        tool_type = tool_info["tool_type"]
        parameters = tool_info["parameters"]
        
        if tool_type in self.tool_handlers:
            try:
                result = await self.tool_handlers[tool_type](query, parameters, context)
                return {
                    "content": result.get("message", "工具调用完成"),
                    "tool_type": tool_type,
                    "parameters": parameters,
                    "success": True,
                    "data": result.get("data", {}),
                    "response_type": "tool_result"
                }
            except Exception as e:
                logger.error(f"工具调用失败 {tool_type}: {e}")
                return {
                    "content": f"工具调用失败: {str(e)}",
                    "tool_type": tool_type,
                    "success": False,
                    "error": str(e),
                    "response_type": "tool_error"
                }
        else:
            return await self._handle_unknown_tool(query, context, tool_type)
    
    def _identify_tool(self, query: str, route_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """识别工具类型和参数"""
        query = query.strip()
        
        # 检查匹配的命令模式
        matched_patterns = route_metadata.get("matched_patterns", {}).get("matches", [])
        
        for pattern in matched_patterns:
            if pattern.startswith('/'):
                parts = pattern[1:].split()
                if parts:
                    tool_type = parts[0]
                    parameters = " ".join(parts[1:]) if len(parts) > 1 else ""
                    return {"tool_type": tool_type, "parameters": parameters}
        
        # 使用正则模式匹配
        for tool_type, patterns in self.tool_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    parameters = match.group(1).strip() if match.groups() else ""
                    # 映射工具类型
                    actual_tool = self._map_tool_type(tool_type)
                    return {"tool_type": actual_tool, "parameters": parameters}
        
        return None
    
    def _map_tool_type(self, detected_type: str) -> str:
        """映射检测到的工具类型到实际处理器"""
        mapping = {
            "calculator": "calc",
            "weather": "weather",
            "translation": "translate",
            "reminder": "remind"
        }
        return mapping.get(detected_type, detected_type)
    
    async def _handle_calculator(self, query: str, parameters: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理计算请求"""
        if not parameters:
            # 尝试从原始查询中提取表达式
            calc_match = re.search(r'(\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)*)', query)
            if calc_match:
                parameters = calc_match.group(1)
            else:
                return {
                    "message": "🔢 请告诉我要计算什么？例如：'计算 2 + 3' 或 '8 * 7'",
                    "data": {"error": "no_expression"}
                }
        
        try:
            # 安全的数学表达式计算
            result = self._safe_eval(parameters)
            
            return {
                "message": f"🔢 **计算结果**\n\n表达式: `{parameters}`\n结果: **{result}**",
                "data": {
                    "expression": parameters,
                    "result": result
                }
            }
        except Exception as e:
            return {
                "message": f"❌ 计算错误: {str(e)}\n\n请检查表达式是否正确，例如：'2 + 3' 或 '8 * 7'",
                "data": {
                    "expression": parameters,
                    "error": str(e)
                }
            }
    
    def _safe_eval(self, expression: str) -> float:
        """安全的表达式计算"""
        # 只允许数字、基本运算符、括号和空格
        allowed_chars = "0123456789+-*/()., "
        if not all(c in allowed_chars for c in expression):
            raise ValueError("表达式包含不被允许的字符")
        
        # 简单的表达式计算
        try:
            # 替换中文符号
            expression = expression.replace('×', '*').replace('÷', '/')
            # 移除空格
            expression = expression.replace(' ', '')
            # 计算结果
            result = eval(expression)
            return result
        except ZeroDivisionError:
            raise ValueError("除数不能为零")
        except:
            raise ValueError("表达式格式错误")
    
    async def _handle_weather(self, query: str, parameters: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理天气查询"""
        location = parameters if parameters else "当前位置"
        
        # 模拟天气数据（实际应用中应该调用天气API）
        weather_data = {
            "location": location,
            "temperature": "22°C",
            "condition": "多云",
            "humidity": "65%",
            "wind": "东北风 3级"
        }
        
        weather_text = f"🌤️ **{location}天气**\n\n"
        weather_text += f"🌡️ 温度: {weather_data['temperature']}\n"
        weather_text += f"☁️ 天气: {weather_data['condition']}\n"
        weather_text += f"💧 湿度: {weather_data['humidity']}\n"
        weather_text += f"🌬️ 风力: {weather_data['wind']}\n"
        weather_text += f"\n*注：这是模拟数据，实际部署时需要接入天气API*"
        
        return {
            "message": weather_text,
            "data": weather_data
        }
    
    async def _handle_translation(self, query: str, parameters: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理翻译请求"""
        if not parameters:
            return {
                "message": "🔤 请告诉我要翻译什么内容？例如：'翻译 hello world'",
                "data": {"error": "no_content"}
            }
        
        # 简单的翻译逻辑（实际应用中应该调用翻译API）
        translations = {
            "hello": "你好",
            "world": "世界",
            "good morning": "早上好",
            "thank you": "谢谢",
            "goodbye": "再见",
            "how are you": "你好吗",
            "nice to meet you": "很高兴见到你"
        }
        
        text_lower = parameters.lower()
        translated = translations.get(text_lower)
        
        if translated:
            result_text = f"🔤 **翻译结果**\n\n原文: {parameters}\n译文: **{translated}**"
        else:
            result_text = f"🔤 **翻译请求**\n\n原文: {parameters}\n\n*注：这是模拟翻译功能，实际部署时需要接入翻译API*\n建议翻译: 请使用专业翻译服务"
        
        return {
            "message": result_text,
            "data": {
                "original": parameters,
                "translated": translated or "需要接入翻译API",
                "is_mock": True
            }
        }
    
    async def _handle_reminder(self, query: str, parameters: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理提醒设置"""
        if not parameters:
            return {
                "message": "⏰ 请告诉我要设置什么提醒？例如：'提醒我10分钟后喝水'",
                "data": {"error": "no_content"}
            }
        
        # 简单的提醒逻辑（实际应用中需要实现定时任务）
        reminder_text = f"⏰ **提醒已设置**\n\n内容: {parameters}\n\n"
        reminder_text += "*注：这是模拟提醒功能，实际部署时需要实现定时任务系统*"
        
        return {
            "message": reminder_text,
            "data": {
                "reminder_content": parameters,
                "status": "mock_set",
                "note": "需要实现定时任务系统"
            }
        }
    
    async def _handle_timer(self, query: str, parameters: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理计时器"""
        if not parameters:
            return {
                "message": "⏱️ 请设置计时时间，例如：'设置5分钟计时器'",
                "data": {"error": "no_duration"}
            }
        
        timer_text = f"⏱️ **计时器已启动**\n\n时长: {parameters}\n\n*注：这是模拟计时功能*"
        
        return {
            "message": timer_text,
            "data": {
                "duration": parameters,
                "status": "mock_started"
            }
        }
    
    async def _handle_unknown_tool(self, query: str, context: Dict[str, Any], tool_type: str = None) -> Dict[str, Any]:
        """处理未知工具"""
        available_tools = list(self.tool_handlers.keys())
        
        message = f"🔧 "
        if tool_type:
            message += f"未知的工具类型: '{tool_type}'\n\n"
        else:
            message += "无法识别工具类型\n\n"
        
        message += "**可用工具:**\n"
        message += "• 🔢 计算器: '计算 2+3' 或 '/calc 2+3'\n"
        message += "• 🌤️ 天气: '查天气' 或 '/weather 北京'\n"
        message += "• 🔤 翻译: '翻译 hello' 或 '/translate hello'\n"
        message += "• ⏰ 提醒: '提醒我喝水' 或 '/remind 喝水'\n"
        
        return {
            "content": message,
            "tool_type": tool_type,
            "success": False,
            "available_tools": available_tools,
            "response_type": "unknown_tool"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        base_health = await super().health_check()
        
        base_health.update({
            "available_tools": len(self.tool_handlers),
            "tool_patterns": len(self.tool_patterns),
            "tools": list(self.tool_handlers.keys())
        })
        
        return base_health