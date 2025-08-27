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
python worker.py --loglevel=info                    # 默认统一worker
python worker.py --specialized=unified              # 明确指定统一worker
python worker.py --specialized=document             # 专用文档处理worker
python worker.py --specialized=rag                  # 专用RAG处理worker
python worker.py --specialized=file                 # 专用文件处理worker
python worker.py --queues=document_queue,rag_queue  # 自定义队列
"""

import sys
import os
import logging
import argparse
import platform
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 显式加载.env文件
from dotenv import load_dotenv
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ 已加载环境配置文件: {env_file}")
else:
    print(f"⚠️  环境配置文件不存在: {env_file}")

from modules.services.task_service import CeleryTaskService
from config import get_config

# 确保新的任务处理器被加载
try:
    # 显式导入所有任务处理器以确保它们被注册
    import modules.tasks.handlers.file_handlers
    import modules.tasks.handlers.rag_handlers  
    import modules.tasks.handlers.document_handlers
    import modules.tasks.handlers.summary_handlers  # 新增摘要处理器
    print("✅ 新架构任务处理器加载成功")
except Exception as e:
    print(f"⚠️  新架构任务处理器加载失败: {e}")
    print("   将使用原有任务处理器")

logger = logging.getLogger(__name__)


async def initialize_vector_collections():
    """初始化向量存储集合，在Worker启动时创建"""
    try:
        from modules.vector_store.weaviate_service import WeaviateVectorStore
        from modules.vector_store.base import VectorStoreConfig, VectorStoreProvider, SimilarityMetric
        
        config = get_config()
        
        # 创建WeaviateVectorStore实例，启用集合创建
        weaviate_store = WeaviateVectorStore(
            url=getattr(config, 'weaviate_url', None) or 
                config.vector_db.weaviate_url or 
                "http://localhost:8080",
            api_key=getattr(config, 'weaviate_api_key', None),
            create_collections_on_init=True  # 启动时创建集合
        )
        
        # 初始化连接并创建集合
        await weaviate_store.initialize()
        
        print("🎉 向量存储服务已启动，集合已准备就绪")
        
        # 清理连接
        await weaviate_store.cleanup()
        
    except ImportError as e:
        print(f"向量存储模块不可用: {e}")
        raise
    except Exception as e:
        print(f"向量存储初始化失败: {e}")
        raise


def setup_macos_compatibility():
    """设置macOS兼容性配置以避免fork安全问题"""
    if platform.system() == "Darwin":  # macOS
        print("🍎 检测到macOS系统，设置fork安全配置...")
        
        # 设置环境变量以避免CoreFoundation fork问题
        os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
        os.environ["PYTHONUNBUFFERED"] = "1"  # 确保输出实时显示
        
        print("  ✅ 已设置 OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES")
        print("  ✅ 已设置 PYTHONUNBUFFERED=1")
        
        return True
    return False


def get_safe_pool_type(requested_pool: str) -> str:
    """为macOS返回安全的worker pool类型"""
    if platform.system() == "Darwin":  # macOS
        if requested_pool == "prefork":
            print("⚠️  macOS系统: 将prefork pool改为threads以避免fork安全问题")
            return "threads"
        elif requested_pool in ["eventlet", "gevent"]:
            print(f"⚠️  macOS系统: {requested_pool} pool可能有兼容问题，建议使用threads")
    
    return requested_pool


def create_celery_app():
    """创建并配置 Celery 应用"""
    config = get_config()

    # 创建任务服务实例
    task_service = CeleryTaskService(
        broker_url=config.celery.broker_url,
        result_backend=config.celery.result_backend,
        app_name=config.celery.app_name,
    )

    # 同步初始化（注册任务处理器）
    import asyncio

    asyncio.run(task_service.initialize())
    
    # 初始化向量存储集合 (fail fast)
    try:
        asyncio.run(initialize_vector_collections())
        print("✅ Weaviate集合初始化成功")
    except Exception as e:
        print(f"❌ Weaviate集合初始化失败: {e}")
        print("⚠️  Worker将在没有向量存储的情况下启动")

    # 更新任务路由配置以支持新架构
    app = task_service.app
    app.conf.update(
        task_routes={
            # 文档相关任务
            "document.create": {"queue": "document_queue"},
            "document.update_metadata": {"queue": "document_queue"},
            # RAG相关任务
            "rag.process_document_async": {"queue": "rag_queue"},
            "rag.process_document": {"queue": "rag_queue"},
            "rag.generate_embeddings": {"queue": "rag_queue"},
            "rag.store_vectors": {"queue": "rag_queue"},
            "rag.semantic_search": {"queue": "rag_queue"},
            "rag.cleanup_document": {"queue": "rag_queue"},
            # 摘要相关任务 (新增)
            "summary.generate_document": {"queue": "summary_queue"},
            "summary.update_index": {"queue": "summary_queue"},
            # 文件处理任务
            "file_upload_confirm": {"queue": "file_queue"},
            "TaskName.FILE_UPLOAD_CONFIRM": {"queue": "file_queue"},
            "file.analyze_content": {"queue": "file_queue"},
            "file.cleanup_temp": {"queue": "file_queue"},
            "file.convert_format": {"queue": "file_queue"},
            "file.workflow_status": {"queue": "file_queue"},
            "file.cancel_workflow": {"queue": "file_queue"},
            # 通配符路由（按优先级排序）
            "workflow.*": {"queue": "workflow_queue"},
            "rag.*": {"queue": "rag_queue"},
            "summary.*": {"queue": "summary_queue"},  # 新增摘要通配符路由
            "file.*": {"queue": "file_queue"},
            "notification.*": {"queue": "notification_queue"},
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
        task_serializer="json",
        result_serializer="json",
        accept_content=["json", "pickle"],  # 临时允许pickle以兼容mingle过程
        # 时间配置
        timezone="UTC",
        enable_utc=True,
    )

    return app


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Celery Worker - 架构优化版")

    parser.add_argument(
        "--loglevel",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="日志级别 (default: info)",
    )

    parser.add_argument(
        "--concurrency", type=int, default=None, help="并发数 (default: 从配置文件读取)"
    )

    parser.add_argument(
        "--queues", default=None, help="监听的队列，逗号分隔 (default: 所有队列)"
    )

    parser.add_argument(
        "--specialized",
        choices=["document", "rag", "summary", "file", "workflow", "unified"],
        help="worker类型: document, rag, summary, file, workflow, unified",
    )

    parser.add_argument(
        "--max-tasks-per-child",
        type=int,
        default=None,
        help="每个worker进程处理的最大任务数",
    )

    parser.add_argument(
        "--pool",
        default="prefork",
        choices=["prefork", "eventlet", "gevent", "solo", "threads"],
        help="Worker池类型 (default: prefork, macOS自动转换为threads)",
    )

    return parser.parse_args()


def get_queue_config(specialized=None, custom_queues=None):
    """获取队列配置"""

    # 所有可用队列
    all_queues = [
        "default",  # 默认队列
        "document_queue",  # 文档创建队列
        "rag_queue",  # RAG处理队列
        "summary_queue",  # 摘要处理队列 (新增)
        "file_queue",  # 文件处理队列
        "workflow_queue",  # 工作流队列
        "notification_queue",  # 通知队列
    ]

    # 专用worker配置（保留向后兼容性）
    specialized_configs = {
        "document": {
            "queues": ["document_queue", "default"],
            "concurrency": 2,  # 降低并发数
            "description": "专用文档处理Worker",
        },
        "rag": {
            "queues": ["rag_queue"],
            "concurrency": 1,  # 降低并发数，避免内存问题
            "description": "专用RAG处理Worker",
        },
        "summary": {  # 新增摘要专用worker配置
            "queues": ["summary_queue"],
            "concurrency": 1,  # 摘要生成通常是CPU密集型
            "description": "专用摘要生成Worker",
        },
        "file": {
            "queues": ["file_queue", "default"],
            "concurrency": 1,  # 降低并发数，避免PDF处理内存问题
            "description": "专用文件处理Worker",
        },
        "workflow": {
            "queues": ["workflow_queue", "default"],
            "concurrency": 1,  # 降低并发数
            "description": "专用工作流协调Worker",
        },
        "unified": {
            "queues": all_queues,
            "concurrency": 2,  # 统一worker，适度并发
            "description": "统一处理Worker（推荐）",
        },
    }

    if custom_queues:
        # 自定义队列
        return {"queues": custom_queues.split(","), "description": "自定义队列Worker"}
    elif specialized:
        # 专用worker
        return specialized_configs.get(
            specialized, {"queues": all_queues, "description": "通用Worker"}
        )
    else:
        # 默认：统一worker监听所有队列
        return {
            "queues": all_queues, 
            "concurrency": 2,  # 默认并发数，平衡性能和资源使用
            "description": "统一处理Worker（默认）"
        }


def setup_enhanced_logging(loglevel="info"):
    """设置增强的日志记录"""
    import logging
    from datetime import datetime
    
    # 设置日志级别
    numeric_level = getattr(logging, loglevel.upper(), logging.INFO)
    
    # 创建详细的日志格式
    log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(name)s:%(lineno)d | %(message)s"
    
    # 配置根日志记录器
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 设置 Celery 相关日志
    celery_logger = logging.getLogger('celery')
    celery_logger.setLevel(numeric_level)
    
    # 设置任务执行日志
    task_logger = logging.getLogger('celery.task')
    task_logger.setLevel(numeric_level)
    
    print(f"📋 日志配置:")
    print(f"  - 日志级别: {loglevel.upper()}")
    print(f"  - 时间戳: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  - 进程名称: 包含在日志中")
    print()


def main():
    """主函数 - 启动 Celery Worker"""

    # 解析命令行参数
    args = parse_args()

    print("🚀 启动 Celery Worker - 架构优化版")
    print("=" * 60)

    # 设置macOS兼容性配置
    is_macos = setup_macos_compatibility()

    # 设置增强日志
    setup_enhanced_logging(args.loglevel)

    # 创建 Celery 应用
    print("🔧 正在初始化 Celery 应用...")
    app = create_celery_app()
    print("✅ Celery 应用初始化完成")

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
    concurrency = (
        args.concurrency
        or queue_config.get("concurrency")
        or config.celery.worker_concurrency
    )
    
    # 获取安全的pool类型（macOS兼容）
    safe_pool_type = get_safe_pool_type(args.pool)
    
    print(f"  - 并发数: {concurrency}")
    print(f"  - 池类型: {safe_pool_type}")
    if safe_pool_type != args.pool:
        print(f"    (原始请求: {args.pool}, 已调整为macOS兼容)")

    # 队列配置
    print(f"  - 监听队列: {', '.join(queue_config['queues'])}")
    print()

    # 显示已注册的任务
    print("📝 已注册的任务:")
    registered_tasks = list(app.tasks.keys())
    task_count = 0
    for task_name in sorted(registered_tasks):
        if not task_name.startswith("celery."):  # 跳过 Celery 内置任务
            print(f"  ✅ {task_name}")
            task_count += 1
    print(f"  📊 总计: {task_count} 个任务")
    print()

    # 显示队列路由信息
    print("🔀 任务路由配置:")
    routes = app.conf.task_routes
    route_count = 0
    for pattern, route_config in routes.items():
        queue = route_config.get("queue", "default")
        print(f"  📂 {pattern} → {queue}")
        route_count += 1
    print(f"  📊 总计: {route_count} 个路由规则")
    print()

    print("🔄 Worker 正在监听任务...")
    print("💡 按 Ctrl+C 停止 Worker")
    print("=" * 60)

    # 启动 Worker
    worker_kwargs = {
        "loglevel": args.loglevel,
        "concurrency": concurrency,
        "queues": queue_config["queues"],
        "prefetch_multiplier": config.celery.worker_prefetch_multiplier,
        "max_tasks_per_child": (
            args.max_tasks_per_child or config.celery.worker_max_tasks_per_child
        ),
        "time_limit": config.celery.task_time_limit,
        "soft_time_limit": config.celery.task_soft_time_limit,
        "pool": safe_pool_type,
    }

    print(f"🔧 Worker启动参数详情:")
    print(f"  - 预取乘数: {worker_kwargs['prefetch_multiplier']}")
    print(f"  - 每个子进程最大任务数: {worker_kwargs['max_tasks_per_child']}")
    print(f"  - 任务时间限制: {worker_kwargs['time_limit']}秒")
    print(f"  - 软时间限制: {worker_kwargs['soft_time_limit']}秒")
    print(f"  - 实际池类型: {worker_kwargs['pool']}")
    print()

    worker = app.Worker(**worker_kwargs)

    try:
        print("🚀 正在启动 Celery Worker...")
        worker.start()
    except KeyboardInterrupt:
        print("\n🛑 接收到停止信号，正在关闭 Worker...")
        worker.stop()
        print("✅ Worker 已安全停止")
    except Exception as e:
        print(f"\n❌ Worker 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
