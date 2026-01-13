# Tasks: Refactor Chat to RAG Agent

## 1. Foundation Setup
- [ ] 1.1 创建 `app/backend/src/research_agent/application/agents/` 目录结构
- [ ] 1.2 创建 `__init__.py` 导出模块

## 2. Tools 封装
- [ ] 2.1 创建 `agents/rag_tools.py` - 定义 Tool 基类和接口
- [ ] 2.2 封装 `VectorRetrieveTool` - 基于 `retrieve()` 函数
- [ ] 2.3 封装 `RerankTool` - 基于 `rerank()` 函数
- [ ] 2.4 封装 `GradeDocumentsTool` - 基于 `grade_documents()` 函数
- [ ] 2.5 封装 `QueryRewriteTool` - 基于 `transform_query()` 函数
- [ ] 2.6 封装 `MemoryRetrieveTool` - 基于 `retrieve_memory()` 函数
- [ ] 2.7 封装 `GenerateAnswerTool` - 基于 `generate()` 函数
- [ ] 2.8 为每个 Tool 添加单元测试

## 3. Memory 模块
- [ ] 3.1 创建 `agents/rag_memory.py` - Memory 接口定义
- [ ] 3.2 实现 SessionSummaryMemory - 整合 `get_session_summary()`
- [ ] 3.3 实现 EpisodicMemory - 整合 `retrieve_memory()`
- [ ] 3.4 实现 RAGAgentMemory 统一接口
- [ ] 3.5 添加 Memory 模块测试

## 4. Agent 核心实现
- [ ] 4.1 创建 `agents/rag_agent.py` - Agent 主类
- [ ] 4.2 定义 `RAGAgentState` - 扩展 GraphState
- [ ] 4.3 实现 Agent System Prompt - **全局采用 `build_mega_prompt` (XML模式)**
- [ ] 4.4 实现 Agent StateGraph - 使用 LangGraph
- [ ] 4.5 实现 Tool Router - 根据 intent 选择 tools
- [ ] 4.6 实现 Streaming 支持 - 适配 XML Citation Streaming (`StreamingCitationParser`)
- [ ] 4.7 添加 Agent 集成测试

## 5. 集成与迁移
- [ ] 5.1 修改 `stream_message.py` - 集成 RAGAgent
- [ ] 5.2 添加配置开关 - 支持新旧实现切换
- [ ] 5.3 整合 `ContextEngine` - 与 Agent 对接
- [ ] 5.4 整合 `StreamEventProcessor` - 处理 Agent 事件
- [ ] 5.5 端到端测试验证

## 6. 清理与优化
- [ ] 6.1 移除 `rag_mode` 相关配置和逻辑
- [ ] 6.2 提取可复用代码到 utils
- [ ] 6.3 更新文档和注释
- [ ] 6.4 性能测试对比

## Dependencies
- 2.x 依赖 1.x 完成
- 3.x 可与 2.x 并行
- 4.x 依赖 2.x 和 3.x 完成
- 5.x 依赖 4.x 完成
- 6.x 依赖 5.x 完成

## Parallelizable Work
- 2.2-2.7 可并行开发
- 3.2-3.4 可并行开发
