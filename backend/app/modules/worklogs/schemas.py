"""See FSD §2.11 — Worklog request/response schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator


class WorklogCreateRequest(BaseModel):
    project_id: UUID
    log_date: date
    hours: Decimal
    note: str | None = None

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.5") or v > Decimal("24.0"):
            raise ValueError("Hours must be between 0.5 and 24.0")
        if v % Decimal("0.5") != 0:
            raise ValueError("Hours must be in 0.5 increments")
        return v


class WorklogUpdateRequest(BaseModel):
    hours: Decimal | None = None
    note: str | None = None

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return v
        if v < Decimal("0.5") or v > Decimal("24.0"):
            raise ValueError("Hours must be between 0.5 and 24.0")
        if v % Decimal("0.5") != 0:
            raise ValueError("Hours must be in 0.5 increments")
        return v


class ProjectRef(BaseModel):
    id: UUID
    name: str


class ResourceRef(BaseModel):
    id: UUID
    name: str


class WorklogResponse(BaseModel):
    id: UUID
    project: ProjectRef
    resource: ResourceRef
    log_date: date
    hours: Decimal
    note: str | None
    created_at: str
