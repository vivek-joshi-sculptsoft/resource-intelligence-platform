import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    FIXED_PRICE = "FIXED_PRICE"
    TIME_AND_MATERIAL = "TIME_AND_MATERIAL"
    CLIENT_ONBOARDING = "CLIENT_ONBOARDING"


class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    client_id: uuid.UUID
    type: ProjectType
    billing_currency: str = Field("INR", max_length=3)
    start_date: date | None = None
    contract_end_date: date | None = None
    dm_id: uuid.UUID
    pm_id: uuid.UUID
    worklog_enabled: bool = False
    notes: str | None = None


class ProjectStatusRequest(BaseModel):
    status: ProjectStatus


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    client_id: uuid.UUID | None = None
    type: ProjectType | None = None
    billing_currency: str | None = Field(None, max_length=3)
    start_date: date | None = None
    contract_end_date: date | None = None
    dm_id: uuid.UUID | None = None
    pm_id: uuid.UUID | None = None
    worklog_enabled: bool | None = None
    notes: str | None = None


class RelatedEntity(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class ProjectListItem(BaseModel):
    id: uuid.UUID
    name: str
    client_name: str
    type: str
    status: str
    billing_currency: str
    dm_name: str
    pm_name: str
    start_date: date | None
    contract_end_date: date | None

    model_config = {"from_attributes": True}


class ProjectDetail(BaseModel):
    id: uuid.UUID
    name: str
    client: RelatedEntity
    type: str
    status: str
    billing_currency: str
    contract_value: float | None = None
    start_date: date | None
    contract_end_date: date | None
    dm: RelatedEntity
    pm: RelatedEntity
    worklog_enabled: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
