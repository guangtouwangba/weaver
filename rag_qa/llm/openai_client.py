#!/usr/bin/env python3
"""
OpenAI client for RAG module
Handles LLM integration for question answering
"""

import logging
import os
from typing import List, Dict, Any, Optional

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI client for RAG question answering"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.1)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai library is required. Install with: pip install openai")
        
        # Initialize OpenAI client
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client"""
        try:
            # Get API key from environment or config
            api_key = os.getenv('OPENAI_API_KEY') or self.config.get('api_key')
            
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or add to config")
            
            self.client = openai.OpenAI(api_key=api_key)
            
            logger.info(f"OpenAI client initialized with model: {self.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def generate_answer(self, question: str, context_chunks: List[Dict[str, Any]], 
                       system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate answer using OpenAI API
        
        Args:
            question: User's question
            context_chunks: List of relevant document chunks
            system_prompt: Optional system prompt override
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            # Build context from chunks
            context = self._build_context(context_chunks)
            
            # Build messages
            messages = self._build_messages(question, context, system_prompt)
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False
            )
            
            # Extract answer
            answer = response.choices[0].message.content
            
            # Build result with metadata
            result = {
                'answer': answer,
                'model': self.model,
                'tokens_used': response.usage.total_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'sources': self._extract_sources(context_chunks),
                'context_length': len(context),
                'num_chunks': len(context_chunks)
            }
            
            logger.info(f"Generated answer using {response.usage.total_tokens} tokens")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return {
                'answer': f"I apologize, but I encountered an error while generating the answer: {str(e)}",
                'error': str(e),
                'sources': [],
                'model': self.model
            }
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from document chunks"""
        if not chunks:
            return "No relevant context found."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Extract metadata
            metadata = chunk.get('metadata', {})
            source_doc = metadata.get('source_doc', 'Unknown')
            title = metadata.get('title', 'Unknown Title')
            page = chunk.get('page_number') or metadata.get('chunk_page')
            
            # Build chunk header
            header = f"[Source {i}: {source_doc}]"
            if title and title != 'Unknown Title':
                header += f" - {title}"
            if page:
                header += f" (Page {page})"
            
            # Add chunk content
            content = chunk.get('document', chunk.get('content', ''))
            
            context_parts.append(f"{header}\\n{content}\\n")
        
        return "\\n".join(context_parts)
    
    def _build_messages(self, question: str, context: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Build message list for OpenAI API"""
        
        # Default system prompt
        if not system_prompt:
            system_prompt = """You are an expert AI assistant specialized in answering questions about academic papers, particularly in the fields of machine learning, artificial intelligence, and related areas.

Your task is to provide accurate, detailed, and helpful answers based on the provided context from research papers. Please follow these guidelines:

1. **Answer directly**: Provide clear, direct answers to the user's questions
2. **Use context**: Base your answers primarily on the provided context from the papers
3. **Include citations**: When referencing information, mention the source document (e.g., "According to paper 2508.00123...")
4. **Be specific**: Include relevant details, technical concepts, and findings from the papers
5. **Acknowledge limitations**: If the context doesn't contain enough information, say so
6. **Stay focused**: Keep your answers relevant to the question asked
7. **Technical accuracy**: Maintain technical accuracy when discussing research findings

Format your response with:
- A clear answer to the question
- Specific references to the source papers when appropriate
- Page numbers when available

If multiple papers discuss the same topic, synthesize the information and note any differences in findings or approaches."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Context from research papers:
{context}

Question: {question}

Please provide a comprehensive answer based on the provided context."""}
        ]
        
        return messages
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from chunks"""
        sources = []
        seen_sources = set()
        
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            source_doc = metadata.get('source_doc', 'Unknown')
            
            if source_doc not in seen_sources:
                source_info = {
                    'arxiv_id': source_doc,
                    'title': metadata.get('title', 'Unknown Title'),
                    'authors': metadata.get('authors', 'Unknown Authors'),
                    'similarity': chunk.get('similarity', 0.0)
                }
                sources.append(source_info)
                seen_sources.add(source_doc)
        
        return sources
    
    def generate_streaming_answer(self, question: str, context_chunks: List[Dict[str, Any]], 
                                system_prompt: Optional[str] = None):
        """
        Generate streaming answer (generator function)
        
        Args:
            question: User's question
            context_chunks: List of relevant document chunks
            system_prompt: Optional system prompt override
            
        Yields:
            Chunks of the generated answer
        """
        try:
            # Build context and messages
            context = self._build_context(context_chunks)
            messages = self._build_messages(question, context, system_prompt)
            
            # Generate streaming response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            logger.error(f"Failed to generate streaming answer: {e}")
            yield f"Error generating answer: {str(e)}"
    
    def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Try a simple API call to validate the key
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models
        
        Returns:
            List of available model names
        """
        try:
            models = self.client.models.list()
            model_names = [model.id for model in models.data if 'gpt' in model.id.lower()]
            return sorted(model_names)
            
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview']  # Default fallback
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def check_context_limit(self, question: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check if context fits within model's token limit
        
        Args:
            question: User's question
            context_chunks: List of context chunks
            
        Returns:
            Dictionary with limit check results
        """
        context = self._build_context(context_chunks)
        messages = self._build_messages(question, context)
        
        # Estimate total tokens
        total_text = " ".join([msg["content"] for msg in messages])
        estimated_tokens = self.estimate_tokens(total_text)
        
        # Model token limits (approximate)
        model_limits = {
            'gpt-3.5-turbo': 4096,
            'gpt-4': 8192,
            'gpt-4-turbo-preview': 128000,
            'gpt-4o': 128000
        }
        
        limit = model_limits.get(self.model, 4096)
        
        return {
            'estimated_tokens': estimated_tokens,
            'token_limit': limit,
            'within_limit': estimated_tokens <= limit,
            'suggested_max_chunks': len(context_chunks) if estimated_tokens <= limit else int(len(context_chunks) * limit / estimated_tokens)
        }