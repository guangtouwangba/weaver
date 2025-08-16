# Dev Container for RAG Research Agent

This directory contains the development container configuration for the RAG Research Agent project.

## 🚀 Quick Start

### Option 1: VS Code with Dev Containers Extension

1. **Install Prerequisites:**
   - [VS Code](https://code.visualstudio.com/)
   - [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **Open in Dev Container:**
   ```bash
   # Clone the repository
   git clone <your-repo-url>
   cd research-agent-rag
   
   # Open in VS Code
   code .
   
   # Use Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
   # Run: "Dev Containers: Reopen in Container"
   ```

3. **Manual Setup (after container starts):**
   ```bash
   # Run the setup script
   ./.devcontainer/setup-dev.sh
   
   # Start middleware services
   make start
   ```

### Option 2: Docker Compose (Manual)

1. **Start the development environment:**
   ```bash
   cd .devcontainer
   docker-compose up -d
   ```

2. **Enter the development container:**
   ```bash
   docker-compose exec app bash
   ```

3. **Run setup:**
   ```bash
   ./.devcontainer/setup-dev.sh
   make start
   ```

## 🏗️ Architecture

### Services Included

- **app**: Main development container with Python, tools, and your code
- **postgres**: PostgreSQL database for data storage
- **redis**: Redis for caching and queues
- **elasticsearch**: Full-text search and analytics
- **minio**: S3-compatible object storage
- **weaviate**: Vector database for embeddings
- **chromadb**: Alternative vector database
- **prometheus**: Metrics collection
- **grafana**: Metrics visualization

### Port Mappings

| Service | Container Port | Host Port | URL |
|---------|----------------|-----------|-----|
| FastAPI App | 8000 | 8000 | http://localhost:8000 |
| Jupyter Lab | 8888 | 8888 | http://localhost:8888 |
| PostgreSQL | 5432 | 5432 | localhost:5432 |
| Redis | 6379 | 6379 | localhost:6379 |
| Elasticsearch | 9200 | 9200 | http://localhost:9200 |
| MinIO API | 9000 | 9000 | http://localhost:9000 |
| MinIO Console | 9001 | 9001 | http://localhost:9001 |
| Weaviate | 8080 | 8080 | http://localhost:8080 |
| ChromaDB | 8000 | 8001 | http://localhost:8001 |
| Prometheus | 9090 | 9090 | http://localhost:9090 |
| Grafana | 3000 | 3000 | http://localhost:3000 |

## 🛠️ Development Tools

### Pre-installed Tools

- **Python 3.11** with pip and venv
- **Git** for version control
- **Docker** for containerization
- **Zsh** with Oh My Zsh
- **Development tools**: black, isort, flake8, mypy, pytest
- **Jupyter Lab** for interactive development

### VS Code Extensions

The following extensions are automatically installed:

- **Python**: Core Python support
- **Black Formatter**: Code formatting
- **isort**: Import organization  
- **Jupyter**: Notebook support
- **YAML**: YAML file support
- **Docker**: Docker integration
- **GitLens**: Enhanced Git features

## 📁 File Structure

```
.devcontainer/
├── devcontainer.json          # Main dev container configuration
├── docker-compose.yml         # Multi-service development environment
├── Dockerfile                 # Custom development image (if needed)
├── setup-dev.sh              # Manual setup script
├── post-create.sh             # Automatic setup after container creation
├── post-start.sh              # Automatic setup after container starts
├── init-scripts/              # Database initialization scripts
│   └── init-db.sql
├── monitoring/                # Monitoring configuration
│   └── prometheus.yml
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

The development container includes these environment variables:

```bash
PYTHONPATH=/workspace
DATABASE_URL=postgresql://rag_user:rag_password@postgres:5432/rag_db
REDIS_URL=redis://redis:6379
ELASTICSEARCH_URL=http://elasticsearch:9200
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### Database Configuration

- **Database**: rag_db
- **User**: rag_user  
- **Password**: rag_password
- **Host**: postgres (or localhost from host)
- **Port**: 5432

### Storage Configuration

- **MinIO Access Key**: minioadmin
- **MinIO Secret Key**: minioadmin
- **Default Buckets**: documents, embeddings, models

## 🚨 Troubleshooting

### Common Issues

1. **Container Build Fails**
   ```bash
   # Try rebuilding without cache
   docker-compose build --no-cache app
   ```

2. **Services Not Starting**
   ```bash
   # Check service logs
   docker-compose logs <service-name>
   
   # Restart specific service
   docker-compose restart <service-name>
   ```

3. **Port Conflicts**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

4. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   
   # Or from inside container
   sudo chown -R vscode:vscode /workspace
   ```

5. **Python Environment Issues**
   ```bash
   # Recreate virtual environment
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

### Reset Environment

To completely reset the development environment:

```bash
# Stop and remove all containers
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Rebuild and start
docker-compose up --build -d
```

## 🎯 Development Workflow

### Daily Development

1. **Start the environment:**
   ```bash
   # Open in VS Code with Dev Containers, or:
   docker-compose up -d
   ```

2. **Run setup (first time only):**
   ```bash
   ./.devcontainer/setup-dev.sh
   ```

3. **Start middleware:**
   ```bash
   make start
   ```

4. **Develop:**
   - Edit code in VS Code
   - Run tests: `make test`
   - Format code: `make format`
   - Check linting: `make lint`

5. **Clean up:**
   ```bash
   make stop          # Stop middleware
   docker-compose down # Stop dev environment
   ```

### Testing

```bash
# Run all tests
make test

# Run specific tests
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=rag tests/
```

### Code Quality

```bash
# Format code
make format

# Check formatting
black --check .
isort --check-only .

# Lint code
make lint
flake8 .
mypy rag/
```

## 📚 Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/remote/containers)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dev Container Specification](https://containers.dev/)

## 🆘 Support

If you encounter issues:

1. Check this README and troubleshooting section
2. Check the main project documentation
3. Review Docker and service logs
4. Create an issue in the project repository

Happy coding! 🚀
