"""诊断 LangExtract 配置脚本

这个脚本帮助你快速检查 LangExtract 的配置是否正确。

使用方法:
    python examples/diagnose_langextract_config.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared_config.settings import AppSettings


def check_env_file():
    """检查 .env 文件是否存在"""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env 文件存在")
        return True
    else:
        print("❌ .env 文件不存在")
        print("   请创建 .env 文件并配置必要的环境变量")
        return False


def check_api_key(provider: str):
    """检查 API Key 配置"""
    print(f"\n🔑 检查 API Key 配置 (Provider: {provider})...")
    
    if provider == "openrouter":
        # Check OPENROUTER_API_KEY
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        langextract_key = os.getenv("LANGEXTRACT_API_KEY")
        
        if openrouter_key:
            print(f"✅ OPENROUTER_API_KEY 已设置")
            print(f"   值: {openrouter_key[:15]}...{openrouter_key[-4:]}")
            return True
        elif langextract_key:
            print(f"✅ LANGEXTRACT_API_KEY 已设置")
            print(f"   值: {langextract_key[:15]}...{langextract_key[-4:]}")
            return True
        else:
            print(f"❌ 未找到 API Key")
            print(f"   请在 .env 文件中设置:")
            print(f"   OPENROUTER_API_KEY=sk-or-v1-your-key-here")
            print(f"   或")
            print(f"   LANGEXTRACT_API_KEY=sk-or-v1-your-key-here")
            return False
    
    elif provider == "gemini":
        key = os.getenv("LANGEXTRACT_API_KEY")
        if key:
            print(f"✅ LANGEXTRACT_API_KEY 已设置")
            print(f"   值: {key[:15]}...{key[-4:]}")
            return True
        else:
            print(f"❌ 未找到 LANGEXTRACT_API_KEY")
            print(f"   请在 .env 文件中设置:")
            print(f"   LANGEXTRACT_API_KEY=your-gemini-api-key")
            return False
    
    elif provider == "openai":
        key = os.getenv("LANGEXTRACT_API_KEY")
        if key:
            print(f"✅ LANGEXTRACT_API_KEY 已设置")
            print(f"   值: {key[:15]}...{key[-4:]}")
            return True
        else:
            print(f"❌ 未找到 LANGEXTRACT_API_KEY")
            print(f"   请在 .env 文件中设置:")
            print(f"   LANGEXTRACT_API_KEY=your-openai-api-key")
            return False
    
    elif provider == "ollama":
        print(f"✅ Ollama 不需要 API Key")
        return True
    
    else:
        print(f"⚠️  未知的 Provider: {provider}")
        return False


def check_langextract_installed():
    """检查 langextract 是否已安装"""
    print("\n📦 检查依赖...")
    try:
        import langextract
        print(f"✅ langextract 已安装 (版本: {langextract.__version__ if hasattr(langextract, '__version__') else '未知'})")
        return True
    except ImportError:
        print(f"❌ langextract 未安装")
        print(f"   请运行: pip install langextract")
        return False


def diagnose():
    """运行完整诊断"""
    print("=" * 80)
    print("🔍 LangExtract 配置诊断")
    print("=" * 80)
    
    # Check .env file
    has_env = check_env_file()
    
    # Check langextract installation
    has_langextract = check_langextract_installed()
    
    # Load settings
    print("\n⚙️  加载配置...")
    try:
        settings = AppSettings()  # type: ignore[arg-type]
        print("✅ 配置加载成功")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return
    
    # Display configuration
    print("\n📋 当前配置:")
    print(f"  解析器类型: {settings.document_parser.parser_type}")
    print(f"  Provider: {settings.document_parser.langextract_provider}")
    print(f"  模型: {settings.document_parser.langextract_model_id}")
    
    if settings.document_parser.langextract_base_url:
        print(f"  Base URL: {settings.document_parser.langextract_base_url}")
    
    print(f"  Fence Output: {settings.document_parser.langextract_fence_output}")
    print(f"  Use Schema: {settings.document_parser.langextract_use_schema}")
    print(f"  增强解析: {settings.document_parser.enable_enhanced_parsing}")
    
    # Check API Key
    provider = settings.document_parser.langextract_provider
    has_key = check_api_key(provider)
    
    # Check OpenRouter specific settings
    if provider == "openrouter":
        print("\n🌐 OpenRouter 配置:")
        site_url = os.getenv("OPENROUTER_SITE_URL")
        site_name = os.getenv("OPENROUTER_SITE_NAME")
        
        if site_url:
            print(f"  ✅ OPENROUTER_SITE_URL: {site_url}")
        else:
            print(f"  ⚠️  OPENROUTER_SITE_URL 未设置 (可选，但推荐)")
        
        if site_name:
            print(f"  ✅ OPENROUTER_SITE_NAME: {site_name}")
        else:
            print(f"  ⚠️  OPENROUTER_SITE_NAME 未设置 (可选，但推荐)")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 诊断总结")
    print("=" * 80)
    
    all_good = has_env and has_langextract and has_key
    
    if all_good:
        print("✅ 所有检查通过！你可以开始使用 LangExtract 了")
        print("\n下一步:")
        print("  1. 运行测试: python examples/test_langextract_parser.py")
        print("  2. 上传文档测试实际解析效果")
    else:
        print("❌ 发现问题，请根据上面的提示进行修复")
        print("\n需要修复:")
        if not has_env:
            print("  - 创建 .env 文件")
        if not has_langextract:
            print("  - 安装 langextract: pip install langextract")
        if not has_key:
            print("  - 配置 API Key")
    
    print("\n" + "=" * 80)
    
    # Provider specific quick start
    if provider == "openrouter":
        print("\n💡 OpenRouter 快速配置:")
        print("=" * 80)
        print("在 .env 文件中添加:")
        print("")
        print("OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        print("LANGEXTRACT_PROVIDER=openrouter")
        print("LANGEXTRACT_MODEL_ID=anthropic/claude-3-haiku")
        print("DOCUMENT_PARSER_TYPE=langextract")
        print("PARSER_ENABLE_ENHANCED=true")
        print("")
        print("获取 API Key: https://openrouter.ai/keys")
        print("=" * 80)
    
    elif provider == "gemini":
        print("\n💡 Gemini 快速配置:")
        print("=" * 80)
        print("在 .env 文件中添加:")
        print("")
        print("LANGEXTRACT_API_KEY=your-gemini-api-key")
        print("LANGEXTRACT_PROVIDER=gemini")
        print("LANGEXTRACT_MODEL_ID=gemini-2.5-flash")
        print("DOCUMENT_PARSER_TYPE=langextract")
        print("PARSER_ENABLE_ENHANCED=true")
        print("")
        print("获取 API Key: https://aistudio.google.com/apikey")
        print("=" * 80)
    
    elif provider == "ollama":
        print("\n💡 Ollama 快速配置:")
        print("=" * 80)
        print("1. 安装 Ollama:")
        print("   curl -fsSL https://ollama.com/install.sh | sh")
        print("")
        print("2. 下载模型:")
        print("   ollama pull gemma2:2b")
        print("")
        print("3. 启动服务:")
        print("   ollama serve")
        print("")
        print("4. 在 .env 文件中配置:")
        print("   LANGEXTRACT_PROVIDER=ollama")
        print("   LANGEXTRACT_MODEL_ID=gemma2:2b")
        print("   DOCUMENT_PARSER_TYPE=langextract")
        print("=" * 80)


if __name__ == "__main__":
    diagnose()

