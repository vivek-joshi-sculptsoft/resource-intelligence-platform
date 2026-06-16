"""See FSD §2.10 — NonHumanCost API endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.nonhuman_costs.schemas import NonHumanCostCreateRequest, NonHumanCostUpdateRequest
from app.modules.nonhuman_costs.service import (
    create_cost,
    delete_cost,
    get_cost,
    get_cost_summary,
    list_costs,
    update_cost,
)
from app.modules.projects.service import get_project
from app.shared.access_control import check_access
from app.shared.exceptions import ForbiddenError

router = APIRouter(tags=["non-human-costs"])

DATA_TYPE = "non_human_costs"


def _check_portfolio_scope(project, permission, current_user: User) -> None:
    """See FSD §10 — OWN_PORTFOLIO means dm_id or pm_id = user's resource_id."""
    if not permission.is_own_portfolio:
        return
    if current_user.resource_id and (
        project.dm_id == current_user.resource_id or project.pm_id == current_user.resource_id
    ):
        return
    raise ForbiddenError()


@router.get("/api/v1/projects/{project_id}/costs")
async def list_costs_endpoint(
    project_id: uuid.UUID,
    category: str | None = Query(None),
    is_recurring: bool | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    return await list_costs(
        db,
        project_id,
        category=category,
        is_recurring=is_recurring,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )


@router.post("/api/v1/projects/{project_id}/costs", status_code=201)
async def create_cost_endpoint(
    project_id: uuid.UUID,
    body: NonHumanCostCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await create_cost(
        db,
        project_id=project_id,
        current_user_id=current_user.id,
        description=body.description,
        category=body.category.value,
        amount=body.amount,
        currency=body.currency,
        exchange_rate=body.exchange_rate,
        cost_date=body.cost_date,
        is_recurring=body.is_recurring,
        recurring_end_date=body.recurring_end_date,
    )
    return {"data": data}


@router.get("/api/v1/projects/{project_id}/costs/summary")
async def cost_summary_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    return await get_cost_summary(db, project_id)


@router.get("/api/v1/projects/{project_id}/costs/{cost_id}")
async def get_cost_endpoint(
    project_id: uuid.UUID,
    cost_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await get_cost(db, cost_id, project_id)
    return {"data": data}


@router.put("/api/v1/projects/{project_id}/costs/{cost_id}")
async def update_cost_endpoint(
    project_id: uuid.UUID,
    cost_id: uuid.UUID,
    body: NonHumanCostUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    fields = body.model_dump(exclude_unset=True)
    if "category" in fields and fields["category"] is not None:
        fields["category"] = fields["category"].value

    data = await update_cost(
        db,
        cost_id=cost_id,
        project_id=project_id,
        current_user_id=current_user.id,
        **fields,
    )
    return {"data": data}


@router.delete("/api/v1/projects/{project_id}/costs/{cost_id}")
async def delete_cost_endpoint(
    project_id: uuid.UUID,
    cost_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    await delete_cost(db, cost_id, project_id, current_user.id)
    return {"success": True}
