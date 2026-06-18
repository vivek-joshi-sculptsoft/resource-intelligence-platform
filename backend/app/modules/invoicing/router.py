"""See FSD §2.8 — Milestone API endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.invoicing.schemas import (
    MilestoneCreateRequest,
    MilestoneStatusRequest,
    MilestoneUpdateRequest,
)
from app.modules.invoicing.service import (
    create_milestone,
    get_milestone,
    list_milestones,
    transition_milestone_status,
    update_milestone,
)
from app.modules.projects.service import get_project
from app.shared.access_control import check_access
from app.shared.exceptions import ForbiddenError

router = APIRouter(tags=["invoicing"])

DATA_TYPE = "milestones"


def _check_portfolio_scope(project, permission, current_user: User) -> None:
    """See FSD §10 — OWN_PORTFOLIO means dm_id or pm_id = user's resource_id."""
    if not permission.is_own_portfolio:
        return
    if current_user.resource_id and (
        project.dm_id == current_user.resource_id or project.pm_id == current_user.resource_id
    ):
        return
    raise ForbiddenError()


@router.get("/api/v1/projects/{project_id}/milestones")
async def list_milestones_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await list_milestones(db, project_id)
    return {"data": data}


@router.post("/api/v1/projects/{project_id}/milestones", status_code=201)
async def create_milestone_endpoint(
    project_id: uuid.UUID,
    body: MilestoneCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await create_milestone(
        db,
        project_id=project_id,
        current_user_id=current_user.id,
        name=body.name,
        amount=body.amount,
        planned_delivery_date=body.planned_delivery_date,
        sort_order=body.sort_order,
    )
    return {"data": data}


@router.get("/api/v1/projects/{project_id}/milestones/{milestone_id}")
async def get_milestone_endpoint(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await get_milestone(db, milestone_id, project_id)
    return {"data": data}


@router.put("/api/v1/projects/{project_id}/milestones/{milestone_id}")
async def update_milestone_endpoint(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    body: MilestoneUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    fields = body.model_dump(exclude_unset=True)
    data = await update_milestone(
        db,
        milestone_id=milestone_id,
        project_id=project_id,
        current_user_id=current_user.id,
        **fields,
    )
    return {"data": data}


@router.put("/api/v1/projects/{project_id}/milestones/{milestone_id}/status")
async def transition_milestone_status_endpoint(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    body: MilestoneStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await transition_milestone_status(
        db,
        milestone_id=milestone_id,
        project_id=project_id,
        current_user_id=current_user.id,
        role_code=current_user.role.code,
        new_status=body.status,
    )
    return {"data": data}
