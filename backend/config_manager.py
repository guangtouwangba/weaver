#!/usr/bin/env python3
"""
Configuration Manager for Research Agent RAG System
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration for the research agent system"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return self._get_default_config()
        else:
            logger.info("No config file found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "api_keys": {
                "openai": "",
                "deepseek": "",
                "anthropic": ""
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
                },
                "anthropic": {
                    "model": "claude-3-5-sonnet-20241022",
                    "available_models": [
                        "claude-3-5-sonnet-20241022",
                        "claude-3-5-haiku-20241022",
                        "claude-3-opus-20240229",
                        "claude-3-sonnet-20240229"
                    ]
                }
            },
            "agents": {
                "google_engineer": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "enabled": True
                },
                "mit_researcher": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "enabled": True
                },
                "industry_expert": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "enabled": True
                },
                "paper_analyst": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "enabled": True
                }
            },
            "research": {
                "max_papers": 20,
                "include_recent": True,
                "min_similarity_threshold": 0.5
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_api_key(self, provider: str) -> str:
        """Get API key for a provider"""
        return self.config["api_keys"].get(provider, "")
    
    def set_api_key(self, provider: str, api_key: str):
        """Set API key for a provider"""
        self.config["api_keys"][provider] = api_key
        self.save_config()
    
    def get_default_provider(self) -> str:
        """Get default provider"""
        return self.config["providers"]["default"]
    
    def set_default_provider(self, provider: str):
        """Set default provider"""
        self.config["providers"]["default"] = provider
        self.save_config()
    
    def get_model(self, provider: str) -> str:
        """Get default model for a provider"""
        return self.config["providers"][provider]["model"]
    
    def set_model(self, provider: str, model: str):
        """Set default model for a provider"""
        self.config["providers"][provider]["model"] = model
        self.save_config()
    
    def get_available_models(self, provider: str) -> list:
        """Get available models for a provider"""
        return self.config["providers"][provider]["available_models"]
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for an agent"""
        return self.config["agents"].get(agent_name, {})
    
    def set_agent_config(self, agent_name: str, config: Dict[str, Any]):
        """Set configuration for an agent"""
        self.config["agents"][agent_name] = config
        self.save_config()
    
    def get_research_config(self) -> Dict[str, Any]:
        """Get research configuration"""
        return self.config["research"]
    
    def set_research_config(self, config: Dict[str, Any]):
        """Set research configuration"""
        self.config["research"].update(config)
        self.save_config()
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check if at least one API key is provided
        api_keys = self.config["api_keys"]
        if not any(api_keys.values()):
            errors.append("No API keys provided")
        
        # Check if default provider is valid
        default_provider = self.config["providers"]["default"]
        if default_provider not in ["openai", "deepseek", "anthropic"]:
            errors.append(f"Invalid default provider: {default_provider}")
        
        # Check if models are valid for their providers
        for provider, provider_config in self.config["providers"].items():
            if provider == "default":
                continue
            
            model = provider_config["model"]
            available_models = provider_config["available_models"]
            if model not in available_models:
                errors.append(f"Invalid model '{model}' for provider '{provider}'")
        
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def print_config(self):
        """Print current configuration"""
        print("🔧 Current Configuration")
        print("=" * 50)
        
        # API Keys
        print("\n🔑 API Keys:")
        for provider, key in self.config["api_keys"].items():
            status = "✅ Set" if key else "❌ Not set"
            print(f"   {provider.upper()}: {status}")
        
        # Default Provider
        print(f"\n🤖 Default Provider: {self.config['providers']['default'].upper()}")
        
        # Provider Models
        print("\n📋 Provider Models:")
        for provider, config in self.config["providers"].items():
            if provider == "default":
                continue
            print(f"   {provider.upper()}: {config['model']}")
        
        # Agent Configuration
        print("\n👥 Agent Configuration:")
        for agent_name, config in self.config["agents"].items():
            status = "✅ Enabled" if config.get("enabled", True) else "❌ Disabled"
            print(f"   {agent_name}: {config['provider']} ({config['model']}) - {status}")
        
        # Research Configuration
        print("\n📚 Research Configuration:")
        research_config = self.config["research"]
        print(f"   Max papers: {research_config['max_papers']}")
        print(f"   Include recent: {research_config['include_recent']}")
        print(f"   Min similarity: {research_config['min_similarity_threshold']}")

def interactive_config():
    """Interactive configuration setup"""
    config_manager = ConfigManager()
    
    print("🚀 Research Agent RAG System - Configuration Setup")
    print("=" * 60)
    
    while True:
        print("\n📋 Configuration Menu:")
        print("1. Set API Keys")
        print("2. Configure Providers")
        print("3. Configure Agents")
        print("4. Configure Research Parameters")
        print("5. View Current Configuration")
        print("6. Validate Configuration")
        print("7. Save and Exit")
        print("0. Exit without saving")
        
        choice = input("\nEnter your choice (0-7): ").strip()
        
        if choice == "1":
            set_api_keys(config_manager)
        elif choice == "2":
            configure_providers(config_manager)
        elif choice == "3":
            configure_agents(config_manager)
        elif choice == "4":
            configure_research(config_manager)
        elif choice == "5":
            config_manager.print_config()
        elif choice == "6":
            if config_manager.validate_config():
                print("✅ Configuration is valid!")
            else:
                print("❌ Configuration has errors. Please fix them.")
        elif choice == "7":
            config_manager.save_config()
            print("✅ Configuration saved!")
            break
        elif choice == "0":
            print("👋 Exiting without saving...")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def set_api_keys(config_manager: ConfigManager):
    """Set API keys interactively"""
    print("\n🔑 Setting API Keys")
    print("-" * 30)
    
    providers = ["openai", "deepseek", "anthropic"]
    
    for provider in providers:
        current_key = config_manager.get_api_key(provider)
        masked_key = "*" * len(current_key) if current_key else "Not set"
        
        print(f"\n{provider.upper()} API Key (current: {masked_key}):")
        new_key = input("Enter new key (or press Enter to keep current): ").strip()
        
        if new_key:
            config_manager.set_api_key(provider, new_key)
            print(f"✅ {provider.upper()} API key updated")
        else:
            print(f"⏭️  Keeping current {provider.upper()} API key")

def configure_providers(config_manager: ConfigManager):
    """Configure providers interactively"""
    print("\n🤖 Configuring Providers")
    print("-" * 30)
    
    # Set default provider
    current_default = config_manager.get_default_provider()
    print(f"\nCurrent default provider: {current_default.upper()}")
    
    providers = ["openai", "deepseek", "anthropic"]
    print("Available providers:")
    for i, provider in enumerate(providers, 1):
        print(f"   {i}. {provider.upper()}")
    
    choice = input("Select default provider (1-3): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= 3:
        new_default = providers[int(choice) - 1]
        config_manager.set_default_provider(new_default)
        print(f"✅ Default provider set to {new_default.upper()}")
    
    # Configure models for each provider
    for provider in providers:
        current_model = config_manager.get_model(provider)
        available_models = config_manager.get_available_models(provider)
        
        print(f"\n{provider.upper()} Models:")
        for i, model in enumerate(available_models, 1):
            marker = " ← Current" if model == current_model else ""
            print(f"   {i}. {model}{marker}")
        
        choice = input(f"Select {provider.upper()} model (1-{len(available_models)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(available_models):
            new_model = available_models[int(choice) - 1]
            config_manager.set_model(provider, new_model)
            print(f"✅ {provider.upper()} model set to {new_model}")

def configure_agents(config_manager: ConfigManager):
    """Configure agents interactively"""
    print("\n👥 Configuring Agents")
    print("-" * 30)
    
    agents = ["google_engineer", "mit_researcher", "industry_expert", "paper_analyst"]
    providers = ["openai", "deepseek", "anthropic"]
    
    for agent_name in agents:
        current_config = config_manager.get_agent_config(agent_name)
        current_provider = current_config.get("provider", "openai")
        current_model = current_config.get("model", "gpt-4o-mini")
        current_enabled = current_config.get("enabled", True)
        
        print(f"\n{agent_name.replace('_', ' ').title()}:")
        print(f"   Current: {current_provider} ({current_model}) - {'Enabled' if current_enabled else 'Disabled'}")
        
        # Provider selection
        print("   Available providers:")
        for i, provider in enumerate(providers, 1):
            marker = " ← Current" if provider == current_provider else ""
            print(f"      {i}. {provider.upper()}{marker}")
        
        choice = input("   Select provider (1-3): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 3:
            new_provider = providers[int(choice) - 1]
            current_config["provider"] = new_provider
            
            # Model selection for the provider
            available_models = config_manager.get_available_models(new_provider)
            print(f"   Available models for {new_provider.upper()}:")
            for i, model in enumerate(available_models, 1):
                marker = " ← Current" if model == current_model else ""
                print(f"      {i}. {model}{marker}")
            
            choice = input(f"   Select {new_provider.upper()} model (1-{len(available_models)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(available_models):
                new_model = available_models[int(choice) - 1]
                current_config["model"] = new_model
                
                # Enable/disable
                enable = input("   Enable this agent? (y/n): ").strip().lower()
                current_config["enabled"] = enable in ["y", "yes"]
                
                config_manager.set_agent_config(agent_name, current_config)
                print(f"   ✅ {agent_name} configured")

def configure_research(config_manager: ConfigManager):
    """Configure research parameters interactively"""
    print("\n📚 Configuring Research Parameters")
    print("-" * 40)
    
    current_config = config_manager.get_research_config()
    
    # Max papers
    current_max = current_config.get("max_papers", 20)
    print(f"\nCurrent max papers per topic: {current_max}")
    new_max = input("Enter new max papers (5-50): ").strip()
    if new_max.isdigit() and 5 <= int(new_max) <= 50:
        current_config["max_papers"] = int(new_max)
    
    # Include recent
    current_recent = current_config.get("include_recent", True)
    print(f"Current include recent papers: {current_recent}")
    recent_choice = input("Include recent papers? (y/n): ").strip().lower()
    current_config["include_recent"] = recent_choice in ["y", "yes"]
    
    # Min similarity threshold
    current_threshold = current_config.get("min_similarity_threshold", 0.5)
    print(f"Current min similarity threshold: {current_threshold}")
    new_threshold = input("Enter new threshold (0.1-1.0): ").strip()
    try:
        threshold = float(new_threshold)
        if 0.1 <= threshold <= 1.0:
            current_config["min_similarity_threshold"] = threshold
    except ValueError:
        print("Invalid threshold value")
    
    config_manager.set_research_config(current_config)
    print("✅ Research parameters updated")

if __name__ == "__main__":
    interactive_config() 