# Vector Database Configuration Guide

This system supports multiple vector database providers. Configure your preferred provider using environment variables.

## Supported Vector Databases

- **ChromaDB** - Local/Self-hosted (Default)
- **Pinecone** - Cloud-hosted
- **Weaviate** - Cloud/Self-hosted  
- **Qdrant** - Cloud/Self-hosted

## Configuration

### 1. Set Vector Database Type

```bash
VECTOR_DB_TYPE=pinecone  # or chroma, weaviate, qdrant
```

### 2. Provider-Specific Configuration

#### ChromaDB (Local)
```bash
VECTOR_DB_TYPE=chroma
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_COLLECTION=research-papers
CHROMA_HOST=  # Leave empty for local, or set for remote
CHROMA_PORT=8000
```

#### Pinecone (Cloud)
```bash
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=research-papers
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_DIMENSION=384
```

#### Weaviate (Cloud/Self-hosted)
```bash
VECTOR_DB_TYPE=weaviate
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your_weaviate_api_key_here
WEAVIATE_CLASS_NAME=ResearchPaper
```

#### Qdrant (Cloud/Self-hosted)
```bash
VECTOR_DB_TYPE=qdrant
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION=research-papers
QDRANT_VECTOR_SIZE=384
```

## Embedding Models

### Set Embedding Provider
```bash
EMBEDDING_MODEL_TYPE=openai  # or anthropic, huggingface, deepseek
```

### Provider-Specific Models
```bash
# OpenAI (Requires OPENAI_API_KEY)
EMBEDDING_MODEL_TYPE=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Anthropic (Requires ANTHROPIC_API_KEY)
EMBEDDING_MODEL_TYPE=anthropic
ANTHROPIC_EMBEDDING_MODEL=claude-3-haiku-20240307

# HuggingFace (Local, no API key required)
EMBEDDING_MODEL_TYPE=huggingface
HUGGINGFACE_EMBEDDING_MODEL=all-MiniLM-L6-v2

# DeepSeek (Requires DEEPSEEK_API_KEY)
EMBEDDING_MODEL_TYPE=deepseek
DEEPSEEK_EMBEDDING_MODEL=deepseek-embedding
```

## Setup Examples

### Example 1: Pinecone + OpenAI
```bash
# Vector Database
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=pk-your-api-key
PINECONE_INDEX_NAME=research-papers
PINECONE_ENVIRONMENT=us-west1-gcp

# Embeddings
EMBEDDING_MODEL_TYPE=openai
OPENAI_API_KEY=sk-your-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Example 2: Weaviate + HuggingFace (Local)
```bash
# Vector Database
VECTOR_DB_TYPE=weaviate
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your-weaviate-key
WEAVIATE_CLASS_NAME=ResearchPaper

# Embeddings (Local)
EMBEDDING_MODEL_TYPE=huggingface
HUGGINGFACE_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Example 3: ChromaDB (Local)
```bash
# Vector Database (Local)
VECTOR_DB_TYPE=chroma
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_COLLECTION=research-papers

# Embeddings
EMBEDDING_MODEL_TYPE=openai
OPENAI_API_KEY=sk-your-api-key
```

## Getting API Keys

### Pinecone
1. Sign up at [pinecone.io](https://pinecone.io)
2. Create a project and get your API key
3. Create an index with dimension 384 (for text-embedding-3-small)

### Weaviate
1. Sign up at [weaviate.io](https://weaviate.io) for cloud
2. Create a cluster and get your URL and API key
3. Or self-host using Docker

### Qdrant
1. Sign up at [qdrant.tech](https://qdrant.tech) for cloud
2. Create a cluster and get your URL and API key
3. Or self-host using Docker

## Testing Configuration

The system will automatically test your configuration on startup. Check the logs for:

```
✅ Vector DB (pinecone): Healthy
✅ Embedding Model (openai): Healthy
```

If you see errors, check your API keys and connection settings.

## Performance Considerations

- **ChromaDB**: Best for local development and small datasets
- **Pinecone**: Best for production with high-performance requirements
- **Weaviate**: Good balance of features and performance
- **Qdrant**: Good for self-hosted production deployments

## Migration Between Providers

To switch providers:

1. Export your data from the current provider (if needed)
2. Update environment variables for the new provider
3. Restart the system - it will create new collections/indexes
4. Re-index your papers using the cronjob system