"""See FSD §7.1 — Utilization dashboard response schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class BenchResource(BaseModel):
    id: UUID
    name: str
    designation: str
    days_on_bench: int


class UpcomingRelease(BaseModel):
    resource_name: str
    project_name: str
    end_date: date
    days_remaining: int


class DMDashboardResponse(BaseModel):
    portfolio_utilization_pct: Decimal
    active_project_count: int
    resource_count: int
    bench_count: int
    upcoming_releases_30d: list[UpcomingRelease]
    delivery_delays: list | None = None
    projected_revenue_inr: Decimal | None = None
    total_cost_inr: Decimal | None = None


class AvailabilityBenchResource(BaseModel):
    id: UUID
    name: str
    designation: str
    technical_expertise: str | None
    days_on_bench: int
    tags: list[str]
    bench_cost_daily: Decimal | None = None
    bench_cost_total: Decimal | None = None


class AvailabilityPartialResource(BaseModel):
    id: UUID
    name: str
    designation: str
    total_allocation_pct: int
    spare_capacity_pct: int
    projects: list[str]


class AvailabilityReleasingSoon(BaseModel):
    resource_id: UUID
    name: str
    designation: str
    project_name: str
    allocation_pct: int
    end_date: date
    days_remaining: int


class AvailabilityFullyAllocated(BaseModel):
    id: UUID
    name: str
    designation: str
    total_allocation_pct: int
    projects: list[str]


class AvailabilityResponse(BaseModel):
    bench: list[AvailabilityBenchResource]
    partial: list[AvailabilityPartialResource]
    releasing_soon: list[AvailabilityReleasingSoon]
    fully_allocated: list[AvailabilityFullyAllocated]
    can_see_bench_cost: bool = False
    total_bench_cost_monthly: Decimal | None = None


class BenchListItem(BaseModel):
    """See modules/10-bench-forecasting/API.md — GET /api/bench."""

    id: UUID
    name: str
    designation: str
    technical_expertise: str | None
    tags: list[str]
    days_on_bench: int
    bench_start_date: date
    loaded_cost_monthly: Decimal | None = None
    daily_bench_cost_inr: Decimal | None = None
    total_bench_cost_inr: Decimal | None = None


class BenchSummaryResource(BaseModel):
    name: str
    days_on_bench: int


class BenchSummaryResponse(BaseModel):
    """See modules/10-bench-forecasting/API.md — GET /api/bench/summary."""

    bench_count: int
    total_bench_cost_monthly: Decimal | None = None
    average_bench_duration: Decimal | None = None
    resources: list[BenchSummaryResource]


class AvailabilityUpcomingResource(BaseModel):
    id: UUID
    name: str
    designation: str


class AvailabilityUpcomingProject(BaseModel):
    id: UUID
    name: str


class AvailabilityUpcomingItem(BaseModel):
    """See modules/10-bench-forecasting/API.md — GET /api/availability/upcoming."""

    resource: AvailabilityUpcomingResource
    project: AvailabilityUpcomingProject
    allocation_pct: int
    end_date: date
    days_remaining: int


class AvailabilityPartialProject(BaseModel):
    id: UUID
    name: str


class AvailabilityPartialItem(BaseModel):
    """See modules/10-bench-forecasting/API.md — GET /api/availability/partial."""

    id: UUID
    name: str
    designation: str
    total_allocation_pct: int
    spare_capacity_pct: int
    projects: list[AvailabilityPartialProject]


class OverdueMilestoneItem(BaseModel):
    """See FSD §12 — Overdue Milestones: planned_delivery_date < today AND status = PLANNED."""

    id: UUID
    project_id: UUID
    project_name: str
    name: str
    planned_delivery_date: date
    days_overdue: int


class CompanyDashboardResponse(BaseModel):
    billable_utilization_pct: Decimal
    total_active_resources: int
    bench_count: int
    bench_resources: list[BenchResource]
    shadow_count: int
    shadow_total_allocation_pct: int
    active_project_count: int
    active_projects_by_type: dict[str, int]
    upcoming_releases_30d: list[UpcomingRelease]
    overdue_milestones_count: int | None = None
    overdue_milestones: list[OverdueMilestoneItem] | None = None
    resource_cost_inr: Decimal | None = None
    non_human_cost_inr: Decimal | None = None
    projected_revenue_inr: Decimal | None = None
    actual_revenue_inr: Decimal | None = None
    total_cost_inr: Decimal | None = None
    projected_margin_inr: Decimal | None = None
    projected_margin_pct: Decimal | None = None
    actual_margin_inr: Decimal | None = None
    actual_margin_pct: Decimal | None = None
    overall_margin_pct: Decimal | None = None
    total_bench_cost_monthly: Decimal | None = None
