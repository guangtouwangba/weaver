#!/bin/bash
# fly-setup.sh - 首次设置 Fly.io 应用
# 使用方法: ./scripts/fly-setup.sh
#
# 这个脚本会创建所有需要的 Fly.io 应用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 fly CLI
if ! command -v fly &> /dev/null; then
    print_error "fly CLI is not installed"
    print_info "Install it from: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# 检查是否已登录
if ! fly auth whoami &> /dev/null; then
    print_warning "You are not logged in to Fly.io"
    print_info "Running: fly auth login"
    fly auth login
fi

print_info "Current user: $(fly auth whoami)"
echo ""

# 定义要创建的应用
APPS=(
    "research-rag-web-dev"
    "research-rag-web-prod"
    "research-rag-api-dev"
    "research-rag-api-prod"
)

# 创建应用
for app in "${APPS[@]}"; do
    print_info "Creating app: $app"
    
    if fly apps list | grep -q "$app"; then
        print_warning "App '$app' already exists, skipping..."
    else
        fly apps create "$app" --org personal || {
            print_error "Failed to create app: $app"
            continue
        }
        print_success "Created app: $app"
    fi
done

echo ""
print_success "Setup complete!"
echo ""
print_info "Next steps:"
echo "  1. Set secrets for each app:"
echo "     fly secrets set SECRET_KEY=xxx -a research-rag-web-dev"
echo "     fly secrets set DATABASE_URL=xxx -a research-rag-api-dev"
echo ""
echo "  2. Deploy your apps:"
echo "     ./scripts/deploy.sh web dev"
echo "     ./scripts/deploy.sh api dev"
echo ""
echo "  3. View your apps:"
echo "     fly apps list"
echo "     fly status -a research-rag-web-dev"

