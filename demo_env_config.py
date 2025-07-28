#!/usr/bin/env python3
"""
Demo script showing how to use .env file configuration for the Research Agent RAG System
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from config import Config

def demo_config_loading():
    """Demonstrate configuration loading from .env file"""
    print("🔧 Research Agent RAG System - Configuration Demo")
    print("=" * 60)
    
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validation passed!")
        
        # Display current configuration
        config_dict = Config.to_dict()
        
        print(f"\n📋 Current Configuration:")
        print(f"├── Default Provider: {config_dict['default_provider']}")
        
        print(f"├── API Keys Available:")
        for provider, available in config_dict['api_keys'].items():
            status = "✅" if available else "❌"
            print(f"│   ├── {provider.title()}: {status}")
        
        print(f"├── Models:")
        for provider, model in config_dict['models'].items():
            print(f"│   ├── {provider.title()}: {model}")
        
        print(f"├── Agent Configurations:")
        for agent_name, agent_config in config_dict['agent_configs'].items():
            provider = agent_config['provider']
            model = agent_config['model']
            print(f"│   ├── {agent_name.replace('_', ' ').title()}: {provider}/{model}")
        
        print(f"├── Search Settings:")
        search_config = config_dict['search']
        print(f"│   ├── Similarity Threshold: {search_config['min_similarity_threshold']}")
        print(f"│   ├── ArXiv Fallback: {search_config['enable_arxiv_fallback']}")
        print(f"│   └── Query Expansion: {search_config['enable_query_expansion']}")
        
        print(f"└── Research Settings:")
        research_config = config_dict['research']
        print(f"    ├── Max Papers: {research_config['default_max_papers']}")
        print(f"    └── Include Recent: {research_config['default_include_recent']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def demo_agent_config_methods():
    """Demonstrate agent configuration methods"""
    print(f"\n🤖 Agent Configuration Methods:")
    print("=" * 40)
    
    # Show individual agent configs
    agents = ["google_engineer", "mit_researcher", "industry_expert", "paper_analyst"]
    
    for agent_name in agents:
        config = Config.get_agent_config(agent_name)
        provider = config['provider']
        model = config['model']
        api_key_available = bool(Config.get_api_key_for_provider(provider))
        
        print(f"├── {agent_name.replace('_', ' ').title()}:")
        print(f"│   ├── Provider: {provider}")
        print(f"│   ├── Model: {model}")
        print(f"│   └── API Key: {'✅' if api_key_available else '❌'}")

def demo_env_file_examples():
    """Show examples of .env file configurations"""
    print(f"\n📄 .env File Configuration Examples:")
    print("=" * 45)
    
    print("1. Basic Configuration:")
    print("   OPENAI_API_KEY=sk-...")
    print("   DEFAULT_PROVIDER=openai")
    print("   OPENAI_MODEL=gpt-4o-mini")
    print()
    
    print("2. Multi-Provider Setup:")
    print("   OPENAI_API_KEY=sk-...")
    print("   DEEPSEEK_API_KEY=sk-...")
    print("   ANTHROPIC_API_KEY=sk-...")
    print("   DEFAULT_PROVIDER=openai")
    print()
    
    print("3. Per-Agent Configuration:")
    print("   GOOGLE_ENGINEER_PROVIDER=openai")
    print("   GOOGLE_ENGINEER_MODEL=gpt-4o")
    print("   MIT_RESEARCHER_PROVIDER=anthropic")
    print("   MIT_RESEARCHER_MODEL=claude-3-5-sonnet-20241022")
    print()
    
    print("4. JSON Configuration (Advanced):")
    print('   AGENT_CONFIGS={"google_engineer": {"provider": "openai", "model": "gpt-4o"}}')
    print()
    
    print("5. Search & Research Settings:")
    print("   MIN_SIMILARITY_THRESHOLD=0.7")
    print("   ENABLE_ARXIV_FALLBACK=true")
    print("   DEFAULT_MAX_PAPERS=30")
    print("   DEFAULT_SELECTED_AGENTS=Google Engineer,MIT Researcher")

def main():
    """Run the configuration demo"""
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_file):
        print("⚠️  No .env file found!")
        print("Please copy .env.example to .env and configure your API keys.")
        print()
        demo_env_file_examples()
        return
    
    # Demonstrate configuration loading
    if demo_config_loading():
        demo_agent_config_methods()
        print(f"\n🎉 Configuration loaded successfully!")
        print(f"You can now run: streamlit run chat/chat_interface.py")
    else:
        print(f"\n💡 Please check your .env file configuration.")
        demo_env_file_examples()

if __name__ == "__main__":
    main()