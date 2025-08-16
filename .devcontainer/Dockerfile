FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        build-essential \
        curl \
        git \
        openssh-client \
        wget \
        unzip \
        zip \
        nano \
        vim \
        jq \
        tree \
        htop \
        postgresql-client \
        redis-tools \
        ca-certificates \
        gnupg \
        lsb-release \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install uv (faster Python package installer)
RUN pip install --no-cache-dir uv

# Install Node.js and npm (for frontend tooling if needed)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create workspace directory
WORKDIR /workspace

# Set up Python environment
RUN python -m pip install --upgrade pip

# Install common Python tools
RUN pip install --no-cache-dir \
    black \
    isort \
    flake8 \
    mypy \
    pytest \
    pytest-asyncio \
    pytest-cov \
    jupyter \
    jupyterlab \
    ipython \
    pre-commit

# Create non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Add user to sudoers
RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Switch to non-root user
USER $USERNAME

# Set up shell
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc \
    && echo 'export PYTHONPATH="/workspace:$PYTHONPATH"' >> ~/.zshrc

# Set default shell
SHELL ["/bin/zsh", "-c"]

# Expose common ports
EXPOSE 8000 8888 5432 6379 9200 9000 3000

CMD ["sleep", "infinity"]