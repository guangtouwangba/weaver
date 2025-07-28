"""
Model client factory supporting multiple LLM providers including DeepSeek
"""

import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class BaseModelClient(ABC):
    """Base class for model clients"""
    
    @abstractmethod
    def create_chat_completion(self, 
                              messages: list, 
                              model: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1500,
                              stream: bool = False) -> Dict[str, Any]:
        """Create a chat completion"""
        pass

class OpenAIClient(BaseModelClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def create_chat_completion(self, 
                              messages: list, 
                              model: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1500,
                              stream: bool = False) -> Dict[str, Any]:
        """Create OpenAI chat completion"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else {},
                "model": response.model,
                "provider": "openai"
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class DeepSeekClient(BaseModelClient):
    """DeepSeek API client"""
    
    def __init__(self, api_key: str):
        # DeepSeek uses OpenAI-compatible API format
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def create_chat_completion(self, 
                              messages: list, 
                              model: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1500,
                              stream: bool = False) -> Dict[str, Any]:
        """Create DeepSeek chat completion"""
        try:
            # Map model names to DeepSeek equivalents
            deepseek_model = self._map_model_name(model)
            
            response = self.client.chat.completions.create(
                model=deepseek_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else {},
                "model": response.model,
                "provider": "deepseek"
            }
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    def _map_model_name(self, model: str) -> str:
        """Map generic model names to DeepSeek model names"""
        model_mapping = {
            "gpt-4o-mini": "deepseek-chat",
            "gpt-4o": "deepseek-chat", 
            "gpt-4": "deepseek-chat",
            "gpt-3.5-turbo": "deepseek-chat",
            "deepseek-chat": "deepseek-chat",
            "deepseek-reasoner": "deepseek-reasoner",
            "deepseek-v3": "deepseek-chat",
            "deepseek-r1": "deepseek-reasoner"
        }
        return model_mapping.get(model, "deepseek-chat")

class ModelClientFactory:
    """Factory for creating model clients"""
    
    @staticmethod
    def create_client(provider: str, api_key: str) -> BaseModelClient:
        """Create a model client for the specified provider"""
        if provider.lower() == "openai":
            return OpenAIClient(api_key)
        elif provider.lower() == "deepseek":
            return DeepSeekClient(api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @staticmethod
    def get_supported_providers() -> list:
        """Get list of supported providers"""
        return ["openai", "deepseek"]
    
    @staticmethod
    def get_model_mapping(provider: str) -> Dict[str, str]:
        """Get model mapping for a provider"""
        if provider.lower() == "openai":
            return {
                "gpt-4o-mini": "gpt-4o-mini",
                "gpt-4o": "gpt-4o",
                "gpt-4": "gpt-4",
                "gpt-3.5-turbo": "gpt-3.5-turbo"
            }
        elif provider.lower() == "deepseek":
            return {
                "gpt-4o-mini": "deepseek-chat",
                "gpt-4o": "deepseek-chat",
                "gpt-4": "deepseek-chat", 
                "gpt-3.5-turbo": "deepseek-chat",
                "deepseek-chat": "deepseek-chat",
                "deepseek-reasoner": "deepseek-reasoner"
            }
        else:
            return {} 