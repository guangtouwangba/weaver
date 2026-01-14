# Design: RAG Agent Architecture

## Context
当前的 RAG 实现分散在多个文件中：
- `rag_graph.py` (2374 行) - 包含所有节点函数、状态定义、图构建
- `stream_message.py` - Use Case 入口，处理 streaming
- `context_engine.py` - 上下文聚合
- `rag_prompt.py` - Prompt 模板

这种架构的问题：
1. 节点函数与图强耦合，难以独立测试
2. 固定的 workflow，无法根据场景动态调整
3. 添加新能力需要修改 graph builder
4. 与 LangGraph Agent 生态不兼容

## Goals / Non-Goals

### Goals
- 将 RAG 能力封装为可复用的 Tools
- 实现基于 LangGraph 的 Agent 架构
- 保留现有的 streaming 能力和 prompt 设计
- 提供更好的可测试性和可扩展性
- 支持动态 tool 调用决策

### Non-Goals
- 不改变对外 API 接口（StreamMessageInput/StreamEvent）
- 不重写 prompt 模板（保留 rag_prompt.py）
- 不改变 frontend 集成方式
- 不引入新的外部依赖（使用现有的 LangGraph）

## Decisions

### Decision 1: 使用 LangGraph StateGraph + Tools 架构
**选择**: 使用 LangGraph 的 `create_react_agent` 或自定义 StateGraph with tool nodes

**理由**:
- 现有代码已经使用 LangGraph，迁移成本低
- 支持 streaming
- 与 LangChain 工具生态兼容

**替代方案**:
- LangChain AgentExecutor: 更简单但 streaming 控制弱
- 纯自定义实现: 灵活但工作量大

### Decision 2: Tool 封装粒度
**选择**: 中粒度封装，每个核心能力一个 Tool

| Tool | 源函数 | 职责 |
|------|--------|------|
| `vector_retrieve` | `retrieve()` | 向量检索 |
| `rerank` | `rerank()` | LLM 重排序 |
| `grade` | `grade_documents()` | 相关性评估 |
| `query_rewrite` | `transform_query()` | 查询重写 |
| `memory_retrieve` | `retrieve_memory()` | 记忆检索 |

**理由**:
- 保持工具独立性，便于测试
- 粒度适中，不会产生过多 tool calls
- 每个 tool 有明确的输入输出

### Decision 3: Memory 模块设计
**选择**: 统一的 Memory 接口，内部包含三种记忆类型

```python
class RAGAgentMemory:
    async def get_session_summary(project_id) -> str
    async def retrieve_relevant_memories(query, project_id) -> list[Memory]
    async def store_interaction(question, answer, project_id) -> None
```

**理由**:
- 封装复杂性，对 Agent 暴露简单接口
- 支持未来扩展新的记忆类型

### Decision 4: Agent State 设计
**选择**: 继承并扩展现有 GraphState

```python
class RAGAgentState(TypedDict):
    # 继承现有字段
    question: str
    documents: list[Document]
    generation: str
    # Agent 特有字段
    tool_calls: list[ToolCall]
    agent_scratchpad: list[BaseMessage]
    should_continue: bool
```

### Decision 5: Prompt 集成策略 (XML Mega-Prompt Default)
**选择**: 全局默认使用 XML Mega-Prompt 模式，废弃 `rag_mode`。

**Prompt 结构**:
```xml
<system_instruction>
You are a RAG Agent. Use the provided tools and context to answer.
...
</system_instruction>

<documents>
  <document id="doc_01">...</document>
  <document id="doc_02">...</document>
</documents>

<output_rules>
Must use <cite doc_id="..." quote="...">...</cite> for citations.
</output_rules>
```

**理由**:
- 提高模型指令遵循能力
- 统一 Citation 格式，简化前端解析逻辑
- 支持严格的幻觉校验 (Quote Verification)
- 简化配置，不再需要在 multiple modes 间切换

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    StreamMessageUseCase                          │
│  (入口，处理 SSE streaming，保持对外接口不变)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         RAGAgent                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Agent Executor                            ││
│  │  (LangGraph StateGraph / ReAct Loop)                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│          ┌──────────────────┼──────────────────┐                │
│          ▼                  ▼                  ▼                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │     Tools     │  │    Memory     │  │   Prompts     │       │
│  │  - retrieve   │  │  - session    │  │ (rag_prompt.py)│       │
│  │  - rerank     │  │  - episodic   │  └───────────────┘       │
│  │  - grade      │  │  - semantic   │                           │
│  │  - rewrite    │  └───────────────┘                           │
│  │  - generate   │                                              │
│  └───────────────┘                                              │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    ContextEngine                             ││
│  │  (Canvas Context + URL Content + Entity Tracking)           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Streaming 复杂性增加 | Tool calls 可能破坏流式输出 | 使用 LangGraph 的 streaming_mode="custom" |
| Agent 可能做出错误决策 | 调用不必要的 tools | 提供清晰的 tool 描述，使用 intent 引导 |
| 性能可能下降 | Agent 推理增加延迟 | 对简单查询使用快速路径 |
| 向后兼容性 | 现有测试可能失败 | 保持 StreamEvent 接口不变 |

## Migration Plan

### Phase 1: Tool 封装 (不改变行为)
1. 创建 `agents/rag_tools.py`，封装现有函数为 tools
2. 每个 tool 添加独立单元测试
3. **验证**: 现有 `rag_graph.py` 继续工作

### Phase 2: Memory 模块
1. 创建 `agents/rag_memory.py`
2. 整合 session summary + episodic memory
3. **验证**: Memory 功能正常

### Phase 3: Agent 实现
1. 创建 `agents/rag_agent.py`
2. 实现 Agent StateGraph
3. **验证**: Agent 能正确调用 tools

### Phase 4: 集成
1. 修改 `stream_message.py` 使用新 Agent
2. 保留 fallback 到旧实现
3. **验证**: E2E 测试通过

### Rollback
- 通过配置开关切换新旧实现
- 旧代码保留 2 个版本周期

## Open Questions

1. **Tool 调用策略**: 是否需要限制单次请求的最大 tool calls 次数？
2. **缓存策略**: Agent 决策结果是否需要缓存？
3. **观测性**: 如何记录 Agent 的决策过程用于调试？
