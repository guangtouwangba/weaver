# 本地RAG系统迭代测试指南

## 🎯 概述

`test_rag_local.py` 是一个用于本地持续迭代和测试RAG系统的脚本，使用真实的组件而不是模拟组件。

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装必要的依赖
pip install openai

# 设置OpenAI API密钥
export OPENAI_API_KEY='your_api_key_here'
```

### 2. 准备测试文档

将要测试的文档放入 `test_documents/` 目录：

```
test_documents/
├── 段永平01 段永平投资问答录(投资逻辑篇) (段永平) (Z-Library).pdf
├── 段永平投资回答录 (芒格书院) (Z-Library).pdf
└── 你的其他文档...
```

支持的文档格式：
- PDF (.pdf)
- 文本文件 (.txt)
- Markdown (.md)
- Word文档 (.docx)
- HTML (.html)

### 3. 运行测试

#### 方式1：使用启动脚本（推荐）
```bash
./run_rag_test.sh
```

#### 方式2：直接运行
```bash
# 设置环境变量并运行
OPENAI_API_KEY='your_api_key_here' python test_rag_local.py

# 或者先导出环境变量
export OPENAI_API_KEY='your_api_key_here'
python test_rag_local.py
```

## ⚙️ 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API密钥（必需） |
| `USE_WEAVIATE` | `false` | 是否使用Weaviate向量存储 |
| `WEAVIATE_URL` | `http://localhost:8080` | Weaviate服务地址 |

### 配置示例

```bash
# 使用内存向量存储（默认）
export USE_WEAVIATE=false
python test_rag_local.py

# 使用Weaviate向量存储
export USE_WEAVIATE=true
export WEAVIATE_URL=http://localhost:8080
python test_rag_local.py
```

## 🔧 系统架构

### 核心组件

1. **OpenAI嵌入服务** - 真实的OpenAI text-embedding-3-small
2. **向量存储** - 内存存储或Weaviate
3. **LLM服务** - 真实的OpenAI GPT-4o-mini
4. **文档处理** - 真实的文档加载和分块处理

### 处理流程

```
文档加载 → 分块处理 → 生成嵌入 → 存储到向量库
                                      ↓
用户查询 → 生成查询嵌入 → 相似度检索 → 构建上下文 → LLM生成回答
```

## 📊 测试功能

### 自动测试查询

脚本会根据文档内容自动选择合适的测试查询：

**投资文档**（检测到"投资"、"段永平"等关键词）：
- 段永平的投资理念是什么？
- 什么是价值投资？
- 如何选择好的投资标的？
- 投资中最重要的原则有哪些？
- 等等...

**通用文档**：
- 这个文档主要讲了什么内容？
- 请总结一下主要观点
- 有哪些重要的概念或原则？
- 等等...

### 交互式测试

测试完成后可以进入交互式模式，输入自定义查询进行实时测试。

### 测试报告

系统会自动生成详细的JSON测试报告，包含：
- 查询成功率
- 平均处理时间
- Token使用统计
- 检索文档数量
- 每个查询的详细结果

## 📈 性能监控

### 关键指标

- **处理时间**: 每个查询的端到端处理时间
- **Token使用**: OpenAI API的Token消耗
- **检索质量**: 相似度分数和检索文档数量
- **成功率**: 查询处理成功的比例

### 示例输出

```
--- 测试查询 1/10 ---
查询: 段永平的投资理念是什么？
回答: 段永平的投资理念主要基于价值投资...
检索到 3 个相关文档
处理时间: 1234.56ms
Token使用: 1500

相关文档:
  1. [0.892] 段永平投资问答录: 价值投资是我一直坚持的理念...
  2. [0.845] 段永平投资回答录: 投资最重要的是理解企业的内在价值...
```

## 🔄 迭代开发

### 配置调优

在 `test_rag_local.py` 中可以调整以下参数：

```python
@dataclass
class RAGConfig:
    # 文档处理配置
    chunk_size: int = 1000          # 分块大小
    chunk_overlap: int = 200        # 分块重叠
    min_chunk_size: int = 100       # 最小分块大小
    max_chunk_size: int = 2000      # 最大分块大小
    
    # 检索配置
    max_results: int = 5            # 最大检索结果数
    score_threshold: float = 0.0    # 相似度阈值
    
    # 生成配置
    temperature: float = 0.7        # LLM温度
    max_tokens: int = 1000          # 最大生成Token数
```

### 实验流程

1. **修改配置参数**
2. **运行测试脚本**
3. **分析测试报告**
4. **调整参数并重复**

### A/B测试

可以创建多个配置版本进行对比：

```bash
# 测试配置A
python test_rag_local.py  # 使用默认配置

# 修改配置后测试配置B
# 编辑 test_rag_local.py 中的 RAGConfig
python test_rag_local.py

# 对比两次的测试报告
```

## 🛠️ 故障排除

### 常见问题

1. **OpenAI API密钥错误**
   ```
   ❌ 请设置OPENAI_API_KEY环境变量
   ```
   解决：确保正确设置了有效的OpenAI API密钥

2. **文档加载失败**
   ```
   ❌ 没有加载任何文档，请检查test_documents目录
   ```
   解决：确保 `test_documents/` 目录存在且包含支持的文档格式

3. **Weaviate连接失败**
   ```
   Weaviate初始化失败: ..., 使用内存存储
   ```
   解决：检查Weaviate服务是否运行，或设置 `USE_WEAVIATE=false`

### 调试模式

修改日志级别以获取更详细的调试信息：

```python
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📝 扩展开发

### 添加新的文档类型

1. 在 `modules/file_loader/` 中添加新的加载器
2. 在 `FileLoaderFactory` 中注册新的文件类型
3. 测试脚本会自动支持新的文档类型

### 添加新的向量存储

1. 实现 `IVectorStore` 接口
2. 在 `LocalRAGPipeline` 中添加初始化逻辑
3. 通过环境变量控制选择

### 自定义测试查询

修改 `INVESTMENT_QUERIES` 或 `GENERAL_QUERIES` 列表：

```python
CUSTOM_QUERIES = [
    "你的自定义查询1",
    "你的自定义查询2",
    # ...
]
```

## 🎯 最佳实践

1. **文档准备**：确保文档质量和相关性
2. **参数调优**：从默认参数开始，逐步优化
3. **批量测试**：使用多个查询评估整体性能
4. **版本控制**：记录每次实验的配置和结果
5. **成本控制**：监控OpenAI API的Token使用

## 📊 示例报告

测试完成后会生成类似以下的报告：

```json
{
  "timestamp": "2024-01-15T09:03:00.000Z",
  "config": {
    "embedding_model": "text-embedding-3-small",
    "chat_model": "gpt-4o-mini",
    "chunk_size": 1000,
    "max_results": 5
  },
  "summary": {
    "total_queries": 10,
    "successful_queries": 10,
    "success_rate": 100.0
  },
  "performance": {
    "average_processing_time_ms": 1234.56,
    "average_tokens": 1500,
    "total_tokens_used": 15000
  }
}
```

这个脚本为你提供了一个完整的本地RAG开发和测试环境，支持快速迭代和性能优化！🚀
