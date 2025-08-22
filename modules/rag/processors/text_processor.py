"""
文本处理器

专门处理文本文档的清理、标准化和预处理。
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from ...models import (
    ChunkingStrategy,
    Document,
    DocumentChunk,
    ProcessingRequest,
    ProcessingResult,
    ProcessingStatus,
)
from .base import DocumentProcessorError, IDocumentProcessor

logger = logging.getLogger(__name__)


class TextProcessor(IDocumentProcessor):
    """文本处理器实现"""

    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_control_chars: bool = True,
        min_chunk_size: int = 50,
    ):
        """
        初始化文本处理器

        Args:
            remove_extra_whitespace: 是否移除多余空白字符
            normalize_unicode: 是否标准化Unicode字符
            remove_control_chars: 是否移除控制字符
            min_chunk_size: 最小块大小
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_control_chars = remove_control_chars
        self.min_chunk_size = min_chunk_size

    @property
    def processor_name(self) -> str:
        """获取处理器名称"""
        return "TextProcessor"

    @property
    def supported_strategies(self) -> List[str]:
        """获取支持的处理策略"""
        return [
            ChunkingStrategy.FIXED_SIZE.value,
            ChunkingStrategy.PARAGRAPH.value,
            ChunkingStrategy.SENTENCE.value,
        ]

    async def validate_document(self, document: Document) -> bool:
        """验证文档是否可以处理"""
        try:
            # 检查文档是否为空
            if document.is_empty:
                return False

            # 检查内容长度
            if len(document.content) < self.min_chunk_size:
                return False

            # 检查是否是文本类型
            text_types = ["text/", "application/json", "application/csv"]
            return any(document.content_type.value.startswith(t) for t in text_types)

        except Exception as e:
            logger.warning(f"文档验证失败 {document.id}: {e}")
            return False

    async def clean_content(self, content: str) -> str:
        """清理文档内容"""
        try:
            cleaned = content

            # Unicode标准化
            if self.normalize_unicode:
                import unicodedata

                cleaned = unicodedata.normalize("NFKC", cleaned)

            # 移除控制字符
            if self.remove_control_chars:
                # 保留换行符和制表符，移除其他控制字符
                cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)

            # 处理空白字符
            if self.remove_extra_whitespace:
                # 移除行首行尾空白
                lines = [line.strip() for line in cleaned.split("\n")]
                # 移除空行（可选）
                lines = [line for line in lines if line]
                # 重新组合，使用单个换行符
                cleaned = "\n".join(lines)

                # 移除多余空格
                cleaned = re.sub(r" +", " ", cleaned)

            return cleaned.strip()

        except Exception as e:
            logger.error(f"内容清理失败: {e}")
            return content  # 返回原始内容

    async def create_chunks(self, document: Document, **kwargs) -> List[DocumentChunk]:
        """创建文档块"""
        try:
            strategy = kwargs.get("strategy", ChunkingStrategy.FIXED_SIZE)
            chunk_size = kwargs.get("chunk_size", 1000)
            overlap = kwargs.get("overlap", 200)

            # 清理内容
            content = await self.clean_content(document.content)

            chunks = []
            if strategy == ChunkingStrategy.FIXED_SIZE:
                chunks = await self._create_fixed_size_chunks(
                    document, content, chunk_size, overlap
                )
            elif strategy == ChunkingStrategy.PARAGRAPH:
                chunks = await self._create_paragraph_chunks(
                    document, content, chunk_size
                )
            elif strategy == ChunkingStrategy.SENTENCE:
                chunks = await self._create_sentence_chunks(
                    document, content, chunk_size
                )
            else:
                raise DocumentProcessorError(
                    f"不支持的分块策略: {strategy}",
                    document_id=document.id,
                    error_code="UNSUPPORTED_STRATEGY",
                )

            # 过滤太小的块
            valid_chunks = [
                chunk
                for chunk in chunks
                if len(chunk.content.strip()) >= self.min_chunk_size
            ]

            logger.info(f"文档 {document.id} 创建了 {len(valid_chunks)} 个块")
            return valid_chunks

        except DocumentProcessorError:
            raise
        except Exception as e:
            logger.error(f"创建文档块失败 {document.id}: {e}")
            raise DocumentProcessorError(
                f"创建文档块失败: {str(e)}",
                document_id=document.id,
                error_code="CHUNKING_FAILED",
            )

    async def process_document(self, request: ProcessingRequest) -> ProcessingResult:
        """处理文档"""
        start_time = asyncio.get_event_loop().time()
        document = request.document

        try:
            # 验证文档
            if not await self.validate_document(document):
                raise DocumentProcessorError(
                    f"文档验证失败: {document.id}",
                    document_id=document.id,
                    error_code="VALIDATION_FAILED",
                )

            # 创建文档块
            chunks = await self.create_chunks(
                document,
                strategy=request.chunking_strategy,
                chunk_size=request.chunk_size,
                overlap=request.chunk_overlap,
            )

            # 计算处理时间
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # 创建处理结果
            result = ProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.COMPLETED,
                chunks_created=len(chunks),
                chunks=chunks,
                processing_time_ms=processing_time,
                metadata={
                    "processor_name": self.processor_name,
                    "strategy": request.chunking_strategy.value,
                    "chunk_size": request.chunk_size,
                    "overlap": request.chunk_overlap,
                    "original_length": len(document.content),
                    "cleaned_length": len(chunks[0].content) if chunks else 0,
                },
            )

            logger.info(
                f"文档处理完成 {document.id}: {len(chunks)} 块, {processing_time:.2f}ms"
            )
            return result

        except DocumentProcessorError:
            raise
        except Exception as e:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"文档处理失败 {document.id}: {e}")

            return ProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.FAILED,
                chunks_created=0,
                chunks=[],
                processing_time_ms=processing_time,
                error_message=str(e),
                metadata={"processor_name": self.processor_name},
            )

    async def _create_fixed_size_chunks(
        self, document: Document, content: str, chunk_size: int, overlap: int
    ) -> List[DocumentChunk]:
        """创建固定大小的块"""
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(content):
            end = start + chunk_size
            chunk_content = content[start:end]

            # 尝试在单词边界分割
            if end < len(content) and not content[end].isspace():
                # 寻找最近的空格
                last_space = chunk_content.rfind(" ")
                if last_space > chunk_size * 0.8:  # 如果空格位置合理
                    chunk_content = chunk_content[:last_space]
                    end = start + last_space

            chunk = DocumentChunk(
                document_id=document.id,
                content=chunk_content.strip(),
                chunk_index=chunk_index,
                start_position=start,
                end_position=end,
                chunk_size=len(chunk_content),
                overlap_size=overlap if chunk_index > 0 else 0,
                strategy=ChunkingStrategy.FIXED_SIZE,
                metadata={"original_start": start, "original_end": end},
            )

            chunks.append(chunk)
            chunk_index += 1

            # 计算下一个起始位置（考虑重叠）
            start = max(start + chunk_size - overlap, end)

            # 避免无限循环
            if start >= len(content):
                break

        return chunks

    async def _create_paragraph_chunks(
        self, document: Document, content: str, max_size: int
    ) -> List[DocumentChunk]:
        """创建段落块"""
        chunks = []
        paragraphs = content.split("\n\n")

        current_chunk = ""
        chunk_index = 0
        start_position = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 如果当前块加上新段落仍在大小限制内
            if len(current_chunk + paragraph) <= max_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 保存当前块
                if current_chunk:
                    chunk = DocumentChunk(
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        start_position=start_position,
                        end_position=start_position + len(current_chunk),
                        strategy=ChunkingStrategy.PARAGRAPH,
                        metadata={"type": "paragraph_group"},
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    start_position += len(current_chunk) + 2  # +2 for \n\n

                # 开始新块
                current_chunk = paragraph

        # 处理最后一个块
        if current_chunk:
            chunk = DocumentChunk(
                document_id=document.id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_position=start_position,
                end_position=start_position + len(current_chunk),
                strategy=ChunkingStrategy.PARAGRAPH,
                metadata={"type": "paragraph_group"},
            )
            chunks.append(chunk)

        return chunks

    async def _create_sentence_chunks(
        self, document: Document, content: str, max_size: int
    ) -> List[DocumentChunk]:
        """创建句子块"""
        chunks = []

        # 简单的句子分割（可以改进为使用NLP库）
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]

        current_chunk = ""
        chunk_index = 0
        start_position = 0

        for sentence in sentences:
            # 如果当前块加上新句子仍在大小限制内
            if len(current_chunk + sentence) <= max_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                # 保存当前块
                if current_chunk:
                    chunk = DocumentChunk(
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        start_position=start_position,
                        end_position=start_position + len(current_chunk),
                        strategy=ChunkingStrategy.SENTENCE,
                        metadata={"type": "sentence_group"},
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    start_position += len(current_chunk) + 2

                # 开始新块
                current_chunk = sentence

        # 处理最后一个块
        if current_chunk:
            chunk = DocumentChunk(
                document_id=document.id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_position=start_position,
                end_position=start_position + len(current_chunk),
                strategy=ChunkingStrategy.SENTENCE,
                metadata={"type": "sentence_group"},
            )
            chunks.append(chunk)

        return chunks
