"""See FSD §2.7, §6.1, §8, §11 — Assignment CRUD with 7 validations."""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.allocations.models import Assignment
from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.auth.models import User
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.shared.access_control import Permission, can_see_field
from app.shared.exceptions import NotFoundError, ValidationError


def _validate_assignment_rules(
    allocation_pct: int,
    billability_pct: int,
    is_shadow: bool,
    start_date: date,
    end_date: date | None,
) -> None:
    # See FSD §11 — 7 assignment validations
    # (1) allocation_pct 1-100: enforced by Pydantic
    # (2) billability_pct 0-100: enforced by Pydantic
    # (3) billability <= allocation
    if billability_pct > allocation_pct:
        raise ValidationError(
            "billability_pct cannot exceed allocation_pct",
            field="billability_pct",
        )
    # (4) shadow → billability must be 0
    if is_shadow and billability_pct != 0:
        raise ValidationError(
            "Shadow assignments must have billability_pct = 0",
            field="billability_pct",
        )
    # (5) end_date after start_date
    if end_date is not None and end_date <= start_date:
        raise ValidationError(
            "end_date must be after start_date",
            field="end_date",
        )


async def _check_duplicate_active(
    db: AsyncSession,
    resource_id: uuid.UUID,
    project_id: uuid.UUID,
    exclude_id: uuid.UUID | None = None,
) -> None:
    # (6) one ACTIVE per (resource, project)
    query = select(Assignment).where(
        Assignment.resource_id == resource_id,
        Assignment.project_id == project_id,
        Assignment.status == "ACTIVE",
    )
    if exclude_id:
        query = query.where(Assignment.id != exclude_id)
    result = await db.execute(query)
    if result.scalar_one_or_none() is not None:
        raise ValidationError(
            "Resource already has an active assignment on this project",
            field="resource_id",
        )


async def _check_project_active(db: AsyncSession, project_id: uuid.UUID) -> Project:
    # (7) no assignment on non-ACTIVE project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", str(project_id))
    if project.status != "ACTIVE":
        raise ValidationError(
            "Cannot create/modify assignments on a non-ACTIVE project",
            field="project_id",
        )
    return project


async def _validate_resource(db: AsyncSession, resource_id: uuid.UUID) -> Resource:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if resource is None:
        raise NotFoundError("Resource", str(resource_id))
    if not resource.is_active:
        raise ValidationError("Resource is not active", field="resource_id")
    return resource


async def _check_over_allocation(
    db: AsyncSession,
    resource_id: uuid.UUID,
    new_allocation: int,
    exclude_id: uuid.UUID | None = None,
) -> int | None:
    """Return total allocation if over 100%, else None."""
    query = select(func.coalesce(func.sum(Assignment.allocation_pct), 0)).where(
        Assignment.resource_id == resource_id,
        Assignment.status == "ACTIVE",
    )
    if exclude_id:
        query = query.where(Assignment.id != exclude_id)
    result = await db.execute(query)
    current_total = result.scalar() or 0
    new_total = current_total + new_allocation
    if new_total > 100:
        return new_total
    return None


async def _load_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.project), selectinload(Assignment.resource))
        .where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise NotFoundError("Assignment", str(assignment_id))
    return assignment


def _assignment_to_dict(
    a: Assignment,
    role_code: str,
) -> dict:
    resource = a.resource
    return {
        "id": a.id,
        "project_id": a.project_id,
        "resource": {
            "id": resource.id,
            "name": resource.name,
            "designation": resource.designation,
            "technical_expertise": resource.technical_expertise,
        }
        if resource
        else None,
        "effective_designation": a.project_designation
        or (resource.designation if resource else None),
        "effective_expertise": a.project_expertise
        or (resource.technical_expertise if resource else None),
        "allocation_pct": a.allocation_pct,
        "billability_pct": a.billability_pct
        if can_see_field(role_code, "billability_pct")
        else None,
        "is_shadow": a.is_shadow if can_see_field(role_code, "is_shadow") else None,
        "billing_rate": a.billing_rate if can_see_field(role_code, "billing_rate") else None,
        "project_designation": a.project_designation,
        "project_expertise": a.project_expertise,
        "start_date": a.start_date.isoformat() if a.start_date else None,
        "end_date": a.end_date.isoformat() if a.end_date else None,
        "status": a.status,
        "released_at": a.released_at.isoformat() if a.released_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _assignment_detail_dict(a: Assignment, role_code: str) -> dict:
    d = _assignment_to_dict(a, role_code)
    project = a.project
    d["project"] = (
        {
            "id": project.id,
            "name": project.name,
            "type": project.type,
            "status": project.status,
            "worklog_enabled": project.worklog_enabled,
            "client_name": project.client.name if project.client else None,
        }
        if project
        else None
    )
    return d


async def list_project_assignments(
    db: AsyncSession,
    project_id: uuid.UUID,
    permission: Permission,
    current_user: User,
    status: str | None = None,
) -> list[dict]:
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Project", str(project_id))

    query = (
        select(Assignment)
        .options(selectinload(Assignment.resource), selectinload(Assignment.project))
        .where(Assignment.project_id == project_id)
    )
    if status:
        query = query.where(Assignment.status == status)
    query = query.order_by(Assignment.created_at.desc())

    result = await db.execute(query)
    assignments = list(result.scalars().all())
    role_code = current_user.role.code
    return [_assignment_to_dict(a, role_code) for a in assignments]


async def list_resource_assignments(
    db: AsyncSession,
    resource_id: uuid.UUID,
    permission: Permission,
    current_user: User,
    status: str | None = None,
) -> list[dict]:
    # Verify resource exists
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Resource", str(resource_id))

    query = (
        select(Assignment)
        .options(selectinload(Assignment.resource), selectinload(Assignment.project))
        .where(Assignment.resource_id == resource_id)
    )
    if status:
        query = query.where(Assignment.status == status)
    query = query.order_by(Assignment.created_at.desc())

    result = await db.execute(query)
    assignments = list(result.scalars().all())
    role_code = current_user.role.code
    return [_assignment_detail_dict(a, role_code) for a in assignments]


async def create_assignment(
    db: AsyncSession,
    project_id: uuid.UUID,
    resource_id: uuid.UUID,
    allocation_pct: int,
    billability_pct: int,
    is_shadow: bool,
    start_date: date,
    end_date: date | None = None,
    project_designation: str | None = None,
    project_expertise: str | None = None,
    current_user_id: uuid.UUID | None = None,
    role_code: str = "CEO",
) -> tuple[dict, list[str]]:
    await _check_project_active(db, project_id)
    await _validate_resource(db, resource_id)
    _validate_assignment_rules(allocation_pct, billability_pct, is_shadow, start_date, end_date)
    await _check_duplicate_active(db, resource_id, project_id)

    warnings: list[str] = []
    over = await _check_over_allocation(db, resource_id, allocation_pct)
    if over is not None:
        warnings.append(f"Resource total allocation will be {over}% (over 100%)")

    assignment = Assignment(
        id=uuid.uuid4(),
        project_id=project_id,
        resource_id=resource_id,
        allocation_pct=allocation_pct,
        billability_pct=billability_pct,
        is_shadow=is_shadow,
        project_designation=project_designation,
        project_expertise=project_expertise,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(assignment)
    await db.flush()

    await audit_log(
        db,
        entity_type="assignment",
        entity_id=assignment.id,
        action=AuditAction.CREATE,
        changes={
            "project_id": str(project_id),
            "resource_id": str(resource_id),
            "allocation_pct": allocation_pct,
            "billability_pct": billability_pct,
            "is_shadow": is_shadow,
            "start_date": start_date.isoformat(),
        },
        user_id=current_user_id or uuid.UUID(int=0),
    )

    loaded = await _load_assignment(db, assignment.id)
    return _assignment_detail_dict(loaded, role_code), warnings


async def get_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    role_code: str = "CEO",
) -> dict:
    assignment = await _load_assignment(db, assignment_id)
    return _assignment_detail_dict(assignment, role_code)


async def update_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    current_user_id: uuid.UUID,
    role_code: str = "CEO",
    **fields: Any,
) -> tuple[dict, list[str]]:
    assignment = await _load_assignment(db, assignment_id)

    if assignment.status != "ACTIVE":
        raise ValidationError("Cannot update a released assignment", field="status")

    await _check_project_active(db, assignment.project_id)

    new_alloc = fields.get("allocation_pct", assignment.allocation_pct)
    new_bill = fields.get("billability_pct", assignment.billability_pct)
    new_shadow = fields.get("is_shadow", assignment.is_shadow)
    new_start = fields.get("start_date", assignment.start_date)
    new_end = fields.get("end_date", assignment.end_date)

    _validate_assignment_rules(new_alloc, new_bill, new_shadow, new_start, new_end)

    changes: dict[str, tuple] = {}
    for field_name, new_val in fields.items():
        old_val = getattr(assignment, field_name, None)
        if str(old_val) != str(new_val):
            changes[field_name] = (old_val, new_val)
            setattr(assignment, field_name, new_val)

    warnings: list[str] = []
    if "allocation_pct" in changes:
        over = await _check_over_allocation(
            db, assignment.resource_id, new_alloc, exclude_id=assignment.id
        )
        if over is not None:
            warnings.append(f"Resource total allocation will be {over}% (over 100%)")

    if changes:
        await audit_log(
            db,
            entity_type="assignment",
            entity_id=assignment.id,
            action=AuditAction.UPDATE,
            changes=changes,
            user_id=current_user_id,
        )

    await db.flush()
    loaded = await _load_assignment(db, assignment.id)
    return _assignment_detail_dict(loaded, role_code), warnings


async def release_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    current_user_id: uuid.UUID,
    role_code: str = "CEO",
) -> dict:
    """See FSD §6.1 — Manual release of an active assignment."""
    assignment = await _load_assignment(db, assignment_id)

    if assignment.status != "ACTIVE":
        raise ValidationError("Only ACTIVE assignments can be released", field="status")

    now = datetime.now(UTC)
    old_status = assignment.status
    assignment.status = "RELEASED"
    assignment.released_at = now

    early = assignment.end_date and assignment.end_date > now.date()

    await audit_log(
        db,
        entity_type="assignment",
        entity_id=assignment.id,
        action=AuditAction.UPDATE,
        changes={
            "status": (old_status, "RELEASED"),
            "released_at": (None, now.isoformat()),
        },
        user_id=current_user_id,
        metadata={"early_release": early} if early else None,
    )

    await db.flush()
    loaded = await _load_assignment(db, assignment.id)
    return _assignment_detail_dict(loaded, role_code)
