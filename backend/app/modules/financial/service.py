"""See BUSINESS-RULES.md §7.2-§7.5 — project cost, revenue, and margin calculations."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.auth.models import SystemConfig
from app.modules.financial.schemas import ProjectFinancialsResponse, ResourceCostBreakdownItem
from app.modules.invoicing.models import Invoice
from app.modules.nonhuman_costs.models import NonHumanCost
from app.modules.projects.models import Project

WORKING_HOURS_PER_DAY = 8


async def _get_working_days(db: AsyncSession) -> int:
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "system.working_days_per_month")
    )
    config = result.scalar_one_or_none()
    return int(config.value) if config else 22


async def get_project_financials(
    db: AsyncSession,
    project: Project,
    can_see_cost: bool,
    can_see_rate: bool,
    can_see_invoicing: bool,
    can_see_nonhuman: bool,
) -> ProjectFinancialsResponse:
    """See BUSINESS-RULES.md §7.2-§7.5. Fields are null where inputs are missing or restricted."""

    working_days = await _get_working_days(db)

    active_assignments = (
        (
            await db.execute(
                select(Assignment).where(
                    Assignment.project_id == project.id,
                    Assignment.status == "ACTIVE",
                )
            )
        )
        .scalars()
        .all()
    )

    # See BUSINESS-RULES.md §7.2 — Resource Cost (shadow resources contribute to cost)
    resource_cost_inr: Decimal | None = None
    resource_cost_breakdown: list[ResourceCostBreakdownItem] = []
    missing_costs: list[str] = []

    if can_see_cost:
        cost_total = Decimal("0")
        cost_complete = True
        for a in active_assignments:
            loaded_cost = a.resource.loaded_cost_monthly
            if loaded_cost is None:
                cost_complete = False
                missing_costs.append(a.resource.name)
                resource_cost_breakdown.append(
                    ResourceCostBreakdownItem(
                        resource_name=a.resource.name,
                        allocation_pct=a.allocation_pct,
                        loaded_cost_monthly=None,
                        cost_contribution_inr=None,
                    )
                )
                continue
            contribution = Decimal(str(loaded_cost)) * a.allocation_pct / Decimal("100")
            cost_total += contribution
            resource_cost_breakdown.append(
                ResourceCostBreakdownItem(
                    resource_name=a.resource.name,
                    allocation_pct=a.allocation_pct,
                    loaded_cost_monthly=Decimal(str(loaded_cost)),
                    cost_contribution_inr=contribution,
                )
            )
        resource_cost_inr = cost_total if cost_complete else None
    else:
        resource_cost_breakdown = [
            ResourceCostBreakdownItem(
                resource_name=a.resource.name,
                allocation_pct=a.allocation_pct,
                loaded_cost_monthly=None,
                cost_contribution_inr=None,
            )
            for a in active_assignments
        ]

    # See BUSINESS-RULES.md §7.2 — Non-Human Cost
    non_human_cost_inr: Decimal | None = None
    if can_see_nonhuman:
        nonhuman_costs = (
            (
                await db.execute(
                    select(NonHumanCost).where(
                        NonHumanCost.project_id == project.id,
                        NonHumanCost.is_active == True,  # noqa: E712
                    )
                )
            )
            .scalars()
            .all()
        )
        non_human_cost_inr = sum(
            (Decimal(str(c.amount_inr)) for c in nonhuman_costs), Decimal("0")
        )

    total_cost_inr: Decimal | None = None
    if resource_cost_inr is not None and non_human_cost_inr is not None:
        total_cost_inr = resource_cost_inr + non_human_cost_inr

    # See BUSINESS-RULES.md §7.3 — Projected Revenue
    # No exchange_rate field exists on Project/Assignment for billing_rate (only Invoice/
    # NonHumanCost have one). We reuse the most recent invoice's exchange_rate as the
    # "latest_exchange_rate" called for by the formula; falls back to 1.0 if none exists yet.
    projected_revenue_inr: Decimal | None = None
    missing_rates: list[str] = []
    exchange_rate_used: Decimal | None = None

    if can_see_rate:
        if project.billing_currency == "INR":
            exchange_rate_used = Decimal("1.0")
        else:
            latest_invoice = (
                await db.execute(
                    select(Invoice)
                    .where(Invoice.project_id == project.id)
                    .order_by(Invoice.invoice_date.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            exchange_rate_used = (
                Decimal(str(latest_invoice.exchange_rate)) if latest_invoice else Decimal("1.0")
            )

        revenue_complete = True
        revenue_total = Decimal("0")
        for a in active_assignments:
            if a.is_shadow:
                continue
            if a.billing_rate is None:
                revenue_complete = False
                missing_rates.append(a.resource.name)
                continue
            revenue_total += (
                Decimal(a.billability_pct)
                / Decimal("100")
                * Decimal(working_days)
                * Decimal(WORKING_HOURS_PER_DAY)
                * Decimal(str(a.billing_rate))
            )
        projected_revenue_inr = revenue_total * exchange_rate_used if revenue_complete else None

    # See BUSINESS-RULES.md §7.4 — Actual Revenue (source of truth: invoices, not allocation)
    actual_revenue_inr: Decimal | None = None
    if can_see_invoicing:
        invoices = (
            (
                await db.execute(
                    select(Invoice).where(
                        Invoice.project_id == project.id,
                        Invoice.status.in_(["APPROVED", "PAID"]),
                    )
                )
            )
            .scalars()
            .all()
        )
        actual_revenue_inr = sum((Decimal(str(i.amount_inr)) for i in invoices), Decimal("0"))

    # See BUSINESS-RULES.md §7.5 — Margin (null-safe; pct undefined at zero revenue)
    projected_margin_inr: Decimal | None = None
    projected_margin_pct: Decimal | None = None
    if projected_revenue_inr is not None and total_cost_inr is not None:
        projected_margin_inr = projected_revenue_inr - total_cost_inr
        if projected_revenue_inr != 0:
            projected_margin_pct = (projected_margin_inr / projected_revenue_inr * 100).quantize(
                Decimal("0.01")
            )

    actual_margin_inr: Decimal | None = None
    actual_margin_pct: Decimal | None = None
    if actual_revenue_inr is not None and total_cost_inr is not None:
        actual_margin_inr = actual_revenue_inr - total_cost_inr
        if actual_revenue_inr != 0:
            actual_margin_pct = (actual_margin_inr / actual_revenue_inr * 100).quantize(
                Decimal("0.01")
            )

    return ProjectFinancialsResponse(
        resource_cost_inr=resource_cost_inr,
        non_human_cost_inr=non_human_cost_inr,
        total_cost_inr=total_cost_inr,
        projected_revenue_inr=projected_revenue_inr,
        actual_revenue_inr=actual_revenue_inr,
        projected_margin_inr=projected_margin_inr,
        projected_margin_pct=projected_margin_pct,
        actual_margin_inr=actual_margin_inr,
        actual_margin_pct=actual_margin_pct,
        resource_cost_breakdown=resource_cost_breakdown,
        missing_costs=missing_costs,
        missing_rates=missing_rates,
        exchange_rate_used=exchange_rate_used,
    )
