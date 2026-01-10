from pydantic import BaseModel


class MigrateDataRequest(BaseModel):
    """Request to migrate anonymous data to authenticated user."""

    anonymous_session_id: str
