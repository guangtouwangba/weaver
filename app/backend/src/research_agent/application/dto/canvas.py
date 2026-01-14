# ruff: noqa: N815
"""Canvas DTOs for API requests/responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CanvasNodeDTO(BaseModel):
    """Canvas node DTO."""

    id: str
    type: str = "card"
    subType: str | None = None  # 'source' for PDF documents
    title: str = ""
    content: str = ""
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 150
    color: str = "default"
    tags: list[str] = []
    sourceId: str | None = None
    sourcePage: int | None = None
    fileMetadata: dict[str, Any] | None = None  # Metadata including thumbnail URL
    # New fields for view system
    viewType: str = "free"  # 'free' | 'thinking'
    sectionId: str | None = None
    promotedFrom: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None


class CanvasEdgeDTO(BaseModel):
    """Canvas edge DTO."""

    id: str | None = None
    source: str
    target: str
    relationType: str | None = None  # 'structural', 'supports', 'contradicts', 'correlates'
    label: str | None = None
    metadata: dict[str, Any] | None = None


class CanvasViewportDTO(BaseModel):
    """Canvas viewport DTO."""

    x: float = 0
    y: float = 0
    scale: float = 1


class CanvasSectionDTO(BaseModel):
    """Canvas section DTO."""

    id: str
    title: str
    viewType: str = "free"  # 'free' | 'thinking'
    isCollapsed: bool = False
    nodeIds: list[str] = []
    x: float = 0
    y: float = 0
    width: float | None = None
    height: float | None = None
    conversationId: str | None = None
    question: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None


class CanvasViewStateDTO(BaseModel):
    """Canvas view state DTO."""

    viewType: str  # 'free' | 'thinking'
    viewport: CanvasViewportDTO
    selectedNodeIds: list[str] = []
    collapsedSectionIds: list[str] = []


class CanvasDataRequest(BaseModel):
    """Request DTO for saving canvas data."""

    nodes: list[CanvasNodeDTO] = []
    edges: list[CanvasEdgeDTO] = []
    sections: list[CanvasSectionDTO] = []
    viewport: CanvasViewportDTO = CanvasViewportDTO()  # Legacy: for backward compatibility
    viewStates: dict[str, CanvasViewStateDTO] = {}  # Key: 'free' | 'thinking'


class CanvasDataResponse(BaseModel):
    """Response DTO for canvas data."""

    nodes: list[CanvasNodeDTO]
    edges: list[CanvasEdgeDTO]
    sections: list[CanvasSectionDTO] = []
    viewport: CanvasViewportDTO  # Legacy: for backward compatibility
    viewStates: dict[str, CanvasViewStateDTO] = {}  # Key: 'free' | 'thinking'
    updated_at: datetime | None = None
    version: int | None = None  # Canvas version for optimistic locking


class CanvasSaveResponse(BaseModel):
    """Response DTO for canvas save operation."""

    success: bool
    updated_at: datetime
    version: int  # Canvas version after save


class CreateCanvasNodeRequest(BaseModel):
    """Request DTO for creating a canvas node."""

    type: str = "card"
    title: str = ""
    content: str = ""
    x: float
    y: float
    width: float = 200
    height: float = 150
    color: str = "default"
    tags: list[str] = []
    sourceId: str | None = None
    sourcePage: int | None = None
    fileMetadata: dict[str, Any] | None = None
    viewType: str = "free"  # 'free' | 'thinking'
    sectionId: str | None = None
    promotedFrom: str | None = None


class UpdateCanvasNodeRequest(BaseModel):
    """Request DTO for updating a canvas node."""

    type: str | None = None
    title: str | None = None
    content: str | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    color: str | None = None
    tags: list[str] | None = None
    sourceId: str | None = None
    sourcePage: int | None = None
    fileMetadata: dict[str, Any] | None = None
    viewType: str | None = None
    sectionId: str | None = None
    promotedFrom: str | None = None


class CanvasNodeOperationResponse(BaseModel):
    """Response DTO for canvas node operations."""

    success: bool
    nodeId: str | None = None
    updated_at: datetime
    version: int  # Canvas version after operation
