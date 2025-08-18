"""
Infrastructure configuration management.

Centralized configuration for all infrastructure components including
database, messaging, storage, caching, and monitoring systems.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import timedelta
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')
load_dotenv('.env.middleware')


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "rag_db"
    username: str = "rag_user"
    password: str = "rag_password"
    ssl_mode: str = "prefer"
    
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    
    # Query settings
    echo: bool = False
    statement_timeout: int = 30000  # milliseconds
    
    @property
    def sync_url(self) -> str:
        """Synchronous database connection URL."""
        base_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        if self.ssl_mode != 'prefer':
            base_url += f"?sslmode={self.ssl_mode}"
        return base_url
    
    @property
    def async_url(self) -> str:
        """Asynchronous database connection URL."""
        base_url = f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        if self.ssl_mode != 'prefer':
            base_url += f"?ssl={self.ssl_mode}"
        return base_url
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'rag_db'),
            username=os.getenv('POSTGRES_USER', 'rag_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'rag_password'),
            ssl_mode=os.getenv('POSTGRES_SSL_MODE', 'prefer'),
            pool_size=int(os.getenv('DB_POOL_SIZE', 10)),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 20)),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', 3600)),
            echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
        )


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    ssl: bool = False
    
    # Connection pool settings
    max_connections: int = 10
    retry_on_timeout: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    
    @property
    def url(self) -> str:
        """Redis connection URL."""
        auth = f":{self.password}@" if self.password else ""
        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            database=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', 10))
        )


@dataclass
class MessagingConfig:
    """Messaging system configuration."""
    # Redis-based messaging
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # Message settings
    default_message_ttl: timedelta = field(default_factory=lambda: timedelta(hours=24))
    dead_letter_ttl: timedelta = field(default_factory=lambda: timedelta(days=7))
    max_retries: int = 3
    retry_delay: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    
    # Consumer settings
    max_concurrent_consumers: int = 10
    consumer_timeout: float = 30.0
    
    # Queue settings
    task_queue_prefix: str = "tasks"
    event_queue_prefix: str = "events"
    dlq_prefix: str = "dlq"
    
    @classmethod
    def from_env(cls) -> 'MessagingConfig':
        """Create configuration from environment variables."""
        return cls(
            redis=RedisConfig.from_env(),
            default_message_ttl=timedelta(hours=int(os.getenv('MSG_DEFAULT_TTL_HOURS', 24))),
            dead_letter_ttl=timedelta(days=int(os.getenv('MSG_DLQ_TTL_DAYS', 7))),
            max_retries=int(os.getenv('MSG_MAX_RETRIES', 3)),
            max_concurrent_consumers=int(os.getenv('MSG_MAX_CONCURRENT', 10))
        )


@dataclass
class StorageConfig:
    """Object storage configuration."""
    # MinIO/S3 settings
    endpoint: str = "localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    secure: bool = False
    region: str = "us-east-1"
    
    # Bucket settings
    default_bucket: str = "documents"
    temp_bucket: str = "temp"
    backup_bucket: str = "backups"
    
    # File settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        '.pdf', '.doc', '.docx', '.txt', '.md', '.csv',
        '.jpg', '.jpeg', '.png', '.gif', '.svg',
        '.mp3', '.mp4', '.avi', '.zip', '.tar', '.gz'
    ])
    
    # URL settings
    presigned_url_expiry: timedelta = field(default_factory=lambda: timedelta(hours=1))
    public_url_base: Optional[str] = None
    
    @property
    def minio_config(self) -> Dict[str, Any]:
        """MinIO client configuration."""
        return {
            'endpoint': self.endpoint,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'secure': self.secure,
            'region': self.region
        }
    
    @classmethod
    def from_env(cls) -> 'StorageConfig':
        """Create configuration from environment variables."""
        return cls(
            endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
            secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true',
            region=os.getenv('MINIO_REGION', 'us-east-1'),
            default_bucket=os.getenv('STORAGE_DEFAULT_BUCKET', 'documents'),
            max_file_size=int(os.getenv('STORAGE_MAX_FILE_SIZE', 100 * 1024 * 1024)),
            public_url_base=os.getenv('STORAGE_PUBLIC_URL_BASE')
        )


@dataclass
class CacheConfig:
    """Cache configuration."""
    # Redis settings (reusing Redis config)
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # Cache settings
    default_ttl: timedelta = field(default_factory=lambda: timedelta(hours=1))
    key_prefix: str = "cache"
    serializer: str = "json"  # json, pickle, msgpack
    
    # Cache strategies
    enable_compression: bool = False
    max_key_length: int = 250
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Create configuration from environment variables."""
        return cls(
            redis=RedisConfig.from_env(),
            default_ttl=timedelta(seconds=int(os.getenv('CACHE_DEFAULT_TTL', 3600))),
            key_prefix=os.getenv('CACHE_KEY_PREFIX', 'cache'),
            serializer=os.getenv('CACHE_SERIALIZER', 'json'),
            enable_compression=os.getenv('CACHE_COMPRESSION', 'false').lower() == 'true'
        )


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    # Metrics
    enable_metrics: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # Health checks
    health_check_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    health_check_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=5))
    
    # Alerting
    enable_alerts: bool = False
    alert_webhook_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'MonitoringConfig':
        """Create configuration from environment variables."""
        return cls(
            enable_metrics=os.getenv('MONITORING_ENABLE_METRICS', 'true').lower() == 'true',
            metrics_port=int(os.getenv('MONITORING_METRICS_PORT', 9090)),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_format=os.getenv('LOG_FORMAT', 'json'),
            log_file=os.getenv('LOG_FILE'),
            enable_alerts=os.getenv('MONITORING_ENABLE_ALERTS', 'false').lower() == 'true',
            alert_webhook_url=os.getenv('MONITORING_ALERT_WEBHOOK_URL')
        )


@dataclass
class SecurityConfig:
    """Security configuration."""
    # Encryption
    encryption_key: Optional[str] = None
    encryption_algorithm: str = "AES-256-GCM"
    
    # Authentication
    jwt_secret: Optional[str] = None
    jwt_expiry: timedelta = field(default_factory=lambda: timedelta(hours=24))
    
    # Rate limiting
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 1000
    rate_limit_window: timedelta = field(default_factory=lambda: timedelta(hours=1))
    
    # CORS
    cors_origins: List[str] = field(default_factory=list)
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Create configuration from environment variables."""
        cors_origins = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
        return cls(
            encryption_key=os.getenv('ENCRYPTION_KEY'),
            jwt_secret=os.getenv('JWT_SECRET'),
            enable_rate_limiting=os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true',
            rate_limit_requests=int(os.getenv('RATE_LIMIT_REQUESTS', 1000)),
            cors_origins=[origin.strip() for origin in cors_origins if origin.strip()]
        )


@dataclass
class InfrastructureConfig:
    """Complete infrastructure configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    messaging: MessagingConfig = field(default_factory=MessagingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> 'InfrastructureConfig':
        """Create complete configuration from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            messaging=MessagingConfig.from_env(),
            storage=StorageConfig.from_env(),
            cache=CacheConfig.from_env(),
            monitoring=MonitoringConfig.from_env(),
            security=SecurityConfig.from_env(),
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Validate database
        if not self.database.host:
            errors.append("Database host is required")
        if not self.database.username:
            errors.append("Database username is required")
        if not self.database.password:
            errors.append("Database password is required")
        
        # Validate storage
        if not self.storage.endpoint:
            errors.append("Storage endpoint is required")
        if not self.storage.access_key:
            errors.append("Storage access key is required")
        if not self.storage.secret_key:
            errors.append("Storage secret key is required")
        
        # Validate security in production
        if self.environment == 'production':
            if not self.security.encryption_key:
                errors.append("Encryption key is required in production")
            if not self.security.jwt_secret:
                errors.append("JWT secret is required in production")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        config_dict = {
            'environment': self.environment,
            'debug': self.debug,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'username': self.database.username,
                'pool_size': self.database.pool_size,
                'echo': self.database.echo
            },
            'messaging': {
                'redis_host': self.messaging.redis.host,
                'redis_port': self.messaging.redis.port,
                'max_retries': self.messaging.max_retries,
                'max_concurrent_consumers': self.messaging.max_concurrent_consumers
            },
            'storage': {
                'endpoint': self.storage.endpoint,
                'region': self.storage.region,
                'default_bucket': self.storage.default_bucket,
                'max_file_size': self.storage.max_file_size
            },
            'cache': {
                'redis_host': self.cache.redis.host,
                'redis_port': self.cache.redis.port,
                'serializer': self.cache.serializer,
                'enable_compression': self.cache.enable_compression
            },
            'monitoring': {
                'enable_metrics': self.monitoring.enable_metrics,
                'log_level': self.monitoring.log_level,
                'log_format': self.monitoring.log_format
            }
        }
        return config_dict


# Global configuration instance
def get_config() -> InfrastructureConfig:
    """Get the global infrastructure configuration."""
    return InfrastructureConfig.from_env()


# Configuration validation helper
def validate_config() -> bool:
    """Validate configuration and log any errors."""
    config = get_config()
    errors = config.validate()
    
    if errors:
        for error in errors:
            print(f"Configuration error: {error}")
        return False
    
    return True


# Development configuration override
def get_dev_config() -> InfrastructureConfig:
    """Get development-specific configuration."""
    config = get_config()
    config.debug = True
    config.database.echo = True
    config.monitoring.log_level = "DEBUG"
    return config


# Test configuration override
def get_test_config() -> InfrastructureConfig:
    """Get test-specific configuration."""
    config = get_config()
    config.environment = "test"
    config.database.database = f"{config.database.database}_test"
    config.storage.default_bucket = f"{config.storage.default_bucket}-test"
    config.cache.key_prefix = f"{config.cache.key_prefix}-test"
    return config