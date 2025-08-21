"""
简单的任务系统调试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from unittest.mock import MagicMock

from modules.tasks.base import ITaskHandler, TaskConfig, TaskPriority
from modules.services.task_service import CeleryTaskService, TaskRegistry

class SimpleTaskHandler(ITaskHandler):
    """简单任务处理器"""
    
    def __init__(self, task_name: str):
        self._task_name = task_name
        
    @property
    def task_name(self) -> str:
        return self._task_name
    
    @property
    def task_config(self):
        return TaskConfig(
            task_name=self._task_name,
            priority=TaskPriority.NORMAL,
            timeout=300,
            retry_count=3
        )
    
    async def handle(self, *args, **kwargs):
        return {"result": "success", "args": args, "kwargs": kwargs}

async def main():
    print("🔧 开始调试任务系统...")
    
    # 1. 创建注册表
    registry = TaskRegistry()
    print(f"✓ 创建注册表，当前已注册任务: {registry.list_tasks()}")
    
    # 2. 注册任务处理器
    handler = SimpleTaskHandler("test.simple_task")
    registry.register("test.simple_task", handler)
    print(f"✓ 注册任务处理器，当前已注册任务: {registry.list_tasks()}")
    
    # 3. 检查是否已注册
    is_registered = registry.is_registered("test.simple_task")
    print(f"✓ 检查任务是否已注册: {is_registered}")
    
    # 4. 创建任务服务
    task_service = CeleryTaskService(
        broker_url="memory://",
        backend_url="cache+memory://",
        registry=registry
    )
    
    # 模拟Celery应用
    mock_app = MagicMock()
    mock_result = MagicMock()
    mock_result.id = "test-task-123"
    mock_app.send_task.return_value = mock_result
    task_service.app = mock_app
    
    print(f"✓ 创建任务服务")
    
    # 5. 检查任务服务中的注册状态
    service_registered = task_service.is_handler_registered("test.simple_task")
    print(f"✓ 任务服务中是否已注册: {service_registered}")
    
    # 6. 尝试提交任务
    try:
        task_id = await task_service.submit_task("test.simple_task", "arg1", "arg2", param="value")
        print(f"✓ 任务提交成功: {task_id}")
        
        # 验证调用
        mock_app.send_task.assert_called_once()
        print("✓ Celery调用验证成功")
        
    except Exception as e:
        print(f"❌ 任务提交失败: {e}")
        print(f"   注册表handlers: {registry._handlers}")
        print(f"   注册表configs: {registry._configs}")
        
    print("🎉 调试完成!")

if __name__ == "__main__":
    asyncio.run(main())