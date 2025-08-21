"""
应用程序配置模块

提供整个RAG知识管理系统的应用级配置。
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class Environment(Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class AppConfig:
    """应用程序配置"""
    # 基础配置
    app_name: str = "RAG Knowledge Management System"
    version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # 安全配置
    secret_key: str = "your-secret-key-here"
    allowed_hosts: List[str] = None
    cors_origins: List[str] = None
    cors_credentials: bool = True
    cors_methods: List[str] = None
    cors_headers: List[str] = None
    
    # API配置
    api_prefix: str = "/api/v1"
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    openapi_url: Optional[str] = "/openapi.json"
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    
    # 性能配置
    request_timeout: int = 30
    keepalive_timeout: int = 5
    max_request_size: int = 100 * 1024 * 1024  # 100MB
    
    # 监控配置
    enable_metrics: bool = True
    metrics_path: str = "/metrics"
    health_check_path: str = "/health"
    
    # 文件处理配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = None
    upload_timeout: int = 300  # 5分钟
    
    # RAG配置
    default_chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_document: int = 1000
    
    def __post_init__(self):
        """初始化后处理"""
        if self.allowed_hosts is None:
            if self.environment == Environment.DEVELOPMENT:
                self.allowed_hosts = ["*"]
            else:
                self.allowed_hosts = []
        
        if self.cors_origins is None:
            if self.environment == Environment.DEVELOPMENT:
                self.cors_origins = ["*"]
            else:
                self.cors_origins = []
        
        if self.cors_methods is None:
            self.cors_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        
        if self.cors_headers is None:
            self.cors_headers = ["*"]
        
        if self.allowed_file_types is None:
            self.allowed_file_types = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "text/markdown",
                "text/html",
                "text/csv",
                "application/json"
            ]
        
        # 根据环境调整配置
        if self.environment == Environment.PRODUCTION:
            self.debug = False
            self.docs_url = None
            self.redoc_url = None
            self.openapi_url = None
        elif self.environment == Environment.DEVELOPMENT:
            self.debug = True
    
    def get_cors_config(self) -> Dict[str, Any]:
        """获取CORS配置"""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_credentials,
            "allow_methods": self.cors_methods,
            "allow_headers": self.cors_headers
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": self.log_format,
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": self.log_level
                }
            },
            "root": {
                "level": self.log_level,
                "handlers": ["console"]
            }
        }
        
        # 添加文件日志处理器
        if self.log_file:
            config["handlers"]["file"] = {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": self.log_file,
                "when": "D",
                "interval": 1,
                "backupCount": 30,
                "formatter": "json" if self.environment == Environment.PRODUCTION else "default",
                "level": self.log_level
            }
            config["root"]["handlers"].append("file")
        
        return config
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """从环境变量创建配置"""
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        try:
            environment = Environment(env_str)
        except ValueError:
            environment = Environment.DEVELOPMENT
        
        # 处理列表类型的环境变量
        def parse_list(env_var: str, default: List[str] = None) -> List[str]:
            value = os.getenv(env_var)
            if value:
                return [item.strip() for item in value.split(",")]
            return default or []
        
        return cls(
            app_name=os.getenv("APP_NAME", "RAG Knowledge Management System"),
            version=os.getenv("APP_VERSION", "1.0.0"),
            environment=environment,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            workers=int(os.getenv("WORKERS", "1")),
            
            secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"),
            allowed_hosts=parse_list("ALLOWED_HOSTS"),
            cors_origins=parse_list("CORS_ORIGINS"),
            cors_credentials=os.getenv("CORS_CREDENTIALS", "true").lower() == "true",
            cors_methods=parse_list("CORS_METHODS"),
            cors_headers=parse_list("CORS_HEADERS"),
            
            api_prefix=os.getenv("API_PREFIX", "/api/v1"),
            docs_url=os.getenv("DOCS_URL", "/docs"),
            redoc_url=os.getenv("REDOC_URL", "/redoc"),
            openapi_url=os.getenv("OPENAPI_URL", "/openapi.json"),
            
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_file=os.getenv("LOG_FILE"),
            log_rotation=os.getenv("LOG_ROTATION", "1 day"),
            log_retention=os.getenv("LOG_RETENTION", "30 days"),
            
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            keepalive_timeout=int(os.getenv("KEEPALIVE_TIMEOUT", "5")),
            max_request_size=int(os.getenv("MAX_REQUEST_SIZE", str(100 * 1024 * 1024))),
            
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            metrics_path=os.getenv("METRICS_PATH", "/metrics"),
            health_check_path=os.getenv("HEALTH_CHECK_PATH", "/health"),
            
            max_file_size=int(os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024))),
            allowed_file_types=parse_list("ALLOWED_FILE_TYPES"),
            upload_timeout=int(os.getenv("UPLOAD_TIMEOUT", "300")),
            
            default_chunk_size=int(os.getenv("DEFAULT_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            max_chunks_per_document=int(os.getenv("MAX_CHUNKS_PER_DOCUMENT", "1000"))
        )
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == Environment.DEVELOPMENT

# 默认应用配置实例
default_app_config = AppConfig.from_env()