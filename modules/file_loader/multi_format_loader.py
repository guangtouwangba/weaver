"""
多格式文件加载器

支持多种文件格式的加载器，包括PDF、Word文档等。
通过组合多个专用加载器来处理不同格式。
"""

import logging
from typing import Dict, List, Optional
import asyncio

from .base import IFileLoader, FileLoaderError
from .text_loader import TextFileLoader
from ..models import Document, FileLoadRequest
from ..schemas.enums import ContentType

logger = logging.getLogger(__name__)


class MultiFormatFileLoader(IFileLoader):
    """多格式文件加载器"""
    
    def __init__(self, max_file_size_mb: int = 100):
        """
        初始化多格式文件加载器
        
        Args:
            max_file_size_mb: 最大文件大小(MB)
        """
        self.max_file_size_mb = max_file_size_mb
        
        # 初始化各种专用加载器
        self._loaders: Dict[ContentType, IFileLoader] = {}
        self._register_loaders()
    
    def _register_loaders(self):
        """注册各种专用加载器"""
        # 文本文件加载器
        text_loader = TextFileLoader(max_file_size=self.max_file_size_mb * 1024 * 1024)
        for content_type in text_loader.supported_types():
            self._loaders[content_type] = text_loader
        
        # 这里可以注册更多专用加载器
        # PDF加载器、Word加载器等
        from .pdf_loader import PDFFileLoader
        pdf_loader = PDFFileLoader(max_file_size=self.max_file_size_mb * 1024 * 1024)
        self._loaders[ContentType.PDF] = pdf_loader
    
    @property
    def loader_name(self) -> str:
        """获取加载器名称"""
        return "MultiFormatFileLoader"
    
    @property
    def supported_types(self) -> List[ContentType]:
        """获取支持的内容类型"""
        return list(self._loaders.keys())
    
    def supports_content_type(self, content_type: ContentType) -> bool:
        """检查是否支持指定的内容类型"""
        return content_type in self._loaders
    
    async def validate_file(self, file_path: str) -> bool:
        """验证文件是否可以加载"""
        try:
            # 检测内容类型
            from ..models import detect_content_type
            content_type = detect_content_type(file_path)
            
            # 检查是否支持
            if not self.supports_content_type(content_type):
                return False
            
            # 使用对应的加载器验证
            loader = self._loaders[content_type]
            return await loader.validate_file(file_path)
            
        except Exception as e:
            logger.warning(f"文件验证失败 {file_path}: {e}")
            return False
    
    async def load_document(self, request: FileLoadRequest) -> Document:
        """加载文档"""
        try:
            # 确定内容类型
            content_type = request.content_type
            if content_type is None:
                from ..models import detect_content_type
                content_type = detect_content_type(request.file_path)
            
            # 如果content_type是字符串，转换为ContentType枚举
            if isinstance(content_type, str):
                try:
                    content_type = ContentType(content_type)
                except ValueError:
                    # 如果字符串不匹配任何枚举值，尝试转换为TEXT类型
                    content_type = ContentType.TXT
            
            # 检查是否支持
            if not self.supports_content_type(content_type):
                raise FileLoaderError(
                    f"不支持的文件格式: {content_type}",
                    file_path=request.file_path,
                    error_code="UNSUPPORTED_FORMAT"
                )
            
            # 使用对应的加载器
            loader = self._loaders[content_type]
            document = await loader.load_document(request)
            
            # 添加多格式加载器的元数据
            document.metadata.update({
                "multi_format_loader": True,
                "delegate_loader": loader.loader_name,
                "detected_type": content_type.value if hasattr(content_type, 'value') else str(content_type)
            })
            
            logger.info(f"使用 {loader.loader_name} 加载文档: {request.file_path}")
            return document
            
        except FileLoaderError:
            raise
        except Exception as e:
            logger.error(f"加载文档失败 {request.file_path}: {e}")
            raise FileLoaderError(
                f"加载文档失败: {str(e)}",
                file_path=request.file_path,
                error_code="LOAD_FAILED"
            )
    
    def get_loader_for_type(self, content_type: ContentType) -> Optional[IFileLoader]:
        """获取指定类型的加载器"""
        return self._loaders.get(content_type)
    
    def register_loader(self, content_type: ContentType, loader: IFileLoader):
        """注册新的加载器"""
        self._loaders[content_type] = loader
        logger.info(f"注册新加载器: {content_type} -> {loader.loader_name}")
    
    async def load_documents_batch(self, requests: List[FileLoadRequest]) -> List[Document]:
        """批量加载文档"""
        documents = []
        
        # 并发加载文档
        tasks = [self.load_document(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量加载失败 {requests[i].file_path}: {result}")
                # 可以选择跳过失败的文档或抛出异常
                continue
            else:
                documents.append(result)
        
        logger.info(f"批量加载完成: {len(documents)}/{len(requests)} 成功")
        return documents


# 便利函数
async def load_document_from_path(file_path: str, **kwargs) -> Document:
    """
    从文件路径加载文档的便利函数
    
    Args:
        file_path: 文件路径
        **kwargs: 其他参数
        
    Returns:
        Document: 加载的文档
    """
    # 构建元数据，包含所有额外参数
    metadata = kwargs.get('metadata', {})
    metadata.update({
        'encoding': kwargs.get('encoding', 'utf-8'),
        'max_file_size_mb': kwargs.get('max_file_size_mb', 100),
        'extract_metadata': kwargs.get('extract_metadata', True),
        'custom_params': kwargs.get('custom_params', {})
    })
    
    # 确定内容类型
    content_type = kwargs.get('content_type')
    logger.info(f"加载文档: {file_path}, 内容类型: {content_type}, 元数据: {metadata}")
    if content_type is None:
        # 根据文件扩展名推断内容类型
        import os
        ext = os.path.splitext(file_path)[1].lower()
        content_type_mapping = {
            '.pdf': 'pdf',
            '.txt': 'txt', 
            '.doc': 'doc',
            '.docx': 'docx',
            '.html': 'html',
            '.md': 'md',
            '.json': 'json',
            '.csv': 'csv',
        }
        content_type = content_type_mapping.get(ext, 'text')
    
    request = FileLoadRequest(
        file_path=file_path,
        content_type=content_type,
        metadata=metadata
    )
    
    loader = MultiFormatFileLoader(max_file_size_mb=metadata.get('max_file_size_mb', 100))
    return await loader.load_document(request)


async def load_documents_from_paths(file_paths: List[str], **kwargs) -> List[Document]:
    """
    从文件路径列表批量加载文档的便利函数
    
    Args:
        file_paths: 文件路径列表
        **kwargs: 其他参数
        
    Returns:
        List[Document]: 加载的文档列表
    """
    # 构建元数据，包含所有额外参数
    metadata = kwargs.get('metadata', {})
    metadata.update({
        'encoding': kwargs.get('encoding', 'utf-8'),
        'max_file_size_mb': kwargs.get('max_file_size_mb', 100),
        'extract_metadata': kwargs.get('extract_metadata', True),
        'custom_params': kwargs.get('custom_params', {})
    })
    
    # 确定内容类型映射
    import os
    content_type_mapping = {
        '.pdf': 'pdf',
        '.txt': 'txt', 
        '.doc': 'doc',
        '.docx': 'docx',
        '.html': 'html',
        '.md': 'md',
        '.json': 'json',
        '.csv': 'csv',
    }
    
    requests = []
    for path in file_paths:
        # 为每个文件确定内容类型
        content_type = kwargs.get('content_type')
        if content_type is None:
            ext = os.path.splitext(path)[1].lower()
            content_type = content_type_mapping.get(ext, 'text')
        
        requests.append(FileLoadRequest(
            file_path=path,
            content_type=content_type,
            metadata=metadata.copy()  # 为每个请求复制一份元数据
        ))
    
    loader = MultiFormatFileLoader(max_file_size_mb=metadata.get('max_file_size_mb', 100))
    return await loader.load_documents_batch(requests)