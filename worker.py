#!/usr/bin/env python3
"""
Celery Worker 启动脚本 - 架构优化版

这个脚本用于启动 Celery Worker 进程来监听和处理异步任务。
支持新的任务分离架构，包括：
1. 独立的文档创建任务 (document_queue)
2. 独立的RAG处理任务 (rag_queue) 
3. 文件处理任务 (file_queue)
4. 工作流协调任务 (workflow_queue)

Worker 进程会：
1. 连接到 Redis 消息队列
2. 监听指定队列中的任务
3. 根据任务路由规则分发任务到对应的处理器
4. 执行任务并返回结果

使用方法:
python worker.py [选项]

示例:
python worker.py --loglevel=info
python worker.py --queues=document_queue,file_queue,rag_queue --concurrency=4
python worker.py --specialized=document  # 专用文档处理worker
python worker.py --specialized=rag       # 专用RAG处理worker
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.services.task_service import CeleryTaskService
from config import get_config

# 确保新的任务处理器被加载
try:
    from modules.tasks.handlers.document_handlers import DocumentCreateHandler
    from modules.tasks.handlers.rag_handlers import AsyncDocumentProcessingHandler
    from modules.tasks.handlers.file_handlers_v2 import OptimizedFileUploadCompleteHandler
    print("✅ 新架构任务处理器加载成功")
except Exception as e:
    print(f"⚠️  新架构任务处理器加载失败: {e}")
    print("   将使用原有任务处理器")

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
    
    # 更新任务路由配置以支持新架构
    app = task_service.app
    app.conf.update(
        task_routes={
            # 文档相关任务
            'document.create': {'queue': 'document_queue'},
            'document.update_metadata': {'queue': 'document_queue'},
            
            # RAG相关任务  
            'rag.process_document_async': {'queue': 'rag_queue'},
            'rag.process_document': {'queue': 'rag_queue'},
            'rag.generate_embeddings': {'queue': 'rag_queue'},
            'rag.store_vectors': {'queue': 'rag_queue'},
            'rag.semantic_search': {'queue': 'rag_queue'},
            'rag.cleanup_document': {'queue': 'rag_queue'},
            
            # 文件处理任务
            'TaskName.FILE_UPLOAD_CONFIRM': {'queue': 'file_queue'},
            'file.analyze_content': {'queue': 'file_queue'},
            'file.cleanup_temp': {'queue': 'file_queue'},
            'file.convert_format': {'queue': 'file_queue'},
            'file.workflow_status': {'queue': 'file_queue'},
            'file.cancel_workflow': {'queue': 'file_queue'},
            
            # 工作流任务
            'workflow.*': {'queue': 'workflow_queue'},
        },
        
        # 队列优先级配置
        task_queue_max_priority=10,
        task_default_priority=5,
        worker_prefetch_multiplier=1,
        
        # 结果配置
        result_expires=3600,  # 结果保存1小时
        task_track_started=True,
        task_send_events=True,
        
        # 序列化配置
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        
        # 时间配置
        timezone='UTC',
        enable_utc=True,
    )
    
    return app


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Celery Worker - 架构优化版")
    
    parser.add_argument('--loglevel', default='info', 
                       choices=['debug', 'info', 'warning', 'error'],
                       help='日志级别 (default: info)')
    
    parser.add_argument('--concurrency', type=int, default=None,
                       help='并发数 (default: 从配置文件读取)')
    
    parser.add_argument('--queues', default=None,
                       help='监听的队列，逗号分隔 (default: 所有队列)')
    
    parser.add_argument('--specialized', choices=['document', 'rag', 'file', 'workflow'],
                       help='专用worker类型')
    
    parser.add_argument('--max-tasks-per-child', type=int, default=None,
                       help='每个worker进程处理的最大任务数')
    
    parser.add_argument('--pool', default='prefork',
                       choices=['prefork', 'eventlet', 'gevent', 'solo'],
                       help='Worker池类型 (default: prefork)')
    
    return parser.parse_args()


def get_queue_config(specialized=None, custom_queues=None):
    """获取队列配置"""
    
    # 所有可用队列
    all_queues = [
        'default',           # 默认队列
        'document_queue',    # 文档创建队列
        'rag_queue',        # RAG处理队列
        'file_queue',       # 文件处理队列
        'workflow_queue',   # 工作流队列
        'notification_queue' # 通知队列
    ]
    
    # 专用worker配置
    specialized_configs = {
        'document': {
            'queues': ['document_queue', 'default'],
            'concurrency': 4,
            'description': '专用文档处理Worker'
        },
        'rag': {
            'queues': ['rag_queue'],
            'concurrency': 2,  # RAG任务通常消耗更多资源
            'description': '专用RAG处理Worker'
        },
        'file': {
            'queues': ['file_queue', 'default'],
            'concurrency': 3,
            'description': '专用文件处理Worker'
        },
        'workflow': {
            'queues': ['workflow_queue', 'default'],
            'concurrency': 2,
            'description': '专用工作流协调Worker'
        }
    }
    
    if custom_queues:
        # 自定义队列
        return {
            'queues': custom_queues.split(','),
            'description': '自定义队列Worker'
        }
    elif specialized:
        # 专用worker
        return specialized_configs.get(specialized, {
            'queues': all_queues,
            'description': '通用Worker'
        })
    else:
        # 默认：监听所有队列
        return {
            'queues': all_queues,
            'description': '通用Worker'
        }


def main():
    """主函数 - 启动 Celery Worker"""
    
    # 解析命令行参数
    args = parse_args()
    
    print("🚀 启动 Celery Worker - 架构优化版")
    print("=" * 60)
    
    # 创建 Celery 应用
    app = create_celery_app()
    
    # 获取配置
    config = get_config()
    queue_config = get_queue_config(args.specialized, args.queues)
    
    # 显示配置信息
    print(f"📋 Worker 配置信息:")
    print(f"  - Worker类型: {queue_config.get('description', '通用Worker')}")
    print(f"  - Broker URL: {config.celery.broker_url}")
    print(f"  - Result Backend: {config.celery.result_backend}")
    print(f"  - App Name: {config.celery.app_name}")
    
    # 并发配置
    concurrency = (args.concurrency or 
                  queue_config.get('concurrency') or 
                  config.celery.worker_concurrency)
    print(f"  - 并发数: {concurrency}")
    print(f"  - 池类型: {args.pool}")
    
    # 队列配置
    print(f"  - 监听队列: {', '.join(queue_config['queues'])}")
    print()
    
    # 显示已注册的任务
    print("📝 已注册的任务:")
    registered_tasks = list(app.tasks.keys())
    task_count = 0
    for task_name in sorted(registered_tasks):
        if not task_name.startswith('celery.'):  # 跳过 Celery 内置任务
            print(f"  ✅ {task_name}")
            task_count += 1
    print(f"  📊 总计: {task_count} 个任务")
    print()
    
    # 显示队列路由信息
    print("🔀 任务路由配置:")
    routes = app.conf.task_routes
    route_count = 0
    for pattern, route_config in routes.items():
        queue = route_config.get('queue', 'default')
        print(f"  📂 {pattern} → {queue}")
        route_count += 1
    print(f"  📊 总计: {route_count} 个路由规则")
    print()
    
    print("🔄 Worker 正在监听任务...")
    print("💡 按 Ctrl+C 停止 Worker")
    print("=" * 60)
    
    # 启动 Worker
    worker_kwargs = {
        'loglevel': args.loglevel,
        'concurrency': concurrency,
        'queues': queue_config['queues'],
        'prefetch_multiplier': config.celery.worker_prefetch_multiplier,
        'max_tasks_per_child': (args.max_tasks_per_child or 
                               config.celery.worker_max_tasks_per_child),
        'time_limit': config.celery.task_time_limit,
        'soft_time_limit': config.celery.task_soft_time_limit,
        'pool': args.pool,
    }
    
    worker = app.Worker(**worker_kwargs)
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\n🛑 Worker 停止")
        worker.stop()


if __name__ == '__main__':
    main()
