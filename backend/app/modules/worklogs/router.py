"""See FSD §2.11 — Worklog API endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.modules.worklogs.schemas import WorklogCreateRequest, WorklogUpdateRequest
from app.modules.worklogs.service import (
    create_worklog,
    delete_worklog,
    list_all_worklogs,
    list_my_worklogs,
    list_project_worklogs,
    list_resource_worklogs,
    update_worklog,
)
from app.shared.access_control import check_access
from app.shared.exceptions import ForbiddenError, NotFoundError

router = APIRouter(tags=["worklogs"])


def _require_resource_id(user: User) -> uuid.UUID:
    if not user.resource_id:
        raise ForbiddenError("User has no linked resource profile")
    return user.resource_id


@router.get("/api/v1/worklogs/my")
async def get_my_worklogs(
    project_id: uuid.UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    resource_id = _require_resource_id(current_user)
    items, total = await list_my_worklogs(
        db, resource_id, project_id, start_date, end_date, page, limit
    )
    return {
        "data": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/api/v1/worklogs")
async def list_worklogs_endpoint(
    project_id: uuid.UUID | None = Query(None),
    resource_id: uuid.UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "worklogs")
    items, total = await list_all_worklogs(
        db,
        permission,
        current_user.resource_id,
        project_id,
        resource_id,
        start_date,
        end_date,
        page,
        limit,
    )
    return {
        "data": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/api/v1/worklogs", status_code=201)
async def create_worklog_endpoint(
    body: WorklogCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "worklogs", require_edit=True)
    resource_id = _require_resource_id(current_user)
    result = await create_worklog(db, resource_id, body)
    return {"data": result.model_dump()}


@router.put("/api/v1/worklogs/{worklog_id}")
async def update_worklog_endpoint(
    worklog_id: uuid.UUID,
    body: WorklogUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "worklogs", require_edit=True)
    resource_id = _require_resource_id(current_user)
    result = await update_worklog(db, worklog_id, resource_id, body)
    return {"data": result.model_dump()}


@router.delete("/api/v1/worklogs/{worklog_id}")
async def delete_worklog_endpoint(
    worklog_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "worklogs", require_edit=True)
    resource_id = _require_resource_id(current_user)
    await delete_worklog(db, worklog_id, resource_id)
    return {"success": True}


@router.get("/api/v1/projects/{project_id}/worklogs")
async def get_project_worklogs(
    project_id: uuid.UUID,
    resource_id: uuid.UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "worklogs")

    # SELF_ONLY scope can't view project-level aggregated worklogs
    if permission.is_self_only:
        raise ForbiddenError()

    project = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", str(project_id))

    # See FSD §10 — OWN_PORTFOLIO: DM/PM sees only projects where they are dm or pm
    if permission.is_own_portfolio:
        if not current_user.resource_id:
            raise ForbiddenError()
        if project.dm_id != current_user.resource_id and project.pm_id != current_user.resource_id:
            raise ForbiddenError()

    items, total = await list_project_worklogs(
        db, project_id, resource_id, start_date, end_date, page, limit
    )
    return {
        "data": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/api/v1/resources/{resource_id}/worklogs")
async def get_resource_worklogs(
    resource_id: uuid.UUID,
    project_id: uuid.UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "worklogs")

    target = (
        await db.execute(select(Resource).where(Resource.id == resource_id))
    ).scalar_one_or_none()
    if not target:
        raise NotFoundError("Resource", str(resource_id))

    # See FSD §10 — SELF_ONLY: Engineer can only see own worklogs
    if permission.is_self_only and current_user.resource_id != resource_id:
        raise ForbiddenError()

    # See FSD §10 — OWN_PORTFOLIO: DM/PM sees only resources on their projects
    if permission.is_own_portfolio:
        if not current_user.resource_id:
            raise ForbiddenError()
        from app.modules.allocations.models import Assignment

        has_overlap = (
            await db.execute(
                select(Assignment.id)
                .join(Project)
                .where(
                    Assignment.resource_id == resource_id,
                    (Project.dm_id == current_user.resource_id)
                    | (Project.pm_id == current_user.resource_id),
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if not has_overlap:
            raise ForbiddenError()

    items, total = await list_resource_worklogs(
        db, resource_id, project_id, start_date, end_date, page, limit
    )
    return {
        "data": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }
