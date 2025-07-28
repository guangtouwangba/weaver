# Research Agent RAG System - Usage Guide

## 🔧 Configuration Setup

### Method 1: Interactive Configuration (Recommended)

Run the configuration manager to set up your API keys and model preferences:

```bash
python config_manager.py
```

This will guide you through:
- Setting API keys for OpenAI, DeepSeek, and Anthropic
- Choosing default providers and models
- Configuring individual agents
- Setting research parameters

### Method 2: Web Interface Configuration

1. Start the web interface:
```bash
streamlit run chat/chat_interface.py
```

2. Use the sidebar to configure:
   - **API Keys**: Enter your OpenAI, DeepSeek, and/or Anthropic API keys
   - **Default Provider**: Choose the default AI provider
   - **Model Selection**: Select models for each provider
   - **Agent Configuration**: Configure individual agents with specific providers and models
   - **Research Parameters**: Adjust paper limits and search settings

## 🤖 Supported AI Providers

### OpenAI
- **Models**: `gpt-4o`, `gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo`
- **API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### DeepSeek
- **Models**: `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3`, `deepseek-r1`
- **API Key**: Get from [DeepSeek Platform](https://platform.deepseek.com/)
- **Features**: OpenAI-compatible API

### Anthropic
- **Models**: `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`, `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- **API Key**: Get from [Anthropic Console](https://console.anthropic.com/)

## 👥 Agent Configuration

### Available Agents
1. **Google Engineer**: Specialized in large-scale systems and engineering practices
2. **MIT Researcher**: Academic research perspective and methodology
3. **Industry Expert**: Practical business and industry applications
4. **Paper Analyst**: Detailed paper analysis and synthesis

### Per-Agent Configuration
Each agent can be configured with:
- **Provider**: Choose which AI provider to use
- **Model**: Select specific model for that provider
- **Enabled/Disabled**: Toggle agent participation

## 📚 Research Parameters

### Paper Limits
- **Max Papers**: Number of papers to analyze per topic (5-50)
- **Include Recent**: Prioritize recent papers in search results
- **Min Similarity**: Threshold for paper relevance (0.1-1.0)

### Search Strategy
- **Query Expansion**: Automatically expands search queries for better coverage
- **Vector Search**: Uses semantic similarity to find relevant papers
- **ArXiv Fallback**: Direct arXiv search when vector database is insufficient

## 🚀 Usage Examples

### Basic Usage
1. Start the web interface
2. Enter your API keys in the sidebar
3. Type a research query like: "What are the latest developments in transformer architecture?"
4. The system will:
   - Search for relevant papers
   - Analyze them with multiple agents
   - Generate a comprehensive discussion

### Advanced Configuration
1. Use the sidebar to configure individual agents
2. Set different providers for different agents:
   - Google Engineer: DeepSeek (for technical analysis)
   - MIT Researcher: OpenAI (for academic perspective)
   - Industry Expert: Anthropic (for business insights)
   - Paper Analyst: DeepSeek (for detailed analysis)

### Multi-Provider Strategy
```python
# Example configuration
agent_configs = {
    "google_engineer": {
        "provider": "deepseek",
        "model": "deepseek-reasoner"
    },
    "mit_researcher": {
        "provider": "openai", 
        "model": "gpt-4o"
    },
    "industry_expert": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022"
    },
    "paper_analyst": {
        "provider": "deepseek",
        "model": "deepseek-chat"
    }
}
```

## 🔍 Features

### Multi-Agent Discussion
- **Latest Research**: What are the newest developments?
- **Problems & Challenges**: What issues exist in the field?
- **Engineering Applications**: What can be used in practice?
- **New Directions**: What are emerging research directions?

### No Artificial Limits
- **Paper Analysis**: All available papers are analyzed
- **Theme Extraction**: All identified themes are included
- **Recommendations**: All generated recommendations are provided
- **Search Results**: No arbitrary limits on search results

### Flexible Configuration
- **Provider Mix**: Use different providers for different agents
- **Model Selection**: Choose optimal models for each use case
- **Dynamic Switching**: Change providers and models on the fly
- **Persistent Settings**: Configuration is saved between sessions

## 🛠️ Troubleshooting

### Common Issues

1. **No API Keys Provided**
   - Solution: Enter at least one API key in the sidebar
   - Supported: OpenAI, DeepSeek, or Anthropic

2. **Model Not Available**
   - Solution: Check the provider's model list
   - Ensure you have access to the selected model

3. **Search Timeout**
   - Solution: The system now waits indefinitely
   - Check your internet connection and API key validity

4. **Agent Configuration Issues**
   - Solution: Use the interactive config manager
   - Or reset configuration in the web interface

### Debug Information
- Enable "Show Logs" in the sidebar to see detailed information
- Check the debug section for error messages
- Use the configuration manager to validate settings

## 📖 API Documentation

### DeepSeek API
- **Documentation**: https://api-docs.deepseek.com/zh-cn/
- **Compatibility**: OpenAI-compatible format
- **Models**: Chat and reasoning models available

### OpenAI API
- **Documentation**: https://platform.openai.com/docs
- **Models**: GPT-4 and GPT-3.5 series

### Anthropic API
- **Documentation**: https://docs.anthropic.com/
- **Models**: Claude 3.5 and Claude 3 series

## 🔄 Migration from Previous Version

If you're upgrading from the previous version:

1. **API Keys**: Your existing OpenAI API key will still work
2. **Configuration**: New configuration options are optional
3. **Backward Compatibility**: All existing functionality is preserved
4. **New Features**: Multi-provider support is additive

## 📝 Configuration File

The system creates a `config.json` file with your settings:

```json
{
  "api_keys": {
    "openai": "your-openai-key",
    "deepseek": "your-deepseek-key", 
    "anthropic": "your-anthropic-key"
  },
  "providers": {
    "default": "openai",
    "openai": {
      "model": "gpt-4o-mini",
      "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
    },
    "deepseek": {
      "model": "deepseek-chat",
      "available_models": ["deepseek-chat", "deepseek-reasoner", "deepseek-v3", "deepseek-r1"]
    }
  },
  "agents": {
    "google_engineer": {
      "provider": "deepseek",
      "model": "deepseek-reasoner",
      "enabled": true
    }
  },
  "research": {
    "max_papers": 20,
    "include_recent": true,
    "min_similarity_threshold": 0.5
  }
}
```

## 🎯 Best Practices

1. **Provider Selection**
   - Use DeepSeek for technical analysis and reasoning
   - Use OpenAI for general conversation and synthesis
   - Use Anthropic for business and industry insights

2. **Model Selection**
   - Use larger models (GPT-4, Claude-3.5) for complex analysis
   - Use smaller models (GPT-3.5, Claude-3-Haiku) for cost efficiency
   - Use specialized models (DeepSeek-Reasoner) for technical tasks

3. **Agent Configuration**
   - Match agent expertise with appropriate providers
   - Enable all agents for comprehensive analysis
   - Use different models for different perspectives

4. **Research Parameters**
   - Start with default settings
   - Increase max papers for comprehensive analysis
   - Adjust similarity threshold based on topic specificity 