"""See FSD §7.2-§7.5 — Project financials response shapes."""

from decimal import Decimal

from pydantic import BaseModel


class ResourceCostBreakdownItem(BaseModel):
    resource_name: str
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
