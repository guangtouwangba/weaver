"""LangGraph workflow for mindmap generation using direct generation algorithm.

Simple 2-step workflow:
1. Direct Generation - Single LLM call generates entire mindmap from full text
2. Refinement - Single LLM call cleans up duplicates and improves structure

This replaces the old complex DocTree algorithm (chunking → parsing → clustering → aggregation)
with a much simpler approach that leverages large context window LLMs.
"""

import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from research_agent.domain.agents.base_agent import OutputEvent, OutputEventType
from research_agent.domain.entities.output import MindmapEdge, MindmapNode, SourceRef
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger

# Layout constants (positions handled by frontend)
NODE_WIDTH = 200
NODE_HEIGHT = 80

# Configuration
MAX_DIRECT_TOKENS = 500000  # Max tokens for direct generation (configurable)
DEFAULT_MAX_DEPTH = 3

# Type alias for event emission callback
EventCallback = Callable[[OutputEvent], Awaitable[None]]


async def _noop_emit(event: OutputEvent) -> None:
    """Default no-op event emitter for testing."""
    pass


class MindmapState(TypedDict):
    """State passed between nodes in the mindmap generation workflow."""

    # Input
    document_content: str
    document_title: str
    document_id: Optional[str]  # Document ID for source references
    max_depth: int
    max_branches: int
    language: str  # "zh", "en", or "auto"

    # Output accumulation
    markdown_output: str  # Raw markdown from generation
    nodes: Dict[str, Dict[str, Any]]  # node_id -> node_data
    edges: List[Dict[str, Any]]  # edge data list
    root_id: Optional[str]

    # Streaming callback (injected)
    emit_event: EventCallback

    # LLM service (injected)
    llm_service: LLMService

    # Error handling
    error: Optional[str]


# =============================================================================
# Prompts - Chinese
# =============================================================================

DIRECT_PROMPT_ZH = """请将以下文本转换为**结构化的知识笔记**。

## 文本内容
{content}

## 核心原则

❌ 不要：平铺直叙，照搬原文结构
✅ 要做：提炼核心，按逻辑重组

## 输出结构

### 第1层：核心要点（5-10个）
- 文本中最重要的核心观点/概念/主题
- 每个要点用简洁的短语概括

### 第2层：展开说明
- 对每个核心要点的具体解释
- 关键定义、方法、步骤

### 第3层：支撑细节
- 具体案例、数据、引用
- 保留原文中的关键信息（人名、地名、数字、时间）

## 来源引用规则
- 输入文本可能包含来源标记如 `[PAGE:X]` 或 `[TIME:MM:SS]`
- 当提取某个观点时，在末尾**必须保留**最相关的来源标记
- 如果某个观点跨越多个来源，保留主要来源的标记
- 示例: "投资的核心是理解未来现金流 [PAGE:15]" 或 "AI Agent 能自主规划任务 [TIME:05:30]"

## 提取原则

1. **保留具体信息**：人名、公司名、地名、数字、日期、引用
2. **体现因果关系**：原因→结果，问题→解决方案
3. **区分主次**：核心观点 vs 补充说明
4. **删除噪音**：致谢、寒暄、重复内容

## 格式要求
- # 根标题（概括主题）
- - 和 2空格缩进表示层级
- 控制在 3-4 层
- 节点名 ≤ 30 字符

直接输出 Markdown，不要解释：
"""

REFINE_PROMPT_ZH = """优化以下 Markdown 大纲，使其更清晰、更有条理。

原始大纲:
```markdown
{content}
```

## 优化规则

### 1. 去重
- 删除父子同名节点（保留子节点内容）
- 删除同级重复节点
- 合并高度相似的内容

### 2. 结构优化
- 控制在 3-4 层深度
- 确保父子节点有逻辑关系
- 相似内容归到同一分类

### 3. 内容清理
- 删除致谢、用户名、寒暄
- 删除过于抽象的分类词（如"主题"、"内容"、"概述"）
- 节点名 ≤ 30 字符

### 4. 保留关键信息
- 人名、地名、公司名
- 数字、日期、具体数据
- 因果关系、对比分析
- **必须保留**来源标注: `[PAGE:X]` 或 `[TIME:MM:SS]`

## 格式
- # 根标题
- - 和 2空格缩进
- 不要解释，直接输出

优化后:
"""

# =============================================================================
# Prompts - English
# =============================================================================

DIRECT_PROMPT_EN = """Convert this text into **structured knowledge notes**.

## Text Content
{content}

## Core Principle

❌ Don't: List everything, follow original structure
✅ Do: Extract core ideas, reorganize logically

## Output Structure

### Layer 1: Core Points (5-10)
- Most important concepts/themes/ideas
- Concise phrase for each

### Layer 2: Elaboration
- Explanation of each core point
- Key definitions, methods, steps

### Layer 3: Supporting Details
- Specific cases, data, quotes
- Preserve key info (names, places, numbers, dates)

## Source Reference Rules
- Input text may contain source markers like `[PAGE:X]` or `[TIME:MM:SS]`
- When extracting points, you **MUST preserve** the most relevant source marker at the end
- If a point spans multiple sources, keep the primary source marker
- Example: "Core of investing is understanding future cash flow [PAGE:15]" or "AI Agent plans tasks autonomously [TIME:05:30]"

## Extraction Principles

1. **Keep specifics**: Names, companies, places, numbers, dates, quotes
2. **Show causality**: Cause → effect, problem → solution
3. **Distinguish importance**: Core ideas vs supporting details
4. **Remove noise**: Acknowledgements, greetings, repetition

## Format
- # for root heading (summarize theme)
- - with 2-space indent for hierarchy
- Keep to 3-4 levels
- Node names ≤ 35 characters

Output Markdown directly, no explanations:
"""

REFINE_PROMPT_EN = """Optimize this Markdown outline for clarity and organization.

Original:
```markdown
{content}
```

## Optimization Rules

### 1. Deduplication
- Remove parent-child with same name (keep child content)
- Remove duplicate siblings
- Merge highly similar content

### 2. Structure
- Keep to 3-4 levels max
- Ensure logical parent-child relationships
- Group similar content together

### 3. Cleanup
- Remove acknowledgements, usernames, greetings
- Remove abstract categories ("Topic", "Content", "Overview")
- Node names ≤ 35 characters

### 4. Preserve Key Info
- Names, places, companies
- Numbers, dates, specific data
- Causality, comparisons
- **Must preserve** source markers: `[PAGE:X]` or `[TIME:MM:SS]`

## Format
- # for root heading
- - with 2-space indents
- No explanations, direct output

Optimized:
"""


# =============================================================================
# Helper Functions
# =============================================================================


def _get_color_for_level(level: int) -> str:
    """Get color for a node based on its depth level."""
    colors = ["primary", "blue", "green", "orange", "purple", "pink"]
    return colors[level % len(colors)]


def _extract_content(text: str) -> str:
    """Extract content from LLM response, removing code blocks."""
    text = text.strip()

    # Remove markdown code blocks if present
    if text.startswith("```markdown"):
        text = text[11:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Ensure it starts with # or -
    if not (text.startswith("#") or text.startswith("-")):
        idx = text.find("#")
        if idx != -1:
            text = text[idx:]

    return text


def _parse_source_marker(text: str) -> tuple[str, List[SourceRef]]:
    """Parse source markers from text and return (clean_text, source_refs).

    Supports:
    - [Page X] or [Page X-Y] for PDFs
    - [MM:SS] or [HH:MM:SS] for videos
    """
    source_refs: List[SourceRef] = []

    # Pattern for page markers: [Page 15] or [Page 15-17]
    page_pattern = r"\[Page\s*(\d+)(?:\s*-\s*(\d+))?\]"
    page_matches = re.findall(page_pattern, text, re.IGNORECASE)
    for match in page_matches:
        page_start = match[0]
        page_end = match[1] if match[1] else page_start
        source_refs.append(
            SourceRef(
                source_id="",  # Will be filled in later
                source_type="document",
                location=f"Page {page_start}"
                if page_start == page_end
                else f"Page {page_start}-{page_end}",
                quote="",
            )
        )

    # Pattern for time markers: [12:30] or [1:23:45]
    time_pattern = r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]"
    time_matches = re.findall(time_pattern, text)
    for timestamp in time_matches:
        source_refs.append(
            SourceRef(
                source_id="",  # Will be filled in later
                source_type="video",
                location=timestamp,
                quote="",
            )
        )

    # Remove markers from text
    clean_text = re.sub(page_pattern, "", text, flags=re.IGNORECASE)
    clean_text = re.sub(time_pattern, "", clean_text)
    clean_text = clean_text.strip()

    return clean_text, source_refs


def _parse_markdown_to_nodes(
    markdown: str,
    document_id: Optional[str] = None,
) -> tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """Parse markdown outline to MindmapNode and MindmapEdge structures.

    Returns:
        Tuple of (nodes_dict, edges_list, root_id)
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    root_id: Optional[str] = None

    lines = markdown.strip().split("\n")
    if not lines:
        return nodes, edges, root_id

    # Stack to track parent nodes at each indent level
    # Each entry: (node_id, indent_level)
    parent_stack: List[tuple[str, int]] = []

    for line in lines:
        if not line.strip():
            continue

        # Check if it's a heading (root)
        if line.startswith("#"):
            # Extract heading text
            heading_match = re.match(r"^#+\s*(.+)$", line)
            if heading_match:
                label = heading_match.group(1).strip()
                clean_label, source_refs = _parse_source_marker(label)

                # Fill in document_id for source refs
                for ref in source_refs:
                    ref.source_id = document_id or ""

                node_id = f"node-{uuid4().hex[:8]}"
                node = MindmapNode(
                    id=node_id,
                    label=clean_label[:50],  # Limit label length
                    content=clean_label,
                    depth=0,
                    parent_id=None,
                    x=0,
                    y=0,
                    width=NODE_WIDTH,
                    height=NODE_HEIGHT,
                    color="primary",
                    status="complete",
                    source_refs=source_refs,
                )
                nodes[node_id] = node.to_dict()
                root_id = node_id
                parent_stack = [(node_id, -1)]  # Root is at indent -1
            continue

        # Check if it's a bullet point
        bullet_match = re.match(r"^(\s*)-\s*(.+)$", line)
        if bullet_match:
            indent = len(bullet_match.group(1))
            label = bullet_match.group(2).strip()
            clean_label, source_refs = _parse_source_marker(label)

            # Fill in document_id for source refs
            for ref in source_refs:
                ref.source_id = document_id or ""

            # Calculate depth based on indent (2 spaces per level)
            depth = (indent // 2) + 1

            # Find parent by popping stack until we find smaller indent
            while parent_stack and parent_stack[-1][1] >= indent:
                parent_stack.pop()

            parent_id = parent_stack[-1][0] if parent_stack else root_id

            node_id = f"node-{uuid4().hex[:8]}"
            node = MindmapNode(
                id=node_id,
                label=clean_label[:50],  # Limit label length
                content=clean_label,
                depth=depth,
                parent_id=parent_id,
                x=0,
                y=0,
                width=NODE_WIDTH,
                height=NODE_HEIGHT,
                color=_get_color_for_level(depth),
                status="complete",
                source_refs=source_refs,
            )
            nodes[node_id] = node.to_dict()

            # Create edge
            if parent_id:
                edge_id = f"edge-{parent_id}-{node_id}"
                edge = MindmapEdge(id=edge_id, source=parent_id, target=node_id)
                edges.append(edge.to_dict())

            # Push to stack
            parent_stack.append((node_id, indent))

    return nodes, edges, root_id


# =============================================================================
# Graph Nodes
# =============================================================================


async def direct_generate(state: MindmapState) -> MindmapState:
    """Phase 1: Direct generation - single LLM call to generate entire mindmap.

    Skips chunking/parsing/aggregation and directly generates mindmap
    using the full document context.
    """
    logger.info(f"[MindmapGraph] direct_generate: title={state['document_title']}")

    emit = state.get("emit_event", _noop_emit)
    llm = state["llm_service"]
    language = state.get("language", "zh")

    # Emit started event
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_STARTED,
            message=f"Generating mindmap for: {state['document_title']}",
        )
    )

    # Emit progress
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_PROGRESS,
            progress=0.2,
            message="Phase 1: Generating mindmap structure...",
        )
    )

    content = state["document_content"]

    # Debug: Check if content contains source markers
    has_time_markers = "[TIME:" in content
    has_page_markers = "[PAGE:" in content or "[Page" in content
    logger.info(
        f"[MindmapGraph] Content analysis: length={len(content)}, "
        f"has_TIME_markers={has_time_markers}, has_PAGE_markers={has_page_markers}"
    )
    if has_time_markers:
        # Log first occurrence of time marker
        import re

        time_match = re.search(r"\[TIME:\d{1,2}:\d{2}(?::\d{2})?\]", content)
        if time_match:
            logger.info(f"[MindmapGraph] First TIME marker found: {time_match.group()}")

    # Choose prompt based on language
    if language == "en":
        prompt = DIRECT_PROMPT_EN.format(content=content)
    else:
        prompt = DIRECT_PROMPT_ZH.format(content=content)

    messages = [
        ChatMessage(role="user", content=prompt),
    ]

    try:
        response = await llm.chat(messages)
        markdown = _extract_content(response.content)

        if not markdown:
            return {**state, "error": "Failed to generate mindmap", "markdown_output": ""}

        logger.info(f"[MindmapGraph] Generated {len(markdown.split(chr(10)))} lines")

        return {
            **state,
            "markdown_output": markdown,
            "error": None,
        }

    except Exception as e:
        logger.error(f"[MindmapGraph] direct_generate failed: {e}")
        return {**state, "error": f"Generation failed: {str(e)}", "markdown_output": ""}


async def refine_output(state: MindmapState) -> MindmapState:
    """Phase 2: Refinement - clean up duplicates and improve structure."""
    logger.info("[MindmapGraph] refine_output")

    emit = state.get("emit_event", _noop_emit)
    llm = state["llm_service"]
    language = state.get("language", "zh")
    markdown = state.get("markdown_output", "")

    if not markdown:
        return {**state, "error": "No content to refine"}

    # Emit progress
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_PROGRESS,
            progress=0.5,
            message="Phase 2: Refining and deduplicating...",
        )
    )

    # Choose prompt based on language
    if language == "en":
        prompt = REFINE_PROMPT_EN.format(content=markdown)
    else:
        prompt = REFINE_PROMPT_ZH.format(content=markdown)

    messages = [
        ChatMessage(role="user", content=prompt),
    ]

    try:
        response = await llm.chat(messages)
        refined = _extract_content(response.content)

        if not refined:
            logger.warning("[MindmapGraph] Refinement returned empty, using original")
            refined = markdown

        original_lines = len(markdown.split("\n"))
        refined_lines = len(refined.split("\n"))
        logger.info(f"[MindmapGraph] Refined: {original_lines} -> {refined_lines} lines")

        return {
            **state,
            "markdown_output": refined,
        }

    except Exception as e:
        logger.warning(f"[MindmapGraph] Refinement failed: {e}, using original")
        return state


async def complete_generation(state: MindmapState) -> MindmapState:
    """Finalize the mindmap generation and emit markdown for frontend parsing."""
    markdown = state.get("markdown_output", "")
    document_id = state.get("document_id")

    logger.info(
        f"[MindmapGraph] complete_generation: markdown_lines={len(markdown.split(chr(10)))}"
    )

    emit = state.get("emit_event", _noop_emit)

    # Emit final progress
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_PROGRESS,
            progress=1.0,
            message="Mindmap generation complete",
        )
    )

    # Emit completion with markdown content for frontend parsing
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_COMPLETE,
            message="Mindmap generation complete",
            markdown_content=markdown,
            document_id=document_id,
        )
    )

    return state


# =============================================================================
# Conditional Edges
# =============================================================================


def should_continue(state: MindmapState) -> str:
    """Decide whether to continue or handle error."""
    if state.get("error"):
        return "error"
    return "continue"


# =============================================================================
# Graph Construction
# =============================================================================


def create_mindmap_graph() -> StateGraph:
    """Create and compile the mindmap generation graph.

    Simple 2-step workflow (frontend parses markdown):
    START → generate → refine → complete → END
    """
    workflow = StateGraph(MindmapState)

    # Add nodes
    workflow.add_node("generate", direct_generate)
    workflow.add_node("refine", refine_output)
    workflow.add_node("complete", complete_generation)

    # Wire edges
    workflow.add_edge(START, "generate")
    workflow.add_conditional_edges(
        "generate",
        should_continue,
        {"continue": "refine", "error": "complete"},
    )
    workflow.add_conditional_edges(
        "refine",
        should_continue,
        {"continue": "complete", "error": "complete"},
    )
    workflow.add_edge("complete", END)

    return workflow.compile()


# Compiled graph singleton
mindmap_graph = create_mindmap_graph()
