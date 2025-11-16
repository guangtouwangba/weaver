#!/bin/bash
# Git 清理脚本 - 移除不应追踪的文件

set -e

echo "🧹 清理 Git 仓库中的构建产物..."
echo ""

# 移除 .egg-info 目录
echo "📦 移除 .egg-info 目录..."
if git ls-files | grep -q "egg-info"; then
    git rm -r --cached knowledge_platform_monorepo.egg-info/ 2>/dev/null || true
    git rm -r --cached "*.egg-info" 2>/dev/null || true
    echo "✅ .egg-info 目录已从 git 追踪中移除"
else
    echo "ℹ️  .egg-info 未被追踪"
fi

# 移除 __pycache__ 目录
echo ""
echo "🗂️  移除 __pycache__ 目录..."
if git ls-files | grep -q "__pycache__"; then
    find . -type d -name "__pycache__" | while read dir; do
        git rm -r --cached "$dir" 2>/dev/null || true
    done
    echo "✅ __pycache__ 目录已从 git 追踪中移除"
else
    echo "ℹ️  __pycache__ 未被追踪"
fi

# 移除 .pyc 文件
echo ""
echo "🐍 移除 .pyc 文件..."
if git ls-files | grep -q "\.pyc$"; then
    find . -type f -name "*.pyc" | while read file; do
        git rm --cached "$file" 2>/dev/null || true
    done
    echo "✅ .pyc 文件已从 git 追踪中移除"
else
    echo "ℹ️  .pyc 文件未被追踪"
fi

# 显示状态
echo ""
echo "📊 当前 Git 状态:"
git status --short

echo ""
echo "✅ 清理完成!"
echo ""
echo "💡 下一步:"
echo "   1. 检查上面的 git status 输出"
echo "   2. 如果看起来正确，运行:"
echo "      git commit -m 'chore: remove build artifacts from git tracking'"
echo "   3. 推送到远程:"
echo "      git push"
echo ""

