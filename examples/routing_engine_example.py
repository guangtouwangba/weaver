#!/usr/bin/env python3
"""
Query Routing Engine 使用示例

展示如何使用查询路由引擎进行智能意图识别和查询分发。
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.routing import QueryRoutingEngine, RoutingEngineFactory
from modules.routing.factory import create_routing_engine
from modules.services.rag_integrated_chat_service import RAGIntegratedChatService, create_rag_integrated_chat_service
from modules.schemas.chat import ChatRequest

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_routing():
    """基础路由演示"""
    print("=" * 60)
    print("🚀 基础路由引擎演示")
    print("=" * 60)
    
    # 创建基础路由引擎（仅使用关键词策略）
    engine = await create_routing_engine(mode="keyword_only")
    
    # 测试查询列表
    test_queries = [
        "什么是机器学习？",           # 应该路由到 rag_handler
        "你好，今天天气不错",         # 应该路由到 chat_handler
        "清除对话历史",              # 应该路由到 system_handler
        "帮我计算 2 + 3 * 4",       # 应该路由到 tool_handler
        "/help",                    # 应该路由到 system_handler
        "我很开心",                  # 应该路由到 chat_handler
        "随便说点什么"               # 应该路由到默认处理器
    ]
    
    print("\n📝 测试查询结果:")
    print("-" * 40)
    
    for query in test_queries:
        try:
            result = await engine.route(query, {"test_mode": True})
            decision = result.decision
            
            print(f"查询: '{query}'")
            print(f"  ├─ 处理器: {decision.handler_name}")
            print(f"  ├─ 置信度: {decision.confidence:.3f}")
            print(f"  ├─ 路由类型: {decision.metadata.get('route_type', 'unknown')}")
            print(f"  └─ 匹配模式: {decision.metadata.get('matched_patterns', {}).get('matches', [])}")
            print()
        except Exception as e:
            print(f"❌ 查询 '{query}' 处理失败: {e}")
    
    # 显示引擎统计
    print("📊 路由引擎统计:")
    stats = engine.get_stats()
    print(f"  ├─ 总路由数: {stats['total_routes']}")
    print(f"  ├─ 平均置信度: {stats['average_confidence']:.3f}")
    print(f"  └─ 处理器使用分布: {stats['handler_usage']}")


async def demo_enhanced_chat_service():
    """增强版聊天服务演示"""
    print("\n" + "=" * 60)
    print("🤖 增强版聊天服务演示")
    print("=" * 60)
    
    # 创建RAG集成聊天服务
    chat_service = await create_rag_integrated_chat_service(
        pipeline_type="simple",  # 使用简单模式用于演示
        enable_routing=True
    )
    
    # 测试对话
    test_conversations = [
        {
            "message": "什么是深度学习？",
            "expected": "rag_handler"
        },
        {
            "message": "你好！",
            "expected": "chat_handler"
        },
        {
            "message": "/status",
            "expected": "system_handler"
        },
        {
            "message": "计算 10 * 5 + 3",
            "expected": "tool_handler"
        }
    ]
    
    print("\n💬 对话测试结果:")
    print("-" * 40)
    
    for i, conv in enumerate(test_conversations, 1):
        try:
            # 创建聊天请求
            request = ChatRequest(
                message=conv["message"],
                conversation_id=f"test_conv_{i}",
                include_context=False  # 简化演示
            )
            
            # 测试路由（不实际执行聊天）
            routing_test = await chat_service.test_routing(conv["message"])
            
            if routing_test["success"]:
                actual_handler = routing_test["handler"]
                confidence = routing_test["confidence"]
                
                print(f"对话 {i}: '{conv['message']}'")
                print(f"  ├─ 预期处理器: {conv['expected']}")
                print(f"  ├─ 实际处理器: {actual_handler}")
                print(f"  ├─ 置信度: {confidence:.3f}")
                print(f"  └─ 匹配: {'✅' if actual_handler == conv['expected'] else '❌'}")
            else:
                print(f"❌ 对话 {i} 路由测试失败: {routing_test['error']}")
            print()
            
        except Exception as e:
            print(f"❌ 对话 {i} 处理失败: {e}")
    
    # 显示服务统计
    print("📈 聊天服务统计:")
    try:
        stats = await chat_service.get_routing_stats()
        print(f"  ├─ 路由启用: {stats['routing_enabled']}")
        print(f"  ├─ 路由初始化: {stats['routing_initialized']}")
        if "engine_stats" in stats:
            engine_stats = stats["engine_stats"]
            print(f"  └─ 引擎统计: {engine_stats.get('total_routes', 0)} 次路由")
    except Exception as e:
        print(f"  └─ 统计获取失败: {e}")


async def demo_config_management():
    """配置管理演示"""
    print("\n" + "=" * 60)
    print("⚙️ 配置管理演示")
    print("=" * 60)
    
    try:
        # 创建带配置管理器的引擎
        engine, config_manager = await RoutingEngineFactory.create_with_config_manager()
        
        # 获取当前配置
        config_result = await config_manager.get_current_config()
        if config_result["success"]:
            config = config_result["config"]
            print("📋 当前配置概览:")
            print(f"  ├─ 处理器数量: {len(config['handlers'])}")
            print(f"  ├─ 总关键词数: {config['total_keywords']}")
            print(f"  └─ 总模式数: {config['total_patterns']}")
            
            print("\n🏷️ 处理器详情:")
            for name, details in config["handlers"].items():
                print(f"  • {name}: {details['name']}")
                print(f"    ├─ 权重: {details['weight']}")
                print(f"    └─ 关键词: {details['keywords_count']} 个")
        
        # 测试查询匹配
        print("\n🔍 查询匹配测试:")
        test_queries = ["什么是AI", "你好", "/help", "计算123"]
        
        for query in test_queries:
            test_result = await config_manager.test_query_matching(query)
            if test_result["success"]:
                decision = test_result["decision"]
                print(f"  '{query}' -> {decision['handler_name']} (置信度: {decision['confidence']:.3f})")
            else:
                print(f"  '{query}' -> 测试失败: {test_result['error']}")
        
        # 配置验证
        print("\n✅ 配置验证:")
        validation = await config_manager.validate_config()
        if validation["success"]:
            result = validation["validation"]
            print(f"  ├─ 配置有效: {'是' if result['valid'] else '否'}")
            if result["issues"]:
                print(f"  ├─ 问题: {result['issues']}")
            if result["warnings"]:
                print(f"  └─ 警告: {result['warnings']}")
            else:
                print("  └─ 无警告")
        
    except Exception as e:
        print(f"❌ 配置管理演示失败: {e}")


async def demo_health_check():
    """健康检查演示"""
    print("\n" + "=" * 60)
    print("🏥 系统健康检查演示")
    print("=" * 60)
    
    try:
        # 创建引擎
        engine = await create_routing_engine(mode="keyword_only")
        
        # 执行健康检查
        health = await engine.health_check()
        
        print("🩺 路由引擎健康状态:")
        print(f"  ├─ 引擎状态: {health['engine_status']}")
        print(f"  ├─ 策略数量: {health['strategies_count']}")
        print(f"  ├─ 处理器数量: {health['handlers_count']}")
        print(f"  ├─ 规则数量: {health['rules_count']}")
        print(f"  └─ 已处理路由: {health['total_routes_processed']}")
        
        if "issues" in health:
            print(f"\n⚠️ 发现问题:")
            for issue in health["issues"]:
                print(f"  • {issue}")
        else:
            print(f"\n✅ 系统运行正常")
            
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")


async def main():
    """主演示函数"""
    print("🎯 Query Routing Engine 完整演示")
    print("=" * 80)
    
    try:
        # 1. 基础路由演示
        await demo_basic_routing()
        
        # 2. 增强版聊天服务演示
        await demo_enhanced_chat_service()
        
        # 3. 配置管理演示
        await demo_config_management()
        
        # 4. 健康检查演示
        await demo_health_check()
        
        print("\n" + "=" * 80)
        print("✅ 所有演示完成！")
        print("\n💡 提示:")
        print("  • 实际使用时需要配置OpenAI API密钥来启用LLM路由策略")
        print("  • 可以通过修改 config/routing/keywords.yaml 来自定义关键词规则")
        print("  • 支持热重载配置，无需重启服务")
        print("  • 所有操作都有详细的日志记录")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        logger.exception("演示失败")


if __name__ == "__main__":
    asyncio.run(main())