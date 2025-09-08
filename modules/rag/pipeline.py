"""
模块化RAG管道实现

提供灵活的RAG管道架构，支持组件的动态组合和工作流编排。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Type
from datetime import datetime, timezone

from modules.rag.base import (
    IRAGPipeline,
    IRAGComponent,
    RAGComponentType,
    RAGContext,
    RAGResponse,
    RAGStrategy,
    RAGMetrics,
    RAGPipelineError,
    RetrievedDocument,
)

logger = logging.getLogger(__name__)


class ModularRAGPipeline(IRAGPipeline):
    """模块化RAG管道"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.components: Dict[RAGComponentType, IRAGComponent] = {}
        self.pipeline_name = self.config.get("pipeline_name", "default")
        self.strategy = RAGStrategy(self.config.get("strategy", "simple"))
        
        # 性能监控
        self.metrics = RAGMetrics()
        self._initialized = False
        
        logger.info(f"ModularRAGPipeline 创建: {self.pipeline_name}, 策略: {self.strategy.value}")
    
    async def initialize(self) -> None:
        """初始化管道"""
        if self._initialized:
            return
        
        try:
            # 初始化所有组件
            for component_type, component in self.components.items():
                if not component.is_initialized:
                    await component.initialize()
                    logger.info(f"组件初始化完成: {component_type.value}")
            
            self._initialized = True
            logger.info(f"RAG管道初始化完成: {self.pipeline_name}")
            
        except Exception as e:
            logger.error(f"RAG管道初始化失败: {e}")
            raise RAGPipelineError(f"管道初始化失败: {e}")
    
    async def add_component(self, component: IRAGComponent) -> None:
        """添加组件"""
        component_type = component.component_type
        
        if component_type in self.components:
            logger.warning(f"替换现有组件: {component_type.value}")
        
        self.components[component_type] = component
        logger.info(f"添加组件: {component_type.value} -> {component.component_name}")
    
    async def remove_component(self, component_type: RAGComponentType) -> None:
        """移除组件"""
        if component_type in self.components:
            component = self.components.pop(component_type)
            await component.cleanup()
            logger.info(f"移除组件: {component_type.value}")
        else:
            logger.warning(f"组件不存在: {component_type.value}")
    
    async def process(self, query: str, **kwargs) -> RAGResponse:
        """处理RAG请求"""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # 创建RAG上下文
            context = RAGContext(
                query=query,
                user_context=kwargs.get("user_context", {}),
                conversation_history=kwargs.get("conversation_history", [])
            )
            
            # 根据策略选择处理流程
            if self.strategy == RAGStrategy.SIMPLE:
                response = await self._process_simple_rag(context, **kwargs)
            elif self.strategy == RAGStrategy.MULTI_HOP:
                response = await self._process_multi_hop_rag(context, **kwargs)
            elif self.strategy == RAGStrategy.ADAPTIVE:
                response = await self._process_adaptive_rag(context, **kwargs)
            else:
                response = await self._process_simple_rag(context, **kwargs)
            
            # 计算总处理时间
            total_time = (time.time() - start_time) * 1000
            response.processing_time_ms = total_time
            self.metrics.total_processing_time_ms = total_time
            
            logger.info(f"RAG处理完成: 查询='{query[:50]}...', "
                       f"耗时={total_time:.1f}ms, 策略={self.strategy.value}")
            
            return response
            
        except Exception as e:
            logger.error(f"RAG处理失败: {e}")
            raise RAGPipelineError(f"RAG处理失败: {e}")
    
    async def _process_simple_rag(self, context: RAGContext, **kwargs) -> RAGResponse:
        """处理简单RAG流程"""
        try:
            # 1. 查询处理
            if RAGComponentType.QUERY_PROCESSOR in self.components:
                query_start = time.time()
                context = await self.components[RAGComponentType.QUERY_PROCESSOR].process(context)
                self.metrics.query_processing_time_ms = (time.time() - query_start) * 1000
            
            # 2. 文档检索
            if RAGComponentType.RETRIEVER in self.components:
                retrieval_start = time.time()
                context = await self.components[RAGComponentType.RETRIEVER].process(context)
                self.metrics.retrieval_time_ms = (time.time() - retrieval_start) * 1000
            
            # 3. 重排序（可选）
            if RAGComponentType.RERANKER in self.components:
                rerank_start = time.time()
                context = await self.components[RAGComponentType.RERANKER].process(context)
                self.metrics.reranking_time_ms = (time.time() - rerank_start) * 1000
            
            # 4. 上下文压缩（可选）
            if RAGComponentType.CONTEXT_COMPRESSOR in self.components:
                context = await self.components[RAGComponentType.CONTEXT_COMPRESSOR].process(context)
            
            # 5. 响应生成
            if RAGComponentType.GENERATOR in self.components:
                generation_start = time.time()
                context = await self.components[RAGComponentType.GENERATOR].process(context)
                self.metrics.generation_time_ms = (time.time() - generation_start) * 1000
            
            # 6. 评估（可选）
            evaluation_metrics = {}
            if RAGComponentType.EVALUATOR in self.components:
                evaluator = self.components[RAGComponentType.EVALUATOR]
                evaluation_metrics = await evaluator.evaluate_generation(
                    context.query,
                    context.processing_metadata.get("generated_answer", ""),
                    context.retrieved_documents
                )
            
            # 构建响应
            return RAGResponse(
                query=context.query,
                answer=context.processing_metadata.get("generated_answer", ""),
                confidence=context.processing_metadata.get("confidence", 0.0),
                retrieved_documents=context.retrieved_documents,
                metadata={
                    "strategy": self.strategy.value,
                    "components_used": list(self.components.keys()),
                    "evaluation_metrics": evaluation_metrics,
                    "processing_metadata": context.processing_metadata
                }
            )
            
        except Exception as e:
            logger.error(f"简单RAG处理失败: {e}")
            raise RAGPipelineError(f"简单RAG处理失败: {e}")
    
    async def _process_multi_hop_rag(self, context: RAGContext, **kwargs) -> RAGResponse:
        """处理多跳RAG流程"""
        max_hops = kwargs.get("max_hops", 3)
        current_query = context.query
        all_retrieved_docs = []
        hop_history = []
        
        try:
            for hop in range(max_hops):
                logger.info(f"执行第 {hop + 1} 跳检索: {current_query[:50]}...")
                
                # 创建当前跳的上下文
                hop_context = RAGContext(
                    query=current_query,
                    retrieved_documents=[],
                    user_context=context.user_context,
                    conversation_history=context.conversation_history
                )
                
                # 查询处理
                if RAGComponentType.QUERY_PROCESSOR in self.components:
                    hop_context = await self.components[RAGComponentType.QUERY_PROCESSOR].process(hop_context)
                
                # 文档检索
                if RAGComponentType.RETRIEVER in self.components:
                    hop_context = await self.components[RAGComponentType.RETRIEVER].process(hop_context)
                
                # 收集检索结果
                hop_docs = hop_context.retrieved_documents
                all_retrieved_docs.extend(hop_docs)
                
                hop_history.append({
                    "hop": hop + 1,
                    "query": current_query,
                    "documents_found": len(hop_docs),
                    "top_scores": [doc.score for doc in hop_docs[:3]]
                })
                
                # 判断是否需要继续
                if not hop_docs or hop >= max_hops - 1:
                    break
                
                # 生成下一跳查询
                if RAGComponentType.GENERATOR in self.components:
                    next_query_context = RAGContext(
                        query=f"基于以下信息，生成下一个搜索查询来回答原问题'{context.query}'",
                        retrieved_documents=hop_docs[:3]  # 使用前3个最相关的文档
                    )
                    next_query_context = await self.components[RAGComponentType.GENERATOR].process(next_query_context)
                    current_query = next_query_context.processing_metadata.get("generated_answer", current_query)
                
                # 避免无限循环
                await asyncio.sleep(0.1)
            
            # 最终答案生成
            context.retrieved_documents = all_retrieved_docs
            if RAGComponentType.GENERATOR in self.components:
                context = await self.components[RAGComponentType.GENERATOR].process(context)
            
            return RAGResponse(
                query=context.query,
                answer=context.processing_metadata.get("generated_answer", ""),
                confidence=context.processing_metadata.get("confidence", 0.0),
                retrieved_documents=all_retrieved_docs,
                metadata={
                    "strategy": "multi_hop",
                    "hops_executed": len(hop_history),
                    "hop_history": hop_history,
                    "total_documents": len(all_retrieved_docs)
                }
            )
            
        except Exception as e:
            logger.error(f"多跳RAG处理失败: {e}")
            raise RAGPipelineError(f"多跳RAG处理失败: {e}")
    
    async def _process_adaptive_rag(self, context: RAGContext, **kwargs) -> RAGResponse:
        """处理自适应RAG流程"""
        try:
            # 1. 首先进行查询分析
            if RAGComponentType.QUERY_PROCESSOR in self.components:
                context = await self.components[RAGComponentType.QUERY_PROCESSOR].process(context)
            
            # 2. 根据查询复杂度选择策略
            if context.query_analysis:
                complexity = context.query_analysis.complexity
                
                if complexity.value in ["multi_hop", "comparative"]:
                    logger.info("检测到复杂查询，使用多跳RAG")
                    return await self._process_multi_hop_rag(context, **kwargs)
                elif complexity.value == "analytical":
                    logger.info("检测到分析性查询，使用增强检索")
                    # 增加检索数量和重排序
                    kwargs["top_k"] = kwargs.get("top_k", 10) * 2
                    return await self._process_simple_rag(context, **kwargs)
                else:
                    logger.info("检测到简单查询，使用标准RAG")
                    return await self._process_simple_rag(context, **kwargs)
            else:
                # 没有查询分析，使用简单RAG
                return await self._process_simple_rag(context, **kwargs)
                
        except Exception as e:
            logger.error(f"自适应RAG处理失败: {e}")
            raise RAGPipelineError(f"自适应RAG处理失败: {e}")
    
    async def get_metrics(self) -> RAGMetrics:
        """获取性能指标"""
        return self.metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "pipeline_name": self.pipeline_name,
            "strategy": self.strategy.value,
            "initialized": self._initialized,
            "components": {}
        }
        
        for component_type, component in self.components.items():
            try:
                component_status = {
                    "name": component.component_name,
                    "initialized": component.is_initialized,
                    "type": component_type.value
                }
                
                # 如果组件有健康检查方法，调用它
                if hasattr(component, 'health_check'):
                    component_health = await component.health_check()
                    component_status.update(component_health)
                
                status["components"][component_type.value] = component_status
                
            except Exception as e:
                status["components"][component_type.value] = {
                    "name": component.component_name,
                    "error": str(e),
                    "status": "unhealthy"
                }
        
        return status
    
    async def cleanup(self) -> None:
        """清理管道资源"""
        for component in self.components.values():
            try:
                await component.cleanup()
            except Exception as e:
                logger.warning(f"组件清理失败: {e}")
        
        self.components.clear()
        self._initialized = False
        logger.info(f"RAG管道清理完成: {self.pipeline_name}")


class RAGPipelineBuilder:
    """RAG管道构建器"""
    
    def __init__(self):
        self.config = {}
        self.components = {}
    
    def set_strategy(self, strategy: RAGStrategy) -> 'RAGPipelineBuilder':
        """设置RAG策略"""
        self.config["strategy"] = strategy.value
        return self
    
    def set_name(self, name: str) -> 'RAGPipelineBuilder':
        """设置管道名称"""
        self.config["pipeline_name"] = name
        return self
    
    def add_component(self, component: IRAGComponent) -> 'RAGPipelineBuilder':
        """添加组件"""
        self.components[component.component_type] = component
        return self
    
    def add_query_processor(self, processor: 'IQueryProcessor') -> 'RAGPipelineBuilder':
        """添加查询处理器"""
        return self.add_component(processor)
    
    def add_retriever(self, retriever: 'IRetriever') -> 'RAGPipelineBuilder':
        """添加检索器"""
        return self.add_component(retriever)
    
    def add_reranker(self, reranker: 'IReranker') -> 'RAGPipelineBuilder':
        """添加重排序器"""
        return self.add_component(reranker)
    
    def add_generator(self, generator: 'IResponseGenerator') -> 'RAGPipelineBuilder':
        """添加响应生成器"""
        return self.add_component(generator)
    
    async def build(self) -> ModularRAGPipeline:
        """构建RAG管道"""
        pipeline = ModularRAGPipeline(self.config)
        
        for component in self.components.values():
            await pipeline.add_component(component)
        
        return pipeline


# 工厂函数
async def create_simple_rag_pipeline(
    query_processor: Optional['IQueryProcessor'] = None,
    retriever: Optional['IRetriever'] = None,
    generator: Optional['IResponseGenerator'] = None,
    **config
) -> ModularRAGPipeline:
    """创建简单RAG管道"""
    builder = RAGPipelineBuilder().set_strategy(RAGStrategy.SIMPLE)
    
    if query_processor:
        builder.add_query_processor(query_processor)
    if retriever:
        builder.add_retriever(retriever)
    if generator:
        builder.add_generator(generator)
    
    return await builder.build()


async def create_multi_hop_rag_pipeline(
    query_processor: 'IQueryProcessor',
    retriever: 'IRetriever',
    generator: 'IResponseGenerator',
    reranker: Optional['IReranker'] = None,
    **config
) -> ModularRAGPipeline:
    """创建多跳RAG管道"""
    builder = (RAGPipelineBuilder()
               .set_strategy(RAGStrategy.MULTI_HOP)
               .add_query_processor(query_processor)
               .add_retriever(retriever)
               .add_generator(generator))
    
    if reranker:
        builder.add_reranker(reranker)
    
    return await builder.build()


async def create_adaptive_rag_pipeline(
    query_processor: 'IQueryProcessor',
    retriever: 'IRetriever', 
    generator: 'IResponseGenerator',
    reranker: Optional['IReranker'] = None,
    evaluator: Optional['IRAGEvaluator'] = None,
    **config
) -> ModularRAGPipeline:
    """创建自适应RAG管道"""
    builder = (RAGPipelineBuilder()
               .set_strategy(RAGStrategy.ADAPTIVE)
               .add_query_processor(query_processor)
               .add_retriever(retriever)
               .add_generator(generator))
    
    if reranker:
        builder.add_reranker(reranker)
    if evaluator:
        builder.add_component(evaluator)
    
    return await builder.build()
