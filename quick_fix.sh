#!/bin/bash
# 一键修复环境和运行测试

set -e

echo "🔧 快速修复脚本"
echo "=========================================="

# 检查 .venv 是否存在
if [ ! -d ".venv" ]; then
    echo "❌ .venv 不存在，正在创建..."
    uv venv .venv
fi

# 激活虚拟环境
echo "✅ 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
uv pip install -e .

# 验证关键依赖
echo ""
echo "🔍 验证依赖安装..."
python -c "import langgraph; print('✅ langgraph:', langgraph.__version__)"
python -c "import langchain; print('✅ langchain:', langchain.__version__)"
python -c "import langchain_community; print('✅ langchain_community: OK')"
python -c "import langchain_openai; print('✅ langchain_openai: OK')"

# 创建 .env 文件（如果不存在）
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 创建 .env 配置文件..."
    cp env.example .env
    echo "✅ .env 文件已创建（使用默认配置）"
fi

echo ""
echo "=========================================="
echo "✅ 环境修复完成！"
echo ""
echo "🚀 运行测试:"
echo "   pytest packages/rag-core/tests/ -v"
echo ""
echo "或使用 Makefile:"
echo "   make test"
echo ""
echo "=========================================="

# 运行测试
echo ""
read -p "是否立即运行测试？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧪 运行测试..."
    pytest packages/rag-core/tests/ -v
fi

