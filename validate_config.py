#!/usr/bin/env python3
"""
Configuration validation script for the Research Agent RAG System
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from config import Config

def validate_configuration():
    """Validate the current configuration"""
    print("🔧 Research Agent RAG System - Configuration Validation")
    print("=" * 65)
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - using environment variables only")
    
    print("\n📋 Configuration Check:")
    print("-" * 30)
    
    errors = []
    warnings = []
    
    # Check API keys
    api_keys = {
        "OpenAI": Config.OPENAI_API_KEY,
        "DeepSeek": Config.DEEPSEEK_API_KEY,
        "Anthropic": Config.ANTHROPIC_API_KEY
    }
    
    available_keys = []
    for provider, key in api_keys.items():
        if key:
            print(f"✅ {provider} API Key: Available")
            available_keys.append(provider.lower())
        else:
            print(f"❌ {provider} API Key: Not set")
    
    if not available_keys:
        errors.append("No API keys are configured")
    else:
        print(f"   Available providers: {', '.join(available_keys)}")
    
    # Check default provider
    print(f"\n🎯 Default Provider: {Config.DEFAULT_PROVIDER}")
    if Config.DEFAULT_PROVIDER not in ["openai", "deepseek", "anthropic"]:
        errors.append(f"Invalid default provider: {Config.DEFAULT_PROVIDER}")
    elif Config.DEFAULT_PROVIDER not in [k.lower() for k in available_keys]:
        errors.append(f"Default provider '{Config.DEFAULT_PROVIDER}' has no API key")
    else:
        print("✅ Default provider is valid and has API key")
    
    # Check models
    print(f"\n🤖 Model Configuration:")
    models = {
        "OpenAI": Config.OPENAI_MODEL,
        "DeepSeek": Config.DEEPSEEK_MODEL,
        "Anthropic": Config.ANTHROPIC_MODEL
    }
    
    for provider, model in models.items():
        print(f"   {provider}: {model}")
    
    # Check agent configurations
    print(f"\n👥 Agent Configuration:")
    agent_configs = Config.get_all_agent_configs()
    
    for agent_name, agent_config in agent_configs.items():
        provider = agent_config['provider']
        model = agent_config['model']
        api_key = Config.get_api_key_for_provider(provider)
        
        status = "✅" if api_key else "❌"
        print(f"   {agent_name.replace('_', ' ').title()}: {provider}/{model} {status}")
        
        if not api_key:
            errors.append(f"Agent '{agent_name}' uses provider '{provider}' but no API key is set")
    
    # Check other settings
    print(f"\n⚙️  Other Settings:")
    print(f"   Vector DB Path: {Config.VECTOR_DB_PATH}")
    print(f"   Max Papers: {Config.MAX_PAPERS_PER_QUERY}")
    print(f"   ArXiv Fallback: {Config.ENABLE_ARXIV_FALLBACK}")
    print(f"   Query Expansion: {Config.ENABLE_QUERY_EXPANSION}")
    print(f"   Agent Discussions: {Config.ENABLE_AGENT_DISCUSSIONS}")
    
    # Run official validation
    print(f"\n🔍 Running Official Validation:")
    try:
        Config.validate()
        print("✅ Official validation passed!")
    except Exception as e:
        errors.append(f"Official validation failed: {e}")
    
    # Display results
    print(f"\n" + "=" * 65)
    if errors:
        print("❌ CONFIGURATION ERRORS:")
        for error in errors:
            print(f"   • {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not errors and not warnings:
        print("🎉 CONFIGURATION IS VALID!")
        print("\nYou can now start the system:")
        print("   python main.py                    # Web interface")
        print("   python main.py --mode cli         # CLI mode")
        print("   streamlit run chat/chat_interface.py  # Direct Streamlit")
    elif errors:
        print(f"\n💡 To fix these issues:")
        print("1. Copy .env.example to .env if you haven't already")
        print("2. Add your API keys to the .env file")
        print("3. Set DEFAULT_PROVIDER to a provider you have an API key for")
        print("4. Run this script again to validate")
        return False
    
    return len(errors) == 0

def show_example_config():
    """Show example configuration"""
    print(f"\n📄 Example .env Configuration:")
    print("-" * 35)
    print("""
# Minimal configuration (OpenAI only)
OPENAI_API_KEY=sk-your-key-here
DEFAULT_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini

# Multi-provider configuration
OPENAI_API_KEY=sk-your-openai-key
DEEPSEEK_API_KEY=sk-your-deepseek-key
ANTHROPIC_API_KEY=sk-your-anthropic-key
DEFAULT_PROVIDER=openai

# Per-agent configuration
GOOGLE_ENGINEER_PROVIDER=openai
MIT_RESEARCHER_PROVIDER=anthropic
INDUSTRY_EXPERT_PROVIDER=deepseek
PAPER_ANALYST_PROVIDER=openai

# Optional settings
MIN_SIMILARITY_THRESHOLD=0.6
ENABLE_ARXIV_FALLBACK=true
DEFAULT_MAX_PAPERS=25
""")

def main():
    """Main validation function"""
    if validate_configuration():
        print("\n🚀 Ready to start the Research Agent RAG System!")
    else:
        print("\n🔧 Please fix the configuration issues above.")
        show_example_config()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())