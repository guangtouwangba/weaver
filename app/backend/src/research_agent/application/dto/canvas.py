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


class CanvasDataRequest(BaseModel):
    """Request DTO for saving canvas data."""

    nodes: List[CanvasNodeDTO] = []
    edges: List[CanvasEdgeDTO] = []
    viewport: CanvasViewportDTO = CanvasViewportDTO()


class CanvasDataResponse(BaseModel):
    """Response DTO for canvas data."""

    nodes: List[CanvasNodeDTO]
    edges: List[CanvasEdgeDTO]
    viewport: CanvasViewportDTO
    updated_at: Optional[datetime] = None


class CanvasSaveResponse(BaseModel):
    """Response DTO for canvas save operation."""

    success: bool
    updated_at: datetime

