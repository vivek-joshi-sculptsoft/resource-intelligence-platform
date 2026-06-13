import uuid
from datetime import date

from pydantic import BaseModel, Field


class ClientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry: str | None = Field(None, max_length=100)
    contact_name: str | None = Field(None, max_length=255)
    contact_email: str | None = None
    contact_phone: str | None = Field(None, max_length=20)
    engagement_start_date: date | None = None
    notes: str | None = None


class ClientUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    industry: str | None = Field(None, max_length=100)
    contact_name: str | None = Field(None, max_length=255)
    contact_email: str | None = None
    contact_phone: str | None = Field(None, max_length=20)
    engagement_start_date: date | None = None
    notes: str | None = None


class ClientListItem(BaseModel):
    id: uuid.UUID
    name: str
    industry: str | None
    engagement_start_date: date | None
    active_project_count: int
    is_active: bool

    model_config = {"from_attributes": True}


class ClientDetail(BaseModel):
    id: uuid.UUID
    name: str
    industry: str | None
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    engagement_start_date: date | None
    notes: str | None
    is_active: bool
    created_at: str
    projects: list[dict]
    dashboard: dict

    model_config = {"from_attributes": True}
