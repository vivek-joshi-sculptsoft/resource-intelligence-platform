"""See FSD §2.8, §2.9 — Milestone and Invoice API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.invoicing.schemas import (
    InvoiceCreateRequest,
    InvoiceStatusRequest,
    InvoiceUpdateRequest,
    MilestoneCreateRequest,
    MilestoneStatusRequest,
    MilestoneUpdateRequest,
)
from app.modules.invoicing.service import (
    create_invoice,
    create_milestone,
    get_milestone,
    get_receivables,
    list_invoices,
    list_milestones,
    transition_invoice_status,
    transition_milestone_status,
    update_invoice,
    update_milestone,
)
from app.modules.projects.service import get_project
from app.shared.access_control import check_access
from app.shared.exceptions import ForbiddenError

router = APIRouter(tags=["invoicing"])

MILESTONE_DATA_TYPE = "milestones"
INVOICE_DATA_TYPE = "invoicing"


def _check_portfolio_scope(project, permission, current_user: User) -> None:
    """See FSD §10 — OWN_PORTFOLIO means dm_id or pm_id = user's resource_id."""
    if not permission.is_own_portfolio:
        return
    if current_user.resource_id and (
        project.dm_id == current_user.resource_id or project.pm_id == current_user.resource_id
    ):
        return
    raise ForbiddenError()


@router.get("/api/v1/projects/{project_id}/milestones")
async def list_milestones_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, MILESTONE_DATA_TYPE)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await list_milestones(db, project_id)
    return {"data": data}


@router.post("/api/v1/projects/{project_id}/milestones", status_code=201)
async def create_milestone_endpoint(
    project_id: uuid.UUID,
    body: MilestoneCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, MILESTONE_DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await create_milestone(
        db,
        project_id=project_id,
        current_user_id=current_user.id,
        name=body.name,
        amount=body.amount,
        planned_delivery_date=body.planned_delivery_date,
        sort_order=body.sort_order,
    )
    return {"data": data}


@router.get("/api/v1/projects/{project_id}/milestones/{milestone_id}")
async def get_milestone_endpoint(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, MILESTONE_DATA_TYPE)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await get_milestone(db, milestone_id, project_id)
    return {"data": data}


@router.put("/api/v1/projects/{project_id}/milestones/{milestone_id}")
async def update_milestone_endpoint(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    body: MilestoneUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, MILESTONE_DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    fields = body.model_dump(exclude_unset=True)
    data = await update_milestone(
        db,
        milestone_id=milestone_id,
        project_id=project_id,
        current_user_id=current_user.id,
        **fields,
    )
    return {"data": data}


@router.put("/api/v1/projects/{project_id}/milestones/{milestone_id}/status")
async def transition_milestone_status_endpoint(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    body: MilestoneStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, MILESTONE_DATA_TYPE, require_edit=True)
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    data = await transition_milestone_status(
        db,
        milestone_id=milestone_id,
        project_id=project_id,
        current_user_id=current_user.id,
        role_code=current_user.role.code,
        new_status=body.status,
    )
    return {"data": data}


# ── Invoice endpoints — See FSD §2.9, §6.3 ──


@router.get("/api/v1/invoices/receivables")
async def get_receivables_endpoint(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX: Finance EDIT ALL, CEO/CTO VIEW ALL, others NONE
    await check_access(db, current_user, INVOICE_DATA_TYPE)
    status_filter = [s.strip() for s in status.split(",")] if status else None
    data = await get_receivables(db, status_filter=status_filter)
    return {"data": data}


@router.get("/api/v1/projects/{project_id}/invoices")
async def list_invoices_endpoint(
    project_id: uuid.UUID,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, INVOICE_DATA_TYPE)
    data, total = await list_invoices(db, project_id, status=status, page=page, limit=limit)
    return {"data": data, "total": total, "page": page, "limit": limit}


@router.post("/api/v1/projects/{project_id}/invoices", status_code=201)
async def create_invoice_endpoint(
    project_id: uuid.UUID,
    body: InvoiceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, INVOICE_DATA_TYPE, require_edit=True)
    data = await create_invoice(
        db,
        project_id=project_id,
        current_user_id=current_user.id,
        invoice_date=body.invoice_date,
        amount=body.amount,
        currency=body.currency,
        exchange_rate=body.exchange_rate,
        milestone_id=body.milestone_id,
        billing_period_start=body.billing_period_start,
        billing_period_end=body.billing_period_end,
        notes=body.notes,
    )
    return {"data": data}


@router.put("/api/v1/projects/{project_id}/invoices/{invoice_id}")
async def update_invoice_endpoint(
    project_id: uuid.UUID,
    invoice_id: uuid.UUID,
    body: InvoiceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, INVOICE_DATA_TYPE, require_edit=True)
    fields = body.model_dump(exclude_unset=True)
    data = await update_invoice(
        db,
        invoice_id=invoice_id,
        project_id=project_id,
        current_user_id=current_user.id,
        **fields,
    )
    return {"data": data}


@router.put("/api/v1/projects/{project_id}/invoices/{invoice_id}/status")
async def transition_invoice_status_endpoint(
    project_id: uuid.UUID,
    invoice_id: uuid.UUID,
    body: InvoiceStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, INVOICE_DATA_TYPE, require_edit=True)
    data = await transition_invoice_status(
        db,
        invoice_id=invoice_id,
        project_id=project_id,
        current_user_id=current_user.id,
        new_status=body.status,
    )
    return {"data": data}
