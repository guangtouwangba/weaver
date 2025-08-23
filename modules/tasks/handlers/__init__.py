"""
任务处理器模块

包含各种业务领域的任务处理器实现：
- RAG相关任务处理器
- 文件处理任务处理器
- 通知任务处理器
"""

# 这里将自动导入所有处理器以便自动注册
from modules.tasks.handlers import file_handlers, rag_handlers

__all__ = ["rag_handlers", "file_handlers"]
