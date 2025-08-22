"""
Configuration Usage Examples

Demonstrates how to use the unified configuration structure in the RAG knowledge management system.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from pathlib import Path
import json

# Import unified configuration system
from config import (
    AppConfig,
    Environment,
    DatabaseConfig,
    StorageConfig,
    StorageProvider,
    RedisConfig,
    get_config,
)


async def example_development_setup():
    """Development environment configuration example"""
    print("=== Development Environment Configuration Example ===")

    # Development environment application configuration
    app_config = AppConfig(
        app_name="RAG Development Environment",
        environment=Environment.DEVELOPMENT,
        debug=True,
        host="localhost",
        port=8000,
        cors_origins=["http://localhost:3000", "http://localhost:8080"],
        log_level="DEBUG",
        max_file_size=50 * 1024 * 1024,  # 50MB, smaller for dev environment
    )

    # Development environment database configuration
    db_config = DatabaseConfig(
        host="localhost",
        port=5432,
        name="rag_dev",
        user="postgres",
        password="dev_password",
        pool_size=5,  # Smaller connection pool for dev
        echo=True,  # Show SQL in development
        ssl_mode="disable",  # No SSL needed in development
    )

    # Development environment storage configuration (using local MinIO)
    storage_config = StorageConfig(
        provider=StorageProvider.MINIO,
        endpoint_url="http://localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        bucket_name="dev-uploads",
        use_ssl=False,
        verify_ssl=False,
    )

    # Development environment Redis configuration
    redis_config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        key_prefix="dev:",
        serializer="json",  # Easier for debugging
        default_ttl=1800,  # 30 minutes
        max_connections=10,
    )

    print(f"Application: {app_config.app_name}")
    print(f"Debug mode: {app_config.debug}")
    print(f"Database: {db_config.url}")
    print(
        f"Storage: {storage_config.provider} at {getattr(storage_config, 'endpoint_url', 'N/A')}"
    )
    print(
        f"Redis: {redis_config.host}:{redis_config.port} (prefix: {redis_config.key_prefix})"
    )


async def example_production_setup():
    """Production environment configuration example"""
    print("\n=== Production Environment Configuration Example ===")

    # Production environment application configuration
    app_config = AppConfig(
        app_name="RAG Knowledge Management System",
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
        request_timeout=60,
    )

    # Production environment database configuration (high availability cluster)
    db_config = DatabaseConfig(
        host="prod-postgres-cluster.internal",
        port=5432,
        name="rag_production",
        user="rag_user",
        password="very-secure-db-password-2024",
        pool_size=20,
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=3600,
        ssl_mode="require",
        ssl_ca="/etc/ssl/certs/postgres-ca.crt",
        application_name="rag-prod",
    )

    # Production environment storage configuration (AWS S3)
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
        max_concurrency=20,
    )

    # Production environment Redis configuration (cluster mode)
    redis_config = RedisConfig(
        cluster_enabled=True,
        cluster_nodes=[
            {"host": "redis-1.prod.internal", "port": 7000},
            {"host": "redis-2.prod.internal", "port": 7000},
            {"host": "redis-3.prod.internal", "port": 7000},
            {"host": "redis-4.prod.internal", "port": 7000},
            {"host": "redis-5.prod.internal", "port": 7000},
            {"host": "redis-6.prod.internal", "port": 7000},
        ],
        password="redis-cluster-password-2024",
        key_prefix="prod:",
        serializer="pickle",  # More efficient serialization for production
        compress=True,  # Enable compression to save bandwidth
        default_ttl=7200,  # 2 hours
        max_connections=200,
    )

    print(f"Application: {app_config.app_name}")
    print(f"Workers: {app_config.workers}")
    print(f"Log file: {app_config.log_file}")
    print(f"Database: {db_config.host} (SSL: {db_config.ssl_mode})")
    print(f"Storage: {storage_config.provider.value} in {storage_config.region}")
    print(f"Redis: Cluster mode ({len(redis_config.cluster_nodes)} nodes)")


async def example_config_from_files():
    """Load configuration from files example"""
    print("\n=== Configuration File Loading Example ===")

    # Create example configuration file
    config_data = {
        "app": {
            "app_name": "RAG System Configuration File Version",
            "environment": "staging",
            "host": "0.0.0.0",
            "port": 9000,
            "debug": False,
            "cors_origins": ["https://staging.example.com"],
            "log_level": "INFO",
        },
        "database": {
            "host": "staging-db.example.com",
            "port": 5432,
            "name": "rag_staging",
            "user": "rag_staging_user",
            "password": "staging_password",
            "pool_size": 15,
            "ssl_mode": "require",
        },
        "storage": {
            "provider": "aws_s3",
            "region": "us-east-1",
            "bucket_name": "staging-rag-uploads",
            "access_key": "AKIA_STAGING_KEY",
            "secret_key": "staging_secret",
        },
        "redis": {
            "host": "staging-redis.example.com",
            "port": 6379,
            "db": 1,
            "password": "staging_redis_password",
            "key_prefix": "staging:",
            "default_ttl": 3600,
            "max_connections": 50,
        },
    }

    # Save configuration file
    config_file = Path("staging_config.json")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    # Load configuration from file
    with open(config_file, "r", encoding="utf-8") as f:
        loaded_config = json.load(f)

    # Create configuration objects
    app_config = AppConfig(**loaded_config["app"])
    db_config = DatabaseConfig(**loaded_config["database"])
    storage_config = StorageConfig(
        provider=StorageProvider(loaded_config["storage"]["provider"]),
        **{k: v for k, v in loaded_config["storage"].items() if k != "provider"},
    )
    redis_config = RedisConfig(**loaded_config["redis"])

    print(f"Configuration loaded from file:")
    print(f"  Application: {app_config.app_name} ({app_config.environment.value})")
    print(f"  Database: {db_config.host}:{db_config.port}")
    print(f"  Storage: {storage_config.provider.value} ({storage_config.bucket_name})")
    print(f"  Redis: {redis_config.host} (prefix: {redis_config.key_prefix})")

    # Clean up example file
    config_file.unlink()


async def example_environment_variable_config():
    """Environment variable configuration example"""
    print("\n=== Environment Variable Configuration Example ===")

    # Set example environment variables
    test_env_vars = {
        "APP_NAME": "Environment Variable RAG System",
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
        "STORAGE_REGION": "us-central1",
    }

    # Temporarily set environment variables
    original_env = {}
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        # Create configuration from environment variables
        app_config = get_config()

        print(f"Environment variable configuration:")
        print(f"  Application: {app_config.app_name}")
        print(f"  Environment: {app_config.environment.value}")
        print(f"  Port: {app_config.port}")
        print(
            f"  Database: {app_config.database.host}:{app_config.database.port}/{app_config.database.name}"
        )
        print(
            f"  Storage: {app_config.storage.provider} ({getattr(app_config.storage, 'bucket_name', 'N/A')})"
        )

    finally:
        # Restore original environment variables
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


async def example_dynamic_config_update():
    """Dynamic configuration update example"""
    print("\n=== Dynamic Configuration Update Example ===")

    # Get current configuration
    config = get_config()

    # Show initial Redis configuration
    initial_redis_config = config.redis
    print(
        f"Initial Redis config: {initial_redis_config.host}:{initial_redis_config.port}"
    )
    print(f"Initial key prefix: {initial_redis_config.key_prefix}")

    # Create new Redis configuration
    new_redis_config = RedisConfig(
        host="updated-redis.example.com",
        port=6380,
        db=2,
        password="updated_password",
        key_prefix="updated:",
        default_ttl=5400,
        max_connections=150,
        serializer="pickle",
        compress=True,
    )

    print(f"\nNew Redis config: {new_redis_config.host}:{new_redis_config.port}")
    print(f"New key prefix: {new_redis_config.key_prefix}")
    print(f"Compression: {new_redis_config.compress}")

    # Show Celery configuration
    celery_config = config.celery
    print(f"Celery Broker: {celery_config.broker_url}")
    print(f"Serializer: {celery_config.task_serializer}")


async def example_config_validation():
    """Configuration validation example"""
    print("\n=== Configuration Validation Example ===")

    # Test valid configuration
    try:
        valid_app_config = AppConfig(
            app_name="Valid Configuration Test",
            environment=Environment.PRODUCTION,
            port=8080,
            workers=4,
            max_file_size=100 * 1024 * 1024,
        )
        print(f"✅ Valid application config: {valid_app_config.app_name}")
        print(
            f"   Production auto-adjustment: debug={valid_app_config.debug}, docs_url={valid_app_config.docs_url}"
        )

    except Exception as e:
        print(f"❌ Application config validation failed: {e}")

    # Test database URL construction
    try:
        db_config = DatabaseConfig(
            host="test-db.com",
            name="test_db",
            user="test_user",
            password="test@pass#word",  # Contains special characters
        )

        async_url = db_config.url
        print(f"✅ Database URL construction successful: {async_url[:50]}...")

    except Exception as e:
        print(f"❌ Database config validation failed: {e}")

    # Test storage provider validation
    storage_providers = [
        StorageProvider.MINIO,
        StorageProvider.AWS_S3,
        StorageProvider.GOOGLE_GCS,
        StorageProvider.LOCAL,
    ]

    for provider in storage_providers:
        try:
            storage_config = StorageConfig(
                provider=provider, bucket_name=f"test-{provider.value}-bucket"
            )
            params = storage_config.get_connection_params()
            print(f"✅ {provider.value} storage config valid: {len(params)} parameters")

        except Exception as e:
            print(f"❌ {provider.value} storage config failed: {e}")


async def main():
    """Main example function"""
    print("🚀 RAG System Complete Configuration Usage Examples\n")

    await example_development_setup()
    await example_production_setup()
    await example_config_from_files()
    await example_environment_variable_config()
    await example_dynamic_config_update()
    await example_config_validation()

    print("\n✨ Configuration usage examples completed!")

    print("\n📚 Configuration best practices:")
    print("1. Use simple configuration for development environment, easy for debugging")
    print("2. Enable security features in production (SSL, authentication)")
    print("3. Use environment variables to manage sensitive configuration")
    print("4. Use configuration files for complex structured configuration")
    print("5. Dynamic configuration updates for runtime adjustments")
    print("6. Configuration validation ensures system stability")

    print("\n🎯 Configuration import methods:")
    print("  from config import get_config")
    print("  from config import DatabaseConfig, StorageProvider")
    print("  from config import RedisConfig, AppConfig")


if __name__ == "__main__":
    asyncio.run(main())
