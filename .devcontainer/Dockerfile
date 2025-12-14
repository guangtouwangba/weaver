# DevContainer Dockerfile for Research Agent RAG
FROM python:3.11-slim

# 设置工作目录
WORKDIR /workspace

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    git \
    curl \
    wget \
    build-essential \
    # PostgreSQL 客户端
    postgresql-client \
    # 其他有用的工具
    vim \
    nano \
    htop \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv (快速的 Python 包管理器)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# 预安装常用 Python 工具
RUN pip install --no-cache-dir \
    ipython \
    ipdb

# 创建数据目录
RUN mkdir -p /workspace/data/uploads /workspace/data/vector_store

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 容器健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 默认命令
CMD ["sleep", "infinity"]

