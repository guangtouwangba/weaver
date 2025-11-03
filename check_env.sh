#!/bin/bash
# 环境诊断脚本

echo "🔍 Python 环境诊断"
echo "=" * 60

echo ""
echo "1️⃣  当前 Python 路径:"
which python
echo "   版本: $(python --version)"

echo ""
echo "2️⃣  当前 pytest 路径:"
if command -v pytest &> /dev/null; then
    which pytest
    echo "   版本: $(pytest --version | head -n 1)"
else
    echo "   ❌ pytest 未找到"
fi

echo ""
echo "3️⃣  .venv 环境检查:"
if [ -f ".venv/bin/python" ]; then
    echo "   ✅ .venv 存在"
    echo "   Python: $(.venv/bin/python --version)"
    if [ -f ".venv/bin/pytest" ]; then
        echo "   ✅ pytest 已安装在 .venv"
    else
        echo "   ❌ pytest 未安装在 .venv"
    fi
else
    echo "   ❌ .venv 不存在"
fi

echo ""
echo "4️⃣  关键依赖检查 (当前环境):"
deps=("langgraph" "langchain" "langchain_community" "langchain_openai" "faiss")
for dep in "${deps[@]}"; do
    if python -c "import $dep" 2>/dev/null; then
        version=$(python -c "import $dep; print(getattr($dep, '__version__', 'unknown'))" 2>/dev/null)
        echo "   ✅ $dep: $version"
    else
        echo "   ❌ $dep: 未安装"
    fi
done

echo ""
echo "5️⃣  .venv 环境中的依赖 (如果存在):"
if [ -f ".venv/bin/python" ]; then
    for dep in "${deps[@]}"; do
        if .venv/bin/python -c "import $dep" 2>/dev/null; then
            version=$(.venv/bin/python -c "import $dep; print(getattr($dep, '__version__', 'unknown'))" 2>/dev/null)
            echo "   ✅ $dep: $version"
        else
            echo "   ❌ $dep: 未安装"
        fi
    done
fi

echo ""
echo "6️⃣  环境变量:"
echo "   PATH (前5个):"
echo "$PATH" | tr ':' '\n' | head -5 | sed 's/^/     /'
echo "   VIRTUAL_ENV: ${VIRTUAL_ENV:-未设置}"

echo ""
echo "=" * 60
echo "💡 建议:"
echo ""
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "   ✅ 虚拟环境已激活"
    if .venv/bin/python -c "import langgraph" 2>/dev/null; then
        echo "   ✅ 依赖已安装"
        echo "   👉 可以直接运行: pytest packages/rag-core/tests/"
    else
        echo "   ❌ 依赖未安装"
        echo "   👉 运行: pip install -e ."
    fi
else
    echo "   ⚠️  虚拟环境未激活"
    echo "   👉 运行: source .venv/bin/activate"
    echo "   👉 然后: pytest packages/rag-core/tests/"
    echo "   👉 或直接: .venv/bin/pytest packages/rag-core/tests/"
fi

