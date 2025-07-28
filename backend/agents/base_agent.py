from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from retrieval.arxiv_client import Paper
from utils.ai_client import AIClientFactory, BaseAIClient, ChatMessage

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Result from an agent's analysis"""
    agent_name: str
    analysis: str
    key_insights: List[str]
    breaking_points: List[str]
    implementation_ideas: List[str]
    confidence_score: float
    metadata: Dict[str, Any]

class BaseResearchAgent(ABC):
    """Base class for all research agents"""
    
    def __init__(self, name: str, role: str, expertise: List[str], 
                 model: str = "gpt-4o-mini", provider: str = "openai", api_key: str = None):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.model = model
        self.provider = provider
        self.api_key = api_key
        self.analysis_history: List[AnalysisResult] = []
        
        # Initialize AI client
        if api_key:
            self.ai_client = AIClientFactory.create_client(provider, api_key)
        else:
            self.ai_client = None
    
    @abstractmethod
    def analyze_paper(self, paper: Paper, context: Optional[Dict] = None) -> AnalysisResult:
        """
        Analyze a research paper from the agent's perspective
        
        Args:
            paper: Paper object to analyze
            context: Optional context from other agents or previous analysis
            
        Returns:
            AnalysisResult with the agent's findings
        """
        pass
    
    @abstractmethod
    def generate_insights(self, papers: List[Paper], topic: str) -> Dict[str, Any]:
        """
        Generate insights from multiple papers on a topic
        
        Args:
            papers: List of papers to analyze
            topic: Research topic
            
        Returns:
            Dictionary with insights and recommendations
        """
        pass
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are a {self.role} with expertise in {', '.join(self.expertise)}.
        
Your role is to analyze research papers from the perspective of a {self.role}.
Focus on:
- Technical feasibility and implementation challenges
- Practical applications and real-world implications
- Identifying key innovations and breakthrough points
- Potential limitations and areas for improvement
- Connections to existing work and future directions

Provide clear, actionable insights that reflect your expertise in {', '.join(self.expertise)}.
Be specific and concrete in your analysis."""
    
    def get_analysis_prompt(self, paper: Paper, context: Optional[Dict] = None) -> str:
        """Generate analysis prompt for a specific paper"""
        context_str = ""
        if context:
            context_str = f"\n\nAdditional context:\n{context}"
        
        return f"""Analyze the following research paper from your perspective as a {self.role}:

Title: {paper.title}
Authors: {', '.join(paper.authors)}
Categories: {', '.join(paper.categories)}
Abstract: {paper.abstract}

Please provide:
1. Key technical insights and innovations
2. Breaking points or limitations in the current approach
3. Practical implementation ideas for real-world applications
4. Your confidence level in the paper's claims (0-1 scale)
5. Connections to your area of expertise

{context_str}

Format your response as a structured analysis focusing on actionable insights."""
    
    def add_to_history(self, result: AnalysisResult):
        """Add analysis result to history"""
        self.analysis_history.append(result)
        logger.info(f"Added analysis result to {self.name} history")
    
    def get_recent_insights(self, n: int = 5) -> List[AnalysisResult]:
        """Get recent analysis results"""
        return self.analysis_history[-n:] if self.analysis_history else []
    
    def create_chat_completion(self, messages: list, temperature: float = 0.7, max_tokens: int = 1500) -> Dict[str, Any]:
        """Create a chat completion using the AI client"""
        if not self.ai_client:
            raise ValueError("AI client not initialized. Please provide an API key.")
        
        # Convert messages to ChatMessage format
        chat_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                chat_messages.append(ChatMessage(role=msg["role"], content=msg["content"]))
            elif isinstance(msg, ChatMessage):
                chat_messages.append(msg)
            else:
                raise ValueError(f"Invalid message format: {type(msg)}")
        
        response = self.ai_client.create_chat_completion(
            messages=chat_messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response.content,
            "model": response.model,
            "provider": response.provider,
            "usage": response.usage,
            "finish_reason": response.finish_reason
        }