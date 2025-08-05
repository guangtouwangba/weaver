"""
RAG Question Answering Module for ArXiv Paper Analysis

This module provides intelligent question-answering capabilities
based on the collected ArXiv papers using Retrieval-Augmented Generation (RAG).
"""

__version__ = "1.0.0"
__author__ = "ArXiv Paper Fetcher"

from .engine.rag_engine import RAGEngine
from .cli.terminal_ui import TerminalUI

__all__ = ["RAGEngine", "TerminalUI"]