# 用户配置中心规划

## 1. 系统架构设计

### 1.1 配置层级
- **全局配置**：系统默认配置，影响所有项目
- **项目配置**：项目级别的配置覆盖，优先级高于全局配置
- **环境变量**：作为最终fallback，用于系统初始化

### 1.2 配置优先级
```
项目配置 > 全局配置 > 环境变量默认值
```

### 1.3 配置分类
1. **模型配置**：LLM模型、Embedding模型
2. **API Key配置**：OpenRouter API Key、OpenAI API Key（可选）
3. **RAG策略配置**：检索策略、生成策略、RAG模式
4. **高级配置**：意图分类开关、缓存设置等

## 2. 数据库设计

### 2.1 全局配置表 (global_settings)
```sql
CREATE TABLE global_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) UNIQUE NOT NULL,  -- 配置键名
    value JSONB NOT NULL,               -- 配置值（JSON格式）
    category VARCHAR(100) NOT NULL,    -- 配置分类：model, api_key, rag_strategy, advanced
    description TEXT,                  -- 配置说明
    is_encrypted BOOLEAN DEFAULT FALSE, -- 是否加密存储（用于API Key）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 项目配置表 (project_settings)
```sql
CREATE TABLE project_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,         -- 配置键名
    value JSONB NOT NULL,              -- 配置值
    category VARCHAR(100) NOT NULL,   -- 配置分类
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, key)            -- 每个项目每个配置键唯一
);
```

### 2.3 配置键定义
- `llm_model`: LLM模型选择（如 "openai/gpt-4o-mini"）
- `embedding_model`: Embedding模型选择（如 "openai/text-embedding-3-small"）
- `openrouter_api_key`: OpenRouter API Key（加密存储）
- `openai_api_key`: OpenAI API Key（可选，加密存储）
- `rag_mode`: RAG模式（"traditional" | "long_context" | "auto"）
- `retrieval_top_k`: 检索Top-K数量
- `retrieval_min_similarity`: 最小相似度阈值
- `use_hybrid_search`: 是否使用混合搜索
- `intent_classification_enabled`: 是否启用意图分类
- `intent_cache_enabled`: 是否启用意图缓存
- `citation_format`: 引用格式（"inline" | "structured" | "both"）

## 3. 后端实现

### 3.1 数据库模型
**文件**: `app/backend/src/research_agent/infrastructure/database/models.py`

添加两个新模型：
- `GlobalSettingModel`: 全局配置模型
- `ProjectSettingModel`: 项目配置模型

### 3.2 配置服务层
**新文件**: `app/backend/src/research_agent/domain/services/settings_service.py`

核心功能：
- `get_setting(key, project_id=None)`: 获取配置（支持优先级查找）
- `set_global_setting(key, value, category)`: 设置全局配置
- `set_project_setting(project_id, key, value, category)`: 设置项目配置
- `delete_project_setting(project_id, key)`: 删除项目配置（恢复为全局配置）
- `validate_api_key(api_key, provider)`: 验证API Key有效性
- `encrypt_value(value)`: 加密敏感值
- `decrypt_value(encrypted_value)`: 解密敏感值

### 3.3 配置仓库
**新文件**: `app/backend/src/research_agent/domain/repositories/settings_repo.py`

定义接口：
- `get_global_setting(key)`
- `get_project_setting(project_id, key)`
- `create_or_update_global_setting(key, value, category)`
- `create_or_update_project_setting(project_id, key, value, category)`
- `delete_project_setting(project_id, key)`

**新文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_settings_repo.py`

实现SQLAlchemy仓库

### 3.4 API端点
**新文件**: `app/backend/src/research_agent/api/v1/settings.py`

端点设计：
- `GET /api/v1/settings/global`: 获取所有全局配置
- `GET /api/v1/settings/global/{key}`: 获取特定全局配置
- `PUT /api/v1/settings/global/{key}`: 更新全局配置
- `GET /api/v1/settings/projects/{project_id}`: 获取项目所有配置
- `GET /api/v1/settings/projects/{project_id}/{key}`: 获取项目特定配置
- `PUT /api/v1/settings/projects/{project_id}/{key}`: 设置项目配置
- `DELETE /api/v1/settings/projects/{project_id}/{key}`: 删除项目配置（恢复为全局）
- `POST /api/v1/settings/validate-api-key`: 验证API Key

### 3.5 配置集成到现有系统
**修改文件**: `app/backend/src/research_agent/config.py`

- 添加`get_setting_from_db(key, project_id=None)`方法
- 修改`get_settings()`以支持从数据库读取配置

**修改文件**: `app/backend/src/research_agent/api/deps.py`

- 修改`get_llm_service()`和`get_embedding_service()`以支持从配置中心读取API Key和模型

**修改文件**: `app/backend/src/research_agent/application/graphs/rag_graph.py`

- 修改`create_rag_graph()`以支持从配置中心读取RAG策略配置

### 3.6 API Key加密
**新文件**: `app/backend/src/research_agent/infrastructure/security/encryption.py`

使用Fernet对称加密：
- 从环境变量读取加密密钥（`ENCRYPTION_KEY`）
- 提供`encrypt()`和`decrypt()`函数

## 4. 前端实现

### 4.1 API客户端
**修改文件**: `app/frontend/src/lib/api.ts`

添加配置相关API：
- `getGlobalSettings()`
- `updateGlobalSetting(key, value)`
- `getProjectSettings(projectId)`
- `updateProjectSetting(projectId, key, value)`
- `deleteProjectSetting(projectId, key)`
- `validateApiKey(apiKey, provider)`

### 4.2 设置页面组件
**修改文件**: `app/frontend/src/app/settings/page.tsx`

实现以下配置面板：

#### 4.2.1 AI模型配置面板
- LLM模型选择下拉框（支持OpenRouter模型列表）
- Embedding模型选择下拉框
- 模型说明和推荐

#### 4.2.2 API Key配置面板
- OpenRouter API Key输入（密码框，支持显示/隐藏）
- OpenAI API Key输入（可选）
- API Key验证按钮
- 加密存储提示

#### 4.2.3 RAG策略配置面板
- RAG模式选择（traditional / long_context / auto）
- 检索配置：
  - Top-K数量滑块
  - 最小相似度阈值滑块
  - 混合搜索开关
- 生成配置：
  - 意图分类开关
  - 意图缓存开关
  - 引用格式选择
- 高级配置折叠面板

#### 4.2.4 项目配置覆盖
- 显示当前项目配置
- 允许为项目设置独立配置
- 显示配置继承关系（全局 vs 项目）

### 4.3 配置管理Hook
**新文件**: `app/frontend/src/hooks/useSettings.ts`

自定义Hook：
- `useGlobalSettings()`: 获取和更新全局配置
- `useProjectSettings(projectId)`: 获取和更新项目配置
- `useSetting(key, projectId?)`: 获取单个配置（支持优先级）

### 4.4 配置验证组件
**新文件**: `app/frontend/src/components/settings/ApiKeyValidator.tsx`

API Key验证组件：
- 输入API Key
- 验证按钮
- 验证状态显示（成功/失败）

## 5. 数据库迁移

### 5.1 创建配置表
**新文件**: `app/backend/alembic/versions/YYYYMMDD_HHMMSS_add_settings_tables.py`

创建迁移：
- 创建`global_settings`表
- 创建`project_settings`表
- 创建索引（project_id, key）
- 初始化默认全局配置

### 5.2 初始化默认配置
在迁移中插入默认全局配置：
- 从环境变量读取默认值
- 插入到`global_settings`表

## 6. 配置使用流程

### 6.1 配置读取流程
1. 检查项目配置（如果提供project_id）
2. 如果不存在，检查全局配置
3. 如果不存在，使用环境变量默认值

### 6.2 配置更新流程
1. 用户在前端修改配置
2. 前端调用API更新配置
3. 后端验证配置值
4. 如果是API Key，进行加密存储
5. 更新数据库
6. 返回更新后的配置

### 6.3 配置应用流程
1. 系统启动时加载全局配置到缓存
2. 请求处理时，根据project_id查找配置
3. 应用配置到LLM服务、RAG图等

## 7. 安全考虑

### 7.1 API Key加密
- 使用Fernet对称加密
- 加密密钥存储在环境变量中
- 数据库只存储加密后的值

### 7.2 配置验证
- API Key格式验证
- 模型名称验证
- 数值范围验证（如top_k > 0）

### 7.3 权限控制
- 全局配置：需要管理员权限（未来扩展）
- 项目配置：项目所有者可配置

## 8. 实施顺序

1. **Phase 1**: 数据库设计和迁移
   - 创建配置表
   - 创建数据库模型和仓库

2. **Phase 2**: 后端核心功能
   - 配置服务实现
   - API端点实现
   - 配置集成到现有系统

3. **Phase 3**: 前端基础UI
   - 设置页面重构
   - 配置表单组件
   - API集成

4. **Phase 4**: 高级功能
   - API Key验证
   - 配置继承显示
   - 项目配置覆盖

5. **Phase 5**: 测试和优化
   - 配置优先级测试
   - 性能优化（配置缓存）
   - 错误处理完善

## 9. 详细任务清单

### 后端任务

1. **数据库迁移**
   - [ ] 创建迁移文件，添加global_settings和project_settings表
   - [ ] 在models.py中添加GlobalSettingModel和ProjectSettingModel
   - [ ] 在迁移中初始化默认全局配置

2. **配置仓库**
   - [ ] 创建配置仓库接口（settings_repo.py）
   - [ ] 实现SQLAlchemy配置仓库（sqlalchemy_settings_repo.py）

3. **配置服务**
   - [ ] 创建配置服务层（settings_service.py）
   - [ ] 实现配置读取、设置、优先级逻辑
   - [ ] 实现API Key验证功能

4. **加密功能**
   - [ ] 实现API Key加密/解密功能（encryption.py）
   - [ ] 配置加密密钥环境变量

5. **API端点**
   - [ ] 创建settings.py API路由
   - [ ] 实现全局配置CRUD端点
   - [ ] 实现项目配置CRUD端点
   - [ ] 实现API Key验证端点

6. **系统集成**
   - [ ] 修改config.py，集成配置中心
   - [ ] 修改deps.py，支持从配置中心读取API Key和模型
   - [ ] 修改rag_graph.py，支持从配置中心读取RAG策略

### 前端任务

1. **API集成**
   - [ ] 在api.ts中添加配置相关API方法
   - [ ] 实现配置CRUD API调用

2. **配置管理Hook**
   - [ ] 创建useSettings Hook
   - [ ] 实现useGlobalSettings和useProjectSettings

3. **设置页面**
   - [ ] 重构settings/page.tsx
   - [ ] 实现AI模型配置面板
   - [ ] 实现API Key配置面板
   - [ ] 实现RAG策略配置面板
   - [ ] 实现项目配置覆盖功能

4. **组件开发**
   - [ ] 创建API Key验证组件
   - [ ] 创建配置继承显示组件

## 10. 配置项详细说明

### 10.1 模型配置

#### LLM模型 (llm_model)
- **类型**: String
- **默认值**: "openai/gpt-4o-mini"
- **可选值**: 
  - "openai/gpt-4o" (推荐用于复杂推理)
  - "openai/gpt-4o-mini" (快速对话)
  - "anthropic/claude-3.5-sonnet" (高质量分析)
  - "openai/o1-preview" (高级推理)
- **说明**: 用于RAG查询和对话的主要语言模型

#### Embedding模型 (embedding_model)
- **类型**: String
- **默认值**: "openai/text-embedding-3-small"
- **可选值**:
  - "openai/text-embedding-3-small" (快速，适合大多数场景)
  - "openai/text-embedding-3-large" (高质量，适合复杂语义)
- **说明**: 用于文档向量化的嵌入模型

### 10.2 API Key配置

#### OpenRouter API Key (openrouter_api_key)
- **类型**: String (加密存储)
- **格式**: "sk-or-v1-..."
- **说明**: OpenRouter API密钥，用于访问LLM和Embedding模型
- **验证**: 通过OpenRouter API验证有效性

#### OpenAI API Key (openai_api_key)
- **类型**: String (加密存储，可选)
- **格式**: "sk-..."
- **说明**: OpenAI直接API密钥，作为OpenRouter的备选方案
- **验证**: 通过OpenAI API验证有效性

### 10.3 RAG策略配置

#### RAG模式 (rag_mode)
- **类型**: String
- **默认值**: "traditional"
- **可选值**:
  - "traditional": 传统chunks模式，精确检索
  - "long_context": 文档全文模式，Mega-Prompt
  - "auto": 根据文档大小自动选择
- **说明**: 控制RAG检索和生成策略

#### 检索Top-K (retrieval_top_k)
- **类型**: Integer
- **默认值**: 5
- **范围**: 1-50
- **说明**: 检索文档数量

#### 最小相似度 (retrieval_min_similarity)
- **类型**: Float
- **默认值**: 0.0
- **范围**: 0.0-1.0
- **说明**: 相似度阈值，低于此值的文档将被过滤

#### 混合搜索 (use_hybrid_search)
- **类型**: Boolean
- **默认值**: True
- **说明**: 是否使用向量+关键词混合搜索

#### 意图分类 (intent_classification_enabled)
- **类型**: Boolean
- **默认值**: True
- **说明**: 是否启用基于意图的自适应RAG策略

#### 意图缓存 (intent_cache_enabled)
- **类型**: Boolean
- **默认值**: True
- **说明**: 是否缓存意图分类结果

#### 引用格式 (citation_format)
- **类型**: String
- **默认值**: "both"
- **可选值**:
  - "inline": 行内引用标记 [doc_01]
  - "structured": XML结构化引用 <cite>
  - "both": 同时支持两种格式
- **说明**: 控制RAG回答中的引用标记格式

## 11. 技术细节

### 11.1 配置缓存策略
- 全局配置在应用启动时加载到内存缓存
- 项目配置按需加载，支持LRU缓存
- 配置更新时自动失效缓存

### 11.2 配置验证规则
- API Key: 格式验证 + 实际API调用验证
- 模型名称: 白名单验证（支持OpenRouter模型列表）
- 数值配置: 范围验证
- 布尔配置: 类型验证

### 11.3 配置迁移策略
- 首次启动时，从环境变量迁移到数据库
- 支持配置回滚到环境变量
- 提供配置导出/导入功能（未来）

## 12. 未来扩展

### 12.1 用户级配置
- 如果未来引入用户系统，支持用户级配置
- 配置优先级：项目 > 用户 > 全局 > 环境变量

### 12.2 配置模板
- 预设配置模板（如"快速模式"、"高质量模式"）
- 一键应用配置模板

### 12.3 配置历史
- 记录配置变更历史
- 支持配置回滚

### 12.4 配置共享
- 项目配置导出为JSON
- 配置导入功能
