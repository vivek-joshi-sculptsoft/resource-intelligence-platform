"""See FSD §2.10 — NonHumanCost request/response schemas."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class CostCategory(StrEnum):
    AI_TOOLS = "AI_TOOLS"
    CLOUD_INFRA = "CLOUD_INFRA"
    DEVICES = "DEVICES"
    THIRD_PARTY_LICENSE = "THIRD_PARTY_LICENSE"
    OTHER = "OTHER"


class NonHumanCostCreateRequest(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    category: CostCategory
    amount: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    exchange_rate: float | None = Field(default=None, gt=0)
    cost_date: date
    is_recurring: bool = False
    recurring_end_date: date | None = None


class NonHumanCostUpdateRequest(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=500)
    category: CostCategory | None = None
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    exchange_rate: float | None = Field(default=None, gt=0)
    cost_date: date | None = None
    is_recurring: bool | None = None
    recurring_end_date: date | None = None
