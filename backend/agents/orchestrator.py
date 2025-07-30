import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dataclasses import dataclass

from retrieval.arxiv_client import ArxivClient, Paper
from database.vector_store_adapter import VectorStoreAdapter
from utils.query_expansion import QueryExpander
from utils.ai_client import ChatMessage
from .google_engineer_agent import GoogleEngineerAgent
from .mit_researcher_agent import MITResearcherAgent
from .industry_expert_agent import IndustryExpertAgent
from .paper_analyst_agent import PaperAnalystAgent
from .base_agent import AnalysisResult

logger = logging.getLogger(__name__)

@dataclass
class DiscussionRound:
    """Represents a single round in the iterative discussion"""
    round_number: int
    agent_name: str
    agent_response: str
    timestamp: datetime
    tokens_used: Optional[int] = None

@dataclass
class IterativeDiscussion:
    """Represents an iterative discussion between multiple agents"""
    query: str
    papers: List[Paper]
    rounds: List[DiscussionRound]
    started_at: datetime
    final_conclusion: Optional[str] = None
    completed_at: Optional[datetime] = None

@dataclass
class ResearchSession:
    """Represents a research session with multiple agents"""
    session_id: str
    topic: str
    papers: List[Paper]
    agent_analyses: Dict[str, List[AnalysisResult]]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "in_progress"

class ResearchOrchestrator:
    """Orchestrates multiple research agents for comprehensive analysis"""
    
    def __init__(self, 
                 openai_api_key: str = None,
                 deepseek_api_key: str = None,
                 anthropic_api_key: Optional[str] = None,
                 db_path: str = "./data/vector_db",
                 max_workers: int = 4,
                 default_provider: str = "openai",
                 agent_configs: Optional[Dict[str, Dict]] = None,
                 ai_client_configs: Optional[Dict[str, Dict]] = None):
        
        self.openai_api_key = openai_api_key
        self.deepseek_api_key = deepseek_api_key
        self.anthropic_api_key = anthropic_api_key
        self.max_workers = max_workers
        self.default_provider = default_provider
        self.ai_client_configs = ai_client_configs or {}
        
        # Initialize components
        self.arxiv_client = ArxivClient()
        
        # Initialize vector database adapter (maintains backward compatibility)
        self.vector_store = VectorStoreAdapter(db_path)
        
        # Initialize query expander with appropriate API key
        query_expander_key = openai_api_key or deepseek_api_key
        if query_expander_key:
            self.query_expander = QueryExpander(query_expander_key)
        else:
            self.query_expander = None
        
        # Initialize research agents with configuration
        self.agents = self._initialize_agents(agent_configs)
        
        # Session management
        self.active_sessions: Dict[str, ResearchSession] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def _initialize_agents(self, agent_configs: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
        """Initialize research agents with configuration"""
        agents = {}
        
        # Get API key for each provider
        api_keys = {
            "openai": self.openai_api_key,
            "deepseek": self.deepseek_api_key,
            "anthropic": self.anthropic_api_key
        }
        
        # Default agent configurations
        default_configs = {
            "google_engineer": {
                "provider": self.default_provider,
                "api_key": api_keys.get(self.default_provider),
                "model": "gpt-4o-mini"
            },
            "mit_researcher": {
                "provider": self.default_provider,
                "api_key": api_keys.get(self.default_provider),
                "model": "gpt-4o-mini"
            },
            "industry_expert": {
                "provider": self.default_provider,
                "api_key": api_keys.get(self.default_provider),
                "model": "gpt-4o-mini"
            },
            "paper_analyst": {
                "provider": self.default_provider,
                "api_key": api_keys.get(self.default_provider),
                "model": "gpt-4o-mini"
            }
        }
        
        # Override with custom configurations
        if agent_configs:
            for agent_name, config in agent_configs.items():
                if agent_name in default_configs:
                    default_configs[agent_name].update(config)
        
        # Create agents
        try:
            for agent_name, config in default_configs.items():
                if not config["api_key"]:
                    logger.warning(f"No API key provided for {agent_name}, skipping...")
                    continue
                
                if agent_name == "google_engineer":
                    agents[agent_name] = GoogleEngineerAgent(
                        api_key=config["api_key"],
                        model=config["model"],
                        provider=config["provider"]
                    )
                elif agent_name == "mit_researcher":
                    agents[agent_name] = MITResearcherAgent(
                        api_key=config["api_key"],
                        model=config["model"],
                        provider=config["provider"]
                    )
                elif agent_name == "industry_expert":
                    agents[agent_name] = IndustryExpertAgent(
                        api_key=config["api_key"],
                        model=config["model"],
                        provider=config["provider"]
                    )
                elif agent_name == "paper_analyst":
                    agents[agent_name] = PaperAnalystAgent(
                        api_key=config["api_key"],
                        model=config["model"],
                        provider=config["provider"]
                    )
            
            logger.info(f"Initialized {len(agents)} agents with {self.default_provider} provider")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise
        
        return agents
    
    async def research_topic(self, 
                           topic: str,
                           max_papers: int = 20,
                           include_recent: bool = True,
                           session_id: Optional[str] = None) -> ResearchSession:
        """
        Conduct comprehensive research on a topic using all agents
        
        Args:
            topic: Research topic to investigate
            max_papers: Maximum number of papers to retrieve
            include_recent: Whether to prioritize recent papers
            session_id: Optional session ID for tracking
            
        Returns:
            ResearchSession with complete analysis
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting research session {session_id} for topic: {topic}")
            
            # Step 1: Retrieve papers
            papers = await self._retrieve_papers(topic, max_papers, include_recent)
            if not papers:
                raise ValueError(f"No papers found for topic: {topic}")
            
            # Step 2: Store papers in vector database
            await self._store_papers(papers)
            
            # Step 3: Create research session
            session = ResearchSession(
                session_id=session_id,
                topic=topic,
                papers=papers,
                agent_analyses={},
                started_at=datetime.now()
            )
            self.active_sessions[session_id] = session
            
            # Step 4: Run parallel analysis with all agents
            agent_analyses = await self._run_parallel_analysis(papers, topic)
            session.agent_analyses = agent_analyses
            
            # Step 5: Generate cross-agent insights
            comprehensive_insights = await self._generate_comprehensive_insights(papers, topic, agent_analyses)
            session.comprehensive_insights = comprehensive_insights
            
            # Step 6: Complete session
            session.completed_at = datetime.now()
            session.status = "completed"
            
            logger.info(f"Completed research session {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error in research session {session_id}: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id].status = "error"
            raise
    
    async def analyze_specific_paper(self, 
                                   paper_id: str,
                                   agents: Optional[List[str]] = None) -> Dict[str, AnalysisResult]:
        """
        Analyze a specific paper with selected agents
        
        Args:
            paper_id: arXiv paper ID
            agents: List of agent names to use (default: all)
            
        Returns:
            Dictionary of agent analyses
        """
        try:
            # Retrieve paper
            paper = self.arxiv_client.get_paper_by_id(paper_id)
            if not paper:
                raise ValueError(f"Paper not found: {paper_id}")
            
            # Select agents
            selected_agents = agents or list(self.agents.keys())
            
            # Run analysis
            analyses = {}
            tasks = []
            
            for agent_name in selected_agents:
                if agent_name in self.agents:
                    task = self._run_agent_analysis(self.agents[agent_name], paper)
                    tasks.append((agent_name, task))
            
            # Execute in parallel
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for i, (agent_name, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(f"Error in {agent_name} analysis: {result}")
                else:
                    analyses[agent_name] = result
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error analyzing paper {paper_id}: {e}")
            raise
    
    def chat_with_papers(self, 
                        query: str,
                        session_id: Optional[str] = None,
                        n_papers: int = None,
                        min_similarity_threshold: float = 0.5,
                        enable_arxiv_fallback: bool = True) -> Dict[str, Any]:
        """
        Enhanced chat interface with multi-agent discussion based on paper content
        
        Args:
            query: User question
            session_id: Optional session to search within
            n_papers: Number of relevant papers to consider
            min_similarity_threshold: Minimum similarity score for vector results
            enable_arxiv_fallback: Whether to search ArXiv if vector DB has insufficient results
            
        Returns:
            Response with relevant papers and multi-agent discussion
        """
        try:
            logger.info(f"Enhanced chat query received: {query[:100]}...")
            logger.debug(f"Session ID: {session_id}, n_papers: {n_papers}, threshold: {min_similarity_threshold}")
            
            # Step 1: Expand the query for better search
            logger.info("Expanding query for better search coverage...")
            try:
                expanded_queries = self.query_expander.expand_query(query, max_expansions=3)
                logger.info(f"Query expanded to {len(expanded_queries)} variations: {expanded_queries}")
            except Exception as e:
                logger.warning(f"Query expansion failed, using original query: {e}")
                expanded_queries = [query]
            
            # Step 2: Search vector store with expanded queries
            all_vector_results = []
            for i, expanded_query in enumerate(expanded_queries):
                logger.info(f"Searching vector store with query {i+1}/{len(expanded_queries)}: {expanded_query}")
                # Get all available papers if n_papers is None, otherwise use the specified limit
                search_limit = n_papers if n_papers is not None else 1000  # Large number to get all
                search_results = self.vector_store.search_papers(expanded_query, n_results=search_limit)
                all_vector_results.extend(search_results)
            
            # Remove duplicates and sort by similarity
            unique_results = {}
            for result in all_vector_results:
                paper_id = result['metadata']['paper_id']
                if paper_id not in unique_results or result['similarity_score'] > unique_results[paper_id]['similarity_score']:
                    unique_results[paper_id] = result
            
            vector_results = sorted(unique_results.values(), key=lambda x: x['similarity_score'], reverse=True)
            # Only limit if n_papers is specified
            if n_papers is not None:
                vector_results = vector_results[:n_papers]
            
            # Filter by similarity threshold
            high_quality_results = [r for r in vector_results if r['similarity_score'] >= min_similarity_threshold]
            
            logger.info(f"Vector search completed: {len(vector_results)} total results, {len(high_quality_results)} above threshold")
            
            # Step 3: Check if we need ArXiv fallback
            arxiv_papers = []
            if enable_arxiv_fallback and len(high_quality_results) < 2:
                logger.info("Insufficient high-quality vector results, triggering ArXiv fallback search...")
                try:
                    # Get more papers from ArXiv if n_papers is None
                    arxiv_limit = n_papers if n_papers is not None else 10
                    arxiv_papers = self._arxiv_fallback_search(query, max_papers=arxiv_limit)
                    logger.info(f"ArXiv fallback returned {len(arxiv_papers)} papers")
                except Exception as e:
                    logger.error(f"ArXiv fallback search failed: {e}")
            
            # Step 4: Combine results and extract paper information
            relevant_papers = []
            
            # Add vector search results
            for i, result in enumerate(high_quality_results):
                logger.debug(f"Processing vector result {i+1}/{len(high_quality_results)}")
                metadata = result['metadata']
                relevant_papers.append({
                    "paper_id": metadata['paper_id'],
                    "title": metadata['title'],
                    "authors": metadata['authors'],
                    "similarity_score": result['similarity_score'],
                    "relevant_text": result['document'],
                    "source": "vector_db"
                })
            
            # Add ArXiv papers if any
            for i, paper in enumerate(arxiv_papers):
                logger.debug(f"Processing ArXiv paper {i+1}/{len(arxiv_papers)}")
                relevant_papers.append({
                    "paper_id": paper.id,
                    "title": paper.title,
                    "authors": ", ".join(paper.authors),
                    "similarity_score": 0.8,  # Assign high score for ArXiv results
                    "relevant_text": paper.abstract or paper.summary,
                    "source": "arxiv_search",
                    "pdf_url": paper.pdf_url,
                    "published": paper.published.isoformat() if paper.published else None
                })
            
            logger.info(f"Total relevant papers: {len(relevant_papers)} ({len(high_quality_results)} from vector DB, {len(arxiv_papers)} from ArXiv)")
            
            # Step 5: Generate multi-agent discussion
            if not relevant_papers:
                logger.warning("No relevant papers found from any source")
                return {
                    "response": "I couldn't find relevant papers for your query. Try rephrasing your question or using more specific academic terms.",
                    "relevant_papers": [],
                    "agent_discussions": {},
                    "search_strategy": "expanded_query_with_arxiv_fallback",
                    "expanded_queries": expanded_queries
                }
            
            # Generate multi-agent discussion
            logger.info("Generating multi-agent discussion based on paper content...")
            agent_discussions = self._generate_multi_agent_discussion(query, relevant_papers)
            
            # Generate comprehensive response
            logger.info("Generating comprehensive response with multi-agent insights...")
            response = self._generate_comprehensive_discussion_response(query, relevant_papers, agent_discussions, expanded_queries)
            logger.info("Multi-agent discussion response generated successfully")
            
            result = {
                "response": response,
                "relevant_papers": relevant_papers,
                "agent_discussions": agent_discussions,
                "session_id": session_id,
                "query": query,
                "search_strategy": "expanded_query_with_arxiv_fallback",
                "expanded_queries": expanded_queries,
                "vector_results_count": len(high_quality_results),
                "arxiv_results_count": len(arxiv_papers)
            }
            
            logger.info("Enhanced chat query completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error in enhanced chat query: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "response": f"Error processing query: {e}",
                "relevant_papers": [],
                "agent_discussions": {},
                "search_strategy": "error"
            }
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a research session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "status": session.status,
            "paper_count": len(session.papers),
            "agents_completed": len(session.agent_analyses),
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
    
    async def _retrieve_papers(self, topic: str, max_papers: int, include_recent: bool) -> List[Paper]:
        """Retrieve papers for the given topic"""
        try:
            if include_recent:
                # Get recent papers first
                recent_papers = self.arxiv_client.search_recent_papers(
                    topic, days_back=30, max_results=max_papers // 2
                )
                # Get general papers
                general_papers = self.arxiv_client.search_papers(
                    topic, max_results=max_papers // 2
                )
                # Combine and deduplicate
                all_papers = recent_papers + general_papers
                seen_ids = set()
                unique_papers = []
                for paper in all_papers:
                    if paper.id not in seen_ids:
                        seen_ids.add(paper.id)
                        unique_papers.append(paper)
                return unique_papers[:max_papers]
            else:
                return self.arxiv_client.search_papers(topic, max_results=max_papers)
                
        except Exception as e:
            logger.error(f"Error retrieving papers: {e}")
            return []
    
    async def _store_papers(self, papers: List[Paper]):
        """Store papers in vector database"""
        try:
            for paper in papers:
                # Download paper text if not already present
                if not paper.full_text:
                    self.arxiv_client.download_paper_text(paper)
                
                # Add to vector store
                self.vector_store.add_paper(paper)
                
            logger.info(f"Stored {len(papers)} papers in vector database")
            
        except Exception as e:
            logger.error(f"Error storing papers: {e}")
            raise
    
    async def _run_parallel_analysis(self, papers: List[Paper], topic: str) -> Dict[str, List[AnalysisResult]]:
        """Run analysis with all agents in parallel"""
        try:
            agent_analyses = {}
            
            # Create tasks for each agent
            tasks = []
            for agent_name, agent in self.agents.items():
                task = self._run_agent_on_papers(agent, papers, topic)
                tasks.append((agent_name, task))
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            # Process results
            for i, (agent_name, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(f"Error in {agent_name} analysis: {result}")
                    agent_analyses[agent_name] = []
                else:
                    agent_analyses[agent_name] = result
            
            return agent_analyses
            
        except Exception as e:
            logger.error(f"Error in parallel analysis: {e}")
            return {}
    
    async def _run_agent_on_papers(self, agent, papers: List[Paper], topic: str) -> List[AnalysisResult]:
        """Run a single agent on all papers"""
        try:
            # Analyze individual papers
            individual_analyses = []
            for paper in papers:  # Analyze all papers
                analysis = await self._run_agent_analysis(agent, paper)
                individual_analyses.append(analysis)
            
            # Generate insights from all papers
            insights = await asyncio.to_thread(agent.generate_insights, papers, topic)
            
            return individual_analyses
            
        except Exception as e:
            logger.error(f"Error running agent {agent.name}: {e}")
            return []
    
    async def _run_agent_analysis(self, agent, paper: Paper) -> AnalysisResult:
        """Run analysis for a single agent on a single paper"""
        return await asyncio.to_thread(agent.analyze_paper, paper)
    
    async def _generate_comprehensive_insights(self, 
                                             papers: List[Paper], 
                                             topic: str, 
                                             agent_analyses: Dict[str, List[AnalysisResult]]) -> Dict[str, Any]:
        """Generate comprehensive insights from all agent analyses"""
        try:
            # Collect all insights
            all_insights = []
            all_breaking_points = []
            all_implementation_ideas = []
            
            for agent_name, analyses in agent_analyses.items():
                for analysis in analyses:
                    all_insights.extend(analysis.key_insights)
                    all_breaking_points.extend(analysis.breaking_points)
                    all_implementation_ideas.extend(analysis.implementation_ideas)
            
            # Generate cross-agent synthesis
            synthesis = {
                "topic": topic,
                "paper_count": len(papers),
                "total_analyses": sum(len(analyses) for analyses in agent_analyses.values()),
                "key_themes": self._extract_themes(all_insights),
                "major_breaking_points": self._extract_themes(all_breaking_points),
                "implementation_opportunities": self._extract_themes(all_implementation_ideas),
                "agent_consensus": self._analyze_agent_consensus(agent_analyses),
                "research_recommendations": self._generate_research_recommendations(agent_analyses)
            }
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Error generating comprehensive insights: {e}")
            return {"error": str(e)}
    
    def _generate_chat_response(self, query: str, relevant_papers: List[Dict]) -> str:
        """Generate a response for chat queries"""
        if not relevant_papers:
            return "I couldn't find any relevant papers for your question."
        
        # Simple response generation (can be enhanced with LLM)
        response = f"Based on {len(relevant_papers)} relevant papers, here's what I found:\n\n"
        
        for i, paper in enumerate(relevant_papers, 1):
            response += f"{i}. **{paper['title']}** by {paper['authors']}\n"
            response += f"   Relevance: {paper['similarity_score']:.2f}\n"
            response += f"   Key excerpt: {paper['relevant_text'][:200]}...\n\n"
        
        return response
    
    def _arxiv_fallback_search(self, query: str, max_papers: int = 10) -> List[Paper]:
        """
        Fallback search using ArXiv when vector DB has insufficient results
        
        Args:
            query: Original search query
            max_papers: Maximum papers to retrieve
            
        Returns:
            List of Paper objects from ArXiv
        """
        try:
            logger.info(f"Starting ArXiv fallback search for: {query}")
            
            # Generate ArXiv-optimized queries
            arxiv_queries = self.query_expander.generate_arxiv_search_queries(query)
            logger.info(f"Generated {len(arxiv_queries)} ArXiv queries: {arxiv_queries}")
            
            all_papers = []
            seen_ids = set()
            
            # Search with each query
            for i, arxiv_query in enumerate(arxiv_queries):
                logger.info(f"Searching ArXiv with query {i+1}/{len(arxiv_queries)}: {arxiv_query}")
                try:
                    papers = self.arxiv_client.search_papers(arxiv_query, max_results=max_papers)
                    logger.info(f"ArXiv query {i+1} returned {len(papers)} papers")
                    
                    # Add unique papers
                    for paper in papers:
                        if paper.id not in seen_ids:
                            seen_ids.add(paper.id)
                            all_papers.append(paper)
                            
                            # Store in vector DB for future searches
                            try:
                                self.vector_store.add_paper(paper)
                                logger.debug(f"Added ArXiv paper {paper.id} to vector DB")
                            except Exception as e:
                                logger.warning(f"Failed to add ArXiv paper to vector DB: {e}")
                    
                    # Stop if we have enough papers
                    if len(all_papers) >= max_papers:
                        break
                        
                except Exception as e:
                    logger.error(f"ArXiv search failed for query '{arxiv_query}': {e}")
                    continue
            
            # Limit results
            result_papers = all_papers[:max_papers]
            logger.info(f"ArXiv fallback search completed: {len(result_papers)} papers found")
            return result_papers
            
        except Exception as e:
            logger.error(f"ArXiv fallback search failed: {e}")
            return []
    

    
    def _extract_themes(self, insights: List[str]) -> List[str]:
        """Extract common themes from insights"""
        # Simplified theme extraction
        themes = {}
        for insight in insights:
            words = insight.lower().split()
            for word in words:
                if len(word) > 5:  # Filter short words
                    themes[word] = themes.get(word, 0) + 1
        
        # Return all themes
        sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes]
    
    def _analyze_agent_consensus(self, agent_analyses: Dict[str, List[AnalysisResult]]) -> Dict[str, Any]:
        """Analyze consensus between agents"""
        if not agent_analyses:
            return {}
        
        # Calculate average confidence by agent
        agent_confidence = {}
        for agent_name, analyses in agent_analyses.items():
            if analyses:
                avg_confidence = sum(a.confidence_score for a in analyses) / len(analyses)
                agent_confidence[agent_name] = avg_confidence
        
        return {
            "agent_confidence_scores": agent_confidence,
            "overall_confidence": sum(agent_confidence.values()) / len(agent_confidence) if agent_confidence else 0,
            "consensus_level": "high" if all(c > 0.7 for c in agent_confidence.values()) else "moderate"
        }
    
    def _generate_research_recommendations(self, agent_analyses: Dict[str, List[AnalysisResult]]) -> List[str]:
        """Generate research recommendations based on agent analyses"""
        recommendations = []
        
        # Extract common implementation ideas
        all_ideas = []
        for analyses in agent_analyses.values():
            for analysis in analyses:
                all_ideas.extend(analysis.implementation_ideas)
        
        # Simple recommendation generation
        if all_ideas:
            recommendations.append("Focus on scalable implementation based on engineering insights")
            recommendations.append("Conduct thorough theoretical validation as highlighted by academic analysis")
            recommendations.append("Evaluate commercial viability and market readiness")
            recommendations.append("Address identified breaking points and limitations")
        
        return recommendations
    
    def _generate_multi_agent_discussion(self, query: str, relevant_papers: List[Dict]) -> Dict[str, Any]:
        """
        Generate iterative multi-agent discussion based on paper content
        
        This creates a conversation-like flow where agents build on each other's insights
        rather than providing independent parallel analyses.
        
        Args:
            query: Original user query
            relevant_papers: List of relevant papers found
            
        Returns:
            Dictionary containing the iterative discussion and final conclusion
        """
        try:
            logger.info(f"Starting iterative multi-agent discussion for {len(relevant_papers)} papers")
            
            # Convert paper dicts to Paper objects for agent analysis
            papers_for_analysis = []
            for paper_dict in relevant_papers:
                paper = Paper(
                    id=paper_dict['paper_id'],
                    title=paper_dict['title'],
                    authors=paper_dict['authors'].split(', ') if isinstance(paper_dict['authors'], str) else paper_dict['authors'],
                    abstract=paper_dict.get('relevant_text', ''),
                    categories=[],
                    published=datetime.now(),
                    updated=datetime.now(),
                    pdf_url=paper_dict.get('pdf_url', ''),
                    entry_id=paper_dict['paper_id'],
                    summary=paper_dict.get('relevant_text', ''),
                    full_text=paper_dict.get('relevant_text', '')
                )
                papers_for_analysis.append(paper)
            
            # Create iterative discussion
            discussion = IterativeDiscussion(
                query=query,
                papers=papers_for_analysis,
                rounds=[],
                started_at=datetime.now()
            )
            
            # Define agent order for the discussion
            agent_order = ["google_engineer", "mit_researcher", "industry_expert", "paper_analyst"]
            available_agents = [name for name in agent_order if name in self.agents]
            
            logger.info(f"Discussion will proceed with {len(available_agents)} agents in order: {available_agents}")
            
            # Run iterative discussion rounds
            for round_num, agent_name in enumerate(available_agents, 1):
                try:
                    logger.info(f"Round {round_num}: {agent_name} is contributing...")
                    
                    # Create context-aware prompt for this agent
                    agent_prompt = self._create_iterative_discussion_prompt(
                        agent_name, query, papers_for_analysis, discussion.rounds
                    )
                    
                    # Get agent's contribution to the discussion
                    agent = self.agents[agent_name]
                    response = self._get_iterative_agent_response(agent, agent_prompt)
                    
                    # Add round to discussion
                    round_entry = DiscussionRound(
                        round_number=round_num,
                        agent_name=agent_name,
                        agent_response=response,
                        timestamp=datetime.now()
                    )
                    discussion.rounds.append(round_entry)
                    
                    logger.info(f"Round {round_num} completed for {agent_name}")
                    
                except Exception as e:
                    logger.error(f"Error in round {round_num} for {agent_name}: {e}")
                    # Add error round but continue with other agents
                    error_round = DiscussionRound(
                        round_number=round_num,
                        agent_name=agent_name,
                        agent_response=f"Error generating response: {e}",
                        timestamp=datetime.now()
                    )
                    discussion.rounds.append(error_round)
            
            # Generate final conclusion from the entire discussion
            logger.info("Generating final conclusion from the discussion...")
            discussion.final_conclusion = self._generate_final_conclusion(discussion)
            discussion.completed_at = datetime.now()
            
            # Format response to maintain compatibility with existing interface
            return {
                "iterative_discussion": discussion,
                "discussion_rounds": [
                    {
                        "round": round.round_number,
                        "agent": round.agent_name,
                        "response": round.agent_response,
                        "timestamp": round.timestamp.isoformat()
                    }
                    for round in discussion.rounds
                ],
                "final_conclusion": discussion.final_conclusion,
                "total_rounds": len(discussion.rounds),
                "agents_participated": list(set(round.agent_name for round in discussion.rounds))
            }
            
        except Exception as e:
            logger.error(f"Error in iterative multi-agent discussion: {e}")
            return {"error": str(e)}
    
    def _create_agent_discussion_prompt(self, agent_name: str, query: str, papers: List[Paper]) -> str:
        """Create a discussion prompt for a specific agent"""
        
        # Agent-specific discussion focuses
        discussion_focuses = {
            "google_engineer": {
                "title": "Engineering & Implementation Perspective",
                "focus": [
                    "Latest engineering approaches and scalable implementations",
                    "Technical challenges and production deployment issues", 
                    "Practical applications in real-world systems",
                    "New engineering directions and architectural innovations"
                ]
            },
            "mit_researcher": {
                "title": "Academic Research & Theoretical Perspective", 
                "focus": [
                    "Latest research trends and theoretical breakthroughs",
                    "Scientific problems and methodological limitations",
                    "Academic applications and research opportunities",
                    "New research directions and unexplored areas"
                ]
            },
            "industry_expert": {
                "title": "Industry & Commercial Perspective",
                "focus": [
                    "Latest industry trends and market opportunities",
                    "Business challenges and commercialization issues",
                    "Practical applications in industry settings",
                    "New business directions and market innovations"
                ]
            },
            "paper_analyst": {
                "title": "Research Analysis & Methodological Perspective",
                "focus": [
                    "Latest methodological innovations and experimental designs",
                    "Research quality issues and methodological limitations", 
                    "Applications in research and analysis contexts",
                    "New analytical directions and methodological advances"
                ]
            }
        }
        
        focus_info = discussion_focuses.get(agent_name, {
            "title": "General Analysis",
            "focus": ["Latest developments", "Problems and challenges", "Practical applications", "New directions"]
        })
        
        papers_summary = "\n\n".join([
            f"**Paper {i+1}**: {paper.title}\n"
            f"Authors: {', '.join(paper.authors)}\n"
            f"Key content: {paper.abstract[:300]}..."
            for i, paper in enumerate(papers)  # Include all papers
        ])
        
        prompt = f"""As a {focus_info['title']}, analyze the following papers in relation to the query: "{query}"

**Papers to analyze:**
{papers_summary}

**Discussion Structure:**
Please provide a comprehensive discussion covering:

1. **Latest Research & Developments** ({focus_info['focus'][0]}):
   - What are the most recent advances in this area?
   - What new approaches or methods are being explored?

2. **Problems & Challenges** ({focus_info['focus'][1]}):
   - What are the main limitations or issues with current approaches?
   - What technical/scientific/business challenges remain?

3. **Practical Applications** ({focus_info['focus'][2]}):
   - How can these developments be applied in practice?
   - What are the most promising use cases?

4. **New Directions & Opportunities** ({focus_info['focus'][3]}):
   - What unexplored areas or new directions should be pursued?
   - What are the next logical steps for advancement?

Provide specific, actionable insights from your perspective. Be concrete and practical in your analysis."""
        
        return prompt
    
    def _get_agent_discussion(self, agent, query: str, papers: List[Paper], discussion_prompt: str) -> str:
        """Get discussion from a specific agent"""
        try:
            # Use the agent's generate_insights method if available
            if hasattr(agent, 'generate_insights'):
                insights = agent.generate_insights(papers, query)
                if isinstance(insights, dict) and 'discussion' in insights:
                    return insights['discussion']
                elif isinstance(insights, str):
                    return insights
                else:
                    # Fallback to generating discussion manually
                    return self._generate_manual_discussion(agent, query, papers, discussion_prompt)
            else:
                # Fallback to manual discussion generation
                return self._generate_manual_discussion(agent, query, papers, discussion_prompt)
                
        except Exception as e:
            logger.error(f"Error getting discussion from {agent.name}: {e}")
            return f"Error generating discussion: {e}"
    
    def _generate_manual_discussion(self, agent, query: str, papers: List[Paper], discussion_prompt: str) -> str:
        """Generate discussion manually using the agent's model"""
        try:
            # This would use the agent's OpenAI client to generate discussion
            # For now, return a structured discussion based on the prompt
            return f"""## {agent.name} Analysis

Based on the analysis of {len(papers)} relevant papers, here are my insights:

### Latest Research & Developments
- Recent advances in the field show promising directions
- New methodologies and approaches are emerging
- Key innovations are being developed

### Problems & Challenges  
- Several technical and practical challenges remain
- Limitations in current approaches need to be addressed
- Scalability and implementation issues exist

### Practical Applications
- Multiple real-world applications are possible
- Industry adoption potential is significant
- Engineering implementation opportunities exist

### New Directions & Opportunities
- Unexplored areas offer exciting possibilities
- Next steps for advancement are clear
- Innovation opportunities are abundant

*This analysis is based on the provided papers and my expertise in {', '.join(agent.expertise)}.*"""
            
        except Exception as e:
            logger.error(f"Error in manual discussion generation: {e}")
            return f"Error generating discussion: {e}"
    
    def _get_agent_focus_areas(self, agent_name: str) -> List[str]:
        """Get focus areas for a specific agent"""
        focus_areas = {
            "google_engineer": ["Engineering", "Scalability", "Production", "Infrastructure"],
            "mit_researcher": ["Research", "Theory", "Academic", "Methodology"],
            "industry_expert": ["Business", "Market", "Commercial", "Industry"],
            "paper_analyst": ["Analysis", "Methodology", "Research Quality", "Experimental Design"]
        }
        return focus_areas.get(agent_name, ["General Analysis"])
    
    def _generate_cross_agent_synthesis(self, agent_discussions: Dict[str, Any], query: str, papers: List[Paper]) -> Dict[str, Any]:
        """Generate synthesis of all agent discussions"""
        try:
            # Extract key themes from all discussions
            all_themes = []
            consensus_points = []
            conflicting_views = []
            
            for agent_name, discussion in agent_discussions.items():
                if agent_name == "synthesis":
                    continue
                    
                if isinstance(discussion, dict) and "discussion" in discussion:
                    discussion_text = discussion["discussion"]
                else:
                    discussion_text = str(discussion)
                
                # Extract themes from discussion
                themes = self._extract_themes_from_discussion(discussion_text)
                all_themes.extend(themes)
            
            # Generate synthesis
            synthesis = {
                "key_themes": list(set(all_themes)),  # All unique themes
                "consensus_points": consensus_points,
                "conflicting_views": conflicting_views,
                "recommendations": self._generate_synthesis_recommendations(agent_discussions, query),
                "summary": f"Multi-agent analysis of {len(papers)} papers reveals {len(set(all_themes))} key themes and areas for further investigation."
            }
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Error generating cross-agent synthesis: {e}")
            return {"error": str(e)}
    
    def _extract_themes_from_discussion(self, discussion_text: str) -> List[str]:
        """Extract key themes from discussion text"""
        # Simple theme extraction - in production, use more sophisticated NLP
        themes = []
        lines = discussion_text.split('\n')
        
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('•'):
                theme = line.strip()[1:].strip()
                if len(theme) > 10:  # Filter out very short themes
                    themes.append(theme)
        
        return themes  # Return all themes
    
    def _generate_synthesis_recommendations(self, agent_discussions: Dict[str, Any], query: str) -> List[str]:
        """Generate recommendations based on all agent discussions"""
        recommendations = [
            "Consider multiple perspectives when evaluating research findings",
            "Balance theoretical insights with practical implementation concerns", 
            "Evaluate both academic rigor and commercial viability",
            "Address identified challenges through interdisciplinary collaboration",
            "Explore emerging opportunities through systematic research"
        ]
        return recommendations
    
    def _generate_comprehensive_discussion_response(self, query: str, relevant_papers: List[Dict], 
                                                  agent_discussions: Dict[str, Any], expanded_queries: List[str]) -> str:
        """Generate comprehensive response with iterative multi-agent discussion"""
        try:
            response_parts = []
            
            # Check if this is the new iterative discussion format
            if "final_conclusion" in agent_discussions and "discussion_rounds" in agent_discussions:
                # New iterative format - emphasize the final result
                response_parts.append(f"# 研究分析结果\n\n")
                response_parts.append(f"**查询问题**: {query}\n\n")
                
                # Show the final conclusion prominently
                final_conclusion = agent_discussions.get("final_conclusion", "")
                if final_conclusion:
                    response_parts.append(f"## 🎯 **最终分析结论**\n\n")
                    response_parts.append(final_conclusion)
                    response_parts.append("\n\n")
                
                # Show search strategy if expanded queries were used
                if len(expanded_queries) > 1:
                    response_parts.append(f"**🔍 搜索策略**: 扩展查询至: {', '.join(expanded_queries[1:])}\n\n")
                
                # Show the discussion flow (but make it secondary to the conclusion)
                discussion_rounds = agent_discussions.get("discussion_rounds", [])
                if discussion_rounds:
                    response_parts.append(f"---\n\n")
                    response_parts.append(f"## 💬 **专家讨论过程**\n\n")
                    response_parts.append(f"*我们的{len(discussion_rounds)}位研究专家通过{len(discussion_rounds)}轮分析讨论了您的问题：*\n\n")
                    
                    for round_data in discussion_rounds:
                        agent_name = round_data.get("agent", "")
                        agent_emoji = self._get_agent_emoji(agent_name)
                        agent_title = self._get_agent_title(agent_name)
                        response = round_data.get("response", "")
                        round_num = round_data.get("round", 0)
                        
                        response_parts.append(f"**Round {round_num} - {agent_emoji} {agent_title}**\n")
                        response_parts.append(f"{response[:300]}..." if len(response) > 300 else response)
                        response_parts.append("\n\n")
                
                # Show papers analyzed
                if relevant_papers:
                    response_parts.append(f"---\n\n")
                    response_parts.append(f"## 📚 **分析的论文** ({len(relevant_papers)} 篇论文)\n\n")
                    for i, paper in enumerate(relevant_papers[:5], 1):  # Show top 5
                        response_parts.append(f"**{i}.** {paper['title']}\n")
                        response_parts.append(f"   作者: {paper['authors']}\n")
                        response_parts.append(f"   相关性: {paper.get('similarity_score', 0):.2f}\n\n")
                    
                    if len(relevant_papers) > 5:
                        response_parts.append(f"*...以及另外{len(relevant_papers) - 5}篇论文*\n\n")
                
            else:
                # Fallback to old format if needed
                response_parts.append(f"# Multi-Agent Research Discussion\n\n")
                response_parts.append(f"**Query**: {query}\n\n")
                response_parts.append(f"I analyzed {len(relevant_papers)} relevant papers with our research agents. Here's their comprehensive discussion:\n\n")
                
                # Show expanded queries if used
                if len(expanded_queries) > 1:
                    response_parts.append(f"**🔍 Search Strategy**: Expanded query to: {', '.join(expanded_queries[1:])}\n\n")
                
                # Show agent discussions
                for agent_name, discussion_data in agent_discussions.items():
                    if agent_name in ["synthesis", "iterative_discussion", "discussion_rounds", "final_conclusion"]:
                        continue
                        
                    agent_emoji = self._get_agent_emoji(agent_name)
                    agent_title = self._get_agent_title(agent_name)
                    
                    response_parts.append(f"## {agent_emoji} {agent_title}\n\n")
                    
                    if isinstance(discussion_data, dict) and "discussion" in discussion_data:
                        discussion_text = discussion_data["discussion"]
                    else:
                        discussion_text = str(discussion_data)
                    
                    response_parts.append(discussion_text)
                    response_parts.append("\n\n")
            
            # Join all parts and return
            return "".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error generating comprehensive discussion response: {e}")
            return f"Error generating response: {e}"
    
    def _get_agent_emoji(self, agent_name: str) -> str:
        """Get emoji for agent"""
        emojis = {
            "google_engineer": "⚙️",
            "mit_researcher": "🎓", 
            "industry_expert": "💼",
            "paper_analyst": "📊"
        }
        return emojis.get(agent_name, "🤖")
    
    def _get_agent_title(self, agent_name: str) -> str:
        """Get display title for agent"""
        titles = {
            "google_engineer": "Google Engineer",
            "mit_researcher": "MIT Researcher",
            "industry_expert": "Industry Expert", 
            "paper_analyst": "Paper Analyst"
        }
        return titles.get(agent_name, agent_name.title())
    
    def _generate_simple_response(self, query: str, relevant_papers: List[Dict], expanded_queries: List[str]) -> str:
        """Generate a simple fallback response"""
        response = f"Based on {len(relevant_papers)} relevant papers, here's what I found:\n\n"
        
        for i, paper in enumerate(relevant_papers, 1):
            response += f"{i}. **{paper['title']}** by {paper['authors']}\n"
            response += f"   Relevance: {paper['similarity_score']:.2f}\n"
            response += f"   Key excerpt: {paper['relevant_text'][:200]}...\n\n"
        
        return response

    def _create_iterative_discussion_prompt(self, agent_name: str, query: str, papers: List[Paper], 
                                          previous_rounds: List[DiscussionRound]) -> str:
        """Create a context-aware discussion prompt for iterative discussion"""
        
        # Agent role descriptions
        agent_roles = {
            "google_engineer": {
                "title": "Senior Software Engineer at Google",
                "focus": "engineering implementation, scalability, production systems, and technical architecture",
                "perspective": "practical implementation and engineering best practices"
            },
            "mit_researcher": {
                "title": "Research Scientist at MIT",
                "focus": "theoretical foundations, research methodology, academic rigor, and scientific advancement",
                "perspective": "academic research and theoretical analysis"
            },
            "industry_expert": {
                "title": "Industry Technology Expert",
                "focus": "market trends, business applications, commercialization, and industry adoption",
                "perspective": "business viability and market impact"
            },
            "paper_analyst": {
                "title": "Research Paper Analyst",
                "focus": "methodological analysis, research quality, experimental design, and data interpretation",
                "perspective": "research methodology and analytical rigor"
            }
        }
        
        role_info = agent_roles.get(agent_name, {
            "title": "Research Expert",
            "focus": "general analysis and insights",
            "perspective": "expert analysis"
        })
        
        # Create papers summary
        papers_summary = "\n".join([
            f"**Paper {i+1}**: {paper.title}\n"
            f"Authors: {', '.join(paper.authors)}\n"
            f"Abstract: {paper.abstract[:300]}..."
            for i, paper in enumerate(papers[:5])  # Limit to top 5 papers
        ])
        
        # Create discussion context from previous rounds
        discussion_context = ""
        if previous_rounds:
            discussion_context = "\n**Previous Discussion:**\n"
            for round in previous_rounds:
                agent_title = self._get_agent_title(round.agent_name)
                discussion_context += f"\n**{agent_title}**: {round.agent_response[:300]}...\n"
        
        # Create the prompt based on whether this is the first round or not
        if not previous_rounds:
            # First round - initiate the discussion
            prompt = f"""You are a {role_info['title']} participating in a research discussion about: "{query}"

**Research Papers:**
{papers_summary}

**Your Role:**
As the first contributor to this discussion, please provide your analysis focusing on {role_info['focus']}. Your {role_info['perspective']} will set the foundation for our discussion.

**Please structure your response as follows:**
1. **Key Findings**: What are the most important insights from these papers relevant to the query?
2. **Your Perspective**: Based on your expertise in {role_info['focus']}, what stands out to you?
3. **Critical Questions**: What questions or challenges do you see that need further discussion?
4. **Implications**: What are the practical implications of these findings?

Keep your response focused and substantive (aim for 300-500 words)."""

        else:
            # Subsequent rounds - respond to previous discussion
            prompt = f"""You are a {role_info['title']} participating in an ongoing research discussion about: "{query}"

**Research Papers:**
{papers_summary}
{discussion_context}

**Your Role:**
As a {role_info['title']}, please contribute to this discussion by building on the previous insights while adding your unique perspective on {role_info['focus']}.

**Please structure your response as follows:**
1. **Response to Previous Points**: Address or build upon the most relevant points from the previous discussion
2. **Your Additional Insights**: What new perspectives can you add based on your expertise in {role_info['focus']}?
3. **Areas of Agreement/Disagreement**: Where do you agree or respectfully disagree with previous contributors?
4. **New Directions**: What additional aspects should we consider?

Keep your response focused and substantive (aim for 300-500 words). Be conversational and reference specific points from the previous discussion."""

        return prompt

    def _get_iterative_agent_response(self, agent, prompt: str) -> str:
        """Get agent's response for iterative discussion"""
        try:
            # Use the agent's AI client to generate response
            if hasattr(agent, 'ai_client') and agent.ai_client:
                messages = [
                    ChatMessage(role="system", content="You are a research expert participating in a scholarly discussion. Provide thoughtful, substantive responses that build on the conversation."),
                    ChatMessage(role="user", content=prompt)
                ]
                
                response = agent.ai_client.create_chat_completion(
                    messages=messages,
                    model=agent.model,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                return response.content
            else:
                # Fallback response if no AI client
                return f"As a {self._get_agent_title(agent.name)}, I would analyze these papers focusing on my expertise areas. However, the AI client is not available for detailed analysis."
                
        except Exception as e:
            logger.error(f"Error generating iterative response for {agent.name}: {e}")
            return f"Error generating response from {self._get_agent_title(agent.name)}: {e}"

    def _generate_final_conclusion(self, discussion: IterativeDiscussion) -> str:
        """Generate final conclusion from the entire iterative discussion"""
        try:
            # Collect all agent responses
            all_responses = [round.agent_response for round in discussion.rounds]
            discussion_text = "\n\n".join([
                f"**{self._get_agent_title(round.agent_name)}**: {round.agent_response}"
                for round in discussion.rounds
            ])
            
            # Create synthesis prompt for Chinese output
            synthesis_prompt = f"""基于以下关于"{discussion.query}"的多专家研究讨论，请提供一个全面的最终结论。

**研究讨论内容：**
{discussion_text}

**请提供一个最终结论，包含以下内容：**
1. **综合关键发现**：整合所有贡献者的重要见解
2. **识别共识**：突出专家们达成一致的领域
3. **处理分歧**：承认并解决任何冲突的观点
4. **提供可行洞察**：提供清晰、实用的要点
5. **建议后续步骤**：推荐具体的后续行动或研究方向

请用中文清晰地组织您的结论，使其全面而简洁（目标400-600字）。这应该是一个决定性的答案，让读者能够理解整个讨论的意义和影响。

请确保：
- 使用专业但易懂的中文表达
- 结构清晰，逻辑性强
- 重点突出最重要的研究发现和实用建议
- 避免重复，保持内容的精炼性"""

            # Use the first available agent's AI client to generate the synthesis
            if self.agents:
                first_agent = next(iter(self.agents.values()))
                if hasattr(first_agent, 'ai_client') and first_agent.ai_client:
                    messages = [
                        ChatMessage(role="system", content="你是一位研究综合专家。你的工作是从多专家讨论中创建全面的最终结论。请始终用中文回答，使用专业但易懂的语言，确保结构清晰、逻辑性强。"),
                        ChatMessage(role="user", content=synthesis_prompt)
                    ]
                    
                    response = first_agent.ai_client.create_chat_completion(
                        messages=messages,
                        model=first_agent.model,
                        max_tokens=1500,
                        temperature=0.3  # Lower temperature for more focused synthesis
                    )
                    
                    return response.content
            
            # Fallback synthesis if no AI client available
            return self._create_manual_synthesis(discussion)
            
        except Exception as e:
            logger.error(f"Error generating final conclusion: {e}")
            return f"Error generating final conclusion: {e}"

    def _create_manual_synthesis(self, discussion: IterativeDiscussion) -> str:
        """Create a manual synthesis as fallback - Chinese output"""
        conclusion = f"## 最终分析总结\n\n**研究问题**: {discussion.query}\n\n"
        conclusion += f"基于{len(discussion.rounds)}位专家对{len(discussion.papers)}篇研究论文的讨论分析：\n\n"
        
        for i, round in enumerate(discussion.rounds, 1):
            agent_title = self._get_agent_title(round.agent_name)
            conclusion += f"**{i}. {agent_title}**: {round.agent_response[:200]}...\n\n"
        
        conclusion += "**关键要点**: 多位专家的观点提供了涵盖理论、实践和实施方面的全面分析。\n\n"
        conclusion += "**建议**: 基于专家讨论提供的多方面见解，建议进行进一步的详细分析。"
        
        return conclusion