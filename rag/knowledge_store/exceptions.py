"""
知识存储异常类定义
"""


class KnowledgeStoreError(Exception):
    """知识存储基础异常类"""
    
    def __init__(self, message: str = "知识存储操作失败", details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class DocumentNotFoundError(KnowledgeStoreError):
    """文档未找到异常"""
    
    def __init__(self, document_id: str, details: str = None):
        message = f"文档未找到: {document_id}"
        super().__init__(message, details)
        self.document_id = document_id


class DocumentAlreadyExistsError(KnowledgeStoreError):
    """文档已存在异常"""
    
    def __init__(self, document_id: str, details: str = None):
        message = f"文档已存在: {document_id}"
        super().__init__(message, details)
        self.document_id = document_id


class InvalidDocumentError(KnowledgeStoreError):
    """无效文档异常"""
    
    def __init__(self, field: str = None, details: str = None):
        message = f"无效文档数据{f': {field}' if field else ''}"
        super().__init__(message, details)
        self.field = field


class StorageConnectionError(KnowledgeStoreError):
    """存储连接异常"""
    
    def __init__(self, storage_type: str, details: str = None):
        message = f"存储连接失败: {storage_type}"
        super().__init__(message, details)
        self.storage_type = storage_type


class StorageOperationError(KnowledgeStoreError):
    """存储操作异常"""
    
    def __init__(self, operation: str, details: str = None):
        message = f"存储操作失败: {operation}"
        super().__init__(message, details)
        self.operation = operation


class ConfigurationError(KnowledgeStoreError):
    """配置错误异常"""
    
    def __init__(self, config_key: str = None, details: str = None):
        message = f"配置错误{f': {config_key}' if config_key else ''}"
        super().__init__(message, details)
        self.config_key = config_key
