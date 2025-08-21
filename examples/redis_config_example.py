"""
Redis配置使用示例

展示如何在实际项目中使用Redis配置管理功能。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from pathlib import Path
from modules.tasks.config import RedisConfig, TaskConfigManager
from modules.services.redis_service import RedisService

async def example_basic_redis_config():
    """基础Redis配置示例"""
    print("=== 基础Redis配置示例 ===")
    
    # 1. 使用默认配置
    default_config = RedisConfig()
    print(f"默认配置: {default_config.host}:{default_config.port}/{default_config.db}")
    
    # 2. 自定义配置
    custom_config = RedisConfig(
        host="redis.myproject.com",
        port=6379,
        db=1,
        password="production_password",
        key_prefix="myapp:",
        default_ttl=7200,  # 2小时
        max_connections=100
    )
    
    print(f"自定义配置: {custom_config.host}:{custom_config.port}")
    print(f"键前缀: {custom_config.key_prefix}")
    print(f"默认过期时间: {custom_config.default_ttl}秒")

async def example_redis_cluster_config():
    """Redis集群配置示例"""
    print("\n=== Redis集群配置示例 ===")
    
    cluster_config = RedisConfig(
        # 启用集群模式
        cluster_enabled=True,
        cluster_nodes=[
            {"host": "redis-1.cluster.com", "port": 7000},
            {"host": "redis-2.cluster.com", "port": 7000},
            {"host": "redis-3.cluster.com", "port": 7000},
            {"host": "redis-4.cluster.com", "port": 7000},
            {"host": "redis-5.cluster.com", "port": 7000},
            {"host": "redis-6.cluster.com", "port": 7000}
        ],
        cluster_require_full_coverage=True,
        cluster_skip_full_coverage_check=False,
        
        # 通用配置
        password="cluster_password",
        socket_timeout=3.0,
        key_prefix="cluster:",
        default_ttl=3600
    )
    
    print(f"集群节点数: {len(cluster_config.cluster_nodes)}")
    print(f"需要全覆盖: {cluster_config.cluster_require_full_coverage}")

async def example_redis_sentinel_config():
    """Redis哨兵配置示例"""
    print("\n=== Redis哨兵配置示例 ===")
    
    sentinel_config = RedisConfig(
        # 启用哨兵模式
        sentinel_enabled=True,
        sentinel_hosts=[
            {"host": "sentinel-1.example.com", "port": 26379},
            {"host": "sentinel-2.example.com", "port": 26379},
            {"host": "sentinel-3.example.com", "port": 26379}
        ],
        sentinel_master_name="mymaster",
        sentinel_socket_timeout=0.1,
        
        # Redis认证
        username="redis_user",
        password="redis_password",
        db=0,
        
        # 其他配置
        key_prefix="sentinel:",
        default_ttl=1800
    )
    
    print(f"哨兵节点数: {len(sentinel_config.sentinel_hosts)}")
    print(f"主节点名: {sentinel_config.sentinel_master_name}")

async def example_ssl_redis_config():
    """SSL Redis配置示例"""
    print("\n=== SSL Redis配置示例 ===")
    
    ssl_config = RedisConfig(
        host="secure-redis.example.com",
        port=6380,  # 常见的Redis SSL端口
        
        # SSL配置
        ssl=True,
        ssl_keyfile="/path/to/client.key",
        ssl_certfile="/path/to/client.crt",
        ssl_ca_certs="/path/to/ca.crt",
        ssl_cert_reqs="required",
        ssl_check_hostname=True,
        
        # 认证
        username="ssl_user",
        password="ssl_password",
        
        # 性能配置
        socket_timeout=10.0,  # SSL连接可能需要更长时间
        socket_connect_timeout=10.0,
        max_connections=20
    )
    
    print(f"SSL Redis: {ssl_config.host}:{ssl_config.port}")
    print(f"证书验证: {ssl_config.ssl_cert_reqs}")

async def example_config_file_usage():
    """配置文件使用示例"""
    print("\n=== 配置文件使用示例 ===")
    
    # 创建示例配置文件
    config_data = {
        "redis": {
            "host": "config-redis.example.com",
            "port": 6379,
            "db": 2,
            "password": "config_password",
            "key_prefix": "config:",
            "default_ttl": 5400,
            "serializer": "json",
            "max_connections": 75,
            "socket_timeout": 7.0,
            "decode_responses": True,
            "health_check_interval": 60
        },
        "worker": {
            "concurrency": 8,
            "time_limit": 1800
        }
    }
    
    # 保存到临时文件
    config_file = Path("temp_redis_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    try:
        # 使用配置文件创建管理器
        manager = TaskConfigManager(str(config_file))
        
        # 获取Redis配置
        redis_config = manager.get_redis_config()
        print(f"从文件加载: {redis_config.host}:{redis_config.port}")
        print(f"键前缀: {redis_config.key_prefix}")
        print(f"连接池: {redis_config.max_connections}")
        
        # 生成Celery配置
        celery_config = manager.get_celery_config()
        print(f"Celery代理: {celery_config['broker_url']}")
        
    finally:
        # 清理临时文件
        if config_file.exists():
            config_file.unlink()

async def example_redis_service_usage():
    """Redis服务使用示例"""
    print("\n=== Redis服务使用示例 ===")
    
    # 创建自定义配置
    config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        key_prefix="example:",
        serializer="json",
        default_ttl=1800
    )
    
    # 注意：这里仅演示配置，实际使用时需要确保Redis服务器运行
    print(f"Redis服务配置:")
    print(f"  连接: {config.host}:{config.port}/{config.db}")
    print(f"  键前缀: {config.key_prefix}")
    print(f"  序列化: {config.serializer}")
    
    # 展示连接参数
    manager = TaskConfigManager()
    manager.update_redis_config(config)
    params = manager.get_redis_connection_params()
    
    print(f"  连接参数:")
    for key, value in params.items():
        if key in ['host', 'port', 'db', 'socket_timeout', 'max_connections']:
            print(f"    {key}: {value}")

async def example_environment_specific_configs():
    """不同环境的配置示例"""
    print("\n=== 不同环境配置示例 ===")
    
    # 开发环境配置
    dev_config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        key_prefix="dev:",
        default_ttl=3600,
        max_connections=10,
        serializer="json"
    )
    print(f"开发环境: {dev_config.host} (连接池: {dev_config.max_connections})")
    
    # 测试环境配置
    test_config = RedisConfig(
        host="test-redis.internal",
        port=6379,
        db=1,
        key_prefix="test:",
        default_ttl=1800,
        max_connections=20,
        serializer="json"
    )
    print(f"测试环境: {test_config.host} (TTL: {test_config.default_ttl}s)")
    
    # 生产环境配置
    prod_config = RedisConfig(
        host="prod-redis.cluster.com",
        port=6379,
        db=0,
        password="secure_production_password",
        username="prod_user",
        key_prefix="prod:",
        default_ttl=7200,
        max_connections=200,
        serializer="pickle",  # 生产环境可能需要更高效的序列化
        
        # 生产环境SSL
        ssl=True,
        ssl_cert_reqs="required",
        
        # 更严格的超时设置
        socket_timeout=3.0,
        socket_connect_timeout=3.0,
        retry_on_timeout=True,
        
        # 健康检查
        health_check_interval=30
    )
    print(f"生产环境: {prod_config.host} (SSL: {prod_config.ssl}, 连接池: {prod_config.max_connections})")

async def main():
    """主函数"""
    print("🚀 Redis配置使用示例\n")
    
    await example_basic_redis_config()
    await example_redis_cluster_config()
    await example_redis_sentinel_config()
    await example_ssl_redis_config()
    await example_config_file_usage()
    await example_redis_service_usage()
    await example_environment_specific_configs()
    
    print("\n✨ 所有示例执行完成！")
    
    print("\n📝 使用建议:")
    print("1. 开发环境使用简单的单实例配置")
    print("2. 生产环境考虑使用集群或哨兵模式")
    print("3. 敏感环境启用SSL和认证")
    print("4. 根据业务需求调整连接池大小和超时设置")
    print("5. 使用配置文件管理不同环境的参数")

if __name__ == "__main__":
    asyncio.run(main())