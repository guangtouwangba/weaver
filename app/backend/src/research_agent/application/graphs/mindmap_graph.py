"""LangGraph workflow for mindmap generation."""

import json
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

# Performance limits - prevent exponential explosion
MAX_TOTAL_NODES = 50  # Hard cap to prevent frontend freezing
DEFAULT_MAX_DEPTH = 2
DEFAULT_MAX_BRANCHES = 4

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

    # Processing state
    current_depth: int
    nodes_to_expand: List[str]  # Node IDs pending expansion at current level

    # Output accumulation
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
# Prompts
# =============================================================================

SYSTEM_PROMPT = """You are an expert at analyzing documents and creating structured mindmaps.
Your task is to extract the key concepts and their hierarchical relationships from the given content.

IMPORTANT: You must respond with ONLY valid JSON, no other text or explanation."""

ROOT_PROMPT = """Analyze the following document and identify the main topic/theme that should be the root of a mindmap.

Document Title: {title}

Document Content:
{content}

Respond with a JSON object containing:
{{
  "label": "Main topic label (brief, 3-5 words max)",
  "content": "A one-sentence summary of the main topic",
  "source_quote": "The EXACT quote from the document that best represents this main topic (copy verbatim, max 200 chars)",
  "source_location": "Page number or section if identifiable (e.g., 'Page 1', 'Introduction'), or null if not identifiable"
}}

Remember: Respond with ONLY the JSON object, nothing else."""

BRANCHES_PROMPT = """Based on the document content and the current mindmap structure, generate the next level of branches.

Document Content:
{content}

Current Node: {current_node_label}
Current Node Content: {current_node_content}
Depth Level: {depth} (0=root, higher=more specific)

Generate {max_branches} key sub-topics or aspects that branch from "{current_node_label}".
Each branch should be distinct and cover different aspects.

IMPORTANT: For each branch, include the EXACT quote from the source document that supports this sub-topic.

Respond with a JSON object containing:
{{
  "branches": [
    {{
      "label": "Branch label (brief, 3-5 words max)",
      "content": "A brief explanation of this sub-topic",
      "source_quote": "The EXACT quote from the document supporting this branch (copy verbatim, max 200 chars)",
      "source_location": "Page number or section if identifiable (e.g., 'Page 3'), or null"
    }}
  ]
}}

Remember: Respond with ONLY the JSON object, nothing else."""


# =============================================================================
# Helper Functions
# =============================================================================


def _parse_json_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    content = response.strip()

    # Remove markdown code blocks if present
    if content.startswith("```"):
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1 :]
        if content.endswith("```"):
            content = content[:-3].strip()
        elif "```" in content:
            content = content[: content.rfind("```")].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(f"[MindmapGraph] JSON parse error: {e}, content: {content[:200]}")
        return None


def _get_color_for_level(level: int) -> str:
    """Get color for a node based on its depth level."""
    colors = ["primary", "blue", "green", "orange", "purple", "pink"]
    return colors[level % len(colors)]


def _truncate_content(content: str, max_chars: int = 50000) -> str:
    """Truncate content to fit within token limits."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[... content truncated ...]"


# =============================================================================
# Graph Nodes
# =============================================================================


async def analyze_document(state: MindmapState) -> MindmapState:
    """Analyze document and prepare for mindmap generation.

    This node validates input and emits the GENERATION_STARTED event.
    """
    logger.info(f"[MindmapGraph] analyze_document: title={state['document_title']}")

    emit = state.get("emit_event", _noop_emit)

    # Emit started event
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_STARTED,
            message=f"Generating mindmap for: {state['document_title']}",
        )
    )

    # Emit initial progress
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_PROGRESS,
            progress=0.1,
            current_level=0,
            total_levels=state["max_depth"] + 1,
            message="Analyzing document...",
        )
    )

    return {
        **state,
        "current_depth": 0,
        "nodes_to_expand": [],
        "nodes": {},
        "edges": [],
        "root_id": None,
        "error": None,
    }


async def generate_root(state: MindmapState) -> MindmapState:
    """Generate the root node of the mindmap."""
    logger.info("[MindmapGraph] generate_root")

    emit = state.get("emit_event", _noop_emit)
    llm = state["llm_service"]

    # Truncate content
    content = _truncate_content(state["document_content"], 8000)

    prompt = ROOT_PROMPT.format(title=state["document_title"], content=content)

    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=prompt),
    ]

    try:
        response = await llm.chat(messages)
        data = _parse_json_response(response.content)

        if not data or "label" not in data:
            return {**state, "error": "Failed to parse root node response"}

        node_id = f"node-{uuid4().hex[:8]}"
        
        # Build source references from LLM response
        source_refs: List[SourceRef] = []
        document_id = state.get("document_id")
        source_quote = data.get("source_quote", "")
        source_location = data.get("source_location")
        
        if source_quote and document_id:
            source_refs.append(SourceRef(
                source_id=document_id,
                source_type="document",
                location=source_location,
                quote=source_quote[:300],  # Limit quote length
            ))
        
        node = MindmapNode(
            id=node_id,
            label=data["label"],
            content=data.get("content", ""),
            depth=0,
            parent_id=None,
            x=0,  # Frontend will apply layout
            y=0,  # Frontend will apply layout
            width=NODE_WIDTH,
            height=NODE_HEIGHT,
            color="primary",
            status="complete",
            source_refs=source_refs,
        )

        # Emit node added event
        await emit(
            OutputEvent(
                type=OutputEventType.NODE_ADDED,
                node_id=node_id,
                node_data=node.to_dict(),
            )
        )

        return {
            **state,
            "root_id": node_id,
            "nodes": {node_id: node.to_dict()},
            "nodes_to_expand": [node_id],
            "current_depth": 1,
        }

    except Exception as e:
        logger.error(f"[MindmapGraph] generate_root failed: {e}")
        return {**state, "error": f"Failed to generate root: {str(e)}"}


async def expand_level(state: MindmapState) -> MindmapState:
    """Expand all nodes at the current level by generating their children."""
    current_depth = state["current_depth"]
    max_depth = state["max_depth"]
    nodes_to_expand = state["nodes_to_expand"]

    logger.info(
        f"[MindmapGraph] expand_level: depth={current_depth}, nodes_to_expand={len(nodes_to_expand)}"
    )

    emit = state.get("emit_event", _noop_emit)
    llm = state["llm_service"]

    # Check if we're approaching the node limit
    current_node_count = len(state["nodes"])
    if current_node_count >= MAX_TOTAL_NODES:
        logger.warning(
            f"[MindmapGraph] Node limit reached ({current_node_count}/{MAX_TOTAL_NODES}), stopping expansion"
        )
        return {
            **state,
            "nodes_to_expand": [],  # Clear to trigger completion
        }

    # Emit progress
    progress = 0.1 + (0.8 * current_depth / max_depth)
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_PROGRESS,
            progress=progress,
            current_level=current_depth,
            total_levels=max_depth + 1,
            message=f"Generating level {current_depth} branches...",
        )
    )

    # Truncate content
    content = _truncate_content(state["document_content"], 6000)

    # Collect new nodes and edges
    nodes = dict(state["nodes"])
    edges = list(state["edges"])
    next_level_nodes: List[str] = []

    # Calculate how many more nodes we can add
    remaining_capacity = MAX_TOTAL_NODES - current_node_count

    for parent_id in nodes_to_expand:
        parent_data = nodes.get(parent_id)
        if not parent_data:
            continue

        prompt = BRANCHES_PROMPT.format(
            content=content,
            current_node_label=parent_data.get("label", ""),
            current_node_content=parent_data.get("content", ""),
            depth=current_depth,
            max_branches=state["max_branches"],
        )

        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt),
        ]

        try:
            response = await llm.chat(messages)
            data = _parse_json_response(response.content)

            if not data or "branches" not in data:
                logger.warning(f"[MindmapGraph] Invalid branches response for {parent_id}")
                continue

            # Limit branches to remaining capacity
            max_branches_to_add = min(state["max_branches"], remaining_capacity)
            branches = data["branches"][:max_branches_to_add]

            if not branches:
                logger.info(f"[MindmapGraph] No capacity for more branches, skipping {parent_id}")
                continue

            for i, branch in enumerate(branches):
                # Double-check capacity (in case of concurrent modifications)
                if len(nodes) >= MAX_TOTAL_NODES:
                    logger.warning(f"[MindmapGraph] Node limit reached during expansion")
                    break

                node_id = f"node-{uuid4().hex[:8]}"

                # Emit node generating event
                await emit(
                    OutputEvent(
                        type=OutputEventType.NODE_GENERATING,
                        node_id=node_id,
                        node_data={"label": branch.get("label", "")},
                    )
                )

                # Build source references from LLM response
                source_refs: List[SourceRef] = []
                document_id = state.get("document_id")
                source_quote = branch.get("source_quote", "")
                source_location = branch.get("source_location")
                
                if source_quote and document_id:
                    source_refs.append(SourceRef(
                        source_id=document_id,
                        source_type="document",
                        location=source_location,
                        quote=source_quote[:300],  # Limit quote length
                    ))

                node = MindmapNode(
                    id=node_id,
                    label=branch.get("label", f"Branch {i + 1}"),
                    content=branch.get("content", ""),
                    depth=current_depth,
                    parent_id=parent_id,
                    x=0,  # Frontend will apply layout
                    y=0,  # Frontend will apply layout
                    width=NODE_WIDTH,
                    height=NODE_HEIGHT,
                    color=_get_color_for_level(current_depth),
                    status="complete",
                    source_refs=source_refs,
                )

                nodes[node_id] = node.to_dict()
                next_level_nodes.append(node_id)

                # Emit node added event
                await emit(
                    OutputEvent(
                        type=OutputEventType.NODE_ADDED,
                        node_id=node_id,
                        node_data=node.to_dict(),
                    )
                )

                # Create edge
                edge_id = f"edge-{parent_id}-{node_id}"
                edge = MindmapEdge(id=edge_id, source=parent_id, target=node_id)
                edges.append(edge.to_dict())

                # Emit edge added event
                await emit(
                    OutputEvent(
                        type=OutputEventType.EDGE_ADDED,
                        edge_id=edge_id,
                        edge_data=edge.to_dict(),
                    )
                )

        except Exception as e:
            logger.error(f"[MindmapGraph] expand_level failed for {parent_id}: {e}")
            # Continue with other nodes

    # Emit level complete
    await emit(
        OutputEvent(
            type=OutputEventType.LEVEL_COMPLETE,
            current_level=current_depth,
            total_levels=max_depth + 1,
        )
    )

    return {
        **state,
        "nodes": nodes,
        "edges": edges,
        "nodes_to_expand": next_level_nodes,
        "current_depth": current_depth + 1,
    }


async def complete_generation(state: MindmapState) -> MindmapState:
    """Finalize the mindmap generation."""
    logger.info(
        f"[MindmapGraph] complete_generation: nodes={len(state['nodes'])}, edges={len(state['edges'])}"
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

    # Emit completion
    await emit(
        OutputEvent(
            type=OutputEventType.GENERATION_COMPLETE,
            message=f"Generated mindmap with {len(state['nodes'])} nodes",
        )
    )

    return state


# =============================================================================
# Conditional Edges
# =============================================================================


def should_continue_expanding(state: MindmapState) -> str:
    """Decide whether to continue expanding or finish."""
    if state.get("error"):
        return "error"

    current_depth = state["current_depth"]
    max_depth = state["max_depth"]
    nodes_to_expand = state["nodes_to_expand"]

    if current_depth <= max_depth and nodes_to_expand:
        return "expand"
    else:
        return "complete"


# =============================================================================
# Graph Construction
# =============================================================================


def create_mindmap_graph() -> StateGraph:
    """Create and compile the mindmap generation graph."""
    workflow = StateGraph(MindmapState)

    # Add nodes
    workflow.add_node("analyze", analyze_document)
    workflow.add_node("generate_root", generate_root)
    workflow.add_node("expand_level", expand_level)
    workflow.add_node("complete", complete_generation)

    # Wire edges
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "generate_root")
    workflow.add_edge("generate_root", "expand_level")

    # Conditional edge for level expansion
    workflow.add_conditional_edges(
        "expand_level",
        should_continue_expanding,
        {
            "expand": "expand_level",
            "complete": "complete",
            "error": "complete",  # Still run complete to emit error event
        },
    )

    workflow.add_edge("complete", END)

    return workflow.compile()


# Compiled graph singleton
mindmap_graph = create_mindmap_graph()

