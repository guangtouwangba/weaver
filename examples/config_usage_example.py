"""
配置使用示例

展示如何在RAG知识管理系统中使用重组后的配置结构。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from pathlib import Path
import json

# 导入配置（需要处理循环导入问题，这里使用相对路径）
config_dir = Path(__file__).parent.parent / "config"
sys.path.insert(0, str(config_dir))
sys.path.insert(0, str(config_dir / "tasks"))

from app import AppConfig, Environment
from database import DatabaseConfig
from storage import StorageConfig, StorageProvider
from config import RedisConfig, TaskConfigManager

async def example_development_setup():
    """开发环境配置示例"""
    print("=== 开发环境配置示例 ===")
    
    # 开发环境应用配置
    app_config = AppConfig(
        app_name="RAG开发环境",
        environment=Environment.DEVELOPMENT,
        debug=True,
        host="localhost",
        port=8000,
        cors_origins=["http://localhost:3000", "http://localhost:8080"],
        log_level="DEBUG",
        max_file_size=50 * 1024 * 1024  # 50MB，开发环境较小
    )
    
    # 开发环境数据库配置
    db_config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="rag_dev",
        username="postgres",
        password="dev_password",
        pool_size=5,  # 开发环境较小的连接池
        echo=True,    # 开发环境显示SQL
        ssl_mode="disable"  # 开发环境不需要SSL
    )
    
    # 开发环境存储配置（使用本地MinIO）
    storage_config = StorageConfig(
        provider=StorageProvider.MINIO,
        endpoint_url="http://localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        bucket_name="dev-uploads",
        use_ssl=False,
        verify_ssl=False
    )
    
    # 开发环境Redis配置
    redis_config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        key_prefix="dev:",
        serializer="json",  # 便于调试
        default_ttl=1800,   # 30分钟
        max_connections=10
    )
    
    print(f"应用: {app_config.app_name}")
    print(f"调试模式: {app_config.debug}")
    print(f"数据库: {db_config.build_url()}")
    print(f"存储: {storage_config.provider.value} at {storage_config.endpoint_url}")
    print(f"Redis: {redis_config.host}:{redis_config.port} (prefix: {redis_config.key_prefix})")

async def example_production_setup():
    """生产环境配置示例"""
    print("\n=== 生产环境配置示例 ===")
    
    # 生产环境应用配置
    app_config = AppConfig(
        app_name="RAG知识管理系统",
        environment=Environment.PRODUCTION,
        debug=False,
        host="0.0.0.0",
        port=8080,
        workers=4,
        cors_origins=["https://rag.company.com", "https://api.company.com"],
        secret_key="super-secure-production-key-2024",
        log_level="INFO",
        log_file="/var/log/rag/app.log",
        max_file_size=500 * 1024 * 1024,  # 500MB
        request_timeout=60
    )
    
    # 生产环境数据库配置（高可用集群）
    db_config = DatabaseConfig(
        host="prod-postgres-cluster.internal",
        port=5432,
        database="rag_production",
        username="rag_user",
        password="very-secure-db-password-2024",
        pool_size=20,
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=3600,
        ssl_mode="require",
        ssl_ca="/etc/ssl/certs/postgres-ca.crt",
        application_name="rag-prod"
    )
    
    # 生产环境存储配置（AWS S3）
    storage_config = StorageConfig(
        provider=StorageProvider.AWS_S3,
        region="us-west-2",
        access_key="AKIA_PRODUCTION_KEY",
        secret_key="production_secret_key",
        bucket_name="company-rag-production",
        bucket_prefix="documents/",
        use_ssl=True,
        verify_ssl=True,
        multipart_threshold=128 * 1024 * 1024,  # 128MB
        max_concurrency=20
    )
    
    # 生产环境Redis配置（集群模式）
    redis_config = RedisConfig(
        cluster_enabled=True,
        cluster_nodes=[
            {"host": "redis-1.prod.internal", "port": 7000},
            {"host": "redis-2.prod.internal", "port": 7000},
            {"host": "redis-3.prod.internal", "port": 7000},
            {"host": "redis-4.prod.internal", "port": 7000},
            {"host": "redis-5.prod.internal", "port": 7000},
            {"host": "redis-6.prod.internal", "port": 7000}
        ],
        password="redis-cluster-password-2024",
        key_prefix="prod:",
        serializer="pickle",    # 生产环境使用更高效的序列化
        compress=True,          # 启用压缩节省带宽
        default_ttl=7200,      # 2小时
        max_connections=200
    )
    
    print(f"应用: {app_config.app_name}")
    print(f"工作进程: {app_config.workers}")
    print(f"日志文件: {app_config.log_file}")
    print(f"数据库: {db_config.host} (SSL: {db_config.ssl_mode})")
    print(f"存储: {storage_config.provider.value} in {storage_config.region}")
    print(f"Redis: 集群模式 ({len(redis_config.cluster_nodes)} 节点)")

async def example_config_from_files():
    """从配置文件加载配置示例"""
    print("\n=== 配置文件加载示例 ===")
    
    # 创建示例配置文件
    config_data = {
        "app": {
            "app_name": "RAG系统配置文件版",
            "environment": "staging",
            "host": "0.0.0.0",
            "port": 9000,
            "debug": False,
            "cors_origins": ["https://staging.example.com"],
            "log_level": "INFO"
        },
        "database": {
            "host": "staging-db.example.com",
            "port": 5432,
            "database": "rag_staging",
            "username": "rag_staging_user",
            "password": "staging_password",
            "pool_size": 15,
            "ssl_mode": "require"
        },
        "storage": {
            "provider": "aws_s3",
            "region": "us-east-1",
            "bucket_name": "staging-rag-uploads",
            "access_key": "AKIA_STAGING_KEY",
            "secret_key": "staging_secret"
        },
        "redis": {
            "host": "staging-redis.example.com",
            "port": 6379,
            "db": 1,
            "password": "staging_redis_password",
            "key_prefix": "staging:",
            "default_ttl": 3600,
            "max_connections": 50
        }
    }
    
    # 保存配置文件
    config_file = Path("staging_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    # 从文件加载配置
    with open(config_file, 'r', encoding='utf-8') as f:
        loaded_config = json.load(f)
    
    # 创建配置对象
    app_config = AppConfig(**loaded_config["app"])
    db_config = DatabaseConfig(**loaded_config["database"])
    storage_config = StorageConfig(
        provider=StorageProvider(loaded_config["storage"]["provider"]),
        **{k: v for k, v in loaded_config["storage"].items() if k != "provider"}
    )
    redis_config = RedisConfig(**loaded_config["redis"])
    
    print(f"从文件加载的配置:")
    print(f"  应用: {app_config.app_name} ({app_config.environment.value})")
    print(f"  数据库: {db_config.host}:{db_config.port}")
    print(f"  存储: {storage_config.provider.value} ({storage_config.bucket_name})")
    print(f"  Redis: {redis_config.host} (前缀: {redis_config.key_prefix})")
    
    # 清理示例文件
    config_file.unlink()

async def example_environment_variable_config():
    """环境变量配置示例"""
    print("\n=== 环境变量配置示例 ===")
    
    # 设置示例环境变量
    test_env_vars = {
        "APP_NAME": "环境变量RAG系统",
        "ENVIRONMENT": "testing",
        "DEBUG": "false",
        "HOST": "0.0.0.0", 
        "PORT": "8888",
        "DB_HOST": "env-db.example.com",
        "DB_PORT": "5433",
        "DB_NAME": "env_rag_db",
        "DB_USER": "env_user",
        "DB_PASSWORD": "env_password",
        "STORAGE_PROVIDER": "google_gcs",
        "STORAGE_BUCKET_NAME": "env-rag-bucket",
        "STORAGE_REGION": "us-central1"
    }
    
    # 临时设置环境变量
    original_env = {}
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        # 从环境变量创建配置
        app_config = AppConfig.from_env()
        db_config = DatabaseConfig.from_env()
        storage_config = StorageConfig.from_env()
        
        print(f"环境变量配置:")
        print(f"  应用: {app_config.app_name}")
        print(f"  环境: {app_config.environment.value}")
        print(f"  端口: {app_config.port}")
        print(f"  数据库: {db_config.host}:{db_config.port}/{db_config.database}")
        print(f"  存储: {storage_config.provider.value} ({storage_config.bucket_name})")
        
    finally:
        # 恢复原始环境变量
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

async def example_dynamic_config_update():
    """动态配置更新示例"""
    print("\n=== 动态配置更新示例 ===")
    
    # 创建任务配置管理器
    manager = TaskConfigManager()
    
    # 获取初始Redis配置
    initial_config = manager.get_redis_config()
    print(f"初始Redis配置: {initial_config.host}:{initial_config.port}")
    print(f"初始键前缀: {initial_config.key_prefix}")
    
    # 动态更新Redis配置
    new_redis_config = RedisConfig(
        host="updated-redis.example.com",
        port=6380,
        db=2,
        password="updated_password",
        key_prefix="updated:",
        default_ttl=5400,
        max_connections=150,
        serializer="pickle",
        compress=True
    )
    
    # 更新配置
    success = manager.update_redis_config(new_redis_config)
    
    # 获取更新后的配置
    updated_config = manager.get_redis_config()
    print(f"\n更新后Redis配置: {updated_config.host}:{updated_config.port}")
    print(f"更新后键前缀: {updated_config.key_prefix}")
    print(f"压缩: {updated_config.compress}")
    
    # 生成更新后的Celery配置
    celery_config = manager.get_celery_config()
    print(f"Celery Broker: {celery_config['broker_url']}")
    print(f"序列化器: {celery_config['task_serializer']}")

async def example_config_validation():
    """配置验证示例"""
    print("\n=== 配置验证示例 ===")
    
    # 测试有效配置
    try:
        valid_app_config = AppConfig(
            app_name="有效配置测试",
            environment=Environment.PRODUCTION,
            port=8080,
            workers=4,
            max_file_size=100 * 1024 * 1024
        )
        print(f"✅ 有效应用配置: {valid_app_config.app_name}")
        print(f"   生产环境自动调整: debug={valid_app_config.debug}, docs_url={valid_app_config.docs_url}")
        
    except Exception as e:
        print(f"❌ 应用配置验证失败: {e}")
    
    # 测试数据库URL构建
    try:
        db_config = DatabaseConfig(
            host="test-db.com",
            database="test_db",
            username="test_user",
            password="test@pass#word",  # 包含特殊字符
            ssl_mode="require"
        )
        
        async_url = db_config.build_url(async_driver=True)
        print(f"✅ 数据库URL构建成功: {async_url[:50]}...")
        
    except Exception as e:
        print(f"❌ 数据库配置验证失败: {e}")
    
    # 测试存储提供商验证
    storage_providers = [
        StorageProvider.MINIO,
        StorageProvider.AWS_S3,
        StorageProvider.GOOGLE_GCS,
        StorageProvider.LOCAL
    ]
    
    for provider in storage_providers:
        try:
            storage_config = StorageConfig(
                provider=provider,
                bucket_name=f"test-{provider.value}-bucket"
            )
            params = storage_config.get_connection_params()
            print(f"✅ {provider.value} 存储配置有效: {len(params)} 个参数")
            
        except Exception as e:
            print(f"❌ {provider.value} 存储配置失败: {e}")

async def main():
    """主示例函数"""
    print("🚀 RAG系统配置使用完整示例\n")
    
    await example_development_setup()
    await example_production_setup()
    await example_config_from_files()
    await example_environment_variable_config()
    await example_dynamic_config_update()
    await example_config_validation()
    
    print("\n✨ 配置使用示例完成！")
    
    print("\n📚 配置最佳实践:")
    print("1. 开发环境使用简单配置，便于调试")
    print("2. 生产环境启用安全特性（SSL、认证）")
    print("3. 使用环境变量管理敏感配置")
    print("4. 配置文件用于复杂的结构化配置")
    print("5. 动态配置更新用于运行时调整")
    print("6. 配置验证确保系统稳定性")
    
    print("\n🎯 配置导入方式:")
    print("  from config import default_app_config")
    print("  from config import DatabaseConfig, StorageProvider")
    print("  from config import RedisConfig, config_manager")

if __name__ == "__main__":
    asyncio.run(main())