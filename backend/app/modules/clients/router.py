import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.clients.schemas import ClientCreateRequest, ClientUpdateRequest
from app.modules.clients.service import (
    create_client,
    deactivate_client,
    get_client_detail,
    list_clients,
    update_client,
)
from app.shared.access_control import check_access
from app.shared.utils import build_pagination_meta

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("")
async def list_clients_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See FSD §10 — client_profiles access check
    permission = await check_access(db, current_user, "client_profiles")

    items, total = await list_clients(
        db,
        permission=permission,
        current_user=current_user,
        page=page,
        limit=limit,
        status=status,
        search=search,
    )

    return {
        "data": items,
        "meta": build_pagination_meta(total, page, limit),
    }


@router.post("", status_code=201)
async def create_client_endpoint(
    body: ClientCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "client_profiles", require_edit=True)

    client = await create_client(
        db,
        name=body.name,
        industry=body.industry,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
        engagement_start_date=body.engagement_start_date,
        notes=body.notes,
        current_user_id=current_user.id,
    )

    detail = await get_client_detail(db, client.id)
    return {"data": detail}


@router.get("/{client_id}")
async def get_client_endpoint(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "client_profiles")

    # See FSD §10 — OWN_PORTFOLIO scope check for detail view
    if permission.is_own_portfolio and current_user.resource_id:
        from sqlalchemy import select

        from app.modules.projects.models import Project

        has_project = await db.execute(
            select(Project.id)
            .where(
                Project.client_id == client_id,
                (Project.dm_id == current_user.resource_id)
                | (Project.pm_id == current_user.resource_id),
            )
            .limit(1)
        )
        if has_project.scalar_one_or_none() is None:
            from app.shared.exceptions import ForbiddenError

            raise ForbiddenError()

    detail = await get_client_detail(db, client_id)
    return {"data": detail}


@router.get("/{client_id}/dashboard")
async def get_client_dashboard_endpoint(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "client_profiles")
    detail = await get_client_detail(db, client_id)
    return {"data": detail["dashboard"]}


@router.put("/{client_id}")
async def update_client_endpoint(
    client_id: uuid.UUID,
    body: ClientUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "client_profiles", require_edit=True)

    fields = body.model_dump(exclude_unset=True)
    await update_client(
        db,
        client_id=client_id,
        current_user_id=current_user.id,
        **fields,
    )

    detail = await get_client_detail(db, client_id)
    return {"data": detail}


@router.delete("/{client_id}")
async def delete_client_endpoint(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "client_profiles", require_edit=True)
    await deactivate_client(db, client_id, current_user.id)
    return {"success": True}
