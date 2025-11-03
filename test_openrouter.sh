#!/bin/bash
# OpenRouter Embedding 测试脚本

set -e

echo "🔍 OpenRouter Embedding 测试"
echo "========================================"

# 检查 .env 文件或环境变量
if [ -f ".env" ]; then
    echo "✅ 找到 .env 文件，测试将自动读取配置"
    # 从 .env 中读取 API key 用于显示（可选）
    if grep -q "OPENROUTER_API_KEY" .env; then
        echo "✅ .env 中已配置 OPENROUTER_API_KEY"
    else
        echo "⚠️  .env 中未找到 OPENROUTER_API_KEY，测试将被跳过"
    fi
elif [ -n "$OPENROUTER_API_KEY" ]; then
    echo "✅ 环境变量中已设置 OPENROUTER_API_KEY"
else
    echo ""
    echo "⚠️  既没有 .env 文件，也没有设置环境变量"
    echo ""
    echo "请选择以下方式之一："
    echo "  1. 创建 .env 文件并添加："
    echo "     OPENROUTER_API_KEY=sk-or-v1-your-key-here"
    echo ""
    echo "  2. 或设置环境变量："
    echo "     export OPENROUTER_API_KEY=sk-or-v1-your-key-here"
    echo ""
    read -p "是否继续运行（测试将被跳过）？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 确保使用项目虚拟环境
echo "1️⃣  检查虚拟环境..."
if [ ! -f ".venv/bin/python" ]; then
    echo "❌ .venv 不存在，请先运行: make install"
    exit 1
fi

echo "✅ 使用 .venv 环境"
echo ""

# 显示环境信息
echo ""
echo "2️⃣  环境信息:"
echo "   Python: $(.venv/bin/python --version)"
echo "   Pytest: $(.venv/bin/pytest --version | head -n 1)"
echo ""

# 运行测试
echo "3️⃣  运行测试..."
echo "========================================"
echo ""

.venv/bin/pytest packages/rag-core/tests/test_openrouter_embeddings.py -v -s "$@"

echo ""
echo "========================================"
echo "✅ 测试完成！"

