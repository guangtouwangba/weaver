# RAG CLI Client - RAG知识管理系统客户端

基于NotebookLM概念的企业级智能知识管理系统客户端。提供完整的主题管理、文件处理、智能对话和系统监控功能，支持多租户、异步处理和分布式部署，是面向开发者和运维人员的专业RAG工具。

## 🌟 核心特性

- 🎯 **智能主题管理**: 支持多项目知识库隔离和管理
- 📁 **多格式文档处理**: PDF、Word、Markdown等格式智能解析
- 💬 **高级对话系统**: 基于RAG的上下文感知对话
- 🔧 **企业级监控**: 完整的系统健康检查和性能监控
- 🚀 **异步处理引擎**: 支持大规模文件批量处理
- 🔐 **多租户架构**: 安全的数据隔离和权限管理
- 🎨 **现代CLI体验**: 美观的终端界面和丰富的交互功能

## 🚀 快速开始

### 1. 安装CLI依赖
```bash
# 安装CLI专用依赖
pip install -r cli_requirements.txt
```

### 2. 启动中间件服务
```bash
# 启动PostgreSQL, Weaviate, Redis等服务
make start
```

### 3. 初始化RAG系统
```bash
python cli.py init
```

### 4. 创建知识主题
```bash
# 创建新主题
python cli.py topics create "研究项目" --description "AI研究相关文档" --set-active
```

### 5. 上传和处理文件
```bash
# 上传文件或目录
python cli.py files upload /path/to/documents --process
```

### 6. 开始智能对话
```bash
python cli.py chat
```

## 📋 核心功能模块

### 🎯 主题管理 (`topics`)
管理知识主题，实现文档的逻辑分组和上下文隔离：

```bash
# 创建主题
python cli.py topics create "项目名称" --description "项目描述" --set-active

# 列出所有主题
python cli.py topics list --limit 20

# 切换当前主题
python cli.py topics switch <topic-id>

# 查看主题详情
python cli.py topics show [topic-id]

# 删除主题
python cli.py topics delete <topic-id> --force
```

### 📁 文件管理 (`files`)
智能文件处理，支持多格式文档的上传、索引和管理：

```bash
# 上传文件或目录
python cli.py files upload /path/to/docs --recursive --process

# 列出文件
python cli.py files list --topic-id <id> --status available

# 查看文件状态
python cli.py files status <file-id>

# 删除文件
python cli.py files delete <file-id> --force
```

**支持的文件格式：**
- PDF文档 (`.pdf`)
- 文本文件 (`.txt`)
- Markdown文档 (`.md`)
- Word文档 (`.docx`)

### 💬 智能对话 (`chat`)
基于RAG的智能对话系统，支持上下文检索和多模型切换：

```bash
# 开始对话
python cli.py chat --model gpt-4 --context-limit 5

# 指定主题对话
python cli.py chat --topic-id <id> --no-context
```

**对话内命令：**
- `/help` - 显示帮助信息
- `/clear` - 清除对话历史
- `/history` - 查看对话历史
- `/exit` 或 `/quit` - 退出对话

### 🔧 系统管理 (`system`)
系统状态监控、健康检查和维护操作：

```bash
# 查看系统状态
python cli.py system status

# 执行健康检查
python cli.py system health

# 系统清理
python cli.py system cleanup --confirm

# 数据备份
python cli.py system backup --output backup.sql
```

### 🚀 系统初始化 (`init`)
一键初始化RAG系统的所有组件：

```bash
python cli.py init
```

- ✅ 加载系统配置
- ✅ 初始化数据库连接
- ✅ 连接向量存储(Weaviate)
- ✅ 初始化AI服务
- ✅ 创建默认主题

### 🧹 数据管理 (`clear`)
安全清理CLI创建的测试数据：

```bash
python cli.py clear --no-confirm
```

## 🛠️ 配置说明

CLI工具复用项目的现有配置系统：

- **数据库配置**: 使用 `config/settings.py` 中的数据库设置
- **AI服务配置**: 需要配置OpenAI API密钥等
- **向量存储配置**: 默认连接本地Weaviate(localhost:8080)

### 环境变量配置示例
```bash
# AI服务配置
export AI__CHAT__OPENAI__API_KEY="your-openai-api-key"

# 数据库配置
export DATABASE__URL="postgresql://user:pass@localhost:5432/rag_db"

# 向量存储配置
export WEAVIATE_URL="http://localhost:8080"
```

## 📝 使用示例

### 完整工作流程
```bash
# 1. 初始化系统
python cli.py init

# 2. 创建知识主题
python cli.py topics create "我的项目" --description "项目相关文档" --set-active

# 3. 上传文档
python cli.py files upload ./documents --recursive --process

# 4. 查看系统状态
python cli.py system status

# 5. 开始智能对话
python cli.py chat --model gpt-4
```

### 智能对话示例
```
您: 文档中提到了什么技术栈？

AI: 根据文档内容，项目使用了以下技术栈：
- 后端框架：FastAPI + 异步编程
- 数据库：PostgreSQL + SQLAlchemy ORM
- 向量存储：Weaviate for 语义检索
- 缓存/消息队列：Redis + Celery
- 对象存储：MinIO (S3兼容)
- 监控：Prometheus + Grafana
- 容器化：Docker + Docker Compose

🔍 检索到 5 个相关上下文
```

### 高级对话功能
```bash
# 使用不同AI模型
python cli.py chat --model gpt-3.5-turbo

# 调整上下文检索数量
python cli.py chat --context-limit 10

# 禁用上下文检索（纯对话模式）
python cli.py chat --no-context

# 指定特定主题进行对话
python cli.py chat --topic-id abc123
```

## 🎯 核心优势

### 🚀 企业级功能
- **主题隔离**: 多租户支持，不同项目数据完全隔离
- **异步处理**: 大文件批量处理，支持后台任务队列
- **智能检索**: 基于Weaviate的语义相似度搜索
- **多模型支持**: 支持OpenAI GPT系列和其他兼容模型
- **状态管理**: 完整的文件处理状态追踪和错误恢复

### 💡 开发体验
- **直接复用**: 与Web应用共享相同的Service层架构
- **类型安全**: 完整的类型提示和参数验证
- **美观界面**: Rich库提供的现代化终端界面
- **命令补全**: Click框架的智能命令补全和帮助
- **错误处理**: 友好的错误提示和调试信息

### 🔧 运维友好
- **健康检查**: 全组件健康状态监控
- **数据备份**: 完整的系统数据备份和恢复
- **清理工具**: 安全的测试数据清理，不影响生产数据
- **配置管理**: 灵活的环境变量和配置文件支持

## ⚠️ 重要注意事项

### 🔧 系统要求
1. **Python版本**: 需要Python 3.8或更高版本
2. **中间件服务**: 必须先启动PostgreSQL、Weaviate、Redis等服务
3. **API密钥**: 需要有效的OpenAI API密钥或其他AI服务密钥
4. **系统资源**: 推荐至少8GB内存用于向量存储和大文件处理

### 🔒 安全和权限
1. **数据隔离**: 虽然共享数据库，但CLI有独立的主题管理
2. **API密钥**: 确保API密钥安全存储，不要提交到版本控制
3. **文件权限**: CLI需要读取上传文件的权限
4. **网络访问**: 需要访问AI服务的网络权限

### 🚀 性能考虑
1. **大文件处理**: 大文件建议使用`--process`选项进行异步处理
2. **批量操作**: 大量文件上传可能需要较长时间
3. **内存使用**: 向量存储和AI服务会消耗较多内存
4. **网络延迟**: AI服务响应时间取决于网络和服务可用性

### 🔄 版本兼容性
1. **向后兼容**: 新版本CLI兼容现有数据结构
2. **配置迁移**: 从旧版本升级时可能需要更新配置
3. **依赖更新**: 定期更新依赖包以获得最新功能和安全修复

## ✅ **企业级CLI客户端特性**

全新升级的RAG CLI Client提供企业级功能支持：

### 🎯 主题管理系统
- ✅ **多项目支持**: 创建、切换、删除知识主题
- ✅ **数据隔离**: 不同主题间完全隔离，支持多租户
- ✅ **状态追踪**: 完整的主题生命周期管理

### 📁 智能文件处理
- ✅ **多格式支持**: PDF、Word、Markdown、文本文件
- ✅ **批量处理**: 目录递归扫描，支持大量文件
- ✅ **异步任务**: 后台处理，支持进度追踪
- ✅ **状态管理**: 文件处理状态实时监控

### 💬 高级对话功能
- ✅ **多模型支持**: GPT-4、GPT-3.5等模型切换
- ✅ **智能检索**: 可配置的上下文检索数量
- ✅ **对话管理**: 历史记录、清理、导出功能
- ✅ **命令系统**: 丰富的对话内命令支持

### 🔧 系统监控与维护
- ✅ **健康检查**: 全组件状态监控和诊断
- ✅ **性能监控**: 系统资源使用情况
- ✅ **数据备份**: 完整的备份和恢复机制
- ✅ **清理工具**: 安全的数据清理和维护

### 测试结果示例
```bash
# 系统初始化
python cli.py init
# 🎉 RAG系统初始化完成!

# 创建主题
python cli.py topics create "AI研究"
# ✅ 主题创建成功! 🎯 已设为当前主题

# 上传文件
python cli.py files upload ./docs --process
# ✅ 文件上传完成! 成功: 15 个
# 🔄 开始异步处理文件...

# 开始对话
python cli.py chat --model gpt-4
# 💬 智能对话模式 - 当前主题: AI研究
```

## 🐛 故障排除

### 数据库连接失败
```bash
# 检查数据库服务状态
make status
python cli.py system health

# 手动启动数据库
docker-compose up -d postgres

# 检查数据库健康状态
python cli.py system status
```

### 向量存储连接失败
```bash
# 检查Weaviate服务
curl http://localhost:8080/v1/meta
python cli.py system health

# 重启服务
docker-compose restart weaviate

# 验证连接
python cli.py system status
```

### AI服务初始化失败
```bash
# 检查API密钥配置
echo $AI__CHAT__OPENAI__API_KEY
python cli.py system health

# 在.env文件中配置
echo 'AI__CHAT__OPENAI__API_KEY=your-key-here' >> .env

# 重新初始化
python cli.py init
```

### 主题和文件管理问题
```bash
# 查看当前主题
python cli.py topics list

# 切换或创建主题
python cli.py topics create "新主题" --set-active

# 检查文件状态
python cli.py files list --status failed

# 重新处理失败的文件
python cli.py files upload /path/to/files --process
```

## 🔄 架构集成

### 与Web应用的协同
RAG CLI Client与Web应用完全集成，共享核心架构：

**共享组件：**
- 🗄️ **数据库**: PostgreSQL + SQLAlchemy模型
- 🧠 **Service层**: 完全相同的业务逻辑
- ⚙️ **配置系统**: 统一的环境变量和设置
- 🤖 **AI服务**: OpenAI等模型接口
- 🔍 **向量存储**: Weaviate语义搜索引擎
- 📦 **对象存储**: MinIO文件存储后端

**独立管理：**
- 🎯 **主题空间**: CLI可以创建独立主题
- 📝 **会话管理**: 独立的对话历史和状态
- 🔧 **命令界面**: 专为开发和运维优化的CLI体验
- 🧪 **测试环境**: 安全的开发测试数据隔离

### 部署场景

**开发环境：**
- CLI用于快速开发测试和调试
- Web应用提供用户界面和API服务
- 共享本地开发数据库和服务

**生产环境：**
- CLI用于运维管理和系统监控
- Web应用处理用户请求和业务逻辑
- 共享生产数据库，但CLI有独立的管理权限

**混合部署：**
- CLI可以连接远程RAG服务进行管理
- 支持多环境配置切换
- 统一的身份认证和权限管理