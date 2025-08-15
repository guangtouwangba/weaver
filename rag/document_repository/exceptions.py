"""
文档仓储异常类定义
"""


class DocumentRepositoryError(Exception):
    """文档仓储错误"""
    pass


class DocumentNotFoundError(DocumentRepositoryError):
    """文档未找到错误"""
    def __init__(self, document_id: str):
        super().__init__(f"Document not found: {document_id}")
        self.document_id = document_id