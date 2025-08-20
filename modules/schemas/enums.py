"""
枚举定义

集中定义所有系统中使用的枚举类型。
"""

from enum import Enum

class FileStatus(str, Enum):
    """文件状态枚举"""
    PENDING = "pending"           # 待处理
    UPLOADING = "uploading"       # 上传中
    UPLOADED = "uploaded"         # 已上传
    PROCESSING = "processing"     # 处理中
    PROCESSED = "processed"       # 已处理
    FAILED = "failed"            # 处理失败
    DELETED = "deleted"          # 已删除

class TopicStatus(str, Enum):
    """主题状态枚举"""
    ACTIVE = "active"            # 活跃
    INACTIVE = "inactive"        # 非活跃
    ARCHIVED = "archived"        # 已归档
    DELETED = "deleted"          # 已删除

class ContentType(str, Enum):
    """内容类型枚举"""
    TEXT = "text"
    TXT = "txt"
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    HTML = "html"
    MD = "md"
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    RTF = "rtf"

class ChunkingStrategy(str, Enum):
    """分块策略枚举"""
    FIXED_SIZE = "fixed_size"         # 固定大小
    SENTENCE = "sentence"             # 按句子
    PARAGRAPH = "paragraph"           # 按段落
    SEMANTIC = "semantic"             # 语义分块
    RECURSIVE = "recursive"           # 递归分块

class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SearchType(str, Enum):
    """搜索类型枚举"""
    SEMANTIC = "semantic"            # 语义搜索
    KEYWORD = "keyword"              # 关键词搜索
    HYBRID = "hybrid"                # 混合搜索
    EXACT = "exact"                  # 精确搜索
