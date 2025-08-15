"""
RAG系统主程序
演示基础RAG功能的完整流程
"""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

# 导入基础接口
from rag.models import RAGConfig, Document, DocumentStatus
from rag.file_loader.base import BaseFileLoader
from rag.file_loader.text_loader import TextFileLoader, MarkdownLoader
from rag.document_spliter.base import BaseDocumentSplitter, FixedSizeSplitter, SentenceSplitter
from rag.vector_store import BaseVectorStore, InMemoryVectorStore
from rag.document_repository import BaseDocumentRepository, InMemoryDocumentRepository
from rag.retriever import BaseRetriever, SemanticRetriever, HybridRetriever
# Router功能已集成到Retriever中


class RAGSystem:
    """RAG系统主类"""
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        初始化RAG系统
        
        Args:
            config: RAG配置
        """
        self.config = config or RAGConfig()
        
        # 验证配置
        config_errors = self.config.validate()
        if config_errors:
            raise ValueError(f"Configuration errors: {'; '.join(config_errors)}")
        
        # 初始化组件
        self.file_loaders = self._initialize_file_loaders()
        self.document_splitter = self._initialize_document_splitter()
        self.vector_store = self._initialize_vector_store()
        self.document_repository = self._initialize_document_repository()
        self.retriever = self._initialize_retriever()
        
        print(f"✅ RAG系统初始化完成")
        print(f"   - 支持文件格式: {self.config.supported_file_types}")
        print(f"   - 块大小: {self.config.chunk_size}")
        print(f"   - 块重叠: {self.config.chunk_overlap}")
        print(f"   - Top-K: {self.config.top_k}")
    
    def _initialize_file_loaders(self) -> dict:
        """初始化文件加载器"""
        loaders = {
            'text': TextFileLoader(),
            'markdown': MarkdownLoader()
        }
        return loaders
    
    def _initialize_document_splitter(self) -> BaseDocumentSplitter:
        """初始化文档分割器"""
        return SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
    
    def _initialize_vector_store(self) -> BaseVectorStore:
        """初始化向量存储"""
        return InMemoryVectorStore(self.config.vector_store_config.__dict__)
    
    def _initialize_document_repository(self) -> BaseDocumentRepository:
        """初始化文档仓储"""
        return InMemoryDocumentRepository()
    
    def _initialize_retriever(self) -> BaseRetriever:
        """初始化检索器"""
        retriever_config = {
            'top_k': self.config.top_k,
            'similarity_threshold': self.config.similarity_threshold,
            'enable_reranking': self.config.enable_reranking
        }
        
        return SemanticRetriever(
            vector_store=self.vector_store,
            document_repository=self.document_repository,
            config=retriever_config
        )
    
    
    def _get_appropriate_loader(self, file_path: str) -> BaseFileLoader:
        """根据文件类型选择合适的加载器"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.md', '.markdown']:
            return self.file_loaders['markdown']
        elif file_ext in ['.txt', '.text']:
            return self.file_loaders['text']
        else:
            # 默认使用文本加载器
            return self.file_loaders['text']
    
    async def process_document(self, file_path: str) -> str:
        """
        处理单个文档的完整流程
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文档ID
        """
        start_time = time.time()
        
        try:
            print(f"\n📄 开始处理文档: {file_path}")
            
            # 1. 选择合适的文件加载器
            loader = self._get_appropriate_loader(file_path)
            
            # 2. 加载文档
            print("   🔄 加载文档...")
            document = await loader.load(file_path)
            print(f"   ✅ 文档加载完成: {document.title}")
            print(f"      - 文件大小: {document.file_size} bytes")
            print(f"      - 字符数: {len(document.content)}")
            print(f"      - 状态: {document.status.value}")
            
            # 3. 存储文档元数据
            print("   🔄 存储文档元数据...")
            doc_id = await self.document_repository.save(document)
            
            # 4. 分割文档
            print("   🔄 分割文档...")
            chunks = await self.document_splitter.split(document)
            print(f"   ✅ 文档分割完成: {len(chunks)} 个块")
            
            if chunks:
                avg_chunk_size = sum(len(chunk.content) for chunk in chunks) / len(chunks)
                print(f"      - 平均块大小: {avg_chunk_size:.0f} 字符")
            
            # 5. 存储向量（这里简化处理，实际应该生成真实的嵌入向量）
            print("   🔄 存储向量...")
            # 为每个块生成简单的伪向量（实际应用中需要真实的嵌入模型）
            for chunk in chunks:
                chunk.embedding = [0.1] * 768  # 简单的占位向量
            
            vector_ids = await self.vector_store.store_chunks(chunks)
            print(f"   ✅ 向量存储完成: {len(vector_ids)} 个向量")
            
            # 6. 更新文档状态
            await self.document_repository.update_status(doc_id, DocumentStatus.COMPLETED)
            
            processing_time = (time.time() - start_time) * 1000
            print(f"   ⏱️  处理完成，耗时: {processing_time:.2f}ms")
            
            return doc_id
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            print(f"   ❌ 处理失败: {str(e)}")
            print(f"   ⏱️  失败耗时: {processing_time:.2f}ms")
            
            # 更新文档状态为错误
            if 'document' in locals():
                await self.document_repository.update_status(document.id, DocumentStatus.ERROR)
            
            raise
    
    async def query(self, question: str) -> dict:
        """
        执行查询
        
        Args:
            question: 查询问题
            
        Returns:
            dict: 查询结果
        """
        start_time = time.time()
        
        try:
            print(f"\n🔍 执行查询: {question}")
            
            # 1. 执行智能检索（包含内置路由决策）
            print("   🔄 执行检索...")
            result = await self.retriever.retrieve(question, top_k=self.config.top_k)
            
            query_time = (time.time() - start_time) * 1000
            
            print(f"   ✅ 检索完成: 找到 {len(result.chunks)} 个相关块")
            print(f"   🎯 使用策略: {result.metadata.get('strategy', 'unknown')}")
            print(f"   ⏱️  查询耗时: {query_time:.2f}ms")
            
            # 2. 格式化结果
            formatted_result = {
                'query': question,
                'answer_chunks': [],
                'total_found': len(result.chunks),
                'query_time_ms': query_time,
                'strategy_used': result.metadata.get('strategy', 'unknown'),
                'preprocessing': result.metadata.get('pre_processing', {}),
                'postprocessing': result.metadata.get('post_processing', {})
            }
            
            for i, (chunk, score) in enumerate(zip(result.chunks, result.relevance_scores)):
                formatted_result['answer_chunks'].append({
                    'rank': i + 1,
                    'content': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    'score': score,
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index
                })
            
            return formatted_result
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            print(f"   ❌ 查询失败: {str(e)}")
            print(f"   ⏱️  失败耗时: {query_time:.2f}ms")
            
            return {
                'query': question,
                'error': str(e),
                'query_time_ms': query_time
            }
    
    async def get_system_status(self) -> dict:
        """获取系统状态"""
        # 获取各组件状态
        vector_store_info = await self.vector_store.get_collection_info()
        document_repository_stats = await self.document_repository.get_statistics()
        
        return {
            'vector_store': vector_store_info,
            'document_repository': document_repository_stats,
            'config': {
                'chunk_size': self.config.chunk_size,
                'chunk_overlap': self.config.chunk_overlap,
                'top_k': self.config.top_k,
                'similarity_threshold': self.config.similarity_threshold
            }
        }


async def main():
    """主程序演示"""
    print("🚀 启动RAG系统演示")
    
    # 创建RAG系统
    config = RAGConfig(
        chunk_size=500,
        chunk_overlap=50,
        top_k=3,
        similarity_threshold=0.1  # 设置较低的阈值以便演示
    )
    
    rag_system = RAGSystem(config)
    
    # 创建示例文档文件
    test_files = []
    
    # 创建测试文档1
    test_file1 = "test_document1.txt"
    with open(test_file1, 'w', encoding='utf-8') as f:
        f.write("""
人工智能基础知识

人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，致力于创造能够执行通常需要人类智能的任务的机器。
这些任务包括学习、推理、问题解决、感知和语言理解。

机器学习是人工智能的一个重要子领域，它使计算机能够在没有明确编程的情况下学习和改进。
深度学习是机器学习的一种特殊形式，它使用人工神经网络来模拟人脑的工作方式。

自然语言处理（NLP）是人工智能的另一个重要分支，专注于使计算机能够理解、解释和生成人类语言。
""")
    test_files.append(test_file1)
    
    # 创建测试文档2
    test_file2 = "test_document2.md"
    with open(test_file2, 'w', encoding='utf-8') as f:
        f.write("""
# RAG系统介绍

## 什么是RAG？

RAG（Retrieval-Augmented Generation）是一种结合了检索和生成的人工智能方法。
它首先从大型知识库中检索相关信息，然后使用这些信息来生成回答。

## RAG的优势

- **准确性**: 基于事实信息生成回答
- **可解释性**: 可以追溯信息来源
- **时效性**: 可以获取最新信息
- **成本效益**: 相比训练大型模型更经济

## 应用场景

RAG系统广泛应用于：
1. 智能问答系统
2. 文档查询与分析
3. 知识管理系统
4. 客户服务机器人
""")
    test_files.append(test_file2)
    
    try:
        # 处理文档
        for file_path in test_files:
            doc_id = await rag_system.process_document(file_path)
            print(f"📋 文档ID: {doc_id}")
        
        # 查询演示
        queries = [
            "什么是人工智能？",
            "RAG有什么优势？",
            "机器学习和深度学习的关系是什么？",
            "RAG系统有哪些应用场景？"
        ]
        
        for query in queries:
            result = await rag_system.query(query)
            
            print("\n" + "="*60)
            print(f"❓ 问题: {result['query']}")
            
            if 'error' in result:
                print(f"❌ 错误: {result['error']}")
            else:
                print(f"📊 找到 {result['total_found']} 个相关结果")
                print(f"🎯 使用策略: {result['strategy_used']}")
                
                # 显示预处理信息
                if result['preprocessing']:
                    preprocessing = result['preprocessing']
                    if 'query_type' in preprocessing:
                        print(f"🧠 查询类型: {preprocessing['query_type']}")
                
                # 显示后处理信息
                if result['postprocessing']:
                    postprocessing = result['postprocessing']
                    if 'reranked' in postprocessing:
                        print(f"🔄 重排序: {'是' if postprocessing['reranked'] else '否'}")
                    if 'total_compressed' in postprocessing and postprocessing['total_compressed'] > 0:
                        print(f"📦 压缩了 {postprocessing['total_compressed']} 个结果")
                
                for chunk_info in result['answer_chunks']:
                    print(f"\n📄 结果 {chunk_info['rank']} (相关性: {chunk_info['score']:.3f}):")
                    print(f"   {chunk_info['content']}")
        
        # 显示系统状态
        print("\n" + "="*60)
        print("📈 系统状态:")
        status = await rag_system.get_system_status()
        
        print(f"   向量存储: {status['vector_store']['total_chunks']} 个块")
        print(f"   文档数量: {status['document_repository']['total_documents']} 个")
        print(f"   配置信息: 块大小={status['config']['chunk_size']}, Top-K={status['config']['top_k']}")
        
    finally:
        # 清理测试文件
        for file_path in test_files:
            try:
                Path(file_path).unlink()
                print(f"🗑️  已删除测试文件: {file_path}")
            except:
                pass
    
    print("\n✅ RAG系统演示完成!")


if __name__ == "__main__":
    asyncio.run(main())