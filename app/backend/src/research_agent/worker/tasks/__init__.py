"""Background task handlers."""

from research_agent.worker.tasks.base import BaseTask
from research_agent.worker.tasks.canvas_cleanup import CanvasCleanupTask
from research_agent.worker.tasks.canvas_syncer import CanvasSyncerTask
from research_agent.worker.tasks.document_processor import DocumentProcessorTask
from research_agent.worker.tasks.graph_extractor import GraphExtractorTask
from research_agent.worker.tasks.thumbnail_generator import ThumbnailGeneratorTask
from research_agent.worker.tasks.url_processor import URLProcessorTask

__all__ = [
    "BaseTask",
    "DocumentProcessorTask",
    "GraphExtractorTask",
    "CanvasSyncerTask",
    "CanvasCleanupTask",
    "ThumbnailGeneratorTask",
    "URLProcessorTask",
]
