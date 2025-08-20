#!/usr/bin/env python3
"""
Advanced RAG System Demonstration

This script demonstrates the capabilities of the advanced RAG system
including document indexing, multi-resource chat, and evaluation.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main demonstration workflow"""
    print("🚀 Advanced RAG System Demonstration")
    print("=" * 60)
    
    try:
        # Import the advanced RAG system
        from modules.rag import TopicChatSystem, ChatRequest, ChatMode
        
        # Initialize the system
        print("\n1. 🔧 Initializing Advanced RAG System...")
        config = {
            "vector_store_type": "chromadb",
            "vector_store_config": {
                "persist_directory": "./demo_data/chroma_db"
            },
            "embedding_cache_config": {
                "enabled": False  # Disable for demo simplicity
            },
            "generation_config": {
                "llm_provider": "openai",
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.1,
                # Note: In production, set via environment variables
                # "openai_api_key": "your-api-key-here"
            }
        }
        
        rag_system = TopicChatSystem(config)
        await rag_system.initialize()
        print("✅ System initialized successfully!")
        
        # Perform health check
        print("\n2. ❤️ System Health Check...")
        health = await rag_system.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Components healthy: {health['health_ratio']:.1%}")
        
        # Create sample documents for demonstration
        print("\n3. 📚 Creating Sample Documents...")
        sample_documents = create_sample_documents()
        
        # Index documents for topic
        topic_id = 1
        print(f"\n4. 📊 Indexing {len(sample_documents)} documents for topic {topic_id}...")
        
        index_result = await rag_system.index_topic_documents(
            topic_id=topic_id,
            documents=sample_documents
        )
        
        if index_result["success"]:
            print("✅ Documents indexed successfully!")
            print(f"   Documents processed: {index_result['documents_processed']}")
            print(f"   Chunks created: {index_result['chunks_created']}")
        else:
            print(f"❌ Indexing failed: {index_result.get('error')}")
            return
        
        # Get topic statistics
        print(f"\n5. 📊 Topic {topic_id} Statistics...")
        stats = await rag_system.get_topic_statistics(topic_id)
        if stats:
            print(f"   Documents: {stats['document_count']}")
            print(f"   Chunks: {stats['total_chunks']}")
            print(f"   Languages: {list(stats['languages'].keys())}")
            print(f"   Content types: {list(stats['content_types'].keys())}")
        
        # Demonstrate chat functionality
        print(f"\n6. 💬 Demonstrating Multi-Resource Chat...")
        await demonstrate_chat_scenarios(rag_system, topic_id)
        
        # Show system metrics
        print(f"\n7. 📈 System Performance Metrics...")
        metrics = await rag_system.get_system_metrics()
        print(f"   Total queries: {metrics['total_queries']}")
        print(f"   Successful responses: {metrics['successful_responses']}")
        print(f"   Average response time: {metrics['average_response_time']:.2f}s")
        print(f"   Active conversations: {metrics['active_conversations']}")
        
        # Demonstrate evaluation
        print(f"\n8. 🧪 Running System Evaluation...")
        await demonstrate_evaluation(rag_system)
        
        print(f"\n✨ Demonstration completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed.")
        print("Run: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        try:
            if 'rag_system' in locals():
                await rag_system.shutdown()
                print("\n🧹 System shutdown completed.")
        except:
            pass

def create_sample_documents() -> List[Dict[str, Any]]:
    """Create sample documents for demonstration"""
    documents = [
        {
            "id": "doc_ai_intro",
            "title": "人工智能概述",
            "content": """
            人工智能（Artificial Intelligence，简称AI）是计算机科学的一个重要分支，
            旨在创建能够执行通常需要人类智能的任务的机器和系统。

            人工智能的发展历程可以追溯到20世纪50年代，当时科学家们开始探索如何让机器
            模拟人类的思维过程。经过几十年的发展，AI已经从理论研究发展成为实际应用的
            重要技术。

            现代人工智能主要包括以下几个重要领域：
            1. 机器学习（Machine Learning）
            2. 深度学习（Deep Learning）
            3. 自然语言处理（Natural Language Processing）
            4. 计算机视觉（Computer Vision）
            5. 专家系统（Expert Systems）

            人工智能的应用领域非常广泛，包括医疗诊断、金融分析、自动驾驶、
            智能助手等多个行业和场景。
            """,
            "metadata": {
                "author": "AI专家",
                "category": "概述",
                "created_at": "2024-01-01",
                "tags": ["人工智能", "概述", "基础知识"]
            }
        },
        {
            "id": "doc_machine_learning",
            "title": "机器学习基础",
            "content": """
            机器学习是人工智能的一个重要子领域，它使计算机系统能够从数据中
            自动学习和改进，而无需进行明确的编程。

            机器学习的核心思想是通过算法分析大量数据，识别其中的模式，
            并利用这些模式对新数据进行预测或决策。

            主要的机器学习类型包括：

            1. 监督学习（Supervised Learning）
               - 使用标记的训练数据来学习输入和输出之间的映射关系
               - 包括分类和回归任务
               - 常见算法：线性回归、决策树、支持向量机、随机森林

            2. 无监督学习（Unsupervised Learning）
               - 在没有标记数据的情况下发现数据中的隐藏模式
               - 包括聚类、降维、关联规则挖掘
               - 常见算法：K-means、层次聚类、PCA

            3. 强化学习（Reinforcement Learning）
               - 通过与环境交互来学习最优策略
               - 适用于游戏、机器人控制等场景
               - 著名应用：AlphaGo、自动驾驶

            机器学习在图像识别、语音识别、推荐系统、欺诈检测等领域
            都有广泛的应用。
            """,
            "metadata": {
                "author": "ML研究员",
                "category": "技术详解",
                "created_at": "2024-01-15",
                "tags": ["机器学习", "算法", "监督学习", "无监督学习"]
            }
        },
        {
            "id": "doc_deep_learning",
            "title": "深度学习详解",
            "content": """
            深度学习是机器学习的一个专门子领域，它基于人工神经网络，
            特别是深层神经网络来进行学习和表示。

            深度学习的核心特征：
            1. 多层神经网络结构
            2. 自动特征提取能力
            3. 端到端学习方式
            4. 大数据驱动

            主要的深度学习架构：

            1. 卷积神经网络（CNN）
               - 主要用于图像处理和计算机视觉
               - 包含卷积层、池化层、全连接层
               - 著名模型：LeNet、AlexNet、VGG、ResNet

            2. 循环神经网络（RNN）
               - 适合处理序列数据
               - 包括LSTM、GRU等变体
               - 应用于自然语言处理、时间序列预测

            3. 生成对抗网络（GAN）
               - 由生成器和判别器组成
               - 能够生成逼真的图像、文本等内容
               - 应用于图像生成、数据增强

            4. 变换器（Transformer）
               - 基于注意力机制的架构
               - 在自然语言处理领域表现出色
               - 代表模型：BERT、GPT、T5

            深度学习与传统机器学习的主要区别在于：
            - 深度学习能自动学习特征表示
            - 需要更多的数据和计算资源
            - 在某些复杂任务上表现更好

            深度学习已成为当前AI发展的重要推动力，在语音识别、
            自然语言处理、计算机视觉等领域取得了突破性进展。
            """,
            "metadata": {
                "author": "DL专家",
                "category": "深入研究",
                "created_at": "2024-02-01",
                "tags": ["深度学习", "神经网络", "CNN", "RNN", "Transformer"]
            }
        },
        {
            "id": "doc_nlp",
            "title": "自然语言处理技术",
            "content": """
            自然语言处理（Natural Language Processing，简称NLP）是人工智能
            的一个重要分支，致力于让计算机理解、处理和生成人类语言。

            NLP的主要任务包括：

            1. 文本预处理
               - 分词（Tokenization）
               - 词性标注（POS Tagging）
               - 命名实体识别（NER）
               - 句法分析（Parsing）

            2. 语义理解
               - 词义消歧
               - 语义角色标注
               - 情感分析
               - 意图识别

            3. 文本生成
               - 机器翻译
               - 文本摘要
               - 对话生成
               - 内容创作

            4. 信息提取
               - 关键词提取
               - 关系抽取
               - 事件抽取
               - 知识图谱构建

            现代NLP技术的发展趋势：

            1. 从统计方法到神经网络方法
            2. 从浅层模型到深度模型
            3. 从任务特定到通用预训练模型
            4. 从小数据到大规模语言模型

            重要的NLP模型和技术：
            - Word2Vec、GloVe等词嵌入技术
            - BERT、GPT等预训练语言模型
            - Attention机制和Transformer架构
            - 多模态语言模型

            NLP的应用场景：
            - 搜索引擎
            - 智能客服
            - 机器翻译
            - 内容推荐
            - 文档分析
            - 语音助手

            随着大语言模型的发展，NLP正在迎来新的变革，
            ChatGPT等模型展示了强大的语言理解和生成能力。
            """,
            "metadata": {
                "author": "NLP专家",
                "category": "技术应用",
                "created_at": "2024-02-15",
                "tags": ["自然语言处理", "NLP", "BERT", "GPT", "文本处理"]
            }
        }
    ]
    
    print(f"   Created {len(documents)} sample documents")
    for doc in documents:
        print(f"   - {doc['title']} ({len(doc['content'])} chars)")
    
    return documents

async def demonstrate_chat_scenarios(rag_system, topic_id: int):
    """Demonstrate different chat scenarios"""
    scenarios = [
        {
            "name": "基础问答",
            "query": "什么是人工智能？",
            "description": "测试基础的定义性问答"
        },
        {
            "name": "比较分析", 
            "query": "机器学习和深度学习有什么区别？",
            "description": "测试跨文档的比较分析能力"
        },
        {
            "name": "技术细节",
            "query": "深度学习中的CNN和RNN分别用于什么场景？",
            "description": "测试技术细节的提取和解释"
        },
        {
            "name": "应用场景",
            "query": "NLP技术有哪些实际应用？",
            "description": "测试应用场景的整理和归纳"
        },
        {
            "name": "综合问题",
            "query": "如何选择合适的AI技术来解决文本分析问题？",
            "description": "测试综合性问题的回答能力"
        }
    ]
    
    conversation_id = f"demo_conversation_{int(time.time())}"
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n   场景 {i}: {scenario['name']}")
        print(f"   描述: {scenario['description']}")
        print(f"   问题: {scenario['query']}")
        
        # Create chat request
        request = ChatRequest(
            query=scenario['query'],
            topic_id=topic_id,
            conversation_id=conversation_id,
            mode=ChatMode.CONVERSATION,
            max_sources=3
        )
        
        # Measure response time
        start_time = time.time()
        
        try:
            response = await rag_system.chat(request)
            response_time = time.time() - start_time
            
            print(f"   ⏱️ 响应时间: {response_time:.2f}s")
            print(f"   🎯 置信度: {response.confidence:.2f}")
            print(f"   📚 使用来源: {len(response.sources)}")
            print(f"   💬 回答: {response.answer[:200]}...")
            
            if response.follow_up_questions:
                print(f"   🔍 后续问题建议:")
                for q in response.follow_up_questions[:2]:
                    print(f"      - {q}")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        print("-" * 50)

async def demonstrate_evaluation(rag_system):
    """Demonstrate system evaluation"""
    try:
        print("   运行系统评估...")
        
        # This would run actual evaluation in a real system
        # For demo, we'll show what the evaluation would look like
        evaluation_result = await rag_system.evaluate_system_performance()
        
        if evaluation_result["evaluation_completed"]:
            print("   ✅ 评估完成!")
            if "overall_score" in evaluation_result:
                print(f"   📊 总体得分: {evaluation_result['overall_score']:.2f}")
            
            if "metric_scores" in evaluation_result:
                print("   📈 分项得分:")
                for metric, score in evaluation_result["metric_scores"].items():
                    print(f"      {metric}: {score:.2f}")
            
            if "recommendations" in evaluation_result:
                print("   💡 改进建议:")
                for rec in evaluation_result["recommendations"][:3]:
                    print(f"      - {rec}")
        else:
            error = evaluation_result.get("error", "Unknown error")
            print(f"   ⚠️ 评估模拟: {error}")
            print("   📝 说明: 完整评估需要测试数据集和LLM API访问")
            
    except Exception as e:
        print(f"   ⚠️ 评估演示失败: {e}")
        print("   📝 这是正常的，因为演示环境可能缺少完整的评估依赖")

if __name__ == "__main__":
    print("🎯 Advanced RAG System Demo")
    print("📝 This demo showcases the multi-resource topic chat capabilities")
    print("💡 Note: Some features require API keys and external services")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo error")