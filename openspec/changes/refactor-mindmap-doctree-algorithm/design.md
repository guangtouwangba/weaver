# Design: Direct Generation Algorithm for Mindmap

## Context
The original DocTree algorithm used a complex 5-phase pipeline:
1. Chunking - Split text into ~2000 token chunks
2. Semantic Parsing - N LLM calls to extract topics per chunk
3. Tree Aggregation - log(N) LLM calls for clustering + summarization
4. MapReduce - 2×nodes LLM calls for concept aggregation (disabled)
5. Mermaid Generation

With modern LLMs having **massive context windows** (Gemini 2.5 Flash: 1M tokens, GPT-4: 128K, Claude: 200K), this complexity is unnecessary for most documents.

## Goals
- Simplify to a 2-step workflow: Generate → Refine
- Reduce LLM calls from N+log(N) to **2 calls total**
- Leverage full document context for better understanding
- Maintain source reference capability
- Support multi-language output (Chinese/English)

## Non-Goals
- Chunking/aggregation for extremely long documents (>500K tokens)
- Complex tree data structures
- Embeddings and clustering

## Algorithm Overview

| Phase | LLM Calls | Description |
|-------|-----------|-------------|
| 1. Direct Generation | 1 | Single call generates entire mindmap |
| 2. Refinement | 1 | Cleans duplicates, improves structure |
| **Total** | **2** | 98% reduction from original algorithm |

### Phase 1: Direct Generation

Single LLM call with carefully designed prompt that instructs the model to:

**Extraction Principles**:
1. Extract 5-10 **core points** (Layer 1)
2. Add **elaboration** for each point (Layer 2)
3. Include **supporting details** - cases, data, quotes (Layer 3)
4. Preserve specific information: names, places, numbers, dates
5. Show causality: cause → effect, problem → solution
6. Remove noise: acknowledgements, greetings, repetition

**Output Format**: Markdown outline with `#` heading and `-` bullet hierarchy

```markdown
# Root Title (summarize theme)
- Core Point 1
  - Elaboration 1.1
    - Detail 1.1.1
  - Elaboration 1.2
- Core Point 2
  - Elaboration 2.1
```

### Phase 2: Refinement

Single LLM call to clean up the generated mindmap:

**Critical Fixes**:
1. **Parent-child duplicates**: Delete child if same name as parent
2. **Sibling duplicates**: Keep only one
3. **Mixed categories**: Reorganize misplaced nodes
4. **Depth control**: Keep to 3-4 levels max
5. **Content cleanup**: Remove usernames, acknowledgements
6. **Preserve specifics**: Keep names, companies, book titles

## Data Flow

```
Input Text (up to 500K tokens)
       ↓
[Direct Generation] ──→ Raw Markdown Outline
       ↓
[Refinement] ──→ Clean Markdown Outline
       ↓
[Parse to Nodes] ──→ MindmapNode/MindmapEdge
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_DIRECT_TOKENS` | 500000 | Max tokens for direct generation |
| `MINDMAP_FORMAT` | markdown | Output format (markdown/mermaid) |
| `language` | auto | Prompt language (zh/en/auto) |

## Source Reference Strategy

Since we no longer chunk the document, source references use a **marker-based approach**:

### Input Preparation (Before LLM Call)

**For PDFs**: Annotate text with page markers
```
[PAGE:1]
This is content from page 1...

[PAGE:2]
This is content from page 2...
```

**For Videos**: Annotate transcript with timestamp markers
```
[TIME:00:00]
Introduction and overview...

[TIME:05:30]
Main topic discussion...
```

### Generation Prompt Enhancement

Add instruction to preserve source markers:
```
## 来源引用规则
- 当提取某个观点时，在末尾标注来源: `[Page X]` 或 `[MM:SS]`
- 如果某个观点跨越多个来源，标注主要来源
- 示例: "投资的核心是理解未来现金流 [Page 15]"
```

### Output Parsing

Parse markers from node content:
```markdown
- 投资原则 [Page 15]
  - 做对的事情 [Page 16-17]
  - 安全边际 [Page 23]
```

Extract to SourceRef:
```python
{
    "label": "投资原则",
    "source_refs": [
        {"type": "pdf", "page": 15}
    ]
}
```

### Video Timestamp Example
```markdown
- 投资策略分析 [12:30]
  - 价值投资核心 [12:45-15:20]
  - 案例: 苹果投资 [18:00]
```

Extract to SourceRef:
```python
{
    "label": "投资策略分析",
    "source_refs": [
        {"type": "video", "start_time": "12:30", "end_time": "12:30"}
    ]
}
```

### Click-to-Navigate Flow

```
User clicks node → Get source_refs → 
  If PDF: Open PDF viewer at page X
  If Video: Seek video player to timestamp MM:SS
```

## Prompts

### Direct Generation (Chinese)
```
请将以下文本转换为**结构化的知识笔记**。

## 核心原则
❌ 不要：平铺直叙，照搬原文结构
✅ 要做：提炼核心，按逻辑重组

## 输出结构
### 第1层：核心要点（5-10个）
### 第2层：展开说明
### 第3层：支撑细节

## 提取原则
1. **保留具体信息**：人名、公司名、地名、数字、日期、引用
2. **体现因果关系**：原因→结果，问题→解决方案
3. **区分主次**：核心观点 vs 补充说明
4. **删除噪音**：致谢、寒暄、重复内容
```

### Refinement Prompt
```
## 必须修复的问题
### 1. 父子重复（最重要！）
### 2. 分类逻辑混乱
### 3. 同级重复

## 优化规则
1. 严格去重
2. 分类逻辑统一
3. 层级控制: 3-4 层
4. 内容清理
5. 保留具体信息
```

## Decisions

### Decision: Use Markdown instead of Mermaid
**Why**: 
- Simpler syntax, easier for LLM to generate correctly
- Easier to parse into nodes/edges
- More readable for debugging

### Decision: Skip chunking for most documents
**Why**:
- Gemini 2.5 Flash handles 1M tokens
- Full context = better understanding
- No information loss from chunking boundaries
- Dramatically fewer API calls

### Decision: Two-pass refinement
**Why**:
- First pass focuses on content extraction
- Second pass focuses on structure cleanup
- Separation of concerns improves output quality

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Very long documents (>500K) | Can add chunking fallback in future |
| Source reference loss | Store document_id, enable text search |
| LLM output variability | Detailed prompts + refinement pass |
| Markdown parsing errors | Robust parser with fallbacks |

## Migration Plan
1. Implement new 2-step workflow
2. Parse Markdown output to MindmapNode/MindmapEdge
3. Maintain existing streaming events for frontend compatibility
4. Remove old chunking/aggregation code

## Open Questions
- Should we support Mermaid output as an option?
- How to handle source references for click-to-navigate?
