# Cleanup Environment Variables - Tasks

## Phase 1: 清理 backend/env.example

- [x] **1.1 移除未使用的数据库池配置**
  - 移除 `DB_POOL_SIZE`
  - 移除 `DB_MAX_OVERFLOW`
  - 这些值目前硬编码在代码中，不通过环境变量配置

- [x] **1.2 移除未使用的 LLM 配置变量**
  - 移除 `LLM_PROVIDER` (代码直接使用 OpenRouter)
  - 移除 `LLM_TEMPERATURE` (未在 config.py 定义)
  - 移除 `LLM_MAX_TOKENS` (未在 config.py 定义)

- [x] **1.3 移除未使用的 Embedding 配置变量**
  - 移除 `EMBEDDING_PROVIDER` (未在 config.py 定义)
  - 移除 `EMBEDDING_DIMENSIONS` (未使用)
  - 移除 `FAKE_EMBEDDING_SIZE` (未使用)

- [x] **1.4 移除未使用的 OpenRouter 站点信息**
  - 移除 `OPENROUTER_SITE_URL`
  - 移除 `OPENROUTER_SITE_NAME`

- [x] **1.5 移除未使用的 OpenAI 配置**
  - 移除 `OPENAI_BASE_URL` (未在 config.py 定义)

- [x] **1.6 清理 Runtime Evaluation 变量**
  - 移除 `RUNTIME_EVALUATION_ENABLED` (使用 `evaluation_enabled` 代替)
  - 移除 `RUNTIME_EVALUATION_MODE`
  - 移除 `RUNTIME_EVALUATION_SAMPLING_RATE` (使用 `evaluation_sample_rate` 代替)
  - 移除 `RUNTIME_EVALUATION_METRICS`
  - 移除 `RUNTIME_EVALUATION_STORAGE_DIR`
  - 移除 `RUNTIME_EVALUATION_SAVE_RESULTS`

## Phase 2: 清理根目录 env.example

- [x] **2.1 简化根目录 env.example**
  - 保留作为快速参考
  - 移除具体变量定义，只保留指向子目录 env.example 的说明
  - 或者完全移除，因为已标注为 legacy

## Phase 3: 验证

- [x] **3.1 确保没有破坏现有功能**
  - 运行后端服务确认启动正常
  - 检查日志无缺失配置警告

## 待确认项

在实施前需要确认以下问题：

1. **DB_POOL_SIZE / DB_MAX_OVERFLOW**: 是否有计划在未来使用这些配置？还是应该从 env.example 移除？

2. **LLM_TEMPERATURE / LLM_MAX_TOKENS**: 这些值目前在代码中如何配置？是否应该添加到 config.py 而非移除？

3. **根目录 env.example**: 是否应该完全移除，还是保留作为文档参考？

## 变量分类汇总

### 确认可移除 (env.example 定义但代码未使用)

```
DB_POOL_SIZE
DB_MAX_OVERFLOW
LLM_PROVIDER
LLM_TEMPERATURE
LLM_MAX_TOKENS
EMBEDDING_PROVIDER
EMBEDDING_DIMENSIONS
FAKE_EMBEDDING_SIZE
OPENROUTER_SITE_URL
OPENROUTER_SITE_NAME
OPENAI_BASE_URL
RUNTIME_EVALUATION_ENABLED
RUNTIME_EVALUATION_MODE
RUNTIME_EVALUATION_SAMPLING_RATE
RUNTIME_EVALUATION_METRICS
RUNTIME_EVALUATION_STORAGE_DIR
RUNTIME_EVALUATION_SAVE_RESULTS
```

### 保留 (非重复，架构需要)

```
SUPABASE_URL (后端使用)
NEXT_PUBLIC_SUPABASE_URL (前端使用，值相同但必须分开)
NEXT_PUBLIC_SUPABASE_ANON_KEY (前端使用)
SUPABASE_SERVICE_ROLE_KEY (后端使用)
```
