"""
兼容性示例

展示如何使用兼容层保持与原有API的兼容性。
"""

import asyncio
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def compatibility_example():
    """兼容性使用示例"""
    
    # 导入兼容层
    from modules import APIAdapter
    
    print("=== API兼容层示例 ===\n")
    
    # 创建API适配器
    adapter = APIAdapter()
    
    # 创建测试文件
    test_file = "compat_test.txt"
    test_content = """
    这是一个兼容性测试文档。
    
    通过API适配器，原有的调用方式仍然可以正常工作。
    这确保了系统升级的平滑过渡。
    """
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        # 1. 模拟原有的文件上传确认流程
        print("1. 文件上传确认（原有接口）:")
        
        upload_result = await adapter.confirm_upload_completion(
            file_id="test_file_123",
            file_path=test_file,
            metadata={"source": "compatibility_test", "version": "1.0"}
        )
        
        print(f"  ✓ 文件ID: {upload_result['file_id']}")
        print(f"  ✓ 状态: {upload_result['status']}")
        print(f"  ✓ 文档ID: {upload_result.get('document_id', 'N/A')}")
        print(f"  ✓ 处理时间: {upload_result.get('processing_time', 0)}ms")
        print(f"  ✓ 创建块数: {upload_result.get('chunks_created', 0)}")
        print(f"  ✓ 消息: {upload_result['message']}")
        
        print()
        
        # 2. 使用原有的知识库搜索接口
        print("2. 知识库搜索（原有接口）:")
        
        search_result = await adapter.search_knowledge(
            query="兼容性",
            limit=5,
            filters={"source": "compatibility_test"}
        )
        
        print(f"  ✓ 查询: {search_result['query']}")
        print(f"  ✓ 状态: {search_result['status']}")
        print(f"  ✓ 结果数量: {len(search_result['results'])}")
        print(f"  ✓ 总数: {search_result['total']}")
        print(f"  ✓ 搜索时间: {search_result['search_time']}ms")
        
        if search_result['results']:
            for i, result in enumerate(search_result['results']):
                print(f"    结果 {i+1}:")
                print(f"      ID: {result['id']}")
                print(f"      分数: {result['score']:.3f}")
                print(f"      内容: {result['content'][:50]}...")
                print()
        
        # 3. 获取文档信息（原有接口）
        print("3. 获取文档信息（原有接口）:")
        
        if upload_result.get('document_id'):
            doc_info = await adapter.get_document_info(upload_result['document_id'])
            
            if doc_info:
                print(f"  ✓ 文档ID: {doc_info['id']}")
                print(f"  ✓ 标题: {doc_info['title']}")
                print(f"  ✓ 内容类型: {doc_info['content_type']}")
                print(f"  ✓ 状态: {doc_info['status']}")
                print(f"  ✓ 创建时间: {doc_info['created_at']}")
            else:
                print("  ✗ 文档未找到")
        
        print()
        
        # 4. 主题管理（原有接口）
        print("4. 主题管理（原有接口）:")
        
        topic_result = await adapter.create_topic(
            title="兼容性测试主题",
            description="用于测试API兼容性的主题",
            metadata={"test": True}
        )
        
        print(f"  ✓ 主题ID: {topic_result['id']}")
        print(f"  ✓ 标题: {topic_result['title']}")
        print(f"  ✓ 状态: {topic_result['status']}")
        print(f"  ✓ 创建时间: {topic_result['created_at']}")
        print(f"  ✓ 消息: {topic_result['message']}")
        
        # 获取主题下的文档
        topic_docs = await adapter.get_topic_documents(topic_result['id'])
        print(f"  ✓ 主题文档数量: {len(topic_docs)}")
        
        print()
        
        # 5. 系统健康检查（原有接口）
        print("5. 系统健康检查（原有接口）:")
        
        health = await adapter.get_system_health()
        
        print(f"  ✓ 系统状态: {health['status']}")
        print(f"  ✓ 检查时间: {health['timestamp']}")
        
        print("  组件状态:")
        for component, status in health['components'].items():
            if isinstance(status, dict):
                comp_status = status.get('status', 'unknown')
                print(f"    {component}: {comp_status}")
        
        print("  系统指标:")
        metrics = health.get('metrics', {})
        for metric, value in metrics.items():
            print(f"    {metric}: {value}")
        
        print()
        
        # 6. 获取支持的文件类型（原有接口）
        print("6. 支持的文件类型（原有接口）:")
        
        file_types = await adapter.get_supported_file_types()
        print(f"  ✓ 支持的MIME类型:")
        for file_type in file_types:
            print(f"    - {file_type}")
        
        print()
        
        # 7. 删除文档（原有接口）
        print("7. 删除文档（原有接口）:")
        
        if upload_result.get('document_id'):
            delete_result = await adapter.delete_document_by_id(upload_result['document_id'])
            
            print(f"  ✓ 文档ID: {delete_result['document_id']}")
            print(f"  ✓ 删除状态: {delete_result['status']}")
            print(f"  ✓ 成功: {delete_result['success']}")
            print(f"  ✓ 消息: {delete_result['message']}")
    
    except Exception as e:
        print(f"兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        try:
            Path(test_file).unlink()
            print(f"\n✓ 清理测试文件: {test_file}")
        except:
            pass
    
    print("\n=== 兼容层示例完成 ===")


async def migration_example():
    """迁移示例：展示如何从原有API逐步迁移到新API"""
    
    print("\n=== 迁移示例：从原有API到新API ===\n")
    
    # 创建测试文件
    test_file = "migration_test.txt"
    test_content = "这是一个迁移测试文档，用于演示API迁移过程。"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("步骤1: 使用原有API（通过兼容层）")
    
    # 原有API方式
    from modules import APIAdapter
    
    adapter = APIAdapter()
    
    old_result = await adapter.confirm_upload_completion(
        file_id="migration_test",
        file_path=test_file
    )
    
    print(f"  原有API结果: {old_result['status']}")
    
    print("\n步骤2: 使用新的模块化API")
    
    # 新API方式
    from modules import SimpleAPI
    
    api = SimpleAPI()
    
    new_result = await api.process_file(
        file_path=test_file,
        chunking_strategy="fixed_size",
        chunk_size=500
    )
    
    print(f"  新API结果: {'成功' if new_result['success'] else '失败'}")
    
    print("\n步骤3: 对比结果")
    
    print("  原有API特点:")
    print("    - 基于事件驱动")
    print("    - 复杂的DDD架构") 
    print("    - 需要深入了解内部结构")
    
    print("  新API特点:")
    print("    - 简单直观的接口")
    print("    - 模块化设计")
    print("    - 更好的错误处理")
    print("    - 内置性能优化")
    
    print("\n迁移建议:")
    print("  1. 首先通过兼容层验证功能")
    print("  2. 逐步替换为新API调用")
    print("  3. 利用新API的高级功能")
    print("  4. 最终移除兼容层依赖")
    
    # 清理
    try:
        Path(test_file).unlink()
    except:
        pass
    
    print("\n=== 迁移示例完成 ===")


if __name__ == "__main__":
    # 运行兼容性示例
    asyncio.run(compatibility_example())
    
    # 运行迁移示例
    asyncio.run(migration_example())
