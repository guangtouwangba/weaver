"""
Advanced Answer Generation and Context Management

Provides sophisticated answer generation with multi-document synthesis,
source attribution, and context-aware conversation management.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from .retrieval import RetrievalResult

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    """LLM provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

class AnswerType(str, Enum):
    """Answer type classification"""
    DIRECT = "direct"
    SYNTHESIS = "synthesis"
    COMPARISON = "comparison"
    EXPLANATION = "explanation"
    PROCEDURAL = "procedural"

@dataclass
class ContextChunk:
    """Context chunk for generation"""
    id: str
    content: str
    document_id: str
    document_title: Optional[str]
    score: float
    metadata: Dict[str, Any]
    page_number: Optional[int] = None
    section: Optional[str] = None

@dataclass
class GeneratedAnswer:
    """Generated answer with metadata"""
    content: str
    answer_type: AnswerType
    confidence: float
    sources: List[Dict[str, Any]]
    model_used: str
    generation_time: float
    token_usage: Optional[Dict[str, int]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    follow_up_questions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ConversationTurn:
    """Single conversation turn"""
    turn_id: str
    query: str
    answer: str
    context_used: List[ContextChunk]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ConversationMemory:
    """Conversation memory state"""
    conversation_id: str
    topic_id: int
    turns: List[ConversationTurn]
    entities: Dict[str, Any]
    ongoing_topics: List[str]
    context_summary: str
    last_updated: datetime

class ILLMClient(ABC):
    """Abstract LLM client interface"""
    
    @abstractmethod
    async def generate_completion(self, messages: List[Dict[str, str]], 
                                model: str, max_tokens: int = 1000,
                                temperature: float = 0.1) -> Dict[str, Any]:
        """Generate completion"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get available models"""
        pass

class OpenAIClient(ILLMClient):
    """OpenAI LLM client"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        try:
            import openai
            
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info("OpenAI client initialized")
            
        except ImportError:
            raise ImportError("openai package required for OpenAI client")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    async def generate_completion(self, messages: List[Dict[str, str]], 
                                model: str = "gpt-4-turbo-preview",
                                max_tokens: int = 1000,
                                temperature: float = 0.1) -> Dict[str, Any]:
        """Generate OpenAI completion"""
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]

class AnthropicClient(ILLMClient):
    """Anthropic Claude client"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Anthropic client"""
        try:
            import anthropic
            
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            self._initialized = True
            logger.info("Anthropic client initialized")
            
        except ImportError:
            raise ImportError("anthropic package required for Anthropic client")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    
    async def generate_completion(self, messages: List[Dict[str, str]], 
                                model: str = "claude-3-sonnet-20240229",
                                max_tokens: int = 1000,
                                temperature: float = 0.1) -> Dict[str, Any]:
        """Generate Anthropic completion"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Convert OpenAI format to Anthropic format
            system_msg = None
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg,
                messages=user_messages
            )
            
            return {
                "content": response.content[0].text,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "finish_reason": response.stop_reason
            }
            
        except Exception as e:
            logger.error(f"Anthropic completion failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]

class PromptTemplate:
    """Prompt template management"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get main system prompt"""
        return """你是一个专业的AI助手，专门基于给定的文档内容回答用户问题。

核心职责：
1. 仅基于提供的上下文信息回答问题
2. 如果上下文中没有相关信息，明确说明无法回答
3. 提供准确、相关、有用的答案
4. 适当引用来源文档

回答准则：
- 保持客观和准确
- 使用清晰易懂的语言
- 适当时提供具体示例
- 承认不确定性或知识局限
- 用中文回答（除非另有说明）

引用格式：
- 使用 [文档标题] 或 [文档ID-页码] 格式
- 在相关信息后标注来源
- 多个来源时按重要性排序"""
    
    @staticmethod
    def build_context_prompt(query: str, context_chunks: List[ContextChunk],
                           conversation_history: Optional[List[ConversationTurn]] = None) -> str:
        """Build context-aware prompt"""
        prompt_parts = []
        
        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("## 对话历史")
            for turn in conversation_history[-3:]:  # Last 3 turns
                prompt_parts.append(f"用户: {turn.query}")
                prompt_parts.append(f"助手: {turn.answer[:200]}...")
            prompt_parts.append("")
        
        # Add context information
        prompt_parts.append("## 相关文档内容")
        for i, chunk in enumerate(context_chunks, 1):
            source_info = f"[文档{i}"
            if chunk.document_title:
                source_info += f": {chunk.document_title}"
            if chunk.page_number:
                source_info += f", 第{chunk.page_number}页"
            source_info += "]"
            
            prompt_parts.append(f"{source_info}")
            prompt_parts.append(f"{chunk.content}\n")
        
        prompt_parts.append("## 当前问题")
        prompt_parts.append(f"{query}")
        
        prompt_parts.append("\n请基于上述文档内容回答问题，并标注信息来源。")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def build_synthesis_prompt(query: str, context_chunks: List[ContextChunk]) -> str:
        """Build multi-document synthesis prompt"""
        return f"""请基于以下多个文档的信息，综合回答用户问题。

用户问题: {query}

文档信息:
{PromptTemplate._format_context_for_synthesis(context_chunks)}

要求:
1. 整合来自多个文档的信息
2. 指出不同文档间的一致性和差异
3. 提供全面、平衡的答案
4. 清楚标注每个信息点的来源
5. 如有矛盾信息，请指出并分析可能原因"""
    
    @staticmethod
    def _format_context_for_synthesis(chunks: List[ContextChunk]) -> str:
        """Format context for synthesis"""
        formatted = []
        doc_groups = {}
        
        # Group by document
        for chunk in chunks:
            doc_id = chunk.document_id
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            doc_groups[doc_id].append(chunk)
        
        # Format each document
        for doc_id, doc_chunks in doc_groups.items():
            doc_title = doc_chunks[0].document_title or f"文档{doc_id}"
            formatted.append(f"\n### {doc_title}")
            
            for chunk in doc_chunks:
                page_info = f"(第{chunk.page_number}页)" if chunk.page_number else ""
                formatted.append(f"- {chunk.content} {page_info}")
        
        return "\n".join(formatted)

class CitationManager:
    """Citation and source attribution management"""
    
    def __init__(self):
        self.citation_patterns = [
            r'\[文档(\d+)[^\]]*\]',
            r'\[(\d+)\]',
            r'根据.*?([文档\d]+)',
            r'在.*?([文档\d]+).*?中'
        ]
    
    def add_citations(self, answer: str, context_chunks: List[ContextChunk]) -> Tuple[str, List[Dict[str, Any]]]:
        """Add citations to answer"""
        import re
        
        # Extract existing citations
        citations = []
        citation_map = {}
        
        # Build citation mapping
        for i, chunk in enumerate(context_chunks, 1):
            citation_id = f"文档{i}"
            citation_map[citation_id] = {
                "id": citation_id,
                "document_id": chunk.document_id,
                "document_title": chunk.document_title,
                "page_number": chunk.page_number,
                "section": chunk.section,
                "content_snippet": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content,
                "score": chunk.score
            }
        
        # Find and validate citations in answer
        for pattern in self.citation_patterns:
            matches = re.finditer(pattern, answer)
            for match in matches:
                citation_ref = match.group(1) if match.groups() else match.group(0)
                if citation_ref in citation_map:
                    citations.append(citation_map[citation_ref])
        
        # Remove duplicates
        unique_citations = []
        seen_ids = set()
        for cite in citations:
            if cite["id"] not in seen_ids:
                unique_citations.append(cite)
                seen_ids.add(cite["id"])
        
        return answer, unique_citations
    
    def generate_source_list(self, context_chunks: List[ContextChunk]) -> List[Dict[str, Any]]:
        """Generate formatted source list"""
        sources = []
        
        for i, chunk in enumerate(context_chunks, 1):
            source = {
                "id": f"source_{i}",
                "document_id": chunk.document_id,
                "title": chunk.document_title or f"文档 {chunk.document_id}",
                "page": chunk.page_number,
                "section": chunk.section,
                "relevance_score": chunk.score,
                "content_preview": chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
            }
            sources.append(source)
        
        return sources

class ContextManager:
    """Advanced context management with conversation memory"""
    
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length
        self.conversations = {}  # In-memory storage, should use persistent storage in production
    
    def estimate_token_count(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for mixed Chinese/English
        return len(text) // 3
    
    def select_context_chunks(self, query: str, retrieval_results: List[RetrievalResult],
                            max_chunks: int = 10) -> List[ContextChunk]:
        """Select and prepare context chunks"""
        # Convert retrieval results to context chunks
        context_chunks = []
        
        for result in retrieval_results[:max_chunks]:
            chunk = ContextChunk(
                id=result.id,
                content=result.content,
                document_id=result.document_id,
                document_title=result.metadata.get("title") if result.metadata else None,
                score=result.score,
                metadata=result.metadata or {},
                page_number=result.metadata.get("page_number") if result.metadata else None,
                section=result.metadata.get("section") if result.metadata else None
            )
            context_chunks.append(chunk)
        
        # Filter by context length
        return self._manage_context_length(context_chunks)
    
    def _manage_context_length(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Manage context length to fit within limits"""
        selected_chunks = []
        total_tokens = 0
        
        # Sort by score (descending)
        sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
        
        for chunk in sorted_chunks:
            chunk_tokens = self.estimate_token_count(chunk.content)
            
            if total_tokens + chunk_tokens <= self.max_context_length:
                selected_chunks.append(chunk)
                total_tokens += chunk_tokens
            else:
                # Try to truncate the chunk if it's valuable
                if chunk.score > 0.7 and not selected_chunks:  # High score and no chunks yet
                    remaining_tokens = self.max_context_length - total_tokens
                    if remaining_tokens > 100:  # Worth truncating
                        truncated_content = chunk.content[:remaining_tokens * 3]  # Rough conversion back
                        chunk.content = truncated_content + "..."
                        selected_chunks.append(chunk)
                break
        
        return selected_chunks
    
    def get_conversation_context(self, conversation_id: str, max_turns: int = 5) -> List[ConversationTurn]:
        """Get conversation context"""
        if conversation_id in self.conversations:
            turns = self.conversations[conversation_id].turns
            return turns[-max_turns:] if turns else []
        return []
    
    def update_conversation_memory(self, conversation_id: str, topic_id: int,
                                 query: str, answer: str, context_chunks: List[ContextChunk]) -> None:
        """Update conversation memory"""
        turn = ConversationTurn(
            turn_id=f"{conversation_id}_{len(self.conversations.get(conversation_id, ConversationMemory('', 0, [], {}, [], '', datetime.now())).turns)}",
            query=query,
            answer=answer,
            context_used=context_chunks,
            timestamp=datetime.now()
        )
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationMemory(
                conversation_id=conversation_id,
                topic_id=topic_id,
                turns=[],
                entities={},
                ongoing_topics=[],
                context_summary="",
                last_updated=datetime.now()
            )
        
        self.conversations[conversation_id].turns.append(turn)
        self.conversations[conversation_id].last_updated = datetime.now()
        
        # Extract entities and topics (simplified implementation)
        self._update_entities_and_topics(conversation_id, query, answer)
    
    def _update_entities_and_topics(self, conversation_id: str, query: str, answer: str) -> None:
        """Update entities and topics tracking"""
        # Simple entity extraction (could be enhanced with NER)
        import re
        
        memory = self.conversations[conversation_id]
        
        # Extract potential entities (capitalized words, numbers)
        entities = re.findall(r'\b[A-Z][a-z]+\b|\b\d+\.?\d*\b', query + " " + answer)
        
        for entity in entities:
            if entity not in memory.entities:
                memory.entities[entity] = {"count": 0, "first_seen": datetime.now()}
            memory.entities[entity]["count"] += 1
            memory.entities[entity]["last_seen"] = datetime.now()

class AdvancedAnswerGenerator:
    """Advanced answer generator with multi-document synthesis"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.OPENAI,
                 config: Optional[Dict[str, Any]] = None):
        self.provider = provider
        self.config = config or {}
        self.llm_client = self._create_client()
        self.citation_manager = CitationManager()
        self.context_manager = ContextManager(
            max_context_length=self.config.get("max_context_length", 4000)
        )
        self._initialized = False
    
    def _create_client(self) -> ILLMClient:
        """Create LLM client"""
        if self.provider == LLMProvider.OPENAI:
            return OpenAIClient(api_key=self.config.get("openai_api_key"))
        elif self.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(api_key=self.config.get("anthropic_api_key"))
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def initialize(self) -> None:
        """Initialize the answer generator"""
        try:
            await self.llm_client.initialize()
            self._initialized = True
            logger.info("Advanced answer generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize answer generator: {e}")
            raise
    
    async def generate_answer(self, query: str, retrieval_results: List[RetrievalResult],
                            conversation_id: Optional[str] = None,
                            topic_id: Optional[int] = None) -> GeneratedAnswer:
        """Generate comprehensive answer"""
        if not self._initialized:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Select and prepare context
            context_chunks = self.context_manager.select_context_chunks(query, retrieval_results)
            
            if not context_chunks:
                return self._generate_no_context_answer(query)
            
            # Get conversation history
            conversation_history = []
            if conversation_id:
                conversation_history = self.context_manager.get_conversation_context(conversation_id)
            
            # Determine answer type
            answer_type = self._classify_answer_type(query, context_chunks)
            
            # Build appropriate prompt
            if answer_type == AnswerType.SYNTHESIS:
                prompt = PromptTemplate.build_synthesis_prompt(query, context_chunks)
            else:
                prompt = PromptTemplate.build_context_prompt(query, context_chunks, conversation_history)
            
            # Generate answer
            messages = [
                {"role": "system", "content": PromptTemplate.get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            model = self.config.get("model", "gpt-4-turbo-preview")
            max_tokens = self.config.get("max_tokens", 1000)
            temperature = self.config.get("temperature", 0.1)
            
            response = await self.llm_client.generate_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Add citations
            answer_with_citations, citations = self.citation_manager.add_citations(
                response["content"], context_chunks
            )
            
            # Generate follow-up questions
            follow_up_questions = await self._generate_follow_up_questions(query, answer_with_citations)
            
            # Calculate confidence
            confidence = self._calculate_confidence(response, context_chunks, citations)
            
            # Generate sources list
            sources = self.citation_manager.generate_source_list(context_chunks)
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            # Update conversation memory
            if conversation_id and topic_id:
                self.context_manager.update_conversation_memory(
                    conversation_id, topic_id, query, answer_with_citations, context_chunks
                )
            
            return GeneratedAnswer(
                content=answer_with_citations,
                answer_type=answer_type,
                confidence=confidence,
                sources=sources,
                model_used=response["model"],
                generation_time=generation_time,
                token_usage=response.get("usage"),
                citations=citations,
                follow_up_questions=follow_up_questions,
                metadata={
                    "context_chunks": len(context_chunks),
                    "conversation_id": conversation_id,
                    "topic_id": topic_id,
                    "finish_reason": response.get("finish_reason")
                }
            )
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return self._generate_error_answer(query, str(e))
    
    def _classify_answer_type(self, query: str, context_chunks: List[ContextChunk]) -> AnswerType:
        """Classify the type of answer needed"""
        query_lower = query.lower()
        
        # Check for comparison
        if any(word in query_lower for word in ["compare", "difference", "vs", "versus", "比较", "区别"]):
            return AnswerType.COMPARISON
        
        # Check for explanation
        if any(word in query_lower for word in ["explain", "why", "how", "解释", "为什么", "如何"]):
            return AnswerType.EXPLANATION
        
        # Check for procedural
        if any(word in query_lower for word in ["how to", "step", "process", "procedure", "步骤", "过程", "怎么做"]):
            return AnswerType.PROCEDURAL
        
        # Check if multiple documents might need synthesis
        unique_docs = set(chunk.document_id for chunk in context_chunks)
        if len(unique_docs) > 2:
            return AnswerType.SYNTHESIS
        
        return AnswerType.DIRECT
    
    async def _generate_follow_up_questions(self, query: str, answer: str) -> List[str]:
        """Generate relevant follow-up questions"""
        try:
            follow_up_prompt = f"""基于以下问答，生成3个相关的后续问题：

原问题: {query}
答案: {answer[:500]}...

请生成3个自然的后续问题，帮助用户深入了解相关话题。每个问题单独一行，不需要编号。"""
            
            messages = [
                {"role": "system", "content": "你是一个帮助用户探索知识的助手。"},
                {"role": "user", "content": follow_up_prompt}
            ]
            
            response = await self.llm_client.generate_completion(
                messages=messages,
                model=self.config.get("model", "gpt-4-turbo-preview"),
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse questions
            questions = [q.strip() for q in response["content"].split('\n') if q.strip()]
            return questions[:3]  # Limit to 3 questions
            
        except Exception as e:
            logger.warning(f"Failed to generate follow-up questions: {e}")
            return []
    
    def _calculate_confidence(self, response: Dict[str, Any], 
                            context_chunks: List[ContextChunk], 
                            citations: List[Dict[str, Any]]) -> float:
        """Calculate answer confidence score"""
        confidence_factors = []
        
        # Citation coverage
        if citations and context_chunks:
            citation_coverage = len(citations) / len(context_chunks)
            confidence_factors.append(min(citation_coverage, 1.0))
        else:
            confidence_factors.append(0.5)  # Medium confidence without citations
        
        # Source quality (average retrieval scores)
        if context_chunks:
            avg_source_score = sum(chunk.score for chunk in context_chunks) / len(context_chunks)
            confidence_factors.append(avg_source_score)
        else:
            confidence_factors.append(0.0)
        
        # Model finish reason
        finish_reason = response.get("finish_reason", "")
        if finish_reason == "stop":
            confidence_factors.append(1.0)
        elif finish_reason == "length":
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        # Answer length appropriateness
        answer_length = len(response.get("content", ""))
        if 100 <= answer_length <= 2000:
            confidence_factors.append(1.0)
        elif answer_length < 100:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.9)
        
        # Calculate weighted average
        return sum(confidence_factors) / len(confidence_factors)
    
    def _generate_no_context_answer(self, query: str) -> GeneratedAnswer:
        """Generate answer when no context is available"""
        return GeneratedAnswer(
            content="抱歉，我无法找到与您问题相关的信息。请尝试重新表述您的问题或确保相关文档已被正确索引。",
            answer_type=AnswerType.DIRECT,
            confidence=0.0,
            sources=[],
            model_used="none",
            generation_time=0.0,
            metadata={"reason": "no_context"}
        )
    
    def _generate_error_answer(self, query: str, error: str) -> GeneratedAnswer:
        """Generate answer for error cases"""
        return GeneratedAnswer(
            content=f"抱歉，在处理您的问题时遇到了技术问题。错误信息：{error}",
            answer_type=AnswerType.DIRECT,
            confidence=0.0,
            sources=[],
            model_used="error",
            generation_time=0.0,
            metadata={"error": error}
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test generation with simple query
            test_query = "Test query"
            test_results = []  # Empty results for testing
            
            # This should handle empty results gracefully
            answer = await self.generate_answer(test_query, test_results)
            
            return {
                "status": "healthy",
                "llm_provider": self.provider.value,
                "models_available": self.llm_client.get_available_models(),
                "test_generation": "success",
                "initialized": self._initialized,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized,
                "timestamp": datetime.now().isoformat()
            }