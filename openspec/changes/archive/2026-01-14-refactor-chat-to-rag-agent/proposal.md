# Change: Refactor Chat to RAG Agent

## Why
当前的 chat 模块 (`stream_message.py` + `rag_graph.py`) 虽然功能完整，但架构上是一个固定的 workflow，缺乏 Agent 的灵活性和可扩展性。将其重构为基于 LangGraph 的 RAG Agent 可以：
- 提供更好的可组合性（Tools 可独立测试、复用）
- 支持动态规划（根据 intent 动态选择 tools）
- 更易于添加新能力（如 web search、calculator 等）
- 与 LangChain/LangGraph 生态更好地对齐

## What Changes

### Core Architecture
- **[NEW]** `agents/rag_agent.py` - RAG Agent 主类，封装完整的 Agent 逻辑
- **[NEW]** `agents/rag_tools.py` - 将现有节点函数封装为 `@tool` 装饰器的工具集
- **[NEW]** `agents/rag_memory.py` - Memory 模块封装（Episodic + Semantic + Session）
- **[MODIFY]** `stream_message.py` - 简化为 Agent 的调用入口
- **[MODIFY]** `rag_prompt.py` - 将 `build_mega_prompt` 设为默认 Prompt 构建方式

### Global Mega-Prompt
- 移除 `rag_mode` 配置，全局默认使用 **XML Mega-Prompt** 模式
- 所有 Generation 步骤均使用 XML 结构化上下文 (`<documents>...`)
- 强制使用 `<cite>` 标签进行引用，以支持前端精确跳转和后端幻觉校验

### Tools 封装
将 `rag_graph.py` 中的核心能力封装为独立 Tools：
- `vector_retrieve` - 向量检索工具
- `rerank_documents` - 文档重排序工具  
- `grade_documents` - 文档相关性评估工具
- `query_rewrite` - 查询重写工具
- `retrieve_memory` - 记忆检索工具
- `generate_answer` - 答案生成工具

### Memory 模块
整合现有的 memory 功能：
- Session Summary（会话摘要）
- Episodic Memory（情景记忆：过去的 Q&A）
- Semantic Memory（语义记忆：向量检索）

### Streaming 保留
- 保留现有的 SSE streaming 能力
- 保留 `StreamingRefInjector` 的视频时间戳处理
- 保留 `StreamEventProcessor` 的事件处理逻辑

### Prompt 保留
- 保留 `rag_prompt.py` 中的所有 prompt 设计
- Agent 系统 prompt 与现有 prompt 集成

## Impact
- Affected specs: `agents` (MODIFIED - 添加 RAG Agent requirement)
- Affected code:
  - `app/backend/src/research_agent/application/graphs/rag_graph.py` (refactor to tools)
  - `app/backend/src/research_agent/application/use_cases/chat/stream_message.py` (simplify)
  - `app/backend/src/research_agent/application/use_cases/chat/context_engine.py` (integrate with agent)
  - New: `app/backend/src/research_agent/application/agents/` directory
