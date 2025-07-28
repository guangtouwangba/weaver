"""
Abstract AI client interface supporting multiple providers
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Provider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "system", "user", "assistant"
    content: str

@dataclass
class ChatCompletion:
    """Chat completion response"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

class BaseAIClient(ABC):
    """Abstract base class for AI clients"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.provider = self._get_provider()
    
    @abstractmethod
    def _get_provider(self) -> Provider:
        """Get the provider type"""
        pass
    
    @abstractmethod
    def create_chat_completion(self, 
                              messages: List[ChatMessage],
                              model: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1500,
                              stream: bool = False) -> ChatCompletion:
        """Create a chat completion"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass
    
    def validate_model(self, model: str) -> bool:
        """Validate if a model is available for this provider"""
        return model in self.get_available_models()

class OpenAIClient(BaseAIClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def _get_provider(self) -> Provider:
        return Provider.OPENAI
    
    def create_chat_completion(self, 
                              messages: List[ChatMessage],
                              model: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1500,
                              stream: bool = False) -> ChatCompletion:
        """Create OpenAI chat completion"""
        try:
            # Convert ChatMessage to dict format
            messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages_dict,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            return ChatCompletion(
                content=response.choices[0].message.content,
                model=response.model,
                provider=self.provider.value,
                usage=response.usage.dict() if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]

class DeepSeekClient(BaseAIClient):
    """DeepSeek API client"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        # DeepSeek uses OpenAI-compatible API format
        super().__init__(api_key, base_url or "https://api.deepseek.com")
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=self.base_url)
    
    def _get_provider(self) -> Provider:
        return Provider.DEEPSEEK
    
    def create_chat_completion(self, 
                              messages: List[ChatMessage],
                              model: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1500,
                              stream: bool = False) -> ChatCompletion:
        """Create DeepSeek chat completion"""
        try:
            # Map model names to DeepSeek equivalents
            deepseek_model = self._map_model_name(model)
            
            # Convert ChatMessage to dict format
            messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            response = self.client.chat.completions.create(
                model=deepseek_model,
                messages=messages_dict,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            return ChatCompletion(
                content=response.choices[0].message.content,
                model=response.model,
                provider=self.provider.value,
                usage=response.usage.dict() if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
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
    
    def get_available_models(self) -> List[str]:
        """Get available DeepSeek models"""
        return [
            "deepseek-chat",
            "deepseek-reasoner",
            "deepseek-v3",
            "deepseek-r1",
            "gpt-4o-mini",  # Mapped to deepseek-chat
            "gpt-4o",       # Mapped to deepseek-chat
            "gpt-4",        # Mapped to deepseek-chat
            "gpt-3.5-turbo" # Mapped to deepseek-chat
        ]

class AnthropicClient(BaseAIClient):
    """Anthropic Claude API client"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def _get_provider(self) -> Provider:
        return Provider.ANTHROPIC
    
    def create_chat_completion(self, 
                              messages: List[ChatMessage],
                              model: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1500,
                              stream: bool = False) -> ChatCompletion:
        """Create Anthropic chat completion"""
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                if msg.role == "system":
                    # Anthropic doesn't support system messages directly
                    # We'll prepend it to the first user message
                    continue
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Handle system message
            system_message = ""
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                    break
            
            response = self.client.messages.create(
                model=model,
                messages=anthropic_messages,
                system=system_message if system_message else None,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return ChatCompletion(
                content=response.content[0].text,
                model=response.model,
                provider=self.provider.value,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                finish_reason=response.stop_reason
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]

class AIClientFactory:
    """Factory for creating AI clients"""
    
    @staticmethod
    def create_client(provider: str, api_key: str, base_url: Optional[str] = None) -> BaseAIClient:
        """Create an AI client for the specified provider"""
        provider_enum = Provider(provider.lower())
        
        if provider_enum == Provider.OPENAI:
            return OpenAIClient(api_key, base_url)
        elif provider_enum == Provider.DEEPSEEK:
            return DeepSeekClient(api_key, base_url)
        elif provider_enum == Provider.ANTHROPIC:
            return AnthropicClient(api_key, base_url)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @staticmethod
    def get_supported_providers() -> List[str]:
        """Get list of supported providers"""
        return [provider.value for provider in Provider]
    
    @staticmethod
    def get_provider_info(provider: str) -> Dict[str, Any]:
        """Get information about a provider"""
        provider_enum = Provider(provider.lower())
        
        info = {
            "name": provider_enum.value,
            "supported_models": [],
            "api_docs_url": "",
            "features": []
        }
        
        if provider_enum == Provider.OPENAI:
            info.update({
                "supported_models": [
                    "gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"
                ],
                "api_docs_url": "https://platform.openai.com/docs",
                "features": ["chat", "completion", "embeddings", "function_calling"]
            })
        elif provider_enum == Provider.DEEPSEEK:
            info.update({
                "supported_models": [
                    "deepseek-chat", "deepseek-reasoner", "deepseek-v3", "deepseek-r1"
                ],
                "api_docs_url": "https://api-docs.deepseek.com/zh-cn/",
                "features": ["chat", "completion", "reasoning"]
            })
        elif provider_enum == Provider.ANTHROPIC:
            info.update({
                "supported_models": [
                    "claude-3-5-sonnet", "claude-3-5-haiku", "claude-3-opus", "claude-3-sonnet"
                ],
                "api_docs_url": "https://docs.anthropic.com/",
                "features": ["chat", "completion", "vision", "function_calling"]
            })
        
        return info 