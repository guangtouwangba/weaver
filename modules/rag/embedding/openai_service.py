"""
OpenAI嵌入服务实现

使用OpenAI API生成文本嵌入向量。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import openai
from openai import AsyncOpenAI

from modules.rag.embedding.base import (
    EmbeddingConfig,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingResult,
    IEmbeddingService,
)

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(IEmbeddingService):
    """OpenAI嵌入服务实现"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        max_batch_size: int = 100,
        max_retries: int = 3,
        request_timeout: int = 30,
    ):
        self.api_key = api_key
        self.model = model
        self.max_batch_size = max_batch_size
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        
        self._client: Optional[AsyncOpenAI] = None
        self._initialized = False
        
        # 模型配置
        self._model_configs = {
            "text-embedding-3-small": {"dimension": 1536, "max_tokens": 8192},
            "text-embedding-3-large": {"dimension": 3072, "max_tokens": 8192},
            "text-embedding-ada-002": {"dimension": 1536, "max_tokens": 8192},
        }
        
        self._config = EmbeddingConfig(
            provider=EmbeddingProvider.OPENAI,
            model_name=model,
            dimension=self._model_configs.get(model, {}).get("dimension", 1536),
            max_tokens=self._model_configs.get(model, {}).get("max_tokens", 8192),
            batch_size=max_batch_size,
        )
        
        logger.info(f"OpenAI嵌入服务初始化: 模型={model}, 维度={self._config.dimension}")
    
    async def initialize(self) -> None:
        """初始化嵌入服务"""
        if self._initialized:
            return
        
        try:
            # 创建异步客户端
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=self.request_timeout,
            )
            
            # 测试连接
            await self._test_connection()
            
            self._initialized = True
            logger.info("OpenAI嵌入服务初始化完成")
            
        except Exception as e:
            logger.error(f"OpenAI嵌入服务初始化失败: {e}")
            raise EmbeddingError(
                f"初始化失败: {e}",
                provider="openai",
                error_code="INITIALIZATION_FAILED"
            )
    
    async def cleanup(self) -> None:
        """清理嵌入服务资源"""
        if self._client:
            await self._client.close()
            self._client = None
        self._initialized = False
        logger.info("OpenAI嵌入服务资源已清理")
    
    async def generate_embeddings(self, texts: List[str]) -> EmbeddingResult:
        """
        生成文本嵌入向量
        
        Args:
            texts: 待嵌入的文本列表
            
        Returns:
            EmbeddingResult: 嵌入结果
        """
        if not self._initialized:
            raise EmbeddingError("服务未初始化", provider="openai")
        
        if not texts:
            return EmbeddingResult(
                vectors=[],
                texts=[],
                model_name=self.model,
                dimension=self.config.dimension,
                processing_time_ms=0.0,
                metadata={'usage': {'prompt_tokens': 0, 'total_tokens': 0}}
            )
        
        start_time = time.time()
        
        try:
            # 文本预处理
            processed_texts = self._preprocess_texts(texts)
            
            # 批量处理
            all_embeddings = []
            total_usage = {'prompt_tokens': 0, 'total_tokens': 0}
            
            for i in range(0, len(processed_texts), self.max_batch_size):
                batch_texts = processed_texts[i:i + self.max_batch_size]
                
                # 生成当前批次的嵌入
                batch_embeddings, batch_usage = await self._generate_batch_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
                
                # 累计使用统计
                for key in batch_usage:
                    total_usage[key] = total_usage.get(key, 0) + batch_usage.get(key, 0)
                
                # 速率限制
                if i + self.max_batch_size < len(processed_texts):
                    await asyncio.sleep(0.1)  # 避免触发速率限制
            
            processing_time = (time.time() - start_time) * 1000
            
            # 计算嵌入维度
            dimension = len(all_embeddings[0]) if all_embeddings else self.config.dimension
            
            result = EmbeddingResult(
                vectors=all_embeddings,
                texts=processed_texts,
                model_name=self.model,
                dimension=dimension,
                processing_time_ms=processing_time,
                metadata={'usage': total_usage}
            )
            
            logger.info(
                f"生成嵌入完成: {len(texts)} 文本, "
                f"耗时 {processing_time:.1f}ms, "
                f"tokens: {total_usage.get('total_tokens', 0)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")
            raise EmbeddingError(
                f"生成嵌入失败: {e}",
                provider="openai",
                error_code="GENERATION_FAILED"
            )
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 待嵌入的文本
            
        Returns:
            List[float]: 嵌入向量
        """
        result = await self.generate_embeddings([text])
        if not result.vectors:
            raise EmbeddingError("未能生成嵌入向量", provider="openai")
        return result.vectors[0]
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量 (别名方法)
        
        Args:
            text: 待嵌入的文本
            
        Returns:
            List[float]: 嵌入向量
        """
        return await self.generate_single_embedding(text)
    
    async def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self._config.dimension
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "service": "openai_embedding",
            "status": "healthy" if self._initialized else "not_initialized",
            "model": self.model,
            "dimension": self._config.dimension,
            "max_batch_size": self.max_batch_size,
        }
        
        if self._initialized:
            try:
                # 测试简单的嵌入生成
                test_result = await self.generate_single_embedding("健康检查测试")
                status["test_embedding_dimension"] = len(test_result)
                status["last_test_success"] = True
            except Exception as e:
                status["status"] = "unhealthy"
                status["last_test_success"] = False
                status["last_error"] = str(e)
        
        return status
    
    @property
    def service_name(self) -> str:
        """获取服务名称"""
        return f"OpenAIEmbedding-{self.model}"
    
    @property
    def config(self) -> EmbeddingConfig:
        """获取配置信息"""
        return self._config
    
    @property
    def supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return ["zh", "en", "ja", "ko", "es", "fr", "de", "it", "pt", "ru"]
    
    async def _test_connection(self) -> None:
        """测试API连接"""
        try:
            # 测试简单的嵌入请求
            response = await self._client.embeddings.create(
                model=self.model,
                input="connection test",
                encoding_format="float"
            )
            
            if not response.data:
                raise EmbeddingError("API测试失败: 返回数据为空")
            
            logger.debug("OpenAI API连接测试成功")
            
        except Exception as e:
            logger.error(f"OpenAI API连接测试失败: {e}")
            raise EmbeddingError(f"API连接测试失败: {e}")
    
    def _preprocess_texts(self, texts: List[str]) -> List[str]:
        """预处理文本"""
        processed = []
        
        for text in texts:
            # 清理文本
            cleaned = text.strip()
            
            # 检查长度限制
            if len(cleaned) > self._config.max_tokens * 4:  # 粗略估算token数
                # 截断过长的文本
                cleaned = cleaned[:self._config.max_tokens * 4]
                logger.warning(f"文本被截断: 原长度 {len(text)}, 截断后 {len(cleaned)}")
            
            # 跳过空文本
            if not cleaned:
                cleaned = "空文本"  # 提供默认文本
            
            processed.append(cleaned)
        
        return processed
    
    async def _generate_batch_embeddings(
        self, texts: List[str]
    ) -> tuple[List[List[float]], Dict[str, int]]:
        """生成批次嵌入"""
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                response = await self._client.embeddings.create(
                    model=self.model,
                    input=texts,
                    encoding_format="float"
                )
                
                # 提取嵌入向量
                embeddings = [item.embedding for item in response.data]
                
                # 提取使用统计
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens,
                }
                
                return embeddings, usage
                
            except openai.RateLimitError as e:
                retry_count += 1
                last_error = e
                wait_time = min(2 ** retry_count, 10)  # 指数退避，最大10秒
                logger.warning(f"速率限制，等待 {wait_time} 秒后重试 (第 {retry_count} 次)")
                await asyncio.sleep(wait_time)
                
            except (openai.APIConnectionError, openai.APITimeoutError) as e:
                retry_count += 1
                last_error = e
                wait_time = min(1 + retry_count, 5)  # 线性增加，最大5秒
                logger.warning(f"网络错误，等待 {wait_time} 秒后重试 (第 {retry_count} 次): {e}")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                # 其他错误直接抛出
                logger.error(f"批次嵌入生成失败: {e}")
                raise EmbeddingError(f"批次嵌入生成失败: {e}")
        
        # 重试次数耗尽
        raise EmbeddingError(
            f"重试 {self.max_retries} 次后仍然失败: {last_error}",
            provider="openai",
            error_code="MAX_RETRIES_EXCEEDED"
        )
