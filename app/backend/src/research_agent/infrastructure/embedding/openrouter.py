"""Embedding service implementations."""

from typing import List

import httpx
from openai import AsyncOpenAI

from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.shared.utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service (direct, not via OpenRouter)."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
    ):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key)

    async def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        if not texts:
            return []

        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]


class OpenRouterEmbeddingService(EmbeddingService):
    """OpenRouter embedding service using direct HTTP calls.
    
    OpenRouter supports embedding models like openai/text-embedding-3-small.
    See: https://openrouter.ai/openai/text-embedding-3-small/api
    
    Uses httpx directly instead of OpenAI SDK for better compatibility.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/text-embedding-3-small",
    ):
        self._model = model
        self._api_key = api_key

    async def _call_api(self, input_data: str | List[str]) -> dict:
        """Call OpenRouter embeddings API directly."""
        url = f"{self.OPENROUTER_BASE_URL}/embeddings"
        is_batch = isinstance(input_data, list)
        input_count = len(input_data) if is_batch else 1
        
        logger.info(
            f"[OpenRouter Embedding] Calling API: model={self._model}, "
            f"batch={is_batch}, items={input_count}"
        )
        logger.debug(f"[OpenRouter Embedding] Request URL: {url}")
        
        # Explicitly disable proxy to avoid SOCKS proxy issues
        # trust_env=False disables reading proxy settings from environment variables
        async with httpx.AsyncClient(
            timeout=60.0,
            trust_env=True,  # 允许使用系统代理环境变量（如 https_proxy）
        ) as client:
            request_payload = {
                "model": self._model,
                "input": input_data,
                "encoding_format": "float",
            }
            logger.debug(f"[OpenRouter Embedding] Request payload keys: {list(request_payload.keys())}")
            if is_batch:
                logger.debug(f"[OpenRouter Embedding] Batch size: {len(input_data)}")
                # Log first item preview for debugging
                if input_data:
                    first_item_preview = input_data[0][:100] + "..." if len(input_data[0]) > 100 else input_data[0]
                    logger.debug(f"[OpenRouter Embedding] First item preview: {first_item_preview}")
            
            try:
                # Log request details for debugging
                api_key_preview = f"{self._api_key[:10]}...{self._api_key[-4:]}" if len(self._api_key) > 14 else "***"
                logger.info(f"[OpenRouter Embedding] API Key preview: {api_key_preview}")
                logger.info(f"[OpenRouter Embedding] Request URL: {url}")
                logger.info(f"[OpenRouter Embedding] Request model: {request_payload['model']}")
                logger.info(f"[OpenRouter Embedding] Request encoding_format: {request_payload.get('encoding_format')}")
                logger.info(f"[OpenRouter Embedding] Request input type: {type(request_payload['input'])}")
                if isinstance(request_payload['input'], list):
                    logger.info(f"[OpenRouter Embedding] Request input length: {len(request_payload['input'])}")
                
                # OpenRouter requires specific headers for embeddings
                # See: https://openrouter.ai/docs/api-reference/embeddings
                headers = {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/research-agent-rag",  # Required for OpenRouter
                    "X-Title": "Research Agent RAG",  # Optional but recommended
                }
                logger.info(f"[OpenRouter Embedding] Request headers: {list(headers.keys())}")
                
                response = await client.post(
                    url,
                    headers=headers,
                    json=request_payload,
                )
                
                logger.info(f"[OpenRouter Embedding] Response status: {response.status_code}")
                logger.info(f"[OpenRouter Embedding] Response headers: {dict(response.headers)}")
                
                # Get full response text for debugging
                response_text = response.text
                logger.info(f"[OpenRouter Embedding] Response body (first 1000 chars): {response_text[:1000]}")
                
                response.raise_for_status()
                result = response.json()
                
                # Log full response structure
                logger.info(f"[OpenRouter Embedding] Response JSON keys: {list(result.keys())}")
                if "error" in result:
                    logger.error(f"[OpenRouter Embedding] Full error response: {result['error']}")
                
                logger.debug(f"[OpenRouter Embedding] Response keys: {list(result.keys())}")
                if "data" in result:
                    logger.info(f"[OpenRouter Embedding] Received {len(result['data'])} embeddings")
                else:
                    logger.warning(f"[OpenRouter Embedding] Response missing 'data' key: {list(result.keys())}")
                
                # Log response structure for debugging
                if "data" not in result:
                    logger.error(
                        f"[OpenRouter Embedding] Response missing 'data' key. "
                        f"Response keys: {list(result.keys())}, "
                        f"Full response: {result}"
                    )
                    # Check for error in response
                    if "error" in result:
                        error_msg = result.get("error", {})
                        if isinstance(error_msg, dict):
                            error_detail = error_msg.get("message", str(error_msg))
                            error_type = error_msg.get("type", "unknown")
                            logger.error(
                                f"[OpenRouter Embedding] API error: type={error_type}, "
                                f"message={error_detail}"
                            )
                        else:
                            error_detail = str(error_msg)
                            logger.error(f"[OpenRouter Embedding] API error: {error_detail}")
                        raise ValueError(
                            f"OpenRouter API error: {error_detail}. "
                            f"Full response: {result}"
                        )
                    raise ValueError(
                        f"Unexpected OpenRouter API response format. "
                        f"Expected 'data' key but got: {list(result.keys())}. "
                        f"Response: {result}"
                    )
                
                return result
                    
            except httpx.ProxyError as e:
                logger.error(f"[OpenRouter Embedding] Proxy error: {e}")
                raise ValueError(
                    f"Proxy configuration error: {e}. "
                    f"Please check HTTP_PROXY/HTTPS_PROXY environment variables or install socksio: pip install httpx[socks]"
                )
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"[OpenRouter Embedding] HTTP error: status={e.response.status_code}, "
                    f"response={e.response.text[:500]}"
                )
                raise
            except httpx.RequestError as e:
                logger.error(f"[OpenRouter Embedding] Request error: {e}")
                raise ValueError(f"Request failed: {e}")
            except Exception as e:
                logger.error(f"[OpenRouter Embedding] Unexpected error: {e}", exc_info=True)
                raise

    async def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        logger.debug(f"[OpenRouter Embedding] Processing single text (length: {len(text)})")
        result = await self._call_api(text)
        
        # Validate response structure
        if "data" not in result:
            logger.error(
                f"[OpenRouter Embedding] Response missing 'data' key. "
                f"Response keys: {list(result.keys())}, "
                f"Full response: {result}"
            )
            raise ValueError(
                f"OpenRouter API response missing 'data' key. "
                f"Response: {result}"
            )
        
        data = result["data"]
        if not data or len(data) == 0:
            logger.error(
                f"[OpenRouter Embedding] Empty data array in response. "
                f"Response: {result}"
            )
            raise ValueError(
                f"OpenRouter API returned empty data array. Response: {result}"
            )
        
        if "embedding" not in data[0]:
            logger.error(
                f"[OpenRouter Embedding] Response data item missing 'embedding' key. "
                f"Data item keys: {list(data[0].keys()) if data[0] else 'empty'}, "
                f"Response: {result}"
            )
            raise ValueError(
                f"OpenRouter API response data item missing 'embedding' key. "
                f"Response: {result}"
            )
        
        embedding = data[0]["embedding"]
        logger.debug(f"[OpenRouter Embedding] Generated embedding (dimension: {len(embedding)})")
        return embedding

    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Get embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum number of texts per API call (default: 100)
                       OpenRouter/OpenAI has limits on batch size
        
        Returns:
            List of embeddings
        """
        if not texts:
            logger.debug("[OpenRouter Embedding] Empty batch, returning empty list")
            return []

        total_texts = len(texts)
        logger.info(f"[OpenRouter Embedding] Processing {total_texts} texts in batches of {batch_size}")
        
        all_embeddings = []
        
        # Process in smaller batches to avoid API limits
        # OpenRouter supports batch processing according to docs
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_texts + batch_size - 1) // batch_size
            
            logger.info(
                f"[OpenRouter Embedding] Processing batch {batch_num}/{total_batches} "
                f"(texts {i+1}-{min(i+batch_size, total_texts)})"
            )
            
            result = await self._call_api(batch)
            
            # Validate response structure
            if "data" not in result:
                logger.error(
                    f"[OpenRouter Embedding] Response missing 'data' key for batch {batch_num}. "
                    f"Response keys: {list(result.keys())}, "
                    f"Response: {result}"
                )
                raise ValueError(
                    f"OpenRouter API response missing 'data' key for batch {batch_num}. "
                    f"Response: {result}"
                )
            
            data = result["data"]
            if not data or len(data) == 0:
                logger.error(
                    f"[OpenRouter Embedding] No data in response for batch {batch_num}. "
                    f"Response keys: {list(result.keys())}, "
                    f"Response: {result}"
                )
                raise ValueError(
                    f"OpenRouter API returned no data for batch {batch_num} embedding. "
                    f"Response: {result}"
                )
            
            # Validate that we got the expected number of embeddings
            received_count = len(data)
            expected_count = len(batch)
            if received_count != expected_count:
                logger.warning(
                    f"[OpenRouter Embedding] Batch {batch_num} count mismatch: "
                    f"expected={expected_count}, received={received_count}"
                )
            
            # Extract embeddings with validation
            for j, item in enumerate(data):
                if "embedding" not in item:
                    logger.error(
                        f"[OpenRouter Embedding] Batch {batch_num}, item {j} missing 'embedding' key. "
                        f"Item keys: {list(item.keys())}"
                    )
                    raise ValueError(f"Item {j} in batch {batch_num} missing 'embedding' key: {item}")
                embedding = item["embedding"]
                if not isinstance(embedding, list) or len(embedding) == 0:
                    logger.warning(
                        f"[OpenRouter Embedding] Batch {batch_num}, item {j} has invalid embedding: {type(embedding)}"
                    )
                all_embeddings.append(embedding)
            
            logger.info(f"[OpenRouter Embedding] Batch {batch_num} completed: {received_count} embeddings")
        
        logger.info(f"[OpenRouter Embedding] All batches completed: {len(all_embeddings)} total embeddings")
        return all_embeddings
