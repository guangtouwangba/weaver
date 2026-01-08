"""DTOs for output generation API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# Request DTOs
# =============================================================================


class GenerateOutputRequest(BaseModel):
    """Request to generate an output."""

    output_type: str = Field(
        ...,
        description="Type of output to generate (mindmap, summary, article, action_list, etc.)",
        pattern="^(mindmap|summary|flashcards|podcast|quiz|timeline|compare|custom|article|action_list)$",
    )
    document_ids: List[UUID] = Field(
        default_factory=list,
        description="List of document IDs to generate output from",
    )
    url_content_ids: List[UUID] = Field(
        default_factory=list,
        description="List of URL content IDs (YouTube, web pages, etc.) to generate output from",
    )
    title: Optional[str] = Field(
        None,
        description="Optional title for the output",
        max_length=255,
    )
    options: Optional[Dict[str, Any]] = Field(
        None,
        description="Output-type specific options (e.g., max_depth for mindmap)",
    )


class ExplainNodeRequest(BaseModel):
    """Request to explain a node."""

    node_data: Dict[str, Any] = Field(
        ...,
        description="Node data including label and content",
    )


class ExpandNodeRequest(BaseModel):
    """Request to expand a node with children."""

    node_data: Dict[str, Any] = Field(
        ...,
        description="Node data including label, content, and position",
    )
    existing_children: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Existing child nodes to avoid duplicates",
    )


class UpdateOutputRequest(BaseModel):
    """Request to update an existing output's data or title."""

    title: Optional[str] = Field(
        None,
        description="New title for the output",
        max_length=255,
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated output data (e.g., mindmap nodes/edges)",
    )


class SynthesizeNodesRequest(BaseModel):
    """Request to synthesize multiple nodes into a consolidated insight."""

    node_ids: List[str] = Field(
        ...,
        description="List of node IDs to synthesize",
        min_length=2,
    )
    mode: str = Field(
        default="connect",
        description="Synthesis mode: connect, inspire, or debate",
        pattern="^(connect|inspire|debate)$",
    )
    # Optional: Direct node content for canvas synthesis (bypasses output data lookup)
    node_data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "Optional list of node content dicts with 'id', 'title', 'content'. "
            "If provided, these contents are used directly for synthesis instead of "
            "looking up nodes in the output's data."
        ),
    )


# =============================================================================
# Response DTOs
# =============================================================================


class OutputResponse(BaseModel):
    """Response for a single output."""

    id: UUID
    project_id: UUID
    output_type: str
    document_ids: List[UUID]
    status: str
    title: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OutputListResponse(BaseModel):
    """Response for listing outputs."""

    outputs: List[OutputResponse]
    total: int


class GenerateOutputResponse(BaseModel):
    """Response when starting output generation."""

    task_id: str = Field(
        ...,
        description="Task ID for tracking generation progress via WebSocket",
    )
    output_id: UUID = Field(
        ...,
        description="ID of the output being generated",
    )
    status: str = Field(
        default="generating",
        description="Initial status of the output",
    )
    websocket_channel: str = Field(
        ...,
        description="WebSocket channel to subscribe to for real-time updates",
    )


class NodeActionResponse(BaseModel):
    """Response when starting a node action (explain/expand)."""

    task_id: str = Field(
        ...,
        description="Task ID for tracking the action progress",
    )
    action: str = Field(
        ...,
        description="Action being performed (explain, expand)",
    )
