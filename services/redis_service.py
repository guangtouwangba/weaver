"""
Redis服务实现

提供统一的Redis连接管理和操作接口，支持单实例、集群、哨兵等多种部署模式。
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Union, List
from abc import ABC, abstractmethod
import json
import pickle
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError, ConnectionError, TimeoutError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

from config import RedisConfig, get_config

logger = logging.getLogger(__name__)

class IRedisService(ABC):
    """Redis服务接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取键值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置键值"""
        pass
    
    @abstractmethod
    async def delete(self, *keys: str) -> int:
        """删除键"""
        pass
    
    @abstractmethod
    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """设置键过期时间"""
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> int:
        """获取键剩余存活时间"""
        pass
    
    @abstractmethod
    async def incr(self, key: str, amount: int = 1) -> int:
        """递增"""
        pass
    
    @abstractmethod
    async def decr(self, key: str, amount: int = 1) -> int:
        """递减"""
        pass
    
    @abstractmethod
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希字段值"""
        pass
    
    @abstractmethod
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """设置哈希字段值"""
        pass
    
    @abstractmethod
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希所有字段"""
        pass
    
    @abstractmethod
    async def lpush(self, name: str, *values: Any) -> int:
        """列表左侧推入"""
        pass
    
    @abstractmethod
    async def rpush(self, name: str, *values: Any) -> int:
        """列表右侧推入"""
        pass
    
    @abstractmethod
    async def lpop(self, name: str) -> Optional[Any]:
        """列表左侧弹出"""
        pass
    
    @abstractmethod
    async def rpop(self, name: str) -> Optional[Any]:
        """列表右侧弹出"""
        pass
    
    @abstractmethod
    async def llen(self, name: str) -> int:
        """获取列表长度"""
        pass
    
    @abstractmethod
    async def lrange(self, name: str, start: int, end: int) -> List[Any]:
        """获取列表范围"""
        pass
    
    @abstractmethod
    async def sadd(self, name: str, *values: Any) -> int:
        """集合添加元素"""
        pass
    
    @abstractmethod
    async def srem(self, name: str, *values: Any) -> int:
        """集合移除元素"""
        pass
    
    @abstractmethod
    async def scard(self, name: str) -> int:
        """获取集合大小"""
        pass
    
    @abstractmethod
    async def smembers(self, name: str) -> set:
        """获取集合所有成员"""
        pass
    
    @abstractmethod
    async def ping(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    async def flushdb(self) -> bool:
        """清空当前数据库"""
        pass

class RedisService(IRedisService):
    """Redis服务实现"""
    
    def __init__(self, config: Optional[RedisConfig] = None):
        """
        初始化Redis服务
        
        Args:
            config: Redis配置，如果不提供则使用全局配置管理器
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not available. Please install redis: pip install redis")
        
        self.config = config or get_config().redis
        self.client: Optional[redis.Redis] = None
        self.cluster_client: Optional[redis.RedisCluster] = None
        self.sentinel_client: Optional[redis.Sentinel] = None
        self._is_cluster = False
        self._is_sentinel = False
        self._connected = False
    
    async def _get_client(self) -> Union[redis.Redis, redis.RedisCluster]:
        """获取Redis客户端"""
        if not self._connected:
            await self._connect()
        
        if self._is_cluster:
            return self.cluster_client
        elif self._is_sentinel:
            return self.sentinel_client.master_for(self.config.sentinel_master_name)
        else:
            return self.client
    
    async def _connect(self):
        """建立Redis连接"""
        try:
            if self.config.cluster_enabled:
                await self._connect_cluster()
            elif self.config.sentinel_enabled:
                await self._connect_sentinel()
            else:
                await self._connect_single()
            
            self._connected = True
            logger.info("Redis连接建立成功")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    async def _connect_single(self):
        """连接单实例Redis"""
        connection_params = self._get_redis_connection_params()
        self.client = redis.Redis(**connection_params)
        
        # 测试连接
        await self.client.ping()
    
    async def _connect_cluster(self):
        """连接Redis集群"""
        cluster_config = self._build_redis_cluster_config()
        if not cluster_config:
            raise ValueError("Redis集群配置无效")
        
        self.cluster_client = redis.RedisCluster(**cluster_config)
        self._is_cluster = True
        
        # 测试连接
        await self.cluster_client.ping()
    
    async def _connect_sentinel(self):
        """连接Redis哨兵"""
        sentinel_config = self._build_redis_sentinel_config()
        if not sentinel_config:
            raise ValueError("Redis哨兵配置无效")
        
        self.sentinel_client = redis.Sentinel(
            sentinel_config["sentinels"],
            socket_timeout=sentinel_config["socket_timeout"]
        )
        self._is_sentinel = True
        
        # 测试连接
        master = self.sentinel_client.master_for(sentinel_config["service_name"])
        await master.ping()
    
    def _get_redis_connection_params(self) -> Dict[str, Any]:
        """获取Redis连接参数字典"""
        params = {
            "host": self.config.host,
            "port": self.config.port,
            "db": self.config.db,
            "decode_responses": self.config.decode_responses,
            "encoding": self.config.encoding,
            "encoding_errors": self.config.encoding_errors,
            "socket_timeout": self.config.socket_timeout,
            "socket_connect_timeout": self.config.socket_connect_timeout,
            "socket_keepalive": self.config.socket_keepalive,
            "retry_on_timeout": self.config.retry_on_timeout,
            "max_connections": self.config.max_connections,
            "health_check_interval": self.config.health_check_interval,
        }
        
        # 添加认证信息
        if self.config.password:
            params["password"] = self.config.password
        if self.config.username:
            params["username"] = self.config.username
        
        # 添加SSL配置
        if self.config.ssl:
            params["ssl"] = True
            if self.config.ssl_keyfile:
                params["ssl_keyfile"] = self.config.ssl_keyfile
            if self.config.ssl_certfile:
                params["ssl_certfile"] = self.config.ssl_certfile
            if self.config.ssl_ca_certs:
                params["ssl_ca_certs"] = self.config.ssl_ca_certs
            params["ssl_cert_reqs"] = self.config.ssl_cert_reqs
            params["ssl_check_hostname"] = self.config.ssl_check_hostname
        
        return params
    
    def _build_redis_cluster_config(self) -> Optional[Dict[str, Any]]:
        """构建Redis集群配置"""
        if not self.config.cluster_enabled:
            return None
        
        return {
            "startup_nodes": getattr(self.config, 'cluster_nodes', []),
            "decode_responses": self.config.decode_responses,
            "socket_timeout": self.config.socket_timeout,
            "socket_connect_timeout": self.config.socket_connect_timeout,
            "retry_on_timeout": self.config.retry_on_timeout,
            "password": self.config.password,
            "username": self.config.username,
        }
    
    def _build_redis_sentinel_config(self) -> Optional[Dict[str, Any]]:
        """构建Redis哨兵配置"""
        if not self.config.sentinel_enabled:
            return None
        
        return {
            "sentinels": getattr(self.config, 'sentinel_hosts', []),
            "service_name": getattr(self.config, 'sentinel_master_name', 'mymaster'),
            "socket_timeout": getattr(self.config, 'sentinel_socket_timeout', 0.1),
            "password": self.config.password,
            "username": self.config.username,
            "db": self.config.db,
            "decode_responses": self.config.decode_responses,
        }
    
    def _serialize(self, value: Any) -> Union[str, bytes]:
        """序列化数据"""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        
        serializer = self.config.serializer.lower()
        
        if serializer == "json":
            return json.dumps(value, ensure_ascii=False)
        elif serializer == "pickle":
            return pickle.dumps(value)
        elif serializer == "msgpack":
            if not MSGPACK_AVAILABLE:
                raise ImportError("msgpack not available. Please install msgpack: pip install msgpack")
            return msgpack.packb(value)
        else:
            raise ValueError(f"不支持的序列化方式: {serializer}")
    
    def _deserialize(self, value: Union[str, bytes]) -> Any:
        """反序列化数据"""
        if value is None:
            return None
        
        serializer = self.config.serializer.lower()
        
        if serializer == "json":
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        elif serializer == "pickle":
            try:
                return pickle.loads(value)
            except (pickle.PickleError, TypeError):
                return value
        elif serializer == "msgpack":
            if not MSGPACK_AVAILABLE:
                raise ImportError("msgpack not available. Please install msgpack: pip install msgpack")
            try:
                return msgpack.unpackb(value, raw=False)
            except (msgpack.exceptions.ExtraData, TypeError):
                return value
        else:
            return value
    
    def _build_key(self, key: str) -> str:
        """构建完整的键名"""
        return f"{self.config.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取键值"""
        try:
            client = await self._get_client()
            full_key = self._build_key(key)
            value = await client.get(full_key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Redis GET失败 {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置键值"""
        try:
            client = await self._get_client()
            full_key = self._build_key(key)
            serialized_value = self._serialize(value)
            
            expire_time = ttl or self.config.default_ttl
            result = await client.set(full_key, serialized_value, ex=expire_time)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET失败 {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """删除键"""
        try:
            client = await self._get_client()
            full_keys = [self._build_key(key) for key in keys]
            return await client.delete(*full_keys)
        except Exception as e:
            logger.error(f"Redis DELETE失败 {keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        try:
            client = await self._get_client()
            full_keys = [self._build_key(key) for key in keys]
            return await client.exists(*full_keys)
        except Exception as e:
            logger.error(f"Redis EXISTS失败 {keys}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置键过期时间"""
        try:
            client = await self._get_client()
            full_key = self._build_key(key)
            return bool(await client.expire(full_key, ttl))
        except Exception as e:
            logger.error(f"Redis EXPIRE失败 {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键剩余存活时间"""
        try:
            client = await self._get_client()
            full_key = self._build_key(key)
            return await client.ttl(full_key)
        except Exception as e:
            logger.error(f"Redis TTL失败 {key}: {e}")
            return -1
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """递增"""
        try:
            client = await self._get_client()
            full_key = self._build_key(key)
            return await client.incr(full_key, amount)
        except Exception as e:
            logger.error(f"Redis INCR失败 {key}: {e}")
            return 0
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """递减"""
        try:
            client = await self._get_client()
            full_key = self._build_key(key)
            return await client.decr(full_key, amount)
        except Exception as e:
            logger.error(f"Redis DECR失败 {key}: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希字段值"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            value = await client.hget(full_name, key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Redis HGET失败 {name}.{key}: {e}")
            return None
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """设置哈希字段值"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            serialized_value = self._serialize(value)
            result = await client.hset(full_name, key, serialized_value)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis HSET失败 {name}.{key}: {e}")
            return False
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希所有字段"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            data = await client.hgetall(full_name)
            return {k.decode() if isinstance(k, bytes) else k: 
                   self._deserialize(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Redis HGETALL失败 {name}: {e}")
            return {}
    
    async def lpush(self, name: str, *values: Any) -> int:
        """列表左侧推入"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            serialized_values = [self._serialize(v) for v in values]
            return await client.lpush(full_name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis LPUSH失败 {name}: {e}")
            return 0
    
    async def rpush(self, name: str, *values: Any) -> int:
        """列表右侧推入"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            serialized_values = [self._serialize(v) for v in values]
            return await client.rpush(full_name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis RPUSH失败 {name}: {e}")
            return 0
    
    async def lpop(self, name: str) -> Optional[Any]:
        """列表左侧弹出"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            value = await client.lpop(full_name)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Redis LPOP失败 {name}: {e}")
            return None
    
    async def rpop(self, name: str) -> Optional[Any]:
        """列表右侧弹出"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            value = await client.rpop(full_name)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Redis RPOP失败 {name}: {e}")
            return None
    
    async def llen(self, name: str) -> int:
        """获取列表长度"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            return await client.llen(full_name)
        except Exception as e:
            logger.error(f"Redis LLEN失败 {name}: {e}")
            return 0
    
    async def lrange(self, name: str, start: int, end: int) -> List[Any]:
        """获取列表范围"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            values = await client.lrange(full_name, start, end)
            return [self._deserialize(v) for v in values]
        except Exception as e:
            logger.error(f"Redis LRANGE失败 {name}: {e}")
            return []
    
    async def sadd(self, name: str, *values: Any) -> int:
        """集合添加元素"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            serialized_values = [self._serialize(v) for v in values]
            return await client.sadd(full_name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis SADD失败 {name}: {e}")
            return 0
    
    async def srem(self, name: str, *values: Any) -> int:
        """集合移除元素"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            serialized_values = [self._serialize(v) for v in values]
            return await client.srem(full_name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis SREM失败 {name}: {e}")
            return 0
    
    async def scard(self, name: str) -> int:
        """获取集合大小"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            return await client.scard(full_name)
        except Exception as e:
            logger.error(f"Redis SCARD失败 {name}: {e}")
            return 0
    
    async def smembers(self, name: str) -> set:
        """获取集合所有成员"""
        try:
            client = await self._get_client()
            full_name = self._build_key(name)
            values = await client.smembers(full_name)
            return {self._deserialize(v) for v in values}
        except Exception as e:
            logger.error(f"Redis SMEMBERS失败 {name}: {e}")
            return set()
    
    async def ping(self) -> bool:
        """健康检查"""
        try:
            client = await self._get_client()
            result = await client.ping()
            return bool(result)
        except Exception as e:
            logger.error(f"Redis PING失败: {e}")
            return False
    
    async def flushdb(self) -> bool:
        """清空当前数据库"""
        try:
            client = await self._get_client()
            result = await client.flushdb()
            return bool(result)
        except Exception as e:
            logger.error(f"Redis FLUSHDB失败: {e}")
            return False
    
    async def close(self):
        """关闭连接"""
        try:
            if self.client:
                await self.client.close()
            if self.cluster_client:
                await self.cluster_client.close()
            if self.sentinel_client:
                # 哨兵客户端通常不需要显式关闭
                pass
            
            self._connected = False
            logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器进入"""
        if not self._connected:
            await self._connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

# 全局Redis服务实例
redis_service = RedisService()