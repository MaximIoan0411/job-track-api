import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.enums import AuditAction


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    action: AuditAction
    changes: dict[str, Any] | None
    created_at: datetime