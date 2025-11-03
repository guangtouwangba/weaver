#!/bin/bash
# 快速创建 .env 配置文件

echo "🔧 创建 .env 配置文件..."

# 检查是否已存在 .env 文件
if [ -f ".env" ]; then
    echo "⚠️  .env 文件已存在！"
    read -p "是否覆盖？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消操作"
        exit 1
    fi
    echo "🗑️  删除旧文件..."
    rm .env
fi

# 复制模板文件
if [ -f "env.example" ]; then
    echo "📋 从 env.example 复制配置..."
    cp env.example .env
else
    echo "❌ 错误: env.example 文件不存在"
    exit 1
fi

echo "✅ .env 文件创建成功！"
echo ""
echo "📝 接下来的步骤："
echo "   1. 编辑 .env 文件，设置你的 API key"
echo "   2. 运行 'python debug_settings.py' 验证配置"
echo ""
echo "💡 提示："
echo "   - 使用 fake embedding (默认): 不需要设置 API key"
echo "   - 使用 OpenAI: 设置 OPENAI_API_KEY"
echo "   - 使用 OpenRouter: 设置 OPENROUTER_API_KEY"
echo ""
echo "🔗 获取 API Keys:"
echo "   - OpenRouter: https://openrouter.ai/keys"
echo "   - OpenAI: https://platform.openai.com/api-keys"

