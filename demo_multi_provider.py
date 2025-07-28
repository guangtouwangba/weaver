#!/usr/bin/env python3
"""
Demo script for multi-provider AI client support
"""

import os
import logging
from utils.ai_client import AIClientFactory, ChatMessage

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_provider_info():
    """Demo provider information"""
    print("=== AI Provider Information ===")
    
    providers = AIClientFactory.get_supported_providers()
    print(f"Supported providers: {', '.join(providers)}")
    
    for provider in providers:
        info = AIClientFactory.get_provider_info(provider)
        print(f"\n📋 {provider.upper()}:")
        print(f"   Models: {', '.join(info['supported_models'])}")
        print(f"   Features: {', '.join(info['features'])}")
        print(f"   Docs: {info['api_docs_url']}")

def demo_client_creation():
    """Demo client creation for different providers"""
    print("\n=== Client Creation Demo ===")
    
    # Get API keys from environment
    openai_key = os.getenv('OPENAI_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    clients = {}
    
    # Try to create OpenAI client
    if openai_key:
        try:
            clients['openai'] = AIClientFactory.create_client('openai', openai_key)
            print("✅ OpenAI client created successfully")
        except Exception as e:
            print(f"❌ OpenAI client creation failed: {e}")
    else:
        print("⚠️  OPENAI_API_KEY not found")
    
    # Try to create DeepSeek client
    if deepseek_key:
        try:
            clients['deepseek'] = AIClientFactory.create_client('deepseek', deepseek_key)
            print("✅ DeepSeek client created successfully")
        except Exception as e:
            print(f"❌ DeepSeek client creation failed: {e}")
    else:
        print("⚠️  DEEPSEEK_API_KEY not found")
    
    # Try to create Anthropic client
    if anthropic_key:
        try:
            clients['anthropic'] = AIClientFactory.create_client('anthropic', anthropic_key)
            print("✅ Anthropic client created successfully")
        except Exception as e:
            print(f"❌ Anthropic client creation failed: {e}")
    else:
        print("⚠️  ANTHROPIC_API_KEY not found")
    
    return clients

def demo_chat_completion(clients):
    """Demo chat completion with different providers"""
    print("\n=== Chat Completion Demo ===")
    
    test_messages = [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="What is the difference between RAG and traditional search?")
    ]
    
    for provider_name, client in clients.items():
        print(f"\n🤖 Testing {provider_name.upper()}...")
        
        try:
            # Get available models for this provider
            available_models = client.get_available_models()
            test_model = available_models[0] if available_models else "default"
            
            print(f"   Using model: {test_model}")
            
            # Create chat completion
            response = client.create_chat_completion(
                messages=test_messages,
                model=test_model,
                temperature=0.7,
                max_tokens=200
            )
            
            print(f"   ✅ Success!")
            print(f"   Provider: {response.provider}")
            print(f"   Model: {response.model}")
            print(f"   Response: {response.content[:100]}...")
            
            if response.usage:
                print(f"   Usage: {response.usage}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

def demo_model_validation(clients):
    """Demo model validation"""
    print("\n=== Model Validation Demo ===")
    
    test_models = [
        "gpt-4o-mini",
        "deepseek-chat", 
        "claude-3-5-sonnet-20241022"
    ]
    
    for provider_name, client in clients.items():
        print(f"\n🔍 Validating models for {provider_name.upper()}:")
        
        available_models = client.get_available_models()
        print(f"   Available models: {len(available_models)}")
        
        for test_model in test_models:
            is_valid = client.validate_model(test_model)
            status = "✅" if is_valid else "❌"
            print(f"   {status} {test_model}")

def demo_orchestrator_integration():
    """Demo orchestrator integration with multiple providers"""
    print("\n=== Orchestrator Integration Demo ===")
    
    try:
        from agents.orchestrator import ResearchOrchestrator
        
        # Get API keys
        openai_key = os.getenv('OPENAI_API_KEY')
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not any([openai_key, deepseek_key, anthropic_key]):
            print("❌ No API keys found. Please set at least one of:")
            print("   OPENAI_API_KEY, DEEPSEEK_API_KEY, or ANTHROPIC_API_KEY")
            return
        
        # Create orchestrator with multiple providers
        print("🔧 Creating orchestrator with multi-provider support...")
        
        orchestrator = ResearchOrchestrator(
            openai_api_key=openai_key,
            deepseek_api_key=deepseek_key,
            anthropic_api_key=anthropic_key,
            default_provider="openai",  # or "deepseek" or "anthropic"
            db_path="./data/vector_db"
        )
        
        print(f"✅ Orchestrator created successfully")
        print(f"   Active agents: {len(orchestrator.agents)}")
        
        for agent_name, agent in orchestrator.agents.items():
            print(f"   - {agent_name}: {agent.provider} ({agent.model})")
        
        # Test a simple query
        print("\n🧪 Testing orchestrator with simple query...")
        
        try:
            result = orchestrator.chat_with_papers(
                query="What is machine learning?",
                n_papers=2,
                min_similarity_threshold=0.1
            )
            
            print(f"✅ Query completed successfully")
            print(f"   Papers found: {len(result.get('relevant_papers', []))}")
            print(f"   Response length: {len(result.get('response', ''))}")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
        
    except Exception as e:
        print(f"❌ Orchestrator integration failed: {e}")

def main():
    """Main demo function"""
    print("🚀 Multi-Provider AI Client Demo")
    print("=" * 50)
    
    # Demo 1: Provider information
    demo_provider_info()
    
    # Demo 2: Client creation
    clients = demo_client_creation()
    
    if not clients:
        print("\n❌ No clients available. Please check your API keys.")
        return
    
    # Demo 3: Chat completion
    demo_chat_completion(clients)
    
    # Demo 4: Model validation
    demo_model_validation(clients)
    
    # Demo 5: Orchestrator integration
    demo_orchestrator_integration()
    
    print("\n🎉 Demo completed!")

if __name__ == "__main__":
    main() 