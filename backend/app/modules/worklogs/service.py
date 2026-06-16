"""See FSD §2.11 — Worklog business logic and validations."""

import uuid
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.projects.models import Project
from app.modules.worklogs.models import Worklog
from app.modules.worklogs.schemas import (
    ProjectRef,
    ResourceRef,
    WorklogCreateRequest,
    WorklogResponse,
    WorklogUpdateRequest,
)
from app.shared.access_control import Permission
from app.shared.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError


def _to_response(w: Worklog) -> WorklogResponse:
    return WorklogResponse(
        id=w.id,
        project=ProjectRef(id=w.project.id, name=w.project.name),
        resource=ResourceRef(id=w.resource.id, name=w.resource.name),
        log_date=w.log_date,
        hours=w.hours,
        note=w.note,
        created_at=w.created_at.isoformat() if w.created_at else "",
    )


async def list_my_worklogs(
    db: AsyncSession,
    resource_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[WorklogResponse], int]:
    query = select(Worklog).where(Worklog.resource_id == resource_id)

    if project_id:
        query = query.where(Worklog.project_id == project_id)
    if start_date:
        query = query.where(Worklog.log_date >= start_date)
    if end_date:
        query = query.where(Worklog.log_date <= end_date)

    from sqlalchemy import func

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Worklog.log_date.desc(), Worklog.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    rows = (await db.execute(query)).scalars().all()
    return [_to_response(w) for w in rows], total


async def create_worklog(
    db: AsyncSession,
    resource_id: uuid.UUID,
    body: WorklogCreateRequest,
) -> WorklogResponse:
    # Validation 3: no future dates
    if body.log_date > date.today():
        raise AppError("Cannot log hours for a future date", status_code=422, field="log_date")

    # Validation 1: project worklog_enabled
    project = (
        await db.execute(select(Project).where(Project.id == body.project_id))
    ).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", str(body.project_id))
    if not project.worklog_enabled:
        raise AppError(
            "Worklog is not enabled for this project", status_code=422, field="project_id"
        )

    # Validation 2: active assignment covering log_date
    assignment = (
        await db.execute(
            select(Assignment).where(
                Assignment.resource_id == resource_id,
                Assignment.project_id == body.project_id,
                Assignment.status == "ACTIVE",
                Assignment.start_date <= body.log_date,
                and_(Assignment.end_date.is_(None) | (Assignment.end_date >= body.log_date)),
            )
        )
    ).scalar_one_or_none()
    if not assignment:
        raise AppError(
            "No active assignment found covering this date",
            status_code=422,
            field="log_date",
        )

    # Validation 5: unique per resource+project+day
    existing = (
        await db.execute(
            select(Worklog).where(
                Worklog.resource_id == resource_id,
                Worklog.project_id == body.project_id,
                Worklog.log_date == body.log_date,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError(
            "Worklog entry already exists for this project and date", field="log_date"
        )

    worklog = Worklog(
        id=uuid.uuid4(),
        resource_id=resource_id,
        project_id=body.project_id,
        log_date=body.log_date,
        hours=body.hours,
        note=body.note,
    )
    db.add(worklog)
    await db.flush()

    refreshed = (await db.execute(select(Worklog).where(Worklog.id == worklog.id))).scalar_one()
    return _to_response(refreshed)


async def update_worklog(
    db: AsyncSession,
    worklog_id: uuid.UUID,
    resource_id: uuid.UUID,
    body: WorklogUpdateRequest,
) -> WorklogResponse:
    worklog = (
        await db.execute(select(Worklog).where(Worklog.id == worklog_id))
    ).scalar_one_or_none()
    if not worklog:
        raise NotFoundError("Worklog", str(worklog_id))
    if worklog.resource_id != resource_id:
        raise ForbiddenError("You can only update your own worklog entries")

    if body.hours is not None:
        worklog.hours = body.hours
    if body.note is not None:
        worklog.note = body.note

    await db.flush()
    return _to_response(worklog)


async def delete_worklog(
    db: AsyncSession,
    worklog_id: uuid.UUID,
    resource_id: uuid.UUID,
) -> None:
    worklog = (
        await db.execute(select(Worklog).where(Worklog.id == worklog_id))
    ).scalar_one_or_none()
    if not worklog:
        raise NotFoundError("Worklog", str(worklog_id))
    if worklog.resource_id != resource_id:
        raise ForbiddenError("You can only delete your own worklog entries")

    await db.delete(worklog)
    await db.flush()


async def list_project_worklogs(
    db: AsyncSession,
    project_id: uuid.UUID,
    resource_id_filter: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[WorklogResponse], int]:
    query = select(Worklog).where(Worklog.project_id == project_id)

    if resource_id_filter:
        query = query.where(Worklog.resource_id == resource_id_filter)
    if start_date:
        query = query.where(Worklog.log_date >= start_date)
    if end_date:
        query = query.where(Worklog.log_date <= end_date)

    from sqlalchemy import func

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Worklog.log_date.desc(), Worklog.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    rows = (await db.execute(query)).scalars().all()
    return [_to_response(w) for w in rows], total


async def list_all_worklogs(
    db: AsyncSession,
    permission: Permission,
    current_user_resource_id: uuid.UUID | None,
    project_id_filter: uuid.UUID | None = None,
    resource_id_filter: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[WorklogResponse], int]:
    """See FSD §10 — scope-filtered worklog listing for managers."""

    query = select(Worklog)

    if permission.is_own_portfolio and current_user_resource_id:
        query = query.join(Project).where(
            (Project.dm_id == current_user_resource_id)
            | (Project.pm_id == current_user_resource_id)
        )
    elif permission.is_self_only and current_user_resource_id:
        query = query.where(Worklog.resource_id == current_user_resource_id)

    if project_id_filter:
        query = query.where(Worklog.project_id == project_id_filter)
    if resource_id_filter:
        query = query.where(Worklog.resource_id == resource_id_filter)
    if start_date:
        query = query.where(Worklog.log_date >= start_date)
    if end_date:
        query = query.where(Worklog.log_date <= end_date)

    from sqlalchemy import func

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Worklog.log_date.desc(), Worklog.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    rows = (await db.execute(query)).scalars().all()
    return [_to_response(w) for w in rows], total


async def list_resource_worklogs(
    db: AsyncSession,
    target_resource_id: uuid.UUID,
    project_id_filter: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[WorklogResponse], int]:
    query = select(Worklog).where(Worklog.resource_id == target_resource_id)

    if project_id_filter:
        query = query.where(Worklog.project_id == project_id_filter)
    if start_date:
        query = query.where(Worklog.log_date >= start_date)
    if end_date:
        query = query.where(Worklog.log_date <= end_date)

    from sqlalchemy import func

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Worklog.log_date.desc(), Worklog.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    rows = (await db.execute(query)).scalars().all()
    return [_to_response(w) for w in rows], total
