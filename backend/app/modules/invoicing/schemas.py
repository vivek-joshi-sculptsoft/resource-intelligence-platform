"""See FSD §2.8, §2.9 — Invoicing request/response schemas."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class MilestoneStatus(StrEnum):
    PLANNED = "PLANNED"
    DELIVERED = "DELIVERED"
    APPROVED = "APPROVED"
    INVOICED = "INVOICED"
    PAID = "PAID"


class InvoiceStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PAID = "PAID"


# See FSD §6.2 — Milestone status transitions
MILESTONE_FORWARD_TRANSITIONS: dict[MilestoneStatus, MilestoneStatus] = {
    MilestoneStatus.PLANNED: MilestoneStatus.DELIVERED,
    MilestoneStatus.DELIVERED: MilestoneStatus.APPROVED,
    MilestoneStatus.APPROVED: MilestoneStatus.INVOICED,
    MilestoneStatus.INVOICED: MilestoneStatus.PAID,
}

MILESTONE_BACKWARD_TRANSITIONS: dict[MilestoneStatus, MilestoneStatus] = {
    MilestoneStatus.DELIVERED: MilestoneStatus.PLANNED,
    MilestoneStatus.APPROVED: MilestoneStatus.DELIVERED,
}

# Finance-only transitions
FINANCE_ONLY_TRANSITIONS: set[tuple[str, str]] = {
    (MilestoneStatus.APPROVED, MilestoneStatus.INVOICED),
    (MilestoneStatus.INVOICED, MilestoneStatus.PAID),
}

# See FSD §6.3 — Invoice status transitions (forward-only)
INVOICE_FORWARD_TRANSITIONS: dict[InvoiceStatus, InvoiceStatus] = {
    InvoiceStatus.DRAFT: InvoiceStatus.SUBMITTED,
    InvoiceStatus.SUBMITTED: InvoiceStatus.APPROVED,
    InvoiceStatus.APPROVED: InvoiceStatus.PAID,
}


class MilestoneCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0)
    planned_delivery_date: date | None = None
    sort_order: int | None = None


class MilestoneUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    amount: float | None = Field(default=None, gt=0)
    planned_delivery_date: date | None = None
    sort_order: int | None = None


class MilestoneStatusRequest(BaseModel):
    status: MilestoneStatus


class InvoiceCreateRequest(BaseModel):
    invoice_date: date
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    exchange_rate: float | None = Field(default=None, gt=0)
    milestone_id: str | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    notes: str | None = None


class InvoiceUpdateRequest(BaseModel):
    invoice_date: date | None = None
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    exchange_rate: float | None = Field(default=None, gt=0)
    milestone_id: str | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    notes: str | None = None


class InvoiceStatusRequest(BaseModel):
    status: InvoiceStatus
