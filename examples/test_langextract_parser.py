"""Example demonstrating LangExtract document parser usage.

This script shows how to use the new LangExtract parser for document processing.

Setup:
    1. Install dependencies: pip install langextract
    2. Set API key: export LANGEXTRACT_API_KEY=your-api-key
    3. Configure parser type: export DOCUMENT_PARSER_TYPE=langextract
    4. Run: python examples/test_langextract_parser.py

References:
    - LangExtract GitHub: https://github.com/google/langextract
    - Gemini API Keys: https://aistudio.google.com/apikey
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_core.chains.loaders import load_document_content
from shared_config.settings import AppSettings


def test_langextract_parser():
    """Test the LangExtract parser with sample content."""
    
    print("=" * 80)
    print("🧪 测试 LangExtract 文档解析器")
    print("=" * 80)
    
    # Load settings
    settings = AppSettings()  # type: ignore[arg-type]
    
    # Check API Key availability based on provider
    provider = settings.document_parser.langextract_provider
    has_api_key = False
    
    if provider == "openrouter":
        # For OpenRouter, check both OPENROUTER_API_KEY and LANGEXTRACT_API_KEY
        has_api_key = bool(
            settings.document_parser.openrouter_api_key or 
            settings.document_parser.langextract_api_key
        )
    elif provider == "ollama":
        # Ollama doesn't need API key
        has_api_key = True
    else:
        # For other providers (gemini, openai), check LANGEXTRACT_API_KEY
        has_api_key = bool(settings.document_parser.langextract_api_key)
    
    print(f"\n📋 当前配置:")
    print(f"  ├─ 解析器类型: {settings.document_parser.parser_type}")
    print(f"  ├─ 模型: {settings.document_parser.langextract_model_id}")
    print(f"  ├─ Provider: {provider}")
    if settings.document_parser.langextract_base_url:
        print(f"  ├─ Base URL: {settings.document_parser.langextract_base_url}")
    print(f"  ├─ API Key: {'已配置 ✓' if has_api_key else '未配置 ✗'}")
    if provider == "openrouter" and has_api_key:
        if settings.document_parser.openrouter_api_key:
            print(f"  │  └─ 使用 OPENROUTER_API_KEY")
        elif settings.document_parser.langextract_api_key:
            print(f"  │  └─ 使用 LANGEXTRACT_API_KEY")
    print(f"  └─ 增强解析: {'启用 ✓' if settings.document_parser.enable_enhanced_parsing else '禁用 ✗'}")
    
    # Create sample document
    sample_content = """
# Research Paper: AI in Healthcare

## Abstract
This paper explores the application of artificial intelligence in modern healthcare systems.

## Introduction
Artificial Intelligence (AI) has revolutionized many industries, and healthcare is no exception.
Recent advances in machine learning and deep learning have enabled:

1. Improved diagnostic accuracy
2. Personalized treatment plans
3. Efficient resource allocation

## Methods
We conducted a comprehensive review of 150 peer-reviewed papers published between 2020-2024.

### Data Collection
Data was collected from multiple sources including:
- PubMed Central
- IEEE Xplore
- Google Scholar

## Results
Our analysis revealed that AI applications in healthcare have shown:
- 25% improvement in diagnostic accuracy
- 30% reduction in treatment time
- 40% increase in patient satisfaction

## Discussion
The results demonstrate significant potential for AI in healthcare, though challenges remain
in terms of data privacy, regulatory compliance, and clinical validation.

## Conclusion
AI represents a transformative force in healthcare, with promising applications across
diagnosis, treatment, and patient care management.
"""
    
    # Test with different file types
    test_cases = [
        (".txt", sample_content, "text/plain"),
        (".md", sample_content, "text/markdown"),
    ]
    
    for suffix, content, content_type in test_cases:
        print(f"\n" + "=" * 80)
        print(f"📄 测试文件类型: {suffix}")
        print("=" * 80)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Parse the document
            print(f"\n开始解析...")
            parsed_content = load_document_content(tmp_path, settings)
            
            print(f"\n" + "-" * 80)
            print("✅ 解析结果:")
            print("-" * 80)
            print(f"原始长度: {len(content)} 字符")
            print(f"解析后长度: {len(parsed_content)} 字符")
            print(f"\n前 500 字符:")
            print(parsed_content[:500])
            if len(parsed_content) > 500:
                print("...")
            print("-" * 80)
            
        except Exception as e:
            print(f"\n❌ 解析失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up
            tmp_path.unlink(missing_ok=True)
    
    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)


def test_basic_vs_langextract():
    """Compare basic parser vs LangExtract parser."""
    
    print("\n" + "=" * 80)
    print("🔄 对比测试: 基础解析器 vs LangExtract")
    print("=" * 80)
    
    sample_content = """
Product Review: Smart Watch Pro 2024

Overall Rating: ⭐⭐⭐⭐ (4/5)

Pros:
• Excellent battery life (5 days)
• Beautiful OLED display
• Accurate fitness tracking
• Water resistant (50m)

Cons:
• Limited app ecosystem
• Expensive ($399)
• No cellular connectivity

Verdict: A solid choice for fitness enthusiasts!
"""
    
    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.txt',
        delete=False,
        encoding='utf-8'
    ) as tmp_file:
        tmp_file.write(sample_content)
        tmp_path = Path(tmp_file.name)
    
    try:
        settings = AppSettings()  # type: ignore[arg-type]
        
        # Test basic parser
        print("\n📋 测试基础解析器...")
        settings.document_parser.parser_type = "default"
        basic_result = load_document_content(tmp_path, settings)
        
        # Test LangExtract parser
        print("\n🤖 测试 LangExtract 解析器...")
        settings.document_parser.parser_type = "langextract"
        langextract_result = load_document_content(tmp_path, settings)
        
        # Compare results
        print("\n" + "=" * 80)
        print("📊 对比结果:")
        print("=" * 80)
        print(f"\n基础解析器:")
        print(f"  长度: {len(basic_result)} 字符")
        print(f"  内容: {basic_result[:200]}...")
        
        print(f"\nLangExtract 解析器:")
        print(f"  长度: {len(langextract_result)} 字符")
        print(f"  内容: {langextract_result[:200]}...")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 对比测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tmp_path.unlink(missing_ok=True)


def show_configuration_guide():
    """Show configuration guide for LangExtract."""
    
    print("\n" + "=" * 80)
    print("📚 LangExtract 配置指南")
    print("=" * 80)
    
    guide = """
1. 安装依赖:
   pip install langextract

2. 获取 API Key:
   
   对于 Gemini (推荐):
   - 访问: https://aistudio.google.com/apikey
   - 创建新的 API Key
   
   对于 OpenAI:
   - 访问: https://platform.openai.com/api-keys
   - 创建新的 API Key

3. 配置环境变量 (.env 文件):
   
   # 启用 LangExtract 解析器
   DOCUMENT_PARSER_TYPE=langextract
   
   # Gemini 配置
   LANGEXTRACT_MODEL_ID=gemini-2.5-flash
   LANGEXTRACT_API_KEY=your-gemini-api-key-here
   LANGEXTRACT_PROVIDER=gemini
   PARSER_ENABLE_ENHANCED=true
   
   # 或使用 OpenAI
   LANGEXTRACT_MODEL_ID=gpt-4o
   LANGEXTRACT_API_KEY=your-openai-api-key-here
   LANGEXTRACT_PROVIDER=openai
   LANGEXTRACT_FENCE_OUTPUT=true
   LANGEXTRACT_USE_SCHEMA=false

4. 使用本地模型 (Ollama):
   
   DOCUMENT_PARSER_TYPE=langextract
   LANGEXTRACT_MODEL_ID=gemma2:2b
   LANGEXTRACT_PROVIDER=ollama
   # 不需要 API Key

5. 禁用 AI 增强（回退到基础解析器）:
   
   DOCUMENT_PARSER_TYPE=default
   PARSER_ENABLE_ENHANCED=false

功能特性:
✓ AI 驱动的智能文档理解
✓ 更好的结构化信息提取
✓ 表格和复杂格式处理
✓ 多语言支持
✓ 自动回退到基础解析器（如果失败）

支持的文档格式:
• PDF (.pdf)
• Word (.docx)
• 文本文件 (.txt, .md, .csv, .json, .log)
"""
    
    print(guide)
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test LangExtract document parser"
    )
    parser.add_argument(
        "--guide",
        action="store_true",
        help="Show configuration guide"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare basic vs LangExtract parser"
    )
    
    args = parser.parse_args()
    
    if args.guide:
        show_configuration_guide()
    elif args.compare:
        test_basic_vs_langextract()
    else:
        # Run basic test
        test_langextract_parser()
        
        # Show guide at the end
        print("\n💡 提示: 运行 'python examples/test_langextract_parser.py --guide' 查看完整配置指南")

