from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None
    action: str
    model_name: str
    record_id: int
    record_name: str | None
    description: str | None
    created_at: datetime
