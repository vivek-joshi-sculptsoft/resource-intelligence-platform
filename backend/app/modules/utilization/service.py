"""See FSD §7.1 — Company utilization dashboard service."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.auth.models import SystemConfig
from app.modules.financial.service import get_company_financials
from app.modules.invoicing.models import Milestone
from app.modules.projects.models import Project
from app.modules.resources.models import Resource, ResourceTag
from app.modules.utilization.schemas import (
    AvailabilityBenchResource,
    AvailabilityFullyAllocated,
    AvailabilityPartialItem,
    AvailabilityPartialProject,
    AvailabilityPartialResource,
    AvailabilityReleasingSoon,
    AvailabilityResponse,
    AvailabilityUpcomingItem,
    AvailabilityUpcomingProject,
    AvailabilityUpcomingResource,
    BenchListItem,
    BenchResource,
    BenchSummaryResource,
    BenchSummaryResponse,
    CompanyDashboardResponse,
    DMDashboardResponse,
    OverdueMilestoneItem,
    TopProjectByTeamSize,
    UpcomingRelease,
)


async def get_company_dashboard(db: AsyncSession) -> CompanyDashboardResponse:
    """See FSD §7.1 — Company Utilization formula."""

    active_resources = (
        (
            await db.execute(
                select(Resource).where(Resource.is_active == True)  # noqa: E712
            )
        )
        .scalars()
        .all()
    )
    total_active_resources = len(active_resources)

    # See BUSINESS-RULES.md §7.1 — Billable Allocation per resource
    active_assignments = (
        (await db.execute(select(Assignment).where(Assignment.status == "ACTIVE"))).scalars().all()
    )

    resource_alloc: dict[str, int] = {}
    resource_billable: dict[str, int] = {}
    shadow_resource_ids: set[str] = set()
    shadow_total_pct = 0

    for a in active_assignments:
        rid = str(a.resource_id)
        resource_alloc[rid] = resource_alloc.get(rid, 0) + a.allocation_pct
        if not a.is_shadow:
            resource_billable[rid] = resource_billable.get(rid, 0) + a.billability_pct
        if a.is_shadow:
            shadow_resource_ids.add(rid)
            shadow_total_pct += a.allocation_pct

    # See BUSINESS-RULES.md §7.1 — Company Utilization
    total_billable = sum(resource_billable.values())
    if total_active_resources > 0:
        billable_utilization_pct = Decimal(
            str(round(total_billable / (total_active_resources * 100) * 100, 2))
        )
    else:
        billable_utilization_pct = Decimal("0")

    # See BUSINESS-RULES.md §7.6 — Bench = resource with 0 ACTIVE assignments
    allocated_resource_ids = set(resource_alloc.keys())
    bench_resources_list: list[BenchResource] = []
    today = date.today()

    for r in active_resources:
        rid = str(r.id)
        if rid not in allocated_resource_ids:
            last_release = (
                await db.execute(
                    select(func.max(Assignment.released_at)).where(
                        Assignment.resource_id == r.id,
                        Assignment.released_at.isnot(None),
                    )
                )
            ).scalar()
            if last_release:
                bench_start = last_release.date() if hasattr(last_release, "date") else last_release
            else:
                bench_start = r.date_of_joining or today
            days_on_bench = (today - bench_start).days
            bench_resources_list.append(
                BenchResource(
                    id=r.id,
                    name=r.name,
                    designation=r.designation,
                    days_on_bench=max(days_on_bench, 0),
                )
            )

    # Active projects by type
    project_rows = (
        await db.execute(
            select(Project.type, func.count(Project.id))
            .where(
                Project.status == "ACTIVE",
                Project.is_active == True,  # noqa: E712
            )
            .group_by(Project.type)
        )
    ).all()
    active_projects_by_type: dict[str, int] = {}
    active_project_count = 0
    for ptype, cnt in project_rows:
        active_projects_by_type[ptype] = cnt
        active_project_count += cnt

    # Upcoming releases within 30 days
    window_end = today + timedelta(days=30)
    upcoming = (
        (
            await db.execute(
                select(Assignment).where(
                    Assignment.status == "ACTIVE",
                    Assignment.end_date.isnot(None),
                    Assignment.end_date >= today,
                    Assignment.end_date <= window_end,
                )
            )
        )
        .scalars()
        .all()
    )

    upcoming_releases: list[UpcomingRelease] = []
    for a in upcoming:
        upcoming_releases.append(
            UpcomingRelease(
                resource_name=a.resource.name,
                project_name=a.project.name,
                end_date=a.end_date,
                days_remaining=(a.end_date - today).days,
            )
        )

    # See FSD §12 — Overdue Milestones: planned_delivery_date < today AND status = PLANNED
    overdue_rows = (
        await db.execute(
            select(Milestone, Project.name)
            .join(Project, Milestone.project_id == Project.id)
            .where(
                Milestone.status == "PLANNED",
                Milestone.planned_delivery_date.isnot(None),
                Milestone.planned_delivery_date < today,
                Milestone.is_active == True,  # noqa: E712
            )
        )
    ).all()
    overdue_milestones = [
        OverdueMilestoneItem(
            id=m.id,
            project_id=m.project_id,
            project_name=pname,
            name=m.name,
            planned_delivery_date=m.planned_delivery_date,
            days_overdue=(today - m.planned_delivery_date).days,
        )
        for m, pname in overdue_rows
    ]

    # See BUSINESS-RULES.md §7.8 — Top 5 active projects by team size (DISTINCT resources
    # on ACTIVE assignments), for the "Top 5 Projects by Team Size" widget.
    team_size_col = func.count(func.distinct(Assignment.resource_id)).label("team_size")
    top_project_rows = (
        await db.execute(
            select(Project, team_size_col)
            .join(Assignment, Assignment.project_id == Project.id)
            .where(
                Project.status == "ACTIVE",
                Project.is_active == True,  # noqa: E712
                Assignment.status == "ACTIVE",
            )
            .group_by(Project.id)
            .order_by(team_size_col.desc())
            .limit(5)
        )
    ).all()
    top_5_projects_by_team_size = [
        TopProjectByTeamSize(
            project_id=p.id,
            project_name=p.name,
            team_size=team_size,
            dm_name=p.dm.name,
            pm_name=p.pm.name,
        )
        for p, team_size in top_project_rows
    ]

    # See VRIP-128 — company-wide revenue/cost/margin moved to the Company Finance
    # Dashboard (get_company_finance_dashboard); this endpoint no longer aggregates financials.
    bench_summary = await get_bench_summary(db, can_see_cost=True)

    return CompanyDashboardResponse(
        billable_utilization_pct=billable_utilization_pct,
        total_active_resources=total_active_resources,
        bench_count=len(bench_resources_list),
        bench_resources=bench_resources_list,
        shadow_count=len(shadow_resource_ids),
        shadow_total_allocation_pct=shadow_total_pct,
        active_project_count=active_project_count,
        active_projects_by_type=active_projects_by_type,
        top_5_projects_by_team_size=top_5_projects_by_team_size,
        upcoming_releases_30d=upcoming_releases,
        overdue_milestones_count=len(overdue_milestones),
        overdue_milestones=overdue_milestones,
        total_bench_cost_monthly=bench_summary.total_bench_cost_monthly,
    )


async def get_dm_dashboard(
    db: AsyncSession,
    portfolio_project_ids: list | None = None,
    can_see_cost: bool = False,
    can_see_rate: bool = False,
    can_see_nonhuman: bool = False,
    can_see_margin: bool = False,
) -> DMDashboardResponse:
    """See FSD §7.1 — DM portfolio dashboard. Scoped to projects where dm_id = user's resource_id.
    If portfolio_project_ids is None, returns company-wide data (for CEO/CTO)."""

    today = date.today()

    # Get portfolio projects
    if portfolio_project_ids is not None:
        project_filter = Project.id.in_(portfolio_project_ids)
    else:
        project_filter = True  # noqa: E712 — all projects for CEO/CTO

    portfolio_projects = (
        (
            await db.execute(
                select(Project).where(
                    Project.status == "ACTIVE",
                    Project.is_active == True,  # noqa: E712
                    project_filter,
                )
            )
        )
        .scalars()
        .all()
    )
    active_project_count = len(portfolio_projects)
    portfolio_pids = {p.id for p in portfolio_projects}

    # Get ACTIVE assignments on portfolio projects
    if not portfolio_pids:
        return DMDashboardResponse(
            portfolio_utilization_pct=Decimal("0"),
            active_project_count=0,
            resource_count=0,
            bench_count=0,
            upcoming_releases_30d=[],
        )

    portfolio_assignments = (
        (
            await db.execute(
                select(Assignment).where(
                    Assignment.status == "ACTIVE",
                    Assignment.project_id.in_(portfolio_pids),
                )
            )
        )
        .scalars()
        .all()
    )

    # Unique resources on portfolio projects
    portfolio_resource_ids: set[str] = set()
    resource_billable: dict[str, int] = {}
    for a in portfolio_assignments:
        rid = str(a.resource_id)
        portfolio_resource_ids.add(rid)
        if not a.is_shadow:
            resource_billable[rid] = resource_billable.get(rid, 0) + a.billability_pct

    resource_count = len(portfolio_resource_ids)

    # See BUSINESS-RULES.md §7.1 — Portfolio utilization (scoped)
    total_billable = sum(resource_billable.values())
    if resource_count > 0:
        portfolio_utilization_pct = Decimal(
            str(round(total_billable / (resource_count * 100) * 100, 2))
        )
    else:
        portfolio_utilization_pct = Decimal("0")

    # Bench: portfolio resources with 0 ACTIVE assignments globally
    all_past_resource_ids_result = (
        (
            await db.execute(
                select(Assignment.resource_id)
                .where(
                    Assignment.project_id.in_(portfolio_pids),
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )

    # Get globally allocated resource IDs
    globally_allocated = (
        (
            await db.execute(
                select(Assignment.resource_id)
                .where(
                    Assignment.status == "ACTIVE",
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )
    globally_allocated_set = {str(rid) for rid in globally_allocated}

    bench_count = 0
    for rid in all_past_resource_ids_result:
        if str(rid) not in globally_allocated_set:
            # Confirm resource is still active
            res = (
                await db.execute(
                    select(Resource).where(Resource.id == rid, Resource.is_active == True)  # noqa: E712
                )
            ).scalar_one_or_none()
            if res:
                bench_count += 1

    # Upcoming releases within 30 days on portfolio projects
    window_end = today + timedelta(days=30)
    upcoming = (
        (
            await db.execute(
                select(Assignment).where(
                    Assignment.status == "ACTIVE",
                    Assignment.project_id.in_(portfolio_pids),
                    Assignment.end_date.isnot(None),
                    Assignment.end_date >= today,
                    Assignment.end_date <= window_end,
                )
            )
        )
        .scalars()
        .all()
    )

    upcoming_releases: list[UpcomingRelease] = []
    for a in upcoming:
        upcoming_releases.append(
            UpcomingRelease(
                resource_name=a.resource.name,
                project_name=a.project.name,
                end_date=a.end_date,
                days_remaining=(a.end_date - today).days,
            )
        )

    # See FSD §12 — Delivery Delays: milestones past planned_delivery_date on portfolio projects
    overdue_rows = (
        await db.execute(
            select(Milestone, Project.name)
            .join(Project, Milestone.project_id == Project.id)
            .where(
                Milestone.status == "PLANNED",
                Milestone.planned_delivery_date.isnot(None),
                Milestone.planned_delivery_date < today,
                Milestone.is_active == True,  # noqa: E712
                Milestone.project_id.in_(portfolio_pids),
            )
        )
    ).all()
    delivery_delays = [
        OverdueMilestoneItem(
            id=m.id,
            project_id=m.project_id,
            project_name=pname,
            name=m.name,
            planned_delivery_date=m.planned_delivery_date,
            days_overdue=(today - m.planned_delivery_date).days,
        )
        for m, pname in overdue_rows
    ]

    # See BUSINESS-RULES.md §7.2-§7.5 — Portfolio financials
    financials = await get_company_financials(
        db,
        list(portfolio_projects),
        can_see_cost=can_see_cost,
        can_see_rate=can_see_rate,
        can_see_invoicing=False,
        can_see_nonhuman=can_see_nonhuman,
    )

    projected_margin_inr = None
    projected_margin_pct = None
    if can_see_margin:
        projected_margin_inr = financials.total_projected_margin_inr
        projected_margin_pct = financials.total_projected_margin_pct

    return DMDashboardResponse(
        portfolio_utilization_pct=portfolio_utilization_pct,
        active_project_count=active_project_count,
        resource_count=resource_count,
        bench_count=bench_count,
        upcoming_releases_30d=upcoming_releases,
        delivery_delays_count=len(delivery_delays),
        delivery_delays=delivery_delays,
        resource_cost_inr=financials.total_resource_cost_inr,
        non_human_cost_inr=financials.total_non_human_cost_inr,
        total_cost_inr=financials.total_cost_inr,
        projected_revenue_inr=financials.total_projected_revenue_inr,
        projected_margin_inr=projected_margin_inr,
        projected_margin_pct=projected_margin_pct,
    )


async def get_availability(
    db: AsyncSession, window: int = 30, can_see_cost: bool = False
) -> AvailabilityResponse:
    """See API.md — 4 buckets: bench, partial, releasing_soon, fully_allocated.
    Bench cost fields restricted to CEO/CTO/Finance per ACCESS-MATRIX.md."""

    today = date.today()
    working_days = await _get_working_days(db) if can_see_cost else 22

    active_resources = (
        (
            await db.execute(
                select(Resource).where(Resource.is_active == True)  # noqa: E712
            )
        )
        .scalars()
        .all()
    )

    active_assignments = (
        (await db.execute(select(Assignment).where(Assignment.status == "ACTIVE"))).scalars().all()
    )

    # Build per-resource allocation totals and project lists
    resource_alloc: dict[str, int] = {}
    resource_projects: dict[str, list[str]] = {}
    for a in active_assignments:
        rid = str(a.resource_id)
        resource_alloc[rid] = resource_alloc.get(rid, 0) + a.allocation_pct
        resource_projects.setdefault(rid, [])
        if a.project.name not in resource_projects[rid]:
            resource_projects[rid].append(a.project.name)

    bench: list[AvailabilityBenchResource] = []
    partial: list[AvailabilityPartialResource] = []
    fully_allocated: list[AvailabilityFullyAllocated] = []

    for r in active_resources:
        rid = str(r.id)
        total_pct = resource_alloc.get(rid, 0)

        if total_pct == 0:
            # Bench — 0 active assignments
            last_release = (
                await db.execute(
                    select(func.max(Assignment.released_at)).where(
                        Assignment.resource_id == r.id,
                        Assignment.released_at.isnot(None),
                    )
                )
            ).scalar()
            if last_release:
                bench_start = last_release.date() if hasattr(last_release, "date") else last_release
            else:
                bench_start = r.date_of_joining or today
            days_on_bench = max((today - bench_start).days, 0)

            tags_result = (
                (await db.execute(select(ResourceTag.tag).where(ResourceTag.resource_id == r.id)))
                .scalars()
                .all()
            )

            bench_cost_daily: Decimal | None = None
            bench_cost_total: Decimal | None = None
            if can_see_cost and r.loaded_cost_monthly is not None:
                loaded_cost_monthly = Decimal(str(r.loaded_cost_monthly))
                bench_cost_daily = loaded_cost_monthly / Decimal(working_days)
                bench_cost_total = bench_cost_daily * Decimal(days_on_bench)

            bench.append(
                AvailabilityBenchResource(
                    id=r.id,
                    name=r.name,
                    designation=r.designation,
                    technical_expertise=r.technical_expertise,
                    days_on_bench=days_on_bench,
                    tags=list(tags_result),
                    bench_cost_daily=bench_cost_daily,
                    bench_cost_total=bench_cost_total,
                )
            )
        elif total_pct < 100:
            partial.append(
                AvailabilityPartialResource(
                    id=r.id,
                    name=r.name,
                    designation=r.designation,
                    total_allocation_pct=total_pct,
                    spare_capacity_pct=100 - total_pct,
                    projects=resource_projects.get(rid, []),
                )
            )
        else:
            fully_allocated.append(
                AvailabilityFullyAllocated(
                    id=r.id,
                    name=r.name,
                    designation=r.designation,
                    total_allocation_pct=total_pct,
                    projects=resource_projects.get(rid, []),
                )
            )

    # Releasing soon — ACTIVE assignments with end_date within window
    window_end = today + timedelta(days=window)
    upcoming = (
        (
            await db.execute(
                select(Assignment).where(
                    Assignment.status == "ACTIVE",
                    Assignment.end_date.isnot(None),
                    Assignment.end_date >= today,
                    Assignment.end_date <= window_end,
                )
            )
        )
        .scalars()
        .all()
    )

    releasing_soon: list[AvailabilityReleasingSoon] = []
    for a in upcoming:
        releasing_soon.append(
            AvailabilityReleasingSoon(
                resource_id=a.resource_id,
                name=a.resource.name,
                designation=a.resource.designation,
                project_name=a.project.name,
                allocation_pct=a.allocation_pct,
                end_date=a.end_date,
                days_remaining=(a.end_date - today).days,
            )
        )

    total_bench_cost_monthly: Decimal | None = None
    if can_see_cost:
        known_costs = [
            Decimal(str(r.loaded_cost_monthly))
            for r in active_resources
            if str(r.id) not in resource_alloc and r.loaded_cost_monthly is not None
        ]
        if known_costs:
            total_bench_cost_monthly = sum(known_costs, Decimal("0"))

    return AvailabilityResponse(
        bench=bench,
        partial=partial,
        releasing_soon=releasing_soon,
        fully_allocated=fully_allocated,
        can_see_bench_cost=can_see_cost,
        total_bench_cost_monthly=total_bench_cost_monthly,
    )


async def _get_working_days(db: AsyncSession) -> int:
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "system.working_days_per_month")
    )
    config = result.scalar_one_or_none()
    return int(config.value) if config else 22


async def _bench_resources(db: AsyncSession) -> list[Resource]:
    """See BUSINESS-RULES.md §7.6 — bench = active resource with 0 ACTIVE assignments."""

    active_resources = (
        (await db.execute(select(Resource).where(Resource.is_active == True)))  # noqa: E712
        .scalars()
        .all()
    )
    allocated_resource_ids = set(
        (await db.execute(select(Assignment.resource_id).where(Assignment.status == "ACTIVE")))
        .scalars()
        .all()
    )
    return [r for r in active_resources if r.id not in allocated_resource_ids]


async def _bench_start_and_days(
    db: AsyncSession, resource: Resource, today: date
) -> tuple[date, int]:
    last_release = (
        await db.execute(
            select(func.max(Assignment.released_at)).where(
                Assignment.resource_id == resource.id,
                Assignment.released_at.isnot(None),
            )
        )
    ).scalar()
    if last_release:
        bench_start = last_release.date() if hasattr(last_release, "date") else last_release
    else:
        bench_start = resource.date_of_joining or today
    return bench_start, max((today - bench_start).days, 0)


async def get_bench_list(db: AsyncSession, can_see_cost: bool) -> list[BenchListItem]:
    """See modules/10-bench-forecasting/API.md — GET /api/bench."""

    today = date.today()
    working_days = await _get_working_days(db)
    items: list[BenchListItem] = []

    for r in await _bench_resources(db):
        bench_start, days_on_bench = await _bench_start_and_days(db, r, today)
        tags = (
            (await db.execute(select(ResourceTag.tag).where(ResourceTag.resource_id == r.id)))
            .scalars()
            .all()
        )

        loaded_cost_monthly: Decimal | None = None
        daily_bench_cost_inr: Decimal | None = None
        total_bench_cost_inr: Decimal | None = None
        if can_see_cost and r.loaded_cost_monthly is not None:
            loaded_cost_monthly = Decimal(str(r.loaded_cost_monthly))
            daily_bench_cost_inr = loaded_cost_monthly / Decimal(working_days)
            total_bench_cost_inr = daily_bench_cost_inr * Decimal(days_on_bench)

        items.append(
            BenchListItem(
                id=r.id,
                name=r.name,
                designation=r.designation,
                technical_expertise=r.technical_expertise,
                tags=list(tags),
                days_on_bench=days_on_bench,
                bench_start_date=bench_start,
                loaded_cost_monthly=loaded_cost_monthly,
                daily_bench_cost_inr=daily_bench_cost_inr,
                total_bench_cost_inr=total_bench_cost_inr,
            )
        )
    return items


async def get_bench_summary(db: AsyncSession, can_see_cost: bool) -> BenchSummaryResponse:
    """See modules/10-bench-forecasting/API.md — GET /api/bench/summary."""

    bench_list = await get_bench_list(db, can_see_cost=can_see_cost)

    total_bench_cost_monthly: Decimal | None = None
    if can_see_cost:
        known_costs = [
            item.loaded_cost_monthly for item in bench_list if item.loaded_cost_monthly is not None
        ]
        if known_costs:
            total_bench_cost_monthly = sum(known_costs, Decimal("0"))

    average_bench_duration: Decimal | None = None
    if bench_list:
        average_bench_duration = (
            Decimal(sum(item.days_on_bench for item in bench_list)) / Decimal(len(bench_list))
        ).quantize(Decimal("0.01"))

    return BenchSummaryResponse(
        bench_count=len(bench_list),
        total_bench_cost_monthly=total_bench_cost_monthly,
        average_bench_duration=average_bench_duration,
        resources=[
            BenchSummaryResource(name=item.name, days_on_bench=item.days_on_bench)
            for item in bench_list
        ],
    )


async def get_upcoming_availability(
    db: AsyncSession, window: int = 30
) -> list[AvailabilityUpcomingItem]:
    """See modules/10-bench-forecasting/API.md — GET /api/availability/upcoming."""

    today = date.today()
    window_end = today + timedelta(days=window)
    upcoming = (
        (
            await db.execute(
                select(Assignment).where(
                    Assignment.status == "ACTIVE",
                    Assignment.end_date.isnot(None),
                    Assignment.end_date >= today,
                    Assignment.end_date <= window_end,
                )
            )
        )
        .scalars()
        .all()
    )

    return [
        AvailabilityUpcomingItem(
            resource=AvailabilityUpcomingResource(
                id=a.resource.id, name=a.resource.name, designation=a.resource.designation
            ),
            project=AvailabilityUpcomingProject(id=a.project.id, name=a.project.name),
            allocation_pct=a.allocation_pct,
            end_date=a.end_date,
            days_remaining=(a.end_date - today).days,
        )
        for a in upcoming
    ]


async def get_partial_availability(db: AsyncSession) -> list[AvailabilityPartialItem]:
    """See modules/10-bench-forecasting/API.md — GET /api/availability/partial."""

    active_resources = (
        (await db.execute(select(Resource).where(Resource.is_active == True)))  # noqa: E712
        .scalars()
        .all()
    )
    active_assignments = (
        (await db.execute(select(Assignment).where(Assignment.status == "ACTIVE"))).scalars().all()
    )

    resource_alloc: dict[str, int] = {}
    resource_projects: dict[str, dict] = {}
    for a in active_assignments:
        rid = str(a.resource_id)
        resource_alloc[rid] = resource_alloc.get(rid, 0) + a.allocation_pct
        resource_projects.setdefault(rid, {})[a.project.id] = a.project.name

    items: list[AvailabilityPartialItem] = []
    for r in active_resources:
        rid = str(r.id)
        total_pct = resource_alloc.get(rid, 0)
        if 0 < total_pct < 100:
            items.append(
                AvailabilityPartialItem(
                    id=r.id,
                    name=r.name,
                    designation=r.designation,
                    total_allocation_pct=total_pct,
                    spare_capacity_pct=100 - total_pct,
                    projects=[
                        AvailabilityPartialProject(id=pid, name=pname)
                        for pid, pname in resource_projects.get(rid, {}).items()
                    ],
                )
            )
    return items
