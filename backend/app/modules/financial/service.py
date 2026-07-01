"""See BUSINESS-RULES.md §7.2-§7.6 — project cost, revenue, margin, and bench cost calculations."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.auth.models import SystemConfig
from app.modules.financial.schemas import (
    ClientFinancialsResponse,
    ClientPerProjectItem,
    CompanyFinancialsResponse,
    ProjectFinancialsResponse,
    ProjectTypeRevenueItem,
    ResourceBenchCostResponse,
    ResourceCostBreakdownItem,
)
from app.modules.invoicing.models import Invoice
from app.modules.nonhuman_costs.models import NonHumanCost
from app.modules.projects.models import Project
from app.modules.resources.models import Resource

WORKING_HOURS_PER_DAY = 8


def _sum_or_none(values: list[Decimal | None]) -> Decimal | None:
    """See BUSINESS-RULES.md §7.5 — client/company margin sums across projects.
    Null-safe: matches project-level convention of returning null when any input is missing."""
    if any(v is None for v in values):
        return None
    return sum(values, Decimal("0"))


def _margin(revenue: Decimal | None, cost: Decimal | None) -> tuple[Decimal | None, Decimal | None]:
    if revenue is None or cost is None:
        return None, None
    margin = revenue - cost
    margin_pct = (margin / revenue * 100).quantize(Decimal("0.01")) if revenue != 0 else None
    return margin, margin_pct


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
                        resource_designation=a.resource.designation,
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
                    resource_designation=a.resource.designation,
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
                resource_designation=a.resource.designation,
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
        non_human_cost_inr = sum((Decimal(str(c.amount_inr)) for c in nonhuman_costs), Decimal("0"))

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


async def get_client_financials(
    db: AsyncSession,
    projects: list[Project],
    can_see_cost: bool,
    can_see_rate: bool,
    can_see_invoicing: bool,
    can_see_nonhuman: bool,
) -> ClientFinancialsResponse:
    """See BUSINESS-RULES.md §7.5 — client-level: sum across all the client's projects."""

    per_project_data = [
        (
            project,
            await get_project_financials(
                db, project, can_see_cost, can_see_rate, can_see_invoicing, can_see_nonhuman
            ),
        )
        for project in projects
    ]

    total_resource_cost_inr = _sum_or_none([f.resource_cost_inr for _, f in per_project_data])
    total_non_human_cost_inr = _sum_or_none([f.non_human_cost_inr for _, f in per_project_data])
    total_cost_inr = _sum_or_none([f.total_cost_inr for _, f in per_project_data])
    total_projected_revenue_inr = _sum_or_none(
        [f.projected_revenue_inr for _, f in per_project_data]
    )
    total_actual_revenue_inr = _sum_or_none([f.actual_revenue_inr for _, f in per_project_data])

    projected_margin_inr, projected_margin_pct = _margin(
        total_projected_revenue_inr, total_cost_inr
    )
    actual_margin_inr, actual_margin_pct = _margin(total_actual_revenue_inr, total_cost_inr)

    return ClientFinancialsResponse(
        total_resource_cost_inr=total_resource_cost_inr,
        total_non_human_cost_inr=total_non_human_cost_inr,
        total_cost_inr=total_cost_inr,
        total_projected_revenue_inr=total_projected_revenue_inr,
        total_actual_revenue_inr=total_actual_revenue_inr,
        projected_margin_inr=projected_margin_inr,
        projected_margin_pct=projected_margin_pct,
        actual_margin_inr=actual_margin_inr,
        actual_margin_pct=actual_margin_pct,
        per_project=[
            ClientPerProjectItem(
                project_id=str(project.id),
                project_name=project.name,
                total_cost_inr=f.total_cost_inr,
                projected_revenue_inr=f.projected_revenue_inr,
                actual_revenue_inr=f.actual_revenue_inr,
            )
            for project, f in per_project_data
        ],
    )


async def get_company_financials(
    db: AsyncSession,
    projects: list[Project],
    can_see_cost: bool,
    can_see_rate: bool,
    can_see_invoicing: bool,
    can_see_nonhuman: bool,
) -> CompanyFinancialsResponse:
    """See BUSINESS-RULES.md §7.5 — company-level: sum across all projects."""

    per_project_data = [
        (
            project,
            await get_project_financials(
                db, project, can_see_cost, can_see_rate, can_see_invoicing, can_see_nonhuman
            ),
        )
        for project in projects
    ]

    total_resource_cost_inr = _sum_or_none([f.resource_cost_inr for _, f in per_project_data])
    total_non_human_cost_inr = _sum_or_none([f.non_human_cost_inr for _, f in per_project_data])
    total_cost_inr = _sum_or_none([f.total_cost_inr for _, f in per_project_data])
    total_projected_revenue_inr = _sum_or_none(
        [f.projected_revenue_inr for _, f in per_project_data]
    )
    total_actual_revenue_inr = _sum_or_none([f.actual_revenue_inr for _, f in per_project_data])

    total_projected_margin_inr, total_projected_margin_pct = _margin(
        total_projected_revenue_inr, total_cost_inr
    )
    total_actual_margin_inr, total_actual_margin_pct = _margin(
        total_actual_revenue_inr, total_cost_inr
    )

    by_type: dict[str, list[tuple[Decimal | None, Decimal | None]]] = {}
    for project, f in per_project_data:
        by_type.setdefault(project.type, []).append((f.projected_revenue_inr, f.actual_revenue_inr))
    revenue_by_project_type = [
        ProjectTypeRevenueItem(
            project_type=project_type,
            projected_revenue_inr=_sum_or_none([p for p, _ in pairs]),
            actual_revenue_inr=_sum_or_none([a for _, a in pairs]),
        )
        for project_type, pairs in by_type.items()
    ]

    return CompanyFinancialsResponse(
        total_resource_cost_inr=total_resource_cost_inr,
        total_non_human_cost_inr=total_non_human_cost_inr,
        total_cost_inr=total_cost_inr,
        total_projected_revenue_inr=total_projected_revenue_inr,
        total_actual_revenue_inr=total_actual_revenue_inr,
        total_projected_margin_inr=total_projected_margin_inr,
        total_projected_margin_pct=total_projected_margin_pct,
        total_actual_margin_inr=total_actual_margin_inr,
        total_actual_margin_pct=total_actual_margin_pct,
        revenue_by_project_type=revenue_by_project_type,
    )


async def get_resource_bench_cost(
    db: AsyncSession,
    resource: Resource,
    can_see_cost: bool,
) -> ResourceBenchCostResponse | None:
    """See BUSINESS-RULES.md §7.6 — Bench Cost. None if resource has ACTIVE assignments."""

    active_assignments = (
        await db.execute(
            select(Assignment).where(
                Assignment.resource_id == resource.id,
                Assignment.status == "ACTIVE",
            )
        )
    ).scalars().first()
    if active_assignments is not None:
        return None

    last_released = (
        await db.execute(
            select(Assignment)
            .where(Assignment.resource_id == resource.id, Assignment.released_at.isnot(None))
            .order_by(Assignment.released_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    bench_start_date = (
        last_released.released_at.date() if last_released else resource.date_of_joining
    )
    if bench_start_date is None:
        return ResourceBenchCostResponse(
            days_on_bench=None,
            daily_bench_cost_inr=None,
            total_bench_cost_inr=None,
            bench_start_date=None,
        )

    days_on_bench = (date.today() - bench_start_date).days

    daily_bench_cost_inr: Decimal | None = None
    total_bench_cost_inr: Decimal | None = None
    if can_see_cost and resource.loaded_cost_monthly is not None:
        working_days = await _get_working_days(db)
        daily_bench_cost_inr = Decimal(str(resource.loaded_cost_monthly)) / Decimal(working_days)
        total_bench_cost_inr = daily_bench_cost_inr * Decimal(days_on_bench)

    return ResourceBenchCostResponse(
        days_on_bench=days_on_bench,
        daily_bench_cost_inr=daily_bench_cost_inr,
        total_bench_cost_inr=total_bench_cost_inr,
        bench_start_date=bench_start_date,
    )
