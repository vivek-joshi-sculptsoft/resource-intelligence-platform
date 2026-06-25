"""See modules/08-financial-engine/API.md — financial aggregation endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.financial.service import (
    get_client_financials,
    get_company_financials,
    get_project_financials,
    get_resource_bench_cost,
)
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.shared.access_control import can_see_field, check_access, has_access
from app.shared.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/api/v1/projects", tags=["financial"])
client_financial_router = APIRouter(prefix="/api/v1/clients", tags=["financial"])
dashboard_financial_router = APIRouter(prefix="/api/v1/dashboard", tags=["financial"])
resource_financial_router = APIRouter(prefix="/api/v1/resources", tags=["financial"])


@router.get("/{project_id}/financials")
async def get_project_financials_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — project_margin: CEO/CTO/Finance (ALL), DM (OWN_PORTFOLIO)
    permission = await check_access(db, current_user, "project_margin")

    project = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", str(project_id))

    # See FSD §10 — OWN_PORTFOLIO for project_margin means dm_id = user's resource_id
    if permission.is_own_portfolio:
        if not current_user.resource_id or project.dm_id != current_user.resource_id:
            raise ForbiddenError()

    role_code = current_user.role.code
    data = await get_project_financials(
        db,
        project,
        can_see_cost=can_see_field(role_code, "loaded_cost_monthly"),
        can_see_rate=can_see_field(role_code, "billing_rate"),
        can_see_invoicing=await has_access(db, current_user, "invoicing"),
        can_see_nonhuman=await has_access(db, current_user, "non_human_costs"),
    )
    return {"data": data.model_dump()}


@client_financial_router.get("/{client_id}/financials")
async def get_client_financials_endpoint(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — project_margin: CEO/CTO/Finance (ALL), DM (OWN_PORTFOLIO)
    permission = await check_access(db, current_user, "project_margin")

    client_entity = (
        await db.execute(select(Client).where(Client.id == client_id))
    ).scalar_one_or_none()
    if client_entity is None:
        raise NotFoundError("Client", str(client_id))

    query = select(Project).where(Project.client_id == client_id, Project.is_active == True)  # noqa: E712
    if permission.is_own_portfolio:
        if not current_user.resource_id:
            raise ForbiddenError()
        query = query.where(Project.dm_id == current_user.resource_id)
    projects = (await db.execute(query)).scalars().all()

    role_code = current_user.role.code
    data = await get_client_financials(
        db,
        list(projects),
        can_see_cost=can_see_field(role_code, "loaded_cost_monthly"),
        can_see_rate=can_see_field(role_code, "billing_rate"),
        can_see_invoicing=await has_access(db, current_user, "invoicing"),
        can_see_nonhuman=await has_access(db, current_user, "non_human_costs"),
    )
    return {"data": data.model_dump()}


@dashboard_financial_router.get("/financials")
async def get_company_financials_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — project_margin: CEO/CTO/Finance (ALL), DM (OWN_PORTFOLIO)
    permission = await check_access(db, current_user, "project_margin")

    query = select(Project).where(Project.is_active == True)  # noqa: E712
    if permission.is_own_portfolio:
        if not current_user.resource_id:
            raise ForbiddenError()
        query = query.where(Project.dm_id == current_user.resource_id)
    projects = (await db.execute(query)).scalars().all()

    role_code = current_user.role.code
    data = await get_company_financials(
        db,
        list(projects),
        can_see_cost=can_see_field(role_code, "loaded_cost_monthly"),
        can_see_rate=can_see_field(role_code, "billing_rate"),
        can_see_invoicing=await has_access(db, current_user, "invoicing"),
        can_see_nonhuman=await has_access(db, current_user, "non_human_costs"),
    )
    return {"data": data.model_dump()}


@resource_financial_router.get("/{resource_id}/bench-cost")
async def get_resource_bench_cost_endpoint(
    resource_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — bench_data: CEO/CTO/Finance/DM (VIEW); others NONE
    await check_access(db, current_user, "bench_data")

    resource = (
        await db.execute(select(Resource).where(Resource.id == resource_id))
    ).scalar_one_or_none()
    if resource is None:
        raise NotFoundError("Resource", str(resource_id))

    role_code = current_user.role.code
    data = await get_resource_bench_cost(
        db, resource, can_see_cost=can_see_field(role_code, "loaded_cost_monthly")
    )
    return {"data": data.model_dump() if data else None}
