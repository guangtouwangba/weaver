"""Chat use cases."""

from research_agent.application.use_cases.chat.get_history import (
    ChatMessageDTO,
    GetHistoryInput,
    GetHistoryOutput,
    GetHistoryUseCase,
)
from research_agent.application.use_cases.chat.session_management import (
    CreateSessionInput,
    CreateSessionOutput,
    CreateSessionUseCase,
    DeleteSessionInput,
    DeleteSessionOutput,
    DeleteSessionUseCase,
    GetOrCreateDefaultSessionInput,
    GetOrCreateDefaultSessionOutput,
    GetOrCreateDefaultSessionUseCase,
    ListSessionsInput,
    ListSessionsOutput,
    ListSessionsUseCase,
    SessionDTO,
    UpdateSessionInput,
    UpdateSessionOutput,
    UpdateSessionUseCase,
)

__all__ = [
    # History
    "ChatMessageDTO",
    "GetHistoryInput",
    "GetHistoryOutput",
    "GetHistoryUseCase",
    # Session Management
    "SessionDTO",
    "CreateSessionInput",
    "CreateSessionOutput",
    "CreateSessionUseCase",
    "ListSessionsInput",
    "ListSessionsOutput",
    "ListSessionsUseCase",
    "UpdateSessionInput",
    "UpdateSessionOutput",
    "UpdateSessionUseCase",
    "DeleteSessionInput",
    "DeleteSessionOutput",
    "DeleteSessionUseCase",
    "GetOrCreateDefaultSessionInput",
    "GetOrCreateDefaultSessionOutput",
    "GetOrCreateDefaultSessionUseCase",
]