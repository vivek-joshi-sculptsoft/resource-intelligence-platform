import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.auth.models import User
from app.modules.resources.models import Resource, ResourceTag
from app.shared.access_control import Permission
from app.shared.exceptions import AppError, ConflictError, NotFoundError, ValidationError


async def list_resources(
    db: AsyncSession,
    permission: Permission,
    current_user: User,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    designation: str | None = None,
    expertise: str | None = None,
    tag: str | None = None,
    availability: str | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    query = select(Resource).options(
        selectinload(Resource.tags),
        selectinload(Resource.reporting_manager),
    )
    count_query = select(func.count()).select_from(Resource)

    # See FSD §10 — Scope filtering via WHERE clause
    if permission.is_self_only:
        query = query.where(Resource.id == current_user.resource_id)
        count_query = count_query.where(Resource.id == current_user.resource_id)

    if status == "ACTIVE":
        query = query.where(Resource.is_active.is_(True))
        count_query = count_query.where(Resource.is_active.is_(True))
    elif status == "INACTIVE":
        query = query.where(Resource.is_active.is_(False))
        count_query = count_query.where(Resource.is_active.is_(False))

    if designation:
        query = query.where(Resource.designation == designation)
        count_query = count_query.where(Resource.designation == designation)

    if expertise:
        query = query.where(Resource.technical_expertise == expertise)
        count_query = count_query.where(Resource.technical_expertise == expertise)

    if tag:
        tag_subq = select(ResourceTag.resource_id).where(ResourceTag.tag == tag).subquery()
        query = query.where(Resource.id.in_(select(tag_subq.c.resource_id)))
        count_query = count_query.where(Resource.id.in_(select(tag_subq.c.resource_id)))

    if search:
        like = f"%{search}%"
        tag_search_subq = select(ResourceTag.resource_id).where(ResourceTag.tag.ilike(like))
        search_filter = (
            Resource.name.ilike(like)
            | Resource.employee_id.ilike(like)
            | Resource.id.in_(tag_search_subq)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Resource.name.asc()).offset(offset).limit(limit)
    result = await db.execute(query)
    resources = list(result.scalars().all())

    items = []
    for r in resources:
        alloc_pct = await _get_total_allocation(db, r.id)
        if availability == "bench" and alloc_pct > 0:
            continue
        if availability == "full" and alloc_pct < 100:
            continue
        if availability == "partial" and (alloc_pct == 0 or alloc_pct >= 100):
            continue

        items.append(
            {
                "id": r.id,
                "employee_id": r.employee_id,
                "name": r.name,
                "designation": r.designation,
                "technical_expertise": r.technical_expertise,
                "total_allocation_pct": alloc_pct,
                "is_active": r.is_active,
                "tags": [t.tag for t in r.tags],
                "loaded_cost_monthly": (
                    float(r.loaded_cost_monthly) if r.loaded_cost_monthly else None
                ),
            }
        )

    return items, total


async def create_resource(
    db: AsyncSession,
    employee_id: str,
    name: str,
    designation: str,
    technical_expertise: str | None,
    date_of_joining: Any,
    reporting_manager_id: uuid.UUID | None,
    tags: list[str],
    current_user_id: uuid.UUID,
    loaded_cost_monthly: float | None = None,
) -> Resource:
    existing = await db.execute(select(Resource).where(Resource.employee_id == employee_id))
    if existing.scalar_one_or_none():
        raise ConflictError("Employee ID is already in use", field="employee_id")

    if reporting_manager_id:
        mgr = await db.execute(select(Resource).where(Resource.id == reporting_manager_id))
        if mgr.scalar_one_or_none() is None:
            raise NotFoundError("Reporting manager", str(reporting_manager_id))

    resource = Resource(
        id=uuid.uuid4(),
        employee_id=employee_id,
        name=name,
        designation=designation,
        technical_expertise=technical_expertise,
        date_of_joining=date_of_joining,
        reporting_manager_id=reporting_manager_id,
        loaded_cost_monthly=loaded_cost_monthly,
    )
    db.add(resource)
    await db.flush()

    for t in tags:
        db.add(ResourceTag(resource_id=resource.id, tag=t[:100]))

    create_changes: dict[str, Any] = {
        "employee_id": employee_id,
        "name": name,
        "designation": designation,
    }
    if loaded_cost_monthly is not None:
        create_changes["loaded_cost_monthly"] = loaded_cost_monthly

    await audit_log(
        db,
        entity_type="resource",
        entity_id=resource.id,
        action=AuditAction.CREATE,
        changes=create_changes,
        user_id=current_user_id,
    )

    result = await db.execute(
        select(Resource)
        .options(
            selectinload(Resource.tags),
            selectinload(Resource.reporting_manager),
        )
        .where(Resource.id == resource.id)
    )
    return result.scalar_one()


async def get_resource(db: AsyncSession, resource_id: uuid.UUID) -> Resource:
    result = await db.execute(
        select(Resource)
        .options(
            selectinload(Resource.tags),
            selectinload(Resource.reporting_manager),
        )
        .where(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if resource is None:
        raise NotFoundError("Resource", str(resource_id))
    return resource


async def update_resource(
    db: AsyncSession,
    resource_id: uuid.UUID,
    current_user_id: uuid.UUID,
    **fields: Any,
) -> Resource:
    resource = await get_resource(db, resource_id)
    changes: dict[str, tuple] = {}

    for field_name, new_val in fields.items():
        if new_val is None:
            continue
        old_val = getattr(resource, field_name, None)

        if field_name == "reporting_manager_id" and new_val:
            if new_val == resource_id:
                raise ValidationError(
                    "Resource cannot be their own reporting manager",
                    field="reporting_manager_id",
                )
            mgr = await db.execute(select(Resource).where(Resource.id == new_val))
            if mgr.scalar_one_or_none() is None:
                raise NotFoundError("Reporting manager", str(new_val))

        if field_name == "employee_id" and new_val != old_val:
            dup = await db.execute(
                select(Resource).where(
                    Resource.employee_id == new_val,
                    Resource.id != resource_id,
                )
            )
            if dup.scalar_one_or_none():
                raise ConflictError("Employee ID is already in use", field="employee_id")

        if str(old_val) != str(new_val):
            changes[field_name] = (old_val, new_val)
            setattr(resource, field_name, new_val)

    if changes:
        await audit_log(
            db,
            entity_type="resource",
            entity_id=resource.id,
            action=AuditAction.UPDATE,
            changes=changes,
            user_id=current_user_id,
        )

    await db.flush()
    result = await db.execute(
        select(Resource)
        .options(
            selectinload(Resource.tags),
            selectinload(Resource.reporting_manager),
        )
        .where(Resource.id == resource.id)
    )
    return result.scalar_one()


async def deactivate_resource(
    db: AsyncSession,
    resource_id: uuid.UUID,
    current_user_id: uuid.UUID,
) -> None:
    resource = await get_resource(db, resource_id)

    if not resource.is_active:
        raise AppError("Resource is already inactive", status_code=400)

    # See FSD §8 — Deactivation blocked if resource is DM or PM on ACTIVE project
    from app.modules.projects.models import Project

    active_as_manager = await db.execute(
        select(func.count())
        .select_from(Project)
        .where(
            (Project.dm_id == resource_id) | (Project.pm_id == resource_id),
            Project.status == "ACTIVE",
        )
    )
    if (active_as_manager.scalar() or 0) > 0:
        raise AppError(
            "Cannot deactivate: resource is DM or PM on an active project",
            status_code=400,
        )

    resource.is_active = False

    await audit_log(
        db,
        entity_type="resource",
        entity_id=resource.id,
        action=AuditAction.DELETE,
        changes={"is_active": (True, False)},
        user_id=current_user_id,
    )


async def add_tag(
    db: AsyncSession,
    resource_id: uuid.UUID,
    tag: str,
    current_user_id: uuid.UUID,
) -> list[str]:
    resource = await get_resource(db, resource_id)
    existing_tags = {t.tag for t in resource.tags}

    if tag in existing_tags:
        return sorted(existing_tags)

    db.add(ResourceTag(resource_id=resource_id, tag=tag))

    await audit_log(
        db,
        entity_type="resource",
        entity_id=resource_id,
        action=AuditAction.UPDATE,
        changes={"tags": (None, tag)},
        user_id=current_user_id,
    )

    await db.flush()
    return sorted(existing_tags | {tag})


async def remove_tag(
    db: AsyncSession,
    resource_id: uuid.UUID,
    tag: str,
    current_user_id: uuid.UUID,
) -> list[str]:
    resource = await get_resource(db, resource_id)

    tag_obj = None
    for t in resource.tags:
        if t.tag == tag:
            tag_obj = t
            break

    if tag_obj is None:
        raise NotFoundError("Tag", tag)

    await db.delete(tag_obj)

    await audit_log(
        db,
        entity_type="resource",
        entity_id=resource_id,
        action=AuditAction.UPDATE,
        changes={"tags": (tag, None)},
        user_id=current_user_id,
    )

    await db.flush()
    remaining = {t.tag for t in resource.tags if t.tag != tag}
    return sorted(remaining)


async def _get_total_allocation(db: AsyncSession, resource_id: uuid.UUID) -> int:
    """Sum of active assignment allocation_pct for this resource.

    Returns 0 if no assignments module yet.
    """
    try:
        from app.modules.allocations.models import Assignment

        result = await db.execute(
            select(func.coalesce(func.sum(Assignment.allocation_pct), 0)).where(
                Assignment.resource_id == resource_id,
                Assignment.status == "ACTIVE",
            )
        )
        return int(result.scalar() or 0)
    except Exception:
        return 0
