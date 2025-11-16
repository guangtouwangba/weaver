#!/bin/bash
# DevContainer 启动后脚本 - 自动安装依赖和设置环境

set -e

echo "🚀 DevContainer 启动后初始化..."
echo ""

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 等待 PostgreSQL 准备就绪
info "等待 PostgreSQL 启动..."
max_attempts=30
attempt=0
while ! pg_isready -h postgres -U postgres > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        warning "PostgreSQL 启动超时，请手动检查"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""
success "PostgreSQL 已就绪"

# 等待 Redis 准备就绪
info "等待 Redis 启动..."
attempt=0
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        warning "Redis 启动超时，请手动检查"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""
success "Redis 已就绪"

# 创建虚拟环境
info "创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    uv venv venv
    success "虚拟环境创建成功"
else
    warning "虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装 Python 依赖
info "安装 Python 依赖..."
uv pip install -e .
success "Python 依赖安装完成"

# 安装 langextract
info "安装 LangExtract..."
uv pip install langextract
success "LangExtract 安装完成"

# 安装开发依赖
info "安装开发依赖..."
uv pip install -e ".[dev]"
success "开发依赖安装完成"

# 设置环境变量文件
if [ ! -f ".env" ]; then
    info "创建 .env 文件..."
    cp env.example .env
    success ".env 文件已创建"
    warning "请编辑 .env 文件，填入你的 API Keys"
else
    success ".env 文件已存在"
fi

# 运行数据库迁移
info "运行数据库迁移..."
if python migrate_db.py; then
    success "数据库迁移完成"
else
    warning "数据库迁移失败，请稍后手动运行: python migrate_db.py"
fi

# 验证安装
info "验证安装..."
python << 'EOF'
try:
    from shared_config.settings import AppSettings
    from rag_core.preprocessing.langextract_parser import create_langextract_parser
    from domain_models import Topic
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
EOF

# 安装前端依赖（如果存在）
if [ -d "apps/web" ]; then
    info "安装前端依赖..."
    cd apps/web
    if [ -f "package.json" ]; then
        npm install
        success "前端依赖安装完成"
    fi
    cd /workspace
fi

# 显示完成信息
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║           🎉 DevContainer 初始化完成！                       ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 下一步："
echo ""
echo "1️⃣  配置 API Keys (.env 文件):"
echo "   OPENROUTER_API_KEY=sk-or-v1-your-key-here"
echo ""
echo "2️⃣  启动 API 服务:"
echo "   make run"
echo "   或: python start_backend.py"
echo ""
echo "3️⃣  启动前端 (可选):"
echo "   cd apps/web && npm run dev"
echo ""
echo "4️⃣  运行测试:"
echo "   make test"
echo ""
echo "📊 服务状态:"
echo "   - PostgreSQL: postgres:5432"
echo "   - Redis: redis:6379"
echo "   - API: http://localhost:8000"
echo "   - 前端: http://localhost:5173"
echo ""
echo "💡 提示: 虚拟环境已自动激活"
echo ""

