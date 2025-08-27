#!/usr/bin/env python3
"""
Semantic Router Integration Example

演示如何使用集成的 semantic-router 库进行语义路由。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict, Any
from config.settings import AppConfig
from modules.routing.factory import RoutingEngineFactory, create_routing_engine


async def example_basic_semantic_routing():
    """基础语义路由示例"""
    print("=== 基础语义路由示例 ===")
    
    # 创建语义路由配置
    semantic_config = {
        "enabled": True,
        "encoder_type": "fastembed",
        "fastembed_model": "BAAI/bge-small-en-v1.5",
        "threshold": 0.5,
        "top_k": 1,
        "routes_config_file": "config/routing/semantic_routes.yaml"
    }
    
    try:
        # 创建语义路由引擎
        engine = await create_routing_engine(
            mode="semantic_router",
            semantic_config=semantic_config
        )
        
        print("✅ 语义路由引擎创建成功")
        
        # 测试查询
        test_queries = [
            "搜索文档中关于Python的内容",
            "总结一下这个文档",
            "你好，早上好",
            "系统状态如何",
            "调用工具处理数据"
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            
            # 执行路由决策
            result = await engine.route_query(query, {})
            
            print(f"  路由结果: {result.decision.handler_name}")
            print(f"  置信度: {result.decision.confidence:.3f}")
            print(f"  策略: {result.decision.metadata.get('strategy', 'unknown')}")
            
            if 'route_name' in result.decision.metadata:
                print(f"  匹配路由: {result.decision.metadata['route_name']}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")


async def example_custom_semantic_routes():
    """自定义语义路由示例"""
    print("\n=== 自定义语义路由示例 ===")
    
    # 自定义路由配置
    custom_routes = [
        {
            "name": "weather_query",
            "handler": "weather_handler",
            "utterances": [
                "今天天气怎么样",
                "明天会下雨吗",
                "气温多少度",
                "weather forecast",
                "what's the temperature",
                "will it rain tomorrow"
            ]
        },
        {
            "name": "joke_request", 
            "handler": "joke_handler",
            "utterances": [
                "讲个笑话",
                "来个段子",
                "逗我笑笑",
                "tell me a joke",
                "make me laugh",
                "something funny"
            ]
        }
    ]
    
    semantic_config = {
        "enabled": True,
        "encoder_type": "fastembed",
        "threshold": 0.6,
        "top_k": 1
    }
    
    try:
        # 使用自定义路由创建引擎
        engine = await RoutingEngineFactory.create_semantic_router_engine(
            semantic_config=semantic_config
        )
        
        # 注入自定义路由（需要重新创建strategy）
        from modules.routing.strategies.semantic_router_strategy import SemanticRouterStrategy
        
        custom_strategy = SemanticRouterStrategy(
            encoder_type="fastembed",
            routes_config=custom_routes,
            threshold=0.6
        )
        await custom_strategy.initialize()
        
        # 重新注册策略
        engine.register_strategy("semantic_router", custom_strategy)
        
        print("✅ 自定义语义路由引擎创建成功")
        
        # 测试自定义路由
        custom_queries = [
            "今天北京天气怎么样？",
            "讲个笑话逗我开心",
            "明天会下雨吗？",
            "tell me something funny",
            "what's the weather like"
        ]
        
        for query in custom_queries:
            print(f"\n查询: {query}")
            
            result = await engine.route_query(query, {})
            
            print(f"  路由结果: {result.decision.handler_name}")
            print(f"  置信度: {result.decision.confidence:.3f}")
            
            if 'route_name' in result.decision.metadata:
                print(f"  匹配路由: {result.decision.metadata['route_name']}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")


async def example_encoder_comparison():
    """不同编码器性能比较示例"""
    print("\n=== 编码器性能比较示例 ===")
    
    # 测试不同编码器
    encoders = [
        {"type": "fastembed", "model": "BAAI/bge-small-en-v1.5"},
        # 注意：下面的编码器需要相应的API密钥
        # {"type": "openai", "model": "text-embedding-3-small"},
        # {"type": "cohere", "model": "embed-multilingual-v3.0"}
    ]
    
    test_query = "搜索文档中关于机器学习的内容"
    
    for encoder_info in encoders:
        print(f"\n--- 测试编码器: {encoder_info['type']} ---")
        
        semantic_config = {
            "enabled": True,
            "encoder_type": encoder_info["type"],
            "threshold": 0.5,
            "routes_config_file": "config/routing/semantic_routes.yaml"
        }
        
        # 添加模型配置
        if encoder_info["type"] == "fastembed":
            semantic_config["fastembed_model"] = encoder_info["model"]
        elif encoder_info["type"] == "openai":
            semantic_config["encoder_model"] = encoder_info["model"]
            # 需要设置 OPENAI_API_KEY 环境变量
            if not os.getenv("OPENAI_API_KEY"):
                print("  ⚠️  需要设置 OPENAI_API_KEY 环境变量")
                continue
        
        try:
            import time
            start_time = time.time()
            
            engine = await create_routing_engine(
                mode="semantic_router",
                semantic_config=semantic_config
            )
            
            result = await engine.route_query(test_query, {})
            
            end_time = time.time()
            
            print(f"  ✅ 路由结果: {result.decision.handler_name}")
            print(f"  ⏱️  处理时间: {(end_time - start_time)*1000:.2f}ms")
            print(f"  📊 置信度: {result.decision.confidence:.3f}")
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")


async def example_with_app_config():
    """使用应用配置的语义路由示例"""
    print("\n=== 使用应用配置示例 ===")
    
    try:
        # 加载应用配置
        config = AppConfig()
        
        print("当前配置:")
        print(f"  默认策略: {config.route_strategy.default_strategy}")
        print(f"  Semantic Router 启用: {config.semantic_router.enabled}")
        print(f"  编码器类型: {config.semantic_router.encoder_type}")
        print(f"  阈值: {config.semantic_router.threshold}")
        
        if config.semantic_router.enabled:
            # 使用配置创建引擎
            semantic_config = {
                "enabled": config.semantic_router.enabled,
                "encoder_type": config.semantic_router.encoder_type,
                "threshold": config.semantic_router.threshold,
                "top_k": config.semantic_router.top_k,
                "routes_config_file": config.semantic_router.routes_config_file
            }
            
            # 添加API密钥（如果配置了）
            if config.semantic_router.openai_api_key:
                semantic_config["openai_api_key"] = config.semantic_router.openai_api_key
            if config.semantic_router.cohere_api_key:
                semantic_config["cohere_api_key"] = config.semantic_router.cohere_api_key
            
            # 添加模型配置
            if config.semantic_router.encoder_type == "fastembed":
                semantic_config["fastembed_model"] = config.semantic_router.fastembed_model
            elif config.semantic_router.encoder_type == "huggingface":
                semantic_config["huggingface_model"] = config.semantic_router.huggingface_model
            
            engine = await create_routing_engine(
                mode=config.route_strategy.default_strategy if config.route_strategy.default_strategy == "semantic_router" else "default",
                semantic_config=semantic_config
            )
            
            # 测试查询
            result = await engine.route_query("搜索相关文档信息", {})
            print(f"\n✅ 路由测试成功: {result.decision.handler_name}")
        else:
            print("  ℹ️  Semantic Router 未启用，使用默认路由策略")
            
    except Exception as e:
        print(f"❌ 错误: {e}")


async def example_route_info():
    """路由信息查看示例"""
    print("\n=== 路由信息查看示例 ===")
    
    semantic_config = {
        "enabled": True,
        "encoder_type": "fastembed",
        "routes_config_file": "config/routing/semantic_routes.yaml"
    }
    
    try:
        engine = await create_routing_engine(
            mode="semantic_router",
            semantic_config=semantic_config
        )
        
        # 获取策略信息
        strategy = engine.strategies.get("semantic_router")
        if strategy and hasattr(strategy, 'get_route_info'):
            info = strategy.get_route_info()
            
            print("语义路由策略信息:")
            print(f"  策略名称: {info['strategy_name']}")
            print(f"  编码器类型: {info['encoder_type']}")
            print(f"  阈值: {info['threshold']}")
            print(f"  路由数量: {info['routes_count']}")
            
            print("\n可用路由:")
            for route in info['routes']:
                print(f"  - {route['name']}: {route['handler']} ({route['utterances_count']} 个示例)")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


async def main():
    """主函数"""
    print("🚀 Semantic Router 集成示例")
    print("=" * 50)
    
    # 检查依赖
    try:
        import semantic_router
        print(f"✅ semantic-router 版本: {semantic_router.__version__}")
    except ImportError:
        print("❌ semantic-router 未安装")
        print("请运行: uv add semantic-router 或 pip install semantic-router")
        return
    
    # 运行示例
    examples = [
        example_basic_semantic_routing,
        example_custom_semantic_routes,
        example_encoder_comparison,
        example_with_app_config,
        example_route_info
    ]
    
    for example_func in examples:
        try:
            await example_func()
            await asyncio.sleep(1)  # 短暂等待
        except KeyboardInterrupt:
            print("\n⏹️  用户中断")
            break
        except Exception as e:
            print(f"❌ 示例执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✅ 示例执行完成")


if __name__ == "__main__":
    asyncio.run(main())