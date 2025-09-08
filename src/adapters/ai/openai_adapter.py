"""
OpenAI service adapter.

Implements AI services using OpenAI's API.
"""

from typing import List, Optional, Dict, Any
import openai
from openai import AsyncOpenAI

from ...core.domain_services.chat_service import ChatService, ChatContext
from ...core.domain_services.vector_search_service import VectorSearchService
from ...core.domain_services.document_processing_service import DocumentProcessingService
from ...core.value_objects.chat_message import ChatMessage
from ...core.value_objects.document_chunk import DocumentChunk


class OpenAIAdapter(ChatService, VectorSearchService, DocumentProcessingService):
    """OpenAI implementation of AI services."""
    
    def __init__(
        self, 
        api_key: str, 
        chat_model: str = "gpt-3.5-turbo",
        embedding_model: str = "text-embedding-ada-002"
    ):
        self._client = AsyncOpenAI(api_key=api_key)
        self._chat_model = chat_model
        self._embedding_model = embedding_model
    
    # ChatService implementation
    async def generate_response(
        self, 
        message: str, 
        context: ChatContext,
        model_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response based on message and context."""
        try:
            # Build messages for OpenAI API
            messages = self._build_openai_messages(message, context)
            
            # Merge default config with provided config
            config = {
                "model": self._chat_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            if model_config:
                config.update(model_config)
            
            response = await self._client.chat.completions.create(**config)
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate response: {str(e)}")
    
    async def generate_session_title(self, messages: List[ChatMessage]) -> str:
        """Generate a title for a chat session based on messages."""
        try:
            # Use first few messages to generate title
            content = " ".join([msg.content for msg in messages[:3]])
            
            response = await self._client.chat.completions.create(
                model=self._chat_model,
                messages=[
                    {"role": "system", "content": "Generate a short, descriptive title (max 50 characters) for this conversation:"},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception:
            return "Chat Session"
    
    async def generate_session_summary(self, messages: List[ChatMessage]) -> str:
        """Generate a summary for a chat session."""
        try:
            content = " ".join([msg.content for msg in messages])
            
            response = await self._client.chat.completions.create(
                model=self._chat_model,
                messages=[
                    {"role": "system", "content": "Provide a concise summary of this conversation:"},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception:
            return "Conversation summary unavailable"
    
    async def extract_intent(self, message: str) -> Dict[str, Any]:
        """Extract user intent from message."""
        try:
            response = await self._client.chat.completions.create(
                model=self._chat_model,
                messages=[
                    {"role": "system", "content": "Extract the user's intent from this message. Respond with JSON format: {\"intent\": \"intent_name\", \"entities\": [], \"confidence\": 0.95}"},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception:
            return {"intent": "general_query", "entities": [], "confidence": 0.5}
    
    async def suggest_follow_up_questions(
        self, 
        context: ChatContext,
        count: int = 3
    ) -> List[str]:
        """Suggest follow-up questions based on context."""
        try:
            context_text = self.format_context_for_ai(context)
            
            response = await self._client.chat.completions.create(
                model=self._chat_model,
                messages=[
                    {"role": "system", "content": f"Based on this context, suggest {count} relevant follow-up questions:"},
                    {"role": "user", "content": context_text}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            # Parse response and extract questions
            questions_text = response.choices[0].message.content
            questions = [q.strip() for q in questions_text.split('\n') if q.strip() and '?' in q]
            return questions[:count]
            
        except Exception:
            return ["Can you tell me more about this topic?", "What are the key points?", "Are there any examples?"]
    
    async def evaluate_response_quality(
        self, 
        question: str, 
        response: str, 
        context: ChatContext
    ) -> Dict[str, Any]:
        """Evaluate the quality of a generated response."""
        # This is a simplified implementation
        # In practice, you might use more sophisticated evaluation methods
        return {
            "relevance_score": 0.8,
            "completeness_score": 0.7,
            "accuracy_score": 0.9,
            "overall_score": 0.8
        }
    
    async def detect_sensitive_content(self, message: str) -> Dict[str, Any]:
        """Detect sensitive or inappropriate content."""
        try:
            response = await self._client.moderations.create(input=message)
            moderation = response.results[0]
            
            return {
                "is_flagged": moderation.flagged,
                "categories": dict(moderation.categories),
                "category_scores": dict(moderation.category_scores)
            }
            
        except Exception:
            return {"is_flagged": False, "categories": {}, "category_scores": {}}
    
    def format_context_for_ai(self, context: ChatContext) -> str:
        """Format context information for AI model consumption."""
        formatted_context = []
        
        # Add relevant document chunks
        if context.relevant_chunks:
            formatted_context.append("Relevant information:")
            for i, chunk in enumerate(context.relevant_chunks[:5]):  # Limit to 5 chunks
                formatted_context.append(f"{i+1}. {chunk.content[:500]}...")
        
        # Add conversation history
        if context.conversation_history:
            formatted_context.append("\nRecent conversation:")
            for msg in context.conversation_history[-5:]:  # Last 5 messages
                role = msg.role.value.title()
                formatted_context.append(f"{role}: {msg.content}")
        
        return "\n".join(formatted_context)
    
    def should_use_context(self, message: str, session) -> bool:
        """Determine if context should be used for this message."""
        # Use context for questions that seem to require knowledge
        question_indicators = ["what", "how", "why", "when", "where", "explain", "tell me", "describe"]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in question_indicators)
    
    # VectorSearchService implementation
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        try:
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    # DocumentProcessingService implementation
    def generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate a summary of the content."""
        # This would be implemented synchronously or made async
        # For now, return a simple truncation
        words = content.split()
        if len(words) <= max_length:
            return content
        return " ".join(words[:max_length]) + "..."
    
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content."""
        # Simple keyword extraction - in practice, you'd use more sophisticated methods
        import re
        words = re.findall(r'\b\w+\b', content.lower())
        # Filter out common words and return most frequent
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        filtered_words = [w for w in words if w not in common_words and len(w) > 3]
        
        from collections import Counter
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    def _build_openai_messages(self, message: str, context: ChatContext) -> List[Dict[str, str]]:
        """Build messages list for OpenAI API."""
        messages = []
        
        # System message with context
        system_content = "You are a helpful AI assistant. Use the provided context to answer questions accurately."
        
        if context.relevant_chunks:
            context_text = self.format_context_for_ai(context)
            system_content += f"\n\nContext:\n{context_text}"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        for msg in context.conversation_history[-10:]:  # Last 10 messages
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return messages