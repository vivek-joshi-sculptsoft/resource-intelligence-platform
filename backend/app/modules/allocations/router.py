"""See FSD §2.7 — Assignment API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.allocations.schemas import AssignmentCreateRequest, AssignmentUpdateRequest
from app.modules.allocations.jobs import run_auto_release
from app.modules.allocations.service import (
    create_assignment,
    get_assignment,
    list_project_assignments,
    list_resource_assignments,
    release_assignment,
    update_assignment,
)
from app.modules.auth.models import User
from app.modules.projects.service import get_project
from app.shared.access_control import check_access
from app.shared.exceptions import ForbiddenError

router = APIRouter(tags=["assignments"])


def _check_portfolio_scope_for_project(project, permission, current_user: User) -> None:
    """See FSD §10 — OWN_PORTFOLIO means dm_id or pm_id = user's resource_id."""
    if not permission.is_own_portfolio:
        return
    if current_user.resource_id and (
        project.dm_id == current_user.resource_id
        or project.pm_id == current_user.resource_id
    ):
        return
    raise ForbiddenError()


@router.get("/api/v1/projects/{project_id}/assignments")
async def list_project_assignments_endpoint(
    project_id: uuid.UUID,
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "allocation")
    project = await get_project(db, project_id)
    _check_portfolio_scope_for_project(project, permission, current_user)

    items = await list_project_assignments(db, project_id, permission, current_user, status)
    return {"data": items}


@router.post("/api/v1/projects/{project_id}/assignments", status_code=201)
async def create_assignment_endpoint(
    project_id: uuid.UUID,
    body: AssignmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "allocation", require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope_for_project(project, permission, current_user)

    data, warnings = await create_assignment(
        db,
        project_id=project_id,
        resource_id=body.resource_id,
        allocation_pct=body.allocation_pct,
        billability_pct=body.billability_pct,
        is_shadow=body.is_shadow,
        start_date=body.start_date,
        end_date=body.end_date,
        project_designation=body.project_designation,
        project_expertise=body.project_expertise,
        current_user_id=current_user.id,
        role_code=current_user.role.code,
    )
    result: dict = {"data": data}
    if warnings:
        result["warnings"] = warnings
    return result


@router.get("/api/v1/assignments/{assignment_id}")
async def get_assignment_endpoint(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "allocation")
    data = await get_assignment(db, assignment_id, role_code=current_user.role.code)

    # See FSD §10 — SELF_ONLY: engineer can only see own assignments
    if permission.is_self_only:
        if not current_user.resource_id or str(data.get("resource", {}).get("id")) != str(current_user.resource_id):
            raise ForbiddenError()

    if permission.is_own_portfolio:
        project = await get_project(db, data["project_id"])
        _check_portfolio_scope_for_project(project, permission, current_user)

    return {"data": data}


@router.put("/api/v1/assignments/{assignment_id}")
async def update_assignment_endpoint(
    assignment_id: uuid.UUID,
    body: AssignmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "allocation", require_edit=True)

    existing = await get_assignment(db, assignment_id)
    if permission.is_own_portfolio:
        project = await get_project(db, existing["project_id"])
        _check_portfolio_scope_for_project(project, permission, current_user)

    fields = body.model_dump(exclude_unset=True)
    data, warnings = await update_assignment(
        db,
        assignment_id=assignment_id,
        current_user_id=current_user.id,
        role_code=current_user.role.code,
        **fields,
    )
    result: dict = {"data": data}
    if warnings:
        result["warnings"] = warnings
    return result


@router.post("/api/v1/assignments/{assignment_id}/release")
async def release_assignment_endpoint(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "allocation", require_edit=True)

    existing = await get_assignment(db, assignment_id)
    if permission.is_own_portfolio:
        project = await get_project(db, existing["project_id"])
        _check_portfolio_scope_for_project(project, permission, current_user)

    data = await release_assignment(
        db,
        assignment_id=assignment_id,
        current_user_id=current_user.id,
        role_code=current_user.role.code,
    )
    return {"data": data}


@router.get("/api/v1/resources/{resource_id}/assignments")
async def list_resource_assignments_endpoint(
    resource_id: uuid.UUID,
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "allocation")

    # See FSD §10 — SELF_ONLY: engineer can only see own assignments
    if permission.is_self_only:
        if not current_user.resource_id or resource_id != current_user.resource_id:
            raise ForbiddenError()

    items = await list_resource_assignments(db, resource_id, permission, current_user, status)
    return {"data": items}


@router.post("/api/v1/jobs/auto-release")
async def trigger_auto_release(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """See FSD §8 — Manual trigger for auto-release job. Admin (CEO/CTO) only."""
    role_code = current_user.role.code
    if role_code not in {"CEO", "CTO"}:
        raise ForbiddenError()

    released = await run_auto_release(db)
    return {"released_count": len(released), "assignments": released}
