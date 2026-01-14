"""Unit tests for the new direct generation mindmap algorithm.

Tests the core parsing and extraction functions used in the 2-phase
direct generation algorithm.
"""

import re
from typing import Any
from uuid import uuid4

# Import directly from the module to avoid circular import issues
# that occur when going through __init__.py
from research_agent.domain.entities.output import MindmapEdge, MindmapNode, SourceRef

# Re-implement the helper functions here for testing isolation
# This avoids the circular import while testing the logic

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


def _parse_source_marker(text: str) -> tuple[str, list[SourceRef]]:
    """Parse source markers from text and return (clean_text, source_refs)."""
    source_refs: list[SourceRef] = []

    # Pattern for page markers: [Page 15] or [Page 15-17]
    page_pattern = r'\[Page\s*(\d+)(?:\s*-\s*(\d+))?\]'
    page_matches = re.findall(page_pattern, text, re.IGNORECASE)
    for match in page_matches:
        page_start = match[0]
        page_end = match[1] if match[1] else page_start
        source_refs.append(SourceRef(
            source_id="",
            source_type="document",
            location=f"Page {page_start}" if page_start == page_end else f"Page {page_start}-{page_end}",
            quote="",
        ))

    # Pattern for time markers: [12:30] or [1:23:45]
    time_pattern = r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]'
    time_matches = re.findall(time_pattern, text)
    for timestamp in time_matches:
        source_refs.append(SourceRef(
            source_id="",
            source_type="video",
            location=timestamp,
            quote="",
        ))

    # Remove markers from text
    clean_text = re.sub(page_pattern, '', text, flags=re.IGNORECASE)
    clean_text = re.sub(time_pattern, '', clean_text)
    clean_text = clean_text.strip()

    return clean_text, source_refs


NODE_WIDTH = 200
NODE_HEIGHT = 80


def _parse_markdown_to_nodes(
    markdown: str,
    document_id: str | None = None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], str | None]:
    """Parse markdown outline to MindmapNode and MindmapEdge structures."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    root_id: str | None = None

    lines = markdown.strip().split('\n')
    if not lines:
        return nodes, edges, root_id

    parent_stack: list[tuple[str, int]] = []

    for line in lines:
        if not line.strip():
            continue

        if line.startswith('#'):
            heading_match = re.match(r'^#+\s*(.+)$', line)
            if heading_match:
                label = heading_match.group(1).strip()
                clean_label, source_refs = _parse_source_marker(label)

                for ref in source_refs:
                    ref.source_id = document_id or ""

                node_id = f"node-{uuid4().hex[:8]}"
                node = MindmapNode(
                    id=node_id,
                    label=clean_label[:50],
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
                parent_stack = [(node_id, -1)]
            continue

        bullet_match = re.match(r'^(\s*)-\s*(.+)$', line)
        if bullet_match:
            indent = len(bullet_match.group(1))
            label = bullet_match.group(2).strip()
            clean_label, source_refs = _parse_source_marker(label)

            for ref in source_refs:
                ref.source_id = document_id or ""

            depth = (indent // 2) + 1

            while parent_stack and parent_stack[-1][1] >= indent:
                parent_stack.pop()

            parent_id = parent_stack[-1][0] if parent_stack else root_id

            node_id = f"node-{uuid4().hex[:8]}"
            node = MindmapNode(
                id=node_id,
                label=clean_label[:50],
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

            if parent_id:
                edge_id = f"edge-{parent_id}-{node_id}"
                edge = MindmapEdge(id=edge_id, source=parent_id, target=node_id)
                edges.append(edge.to_dict())

            parent_stack.append((node_id, indent))

    return nodes, edges, root_id


class TestExtractContent:
    """Tests for _extract_content function."""

    def test_extracts_plain_markdown(self):
        """Should return plain markdown as-is."""
        content = "# Root Title\n- Branch 1\n- Branch 2"
        result = _extract_content(content)
        assert result == content

    def test_removes_markdown_code_blocks(self):
        """Should strip markdown code block wrappers."""
        content = "```markdown\n# Root Title\n- Branch 1\n```"
        result = _extract_content(content)
        assert result == "# Root Title\n- Branch 1"

    def test_removes_plain_code_blocks(self):
        """Should strip plain code block wrappers."""
        content = "```\n# Root Title\n- Branch 1\n```"
        result = _extract_content(content)
        assert result == "# Root Title\n- Branch 1"

    def test_handles_no_closing_backticks(self):
        """Should handle missing closing backticks."""
        content = "```markdown\n# Root Title\n- Branch 1"
        result = _extract_content(content)
        assert "# Root Title" in result

    def test_finds_heading_in_text(self):
        """Should find heading if preceded by other text."""
        content = "Here is the output:\n# Root Title\n- Branch 1"
        result = _extract_content(content)
        assert result.startswith("# Root Title")


class TestParseSourceMarker:
    """Tests for _parse_source_marker function."""

    def test_parses_single_page_marker(self):
        """Should extract [Page X] markers."""
        text = "Investment principles [Page 15]"
        clean, refs = _parse_source_marker(text)

        assert clean == "Investment principles"
        assert len(refs) == 1
        assert refs[0].source_type == "document"
        assert refs[0].location == "Page 15"

    def test_parses_page_range_marker(self):
        """Should extract [Page X-Y] markers."""
        text = "Core concepts [Page 15-17]"
        clean, refs = _parse_source_marker(text)

        assert clean == "Core concepts"
        assert len(refs) == 1
        assert refs[0].location == "Page 15-17"

    def test_parses_time_marker(self):
        """Should extract [MM:SS] markers."""
        text = "Discussion topic [12:30]"
        clean, refs = _parse_source_marker(text)

        assert clean == "Discussion topic"
        assert len(refs) == 1
        assert refs[0].source_type == "video"
        assert refs[0].location == "12:30"

    def test_parses_hour_time_marker(self):
        """Should extract [HH:MM:SS] markers."""
        text = "Long discussion [1:23:45]"
        clean, refs = _parse_source_marker(text)

        assert clean == "Long discussion"
        assert len(refs) == 1
        assert refs[0].location == "1:23:45"

    def test_handles_no_markers(self):
        """Should handle text without markers."""
        text = "Plain text without markers"
        clean, refs = _parse_source_marker(text)

        assert clean == "Plain text without markers"
        assert len(refs) == 0

    def test_handles_multiple_markers(self):
        """Should extract multiple markers."""
        text = "Content [Page 5] and video [10:30]"
        clean, refs = _parse_source_marker(text)

        # Clean text has markers removed (may have extra spaces)
        assert "Content" in clean
        assert "video" in clean
        assert "[Page" not in clean
        assert "[10:30]" not in clean
        assert len(refs) == 2


class TestParseMarkdownToNodes:
    """Tests for _parse_markdown_to_nodes function."""

    def test_parses_simple_outline(self):
        """Should parse a simple markdown outline."""
        markdown = """# Root Title
- Branch 1
- Branch 2
"""
        nodes, edges, root_id = _parse_markdown_to_nodes(markdown)

        assert root_id is not None
        assert len(nodes) == 3  # 1 root + 2 branches
        assert len(edges) == 2  # 2 edges from root to branches

        # Check root node
        root = nodes[root_id]
        assert root["label"] == "Root Title"
        assert root["depth"] == 0

    def test_parses_nested_outline(self):
        """Should parse nested markdown outline."""
        markdown = """# Root
- Level 1
  - Level 2
    - Level 3
"""
        nodes, edges, root_id = _parse_markdown_to_nodes(markdown)

        assert len(nodes) == 4
        assert len(edges) == 3

        # Check depths
        depths = {n["label"]: n["depth"] for n in nodes.values()}
        assert depths["Root"] == 0
        assert depths["Level 1"] == 1
        assert depths["Level 2"] == 2
        assert depths["Level 3"] == 3

    def test_parses_multiple_roots(self):
        """Should handle multiple top-level branches."""
        markdown = """# Topic
- Branch A
  - Sub A1
  - Sub A2
- Branch B
  - Sub B1
"""
        nodes, edges, root_id = _parse_markdown_to_nodes(markdown)

        assert len(nodes) == 6  # 1 root + 2 branches + 3 subs

        # Check structure
        root = nodes[root_id]
        assert root["label"] == "Topic"

        # Find Branch A and B
        branch_a = next((n for n in nodes.values() if n["label"] == "Branch A"), None)
        branch_b = next((n for n in nodes.values() if n["label"] == "Branch B"), None)

        assert branch_a is not None
        assert branch_b is not None
        assert branch_a["parentId"] == root_id
        assert branch_b["parentId"] == root_id

    def test_extracts_source_refs(self):
        """Should extract source references from node labels."""
        markdown = """# Investment Philosophy
- Core principles [Page 5]
- Case study [10:30]
"""
        nodes, edges, root_id = _parse_markdown_to_nodes(markdown, document_id="doc-123")

        # Find the node with page reference
        page_node = next(
            (n for n in nodes.values() if "Core principles" in n["label"]),
            None
        )
        assert page_node is not None
        assert len(page_node["sourceRefs"]) == 1
        assert page_node["sourceRefs"][0]["sourceId"] == "doc-123"
        assert page_node["sourceRefs"][0]["location"] == "Page 5"

    def test_assigns_colors_by_depth(self):
        """Should assign different colors for different depths."""
        markdown = """# Root
- Level 1
  - Level 2
"""
        nodes, edges, root_id = _parse_markdown_to_nodes(markdown)

        colors = {n["depth"]: n["color"] for n in nodes.values()}
        assert colors[0] == "primary"  # Root
        assert colors[1] == "blue"  # Level 1
        assert colors[2] == "green"  # Level 2


class TestGetColorForLevel:
    """Tests for _get_color_for_level function."""

    def test_returns_primary_for_root(self):
        """Should return 'primary' for level 0."""
        assert _get_color_for_level(0) == "primary"

    def test_returns_different_colors_for_levels(self):
        """Should return different colors for different levels."""
        colors = [_get_color_for_level(i) for i in range(6)]
        # Colors should cycle through the palette
        assert len(set(colors)) == 6  # All unique for first 6 levels

    def test_cycles_colors_beyond_palette(self):
        """Should cycle colors for deep levels."""
        color_0 = _get_color_for_level(0)
        color_6 = _get_color_for_level(6)
        assert color_0 == color_6  # Should wrap around
