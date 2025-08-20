"""
基础使用示例

展示如何使用新的模块化API进行基本的文档处理和搜索。
"""

import asyncio
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_example():
    """基础使用示例"""
    
    # 导入模块化API
    from modules import SimpleAPI
    
    # 创建API实例
    api = SimpleAPI()
    
    print("=== 模块化RAG系统 - 基础使用示例 ===\n")
    
    # 1. 处理单个文件
    print("1. 处理单个文件:")
    
    # 创建测试文件
    test_file = "test_document.txt"
    test_content = """
    这是一个测试文档。
    
    文档包含多个段落，用于演示文档处理功能。
    系统会将这个文档分割成多个块，以便进行高效的搜索和检索。
    
    模块化架构使得系统更加灵活和易于维护。
    每个模块都有明确的职责，可以独立开发和测试。
    """
    
    # 写入测试文件
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        # 处理文件
        result = await api.process_file(
            file_path=test_file,
            chunking_strategy="paragraph",  # 使用段落分块
            chunk_size=500,
            generate_embeddings=True
        )
        
        print(f"  ✓ 处理成功: {result['success']}")
        print(f"  ✓ 文档ID: {result['document_id']}")
        print(f"  ✓ 创建块数: {result['chunks_created']}")
        print(f"  ✓ 处理时间: {result['processing_time_ms']:.2f}ms")
        
    except Exception as e:
        print(f"  ✗ 处理失败: {e}")
        return
    
    print()
    
    # 2. 搜索文档
    print("2. 搜索文档:")
    
    try:
        search_result = await api.search(
            query="模块化架构",
            limit=5
        )
        
        print(f"  ✓ 搜索查询: {search_result['query']}")
        print(f"  ✓ 找到结果: {len(search_result['results'])}")
        print(f"  ✓ 搜索时间: {search_result['search_time_ms']:.2f}ms")
        
        for i, result in enumerate(search_result['results']):
            print(f"    结果 {i+1}:")
            print(f"      内容: {result['content'][:100]}...")
            print(f"      分数: {result['score']:.3f}")
            print()
    
    except Exception as e:
        print(f"  ✗ 搜索失败: {e}")
    
    # 3. 获取文档信息
    print("3. 获取文档信息:")
    
    try:
        document_id = result['document_id']
        doc_info = await api.get_document(document_id)
        
        if doc_info:
            print(f"  ✓ 文档标题: {doc_info['title']}")
            print(f"  ✓ 内容类型: {doc_info['content_type']}")
            print(f"  ✓ 文件大小: {doc_info['file_size']} 字节")
            print(f"  ✓ 创建时间: {doc_info['created_at']}")
        else:
            print("  ✗ 文档未找到")
    
    except Exception as e:
        print(f"  ✗ 获取文档信息失败: {e}")
    
    print()
    
    # 4. 获取文档块
    print("4. 获取文档块:")
    
    try:
        chunks = await api.get_document_chunks(document_id)
        
        print(f"  ✓ 找到 {len(chunks)} 个文档块:")
        
        for i, chunk in enumerate(chunks):
            print(f"    块 {i+1}:")
            print(f"      索引: {chunk['chunk_index']}")
            print(f"      大小: {chunk['chunk_size']} 字符")
            print(f"      内容预览: {chunk['content'][:50]}...")
            print()
    
    except Exception as e:
        print(f"  ✗ 获取文档块失败: {e}")
    
    # 5. 获取系统状态
    print("5. 获取系统状态:")
    
    try:
        status = await api.get_status()
        
        print(f"  ✓ API状态: {status['api']['name']}")
        print(f"  ✓ 初始化状态: {status['api']['initialized']}")
        print(f"  ✓ 缓存启用: {status['api']['caching_enabled']}")
        print(f"  ✓ 整体状态: {status['components']['overall_status']}")
    
    except Exception as e:
        print(f"  ✗ 获取状态失败: {e}")
    
    print()
    
    # 6. 获取支持的格式
    print("6. 支持的文件格式:")
    
    try:
        formats = await api.get_supported_formats()
        print(f"  ✓ 支持的格式: {', '.join(formats)}")
    
    except Exception as e:
        print(f"  ✗ 获取支持格式失败: {e}")
    
    # 清理测试文件
    try:
        Path(test_file).unlink()
        print(f"\n✓ 清理测试文件: {test_file}")
    except:
        pass
    
    print("\n=== 示例完成 ===")


async def batch_processing_example():
    """批量处理示例"""
    
    from modules import SimpleAPI
    
    print("\n=== 批量处理示例 ===\n")
    
    api = SimpleAPI()
    
    # 创建多个测试文件
    test_files = []
    test_contents = [
        "这是第一个文档，包含关于人工智能的内容。",
        "第二个文档讨论机器学习的基础概念。",
        "第三个文档专注于深度学习和神经网络。"
    ]
    
    for i, content in enumerate(test_contents):
        filename = f"test_doc_{i+1}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        test_files.append(filename)
    
    print(f"创建了 {len(test_files)} 个测试文件")
    
    try:
        # 批量处理文件
        print("\n批量处理文件:")
        
        results = await api.process_files(
            file_paths=test_files,
            chunking_strategy="sentence",
            chunk_size=200,
            max_concurrent=2  # 限制并发数
        )
        
        success_count = sum(1 for r in results if r.get('success', False))
        print(f"  ✓ 处理完成: {success_count}/{len(results)} 成功")
        
        for i, result in enumerate(results):
            if result.get('success'):
                print(f"    文件 {i+1}: ✓ 成功 (文档ID: {result.get('document_id', 'N/A')})")
            else:
                print(f"    文件 {i+1}: ✗ 失败 ({result.get('error', 'Unknown error')})")
        
        # 批量搜索测试
        print("\n批量搜索测试:")
        
        search_queries = ["人工智能", "机器学习", "深度学习"]
        
        for query in search_queries:
            search_result = await api.search(query, limit=3)
            print(f"  查询 '{query}': 找到 {len(search_result['results'])} 个结果")
    
    except Exception as e:
        print(f"批量处理失败: {e}")
    
    finally:
        # 清理测试文件
        for filename in test_files:
            try:
                Path(filename).unlink()
            except:
                pass
        print(f"\n✓ 清理了 {len(test_files)} 个测试文件")
    
    print("\n=== 批量处理示例完成 ===")


if __name__ == "__main__":
    # 运行基础示例
    asyncio.run(basic_example())
    
    # 运行批量处理示例
    asyncio.run(batch_processing_example())
