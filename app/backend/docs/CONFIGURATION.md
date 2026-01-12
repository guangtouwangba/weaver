# Backend Configuration

The application uses `pydantic-settings` for configuration management. Settings are loaded from environment variables or a `.env` file.

## Loading Strategy
The system searches for a `.env` file in the following order:
1. Current working directory
2. Project root
3. Based on `config.py` location

If no `.env` file is found, it falls back to system environment variables (common in production environments like Zeabur/Docker).

## Configuration Options

### Database
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Connection string for PostgreSQL | `postgresql+asyncpg://...` |
| `DATABASE_CLIENT_TYPE` | Type of client to use (`postgres`, `supabase`, `sqlalchemy`) | `postgres` |

### LLM & Embeddings (OpenRouter)
| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | API key for OpenRouter | `""` |
| `LLM_MODEL` | Model to use for generation | `openai/gpt-4o-mini` |
| `EMBEDDING_MODEL` | Model to use for embeddings | `openai/text-embedding-3-small` |
| `OPENAI_API_KEY` | Optional fallback if not using OpenRouter | `""` |

### Vision & OCR
| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key for Vision OCR | `""` |
| `OCR_MODE` | Strategy (`auto`, `unstructured`, `docling`, `gemini`) | `auto` |
| `GEMINI_OCR_CONCURRENCY` | Concurrent Gemini requests | `3` |
| `GEMINI_REQUEST_TIMEOUT` | Timeout per request (seconds) | `60` |

### YouTube Extraction
| Variable | Description | Default |
|----------|-------------|---------|
| `YOUTUBE_COOKIES_PATH` | Path to Netscape cookies file (for auth) | `""` |
| `YOUTUBE_COOKIES_CONTENT` | Raw content of cookies file (for cloud envs) | `""` |
| `URL_EXTRACTION_TIMEOUT` | Timeout for extraction tasks | `60` |

### Storage
| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_DIR` | Local directory for uploads | `./data/uploads` |
| `SUPABASE_URL` | Supabase URL (if using Supabase storage) | `""` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key | `""` |
| `STORAGE_BUCKET` | Storage bucket name | `documents` |

### Retrieval (RAG)
| Variable | Description | Default |
|----------|-------------|---------|
| `RETRIEVAL_TOP_K` | Number of documents to retrieve | `5` |
| `RETRIEVAL_MIN_SIMILARITY` | Minimum similarity threshold | `0.0` |
| `INTENT_CLASSIFICATION_ENABLED` | Enable intent-based retrieval | `True` |
| `RAG_MODE` | Strategy (`traditional`, `long_context`, `auto`) | `traditional` |
| `LONG_CONTEXT_SAFETY_RATIO` | Context usage ratio safety margin | `0.55` |

### Observability
| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOKI_URL` | URL for Loki logging | `""` |
| `LANGFUSE_ENABLED` | Enable Langfuse tracing | `False` |
| `LANGFUSE_PUBLIC_KEY` | Langfuse Public Key | `""` |
| `LANGFUSE_SECRET_KEY` | Langfuse Secret Key | `""` |
| `LANGFUSE_HOST` | Langfuse Host URL | `https://cloud.langfuse.com` |

### Security
| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `SUPABASE_JWT_SECRET` | Secret for verifying auth tokens | `""` |
| `AUTH_BYPASS_ENABLED` | Disable auth for local dev | `False` |
