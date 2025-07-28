# Configuration Guide

The Research Agent RAG System supports comprehensive configuration through environment variables and `.env` files. This allows you to customize API providers, models, search parameters, and agent behaviors.

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys:**
   ```bash
   # Edit .env file
   OPENAI_API_KEY=sk-your-openai-key-here
   DEEPSEEK_API_KEY=sk-your-deepseek-key-here  
   ANTHROPIC_API_KEY=sk-your-anthropic-key-here
   ```

3. **Validate your configuration:**
   ```bash
   python validate_config.py
   ```

4. **Start the system:**
   ```bash
   python main.py  # Web interface
   # or
   streamlit run chat/chat_interface.py
   ```

## Configuration Options

### 🔑 API Keys

At least one API key is required:

```env
# OpenAI (GPT models)
OPENAI_API_KEY=sk-your-openai-key-here

# DeepSeek (cost-effective models)
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# Anthropic (Claude models)
ANTHROPIC_API_KEY=sk-your-anthropic-key-here
```

### 🎯 Provider Configuration

Set the default provider for all agents:

```env
# Options: openai, deepseek, anthropic
DEFAULT_PROVIDER=openai
```

### 🤖 Model Configuration

Configure default models for each provider:

```env
# OpenAI models
OPENAI_MODEL=gpt-4o-mini
# Options: gpt-4o, gpt-4o-mini, gpt-4, gpt-3.5-turbo

# DeepSeek models  
DEEPSEEK_MODEL=deepseek-chat
# Options: deepseek-chat, deepseek-reasoner, deepseek-v3, deepseek-r1

# Anthropic models
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
# Options: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229
```

### 👥 Individual Agent Configuration

Configure each agent separately using either approach:

#### Approach 1: Individual Environment Variables (Simpler)

```env
# Google Engineer Agent
GOOGLE_ENGINEER_PROVIDER=openai
GOOGLE_ENGINEER_MODEL=gpt-4o-mini

# MIT Researcher Agent
MIT_RESEARCHER_PROVIDER=anthropic
MIT_RESEARCHER_MODEL=claude-3-5-sonnet-20241022

# Industry Expert Agent
INDUSTRY_EXPERT_PROVIDER=deepseek
INDUSTRY_EXPERT_MODEL=deepseek-chat

# Paper Analyst Agent
PAPER_ANALYST_PROVIDER=openai
PAPER_ANALYST_MODEL=gpt-4o
```

#### Approach 2: JSON Configuration (More Flexible)

```env
AGENT_CONFIGS={"google_engineer": {"provider": "openai", "model": "gpt-4o"}, "mit_researcher": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"}, "industry_expert": {"provider": "deepseek", "model": "deepseek-chat"}}
```

### 🔍 Search Configuration

Control search behavior:

```env
# Minimum similarity threshold for vector search results (0.0-1.0)
MIN_SIMILARITY_THRESHOLD=0.5

# Enable ArXiv fallback search when local results are insufficient
ENABLE_ARXIV_FALLBACK=true

# Maximum papers to fetch from ArXiv fallback
ARXIV_FALLBACK_MAX_PAPERS=10

# Enable AI-powered query expansion
ENABLE_QUERY_EXPANSION=true

# Maximum number of query expansions to generate
MAX_QUERY_EXPANSIONS=3
```

### 💬 Agent Discussion Configuration

Control multi-agent discussions:

```env
# Enable multi-agent discussions and insights
ENABLE_AGENT_DISCUSSIONS=true

# Default selected agents (comma-separated)
DEFAULT_SELECTED_AGENTS=Google Engineer,MIT Researcher,Industry Expert,Paper Analyst
```

### 📚 Research Parameters

Set default research parameters:

```env
# Default maximum papers per research session
DEFAULT_MAX_PAPERS=20

# Default setting for including recent papers
DEFAULT_INCLUDE_RECENT=true
```

### 🗄️ Vector Database Configuration

Configure the vector database:

```env
# Path to vector database storage
VECTOR_DB_PATH=./data/vector_db

# Maximum papers per query
MAX_PAPERS_PER_QUERY=50

# Text chunking parameters
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 📝 Logging Configuration

Configure logging:

```env
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Log file path
LOG_FILE=logs/research_agent.log
```

### 🌐 Server Configuration

Configure the Streamlit server:

```env
# Streamlit server settings
STREAMLIT_HOST=localhost
STREAMLIT_PORT=8501
```

## Configuration Examples

### Example 1: OpenAI Only (Minimal Setup)

```env
# API Key
OPENAI_API_KEY=sk-your-openai-key-here

# Provider Configuration
DEFAULT_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini

# All agents will use OpenAI by default
```

### Example 2: Multi-Provider Setup

```env
# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
ANTHROPIC_API_KEY=sk-your-anthropic-key-here

# Default Provider
DEFAULT_PROVIDER=openai

# Models
OPENAI_MODEL=gpt-4o-mini
DEEPSEEK_MODEL=deepseek-chat
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Agent Specialization
GOOGLE_ENGINEER_PROVIDER=openai
GOOGLE_ENGINEER_MODEL=gpt-4o          # Use more powerful model for engineering
MIT_RESEARCHER_PROVIDER=anthropic     # Use Claude for academic research
INDUSTRY_EXPERT_PROVIDER=deepseek     # Use cost-effective model for industry
PAPER_ANALYST_PROVIDER=openai
```

### Example 3: Research-Optimized Configuration

```env
# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-your-anthropic-key-here

# Provider Configuration
DEFAULT_PROVIDER=anthropic  # Use Claude as default for better reasoning

# Research Settings
DEFAULT_MAX_PAPERS=30               # More papers for comprehensive research
MIN_SIMILARITY_THRESHOLD=0.7        # Higher threshold for quality results
ENABLE_ARXIV_FALLBACK=true          # Always use ArXiv fallback
MAX_QUERY_EXPANSIONS=5              # More query variations

# Agent Selection
DEFAULT_SELECTED_AGENTS=MIT Researcher,Paper Analyst  # Focus on academic agents
```

### Example 4: Cost-Optimized Configuration

```env
# API Keys
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# Provider Configuration
DEFAULT_PROVIDER=deepseek  # Use cost-effective provider

# Model Configuration
DEEPSEEK_MODEL=deepseek-chat

# Research Settings
DEFAULT_MAX_PAPERS=15               # Fewer papers to reduce costs
ENABLE_QUERY_EXPANSION=false        # Disable to reduce API calls
ARXIV_FALLBACK_MAX_PAPERS=5         # Limit ArXiv papers
```

## Validation and Troubleshooting

### Validate Configuration

Run the validation script to check your configuration:

```bash
python validate_config.py
```

This will check:
- ✅ API key availability
- ✅ Provider/model compatibility
- ✅ Agent configurations
- ✅ File permissions
- ✅ Required dependencies

### Common Issues

1. **"No API keys found"**
   - Make sure your `.env` file exists
   - Check that API keys are properly formatted
   - Verify environment variables are loaded

2. **"Default provider has no API key"**
   - Set `DEFAULT_PROVIDER` to a provider you have an API key for
   - Or add the missing API key

3. **"Agent uses provider but no API key is set"**
   - Add the required API key for the provider
   - Or change the agent's provider to one you have an API key for

### Configuration Priority

Settings are loaded in this priority order:

1. **Individual agent environment variables** (highest priority)
   ```env
   GOOGLE_ENGINEER_PROVIDER=openai
   ```

2. **JSON AGENT_CONFIGS**
   ```env
   AGENT_CONFIGS={"google_engineer": {"provider": "openai"}}
   ```

3. **Default provider settings**
   ```env
   DEFAULT_PROVIDER=openai
   ```

4. **System defaults** (lowest priority)

### Demo and Testing

Test your configuration:

```bash
# Show current configuration
python demo_env_config.py

# Validate configuration
python validate_config.py

# Test with CLI mode
python main.py --mode cli

# Test with demo mode
python main.py --mode demo
```

## Advanced Configuration

### Custom Agent Roles

You can customize agent roles by overriding their system prompts in the agent configuration:

```python
# In your custom configuration
agent_configs = {
    "google_engineer": {
        "provider": "openai",
        "model": "gpt-4o",
        "custom_prompt": "You are a senior software engineer at Google..."
    }
}
```

### Environment-Specific Configurations

Use different `.env` files for different environments:

```bash
# Development
cp .env.example .env.dev

# Production
cp .env.example .env.prod

# Load specific environment
export ENV_FILE=.env.prod
python main.py
```

### Configuration Profiles

Create configuration profiles for different use cases:

```bash
# profiles/.env.research
DEFAULT_PROVIDER=anthropic
DEFAULT_MAX_PAPERS=50
MIN_SIMILARITY_THRESHOLD=0.8

# profiles/.env.demo
DEFAULT_PROVIDER=openai
DEFAULT_MAX_PAPERS=10
ENABLE_AGENT_DISCUSSIONS=true
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit `.env` files** to version control
2. **Use environment variables** in production environments
3. **Rotate API keys** regularly
4. **Limit API key permissions** when possible
5. **Monitor API usage** to detect unauthorized access

Add `.env` to your `.gitignore`:

```gitignore
.env
.env.local
.env.*.local
```

For production deployments, use secure secret management systems instead of `.env` files.