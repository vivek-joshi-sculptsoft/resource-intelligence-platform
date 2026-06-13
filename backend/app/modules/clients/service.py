import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.shared.access_control import Permission
from app.shared.exceptions import AppError, ConflictError, NotFoundError


async def list_clients(
    db: AsyncSession,
    permission: Permission,
    current_user: User,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    query = select(Client)
    count_query = select(func.count()).select_from(Client)

    # See FSD §10 — OWN_PORTFOLIO: clients with projects where dm_id or pm_id = user.resource_id
    if permission.is_own_portfolio and current_user.resource_id:
        portfolio_subq = (
            select(Project.client_id)
            .where(
                (Project.dm_id == current_user.resource_id)
                | (Project.pm_id == current_user.resource_id)
            )
            .distinct()
            .subquery()
        )
        query = query.where(Client.id.in_(select(portfolio_subq.c.client_id)))
        count_query = count_query.where(Client.id.in_(select(portfolio_subq.c.client_id)))

    if status == "ACTIVE":
        query = query.where(Client.is_active.is_(True))
        count_query = count_query.where(Client.is_active.is_(True))
    elif status == "INACTIVE":
        query = query.where(Client.is_active.is_(False))
        count_query = count_query.where(Client.is_active.is_(False))

    if search:
        like = f"%{search}%"
        query = query.where(Client.name.ilike(like))
        count_query = count_query.where(Client.name.ilike(like))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Client.name.asc()).offset(offset).limit(limit)
    result = await db.execute(query)
    clients = list(result.scalars().all())

    items = []
    for c in clients:
        active_count = await _active_project_count(db, c.id)
        items.append(
            {
                "id": c.id,
                "name": c.name,
                "industry": c.industry,
                "engagement_start_date": (
                    c.engagement_start_date.isoformat() if c.engagement_start_date else None
                ),
                "active_project_count": active_count,
                "is_active": c.is_active,
            }
        )

    return items, total


async def create_client(
    db: AsyncSession,
    name: str,
    industry: str | None,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    engagement_start_date: Any,
    notes: str | None,
    current_user_id: uuid.UUID,
) -> Client:
    existing = await db.execute(select(Client).where(Client.name == name))
    if existing.scalar_one_or_none():
        raise ConflictError("Client name already exists", field="name")

    client = Client(
        id=uuid.uuid4(),
        name=name,
        industry=industry,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        engagement_start_date=engagement_start_date,
        notes=notes,
    )
    db.add(client)
    await db.flush()

    await audit_log(
        db,
        entity_type="client",
        entity_id=client.id,
        action=AuditAction.CREATE,
        changes={"name": name},
        user_id=current_user_id,
    )

    return client


async def get_client(db: AsyncSession, client_id: uuid.UUID) -> Client:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise NotFoundError("Client", str(client_id))
    return client


async def get_client_detail(db: AsyncSession, client_id: uuid.UUID) -> dict:
    client = await get_client(db, client_id)

    projects_result = await db.execute(select(Project).where(Project.client_id == client_id))
    projects = [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "status": p.status,
            "dm_id": p.dm_id,
            "pm_id": p.pm_id,
        }
        for p in projects_result.scalars().all()
    ]

    active_count = sum(1 for p in projects if p["status"] == "ACTIVE")

    type_counts: dict[str, int] = {}
    for p in projects:
        type_counts[p["type"]] = type_counts.get(p["type"], 0) + 1

    return {
        "id": client.id,
        "name": client.name,
        "industry": client.industry,
        "contact_name": client.contact_name,
        "contact_email": client.contact_email,
        "contact_phone": client.contact_phone,
        "engagement_start_date": (
            client.engagement_start_date.isoformat() if client.engagement_start_date else None
        ),
        "notes": client.notes,
        "is_active": client.is_active,
        "created_at": client.created_at.isoformat() if client.created_at else "",
        "projects": projects,
        "dashboard": {
            "active_resource_count": 0,
            "active_project_count": active_count,
            "total_monthly_billing_inr": None,
            "total_cost_inr": None,
            "aggregate_margin_inr": None,
            "project_count_by_type": type_counts,
        },
    }


async def update_client(
    db: AsyncSession,
    client_id: uuid.UUID,
    current_user_id: uuid.UUID,
    **fields: Any,
) -> Client:
    client = await get_client(db, client_id)
    changes: dict[str, tuple] = {}

    for field_name, new_val in fields.items():
        if new_val is None:
            continue
        old_val = getattr(client, field_name, None)

        if field_name == "name" and new_val != old_val:
            dup = await db.execute(
                select(Client).where(Client.name == new_val, Client.id != client_id)
            )
            if dup.scalar_one_or_none():
                raise ConflictError("Client name already exists", field="name")

        old_str = str(old_val) if old_val is not None else None
        new_str = str(new_val) if new_val is not None else None
        if old_str != new_str:
            changes[field_name] = (old_val, new_val)
            setattr(client, field_name, new_val)

    if changes:
        await audit_log(
            db,
            entity_type="client",
            entity_id=client.id,
            action=AuditAction.UPDATE,
            changes=changes,
            user_id=current_user_id,
        )

    await db.flush()
    return client


async def deactivate_client(
    db: AsyncSession,
    client_id: uuid.UUID,
    current_user_id: uuid.UUID,
) -> None:
    client = await get_client(db, client_id)

    if not client.is_active:
        raise AppError("Client is already inactive", status_code=400)

    active_projects = await db.execute(
        select(func.count())
        .select_from(Project)
        .where(Project.client_id == client_id, Project.status == "ACTIVE")
    )
    if (active_projects.scalar() or 0) > 0:
        raise AppError(
            "Cannot deactivate: client has active projects",
            status_code=400,
        )

    client.is_active = False

    await audit_log(
        db,
        entity_type="client",
        entity_id=client.id,
        action=AuditAction.DELETE,
        changes={"is_active": (True, False)},
        user_id=current_user_id,
    )


async def _active_project_count(db: AsyncSession, client_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Project)
        .where(Project.client_id == client_id, Project.status == "ACTIVE")
    )
    return result.scalar() or 0
