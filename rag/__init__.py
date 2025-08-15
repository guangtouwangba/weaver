"""
Research Agent RAG - Intelligent Knowledge Management Agent System

A comprehensive RAG (Retrieval-Augmented Generation) system based on NotebookLM concept
for intelligent knowledge management and document processing.
"""

__version__ = "0.1.0"
__author__ = "Research Agent Team"
__email__ = "team@research-agent.com"

# Core modules are available for import but not automatically loaded
# This prevents circular import issues during package initialization

__all__ = [
    "knowledge_store",
    "document_spliter", 
    "file_loader",
    "vector_store",
    "retriever",
    "router",
    "index",
    "models",
]
