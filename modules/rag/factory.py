"""
RAG组件工厂

提供便捷的方法来创建和配置RAG管道及其组件。
"""

import logging
from typing import Any, Dict, List, Optional

from modules.rag.base import RAGStrategy
from modules.rag.pipeline import ModularRAGPipeline, RAGPipelineBuilder
from modules.rag.query_processor import BasicQueryProcessor, EnhancedQueryProcessor
from modules.rag.retrievers import VectorRetriever, SummaryRetriever, HybridRetriever
from modules.rag.bm25_retriever import BM25Retriever, DatabaseBM25Retriever
from modules.rag.rerankers import ScoreBasedReranker, CrossEncoderReranker, HybridReranker
from modules.rag.generators import OpenAIResponseGenerator, StreamingResponseGenerator, TemplateResponseGenerator

logger = logging.getLogger(__name__)


class RAGComponentFactory:
    """RAG组件工厂"""
    
    @staticmethod
    def create_query_processor(
        processor_type: str = "basic",
        config: Optional[Dict[str, Any]] = None
    ):
        """创建查询处理器"""
        config = config or {}
        
        if processor_type == "basic":
            return BasicQueryProcessor(config)
        elif processor_type == "enhanced":
            return EnhancedQueryProcessor(config)
        else:
            raise ValueError(f"不支持的查询处理器类型: {processor_type}")
    
    @staticmethod
    def create_vector_retriever(
        vector_store,
        embedding_service,
        config: Optional[Dict[str, Any]] = None
    ):
        """创建向量检索器"""
        return VectorRetriever(vector_store, embedding_service, config)
    
    @staticmethod
    def create_summary_retriever(
        vector_store,
        embedding_service,
        config: Optional[Dict[str, Any]] = None
    ):
        """创建摘要检索器"""
        return SummaryRetriever(vector_store, embedding_service, config)
    
    @staticmethod
    def create_bm25_retriever(
        retriever_type: str = "memory",
        db_session=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """创建BM25检索器"""
        config = config or {}
        
        if retriever_type == "memory":
            return BM25Retriever(config)
        elif retriever_type == "database":
            if not db_session:
                raise ValueError("数据库BM25检索器需要db_session参数")
            return DatabaseBM25Retriever(db_session, config)
        else:
            raise ValueError(f"不支持的BM25检索器类型: {retriever_type}")
    
    @staticmethod
    def create_hybrid_retriever(
        retrievers: List,
        config: Optional[Dict[str, Any]] = None
    ):
        """创建混合检索器"""
        return HybridRetriever(retrievers, config)
    
    @staticmethod
    def create_reranker(
        reranker_type: str = "score_based",
        config: Optional[Dict[str, Any]] = None
    ):
        """创建重排序器"""
        config = config or {}
        
        if reranker_type == "score_based":
            return ScoreBasedReranker(config)
        elif reranker_type == "cross_encoder":
            return CrossEncoderReranker(config)
        else:
            raise ValueError(f"不支持的重排序器类型: {reranker_type}")
    
    @staticmethod
    def create_hybrid_reranker(
        rerankers: List,
        config: Optional[Dict[str, Any]] = None
    ):
        """创建混合重排序器"""
        return HybridReranker(rerankers, config)
    
    @staticmethod
    def create_response_generator(
        generator_type: str = "openai",
        config: Optional[Dict[str, Any]] = None
    ):
        """创建响应生成器"""
        config = config or {}
        
        if generator_type == "openai":
            return OpenAIResponseGenerator(config)
        elif generator_type == "streaming":
            return StreamingResponseGenerator(config)
        elif generator_type == "template":
            return TemplateResponseGenerator(config)
        else:
            raise ValueError(f"不支持的响应生成器类型: {generator_type}")


class RAGPipelineFactory:
    """RAG管道工厂"""
    
    @staticmethod
    async def create_simple_rag_pipeline(
        vector_store,
        embedding_service,
        config: Optional[Dict[str, Any]] = None
    ) -> ModularRAGPipeline:
        """创建简单RAG管道"""
        config = config or {}
        
        # 创建组件
        query_processor = RAGComponentFactory.create_query_processor(
            "basic", config.get("query_processor", {})
        )
        
        vector_retriever = RAGComponentFactory.create_vector_retriever(
            vector_store, embedding_service, config.get("vector_retriever", {})
        )
        
        generator = RAGComponentFactory.create_response_generator(
            "openai", config.get("generator", {})
        )
        
        # 构建管道
        builder = (RAGPipelineBuilder()
                   .set_strategy(RAGStrategy.SIMPLE)
                   .set_name("simple_rag")
                   .add_query_processor(query_processor)
                   .add_retriever(vector_retriever)
                   .add_generator(generator))
        
        return await builder.build()
    
    @staticmethod
    async def create_hybrid_rag_pipeline(
        vector_store,
        embedding_service,
        db_session=None,
        config: Optional[Dict[str, Any]] = None
    ) -> ModularRAGPipeline:
        """创建混合RAG管道（向量+BM25）"""
        config = config or {}
        
        # 创建组件
        query_processor = RAGComponentFactory.create_query_processor(
            "enhanced", config.get("query_processor", {})
        )
        
        # 创建向量检索器
        vector_retriever = RAGComponentFactory.create_vector_retriever(
            vector_store, embedding_service, config.get("vector_retriever", {})
        )
        
        # 创建BM25检索器
        bm25_retriever = RAGComponentFactory.create_bm25_retriever(
            "database" if db_session else "memory",
            db_session,
            config.get("bm25_retriever", {})
        )
        
        # 创建混合检索器
        hybrid_retriever = RAGComponentFactory.create_hybrid_retriever(
            [vector_retriever, bm25_retriever],
            config.get("hybrid_retriever", {})
        )
        
        # 创建重排序器
        reranker = RAGComponentFactory.create_reranker(
            "cross_encoder", config.get("reranker", {})
        )
        
        # 创建响应生成器
        generator = RAGComponentFactory.create_response_generator(
            "openai", config.get("generator", {})
        )
        
        # 构建管道
        builder = (RAGPipelineBuilder()
                   .set_strategy(RAGStrategy.SIMPLE)
                   .set_name("hybrid_rag")
                   .add_query_processor(query_processor)
                   .add_retriever(hybrid_retriever)
                   .add_reranker(reranker)
                   .add_generator(generator))
        
        return await builder.build()
    
    @staticmethod
    async def create_adaptive_rag_pipeline(
        vector_store,
        embedding_service,
        db_session=None,
        config: Optional[Dict[str, Any]] = None
    ) -> ModularRAGPipeline:
        """创建自适应RAG管道"""
        config = config or {}
        
        # 创建组件
        query_processor = RAGComponentFactory.create_query_processor(
            "enhanced", config.get("query_processor", {})
        )
        
        # 创建多个检索器
        vector_retriever = RAGComponentFactory.create_vector_retriever(
            vector_store, embedding_service, config.get("vector_retriever", {})
        )
        
        summary_retriever = RAGComponentFactory.create_summary_retriever(
            vector_store, embedding_service, config.get("summary_retriever", {})
        )
        
        bm25_retriever = RAGComponentFactory.create_bm25_retriever(
            "database" if db_session else "memory",
            db_session,
            config.get("bm25_retriever", {})
        )
        
        # 创建混合检索器
        hybrid_retriever = RAGComponentFactory.create_hybrid_retriever(
            [vector_retriever, summary_retriever, bm25_retriever],
            config.get("hybrid_retriever", {})
        )
        
        # 创建混合重排序器
        score_reranker = RAGComponentFactory.create_reranker(
            "score_based", config.get("score_reranker", {})
        )
        
        cross_reranker = RAGComponentFactory.create_reranker(
            "cross_encoder", config.get("cross_reranker", {})
        )
        
        hybrid_reranker = RAGComponentFactory.create_hybrid_reranker(
            [score_reranker, cross_reranker],
            config.get("hybrid_reranker", {})
        )
        
        # 创建流式响应生成器
        generator = RAGComponentFactory.create_response_generator(
            "streaming", config.get("generator", {})
        )
        
        # 构建管道
        builder = (RAGPipelineBuilder()
                   .set_strategy(RAGStrategy.ADAPTIVE)
                   .set_name("adaptive_rag")
                   .add_query_processor(query_processor)
                   .add_retriever(hybrid_retriever)
                   .add_reranker(hybrid_reranker)
                   .add_generator(generator))
        
        return await builder.build()
    
    @staticmethod
    async def create_multi_hop_rag_pipeline(
        vector_store,
        embedding_service,
        config: Optional[Dict[str, Any]] = None
    ) -> ModularRAGPipeline:
        """创建多跳RAG管道"""
        config = config or {}
        
        # 创建组件
        query_processor = RAGComponentFactory.create_query_processor(
            "enhanced", config.get("query_processor", {})
        )
        
        vector_retriever = RAGComponentFactory.create_vector_retriever(
            vector_store, embedding_service, config.get("vector_retriever", {})
        )
        
        reranker = RAGComponentFactory.create_reranker(
            "cross_encoder", config.get("reranker", {})
        )
        
        generator = RAGComponentFactory.create_response_generator(
            "openai", config.get("generator", {})
        )
        
        # 构建管道
        builder = (RAGPipelineBuilder()
                   .set_strategy(RAGStrategy.MULTI_HOP)
                   .set_name("multi_hop_rag")
                   .add_query_processor(query_processor)
                   .add_retriever(vector_retriever)
                   .add_reranker(reranker)
                   .add_generator(generator))
        
        return await builder.build()


# 便捷函数
async def create_rag_pipeline_from_config(
    pipeline_type: str,
    vector_store,
    embedding_service,
    db_session=None,
    config: Optional[Dict[str, Any]] = None
) -> ModularRAGPipeline:
    """根据配置创建RAG管道"""
    
    if pipeline_type == "simple":
        return await RAGPipelineFactory.create_simple_rag_pipeline(
            vector_store, embedding_service, config
        )
    elif pipeline_type == "hybrid":
        return await RAGPipelineFactory.create_hybrid_rag_pipeline(
            vector_store, embedding_service, db_session, config
        )
    elif pipeline_type == "adaptive":
        return await RAGPipelineFactory.create_adaptive_rag_pipeline(
            vector_store, embedding_service, db_session, config
        )
    elif pipeline_type == "multi_hop":
        return await RAGPipelineFactory.create_multi_hop_rag_pipeline(
            vector_store, embedding_service, config
        )
    else:
        raise ValueError(f"不支持的管道类型: {pipeline_type}")


# 预设配置
DEFAULT_CONFIGS = {
    "simple_rag": {
        "query_processor": {
            "enable_query_expansion": True,
            "enable_entity_extraction": True
        },
        "vector_retriever": {
            "default_top_k": 10,
            "default_score_threshold": 0.0
        },
        "generator": {
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.3
        }
    },
    
    "hybrid_rag": {
        "query_processor": {
            "use_ai_analysis": True,
            "enable_query_expansion": True
        },
        "vector_retriever": {
            "default_top_k": 15,
            "default_score_threshold": 0.0
        },
        "bm25_retriever": {
            "k1": 1.5,
            "b": 0.75
        },
        "hybrid_retriever": {
            "fusion_method": "rrf",
            "rrf_k": 60
        },
        "reranker": {
            "model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "batch_size": 32
        },
        "generator": {
            "model": "gpt-3.5-turbo",
            "max_tokens": 1500,
            "temperature": 0.2
        }
    },
    
    "adaptive_rag": {
        "query_processor": {
            "use_ai_analysis": True,
            "enable_query_expansion": True,
            "max_rewritten_queries": 5
        },
        "vector_retriever": {
            "default_top_k": 20,
            "default_score_threshold": 0.0
        },
        "summary_retriever": {
            "default_top_k": 5,
            "default_score_threshold": 0.75
        },
        "bm25_retriever": {
            "k1": 1.2,
            "b": 0.8
        },
        "hybrid_retriever": {
            "fusion_method": "weighted",
            "weights": [0.6, 0.3, 0.1]  # vector, summary, bm25
        },
        "hybrid_reranker": {
            "combination_method": "weighted_average",
            "weights": [0.7, 0.3]  # score_based, cross_encoder
        },
        "generator": {
            "model": "gpt-4",
            "max_tokens": 2000,
            "temperature": 0.1,
            "enable_streaming": True
        }
    }
}


def get_default_config(pipeline_type: str) -> Dict[str, Any]:
    """获取预设配置"""
    return DEFAULT_CONFIGS.get(pipeline_type, {}).copy()
