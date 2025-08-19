from domain.shared.domain_event import DomainEvent
from domain.shared.event_types import EventType
from domain.file.file import FileEntity

class FileUploadedConfirmEvent(DomainEvent):
    """文件上传确认事件"""

    def __init__(self, file: FileEntity):
        super().__init__(event_type=EventType.FILE_CONFIRMED,
                         file_id=file.id,
                         file_metadata=file.metadata,
                         storage_location=file.storage_location)
        self.file = file  # Store the complete file entity