# Architecture Migration Guide

This guide provides a step-by-step approach to migrate from the current complex architecture to the simplified, more maintainable architecture described in the ARCHITECTURE_REVIEW.md.

## 🚀 Migration Overview

The migration can be done incrementally without breaking the existing system. Each phase can be completed independently, allowing for gradual improvements and validation at each step.

### Migration Phases:
1. **Phase 1**: Replace custom DI with FastAPI dependencies (1-2 weeks)
2. **Phase 2**: Consolidate Application/Services layers (2-3 weeks)  
3. **Phase 3**: Simplify configuration management (1 week)
4. **Phase 4**: Implement comprehensive testing (2 weeks)
5. **Phase 5**: Integrate RAG module (2-3 weeks)
6. **Phase 6**: Final cleanup and optimization (1 week)

## 📋 Phase 1: Replace Custom Dependency Injection

**Duration**: 1-2 weeks  
**Risk**: Low  
**Impact**: High reduction in complexity

### Step 1.1: Create New Dependencies Module

```bash
# Create the new dependencies file
mkdir -p infrastructure/dependencies
touch infrastructure/dependencies/__init__.py
touch infrastructure/dependencies/core.py
```

Copy the content from `examples/simplified_dependencies.py` to `infrastructure/dependencies/core.py` and adapt it to your specific repositories and services.

### Step 1.2: Update Main Application

```python
# main.py - Update imports
from infrastructure.dependencies.core import (
    get_topic_service, get_document_service, get_system_health
)

# Remove old DI setup
# from infrastructure.denpendency_injection import setup_fastapi_integration
# setup_fastapi_integration(app)

# Add health check endpoint using new dependencies
@app.get("/health")
async def health_check(health_status = Depends(get_system_health)):
    return health_status
```

### Step 1.3: Update API Routes One by One

Start with the simplest route (e.g., topic routes):

```python
# api/topic_routes.py - Before
from infrastructure.denpendency_injection.fastapi_integration import get_topic_controller

@router.post("/")
async def create_topic(
    request: CreateTopicRequest,
    controller = Depends(get_topic_controller)
):
    return await controller.create_topic(request)

# api/topic_routes.py - After  
from infrastructure.dependencies.core import get_topic_service

@router.post("/")
async def create_topic(
    request: CreateTopicRequest,
    service: TopicService = Depends(get_topic_service)
):
    return await service.create_topic(request)
```

### Step 1.4: Test and Validate

Run tests after each route migration:
```bash
# Test specific route
python -m pytest tests/api/test_topic_routes.py -v

# Test full application
python -m pytest -x
```

### Step 1.5: Remove Custom DI System

Once all routes are migrated:
```bash
# Remove custom DI directory
rm -rf infrastructure/denpendency_injection/

# Update imports throughout the codebase
grep -r "from infrastructure.denpendency_injection" . --include="*.py"
# Replace each occurrence with new dependency imports
```

## 📋 Phase 2: Consolidate Application/Services Layers

**Duration**: 2-3 weeks  
**Risk**: Medium  
**Impact**: Significant code reduction and clarity

### Step 2.1: Create New Services Structure

```bash
mkdir -p application/services
touch application/services/__init__.py
touch application/services/topic_service.py
touch application/services/document_service.py
touch application/services/search_service.py
```

### Step 2.2: Merge Topic Service

Create `application/services/topic_service.py` based on `examples/consolidated_services.py`:

1. Copy business logic from `application/topic/topic.py`
2. Copy workflow orchestration from `services/topic_service.py` (if exists)
3. Combine them into a single, cohesive service
4. Update all repository and storage interactions

### Step 2.3: Update Dependencies

```python
# infrastructure/dependencies/core.py
def get_topic_service(
    session: AsyncSession = Depends(get_database_session),
    storage: IObjectStorage = Depends(get_object_storage),
    event_bus: EventBus = Depends(get_event_bus)
):
    from application.services.topic_service import TopicService
    return TopicService(session, storage, event_bus)
```

### Step 2.4: Migrate Route by Route

```python
# Update each route to use the new consolidated service
@router.post("/topics/")
async def create_topic(
    request: CreateTopicRequest,
    service: TopicService = Depends(get_topic_service)
):
    return await service.create_topic(request)
```

### Step 2.5: Clean Up Old Structure

After successful migration:
```bash
# Remove old application structure
rm -rf application/topic/
rm -rf services/topic_service.py

# Update all imports
grep -r "from application.topic" . --include="*.py"
grep -r "from services.topic_service" . --include="*.py"
```

## 📋 Phase 3: Simplify Configuration Management

**Duration**: 1 week  
**Risk**: Low  
**Impact**: Better maintainability

### Step 3.1: Create New Configuration

```bash
mkdir -p config
touch config/__init__.py
touch config/settings.py
```

Copy content from `examples/simplified_config.py` to `config/settings.py`.

### Step 3.2: Update Application Startup

```python
# main.py
from config.settings import get_settings

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
    )
    # ... rest of app setup
```

### Step 3.3: Update Infrastructure Components

```python
# infrastructure/database/config.py
from config.settings import get_settings

def get_database_url() -> str:
    settings = get_settings()
    return settings.database.url

# infrastructure/storage/factory.py
def create_storage_from_env():
    settings = get_settings()
    config = settings.get_storage_config()
    # ... create storage based on config
```

### Step 3.4: Clean Up Old Config

```bash
# Remove old configuration files
rm infrastructure/config.py
# Remove scattered config files
find . -name "*.env.*" -not -name ".env.example"
```

## 📋 Phase 4: Implement Comprehensive Testing

**Duration**: 2 weeks  
**Risk**: Low  
**Impact**: Better code quality and confidence

### Step 4.1: Set Up Test Structure

```bash
mkdir -p tests/{unit,integration,api}
mkdir -p tests/unit/{application,infrastructure,domain}
mkdir -p tests/integration/{database,storage,rag}
touch tests/__init__.py
touch tests/conftest.py
```

### Step 4.2: Create Test Fixtures

Copy test fixtures and utilities from `examples/comprehensive_testing.py` to `tests/conftest.py`.

### Step 4.3: Write Unit Tests

Start with the most critical services:
```python
# tests/unit/application/test_topic_service.py
class TestTopicService:
    async def test_create_topic_success(self, topic_service, mock_repo):
        # Test implementation
        pass
```

### Step 4.4: Add Integration Tests

```python  
# tests/integration/database/test_topic_repository.py
class TestTopicRepository:
    async def test_create_and_retrieve_topic(self, test_db_session):
        # Test with real database
        pass
```

### Step 4.5: Configure CI/CD

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=application --cov=infrastructure
```

## 📋 Phase 5: Integrate RAG Module

**Duration**: 2-3 weeks  
**Risk**: Medium  
**Impact**: Unified architecture

### Step 5.1: Move RAG Components

```bash
mkdir -p infrastructure/rag
mv rag/core/* infrastructure/rag/
mv rag/vector_store/* infrastructure/rag/vector_stores/
mv rag/embedding/* infrastructure/rag/embeddings/
```

### Step 5.2: Create RAG Service

```python
# application/services/rag_service.py
class RAGService:
    def __init__(self, 
                 loader: IDocumentLoader,
                 processor: IDocumentProcessor,
                 vector_store: IVectorStore):
        self.loader = loader
        self.processor = processor
        self.vector_store = vector_store
    
    async def process_document(self, document_path: str) -> ProcessingResult:
        # Unified RAG processing pipeline
        pass
```

### Step 5.3: Update Domain Models

```python
# domain/rag/document.py - Move from rag/models.py
@dataclass  
class Document:
    id: str
    title: str
    content: str
    # ... rest of document model
```

### Step 5.4: Update API Routes

```python
# api/rag_routes.py
@router.post("/documents/")
async def process_document(
    file: UploadFile,
    rag_service: RAGService = Depends(get_rag_service)
):
    return await rag_service.process_document(file)
```

## 📋 Phase 6: Final Cleanup and Optimization

**Duration**: 1 week  
**Risk**: Low  
**Impact**: Polish and performance

### Step 6.1: Remove Unused Code

```bash
# Find unused imports
pip install unimport
unimport --check --diff .

# Find unused code
pip install vulture
vulture .
```

### Step 6.2: Optimize Performance

```python
# Add caching where appropriate
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param):
    # Cached expensive computation
    pass
```

### Step 6.3: Update Documentation

```markdown
# Update README.md, API docs, etc.
- Architecture diagrams
- API documentation
- Development setup
- Deployment guides
```

### Step 6.4: Final Testing

```bash
# Run comprehensive test suite
pytest --cov=application --cov=infrastructure --cov-report=html

# Load testing
pytest -m performance

# Integration testing
pytest -m integration
```

## 🔧 Migration Utilities

### Automated Refactoring Script

```python
#!/usr/bin/env python3
"""
Migration utility script to help with common refactoring tasks.
"""

import os
import re
from pathlib import Path

def replace_imports(directory: Path, old_import: str, new_import: str):
    """Replace import statements across all Python files."""
    for py_file in directory.rglob("*.py"):
        content = py_file.read_text()
        if old_import in content:
            new_content = content.replace(old_import, new_import)
            py_file.write_text(new_content)
            print(f"Updated imports in {py_file}")

def remove_unused_di_references():
    """Remove references to custom DI system."""
    old_imports = [
        "from infrastructure.denpendency_injection",
        "from infrastructure.denpendency_injection.registry import get_registry",
        "from infrastructure.denpendency_injection.fastapi_integration",
    ]
    
    for old_import in old_imports:
        replace_imports(Path("."), old_import, "# Removed custom DI import")

if __name__ == "__main__":
    print("Starting migration utilities...")
    remove_unused_di_references()
    print("Migration utilities completed!")
```

## ✅ Validation Checklist

After each phase, verify:

- [ ] All tests pass
- [ ] Application starts without errors
- [ ] API endpoints respond correctly
- [ ] Database operations work
- [ ] Storage operations work
- [ ] No unused imports or code
- [ ] Performance is not degraded
- [ ] Documentation is updated

## 🚨 Rollback Plan

For each phase, maintain the ability to rollback:

1. **Use Feature Branches**: Each phase in a separate branch
2. **Database Migrations**: Ensure all migrations are reversible
3. **Configuration**: Keep old configuration files until migration is complete
4. **Gradual Rollout**: Use feature flags to enable/disable new components
5. **Monitoring**: Monitor application health during migration

## 📊 Expected Results

After completing the migration:

- **~30% reduction in codebase size**
- **Simplified dependency management**
- **Faster development cycle**
- **Better test coverage (>80%)**
- **Improved performance** (fewer abstraction layers)
- **Enhanced maintainability**
- **Better developer experience**

## 💡 Tips for Success

1. **Start Small**: Begin with the least risky components
2. **Test Frequently**: Run tests after every significant change
3. **Communicate**: Keep team informed of progress and issues
4. **Document Changes**: Update documentation as you go
5. **Monitor Performance**: Watch for any performance regressions
6. **Get Reviews**: Have team members review each phase
7. **Plan for Issues**: Budget extra time for unexpected problems

This migration guide ensures a smooth transition to a cleaner, more maintainable architecture while preserving all existing functionality.