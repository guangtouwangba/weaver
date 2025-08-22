"""
独立的Redis配置示例

直接使用配置类，避免复杂的模块导入。
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class RedisConfig:
    """Redis配置（简化版用于示例）"""

    # 连接配置
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None

    # 连接池配置
    max_connections: int = 50

    # 超时配置
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True

    # 重试配置
    retry_on_timeout: bool = True

    # SSL配置
    ssl: bool = False
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_cert_reqs: str = "required"
    ssl_ca_certs: Optional[str] = None
    ssl_check_hostname: bool = False

    # 集群配置
    cluster_enabled: bool = False
    cluster_nodes: Optional[List[Dict[str, Any]]] = None
    cluster_require_full_coverage: bool = True

    # 哨兵配置
    sentinel_enabled: bool = False
    sentinel_hosts: Optional[List[Dict[str, Any]]] = None
    sentinel_master_name: str = "mymaster"
    sentinel_socket_timeout: float = 0.1

    # 缓存配置
    default_ttl: int = 3600
    key_prefix: str = "rag:"
    serializer: str = "json"
    compress: bool = False
    compress_threshold: int = 1024

    # 性能配置
    decode_responses: bool = True
    encoding: str = "utf-8"

    # 健康检查配置
    health_check_interval: int = 30


def build_redis_url(config: RedisConfig, db: Optional[int] = None) -> str:
    """构建Redis连接URL"""
    database = db if db is not None else config.db

    if config.password:
        if config.username:
            auth = f"{config.username}:{config.password}"
        else:
            auth = config.password
        url = f"redis://:{auth}@{config.host}:{config.port}/{database}"
    else:
        url = f"redis://{config.host}:{config.port}/{database}"

    if config.ssl:
        url = url.replace("redis://", "rediss://")

    return url


def example_basic_config():
    """基础配置示例"""
    print("=== 基础Redis配置 ===")

    # 默认配置
    config = RedisConfig()
    print(f"默认配置: {config.host}:{config.port}/{config.db}")
    print(f"键前缀: {config.key_prefix}")
    print(f"默认TTL: {config.default_ttl}秒")

    # 自定义配置
    custom_config = RedisConfig(
        host="redis.production.com",
        port=6379,
        db=1,
        password="secure_password_123",
        key_prefix="myapp:",
        default_ttl=7200,
        max_connections=200,
        socket_timeout=3.0,
    )

    print(f"\n自定义配置: {custom_config.host}:{custom_config.port}")
    print(f"认证: {'是' if custom_config.password else '否'}")
    print(f"连接池: {custom_config.max_connections}")


def example_cluster_config():
    """集群配置示例"""
    print("\n=== Redis集群配置 ===")

    cluster_config = RedisConfig(
        cluster_enabled=True,
        cluster_nodes=[
            {"host": "redis-1.cluster.local", "port": 7000},
            {"host": "redis-2.cluster.local", "port": 7000},
            {"host": "redis-3.cluster.local", "port": 7000},
            {"host": "redis-4.cluster.local", "port": 7000},
            {"host": "redis-5.cluster.local", "port": 7000},
            {"host": "redis-6.cluster.local", "port": 7000},
        ],
        cluster_require_full_coverage=True,
        password="cluster_password",
        key_prefix="cluster:",
        default_ttl=3600,
        max_connections=300,
    )

    print(f"集群模式: {'启用' if cluster_config.cluster_enabled else '禁用'}")
    print(f"集群节点: {len(cluster_config.cluster_nodes)}个")
    print(
        f"需要全覆盖: {'是' if cluster_config.cluster_require_full_coverage else '否'}"
    )
    print(f"连接池: {cluster_config.max_connections}")


def example_sentinel_config():
    """哨兵配置示例"""
    print("\n=== Redis哨兵配置 ===")

    sentinel_config = RedisConfig(
        sentinel_enabled=True,
        sentinel_hosts=[
            {"host": "sentinel-1.internal", "port": 26379},
            {"host": "sentinel-2.internal", "port": 26379},
            {"host": "sentinel-3.internal", "port": 26379},
        ],
        sentinel_master_name="production-master",
        sentinel_socket_timeout=0.1,
        username="redis_user",
        password="redis_password",
        db=0,
        key_prefix="sentinel:",
        default_ttl=1800,
    )

    print(f"哨兵模式: {'启用' if sentinel_config.sentinel_enabled else '禁用'}")
    print(f"哨兵节点: {len(sentinel_config.sentinel_hosts)}个")
    print(f"主节点名: {sentinel_config.sentinel_master_name}")
    print(f"Socket超时: {sentinel_config.sentinel_socket_timeout}秒")


def example_ssl_config():
    """SSL配置示例"""
    print("\n=== Redis SSL配置 ===")

    ssl_config = RedisConfig(
        host="secure-redis.example.com",
        port=6380,
        db=0,
        # SSL启用和证书
        ssl=True,
        ssl_keyfile="/etc/ssl/redis/client.key",
        ssl_certfile="/etc/ssl/redis/client.crt",
        ssl_ca_certs="/etc/ssl/redis/ca.crt",
        ssl_cert_reqs="required",
        ssl_check_hostname=True,
        # 认证
        username="ssl_user",
        password="ssl_password",
        # 调整超时（SSL握手需要更多时间）
        socket_timeout=10.0,
        socket_connect_timeout=10.0,
        # 缓存配置
        key_prefix="secure:",
        serializer="json",
        default_ttl=3600,
    )

    print(f"SSL启用: {'是' if ssl_config.ssl else '否'}")
    print(f"证书验证: {ssl_config.ssl_cert_reqs}")
    print(f"主机名检查: {'是' if ssl_config.ssl_check_hostname else '否'}")
    print(f"连接超时: {ssl_config.socket_connect_timeout}秒")


def example_url_building():
    """URL构建示例"""
    print("\n=== Redis URL构建示例 ===")

    # 基础URL
    basic_config = RedisConfig(host="localhost", port=6379, db=0)
    basic_url = build_redis_url(basic_config)
    print(f"基础URL: {basic_url}")

    # 带密码URL
    auth_config = RedisConfig(
        host="redis.example.com", port=6379, db=1, password="mypassword"
    )
    auth_url = build_redis_url(auth_config)
    print(f"认证URL: {auth_url}")

    # 带用户名和密码URL
    user_auth_config = RedisConfig(
        host="redis.example.com", port=6379, db=2, username="myuser", password="mypass"
    )
    user_auth_url = build_redis_url(user_auth_config)
    print(f"用户认证URL: {user_auth_url}")

    # SSL URL
    ssl_config = RedisConfig(
        host="secure-redis.com", port=6380, db=0, ssl=True, password="sslpass"
    )
    ssl_url = build_redis_url(ssl_config)
    print(f"SSL URL: {ssl_url}")


def example_performance_configs():
    """性能优化配置示例"""
    print("\n=== 性能优化配置示例 ===")

    # 高性能配置
    high_perf_config = RedisConfig(
        host="redis-performance.local",
        port=6379,
        db=0,
        # 连接池优化
        max_connections=500,
        socket_keepalive=True,
        # 超时优化
        socket_timeout=2.0,
        socket_connect_timeout=2.0,
        retry_on_timeout=True,
        # 序列化优化
        serializer="pickle",  # 比JSON更快，但不可读
        compress=True,
        compress_threshold=512,  # 压缩阈值
        # 缓存策略
        default_ttl=1800,  # 30分钟
        key_prefix="perf:",
        # 健康检查
        health_check_interval=15,  # 更频繁的健康检查
    )

    print(f"连接池大小: {high_perf_config.max_connections}")
    print(f"序列化器: {high_perf_config.serializer}")
    print(f"数据压缩: {'启用' if high_perf_config.compress else '禁用'}")
    print(f"压缩阈值: {high_perf_config.compress_threshold} bytes")
    print(f"健康检查间隔: {high_perf_config.health_check_interval}秒")


def example_environment_configs():
    """不同环境配置示例"""
    print("\n=== 环境特定配置示例 ===")

    # 开发环境
    dev_config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        key_prefix="dev:",
        default_ttl=3600,
        max_connections=10,
        serializer="json",  # 便于调试
    )

    # 测试环境
    test_config = RedisConfig(
        host="test-redis.internal",
        port=6379,
        db=1,
        key_prefix="test:",
        default_ttl=900,  # 更短的TTL
        max_connections=20,
        serializer="json",
    )

    # 生产环境
    prod_config = RedisConfig(
        host="prod-redis.internal",
        port=6379,
        db=0,
        password="production_secret_2024",
        username="prod_user",
        # SSL安全
        ssl=True,
        ssl_cert_reqs="required",
        # 性能优化
        key_prefix="prod:",
        default_ttl=7200,
        max_connections=500,
        serializer="pickle",
        compress=True,
        # 健壮性配置
        socket_timeout=3.0,
        retry_on_timeout=True,
        health_check_interval=30,
    )

    print("环境配置对比:")
    print(
        f"  开发: {dev_config.host} (连接: {dev_config.max_connections}, TTL: {dev_config.default_ttl}s)"
    )
    print(
        f"  测试: {test_config.host} (连接: {test_config.max_connections}, TTL: {test_config.default_ttl}s)"
    )
    print(
        f"  生产: {prod_config.host} (连接: {prod_config.max_connections}, TTL: {prod_config.default_ttl}s, SSL: {prod_config.ssl})"
    )


def example_config_to_file():
    """配置文件保存示例"""
    print("\n=== 配置文件保存示例 ===")

    config = RedisConfig(
        host="file-config.example.com",
        port=6379,
        db=2,
        password="file_config_password",
        key_prefix="fileconfig:",
        default_ttl=5400,
        max_connections=100,
        serializer="json",
        ssl=False,
        compress=True,
    )

    # 转换为字典
    config_dict = {
        "redis": asdict(config),
        "metadata": {
            "version": "1.0",
            "environment": "example",
            "created_by": "redis_config_example",
        },
    }

    # 保存到JSON文件
    config_file = Path("example_redis_config.json")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)

    print(f"配置已保存到: {config_file}")
    print(f"文件大小: {config_file.stat().st_size} bytes")

    # 从文件读取配置
    with open(config_file, "r", encoding="utf-8") as f:
        loaded_config = json.load(f)

    redis_config = RedisConfig(**loaded_config["redis"])
    print(f"从文件加载: {redis_config.host}:{redis_config.port}")
    print(f"键前缀: {redis_config.key_prefix}")

    # 清理示例文件
    config_file.unlink()
    print("示例文件已清理")


def main():
    """主函数"""
    print("🚀 Redis配置完整示例\n")

    example_basic_config()
    example_cluster_config()
    example_sentinel_config()
    example_ssl_config()
    example_url_building()
    example_performance_configs()
    example_environment_configs()
    example_config_to_file()

    print("\n✨ 所有示例执行完成！")

    print("\n📋 配置要点总结:")
    print("✓ 基础配置：host, port, db, password")
    print("✓ 连接池：max_connections, socket_timeout")
    print("✓ 缓存策略：key_prefix, default_ttl, serializer")
    print("✓ 安全配置：SSL, 用户认证")
    print("✓ 高可用：集群模式, 哨兵模式")
    print("✓ 性能优化：压缩, 序列化器选择")
    print("✓ 环境区分：不同环境使用不同配置")

    print("\n🎯 最佳实践建议:")
    print("1. 开发环境使用简单配置，便于调试")
    print("2. 生产环境启用SSL和认证")
    print("3. 根据负载调整连接池大小")
    print("4. 选择合适的序列化器（JSON vs Pickle）")
    print("5. 设置合理的TTL避免内存泄漏")
    print("6. 使用配置文件管理不同环境")
    print("7. 监控健康状态和性能指标")


if __name__ == "__main__":
    main()
