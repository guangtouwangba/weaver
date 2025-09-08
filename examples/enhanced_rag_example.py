"""
增强RAG系统使用示例

展示如何使用新的模块化RAG架构来构建和使用不同类型的RAG管道。
"""

import asyncio
import logging
import os
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入RAG组件
from modules.rag.factory import RAGPipelineFactory, get_default_config, create_rag_pipeline_from_config
from modules.rag.base import RAGStrategy
from modules.vector_store.weaviate_service import WeaviateVectorStore
from modules.embedding.openai_service import OpenAIEmbeddingService


async def create_services():
    """创建基础服务"""
    # 创建向量存储服务
    vector_store = WeaviateVectorStore(
        url="http://localhost:8080",
        create_collections_on_init=True
    )
    
    # 创建嵌入服务
    embedding_service = OpenAIEmbeddingService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-small"
    )
    
    # 初始化服务
    await vector_store.initialize()
    await embedding_service.initialize()
    
    return vector_store, embedding_service


async def example_simple_rag():
    """简单RAG示例"""
    logger.info("=== 简单RAG示例 ===")
    
    # 创建基础服务
    vector_store, embedding_service = await create_services()
    
    try:
        # 创建简单RAG管道
        config = get_default_config("simple_rag")
        pipeline = await RAGPipelineFactory.create_simple_rag_pipeline(
            vector_store, embedding_service, config
        )
        
        # 初始化管道
        await pipeline.initialize()
        
        # 测试查询
        query = "什么是机器学习？"
        response = await pipeline.process(query)
        
        logger.info(f"查询: {query}")
        logger.info(f"回答: {response.answer}")
        logger.info(f"置信度: {response.confidence:.3f}")
        logger.info(f"检索到的文档数: {len(response.retrieved_documents)}")
        logger.info(f"处理时间: {response.processing_time_ms:.1f}ms")
        
        # 健康检查
        health = await pipeline.health_check()
        logger.info(f"管道健康状态: {health}")
        
    finally:
        # 清理资源
        await pipeline.cleanup()
        await vector_store.cleanup()
        await embedding_service.cleanup()


async def example_hybrid_rag():
    """混合RAG示例（向量+BM25）"""
    logger.info("=== 混合RAG示例 ===")
    
    # 创建基础服务
    vector_store, embedding_service = await create_services()
    
    try:
        # 创建混合RAG管道
        config = get_default_config("hybrid_rag")
        pipeline = await RAGPipelineFactory.create_hybrid_rag_pipeline(
            vector_store, embedding_service, None, config
        )
        
        # 初始化管道
        await pipeline.initialize()
        
        # 测试查询
        query = "深度学习和机器学习有什么区别？"
        response = await pipeline.process(
            query,
            user_context={
                "top_k": 15,
                "rerank_top_k": 10,
                "score_threshold": 0.1
            }
        )
        
        logger.info(f"查询: {query}")
        logger.info(f"回答: {response.answer}")
        logger.info(f"置信度: {response.confidence:.3f}")
        logger.info(f"检索到的文档数: {len(response.retrieved_documents)}")
        logger.info(f"处理时间: {response.processing_time_ms:.1f}ms")
        
        # 显示检索结果详情
        for i, doc in enumerate(response.retrieved_documents[:3]):
            logger.info(f"文档 {i+1}: 分数={doc.score:.3f}, 来源={doc.source}")
            logger.info(f"  内容预览: {doc.content[:100]}...")
        
    finally:
        # 清理资源
        await pipeline.cleanup()
        await vector_store.cleanup()
        await embedding_service.cleanup()


async def example_adaptive_rag():
    """自适应RAG示例"""
    logger.info("=== 自适应RAG示例 ===")
    
    # 创建基础服务
    vector_store, embedding_service = await create_services()
    
    try:
        # 创建自适应RAG管道
        config = get_default_config("adaptive_rag")
        pipeline = await RAGPipelineFactory.create_adaptive_rag_pipeline(
            vector_store, embedding_service, None, config
        )
        
        # 初始化管道
        await pipeline.initialize()
        
        # 测试不同复杂度的查询
        queries = [
            "什么是Python？",  # 简单查询
            "比较Python和Java的优缺点",  # 比较性查询
            "为什么深度学习在图像识别中表现出色？",  # 分析性查询
        ]
        
        for query in queries:
            logger.info(f"\n--- 处理查询: {query} ---")
            
            response = await pipeline.process(query)
            
            logger.info(f"回答: {response.answer[:200]}...")
            logger.info(f"置信度: {response.confidence:.3f}")
            logger.info(f"检索策略: {response.metadata.get('strategy', 'unknown')}")
            logger.info(f"处理时间: {response.processing_time_ms:.1f}ms")
            
            # 显示查询分析结果
            if "processing_metadata" in response.metadata:
                metadata = response.metadata["processing_metadata"]
                if "query_processor" in metadata:
                    qp_info = metadata["query_processor"]
                    logger.info(f"查询复杂度: {qp_info.get('complexity', 'unknown')}")
                    logger.info(f"查询意图: {qp_info.get('intent', 'unknown')}")
        
    finally:
        # 清理资源
        await pipeline.cleanup()
        await vector_store.cleanup()
        await embedding_service.cleanup()


async def example_multi_hop_rag():
    """多跳RAG示例"""
    logger.info("=== 多跳RAG示例 ===")
    
    # 创建基础服务
    vector_store, embedding_service = await create_services()
    
    try:
        # 创建多跳RAG管道
        pipeline = await RAGPipelineFactory.create_multi_hop_rag_pipeline(
            vector_store, embedding_service
        )
        
        # 初始化管道
        await pipeline.initialize()
        
        # 测试需要多跳推理的查询
        query = "机器学习中的监督学习和无监督学习有什么区别，各自适用于什么场景？"
        
        response = await pipeline.process(
            query,
            max_hops=3,
            user_context={"top_k": 10}
        )
        
        logger.info(f"查询: {query}")
        logger.info(f"回答: {response.answer}")
        logger.info(f"置信度: {response.confidence:.3f}")
        logger.info(f"处理时间: {response.processing_time_ms:.1f}ms")
        
        # 显示多跳信息
        if "hop_history" in response.metadata:
            hop_history = response.metadata["hop_history"]
            logger.info(f"执行了 {len(hop_history)} 跳检索:")
            for hop in hop_history:
                logger.info(f"  第{hop['hop']}跳: 查询='{hop['query'][:50]}...', "
                           f"找到{hop['documents_found']}个文档")
        
    finally:
        # 清理资源
        await pipeline.cleanup()
        await vector_store.cleanup()
        await embedding_service.cleanup()


async def example_custom_pipeline():
    """自定义管道示例"""
    logger.info("=== 自定义管道示例 ===")
    
    # 创建基础服务
    vector_store, embedding_service = await create_services()
    
    try:
        # 使用配置文件创建管道
        custom_config = {
            "query_processor": {
                "use_ai_analysis": False,  # 使用基础查询处理
                "enable_query_expansion": True
            },
            "vector_retriever": {
                "default_top_k": 20,
                "collection_name": "documents"
            },
            "generator": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 800,
                "temperature": 0.5,
                "system_prompt": "你是一个专业的技术文档助手，请用简洁明了的语言回答问题。"
            }
        }
        
        pipeline = await create_rag_pipeline_from_config(
            "simple",
            vector_store,
            embedding_service,
            config=custom_config
        )
        
        # 初始化管道
        await pipeline.initialize()
        
        # 测试查询
        query = "如何优化数据库查询性能？"
        response = await pipeline.process(query)
        
        logger.info(f"查询: {query}")
        logger.info(f"回答: {response.answer}")
        logger.info(f"置信度: {response.confidence:.3f}")
        
        # 获取性能指标
        metrics = await pipeline.get_metrics()
        logger.info(f"性能指标:")
        logger.info(f"  总处理时间: {metrics.total_processing_time_ms:.1f}ms")
        logger.info(f"  查询处理时间: {metrics.query_processing_time_ms:.1f}ms")
        logger.info(f"  检索时间: {metrics.retrieval_time_ms:.1f}ms")
        logger.info(f"  生成时间: {metrics.generation_time_ms:.1f}ms")
        
    finally:
        # 清理资源
        await pipeline.cleanup()
        await vector_store.cleanup()
        await embedding_service.cleanup()


async def example_streaming_response():
    """流式响应示例"""
    logger.info("=== 流式响应示例 ===")
    
    # 创建基础服务
    vector_store, embedding_service = await create_services()
    
    try:
        # 创建带流式生成器的管道
        from modules.rag.pipeline import RAGPipelineBuilder
        from modules.rag.query_processor import BasicQueryProcessor
        from modules.rag.retrievers import VectorRetriever
        from modules.rag.generators import StreamingResponseGenerator
        
        # 手动构建管道
        query_processor = BasicQueryProcessor()
        retriever = VectorRetriever(vector_store, embedding_service)
        generator = StreamingResponseGenerator({
            "model": "gpt-3.5-turbo",
            "enable_streaming": True
        })
        
        pipeline = await (RAGPipelineBuilder()
                         .set_strategy(RAGStrategy.SIMPLE)
                         .set_name("streaming_rag")
                         .add_query_processor(query_processor)
                         .add_retriever(retriever)
                         .add_generator(generator)
                         .build())
        
        # 初始化管道
        await pipeline.initialize()
        
        # 测试流式响应
        query = "解释一下什么是RESTful API的设计原则"
        
        logger.info(f"查询: {query}")
        logger.info("流式回答:")
        
        # 这里演示如何获取流式响应（需要修改管道支持）
        response = await pipeline.process(query)
        logger.info(response.answer)
        
    finally:
        # 清理资源
        await pipeline.cleanup()
        await vector_store.cleanup()
        await embedding_service.cleanup()


async def main():
    """主函数 - 运行所有示例"""
    try:
        # 检查环境变量
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("请设置 OPENAI_API_KEY 环境变量")
            return
        
        # 运行示例
        await example_simple_rag()
        await asyncio.sleep(1)
        
        await example_hybrid_rag()
        await asyncio.sleep(1)
        
        await example_adaptive_rag()
        await asyncio.sleep(1)
        
        await example_multi_hop_rag()
        await asyncio.sleep(1)
        
        await example_custom_pipeline()
        await asyncio.sleep(1)
        
        await example_streaming_response()
        
        logger.info("所有示例运行完成！")
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
