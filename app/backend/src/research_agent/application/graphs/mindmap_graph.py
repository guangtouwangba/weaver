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

from research_agent.domain.entities.output import (
    MindmapEdge,
    MindmapNode,
    OutputEvent,
    OutputEventType,
    SourceRef,
)
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.infrastructure.llm.prompts import PromptLoader
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
    language: str  # "zh", "en", or "auto"
    skills: List[Any]  # Available skills for the agent

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

# Template paths
DIRECT_GENERATION_TEMPLATE = "agents/mindmap/direct_generation.j2"
REFINE_TEMPLATE = "agents/mindmap/refine.j2"


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


def _count_source_markers(text: str) -> dict[str, int]:
    """Count source markers in text.

    Returns a dict with counts for each marker type:
    - 'time': count of [TIME:MM:SS] markers
    - 'page': count of [PAGE:X] markers
    - 'total': total count
    """
    # Pattern for time markers: [TIME:12:30], [TIME:1:23:45]
    time_pattern = r"\[TIME:\d{1,2}:\d{2}(?::\d{2})?\]"
    time_count = len(re.findall(time_pattern, text, re.IGNORECASE))

    # Pattern for page markers: [PAGE:15], [PAGE:15-17]
    page_pattern = r"\[PAGE:\d+(?:\s*-\s*\d+)?\]"
    page_count = len(re.findall(page_pattern, text, re.IGNORECASE))

    return {"time": time_count, "page": page_count, "total": time_count + page_count}


def _validate_marker_preservation(original: str, refined: str) -> tuple[bool, str]:
    """Validate that source markers are preserved after refinement.

    Returns (is_valid, message).
    - is_valid: True if markers are preserved (or original had none)
    - message: Description of the validation result
    """
    original_counts = _count_source_markers(original)
    refined_counts = _count_source_markers(refined)

    # If original had no markers, nothing to validate
    if original_counts["total"] == 0:
        return True, "No source markers in original content"

    # Check if refined has significantly fewer markers (allow some reduction due to deduplication)
    # We use 50% threshold - if more than half are lost, consider it a failure
    preservation_ratio = (
        refined_counts["total"] / original_counts["total"] if original_counts["total"] > 0 else 1.0
    )

    if preservation_ratio < 0.5:
        return False, (
            f"Source markers lost during refinement: "
            f"original had {original_counts['total']} markers "
            f"(TIME:{original_counts['time']}, PAGE:{original_counts['page']}), "
            f"refined has {refined_counts['total']} markers "
            f"(TIME:{refined_counts['time']}, PAGE:{refined_counts['page']}), "
            f"preservation ratio: {preservation_ratio:.1%}"
        )

    return True, (
        f"Source markers preserved: "
        f"original {original_counts['total']} -> refined {refined_counts['total']} "
        f"(preservation ratio: {preservation_ratio:.1%})"
    )


def _parse_source_marker(text: str) -> tuple[str, List[SourceRef]]:
    """Parse source markers from text and return (clean_text, source_refs).

    Supports multiple formats for compatibility:
    - [PAGE:X] or [PAGE:X-Y] (source annotator format)
    - [Page X] or [Page X-Y] (LLM may output this format)
    - [TIME:MM:SS] or [TIME:HH:MM:SS] (source annotator format)
    - [MM:SS] or [HH:MM:SS] (LLM may output this format)
    """
    source_refs: List[SourceRef] = []

    # Pattern for page markers: [PAGE:15], [PAGE:15-17], [Page 15], [Page 15-17]
    # Supports both [PAGE:X] and [Page X] formats
    page_pattern = r"\[(?:PAGE:|Page\s*)(\d+)(?:\s*-\s*(\d+))?\]"
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

    # Pattern for time markers: [TIME:12:30], [TIME:1:23:45], [12:30], [1:23:45]
    # Supports both [TIME:MM:SS] and [MM:SS] formats
    time_pattern = r"\[(?:TIME:)?(\d{1,2}:\d{2}(?::\d{2})?)\]"
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

    # Remove markers from text (both formats)
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
    logger.info(f"[_parse_markdown_to_nodes] Parsing {len(lines)} lines of markdown")
    if not lines:
        return nodes, edges, root_id

    # Stack to track parent nodes at each depth level
    # Each entry: (node_id, depth)
    parent_stack: List[tuple[str, int]] = []

    # Track the depth of the most recent header to anchor bullet points
    # Start at -1 so top level bullets (if valid) start at 0
    last_header_depth = -1

    for line in lines:
        if not line.strip():
            continue

        current_depth = 0
        clean_label = ""
        source_refs = []
        is_valid_node = False

        # Check if it's a heading
        heading_match = re.match(r"^(#+)\s*(.+)$", line)
        if heading_match:
            is_valid_node = True
            level = len(heading_match.group(1))
            # Map level 1 (#) to depth 0, level 2 (##) to depth 1, etc.
            current_depth = level - 1
            last_header_depth = current_depth

            label = heading_match.group(2).strip()
            clean_label, source_refs = _parse_source_marker(label)

        # Check if it's a bullet point
        else:
            bullet_match = re.match(r"^(\s*)-\s*(.+)$", line)
            if bullet_match:
                is_valid_node = True
                indent = len(bullet_match.group(1))
                # Bullets start 1 level deeper than the last header
                # Indent 0 = last_header_depth + 1
                current_depth = last_header_depth + 1 + (indent // 2)

                label = bullet_match.group(2).strip()
                clean_label, source_refs = _parse_source_marker(label)

        if not is_valid_node:
            continue

        # Common node creation logic

        # Fill in document_id for source refs
        for ref in source_refs:
            ref.source_id = document_id or ""

        # Find parent
        # Pop stack until we find a node with depth < current_depth
        while parent_stack and parent_stack[-1][1] >= current_depth:
            parent_stack.pop()

        parent_id = parent_stack[-1][0] if parent_stack else None

        node_id = f"node-{uuid4().hex[:8]}"

        # Set root_id if this is the first root encountered
        if parent_id is None and root_id is None:
            root_id = node_id

        node = MindmapNode(
            id=node_id,
            label=clean_label[:50],  # Limit label length
            content=clean_label,
            depth=current_depth,
            parent_id=parent_id,
            x=0,
            y=0,
            width=NODE_WIDTH,
            height=NODE_HEIGHT,
            color=_get_color_for_level(current_depth),
            status="complete",
            source_refs=source_refs,
        )
        nodes[node_id] = node.to_dict()

        if parent_id:
            edge_id = f"edge-{parent_id}-{node_id}"
            edge = MindmapEdge(id=edge_id, source=parent_id, target=node_id)
            edges.append(edge.to_dict())

        parent_stack.append((node_id, current_depth))
        logger.debug(f"[_parse_markdown_to_nodes] Created node {node_id} at depth {current_depth}")

    logger.info(f"[_parse_markdown_to_nodes] Parsed {len(nodes)} nodes and {len(edges)} edges")
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
    skills = state.get("skills", [])
    prompt_loader = PromptLoader.get_instance()

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
    # Render prompt using Jinja2
    prompt = prompt_loader.render(
        DIRECT_GENERATION_TEMPLATE,
        content=content,
        language=language,
        skills=skills,
    )

    messages = [
        ChatMessage(role="user", content=prompt),
    ]

    try:
        response = await llm.chat(messages)
        markdown = _extract_content(response.content)

        if not markdown:
            return {**state, "error": "Failed to generate mindmap", "markdown_output": ""}

        # Validate source marker preservation in direct generation
        input_marker_counts = _count_source_markers(content)
        output_marker_counts = _count_source_markers(markdown)
        logger.info(
            f"[MindmapGraph] Direct generation marker check: "
            f"input had {input_marker_counts['total']} markers "
            f"(TIME:{input_marker_counts['time']}, PAGE:{input_marker_counts['page']}), "
            f"output has {output_marker_counts['total']} markers "
            f"(TIME:{output_marker_counts['time']}, PAGE:{output_marker_counts['page']})"
        )

        if input_marker_counts["total"] > 0 and output_marker_counts["total"] == 0:
            logger.warning(
                f"[MindmapGraph] WARNING: All source markers lost during direct generation! "
                f"Input had {input_marker_counts['total']} markers but output has none."
            )
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
    skills = state.get("skills", [])
    markdown = state.get("markdown_output", "")
    prompt_loader = PromptLoader.get_instance()

    if not markdown:
        return {**state, "error": "No content to refine"}

    # Count original markers for validation
    original_marker_counts = _count_source_markers(markdown)
    logger.info(
        f"[MindmapGraph] Original content has {original_marker_counts['total']} source markers "
        f"(TIME:{original_marker_counts['time']}, PAGE:{original_marker_counts['page']})"
    )

    # Log original markdown before refine
    logger.info(f"[MindmapGraph] Original Markdown (before refine):\n{markdown}")

    # Emit progress
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_PROGRESS,
            progress=0.5,
            message="Phase 2: Refining and deduplicating...",
        )
    )

    # Choose prompt based on language
    # Render prompt using Jinja2
    prompt = prompt_loader.render(
        REFINE_TEMPLATE,
        content=markdown,
        language=language,
        skills=skills,
    )

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

        # Validate source marker preservation
        is_valid, validation_msg = _validate_marker_preservation(markdown, refined)
        logger.info(f"[MindmapGraph] Marker validation: {validation_msg}")

        if not is_valid:
            logger.warning(
                f"[MindmapGraph] Source markers lost during refinement! "
                f"Falling back to original content to preserve navigation functionality."
            )
            # Use original content to preserve source markers
            refined = markdown

        # Log the refined markdown for debugging
        logger.info(f"[MindmapGraph] Refined Markdown Output:\n{refined}")

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

    # Log the full markdown content for debugging
    logger.info(f"[MindmapGraph] Final Markdown Output:\n{markdown}")

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
