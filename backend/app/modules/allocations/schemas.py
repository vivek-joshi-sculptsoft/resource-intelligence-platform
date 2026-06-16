"""See FSD §2.7 — Assignment schemas."""

import uuid
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class AssignmentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    AUTO_RELEASED = "AUTO_RELEASED"


class AssignmentCreateRequest(BaseModel):
    resource_id: uuid.UUID
    allocation_pct: int = Field(ge=1, le=100)
    billability_pct: int = Field(ge=0, le=100)
    is_shadow: bool = False
    project_designation: str | None = None
    project_expertise: str | None = None
    billing_rate: float | None = None
    start_date: date
    end_date: date | None = None


class AssignmentUpdateRequest(BaseModel):
    allocation_pct: int | None = Field(None, ge=1, le=100)
    billability_pct: int | None = Field(None, ge=0, le=100)
    is_shadow: bool | None = None
    project_designation: str | None = None
    project_expertise: str | None = None
    billing_rate: float | None = None
    start_date: date | None = None
    end_date: date | None = None
