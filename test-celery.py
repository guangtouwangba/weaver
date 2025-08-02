#!/usr/bin/env python3
"""
Celery配置测试脚本
Test script for Celery configuration
"""

import os
import sys
import time
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_redis_connection():
    """测试Redis连接"""
    try:
        import redis
        
        # 从环境变量获取Redis配置
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_password = os.getenv('REDIS_PASSWORD', 'redis_password')
        
        # 连接Redis
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )
        
        # 测试连接
        result = r.ping()
        print(f"✅ Redis连接成功: {redis_host}:{redis_port}")
        return True
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False

def test_celery_app():
    """测试Celery应用"""
    try:
        from celery_app import celery_app
        
        # 检查Celery配置
        print(f"✅ Celery应用加载成功")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        
        # 检查注册的任务
        registered_tasks = list(celery_app.tasks.keys())
        print(f"   注册任务数: {len(registered_tasks)}")
        
        for task in registered_tasks:
            if not task.startswith('celery.'):  # 过滤内置任务
                print(f"     - {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery应用加载失败: {e}")
        return False

def test_task_import():
    """测试任务导入"""
    try:
        from tasks.research_tasks import execute_research_job
        print(f"✅ 任务导入成功: execute_research_job")
        return True
        
    except Exception as e:
        print(f"❌ 任务导入失败: {e}")
        return False

def test_worker_status():
    """测试Worker状态"""
    try:
        from celery_app import celery_app
        
        # 检查活跃的Worker
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ 发现活跃的Worker: {len(active_workers)}")
            for worker_name, tasks in active_workers.items():
                print(f"   Worker: {worker_name} - 活跃任务: {len(tasks)}")
        else:
            print(f"⚠️ 没有发现活跃的Worker")
            
        return True
        
    except Exception as e:
        print(f"❌ Worker状态检查失败: {e}")
        return False

def test_simple_task():
    """测试简单任务执行"""
    try:
        from celery_app import celery_app
        
        # 创建一个简单的测试任务
        @celery_app.task
        def test_task(message):
            return f"Hello {message}!"
        
        # 发送任务
        result = test_task.delay("Celery")
        print(f"✅ 任务发送成功: {result.id}")
        
        # 等待结果（最多10秒）
        try:
            task_result = result.get(timeout=10)
            print(f"✅ 任务执行成功: {task_result}")
            return True
        except Exception as e:
            print(f"⚠️ 任务执行超时或失败: {e}")
            print(f"   任务状态: {result.status}")
            return False
            
    except Exception as e:
        print(f"❌ 任务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 Celery配置测试开始...")
    print("=" * 50)
    
    # 设置环境变量（如果不存在）
    os.environ.setdefault('CELERY_BROKER_URL', 'redis://:redis_password@localhost:6379/0')
    os.environ.setdefault('CELERY_RESULT_BACKEND', 'redis://:redis_password@localhost:6379/0')
    
    tests = [
        ("Redis连接测试", test_redis_connection),
        ("Celery应用测试", test_celery_app),
        ("任务导入测试", test_task_import),
        ("Worker状态测试", test_worker_status),
        ("简单任务测试", test_simple_task),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        success = test_func()
        results.append((test_name, success))
        
        if not success:
            print(f"   跳过后续测试...")
            break
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！Celery配置正确。")
        print("\n📝 下一步:")
        print("   1. 启动Celery Worker: celery -A celery_app worker --loglevel=info")
        print("   2. 启动后端API: python -m uvicorn api.simple_server:app --reload")
        print("   3. 测试job trigger功能")
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
        print("\n🔧 故障排除:")
        print("   1. 确保Redis服务运行: docker-compose -f infra/docker/docker-compose.middleware.yml up -d redis")
        print("   2. 检查环境变量配置")
        print("   3. 查看详细错误信息")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())