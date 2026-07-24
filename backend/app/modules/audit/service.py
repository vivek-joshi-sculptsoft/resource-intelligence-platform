import json
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditAction, AuditLog
from app.modules.audit.schemas import AuditLogChangedBy, AuditLogResponse
from app.modules.auth.models import AccessLevel, Scope, User
from app.shared.access_control import Permission


# See FSD §13 — (table, display-name column) per entity type. Assignment and Invoice
# have no natural display-name column, so entity_name stays null for those types.
ENTITY_NAME_QUERIES: dict[str, tuple[str, str]] = {
    "Project": ("projects", "name"),
    "Resource": ("resources", "name"),
    "Client": ("clients", "name"),
    "Milestone": ("milestones", "name"),
    "NonHumanCost": ("non_human_costs", "description"),
}

# See FSD §10 — entities whose portfolio scope is determined via project ownership
PORTFOLIO_SCOPED_ENTITY_TYPES = {"Project", "Assignment", "Milestone", "Invoice", "NonHumanCost"}


async def _resolve_entity_names(
    db: AsyncSession, entity_ids: set[tuple[str, uuid.UUID]]
) -> dict[tuple[str, str], str]:
    """Batch-resolve entity display names."""
    from sqlalchemy import text

    names: dict[tuple[str, str], str] = {}
    by_type: dict[str, list[str]] = {}
    for etype, eid in entity_ids:
        by_type.setdefault(etype, []).append(str(eid))

    for etype, ids in by_type.items():
        mapping = ENTITY_NAME_QUERIES.get(etype)
        if not mapping:
            continue
        table, column = mapping
        placeholders = ", ".join(f"'{i}'" for i in ids)
        result = await db.execute(
            text(f"SELECT id, {column} FROM {table} WHERE id IN ({placeholders})")  # noqa: S608
        )
        for row in result.fetchall():
            names[(etype, str(row[0]))] = row[1]
    return names


async def _resolve_user_names(
    db: AsyncSession, user_ids: set[uuid.UUID]
) -> dict[uuid.UUID, str]:
    result = await db.execute(
        select(User.id, User.name).where(User.id.in_(user_ids))
    )
    return {row[0]: row[1] for row in result.fetchall()}


async def _get_portfolio_entity_ids(
    db: AsyncSession, resource_id: uuid.UUID
) -> set[str]:
    """Get entity IDs visible to a DM/PM via their project portfolio. See FSD §10."""
    from app.modules.allocations.models import Assignment
    from app.modules.invoicing.models import Invoice, Milestone
    from app.modules.nonhuman_costs.models import NonHumanCost
    from app.modules.projects.models import Project

    project_result = await db.execute(
        select(Project.id).where(
            or_(Project.dm_id == resource_id, Project.pm_id == resource_id)
        )
    )
    project_ids = [row[0] for row in project_result.fetchall()]

    if not project_ids:
        return set()

    entity_ids = {str(pid) for pid in project_ids}

    for model in (Assignment, Milestone, Invoice, NonHumanCost):
        result = await db.execute(select(model.id).where(model.project_id.in_(project_ids)))
        for row in result.fetchall():
            entity_ids.add(str(row[0]))

    return entity_ids


async def query_audit_logs(
    db: AsyncSession,
    permission: Permission,
    current_user: User,
    page: int = 1,
    limit: int = 20,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    changed_by_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_order: str = "desc",
) -> tuple[list[AuditLogResponse], int]:
    """Query audit logs with filters and portfolio scoping. See FSD §13."""
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)

    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
        count_query = count_query.where(AuditLog.entity_id == entity_id)

    if changed_by_id:
        query = query.where(AuditLog.changed_by == changed_by_id)
        count_query = count_query.where(AuditLog.changed_by == changed_by_id)

    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time())
        query = query.where(AuditLog.changed_at >= start_dt)
        count_query = count_query.where(AuditLog.changed_at >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.where(AuditLog.changed_at <= end_dt)
        count_query = count_query.where(AuditLog.changed_at <= end_dt)

    # See FSD §10 — OWN_PORTFOLIO scoping at query level
    if permission.is_own_portfolio and current_user.resource_id:
        visible_ids = await _get_portfolio_entity_ids(db, current_user.resource_id)
        if visible_ids:
            visible_uuids = [uuid.UUID(i) for i in visible_ids]
            entity_id_filter = AuditLog.entity_id.in_(visible_uuids)
            # Also include Resource audit logs for resources on their projects
            resource_ids = await _get_portfolio_resource_ids(db, current_user.resource_id)
            if resource_ids:
                resource_uuids = [uuid.UUID(i) for i in resource_ids]
                resource_filter = (AuditLog.entity_type == "Resource") & (
                    AuditLog.entity_id.in_(resource_uuids)
                )
                combined = or_(entity_id_filter, resource_filter)
            else:
                combined = entity_id_filter
            query = query.where(combined)
            count_query = count_query.where(combined)
        else:
            query = query.where(AuditLog.entity_id == uuid.UUID(int=0))
            count_query = count_query.where(AuditLog.entity_id == uuid.UUID(int=0))
    elif permission.is_own_portfolio:
        query = query.where(AuditLog.entity_id == uuid.UUID(int=0))
        count_query = count_query.where(AuditLog.entity_id == uuid.UUID(int=0))

    order = AuditLog.changed_at.asc() if sort_order == "asc" else AuditLog.changed_at.desc()
    query = query.order_by(order)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    if not rows:
        return [], total

    entity_ids_to_resolve = {(r.entity_type, r.entity_id) for r in rows}
    user_ids_to_resolve = {r.changed_by for r in rows}

    entity_names = await _resolve_entity_names(db, entity_ids_to_resolve)
    user_names = await _resolve_user_names(db, user_ids_to_resolve)

    responses = []
    for row in rows:
        responses.append(
            AuditLogResponse(
                id=row.id,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                entity_name=entity_names.get((row.entity_type, str(row.entity_id))),
                action=row.action.value,
                field_name=row.field_name,
                old_value=row.old_value,
                new_value=row.new_value,
                changed_by=AuditLogChangedBy(
                    id=row.changed_by,
                    name=user_names.get(row.changed_by, "Unknown"),
                ),
                changed_at=row.changed_at,
            )
        )
    return responses, total


async def get_entity_audit_logs(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[AuditLogResponse], int]:
    """Full audit history for one entity. See FSD §13."""
    return await query_audit_logs(
        db,
        permission=Permission(access_level=AccessLevel.VIEW, scope=Scope.ALL),
        current_user=None,  # type: ignore[arg-type]
        page=page,
        limit=limit,
        entity_type=entity_type,
        entity_id=entity_id,
    )


async def _get_portfolio_resource_ids(
    db: AsyncSession, resource_id: uuid.UUID
) -> set[str]:
    """Get resource IDs assigned to projects managed by this DM/PM. See FSD §10."""
    from app.modules.allocations.models import Assignment
    from app.modules.projects.models import Project

    result = await db.execute(
        select(Assignment.resource_id)
        .join(Project, Assignment.project_id == Project.id)
        .where(or_(Project.dm_id == resource_id, Project.pm_id == resource_id))
        .distinct()
    )
    return {str(row[0]) for row in result.fetchall()}


async def audit_log(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
    action: AuditAction,
    changes: dict[str, tuple[Any, Any]] | None = None,
    user_id: uuid.UUID | str = "SYSTEM",
    metadata: dict | None = None,
) -> list[AuditLog]:
    """Log an audit entry. For UPDATE, pass changes as {field: (old, new)}."""
    entries: list[AuditLog] = []

    changed_by = (
        user_id
        if isinstance(user_id, uuid.UUID)
        else uuid.UUID(user_id)
        if user_id != "SYSTEM"
        else uuid.UUID(int=0)
    )

    if action == AuditAction.CREATE:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=None,
            old_value=None,
            new_value=json.dumps(changes) if changes else None,
            changed_by=changed_by,
            metadata_=metadata,
        )
        db.add(entry)
        entries.append(entry)

    elif action == AuditAction.UPDATE and changes:
        for field_name, (old_val, new_val) in changes.items():
            if old_val == new_val:
                continue
            entry = AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                field_name=field_name,
                old_value=json.dumps(old_val, default=str),
                new_value=json.dumps(new_val, default=str),
                changed_by=changed_by,
                metadata_=metadata,
            )
            db.add(entry)
            entries.append(entry)

    elif action == AuditAction.DELETE:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=None,
            old_value=json.dumps(changes) if changes else None,
            new_value=None,
            changed_by=changed_by,
            metadata_=metadata,
        )
        db.add(entry)
        entries.append(entry)

    return entries
