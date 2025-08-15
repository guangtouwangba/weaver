"""
文件加载器基础接口
支持多种文档格式的加载和解析
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Iterator
from pathlib import Path
import asyncio

from ..models import Document, ProcessingResult


class BaseFileLoader(ABC):
    """文件加载器基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文件加载器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        返回支持的文件格式列表
        
        Returns:
            List[str]: 支持的文件扩展名列表，如 ['.txt', '.pdf', '.docx']
        """
        pass
    
    @abstractmethod
    async def load(self, file_path: str) -> Document:
        """
        加载单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Document: 加载的文档对象
            
        Raises:
            FileNotFoundError: 文件不存在
            UnsupportedFormatError: 不支持的文件格式
            DocumentLoadError: 文档加载错误
        """
        pass
    
    @abstractmethod
    async def load_batch(self, file_paths: List[str]) -> Iterator[ProcessingResult]:
        """
        批量加载文件
        
        Args:
            file_paths: 文件路径列表
            
        Yields:
            ProcessingResult: 每个文件的处理结果
        """
        pass
    
    def can_handle(self, file_path: str) -> bool:
        """
        检查是否可以处理指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否可以处理
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_formats()
    
    def validate_file(self, file_path: str) -> List[str]:
        """
        验证文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors = []
        
        # 检查文件是否存在
        if not Path(file_path).exists():
            errors.append(f"File not found: {file_path}")
            return errors
        
        # 检查文件格式
        if not self.can_handle(file_path):
            errors.append(f"Unsupported file format: {Path(file_path).suffix}")
        
        # 检查文件大小
        max_size = self.config.get('max_file_size_mb', 100) * 1024 * 1024
        file_size = Path(file_path).stat().st_size
        if file_size > max_size:
            errors.append(f"File too large: {file_size / (1024*1024):.1f}MB > {max_size / (1024*1024)}MB")
        
        return errors
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取文件基础元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        file_path_obj = Path(file_path)
        stat = file_path_obj.stat()
        
        return {
            'file_name': file_path_obj.name,
            'file_size': stat.st_size,
            'file_extension': file_path_obj.suffix.lower(),
            'created_time': stat.st_ctime,
            'modified_time': stat.st_mtime,
            'file_path': str(file_path_obj.absolute())
        }


# 异常类定义
class DocumentLoadError(Exception):
    """文档加载错误"""
    pass


class UnsupportedFormatError(DocumentLoadError):
    """不支持的文件格式错误"""
    pass