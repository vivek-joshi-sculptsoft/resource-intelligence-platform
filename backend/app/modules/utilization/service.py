"""See FSD §7.1 — Company utilization dashboard service."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.projects.models import Project
from app.modules.resources.models import Resource, ResourceTag
from app.modules.utilization.schemas import (
    AvailabilityBenchResource,
    AvailabilityFullyAllocated,
    AvailabilityPartialResource,
    AvailabilityReleasingSoon,
    AvailabilityResponse,
    BenchResource,
    CompanyDashboardResponse,
    DMDashboardResponse,
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

    return CompanyDashboardResponse(
        billable_utilization_pct=billable_utilization_pct,
        total_active_resources=total_active_resources,
        bench_count=len(bench_resources_list),
        bench_resources=bench_resources_list,
        shadow_count=len(shadow_resource_ids),
        shadow_total_allocation_pct=shadow_total_pct,
        active_project_count=active_project_count,
        active_projects_by_type=active_projects_by_type,
        upcoming_releases_30d=upcoming_releases,
    )


async def get_dm_dashboard(
    db: AsyncSession, portfolio_project_ids: list | None = None
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

    return DMDashboardResponse(
        portfolio_utilization_pct=portfolio_utilization_pct,
        active_project_count=active_project_count,
        resource_count=resource_count,
        bench_count=bench_count,
        upcoming_releases_30d=upcoming_releases,
    )


async def get_availability(db: AsyncSession, window: int = 30) -> AvailabilityResponse:
    """See API.md — 4 buckets: bench, partial, releasing_soon, fully_allocated."""

    today = date.today()

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

            bench.append(
                AvailabilityBenchResource(
                    id=r.id,
                    name=r.name,
                    designation=r.designation,
                    technical_expertise=r.technical_expertise,
                    days_on_bench=days_on_bench,
                    tags=list(tags_result),
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

    return AvailabilityResponse(
        bench=bench,
        partial=partial,
        releasing_soon=releasing_soon,
        fully_allocated=fully_allocated,
    )
