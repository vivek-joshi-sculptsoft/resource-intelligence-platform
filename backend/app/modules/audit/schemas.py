import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class AuditLogChangedBy(BaseModel):
    id: uuid.UUID
    name: str


class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: uuid.UUID
    entity_name: str | None
    action: str
    field_name: str | None
    old_value: Any
    new_value: Any
    changed_by: AuditLogChangedBy
    changed_at: datetime

    @field_validator("old_value", "new_value", mode="before")
    @classmethod
    def parse_json_value(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return v
        return v
