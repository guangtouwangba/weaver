#!/bin/bash
# 修复 Python 版本问题
# 删除旧的虚拟环境并使用 Python 3.11+ 重新创建

set -e

echo "🔧 修复 Python 版本问题..."

# 查找 Python 3.11 或更高版本
PYTHON_CMD=""
for py in python3.12 python3.11 python3; do
    if command -v $py >/dev/null 2>&1; then
        VERSION=$($py --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 11 ]; then
            PYTHON_CMD=$py
            echo "✅ 找到 Python $VERSION: $py"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 错误: 未找到 Python 3.11 或更高版本"
    echo "   请安装 Python 3.11+: brew install python@3.11"
    exit 1
fi

# 删除旧的虚拟环境
if [ -d "venv" ]; then
    echo "🗑️  删除旧的虚拟环境..."
    rm -rf venv
fi

# 创建新的虚拟环境
echo "🐍 使用 $PYTHON_CMD 创建新的虚拟环境..."
$PYTHON_CMD -m venv venv

# 验证虚拟环境中的 Python 版本
VENV_PYTHON_VER=$(venv/bin/python3 --version 2>&1 | awk '{print $2}')
echo "✅ 虚拟环境创建成功，Python 版本: $VENV_PYTHON_VER"

echo ""
echo "✅ 修复完成！现在可以运行: make install-backend"
