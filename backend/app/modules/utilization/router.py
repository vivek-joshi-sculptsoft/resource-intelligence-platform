"""See FSD §7.1 — Utilization dashboard endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.projects.models import Project
from app.modules.utilization.service import (
    get_availability,
    get_bench_list,
    get_bench_summary,
    get_company_dashboard,
    get_dm_dashboard,
    get_partial_availability,
    get_upcoming_availability,
)
from app.shared.access_control import can_see_field
from app.shared.exceptions import ForbiddenError

router = APIRouter(tags=["dashboard"])


@router.get("/api/v1/dashboard/company")
async def company_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — CEO, CTO only
    if current_user.role.code not in {"CEO", "CTO"}:
        raise ForbiddenError()

    data = await get_company_dashboard(db)
    return {"data": data.model_dump()}


@router.get("/api/v1/dashboard/dm")
async def dm_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — DM (OWN_PORTFOLIO), CEO, CTO
    role_code = current_user.role.code
    if role_code not in {"CEO", "CTO", "DM"}:
        raise ForbiddenError()

    # See FSD §10 — OWN_PORTFOLIO: DM sees only projects where dm_id = own resource_id
    portfolio_project_ids = None
    if role_code == "DM":
        if not current_user.resource_id:
            raise ForbiddenError("DM user has no linked resource profile")
        rows = (
            (
                await db.execute(
                    select(Project.id).where(
                        Project.dm_id == current_user.resource_id,
                        Project.status == "ACTIVE",
                        Project.is_active == True,  # noqa: E712
                    )
                )
            )
            .scalars()
            .all()
        )
        portfolio_project_ids = list(rows)

    data = await get_dm_dashboard(db, portfolio_project_ids)
    return {"data": data.model_dump()}


@router.get("/api/v1/dashboard/availability")
async def availability_dashboard(
    window: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — All authenticated roles including Engineer
    data = await get_availability(db, window=window)
    return {"data": data.model_dump()}


@router.get("/api/v1/bench")
async def bench_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — bench_data: all roles; cost fields restricted to CEO/CTO/Finance
    can_see_cost = can_see_field(current_user.role.code, "loaded_cost_monthly")
    data = await get_bench_list(db, can_see_cost=can_see_cost)
    return {"data": [item.model_dump() for item in data]}


@router.get("/api/v1/bench/summary")
async def bench_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — bench_data: all roles; cost fields restricted to CEO/CTO/Finance
    can_see_cost = can_see_field(current_user.role.code, "loaded_cost_monthly")
    data = await get_bench_summary(db, can_see_cost=can_see_cost)
    return {"data": data.model_dump()}


@router.get("/api/v1/availability/upcoming")
async def availability_upcoming(
    window: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — All authenticated roles including Engineer
    data = await get_upcoming_availability(db, window=window)
    return {"data": [item.model_dump() for item in data]}


@router.get("/api/v1/availability/partial")
async def availability_partial(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — All authenticated roles including Engineer
    data = await get_partial_availability(db)
    return {"data": [item.model_dump() for item in data]}
