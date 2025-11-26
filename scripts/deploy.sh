#!/bin/bash
# deploy.sh - 统一部署脚本
# 使用方法:
#   ./scripts/deploy.sh web dev     # 部署 Web 前端到开发环境
#   ./scripts/deploy.sh web prod    # 部署 Web 前端到生产环境
#   ./scripts/deploy.sh api dev     # 部署 API 后端到开发环境
#   ./scripts/deploy.sh api prod    # 部署 API 后端到生产环境
#   ./scripts/deploy.sh all dev     # 部署所有服务到开发环境
#   ./scripts/deploy.sh all prod    # 部署所有服务到生产环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# 打印带颜色的消息
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

# 显示使用帮助
show_help() {
    echo "Usage: $0 <service> <environment>"
    echo ""
    echo "Services:"
    echo "  web   - Deploy web frontend"
    echo "  api   - Deploy API backend"
    echo "  all   - Deploy all services"
    echo ""
    echo "Environments:"
    echo "  dev   - Development environment"
    echo "  prod  - Production environment"
    echo ""
    echo "Examples:"
    echo "  $0 web dev      # Deploy web to development"
    echo "  $0 api prod     # Deploy API to production"
    echo "  $0 all dev      # Deploy everything to development"
}

# 部署 Web 前端
deploy_web() {
    local env=$1
    local config_file="fly.${env}.toml"
    
    print_info "Deploying Web frontend to ${env} environment..."
    
    cd "$ROOT_DIR/web"
    
    if [ ! -f "$config_file" ]; then
        print_error "Config file not found: $config_file"
        exit 1
    fi
    
    print_info "Using config: $config_file"
    fly deploy --config "$config_file"
    
    print_success "Web frontend deployed to ${env}!"
}

# 部署 API 后端
deploy_api() {
    local env=$1
    local config_file="fly.api.${env}.toml"
    
    print_info "Deploying API backend to ${env} environment..."
    
    cd "$ROOT_DIR"
    
    if [ ! -f "$config_file" ]; then
        print_error "Config file not found: $config_file"
        exit 1
    fi
    
    print_info "Using config: $config_file"
    fly deploy --config "$config_file"
    
    print_success "API backend deployed to ${env}!"
}

# 主函数
main() {
    if [ $# -lt 2 ]; then
        show_help
        exit 1
    fi
    
    local service=$1
    local env=$2
    
    # 验证环境参数
    if [ "$env" != "dev" ] && [ "$env" != "prod" ]; then
        print_error "Invalid environment: $env"
        print_error "Must be 'dev' or 'prod'"
        exit 1
    fi
    
    # 检查 fly CLI 是否安装
    if ! command -v fly &> /dev/null; then
        print_error "fly CLI is not installed"
        print_info "Install it from: https://fly.io/docs/hands-on/install-flyctl/"
        exit 1
    fi
    
    # 根据服务类型执行部署
    case $service in
        web)
            deploy_web "$env"
            ;;
        api)
            deploy_api "$env"
            ;;
        all)
            print_info "Deploying all services to ${env}..."
            deploy_web "$env"
            deploy_api "$env"
            print_success "All services deployed to ${env}!"
            ;;
        *)
            print_error "Unknown service: $service"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

