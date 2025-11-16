#!/bin/bash
# 一键安装脚本 - Research Agent RAG 项目
# 适用于新环境快速部署

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# 打印横幅
print_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║      Research Agent RAG - 一键安装脚本                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

# 检查 Python 版本
check_python() {
    info "检查 Python 版本..."
    
    if ! command -v python3 &> /dev/null; then
        error "未找到 Python 3"
        echo "请先安装 Python 3.10 或更高版本"
        echo "访问: https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        error "Python 版本过低: $PYTHON_VERSION"
        echo "需要 Python 3.10 或更高版本"
        exit 1
    fi
    
    success "Python 版本: $PYTHON_VERSION"
}

# 检查/安装 uv
check_uv() {
    info "检查 uv 包管理器..."
    
    if ! command -v uv &> /dev/null; then
        warning "未找到 uv，正在安装..."
        
        # 安装 uv
        if command -v curl &> /dev/null; then
            curl -LsSf https://astral.sh/uv/install.sh | sh
        else
            error "需要 curl 来安装 uv"
            echo "请先安装 curl 或手动安装 uv: https://github.com/astral-sh/uv"
            exit 1
        fi
        
        # 添加到 PATH
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if ! command -v uv &> /dev/null; then
            error "uv 安装失败"
            echo "请手动安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
        fi
    fi
    
    success "uv 已安装: $(uv --version)"
}

# 创建虚拟环境
create_venv() {
    info "创建 Python 虚拟环境..."
    
    if [ -d "venv" ]; then
        warning "虚拟环境已存在，跳过创建"
    else
        uv venv venv
        success "虚拟环境创建成功"
    fi
}

# 安装依赖
install_dependencies() {
    info "安装项目依赖..."
    
    # 使用 uv 安装（更快）
    uv pip install -e .
    
    success "项目依赖安装完成"
}

# 安装 langextract
install_langextract() {
    info "安装 LangExtract..."
    
    uv pip install langextract
    
    success "LangExtract 安装完成"
}

# 验证安装
verify_installation() {
    info "验证安装..."
    
    # 激活虚拟环境并测试导入
    source venv/bin/activate
    
    python3 << 'EOF'
try:
    from shared_config.settings import AppSettings
    from rag_core.preprocessing.langextract_parser import create_langextract_parser
    from domain_models import Topic
    print("✅ 所有模块导入成功")
    exit(0)
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        success "安装验证通过"
    else
        error "安装验证失败"
        exit 1
    fi
}

# 设置环境变量
setup_env() {
    info "检查环境配置..."
    
    if [ ! -f ".env" ]; then
        warning ".env 文件不存在"
        
        if [ -f "env.example" ]; then
            info "从 env.example 创建 .env 文件..."
            cp env.example .env
            success ".env 文件已创建"
            warning "请编辑 .env 文件，填入你的 API Keys"
        else
            error "未找到 env.example 文件"
        fi
    else
        success ".env 文件已存在"
    fi
}

# 检查数据库（可选）
check_database() {
    info "检查数据库配置..."
    
    if command -v psql &> /dev/null; then
        success "PostgreSQL 已安装"
    else
        warning "未检测到 PostgreSQL"
        echo "如需使用数据库功能，请安装 PostgreSQL"
        echo "macOS: brew install postgresql"
        echo "Ubuntu: sudo apt-get install postgresql"
    fi
}

# 显示下一步操作
show_next_steps() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                  🎉 安装完成！                               ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📋 下一步操作："
    echo ""
    echo "1️⃣  激活虚拟环境："
    echo "   source venv/bin/activate"
    echo ""
    echo "2️⃣  配置环境变量（.env 文件）："
    echo "   # 至少需要配置："
    echo "   OPENROUTER_API_KEY=sk-or-v1-your-key-here"
    echo "   LANGEXTRACT_PROVIDER=openrouter"
    echo "   LANGEXTRACT_MODEL_ID=anthropic/claude-3-haiku"
    echo ""
    echo "3️⃣  运行诊断测试："
    echo "   python diagnose_langextract_config.py"
    echo ""
    echo "4️⃣  测试文档解析："
    echo "   python examples/test_langextract_parser.py"
    echo ""
    echo "5️⃣  启动 API 服务："
    echo "   make run"
    echo "   # 或"
    echo "   python start_backend.py"
    echo ""
    echo "📚 更多文档："
    echo "   - 快速开始: QUICKSTART_LANGEXTRACT.md"
    echo "   - 项目 README: README.md"
    echo ""
    echo "💡 常用命令："
    echo "   make help          # 查看所有 Make 命令"
    echo "   make install-dev   # 安装开发依赖"
    echo "   make test          # 运行测试"
    echo "   make lint          # 代码检查"
    echo ""
}

# 主函数
main() {
    print_banner
    
    # 检查系统要求
    check_python
    check_uv
    
    # 安装步骤
    create_venv
    install_dependencies
    install_langextract
    
    # 验证
    verify_installation
    
    # 配置
    setup_env
    check_database
    
    # 完成
    show_next_steps
}

# 运行主函数
main

