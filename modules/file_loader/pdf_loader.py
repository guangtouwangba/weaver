"""
PDF File Loader

Complete implementation for loading PDF files using pymupdf (fitz).
Supports text extraction, metadata extraction, and error handling.
"""

import uuid
import logging
from typing import List, AsyncIterator, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import asyncio

from .factory import register_file_loader

# PDF处理库
try:
    import fitz  # pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    fitz = None

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PyPDF2 = None

from .base import IFileLoader, FileLoaderError
from ..models import Document, create_document_from_path
from ..schemas.enums import ContentType

logger = logging.getLogger(__name__)


@register_file_loader(content_type=ContentType.PDF)
class PDFFileLoader(IFileLoader):
    """PDF file loader implementation."""

    def __init__(self, max_file_size: int = 100 * 1024 * 1024):
        """
        初始化PDF文件加载器
        
        Args:
            max_file_size: 最大文件大小（字节），默认100MB
        """
        self.max_file_size = max_file_size
        self._supported_formats = ['.pdf']
        
        # 检查可用的PDF处理库
        if not HAS_PYMUPDF and not HAS_PYPDF2:
            logger.warning("未安装PDF处理库。建议安装: pip install pymupdf 或 pip install PyPDF2")
        elif HAS_PYMUPDF:
            logger.info("PDFFileLoader 使用 pymupdf (fitz) 进行PDF处理")
        elif HAS_PYPDF2:
            logger.info("PDFFileLoader 使用 PyPDF2 进行PDF处理")

    @property
    def loader_name(self) -> str:
        """获取加载器名称"""
        return "PDFFileLoader"
    
    def supported_formats(self) -> List[str]:
        """获取支持的PDF格式"""
        return self._supported_formats.copy()

    def supports_content_type(self, content_type: ContentType) -> bool:
        """检查是否支持指定的内容类型"""
        return content_type == ContentType.PDF

    async def validate_file(self, file_path: str) -> bool:
        """验证PDF文件是否可以加载"""
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                logger.error(f"PDF文件不存在: {file_path}")
                return False
            
            # 检查文件大小
            if path.stat().st_size > self.max_file_size:
                logger.error(f"PDF文件过大: {path.stat().st_size} bytes > {self.max_file_size} bytes")
                return False
            
            # 检查文件扩展名
            if path.suffix.lower() not in self._supported_formats:
                logger.error(f"不支持的文件格式: {path.suffix}")
                return False
            
            # 尝试打开PDF文件验证格式
            if HAS_PYMUPDF:
                try:
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                    logger.debug(f"PDF验证成功: {file_path} ({page_count} 页)")
                    return True
                except Exception as e:
                    logger.error(f"PDF格式验证失败 (pymupdf): {e}")
                    return False
            elif HAS_PYPDF2:
                try:
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        page_count = len(pdf_reader.pages)
                        logger.debug(f"PDF验证成功: {file_path} ({page_count} 页)")
                        return True
                except Exception as e:
                    logger.error(f"PDF格式验证失败 (PyPDF2): {e}")
                    return False
            else:
                logger.warning("没有可用的PDF处理库，跳过PDF格式验证")
                return True
                
        except Exception as e:
            logger.error(f"PDF文件验证失败: {e}")
            return False
    
    async def load_document(self, request) -> Document:
        """加载PDF文档"""
        from ..models import FileLoadRequest
        
        # 处理不同类型的输入参数
        if isinstance(request, str):
            file_path = request
            metadata = {}
        elif isinstance(request, FileLoadRequest):
            file_path = request.file_path
            metadata = request.metadata or {}
        else:
            file_path = request
            metadata = {}
        
        # 验证文件
        if not await self.validate_file(file_path):
            raise FileLoaderError(f"PDF文件验证失败: {file_path}")
        
        try:
            path = Path(file_path)
            
            # 提取PDF内容
            content = await self._extract_pdf_content(path)
            
            # 提取PDF元数据
            pdf_metadata = await self._extract_pdf_metadata(path)
            
            # 创建文档对象
            document = create_document_from_path(file_path, content)
            
            # 更新元数据
            document.metadata.update({
                'loader': self.loader_name,
                'file_size': path.stat().st_size,
                'extraction_method': 'pymupdf' if HAS_PYMUPDF else ('PyPDF2' if HAS_PYPDF2 else 'placeholder'),
                **pdf_metadata,
                **(metadata or {})
            })
            
            logger.info(f"成功加载PDF文档: {file_path} (页数: {pdf_metadata.get('pdf_pages', 'unknown')}, 字符数: {len(content)})")
            return document
            
        except FileLoaderError:
            raise
        except Exception as e:
            logger.error(f"加载PDF文档失败 {file_path}: {e}")
            raise FileLoaderError(f"加载PDF文档失败: {str(e)}")
    
    async def load_documents_batch(self, requests: List) -> List[Document]:
        """批量加载PDF文档"""
        documents = []
        
        for request in requests:
            try:
                document = await self.load_document(request)
                documents.append(document)
                
            except FileLoaderError as e:
                logger.error(f"批量加载PDF失败: {e}")
                # 继续处理其他文档，不中断整个批次
                continue
        
        logger.info(f"PDF批量加载完成: {len(documents)}/{len(requests)} 成功")
        return documents
    
    async def _extract_pdf_content(self, path: Path) -> str:
        """
        从PDF文件提取文本内容
        
        优先使用pymupdf (fitz)，回退到PyPDF2
        """
        if HAS_PYMUPDF:
            return await self._extract_content_with_pymupdf(path)
        elif HAS_PYPDF2:
            return await self._extract_content_with_pypdf2(path)
        else:
            logger.warning("未安装PDF处理库，返回占位符内容")
            return f"[PDF内容占位符: {path.name}]\n\n此PDF文件需要安装PDF处理库才能提取内容。请安装: pip install pymupdf 或 pip install PyPDF2"
    
    async def _extract_content_with_pymupdf(self, path: Path) -> str:
        """使用pymupdf (fitz)提取PDF内容"""
        try:
            # 在异步函数中运行CPU密集型任务
            def extract_text():
                doc = fitz.open(str(path))
                text_parts = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():  # 只添加非空页面
                        text_parts.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
                
                doc.close()
                return "\n\n".join(text_parts)
            
            # 使用线程池执行器来避免阻塞事件循环
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, extract_text)
            
            if not content.strip():
                logger.warning(f"PDF文件似乎没有可提取的文本内容: {path}")
                return f"[PDF文件 {path.name} 没有可提取的文本内容]"
            
            return content
            
        except Exception as e:
            logger.error(f"使用pymupdf提取PDF内容失败: {e}")
            raise FileLoaderError(f"PDF内容提取失败: {e}")
    
    async def _extract_content_with_pypdf2(self, path: Path) -> str:
        """使用PyPDF2提取PDF内容"""
        try:
            def extract_text():
                text_parts = []
                with open(path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text.strip():  # 只添加非空页面
                            text_parts.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
                
                return "\n\n".join(text_parts)
            
            # 使用线程池执行器来避免阻塞事件循环
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, extract_text)
            
            if not content.strip():
                logger.warning(f"PDF文件似乎没有可提取的文本内容: {path}")
                return f"[PDF文件 {path.name} 没有可提取的文本内容]"
            
            return content
            
        except Exception as e:
            logger.error(f"使用PyPDF2提取PDF内容失败: {e}")
            raise FileLoaderError(f"PDF内容提取失败: {e}")
    
    async def _extract_pdf_metadata(self, path: Path) -> Dict[str, Any]:
        """
        提取PDF元数据
        
        优先使用pymupdf (fitz)，回退到PyPDF2
        """
        if HAS_PYMUPDF:
            return await self._extract_metadata_with_pymupdf(path)
        elif HAS_PYPDF2:
            return await self._extract_metadata_with_pypdf2(path)
        else:
            # 基础元数据
            return {
                'pdf_pages': 'unknown',
                'pdf_author': 'unknown',
                'pdf_title': path.stem,
                'pdf_subject': 'unknown',
                'pdf_creator': 'unknown',
                'pdf_producer': 'unknown',
                'extraction_method': 'no_library'
            }
    
    async def _extract_metadata_with_pymupdf(self, path: Path) -> Dict[str, Any]:
        """使用pymupdf (fitz)提取PDF元数据"""
        try:
            def extract_metadata():
                doc = fitz.open(str(path))
                metadata = doc.metadata
                page_count = len(doc)
                doc.close()
                
                return {
                    'pdf_pages': page_count,
                    'pdf_title': metadata.get('title', path.stem),
                    'pdf_author': metadata.get('author', 'unknown'),
                    'pdf_subject': metadata.get('subject', 'unknown'),
                    'pdf_creator': metadata.get('creator', 'unknown'),
                    'pdf_producer': metadata.get('producer', 'unknown'),
                    'pdf_creation_date': metadata.get('creationDate', 'unknown'),
                    'pdf_modification_date': metadata.get('modDate', 'unknown'),
                    'extraction_method': 'pymupdf'
                }
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_metadata)
            
        except Exception as e:
            logger.error(f"使用pymupdf提取PDF元数据失败: {e}")
            return {
                'pdf_pages': 'error',
                'pdf_author': 'error',
                'pdf_title': path.stem,
                'extraction_method': 'pymupdf_error',
                'error': str(e)
            }
    
    async def _extract_metadata_with_pypdf2(self, path: Path) -> Dict[str, Any]:
        """使用PyPDF2提取PDF元数据"""
        try:
            def extract_metadata():
                with open(path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata = pdf_reader.metadata
                    page_count = len(pdf_reader.pages)
                    
                    return {
                        'pdf_pages': page_count,
                        'pdf_title': str(metadata.get('/Title', path.stem)) if metadata else path.stem,
                        'pdf_author': str(metadata.get('/Author', 'unknown')) if metadata else 'unknown',
                        'pdf_subject': str(metadata.get('/Subject', 'unknown')) if metadata else 'unknown',
                        'pdf_creator': str(metadata.get('/Creator', 'unknown')) if metadata else 'unknown',
                        'pdf_producer': str(metadata.get('/Producer', 'unknown')) if metadata else 'unknown',
                        'pdf_creation_date': str(metadata.get('/CreationDate', 'unknown')) if metadata else 'unknown',
                        'pdf_modification_date': str(metadata.get('/ModDate', 'unknown')) if metadata else 'unknown',
                        'extraction_method': 'PyPDF2'
                    }
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_metadata)
            
        except Exception as e:
            logger.error(f"使用PyPDF2提取PDF元数据失败: {e}")
        return {
                'pdf_pages': 'error',
                'pdf_author': 'error',
                'pdf_title': path.stem,
                'extraction_method': 'PyPDF2_error',
                'error': str(e)
        }

