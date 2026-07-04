"""See FSD §7.2-§7.5 — Project financials response shapes."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ResourceCostBreakdownItem(BaseModel):
    resource_name: str
    resource_designation: str
    allocation_pct: int
    loaded_cost_monthly: Decimal | None
    cost_contribution_inr: Decimal | None


class ProjectFinancialsResponse(BaseModel):
    resource_cost_inr: Decimal | None
    non_human_cost_inr: Decimal | None
    total_cost_inr: Decimal | None
    projected_revenue_inr: Decimal | None
    actual_revenue_inr: Decimal | None
    projected_margin_inr: Decimal | None
    projected_margin_pct: Decimal | None
    actual_margin_inr: Decimal | None
    actual_margin_pct: Decimal | None
    resource_cost_breakdown: list[ResourceCostBreakdownItem]
    missing_costs: list[str]
    missing_rates: list[str]
    exchange_rate_used: Decimal | None


class ClientPerProjectItem(BaseModel):
    project_id: str
    project_name: str
    total_cost_inr: Decimal | None
    projected_revenue_inr: Decimal | None
    actual_revenue_inr: Decimal | None


class ClientFinancialsResponse(BaseModel):
    total_resource_cost_inr: Decimal | None
    total_non_human_cost_inr: Decimal | None
    total_cost_inr: Decimal | None
    total_projected_revenue_inr: Decimal | None
    total_actual_revenue_inr: Decimal | None
    projected_margin_inr: Decimal | None
    projected_margin_pct: Decimal | None
    actual_margin_inr: Decimal | None
    actual_margin_pct: Decimal | None
    per_project: list[ClientPerProjectItem]


class ProjectTypeRevenueItem(BaseModel):
    project_type: str
    projected_revenue_inr: Decimal | None
    actual_revenue_inr: Decimal | None


class CompanyFinancialsResponse(BaseModel):
    total_resource_cost_inr: Decimal | None
    total_non_human_cost_inr: Decimal | None
    total_cost_inr: Decimal | None
    total_projected_revenue_inr: Decimal | None
    total_actual_revenue_inr: Decimal | None
    total_projected_margin_inr: Decimal | None
    total_projected_margin_pct: Decimal | None
    total_actual_margin_inr: Decimal | None
    total_actual_margin_pct: Decimal | None
    revenue_by_project_type: list[ProjectTypeRevenueItem]
    # See BUSINESS-RULES.md §7.2-§7.3 — a single project missing loaded_cost/billing_rate
    # nulls the whole company-wide total (null-safe aggregation). This count lets callers
    # explain a null total instead of showing an unexplained blank.
    projects_with_incomplete_data: int


class ResourceBenchCostResponse(BaseModel):
    days_on_bench: int | None
    daily_bench_cost_inr: Decimal | None
    total_bench_cost_inr: Decimal | None
    bench_start_date: date | None


class CompanyFinanceDashboardResponse(BaseModel):
    """See BUSINESS-RULES.md §7.3a, §7.4, §7.5a — Company Finance Dashboard aggregations."""

    period_start: date
    period_end: date
    actual_revenue_inr: Decimal
    projected_revenue_inr: Decimal
    resource_cost_inr: Decimal
    non_human_cost_inr: Decimal
    total_cost_inr: Decimal
    projected_margin_inr: Decimal
    projected_margin_pct: Decimal | None
    actual_margin_inr: Decimal
    actual_margin_pct: Decimal | None
    projects_with_incomplete_financial_data: int
