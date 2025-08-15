"""
向量存储异常类定义
"""


class VectorStoreError(Exception):
    """向量存储错误"""
    pass


class EmbeddingDimensionError(VectorStoreError):
    """嵌入维度错误"""
    pass