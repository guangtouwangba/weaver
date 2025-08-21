#!/usr/bin/env python3
"""
Celery Worker 启动脚本

这个脚本用于启动 Celery Worker 进程来监听和处理异步任务。
Worker 进程会：
1. 连接到 Redis 消息队列
2. 监听指定队列中的任务
3. 根据任务路由规则分发任务到对应的处理器
4. 执行任务并返回结果

使用方法:
python worker.py [选项]

示例:
python worker.py --loglevel=info
python worker.py --queues=file_queue,rag_queue --concurrency=2
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.services.task_service import CeleryTaskService
from config import get_config

logger = logging.getLogger(__name__)


def create_celery_app():
    """创建并配置 Celery 应用"""
    config = get_config()
    
    # 创建任务服务实例
    task_service = CeleryTaskService(
        broker_url=config.celery.broker_url,
        result_backend=config.celery.result_backend,
        app_name=config.celery.app_name
    )
    
    # 同步初始化（注册任务处理器）
    import asyncio
    asyncio.run(task_service.initialize())
    
    return task_service.app


def main():
    """主函数 - 启动 Celery Worker"""
    
    print("🚀 启动 Celery Worker...")
    print("=" * 60)
    
    # 创建 Celery 应用
    app = create_celery_app()
    
    # 显示配置信息
    config = get_config()
    print(f"📋 Worker 配置信息:")
    print(f"  - Broker URL: {config.celery.broker_url}")
    print(f"  - Result Backend: {config.celery.result_backend}")
    print(f"  - App Name: {config.celery.app_name}")
    print(f"  - 并发数: {config.celery.worker_concurrency}")
    print()
    
    # 显示已注册的任务
    print("📝 已注册的任务:")
    registered_tasks = list(app.tasks.keys())
    for task_name in sorted(registered_tasks):
        if not task_name.startswith('celery.'):  # 跳过 Celery 内置任务
            print(f"  ✅ {task_name}")
    print()
    
    # 显示队列路由信息
    print("🔀 任务路由配置:")
    routes = app.conf.task_routes
    for pattern, route_config in routes.items():
        queue = route_config.get('queue', 'default')
        print(f"  📂 {pattern} → {queue}")
    print()
    
    print("🔄 Worker 正在监听任务...")
    print("💡 按 Ctrl+C 停止 Worker")
    print("=" * 60)
    
    # 启动 Worker
    # 这等价于命令行: celery -A worker.app worker --loglevel=info
    worker = app.Worker(
        loglevel='info',
        concurrency=config.celery.worker_concurrency,
        queues=['default', 'file_queue', 'rag_queue', 'notification_queue'],
        prefetch_multiplier=config.celery.worker_prefetch_multiplier,
        max_tasks_per_child=config.celery.worker_max_tasks_per_child,
        time_limit=config.celery.task_time_limit,
        soft_time_limit=config.celery.task_soft_time_limit,
    )
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\n🛑 Worker 停止")
        worker.stop()


if __name__ == '__main__':
    main()
