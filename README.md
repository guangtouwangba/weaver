# Research Agent RAG

Intelligent Knowledge Management Agent System based on NotebookLM concept, solving the "island problem" between PDF documents and achieving knowledge interconnection.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- [UV](https://github.com/astral-sh/uv) (Python package manager)

### Install UV

```bash
# macOS
brew install uv

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Project Setup

1. **Clone the project**
```bash
git clone <repository-url>
cd research-agent-rag
```

2. **Create virtual environment**
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
# Install all dependencies
make install-all

# Or install separately
make install        # Production dependencies
make install-dev    # Development dependencies
make install-test   # Test dependencies
```

4. **Start middleware services**
```bash
make start
```

5. **Initialize database**
```bash
make db-init
```

## 🛠️ Using Makefile

### Dependency Management
```bash
make install        # Install production dependencies
make install-dev    # Install development dependencies
make install-test   # Install test dependencies
make install-docs   # Install documentation dependencies
make install-prod   # Install production environment dependencies
make install-all    # Install all dependencies
```

### Middleware Management
```bash
make start          # Start all middleware services
make stop           # Stop all middleware services
make restart        # Restart all middleware services
make status         # Check service status
make logs           # View all service logs
make logs-service SERVICE=postgres  # View specific service logs
make health-check   # Check service health status
```

### Development Tools
```bash
make test           # Run tests
make test-cov       # Run tests and generate coverage report
make test-unit      # Run unit tests
make test-integration # Run integration tests
make lint           # Run code linting
make format         # Format code
make check          # Format code and run linting
make pre-commit     # Run pre-commit checks
```

### Database Management
```bash
make db-init        # Initialize database
make db-migrate     # Create new database migration
make db-upgrade     # Upgrade database to latest version
make db-downgrade   # Rollback database to previous version
make db-reset       # Reset database (Dangerous operation!)
```

### Cleanup and Maintenance
```bash
make clean          # Clean Python cache and temporary files
make clean-all      # Clean all content including Docker data
```

### Utility Tools
```bash
make shell          # Start Python interactive shell
make jupyter        # Start Jupyter Notebook
make docs-serve     # Start documentation server
make info           # Display project information
make version        # Display project version
make help           # Show all available commands
```

## 🐳 Docker Services

The project includes the following middleware services:

- **PostgreSQL** (Port: 5432) - Main database
- **Weaviate** (Port: 8080) - Vector database
- **Redis** (Port: 6379) - Cache and session storage
- **Elasticsearch** (Port: 9200) - Full-text search
- **MinIO** (Port: 9000) - Object storage
- **Grafana** (Port: 3000) - Monitoring dashboard
- **Prometheus** (Port: 9090) - Monitoring metrics collection

### Service Management
```bash
# Start all services
make start

# Check service status
make status

# View service logs
make logs

# Stop all services
make stop
```

## 📦 Dependency Management

The project uses UV for dependency management, with configuration file `pyproject.toml`.

### Adding New Dependencies
```bash
# Add production dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Add optional dependency
uv add --optional dev package-name
```

### Updating Dependencies
```bash
# Update all dependencies
uv update

# Update specific dependency
uv update package-name
```

### Generating Lock File
```bash
# Generate dependency lock file
uv lock

# Sync dependencies
uv sync
```

## 🔧 Development Workflow

### 1. Code Formatting
```bash
make format
```

### 2. Code Linting
```bash
make lint
```

### 3. Running Tests
```bash
make test
```

### 4. Pre-commit Checks
```bash
make pre-commit
```

### 5. Complete Check
```bash
make check
```

## 📁 Project Structure

```
research-agent-rag/
├── rag/                    # Core RAG modules
│   ├── knowledge_store/    # Knowledge storage
│   ├── document_spliter/   # Document splitting
│   ├── file_loader/        # File loading
│   ├── vector_store/       # Vector storage
│   ├── retriever/          # Retriever
│   └── router/             # Router
├── config/                 # Configuration files
├── scripts/                # Script files
├── tests/                  # Test files
├── docker-compose.middleware.yaml  # Docker orchestration file
├── pyproject.toml          # Project configuration and dependencies
├── Makefile                # Build and deployment scripts
└── README.md               # Project documentation
```

## 🌟 Features

- **Intelligent Knowledge Extraction**: AI-driven structured knowledge extraction
- **Knowledge Graph**: Build unified knowledge networks
- **Cross-document Association**: Automatically discover related concepts and relationships
- **Multi-modal Support**: Support text, charts, formulas, etc.
- **Collaborative Management**: Hybrid mode of AI suggestions + human confirmation
- **High Performance**: Asynchronous architecture supporting large-scale document processing
- **Extensible**: Modular design supporting multiple storage backends

## 📚 Documentation

- [Architecture Design Roadmap](roadmap.md)
- [Middleware Configuration Guide](README.middleware.md)
- [Database Configuration Guide](README.database.md)

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter problems or have questions, please:

1. Check [Issues](https://github.com/your-org/research-agent-rag/issues)
2. Create a new Issue
3. Contact project maintainers

---

**Note**: This is a research project. Please conduct thorough testing and evaluation before using in production environments.
