"""
文档API层

使用DocumentService进行业务逻辑编排的API接口。
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services import DocumentService
from ..schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentList,
    ProcessingRequest, ProcessingResult, SearchRequest, SearchResponse,
    APIResponse
)

router = APIRouter(prefix="/documents", tags=["documents"])

# 依赖注入
async def get_document_service(session: AsyncSession = Depends(get_db_session)) -> DocumentService:
    """获取文档服务实例"""
    return DocumentService(session)

@router.post("/", response_model=APIResponse, summary="创建文档记录")
async def create_document(
    document_data: DocumentCreate,
    service: DocumentService = Depends(get_document_service)
):
    """
    # 创建新的文档记录
    
    在系统中创建一个新的文档记录，用于跟踪和管理处理后的文档内容。
    
    ## 请求参数
    - **title**: 文档标题（必填）
    - **content**: 文档内容（可选，可以为空）
    - **content_type**: 内容类型（text/plain, text/markdown等）
    - **file_id**: 关联的文件ID（可选）
    - **metadata**: 扩展元数据（可选）
    
    ## 使用场景
    - 手动创建文档记录
    - 从外部系统导入文档
    - 创建虚拟文档（不对应实际文件）
    
    ## 注意事项
    - 此接口不会自动处理文档内容
    - 需要手动调用处理接口进行分块和向量化
    - 对于上传的文件，通常由系统自动创建文档记录
    """
    try:
        async with service:
            document = await service.create_document(document_data)
            
            return APIResponse(
                success=True,
                message="文档创建成功",
                data=document
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建文档失败: {str(e)}")

@router.get("/{document_id}", response_model=APIResponse)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """获取文档详情"""
    try:
        async with service:
            document = await service.get_document(document_id)
            if not document:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            return APIResponse(
                success=True,
                data=document
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")

@router.put("/{document_id}", response_model=APIResponse)
async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    service: DocumentService = Depends(get_document_service)
):
    """更新文档"""
    try:
        async with service:
            document = await service.update_document(document_id, document_data)
            if not document:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            return APIResponse(
                success=True,
                message="文档更新成功",
                data=document
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文档失败: {str(e)}")

@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """删除文档"""
    try:
        async with service:
            success = await service.delete_document(document_id)
            if not success:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            return APIResponse(
                success=True,
                message="文档删除成功"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

@router.get("/", response_model=APIResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    content_type: Optional[str] = Query(None, description="内容类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    file_id: Optional[str] = Query(None, description="文件ID过滤"),
    service: DocumentService = Depends(get_document_service)
):
    """获取文档列表"""
    try:
        async with service:
            document_list = await service.list_documents(
                page=page,
                page_size=page_size,
                content_type=content_type,
                status=status,
                file_id=file_id
            )
            
            return APIResponse(
                success=True,
                data=document_list
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@router.post("/{document_id}/process", response_model=APIResponse, summary="处理文档（分块和向量化）")
async def process_document(
    document_id: str,
    processing_request: ProcessingRequest,
    service: DocumentService = Depends(get_document_service)
):
    """
    # 文档处理：分块、向量化和索引
    
    对指定文档执行完整的RAG处理流程，包括文本分块、生成嵌入向量和建立搜索索引。
    
    ## 路径参数
    - **document_id**: 要处理的文档ID（必填）
    
    ## 请求参数
    - **chunking_strategy**: 分块策略（可选）:
      - `fixed_size`: 固定大小分块（默认）
      - `semantic`: 语义分块
      - `paragraph`: 段落分块
      - `sentence`: 句子分块
    - **chunk_size**: 分块大小（默认500字符）
    - **chunk_overlap**: 分块重叠大小（默认50字符）
    - **embedding_model**: 嵌入模型（可选）
    - **index_immediately**: 是否立即索引（默认true）
    
    ## 处理流程
    
    ### 1️⃣ 预处理阶段
    - 检查文档状态和权限
    - 验证处理参数
    - 准备处理环境
    
    ### 2️⃣ 文本分块阶段
    - 根据选定策略分割文本
    - 保持上下文连续性
    - 生成块元数据
    
    ### 3️⃣ 向量化阶段
    - 使用预训练模型生成嵌入向量
    - 支持多种嵌入模型
    - 批量处理提高效率
    
    ### 4️⃣ 索引存储阶段
    - 存储向量到向量数据库
    - 建立关键词索引
    - 更新文档状态
    
    ## 分块策略说明
    
    ### 📏 固定大小 (Fixed Size)
    - 按字符数分割文本
    - 简单快速，适合大部分文档
    - 可能会打断句子和段落
    
    ### 🤖 语义分块 (Semantic)
    - 基于语义相似性分割
    - 保持语义完整性
    - 适合复杂文档结构
    
    ### 📋 段落分块 (Paragraph)
    - 按段落边界分割
    - 保持内容逻辑完整
    - 适合结构化文档
    
    ### ⚙️ 句子分块 (Sentence)
    - 按句子边界分割
    - 精细粒度分割
    - 适合短文本和问答
    
    ## 返回结果
    - **document_id**: 文档ID
    - **status**: 处理状态 (completed/failed)
    - **chunks_created**: 创建的文档块数量
    - **processing_time**: 处理耗时（秒）
    - **metadata**: 处理统计信息
    - **error_message**: 错误信息（如果失败）
    
    ## 性能考虑
    - 大文档处理可能需要较长时间
    - 建议使用异步处理模式
    - 可通过WebSocket获取实时进度
    
    ## 错误状态
    - **400**: 请求参数错误或文档已处理
    - **404**: 文档不存在
    - **409**: 文档正在处理中
    - **500**: 处理过程中出现错误
    """
    try:
        # 确保document_id一致
        processing_request.document_id = document_id
        
        async with service:
            result = await service.process_document(processing_request)
            
            return APIResponse(
                success=True,
                message="文档处理完成",
                data=result
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文档失败: {str(e)}")

@router.post("/search", response_model=APIResponse, summary="智能文档搜索")
async def search_documents(
    search_request: SearchRequest,
    service: DocumentService = Depends(get_document_service)
):
    """
    # 智能文档搜索（RAG检索增强生成）
    
    使用先进的向量搜索和关键词搜索结合，在文档库中查找与查询相关的内容。
    
    ## 请求参数
    - **query**: 搜索查询语句（必填，支持中英文）
    - **search_type**: 搜索类型（可选）:
      - `semantic`: 语义搜索（默认）
      - `keyword`: 关键词搜索
      - `hybrid`: 混合搜索
    - **limit**: 返回结果数量（默认为10）
    - **threshold**: 相关性阈值（0.0-1.0，默认0.5）
    - **filters**: 过滤条件（可选）:
      - `topic_ids`: 按主题ID过滤
      - `file_ids`: 按文件ID过滤
      - `content_types`: 按内容类型过滤
      - `date_range`: 按时间范围过滤
    
    ## 搜索类型说明
    
    ### 🎯 语义搜索 (Semantic)
    - 使用向量嵌入进行相似度匹配
    - 理解查询的语义含义
    - 适合概念性和上下文搜索
    - 支持同义词和近义词匹配
    
    ### 🔍 关键词搜索 (Keyword)  
    - 基于关键词匹配和TF-IDF
    - 精确匹配特定词汇
    - 适合搜索具体名词、数字、代码
    - 支持布尔搜索和通配符
    
    ### ⚖️ 混合搜索 (Hybrid)
    - 结合语义和关键词搜索优势
    - 自动平衡两种算法的结果
    - 提供最优的搜索体验
    - 适合大部分使用场景
    
    ## 返回结果
    - **query**: 原始搜索查询
    - **results**: 搜索结果列表，每个包含:
      - `document_id`: 文档ID
      - `chunk_id`: 文档块ID（如果适用）
      - `title`: 文档标题
      - `content`: 匹配的内容片段
      - `score`: 相关性得分 (0.0-1.0)
      - `metadata`: 文档元数据
    - **total_results**: 符合条件的总结果数
    - **search_time**: 搜索耗时（秒）
    - **search_type**: 实际使用的搜索类型
    
    ## 搜索技巧
    
    ### 高质量查询
    - 使用完整的句子而非单个词汇
    - 包含上下文信息会提高准确性
    - 使用自然语言描述需求
    
    ### 示例查询
    ```
    "机器学习中的决策树算法原理"
    "Python中如何实现数据库连接池"
    "深度学习模型的过拟合问题及解决方案"
    ```
    
    ## 性能优化
    - 系统会缓存常用查询结果
    - 向量搜索索引已经优化
    - 支持并发搜索请求
    
    ## 限制说明
    - 单次查询最多返回100个结果
    - 搜索请求超时时间为30秒
    - 频繁搜索可能被限流
    """
    try:
        async with service:
            search_response = await service.search_documents(search_request)
            
            return APIResponse(
                success=True,
                data=search_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索文档失败: {str(e)}")

@router.get("/files/{file_id}/documents", response_model=APIResponse)
async def get_file_documents(
    file_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """获取文件的文档列表"""
    try:
        async with service:
            documents = await service.get_file_documents(file_id)
            
            return APIResponse(
                success=True,
                data=documents
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件文档失败: {str(e)}")

@router.get("/{document_id}/chunks", response_model=APIResponse)
async def get_document_chunks(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """获取文档的所有块"""
    try:
        async with service:
            chunks = await service.get_document_chunks(document_id)
            
            return APIResponse(
                success=True,
                data=chunks
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档块失败: {str(e)}")
