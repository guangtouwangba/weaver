# 🤖 RAG Question Answering System

一个基于检索增强生成(RAG)的智能问答系统，专门针对ArXiv学术论文进行问答。

## 🎯 功能特性

- **🔍 智能关键词选择**: 从已收集的论文中选择关键词
- **🧠 AI驱动问答**: 基于论文内容提供详细答案和引用
- **📚 语义搜索**: 基于内容相似度搜索相关论文
- **⚡ 快速检索**: 使用向量数据库进行高效检索
- **💬 友好界面**: 基于Terminal的交互式界面
- **🔑 OpenAI集成**: 使用OpenAI的最新嵌入模型和GPT

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装RAG系统依赖
pip install -r requirements-rag.txt
```

### 2. 设置OpenAI API密钥

**方法1: 使用.env文件 (推荐)**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，设置你的API密钥
# OPENAI_API_KEY=your-openai-api-key-here
```

**方法2: 设置环境变量**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. 确保有论文数据

```bash
# 首先运行论文获取系统收集论文
python simple_paper_fetcher.py
```

### 4. 启动RAG系统

```bash
python rag_main.py
```

## 📋 使用流程

### 1. 选择关键词并构建索引
- 系统会显示数据库中可用的关键词
- 选择感兴趣的关键词（如：rag, agent, llm等）
- 系统自动构建向量索引

### 2. 开始问答
- 输入问题，系统会：
  - 在论文中搜索相关内容
  - 使用AI生成详细答案
  - 提供论文引用和相似度分数

### 3. 搜索论文
- 基于内容相似度搜索相关论文
- 查看论文摘要和相关信息

## 🏗️ 系统架构

```
RAG系统架构:
├── 📄 PDF文本提取 (PyPDF2/pdfplumber)
├── 🔤 文本分块处理 (智能分割)
├── 🧮 向量化 (OpenAI embeddings)
├── 💾 向量数据库 (ChromaDB)
├── 🔍 语义检索 (相似度搜索)
├── 🤖 AI生成 (OpenAI GPT)
└── 💻 Terminal界面 (rich)
```

## ⚙️ 配置说明

RAG系统的配置在 `config.yaml` 的 `rag` 部分：

```yaml
rag:
  # 向量数据库设置
  vector_db:
    type: "chroma"
    persist_directory: "./rag_vector_db"
    collection_name: "arxiv_papers"
  
  # 文本处理设置
  text_processing:
    chunk_size: 1000          # 文本块大小
    chunk_overlap: 200        # 重叠大小
    max_chunks_per_doc: 50    # 每文档最大块数
  
  # 嵌入模型设置 (使用OpenAI)
  embeddings:
    provider: "openai"        # openai 或 sentence-transformers
    model: "text-embedding-3-small"  # OpenAI嵌入模型
    # 可选模型:
    # - text-embedding-3-small (推荐, 性价比高)
    # - text-embedding-3-large (最高质量)
    # - text-embedding-ada-002 (经典模型)
  
  # LLM设置
  llm:
    provider: "openai"
    model: "gpt-3.5-turbo"    # 或 "gpt-4"
    max_tokens: 2000
    temperature: 0.1
  
  # 检索设置
  retrieval:
    top_k: 5                  # 返回最相似的K个结果
    similarity_threshold: 0.7  # 相似度阈值
    max_context_length: 4000  # 最大上下文长度
```

## 🔑 API密钥管理

### .env文件配置 (推荐方式)

1. **复制模板文件**:
   ```bash
   cp .env.example .env
   ```

2. **编辑.env文件**:
   ```bash
   # OpenAI API Configuration
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   
   # OSS Configuration (如果使用OSS存储)
   OSS_ACCESS_KEY_ID=your_oss_access_key
   OSS_ACCESS_KEY_SECRET=your_oss_secret_key
   ```

3. **安全提醒**:
   - ✅ .env文件已在.gitignore中，不会被提交到git
   - ✅ 系统会自动加载.env文件中的变量
   - ⚠️ 不要将真实的API密钥提交到代码仓库

### 环境变量方式

```bash
# 临时设置 (当前session有效)
export OPENAI_API_KEY="sk-your-api-key-here"

# 永久设置 (添加到 ~/.bashrc 或 ~/.zshrc)
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## 🎨 使用示例

### 关键词选择
```
Available Keywords:
┌─────────────┬────────┬──────────────────────────────────────┐
│ Keyword     │ Papers │ Example Papers                       │
├─────────────┼────────┼──────────────────────────────────────┤
│ rag         │   15   │ Retrieval-Augmented Generation...   │
│ agent       │   23   │ Multi-Agent Systems for AI...       │
│ llm         │   18   │ Large Language Models Survey...     │
└─────────────┴────────┴──────────────────────────────────────┘

Enter keywords or numbers: rag, agent
```

### 问答示例
```
❓ Your question: What are the main challenges in RAG systems?

🤖 Answer:
Based on the research papers, the main challenges in RAG systems include:

1. **Retrieval Quality**: Ensuring that the most relevant information is retrieved...
2. **Context Integration**: Effectively combining retrieved information with generation...
3. **Scalability**: Managing large document collections efficiently...

📚 Sources:
┌───────────────┬─────────────────────────────────────────┬────────────┐
│ ArXiv ID      │ Title                                   │ Similarity │
├───────────────┼─────────────────────────────────────────┼────────────┤
│ 2308.12345    │ Challenges in Retrieval-Augmented...   │ 89.2%      │
│ 2309.67890    │ Improving RAG System Performance...     │ 85.7%      │
└───────────────┴─────────────────────────────────────────┴────────────┘
```

## 🔧 高级配置

### OpenAI嵌入模型对比

| 模型 | 维度 | 优点 | 使用场景 |
|------|------|------|----------|
| `text-embedding-3-small` | 1536 | 性价比高，速度快 | 一般问答，大量文档 |
| `text-embedding-3-large` | 3072 | 最高质量 | 高精度要求的场景 |
| `text-embedding-ada-002` | 1536 | 经典稳定 | 兼容性要求高的场景 |

### 性能优化配置

```yaml
# 针对大量文档
text_processing:
  chunk_size: 800        # 减小块大小节省token
  max_chunks_per_doc: 30 # 限制每文档块数

# 针对精确检索
retrieval:
  top_k: 10              # 增加候选数量
  similarity_threshold: 0.8 # 提高阈值

# 更强的LLM
llm:
  model: "gpt-4"         # 更强但更慢更贵
```

### 成本控制

```yaml
# 节约成本的配置
embeddings:
  model: "text-embedding-3-small"  # 选择小模型

text_processing:
  chunk_size: 500        # 减小块大小
  max_chunks_per_doc: 20 # 限制块数量

retrieval:
  top_k: 3               # 减少检索数量

llm:
  model: "gpt-3.5-turbo" # 使用较便宜的模型
  max_tokens: 1000       # 限制生成长度
```

## 🔧 高级功能

### 检查依赖和配置
```bash
python rag_main.py --check-deps
```

### 自定义配置文件
```bash
python rag_main.py my_rag_config.yaml
```

### 调试模式
```bash
python rag_main.py --log-level DEBUG
```

## 🐛 故障排除

### 常见问题

1. **OpenAI API密钥错误**
   ```
   错误: OPENAI_API_KEY environment variable not set
   解决: 
   - 检查.env文件中的API密钥
   - 确保.env文件在项目根目录
   - 验证API密钥格式: sk-...
   ```

2. **API配额超限**
   ```
   错误: Rate limit exceeded
   解决: 
   - 检查OpenAI账户配额
   - 降低batch_size减少并发请求
   - 等待配额重置
   ```

3. **嵌入维度不匹配**
   ```
   错误: Embedding dimension mismatch
   解决: 
   - 清除向量数据库: rm -rf ./rag_vector_db
   - 重新构建索引
   ```

4. **依赖缺失**
   ```
   错误: ImportError: No module named 'openai'
   解决: pip install -r requirements-rag.txt
   ```

### 调试命令
```bash
# 检查系统状态
python rag_main.py --check-deps

# 查看详细日志
python rag_main.py --log-level DEBUG

# 查看日志文件
tail -f rag_qa.log

# 测试API连接
python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI()
print('API连接正常')
"
```

## 📊 性能监控

### Token使用监控
系统会自动记录每次问答的token使用情况：
- **Prompt tokens**: 输入的token数量
- **Completion tokens**: 生成的token数量
- **Total tokens**: 总token使用量

### 成本估算
- `gpt-3.5-turbo`: ~$0.002/1K tokens
- `text-embedding-3-small`: ~$0.00002/1K tokens
- 平均每次问答约消耗1000-3000 tokens

## 🔄 从sentence-transformers迁移

如果你之前使用sentence-transformers，迁移到OpenAI embeddings：

1. **备份现有索引**:
   ```bash
   mv rag_vector_db rag_vector_db_backup
   ```

2. **更新配置**:
   ```yaml
   embeddings:
     provider: "openai"
     model: "text-embedding-3-small"
   ```

3. **重建索引**:
   - 启动RAG系统
   - 重新选择关键词
   - 系统会自动使用新的embedding模型重建索引

## 💡 最佳实践

1. **API密钥安全**:
   - 使用.env文件存储API密钥
   - 定期轮换API密钥
   - 不要在代码中硬编码密钥

2. **成本控制**:
   - 选择合适的嵌入模型
   - 合理设置chunk_size和top_k
   - 监控token使用情况

3. **质量优化**:
   - 选择具体的关键词提高检索精度
   - 调整similarity_threshold过滤低质量结果
   - 使用更强的GPT模型获得更好的答案

4. **性能优化**:
   - 合理设置batch_size避免API限制
   - 缓存常用的查询结果
   - 定期清理无用的向量数据

## 📞 支持

如遇到问题，请：

1. 查看日志文件 `rag_qa.log`
2. 运行 `python rag_main.py --check-deps` 检查配置
3. 参考本文档的故障排除部分
4. 检查OpenAI API状态和配额

---

祝您使用愉快！ 🎉