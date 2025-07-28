import streamlit as st
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import sys
import os
import traceback

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import ResearchOrchestrator
from config import Config

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chat_interface.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatInterface:
    """Streamlit-based chat interface for the research agent system"""
    
    def __init__(self):
        self.orchestrator = None
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None
        if 'orchestrator_initialized' not in st.session_state:
            st.session_state.orchestrator_initialized = False
        if 'research_sessions' not in st.session_state:
            st.session_state.research_sessions = {}
        
        # API Keys - Load from .env as defaults
        if 'openai_api_key' not in st.session_state:
            st.session_state.openai_api_key = Config.OPENAI_API_KEY
        if 'deepseek_api_key' not in st.session_state:
            st.session_state.deepseek_api_key = Config.DEEPSEEK_API_KEY
        if 'anthropic_api_key' not in st.session_state:
            st.session_state.anthropic_api_key = Config.ANTHROPIC_API_KEY
        
        # Provider and Model Configuration - Load from .env as defaults
        if 'default_provider' not in st.session_state:
            st.session_state.default_provider = Config.DEFAULT_PROVIDER
        if 'openai_model' not in st.session_state:
            st.session_state.openai_model = Config.OPENAI_MODEL
        if 'deepseek_model' not in st.session_state:
            st.session_state.deepseek_model = Config.DEEPSEEK_MODEL
        if 'anthropic_model' not in st.session_state:
            st.session_state.anthropic_model = Config.ANTHROPIC_MODEL
        
        # Agent Configuration - Load from .env as defaults
        if 'selected_agents' not in st.session_state:
            st.session_state.selected_agents = Config.get_default_selected_agents()
        if 'agent_configs' not in st.session_state:
            # Convert config agent names to UI agent names
            env_agent_configs = Config.get_all_agent_configs()
            ui_agent_configs = {}
            agent_name_mapping = {
                "google_engineer": "Google Engineer",
                "mit_researcher": "MIT Researcher",
                "industry_expert": "Industry Expert",
                "paper_analyst": "Paper Analyst"
            }
            for env_name, config in env_agent_configs.items():
                ui_name = agent_name_mapping.get(env_name, env_name)
                ui_agent_configs[ui_name] = config
            st.session_state.agent_configs = ui_agent_configs
        
        # Research Parameters - Load from .env as defaults
        if 'max_papers' not in st.session_state:
            st.session_state.max_papers = Config.DEFAULT_MAX_PAPERS
        if 'include_recent' not in st.session_state:
            st.session_state.include_recent = Config.DEFAULT_INCLUDE_RECENT
    
    def _initialize_orchestrator(self) -> bool:
        """Initialize the research orchestrator"""
        try:
            logger.info("Starting orchestrator initialization")
            
            if st.session_state.orchestrator_initialized and hasattr(st.session_state, 'orchestrator'):
                logger.info("Orchestrator already initialized")
                self.orchestrator = st.session_state.orchestrator
                return True
            
            # Get API keys from session state
            openai_key = st.session_state.get('openai_api_key', '')
            deepseek_key = st.session_state.get('deepseek_api_key', '')
            anthropic_key = st.session_state.get('anthropic_api_key', '')
            
            # Check if at least one API key is provided
            if not any([openai_key, deepseek_key, anthropic_key]):
                logger.warning("No API keys provided")
                st.sidebar.warning("Please enter at least one API key (OpenAI, DeepSeek, or Anthropic) to continue")
                return False
            
            # Get configuration from session state
            default_provider = st.session_state.get('default_provider', 'openai')
            agent_configs = st.session_state.get('agent_configs', {})
            
            # Convert agent configs to orchestrator format
            orchestrator_agent_configs = {}
            for agent_name, config in agent_configs.items():
                # Map agent names to orchestrator format
                agent_mapping = {
                    "Google Engineer": "google_engineer",
                    "MIT Researcher": "mit_researcher", 
                    "Industry Expert": "industry_expert",
                    "Paper Analyst": "paper_analyst"
                }
                
                if agent_name in agent_mapping:
                    orchestrator_agent_configs[agent_mapping[agent_name]] = {
                        "provider": config.get('provider', default_provider),
                        "model": config.get('model', 'gpt-4o-mini'),
                        "api_key": self._get_api_key_for_provider(config.get('provider', default_provider))
                    }
            
            logger.info(f"Initializing research orchestrator with provider: {default_provider}")
            logger.info(f"Agent configs: {orchestrator_agent_configs}")
            
            # Initialize orchestrator
            self.orchestrator = ResearchOrchestrator(
                openai_api_key=openai_key,
                deepseek_api_key=deepseek_key,
                anthropic_api_key=anthropic_key,
                default_provider=default_provider,
                agent_configs=orchestrator_agent_configs,
                db_path="./data/vector_db"
            )
            
            # Store in session state for persistence
            st.session_state.orchestrator = self.orchestrator
            st.session_state.orchestrator_initialized = True
            logger.info("Research orchestrator initialized successfully")
            st.sidebar.success("✅ Research agents initialized!")
            return True
            
        except Exception as e:
            error_msg = f"Error initializing orchestrator: {e}"
            logger.error(error_msg, exc_info=True)
            st.sidebar.error(error_msg)
            return False
    
    def _get_api_key_for_provider(self, provider: str) -> str:
        """Get the appropriate API key for a provider"""
        if provider == "openai":
            return st.session_state.get('openai_api_key', '')
        elif provider == "deepseek":
            return st.session_state.get('deepseek_api_key', '')
        elif provider == "anthropic":
            return st.session_state.get('anthropic_api_key', '')
        else:
            return st.session_state.get('openai_api_key', '')  # Default to OpenAI
    
    def run(self):
        """Main application entry point"""
        st.set_page_config(
            page_title="Research Agent RAG System",
            page_icon="🔬",
            layout="wide"
        )
        
        st.title("🔬 Research Agent RAG System")
        st.markdown("Chat with AI research agents to explore academic papers and generate insights")
        
        # Sidebar configuration
        self._render_sidebar()
        
        # Initialize orchestrator
        if not self._initialize_orchestrator():
            st.stop()
        
        # Main interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_chat_interface()
        
        with col2:
            self._render_research_panel()
    
    def _render_sidebar(self):
        """Render the sidebar with configuration options"""
        st.sidebar.header("Configuration")
        
        # API Keys Configuration
        st.sidebar.subheader("🔑 API Keys")
        
        # OpenAI API Key
        openai_key = st.sidebar.text_input(
            "OpenAI API Key",
            value=st.session_state.get('openai_api_key', ''),
            type='password',
            help="Enter your OpenAI API key"
        )
        if openai_key != st.session_state.get('openai_api_key', ''):
            st.session_state.openai_api_key = openai_key
            st.session_state.orchestrator = None  # Reset orchestrator
        
        # DeepSeek API Key
        deepseek_key = st.sidebar.text_input(
            "DeepSeek API Key",
            value=st.session_state.get('deepseek_api_key', ''),
            type='password',
            help="Enter your DeepSeek API key"
        )
        if deepseek_key != st.session_state.get('deepseek_api_key', ''):
            st.session_state.deepseek_api_key = deepseek_key
            st.session_state.orchestrator = None  # Reset orchestrator
        
        # Anthropic API Key
        anthropic_key = st.sidebar.text_input(
            "Anthropic API Key",
            value=st.session_state.get('anthropic_api_key', ''),
            type='password',
            help="Enter your Anthropic API key"
        )
        if anthropic_key != st.session_state.get('anthropic_api_key', ''):
            st.session_state.anthropic_api_key = anthropic_key
            st.session_state.orchestrator = None  # Reset orchestrator
        
        # Provider and Model Configuration
        st.sidebar.subheader("🤖 AI Provider & Models")
        
        # Default provider selection
        providers = ["openai", "deepseek", "anthropic"]
        default_provider = st.sidebar.selectbox(
            "Default Provider",
            providers,
            index=providers.index(st.session_state.get('default_provider', 'openai')),
            help="Select the default AI provider for all agents"
        )
        if default_provider != st.session_state.get('default_provider', 'openai'):
            st.session_state.default_provider = default_provider
            st.session_state.orchestrator = None  # Reset orchestrator
        
        # Model selection for each provider
        st.sidebar.subheader("📋 Model Configuration")
        
        # OpenAI Models
        if openai_key:
            openai_models = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
            openai_model = st.sidebar.selectbox(
                "OpenAI Model",
                openai_models,
                index=openai_models.index(st.session_state.get('openai_model', 'gpt-4o-mini')),
                help="Select OpenAI model"
            )
            if openai_model != st.session_state.get('openai_model', 'gpt-4o-mini'):
                st.session_state.openai_model = openai_model
                st.session_state.orchestrator = None
        
        # DeepSeek Models
        if deepseek_key:
            deepseek_models = ["deepseek-chat", "deepseek-reasoner", "deepseek-v3", "deepseek-r1"]
            deepseek_model = st.sidebar.selectbox(
                "DeepSeek Model",
                deepseek_models,
                index=deepseek_models.index(st.session_state.get('deepseek_model', 'deepseek-chat')),
                help="Select DeepSeek model"
            )
            if deepseek_model != st.session_state.get('deepseek_model', 'deepseek-chat'):
                st.session_state.deepseek_model = deepseek_model
                st.session_state.orchestrator = None
        
        # Anthropic Models
        if anthropic_key:
            anthropic_models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022", 
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229"
            ]
            anthropic_model = st.sidebar.selectbox(
                "Anthropic Model",
                anthropic_models,
                index=anthropic_models.index(st.session_state.get('anthropic_model', 'claude-3-5-sonnet-20241022')),
                help="Select Anthropic model"
            )
            if anthropic_model != st.session_state.get('anthropic_model', 'claude-3-5-sonnet-20241022'):
                st.session_state.anthropic_model = anthropic_model
                st.session_state.orchestrator = None
        
        # Agent Configuration
        st.sidebar.subheader("👥 Agent Configuration")
        
        # Agent selection
        agents = ["Google Engineer", "MIT Researcher", "Industry Expert", "Paper Analyst"]
        selected_agents = st.sidebar.multiselect(
            "Select agents to consult:",
            agents,
            default=st.session_state.get('selected_agents', agents)
        )
        st.session_state.selected_agents = selected_agents
        
        # Individual agent provider configuration
        st.sidebar.subheader("🔧 Per-Agent Provider Settings")
        
        agent_configs = st.session_state.get('agent_configs', {})
        
        for agent_name in ["Google Engineer", "MIT Researcher", "Industry Expert", "Paper Analyst"]:
            if agent_name in selected_agents:
                st.sidebar.write(f"**{agent_name}:**")
                
                # Agent provider
                agent_provider = st.sidebar.selectbox(
                    f"{agent_name} Provider",
                    providers,
                    index=providers.index(agent_configs.get(agent_name, {}).get('provider', default_provider)),
                    key=f"{agent_name}_provider"
                )
                
                # Agent model based on provider
                if agent_provider == "openai" and openai_key:
                    current_model = agent_configs.get(agent_name, {}).get('model', openai_model)
                    # Safe index lookup - fallback to 0 if model not found
                    try:
                        model_index = openai_models.index(current_model)
                    except ValueError:
                        logger.warning(f"Model '{current_model}' not found in OpenAI models, using default")
                        model_index = 0
                    
                    agent_model = st.sidebar.selectbox(
                        f"{agent_name} Model",
                        openai_models,
                        index=model_index,
                        key=f"{agent_name}_model"
                    )
                elif agent_provider == "deepseek" and deepseek_key:
                    current_model = agent_configs.get(agent_name, {}).get('model', deepseek_model)
                    # Safe index lookup - fallback to 0 if model not found
                    try:
                        model_index = deepseek_models.index(current_model)
                    except ValueError:
                        logger.warning(f"Model '{current_model}' not found in DeepSeek models, using default")
                        model_index = 0
                    
                    agent_model = st.sidebar.selectbox(
                        f"{agent_name} Model",
                        deepseek_models,
                        index=model_index,
                        key=f"{agent_name}_model"
                    )
                elif agent_provider == "anthropic" and anthropic_key:
                    current_model = agent_configs.get(agent_name, {}).get('model', anthropic_model)
                    # Safe index lookup - fallback to 0 if model not found
                    try:
                        model_index = anthropic_models.index(current_model)
                    except ValueError:
                        logger.warning(f"Model '{current_model}' not found in Anthropic models, using default")
                        model_index = 0
                    
                    agent_model = st.sidebar.selectbox(
                        f"{agent_name} Model",
                        anthropic_models,
                        index=model_index,
                        key=f"{agent_name}_model"
                    )
                else:
                    agent_model = "default"
                
                # Update agent config
                agent_configs[agent_name] = {
                    'provider': agent_provider,
                    'model': agent_model
                }
        
        st.session_state.agent_configs = agent_configs
        
        # Research parameters
        st.sidebar.subheader("📚 Research Parameters")
        max_papers = st.sidebar.slider("Max papers per topic", 5, 50, st.session_state.get('max_papers', 20))
        include_recent = st.sidebar.checkbox("Prioritize recent papers", st.session_state.get('include_recent', True))
        
        st.session_state.max_papers = max_papers
        st.session_state.include_recent = include_recent
        
        # Session management
        st.sidebar.subheader("Research Sessions")
        if st.session_state.research_sessions:
            session_names = list(st.session_state.research_sessions.keys())
            selected_session = st.sidebar.selectbox(
                "Load previous session:",
                ["None"] + session_names
            )
            if selected_session != "None":
                st.session_state.current_session_id = selected_session
        
        # Clear chat button
        if st.sidebar.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        # Debug section
        st.sidebar.subheader("🐛 Debug Info")
        if st.sidebar.checkbox("Show Logs"):
            try:
                with open('logs/chat_interface.log', 'r') as f:
                    logs = f.readlines()
                    recent_logs = logs[-20:] if len(logs) > 20 else logs
                    log_text = ''.join(recent_logs)
                    st.sidebar.code(log_text, language='text')
            except FileNotFoundError:
                st.sidebar.text("No log file found yet")
        
        if st.sidebar.button("Clear Logs"):
            try:
                with open('logs/chat_interface.log', 'w') as f:
                    f.write("")
                st.sidebar.success("Logs cleared")
            except Exception as e:
                st.sidebar.error(f"Error clearing logs: {e}")
    
    def _render_chat_interface(self):
        """Render the main chat interface"""
        st.subheader("💬 Chat with Research Agents")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show enhanced metadata if available
                if "metadata" in message and message["metadata"]:
                    metadata = message["metadata"]
                    with st.expander("Search Details"):
                        # Show search strategy
                        if "search_strategy" in metadata:
                            st.write(f"**Search Strategy:** {metadata['search_strategy']}")
                        
                        # Show expanded queries
                        if "expanded_queries" in metadata and len(metadata["expanded_queries"]) > 1:
                            st.write(f"**Query Expansion:** {', '.join(metadata['expanded_queries'])}")
                        
                        # Show result counts
                        if "vector_results_count" in metadata and "arxiv_results_count" in metadata:
                            st.write(f"**Results:** {metadata['vector_results_count']} from knowledge base, {metadata['arxiv_results_count']} from ArXiv")
                        
                        # Show papers found
                        if "papers_found" in metadata:
                            st.write(f"**Papers Found:** {metadata['papers_found']}")
                        
                        # Show full metadata
                        st.json(metadata)
        
        # Chat input
        if prompt := st.chat_input("Ask about research papers or start a new research topic..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Determine if this is a research request or chat query
                    if self._is_research_request(prompt):
                        logger.info("Processing as research request")
                        status_text.text("🔍 Processing research request...")
                        progress_bar.progress(10)
                        response = self._handle_research_request(prompt, response_placeholder)
                    else:
                        logger.info("Processing as chat query")
                        status_text.text("💭 Processing chat query...")
                        progress_bar.progress(10)
                        
                        # Add thread handling using ThreadPoolExecutor (works in all threads)
                        from concurrent.futures import ThreadPoolExecutor
                        
                        # Get orchestrator and session ID before entering thread
                        orchestrator = getattr(st.session_state, 'orchestrator', None) or self.orchestrator
                        session_id = getattr(st.session_state, 'current_session_id', None)
                        
                        if not orchestrator:
                            logger.error("Orchestrator not available for threading")
                            response = {
                                "content": "Please initialize the system first by providing API keys.",
                                "metadata": {"error": True}
                            }
                        else:
                            def run_chat_query():
                                # Run chat query without UI updates (these cause NoSessionContext in threads)
                                return self._handle_chat_query_with_orchestrator(prompt, orchestrator, session_id)
                            
                            try:
                                progress_bar.progress(20)
                                status_text.text("🔍 Expanding query and searching knowledge base...")
                                
                                # Run query in separate thread without timeout
                                with ThreadPoolExecutor(max_workers=1) as executor:
                                    future = executor.submit(run_chat_query)
                                    try:
                                        response = future.result()  # No timeout - wait indefinitely
                                    except Exception as e:
                                        logger.error(f"Error in chat query execution: {e}")
                                        response = {
                                            "content": f"Error processing query: {e}",
                                            "metadata": {"error": True}
                                        }
                            except Exception as e:
                                logger.error(f"Error in thread execution: {e}", exc_info=True)
                                # Fallback to direct call
                                response = self._handle_chat_query_with_orchestrator(prompt, orchestrator, session_id)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Debug: Log the response content
                    logger.info(f"Response content length: {len(response.get('content', ''))}")
                    logger.info(f"Response keys: {list(response.keys())}")
                    
                    # Add assistant response to messages with enhanced metadata
                    metadata = response.get("metadata", {})
                    
                    # Add enhanced search information to metadata
                    if "search_strategy" in response:
                        metadata["search_strategy"] = response["search_strategy"]
                    if "expanded_queries" in response:
                        metadata["expanded_queries"] = response["expanded_queries"]
                    if "vector_results_count" in response:
                        metadata["vector_results_count"] = response["vector_results_count"]
                    if "arxiv_results_count" in response:
                        metadata["arxiv_results_count"] = response["arxiv_results_count"]
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response["content"],
                        "metadata": metadata
                    })
                    
                    # Display the response immediately
                    response_placeholder.markdown(response["content"])
                    
                    # Show enhanced metadata in expandable section
                    if metadata:
                        with st.expander("Search Details"):
                            if "search_strategy" in metadata:
                                st.write(f"**Search Strategy:** {metadata['search_strategy']}")
                            if "expanded_queries" in metadata and len(metadata["expanded_queries"]) > 1:
                                st.write(f"**Query Expansion:** {', '.join(metadata['expanded_queries'])}")
                            if "vector_results_count" in metadata and "arxiv_results_count" in metadata:
                                st.write(f"**Results:** {metadata['vector_results_count']} from knowledge base, {metadata['arxiv_results_count']} from ArXiv")
                    
                    # Force a rerun to update the chat display
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Error processing request: {e}"
                    logger.error(error_msg, exc_info=True)
                    progress_bar.empty()
                    status_text.empty()
                    response_placeholder.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg,
                        "metadata": {"error": True}
                    })
    
    def _render_research_panel(self):
        """Render the research management panel"""
        st.subheader("🔍 Research Management")
        
        # New research session
        with st.expander("Start New Research", expanded=False):
            topic = st.text_input("Research Topic:")
            if st.button("Start Research", disabled=not topic):
                self._start_research_session(topic)
        
        # Current session info
        if st.session_state.current_session_id:
            session = st.session_state.research_sessions.get(st.session_state.current_session_id)
            if session:
                st.subheader("Current Session")
                st.write(f"**Topic:** {session.get('topic', 'Unknown')}")
                st.write(f"**Status:** {session.get('status', 'Unknown')}")
                st.write(f"**Papers:** {session.get('paper_count', 0)}")
                
                # Show agent analyses
                if session.get('agent_analyses'):
                    st.subheader("Agent Analyses")
                    for agent_name, analyses in session['agent_analyses'].items():
                        with st.expander(f"{agent_name} ({len(analyses)} analyses)"):
                            for i, analysis in enumerate(analyses):
                                st.write(f"**Analysis {i+1}:**")
                                st.write(analysis.get('analysis', 'No analysis available')[:300] + "...")
        
        # Vector database stats
        if self.orchestrator and self.orchestrator.vector_store:
            try:
                logger.debug("Getting database stats...")
                stats = self.orchestrator.vector_store.get_collection_stats()
                st.subheader("📊 Database Stats")
                st.metric("Total Papers", stats.get('unique_papers', 0))
                st.metric("Total Chunks", stats.get('total_chunks', 0))
                
                # Test database connectivity
                if st.button("🔍 Test Database"):
                    with st.spinner("Testing database connection..."):
                        try:
                            test_results = self.orchestrator.vector_store.search_papers("test", n_results=1)
                            st.success(f"✅ Database OK - {len(test_results)} test results")
                        except Exception as test_e:
                            st.error(f"❌ Database Error: {test_e}")
                            logger.error(f"Database test failed: {test_e}", exc_info=True)
                            
            except Exception as e:
                error_msg = f"Error getting database stats: {e}"
                st.error(error_msg)
                logger.error(error_msg, exc_info=True)
    
    def _is_research_request(self, prompt: str) -> bool:
        """Determine if the prompt is requesting new research"""
        research_keywords = [
            "research", "analyze", "investigate", "study", "explore",
            "papers on", "latest work on", "find papers about"
        ]
        return any(keyword in prompt.lower() for keyword in research_keywords)
    
    def _handle_research_request(self, prompt: str, placeholder) -> Dict[str, Any]:
        """Handle a research request"""
        placeholder.info("🔍 Starting research session...")
        
        try:
            # Extract topic from prompt (simplified)
            topic = self._extract_topic(prompt)
            
            # Start research session
            session_id = f"chat_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Run research (this would be async in a real app)
            placeholder.info("📚 Retrieving papers...")
            
            # For demo purposes, we'll simulate the research process
            # In a real implementation, you'd call:
            # session = await self.orchestrator.research_topic(topic, max_papers=st.session_state.max_papers)
            
            # Simulate research results
            session_data = {
                "session_id": session_id,
                "topic": topic,
                "status": "completed",
                "paper_count": 15,
                "agent_analyses": {
                    "google_engineer": [{"analysis": f"Engineering analysis of {topic}..."}],
                    "mit_researcher": [{"analysis": f"Academic analysis of {topic}..."}],
                    "industry_expert": [{"analysis": f"Industry analysis of {topic}..."}],
                    "paper_analyst": [{"analysis": f"Critical analysis of {topic}..."}]
                }
            }
            
            st.session_state.research_sessions[session_id] = session_data
            st.session_state.current_session_id = session_id
            
            placeholder.success("✅ Research completed!")
            
            # Generate summary response
            response_content = f"""
## Research Summary: {topic}

I've analyzed papers on "{topic}" using our specialized research agents:

**🔧 Google Engineer Perspective:**
- Focus on scalability and production implementation
- Infrastructure requirements and performance considerations

**🎓 MIT Researcher Perspective:**
- Theoretical foundations and mathematical rigor
- Novel algorithmic contributions and research gaps

**💼 Industry Expert Perspective:**
- Commercial viability and market potential
- Business model implications and adoption barriers

**📊 Paper Analyst Perspective:**
- Critical evaluation of methodologies
- Breaking points and limitation analysis

**Key Findings:**
- Found {session_data['paper_count']} relevant papers
- Identified key implementation challenges
- Highlighted commercial opportunities
- Noted theoretical contributions

You can now ask specific questions about the papers or request deeper analysis on particular aspects.
"""
            
            return {
                "content": response_content,
                "metadata": {
                    "session_id": session_id,
                    "topic": topic,
                    "research_type": "comprehensive"
                }
            }
            
        except Exception as e:
            placeholder.error(f"Research failed: {e}")
            return {
                "content": f"I encountered an error while researching '{prompt}': {e}",
                "metadata": {"error": True}
            }
    
    def _handle_chat_query(self, prompt: str, placeholder) -> Dict[str, Any]:
        """Handle a chat query about existing papers"""
        logger.info(f"Starting chat query: {prompt[:100]}...")
        placeholder.info("💭 Searching knowledge base...")
        
        try:
            if not self.orchestrator:
                logger.error("Orchestrator not initialized")
                return {
                    "content": "Please initialize the system first by providing API keys.",
                    "metadata": {"error": True}
                }
            
            logger.info("Orchestrator available, searching for relevant papers...")
            # Search for relevant papers
            logger.debug(f"Query: {prompt}")
            logger.debug(f"Session ID: {st.session_state.current_session_id}")
            
            placeholder.info("🔍 Querying vector database...")
            chat_response = self.orchestrator.chat_with_papers(
                query=prompt,
                session_id=st.session_state.current_session_id,
                n_papers=5
            )
            
            logger.info(f"Chat response received: {len(chat_response.get('relevant_papers', []))} papers found")
            placeholder.success("✅ Found relevant information!")
            
            # Format response
            if chat_response.get("relevant_papers"):
                logger.debug("Formatting response with papers")
                response_content = chat_response["response"]
                
                # Add paper details
                papers = chat_response["relevant_papers"]
                if papers:
                    response_content += "\n\n**Relevant Papers:**\n"
                    for i, paper in enumerate(papers[:3], 1):
                        response_content += f"{i}. **{paper['title']}**\n"
                        response_content += f"   Authors: {paper['authors']}\n"
                        response_content += f"   Relevance: {paper['similarity_score']:.2%}\n\n"
                        logger.debug(f"Paper {i}: {paper['title'][:50]}...")
            else:
                logger.warning("No relevant papers found for query")
                response_content = "I couldn't find specific papers related to your question. Try starting a new research session or asking a different question."
            
            logger.info("Chat query completed successfully")
            return {
                "content": response_content,
                "metadata": {
                    "query_type": "chat",
                    "papers_found": len(chat_response.get("relevant_papers", []))
                }
            }
            
        except Exception as e:
            error_msg = f"Chat query failed: {e}"
            logger.error(error_msg, exc_info=True)
            placeholder.error(error_msg)
            return {
                "content": f"I encountered an error while processing your question: {e}",
                "metadata": {"error": True}
            }
    
    def _handle_chat_query_no_ui(self, prompt: str) -> Dict[str, Any]:
        """Handle a chat query about existing papers without UI updates (for threading)"""
        logger.info(f"Starting chat query: {prompt[:100]}...")
        
        try:
            # Get orchestrator from session state (accessible in threads)
            orchestrator = getattr(st.session_state, 'orchestrator', None)
            if not orchestrator:
                logger.error("Orchestrator not initialized")
                return {
                    "content": "Please initialize the system first by providing API keys.",
                    "metadata": {"error": True}
                }
            
            logger.info("Orchestrator available, searching for relevant papers...")
            # Search for relevant papers
            logger.debug(f"Query: {prompt}")
            logger.debug(f"Session ID: {getattr(st.session_state, 'current_session_id', None)}")
            
            chat_response = orchestrator.chat_with_papers(
                query=prompt,
                session_id=getattr(st.session_state, 'current_session_id', None),
                n_papers=5
            )
            
            logger.info(f"Chat response received: {len(chat_response.get('relevant_papers', []))} papers found")
            
            # Format response
            if chat_response.get("relevant_papers"):
                logger.debug("Formatting response with papers")
                response_content = chat_response["response"]
                
                # Add paper details
                papers = chat_response["relevant_papers"]
                if papers:
                    response_content += "\n\n**Relevant Papers:**\n"
                    for i, paper in enumerate(papers[:3], 1):
                        response_content += f"{i}. **{paper['title']}**\n"
                        response_content += f"   Authors: {paper['authors']}\n"
                        response_content += f"   Relevance: {paper['similarity_score']:.2%}\n\n"
                        logger.debug(f"Paper {i}: {paper['title'][:50]}...")
            else:
                logger.warning("No relevant papers found for query")
                response_content = "I couldn't find specific papers related to your question. Try starting a new research session or asking a different question."
            
            logger.info("Chat query completed successfully")
            return {
                "content": response_content,
                "metadata": {
                    "query_type": "chat",
                    "papers_found": len(chat_response.get("relevant_papers", []))
                }
            }
            
        except Exception as e:
            error_msg = f"Chat query failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "content": f"I encountered an error while processing your question: {e}",
                "metadata": {"error": True}
            }
    
    def _handle_chat_query_with_orchestrator(self, prompt: str, orchestrator, session_id: str = None) -> Dict[str, Any]:
        """Handle a chat query with explicit orchestrator parameter (thread-safe)"""
        logger.info(f"Starting chat query: {prompt[:100]}...")
        
        try:
            if not orchestrator:
                logger.error("Orchestrator parameter not provided")
                return {
                    "content": "Please initialize the system first by providing API keys.",
                    "metadata": {"error": True}
                }
            
            logger.info("Orchestrator available, searching for relevant papers...")
            # Search for relevant papers
            logger.debug(f"Query: {prompt}")
            logger.debug(f"Session ID: {session_id}")
            
            chat_response = orchestrator.chat_with_papers(
                query=prompt,
                session_id=session_id,
                n_papers=5,
                min_similarity_threshold=0.5,
                enable_arxiv_fallback=True
            )
            
            logger.info(f"Enhanced chat response received: {len(chat_response.get('relevant_papers', []))} papers found")
            
            # Return the enhanced response directly (it already includes formatted content)
            logger.info("Enhanced chat query completed successfully")
            return {
                "content": chat_response.get("response", "No response generated"),
                "metadata": {
                    "query_type": "enhanced_chat",
                    "papers_found": len(chat_response.get("relevant_papers", [])),
                    "search_strategy": chat_response.get("search_strategy", "unknown"),
                    "expanded_queries": chat_response.get("expanded_queries", []),
                    "vector_results_count": chat_response.get("vector_results_count", 0),
                    "arxiv_results_count": chat_response.get("arxiv_results_count", 0)
                }
            }
            
        except Exception as e:
            error_msg = f"Chat query failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "content": f"I encountered an error while processing your question: {e}",
                "metadata": {"error": True}
            }
    
    def _extract_topic(self, prompt: str) -> str:
        """Extract research topic from prompt (simplified)"""
        # Remove common research request phrases
        topic = prompt.lower()
        for phrase in ["research", "analyze", "investigate", "study", "explore", "papers on", "latest work on", "find papers about"]:
            topic = topic.replace(phrase, "")
        
        # Clean up
        topic = topic.strip().strip(".,!?")
        return topic if topic else prompt
    
    def _start_research_session(self, topic: str):
        """Start a new research session"""
        try:
            session_id = f"manual_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # For demo purposes, create a placeholder session
            session_data = {
                "session_id": session_id,
                "topic": topic,
                "status": "in_progress",
                "paper_count": 0,
                "agent_analyses": {}
            }
            
            st.session_state.research_sessions[session_id] = session_data
            st.session_state.current_session_id = session_id
            
            st.success(f"Started research session on: {topic}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error starting research session: {e}")

# Main entry point for Streamlit
def main():
    chat_interface = ChatInterface()
    chat_interface.run()

if __name__ == "__main__":
    main()