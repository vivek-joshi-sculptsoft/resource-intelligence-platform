import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.shared.access_control import Permission
from app.shared.exceptions import AppError, NotFoundError, ValidationError

VALID_TYPES = {"FIXED_PRICE", "TIME_AND_MATERIAL", "CLIENT_ONBOARDING"}
VALID_STATUSES = {"ACTIVE", "COMPLETED", "ON_HOLD", "CANCELLED"}
# See FSD §6.4 — contract_end_date required for these types
END_DATE_REQUIRED_TYPES = {"TIME_AND_MATERIAL", "CLIENT_ONBOARDING"}

# See FSD §6.4 — valid status transitions
VALID_TRANSITIONS: dict[str, set[str]] = {
    "ACTIVE": {"COMPLETED", "ON_HOLD", "CANCELLED"},
    "ON_HOLD": {"ACTIVE", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


async def _validate_client(db: AsyncSession, client_id: uuid.UUID) -> None:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise NotFoundError("Client", str(client_id))
    if not client.is_active:
        raise ValidationError("Client is not active", field="client_id")


async def _validate_resource(db: AsyncSession, resource_id: uuid.UUID, field_name: str) -> None:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if resource is None:
        raise NotFoundError("Resource", str(resource_id))
    if not resource.is_active:
        raise ValidationError(f"Resource for {field_name} is not active", field=field_name)


def _validate_type_end_date(project_type: str, contract_end_date: Any) -> None:
    # See FSD §6.4 — contract_end_date required for T&M and CLIENT_ONBOARDING
    if project_type in END_DATE_REQUIRED_TYPES and contract_end_date is None:
        raise ValidationError(
            f"contract_end_date is required for {project_type} projects",
            field="contract_end_date",
        )


async def _load_project(db: AsyncSession, project_id: uuid.UUID) -> Project:
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.client),
            selectinload(Project.dm),
            selectinload(Project.pm),
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", str(project_id))
    return project


def _project_to_list_item(p: Project) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "client_name": p.client.name if p.client else "",
        "type": p.type,
        "status": p.status,
        "billing_currency": p.billing_currency,
        "dm_name": p.dm.name if p.dm else "",
        "pm_name": p.pm.name if p.pm else "",
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "contract_end_date": p.contract_end_date.isoformat() if p.contract_end_date else None,
    }


def _project_to_detail(p: Project) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "client": {"id": p.client.id, "name": p.client.name} if p.client else None,
        "type": p.type,
        "status": p.status,
        "billing_currency": p.billing_currency,
        "contract_value": None,  # Phase 2
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "contract_end_date": p.contract_end_date.isoformat() if p.contract_end_date else None,
        "dm": {"id": p.dm.id, "name": p.dm.name} if p.dm else None,
        "pm": {"id": p.pm.id, "name": p.pm.name} if p.pm else None,
        "worklog_enabled": p.worklog_enabled,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


async def list_projects(
    db: AsyncSession,
    permission: Permission,
    current_user: User,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    client_id: uuid.UUID | None = None,
    project_type: str | None = None,
    dm_id: uuid.UUID | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    query = select(Project).options(
        selectinload(Project.client),
        selectinload(Project.dm),
        selectinload(Project.pm),
    )
    count_query = select(func.count()).select_from(Project)

    # See FSD §10 — Scope filtering via WHERE clause
    if permission.is_own_portfolio and current_user.resource_id:
        scope_filter = (Project.dm_id == current_user.resource_id) | (
            Project.pm_id == current_user.resource_id
        )
        query = query.where(scope_filter)
        count_query = count_query.where(scope_filter)

    if status:
        query = query.where(Project.status == status)
        count_query = count_query.where(Project.status == status)

    if client_id:
        query = query.where(Project.client_id == client_id)
        count_query = count_query.where(Project.client_id == client_id)

    if project_type:
        query = query.where(Project.type == project_type)
        count_query = count_query.where(Project.type == project_type)

    if dm_id:
        query = query.where(Project.dm_id == dm_id)
        count_query = count_query.where(Project.dm_id == dm_id)

    if search:
        like = f"%{search}%"
        query = query.where(Project.name.ilike(like))
        count_query = count_query.where(Project.name.ilike(like))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Project.name.asc()).offset(offset).limit(limit)
    result = await db.execute(query)
    projects = list(result.scalars().all())

    return [_project_to_list_item(p) for p in projects], total


async def create_project(
    db: AsyncSession,
    name: str,
    client_id: uuid.UUID,
    project_type: str,
    dm_id: uuid.UUID,
    pm_id: uuid.UUID,
    billing_currency: str = "INR",
    start_date: Any = None,
    contract_end_date: Any = None,
    worklog_enabled: bool = False,
    notes: str | None = None,
    current_user_id: uuid.UUID | None = None,
) -> Project:
    if project_type not in VALID_TYPES:
        raise ValidationError(f"Invalid project type: {project_type}", field="type")

    _validate_type_end_date(project_type, contract_end_date)

    await _validate_client(db, client_id)
    await _validate_resource(db, dm_id, "dm_id")
    await _validate_resource(db, pm_id, "pm_id")

    project = Project(
        id=uuid.uuid4(),
        name=name,
        client_id=client_id,
        type=project_type,
        billing_currency=billing_currency,
        start_date=start_date,
        contract_end_date=contract_end_date,
        dm_id=dm_id,
        pm_id=pm_id,
        worklog_enabled=worklog_enabled,
        notes=notes,
    )
    db.add(project)
    await db.flush()

    await audit_log(
        db,
        entity_type="project",
        entity_id=project.id,
        action=AuditAction.CREATE,
        changes={
            "name": name,
            "client_id": str(client_id),
            "type": project_type,
            "dm_id": str(dm_id),
            "pm_id": str(pm_id),
        },
        user_id=current_user_id or uuid.UUID(int=0),
    )

    return await _load_project(db, project.id)


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project:
    return await _load_project(db, project_id)


async def update_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    **fields: Any,
) -> Project:
    project = await _load_project(db, project_id)
    changes: dict[str, tuple] = {}

    if "client_id" in fields and fields["client_id"] is not None:
        await _validate_client(db, fields["client_id"])

    if "dm_id" in fields and fields["dm_id"] is not None:
        await _validate_resource(db, fields["dm_id"], "dm_id")

    if "pm_id" in fields and fields["pm_id"] is not None:
        await _validate_resource(db, fields["pm_id"], "pm_id")

    new_type = fields.get("type", project.type)
    new_end_date = fields.get("contract_end_date", project.contract_end_date)
    if "type" in fields or "contract_end_date" in fields:
        _validate_type_end_date(new_type, new_end_date)

    for field_name, new_val in fields.items():
        old_val = getattr(project, field_name, None)
        if str(old_val) != str(new_val):
            changes[field_name] = (old_val, new_val)
            setattr(project, field_name, new_val)

    if changes:
        await audit_log(
            db,
            entity_type="project",
            entity_id=project.id,
            action=AuditAction.UPDATE,
            changes=changes,
            user_id=current_user_id,
        )

    await db.flush()
    return await _load_project(db, project.id)


async def transition_project_status(
    db: AsyncSession,
    project_id: uuid.UUID,
    new_status: str,
    current_user_id: uuid.UUID,
) -> Project:
    """See FSD §6.4 — Project status transitions with auto-release on terminal states."""
    project = await _load_project(db, project_id)
    old_status = project.status

    if new_status not in VALID_STATUSES:
        raise ValidationError(f"Invalid status: {new_status}", field="status")

    allowed = VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise AppError(
            f"Cannot transition from {old_status} to {new_status}",
            status_code=400,
            field="status",
        )

    project.status = new_status

    await audit_log(
        db,
        entity_type="project",
        entity_id=project.id,
        action=AuditAction.UPDATE,
        changes={"status": (old_status, new_status)},
        user_id=current_user_id,
    )

    # See FSD §8 — COMPLETED/CANCELLED auto-releases all ACTIVE assignments
    if new_status in {"COMPLETED", "CANCELLED"}:
        await _auto_release_assignments(db, project_id, current_user_id)

    await db.flush()
    return await _load_project(db, project.id)


async def _auto_release_assignments(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    try:
        from app.modules.allocations.models import Assignment
    except (ImportError, Exception):
        return

    result = await db.execute(
        select(Assignment).where(
            Assignment.project_id == project_id,
            Assignment.status == "ACTIVE",
        )
    )
    assignments = list(result.scalars().all())
    now = datetime.now(UTC)

    for assignment in assignments:
        old_status = assignment.status
        assignment.status = "RELEASED"
        assignment.released_at = now

        await audit_log(
            db,
            entity_type="assignment",
            entity_id=assignment.id,
            action=AuditAction.UPDATE,
            changes={
                "status": (old_status, "RELEASED"),
                "released_at": (None, now.isoformat()),
            },
            user_id=user_id,
        )
