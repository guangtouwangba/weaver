"""
文本文件加载器

专门处理纯文本文件的加载器。
支持多种编码格式和错误处理。
"""

import os
import logging
from typing import Optional, Dict, Any
import asyncio

# 可选依赖：chardet 用于更好的编码检测
try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False
    chardet = None

from .base import IFileLoader, FileLoaderError
from ..models import Document, ContentType, create_document_from_path

logger = logging.getLogger(__name__)


class TextFileLoader(IFileLoader):
    """文本文件加载器"""
    
    def __init__(self, 
                 default_encoding: str = 'utf-8',
                 fallback_encodings: list = None,
                 max_file_size: int = 100 * 1024 * 1024):  # 100MB
        """
        初始化文本文件加载器
        
        Args:
            default_encoding: 默认编码
            fallback_encodings: 回退编码列表
            max_file_size: 最大文件大小（字节）
        """
        self.default_encoding = default_encoding
        self.fallback_encodings = fallback_encodings or ['gbk', 'gb2312', 'latin1', 'ascii']
        self.max_file_size = max_file_size
        
        logger.info(f"TextFileLoader 初始化: 默认编码={default_encoding}, 最大文件大小={max_file_size/1024/1024:.1f}MB")
    
    @property
    def loader_name(self) -> str:
        """获取加载器名称"""
        return "TextFileLoader"
    
    def supported_formats(self) -> list:
        """获取支持的文件格式"""
        return ['.txt', '.md', '.markdown', '.csv', '.log', '.ini', '.cfg', '.conf']
    
    def supported_types(self) -> list:
        """获取支持的内容类型（接口方法）"""
        return [ContentType.TXT]
    
    def supports_content_type(self, content_type: ContentType) -> bool:
        """检查是否支持指定的内容类型"""
        return content_type in self.supported_types()
    
    async def validate_file(self, file_path: str) -> bool:
        """验证文件是否可以加载（接口方法）"""
        return await self.can_load(file_path)
    
    async def can_load(self, file_path: str) -> bool:
        """检查是否可以加载指定文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"文件过大: {file_path} ({file_size/1024/1024:.1f}MB)")
                return False
            
            # 检查文件扩展名
            _, ext = os.path.splitext(file_path.lower())
            if ext in self.supported_formats():
                return True
            
            # 尝试读取文件头部判断是否为文本文件
            try:
                with open(file_path, 'rb') as f:
                    sample = f.read(1024)
                    
                # 检查是否包含过多二进制数据
                if sample:
                    # 计算非ASCII字符比例
                    non_text_chars = sum(1 for byte in sample if byte < 32 and byte not in [9, 10, 13])
                    if non_text_chars / len(sample) > 0.3:  # 超过30%的非文本字符
                        return False
                
                return True
                
            except Exception as e:
                logger.debug(f"检查文件类型失败 {file_path}: {e}")
                return False
            
        except Exception as e:
            logger.error(f"检查文件可加载性失败 {file_path}: {e}")
            return False
    
    async def load_document(self, request) -> Document:
        """加载文档（接口方法）"""
        from ..models import FileLoadRequest
        
        # 如果传入的是路径字符串，转换为请求对象
        if isinstance(request, str):
            file_path = request
            metadata = {}
        elif isinstance(request, FileLoadRequest):
            file_path = request.file_path
            metadata = request.metadata or {}
        else:
            file_path = request
            metadata = {}
        
        return await self.load_file(file_path, metadata)
    
    async def load_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """加载文本文件"""
        try:
            # 验证文件
            if not await self.can_load(file_path):
                raise FileLoaderError(f"无法加载文件: {file_path}")
            
            # 检测编码
            encoding = await self._detect_encoding(file_path)
            
            # 读取文件内容
            content = await self._read_file_content(file_path, encoding)
            
            # 创建文档对象
            document = create_document_from_path(file_path, content)
            
            # 添加元数据
            document.metadata.update({
                'loader': self.loader_name,
                'encoding': encoding,
                'file_size': len(content.encode('utf-8')),
                'char_count': len(content),
                'line_count': len(content.splitlines()),
                'has_chardet': HAS_CHARDET,
                **(metadata or {})
            })
            
            logger.info(f"成功加载文本文件: {file_path} ({len(content)} 字符, 编码: {encoding})")
            return document
            
        except FileLoaderError:
            raise
        except Exception as e:
            logger.error(f"加载文本文件失败 {file_path}: {e}")
            raise FileLoaderError(f"加载文本文件失败: {str(e)}")
    
    async def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            if HAS_CHARDET:
                # 使用chardet检测编码
                with open(file_path, 'rb') as f:
                    sample = f.read(10240)  # 读取前10KB样本
                    if sample:
                        detection = chardet.detect(sample)
                        
                        if detection and detection.get('confidence', 0) > 0.7:
                            detected_encoding = detection['encoding']
                            logger.debug(f"检测到编码: {detected_encoding} (置信度: {detection.get('confidence', 0):.2f})")
                            return detected_encoding
            else:
                # 没有chardet时使用基本的检测方法
                with open(file_path, 'rb') as f:
                    sample = f.read(1000)
                    if sample:
                        # 简单的UTF-8检测
                        try:
                            sample.decode('utf-8')
                            logger.debug("检测到编码: utf-8 (基本检测)")
                            return 'utf-8'
                        except UnicodeDecodeError:
                            pass
                        
                        # 检测常见编码
                        for encoding in self.fallback_encodings:
                            try:
                                sample.decode(encoding)
                                logger.debug(f"检测到编码: {encoding} (基本检测)")
                                return encoding
                            except UnicodeDecodeError:
                                continue
            
            # 回退到默认编码
            logger.warning(f"无法检测编码，使用默认编码: {self.default_encoding}")
            return self.default_encoding
            
        except Exception as e:
            logger.warning(f"编码检测失败 {file_path}: {e}")
            return self.default_encoding
    
    async def _read_file_content(self, file_path: str, encoding: str) -> str:
        """读取文件内容"""
        try:
            # 使用异步方式读取文件
            def read_sync():
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    return f.read()
            
            # 在线程池中执行文件读取
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, read_sync)
            
            return content
            
        except Exception as e:
            # 如果指定编码失败，尝试回退编码
            logger.warning(f"使用编码 {encoding} 读取失败，尝试回退编码: {e}")
            
            for fallback_encoding in self.fallback_encodings:
                try:
                    def read_fallback():
                        with open(file_path, 'r', encoding=fallback_encoding, errors='replace') as f:
                            return f.read()
                    
                    loop = asyncio.get_event_loop()
                    content = await loop.run_in_executor(None, read_fallback)
                    
                    logger.info(f"使用回退编码 {fallback_encoding} 成功读取文件")
                    return content
                    
                except Exception as fallback_error:
                    logger.debug(f"回退编码 {fallback_encoding} 也失败: {fallback_error}")
                    continue
            
            # 所有编码都失败，抛出异常
            raise FileLoaderError(f"无法使用任何编码读取文件: {file_path}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "loader_name": self.loader_name,
            "status": "healthy",
            "supported_formats": self.supported_formats(),
            "default_encoding": self.default_encoding,
            "max_file_size_mb": self.max_file_size / 1024 / 1024,
            "has_chardet": HAS_CHARDET,
            "fallback_encodings": self.fallback_encodings
        }