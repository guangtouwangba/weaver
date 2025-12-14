"""Canvas DTOs for API requests/responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class CanvasNodeDTO(BaseModel):
    """Canvas node DTO."""

    id: str
    type: str = "card"
    title: str = ""
    content: str = ""
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 150
    color: str = "default"
    tags: List[str] = []
    sourceId: Optional[str] = None
    sourcePage: Optional[int] = None
    # New fields for view system
    viewType: str = "free"  # 'free' | 'thinking'
    sectionId: Optional[str] = None
    promotedFrom: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class CanvasEdgeDTO(BaseModel):
    """Canvas edge DTO."""

    id: Optional[str] = None
    source: str
    target: str


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
    nodeIds: List[str] = []
    x: float = 0
    y: float = 0
    width: Optional[float] = None
    height: Optional[float] = None
    conversationId: Optional[str] = None
    question: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class CanvasViewStateDTO(BaseModel):
    """Canvas view state DTO."""

    viewType: str  # 'free' | 'thinking'
    viewport: CanvasViewportDTO
    selectedNodeIds: List[str] = []
    collapsedSectionIds: List[str] = []


class CanvasDataRequest(BaseModel):
    """Request DTO for saving canvas data."""

    nodes: List[CanvasNodeDTO] = []
    edges: List[CanvasEdgeDTO] = []
    sections: List[CanvasSectionDTO] = []
    viewport: CanvasViewportDTO = CanvasViewportDTO()  # Legacy: for backward compatibility
    viewStates: Dict[str, CanvasViewStateDTO] = {}  # Key: 'free' | 'thinking'


class CanvasDataResponse(BaseModel):
    """Response DTO for canvas data."""

    nodes: List[CanvasNodeDTO]
    edges: List[CanvasEdgeDTO]
    sections: List[CanvasSectionDTO] = []
    viewport: CanvasViewportDTO  # Legacy: for backward compatibility
    viewStates: Dict[str, CanvasViewStateDTO] = {}  # Key: 'free' | 'thinking'
    updated_at: Optional[datetime] = None
    version: Optional[int] = None  # Canvas version for optimistic locking


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
    tags: List[str] = []
    sourceId: Optional[str] = None
    sourcePage: Optional[int] = None
    viewType: str = "free"  # 'free' | 'thinking'
    sectionId: Optional[str] = None
    promotedFrom: Optional[str] = None


class UpdateCanvasNodeRequest(BaseModel):
    """Request DTO for updating a canvas node."""

    type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None
    sourceId: Optional[str] = None
    sourcePage: Optional[int] = None
    viewType: Optional[str] = None
    sectionId: Optional[str] = None
    promotedFrom: Optional[str] = None


class CanvasNodeOperationResponse(BaseModel):
    """Response DTO for canvas node operations."""

    success: bool
    nodeId: Optional[str] = None
    updated_at: datetime
    version: int  # Canvas version after operation
