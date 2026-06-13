import uuid
from datetime import date

from pydantic import BaseModel, Field


class ResourceCreateRequest(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    designation: str = Field(..., min_length=1, max_length=100)
    technical_expertise: str | None = Field(None, max_length=100)
    date_of_joining: date | None = None
    reporting_manager_id: uuid.UUID | None = None
    tags: list[str] = Field(default_factory=list)


class ResourceUpdateRequest(BaseModel):
    employee_id: str | None = Field(None, min_length=1, max_length=50)
    name: str | None = Field(None, min_length=1, max_length=255)
    designation: str | None = Field(None, min_length=1, max_length=100)
    technical_expertise: str | None = Field(None, max_length=100)
    date_of_joining: date | None = None
    reporting_manager_id: uuid.UUID | None = None


class TagRequest(BaseModel):
    tag: str = Field(..., min_length=1, max_length=100)


class ManagerResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class ResourceListItem(BaseModel):
    id: uuid.UUID
    employee_id: str
    name: str
    designation: str
    technical_expertise: str | None
    total_allocation_pct: int
    is_active: bool
    tags: list[str]
    loaded_cost_monthly: float | None = None

    model_config = {"from_attributes": True}


class ResourceDetail(BaseModel):
    id: uuid.UUID
    employee_id: str
    name: str
    designation: str
    technical_expertise: str | None
    date_of_joining: date | None
    reporting_manager: ManagerResponse | None
    loaded_cost_monthly: float | None = None
    is_active: bool
    tags: list[str]
    total_allocation_pct: int
    created_at: str

    model_config = {"from_attributes": True}
