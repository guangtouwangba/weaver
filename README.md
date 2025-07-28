# 🔬 Research Agent RAG System

A multi-agent research system that combines RAG (Retrieval-Augmented Generation) with specialized AI agents to analyze academic papers and generate insights from multiple expert perspectives.

## 🌟 Features

### Multi-Agent Analysis
- **Google Engineer Agent**: Focuses on scalability, production systems, and engineering challenges
- **MIT Researcher Agent**: Provides theoretical analysis, mathematical rigor, and academic insights  
- **Industry Expert Agent**: Evaluates commercial viability, market potential, and business applications
- **Paper Analyst Agent**: Conducts critical analysis and identifies breaking points

### Core Capabilities
- **Paper Retrieval**: Automatically fetch papers from arXiv based on research topics
- **Vector Storage**: Store and semantically search papers using ChromaDB
- **Multi-Agent Coordination**: Orchestrate multiple agents for comprehensive analysis
- **Interactive Chat**: Discuss papers and get insights through a conversational interface
- **Research Sessions**: Manage complex research workflows and track progress

### User Interfaces
- **Web Interface**: Streamlit-based chat interface for easy interaction
- **CLI Mode**: Command-line interface for programmatic usage
- **Python API**: Direct integration in your own applications
- **Demo Mode**: Comprehensive demonstration of all features

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+ (excluding 3.9.7)
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management

### 2. Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd research-agent-rag

# Complete setup (installs dependencies, creates .env, sets up git hooks)
make setup

# Or step by step:
make install-dev    # Install dependencies
make setup-env      # Create .env file
```

### 3. Configuration

```bash
# Edit .env and add your API keys
# Required: OPENAI_API_KEY
# Optional: ANTHROPIC_API_KEY
```

### 4. Quick Start

```bash
# Run complete demonstration
make run-demo

# Launch web interface
make run-web

# Or start CLI mode
make run-cli
```

### 🐳 Docker Quick Start

```bash
# Build and run with Docker
make docker-build
make docker-run
```

## 🎯 Usage Examples

### Web Interface
1. Open the Streamlit interface
2. Enter your API key in the sidebar
3. Start a research session on any topic
4. Chat with the papers and get multi-agent insights

### Command Line
```bash
# Start CLI mode
make run-cli

# Available commands:
> research transformer attention mechanisms
> chat What are the main challenges with attention?
> status
> quit
```

### Python API
```python
import asyncio
from agents.orchestrator import ResearchOrchestrator

# Initialize the orchestrator
orchestrator = ResearchOrchestrator(
    openai_api_key="your-api-key"
)

# Start a research session
async def research_example():
    session = await orchestrator.research_topic(
        topic="large language models",
        max_papers=20
    )
    
    # Get comprehensive insights
    for agent_name, analyses in session.agent_analyses.items():
        print(f"{agent_name}: {len(analyses)} analyses")

# Chat with papers
response = orchestrator.chat_with_papers(
    "What are the scaling laws for transformer models?"
)
print(response['response'])
```

## 🏗️ Architecture

```
research-agent-rag/
├── agents/                 # AI research agents
│   ├── base_agent.py      # Base agent class
│   ├── google_engineer_agent.py
│   ├── mit_researcher_agent.py
│   ├── industry_expert_agent.py
│   ├── paper_analyst_agent.py
│   └── orchestrator.py    # Multi-agent coordinator
├── retrieval/             # Paper retrieval system
│   └── arxiv_client.py    # arXiv API integration
├── database/              # Vector database
│   └── vector_store.py    # ChromaDB integration
├── chat/                  # Chat interfaces
│   └── chat_interface.py  # Streamlit web interface
├── examples/              # Examples and demos
│   └── demo.py           # Comprehensive demo
├── config.py             # Configuration management
├── main.py              # Main entry point
└── requirements.txt     # Dependencies
```

## 🤖 Agent Specializations

### Google Engineer Agent
- **Focus**: Large-scale systems, performance, production deployment
- **Expertise**: Distributed systems, ML infrastructure, scalability engineering
- **Output**: Infrastructure requirements, performance bottlenecks, implementation complexity

### MIT Researcher Agent  
- **Focus**: Theoretical foundations, mathematical rigor, novel research
- **Expertise**: Algorithms, theoretical CS, academic methodology
- **Output**: Theoretical contributions, research gaps, experimental validation

### Industry Expert Agent
- **Focus**: Commercial applications, market viability, business models
- **Expertise**: Technology commercialization, competitive analysis, market adoption
- **Output**: Market potential, business opportunities, adoption barriers

### Paper Analyst Agent
- **Focus**: Critical evaluation, breaking point identification, methodology assessment
- **Expertise**: Research quality assessment, reproducibility, cross-paper synthesis
- **Output**: Methodological strengths/weaknesses, breaking points, improvement suggestions

## 📊 Features in Detail

### Paper Retrieval & Storage
- Automated arXiv search with configurable parameters
- Semantic chunking and embedding generation
- Vector similarity search for relevant paper discovery
- Metadata extraction and categorization

### Multi-Agent Analysis
- Parallel processing for faster analysis
- Specialized prompts for each agent perspective
- Confidence scoring and consensus analysis
- Cross-agent insight synthesis

### Research Session Management
- Session tracking and progress monitoring
- Historical analysis storage and retrieval
- Research workflow orchestration
- Real-time status updates

### Interactive Chat
- Natural language queries about papers
- Context-aware responses using vector search
- Multi-agent consultation for complex questions
- Paper recommendation and discovery

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  # Optional

# Database Settings
VECTOR_DB_PATH=./data/vector_db
MAX_PAPERS_PER_QUERY=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Agent Settings
DEFAULT_MODEL=gpt-4o-mini
RESEARCH_TOPICS_CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
```

### Customization
- **Agent Prompts**: Modify agent behavior by editing prompts in agent classes
- **Vector Database**: Switch to Pinecone, Weaviate, or other vector DBs
- **Paper Sources**: Extend beyond arXiv to other academic databases
- **Analysis Pipeline**: Add custom processing steps or filters

## 🧪 Testing & Development

### Available Make Commands

```bash
# See all available commands
make help

# Development workflow
make dev           # Setup development environment
make format        # Format code with black and isort
make lint          # Run linting tools
make test          # Run tests
make test-cov      # Run tests with coverage
make qa            # Run all quality assurance checks

# Running the application
make run-web       # Launch web interface
make run-cli       # Start CLI mode  
make run-demo      # Run demonstration
make run-debug     # Run with debug logging

# Database management
make db-reset      # Reset vector database
make db-backup     # Backup vector database

# Docker support
make docker-build  # Build Docker image
make docker-run    # Run Docker container
make docker-dev    # Development container

# Maintenance
make clean         # Clean build artifacts
make update-deps   # Update dependencies
make security-check # Run security checks
```

### Development Workflow
```bash
# Quick development setup
make dev

# Before committing
make pre-commit

# Continuous development
make run-web      # In one terminal
make logs         # In another terminal to monitor
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow the existing code structure and naming conventions
- Add docstrings for new classes and methods
- Test new features with the demo script
- Update README for significant changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **arXiv**: For providing access to research papers
- **OpenAI**: For powerful language models
- **ChromaDB**: For vector database capabilities
- **Streamlit**: For the web interface framework
- **Research Community**: For inspiring this multi-agent approach

## 🔮 Future Roadmap

- [ ] **Additional Paper Sources**: Google Scholar, Semantic Scholar, PubMed
- [ ] **More Agent Types**: Domain-specific agents (Biology, Physics, etc.)
- [ ] **API Server**: RESTful API for external integrations
- [ ] **Advanced Analytics**: Research trend analysis, citation networks
- [ ] **Collaborative Features**: Multi-user research sessions
- [ ] **Export Capabilities**: PDF reports, research summaries
- [ ] **Integration**: Zotero, Mendeley, and other research tools

---

**Built with ❤️ for the research community**