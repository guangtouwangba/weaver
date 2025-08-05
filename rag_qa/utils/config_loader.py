#!/usr/bin/env python3
"""
Configuration loader for RAG module
Extends the main config with RAG-specific settings
"""

import yaml
import os
from typing import Dict, Any

class RAGConfigLoader:
    """Configuration loader for RAG module"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Add default RAG configuration if not present
            if 'rag' not in config:
                config['rag'] = self._get_default_rag_config()
            
            return config
        except Exception as e:
            raise ValueError(f"Failed to load config from {self.config_path}: {e}")
    
    def _get_default_rag_config(self) -> Dict[str, Any]:
        """Get default RAG configuration"""
        return {
            'vector_db': {
                'type': 'chroma',
                'persist_directory': './rag_vector_db',
                'collection_name': 'arxiv_papers'
            },
            'text_processing': {
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'max_chunks_per_doc': 50
            },
            'embeddings': {
                'model': 'sentence-transformers/all-MiniLM-L6-v2',
                'device': 'cpu'
            },
            'llm': {
                'provider': 'openai',
                'model': 'gpt-3.5-turbo',
                'max_tokens': 2000,
                'temperature': 0.1
            },
            'retrieval': {
                'top_k': 5,
                'similarity_threshold': 0.7,
                'max_context_length': 4000
            },
            'ui': {
                'max_keywords_display': 20,
                'results_per_page': 3,
                'show_similarity_scores': True
            }
        }
    
    def _validate_config(self):
        """Validate RAG configuration"""
        rag_config = self.config.get('rag', {})
        
        # Validate required sections
        required_sections = ['vector_db', 'text_processing', 'embeddings', 'llm', 'retrieval']
        for section in required_sections:
            if section not in rag_config:
                raise ValueError(f"Missing required RAG config section: {section}")
        
        # Validate vector_db config
        vector_db = rag_config['vector_db']
        if vector_db['type'] not in ['chroma', 'faiss']:
            raise ValueError(f"Unsupported vector database type: {vector_db['type']}")
        
        # Validate LLM config
        llm_config = rag_config['llm']
        if llm_config['provider'] not in ['openai', 'anthropic', 'local']:
            raise ValueError(f"Unsupported LLM provider: {llm_config['provider']}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get full configuration"""
        return self.config
    
    def get_rag_config(self) -> Dict[str, Any]:
        """Get RAG-specific configuration"""
        return self.config.get('rag', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config.get('database', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration"""
        return self.config.get('pdf_storage', {})
    
    def update_rag_config(self, updates: Dict[str, Any]):
        """Update RAG configuration"""
        if 'rag' not in self.config:
            self.config['rag'] = {}
        
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config['rag'], updates)
        self._validate_config()
    
    def save_config(self):
        """Save configuration back to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save config to {self.config_path}: {e}")