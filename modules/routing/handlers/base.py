"""
Base Query Handler

查询处理器的基础类，提供通用功能。
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..strategies.base import IQueryHandler

logger = logging.getLogger(__name__)


class BaseQueryHandler(IQueryHandler):
    """查询处理器基础类"""
    
    def __init__(self, handler_name: str):
        self._handler_name = handler_name
        self.processing_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_processing_time = None
        
    @property
    def handler_name(self) -> str:
        return self._handler_name
        
    async def handle(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """处理查询请求"""
        start_time = datetime.now()
        route_metadata = route_metadata or {}
        
        try:
            self.processing_count += 1
            
            logger.info(f"{self.handler_name} 开始处理查询: {query[:50]}...")
            
            # 调用具体的处理逻辑
            result = await self._handle_query(query, context, route_metadata)
            
            self.success_count += 1
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.last_processing_time = processing_time
            
            # 确保结果包含必要字段
            if not isinstance(result, dict):
                result = {"content": str(result)}
                
            result.update({
                "handler": self.handler_name,
                "processing_time_ms": processing_time,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
            logger.info(f"{self.handler_name} 处理完成，耗时: {processing_time:.1f}ms")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.error(f"{self.handler_name} 处理失败: {e}")
            
            return {
                "handler": self.handler_name,
                "processing_time_ms": processing_time,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "content": f"抱歉，处理您的请求时出现了问题：{str(e)}"
            }
    
    async def _handle_query(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        具体的查询处理逻辑，子类需要重写此方法
        
        Args:
            query: 用户查询
            context: 上下文信息
            route_metadata: 路由元数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        raise NotImplementedError("子类必须实现 _handle_query 方法")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        success_rate = 0.0
        if self.processing_count > 0:
            success_rate = self.success_count / self.processing_count
            
        return {
            "status": "healthy",
            "handler": self.handler_name,
            "statistics": {
                "total_processed": self.processing_count,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "success_rate": success_rate,
                "last_processing_time_ms": self.last_processing_time
            }
        }
        
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.processing_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_processing_time = None
        logger.info(f"{self.handler_name} 统计信息已重置")
        
    async def initialize(self) -> None:
        """初始化处理器"""
        logger.info(f"{self.handler_name} 已初始化")
        
    async def cleanup(self) -> None:
        """清理资源"""
        logger.info(f"{self.handler_name} 已清理")