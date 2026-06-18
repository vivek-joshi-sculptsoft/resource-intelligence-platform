"""See FSD §2.8, §2.9, §6.2, §6.3 — Milestone and Invoice business logic."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.invoicing.models import Invoice, Milestone
from app.modules.invoicing.schemas import (
    FINANCE_ONLY_TRANSITIONS,
    INVOICE_FORWARD_TRANSITIONS,
    MILESTONE_BACKWARD_TRANSITIONS,
    MILESTONE_FORWARD_TRANSITIONS,
    InvoiceStatus,
    MilestoneStatus,
)
from app.modules.projects.service import get_project
from app.shared.exceptions import ForbiddenError, NotFoundError, ValidationError

MILESTONE_ENTITY = "Milestone"
INVOICE_ENTITY = "Invoice"


def _milestone_to_dict(milestone: Milestone) -> dict[str, Any]:
    is_delayed = (
        milestone.actual_delivery_date is not None
        and milestone.planned_delivery_date is not None
        and milestone.actual_delivery_date > milestone.planned_delivery_date
    )
    return {
        "id": str(milestone.id),
        "project_id": str(milestone.project_id),
        "name": milestone.name,
        "amount": float(milestone.amount) if milestone.amount is not None else None,
        "planned_delivery_date": (
            milestone.planned_delivery_date.isoformat() if milestone.planned_delivery_date else None
        ),
        "actual_delivery_date": (
            milestone.actual_delivery_date.isoformat() if milestone.actual_delivery_date else None
        ),
        "status": milestone.status,
        "sort_order": milestone.sort_order,
        "is_delayed": is_delayed,
        "is_active": milestone.is_active,
        "created_at": milestone.created_at.isoformat() if milestone.created_at else None,
        "updated_at": milestone.updated_at.isoformat() if milestone.updated_at else None,
    }


async def _load_milestone(
    db: AsyncSession, milestone_id: uuid.UUID, project_id: uuid.UUID
) -> Milestone:
    result = await db.execute(
        select(Milestone).where(
            Milestone.id == milestone_id,
            Milestone.project_id == project_id,
            Milestone.is_active == True,  # noqa: E712
        )
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise NotFoundError("Milestone", str(milestone_id))
    return milestone


async def _check_fixed_price(db: AsyncSession, project_id: uuid.UUID) -> None:
    project = await get_project(db, project_id)
    if project.type != "FIXED_PRICE":
        raise ValidationError("Milestones only apply to FIXED_PRICE projects", field="project_id")


async def list_milestones(db: AsyncSession, project_id: uuid.UUID) -> list[dict[str, Any]]:
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id == project_id, Milestone.is_active == True)  # noqa: E712
        .order_by(Milestone.sort_order)
    )
    return [_milestone_to_dict(m) for m in result.scalars().all()]


async def create_milestone(
    db: AsyncSession,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    *,
    name: str,
    amount: float,
    planned_delivery_date: date | None = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    await _check_fixed_price(db, project_id)

    if amount <= 0:
        raise ValidationError("Milestone amount must be positive", field="amount")

    milestone = Milestone(
        project_id=project_id,
        name=name,
        amount=amount,
        planned_delivery_date=planned_delivery_date,
        sort_order=sort_order,
        status=MilestoneStatus.PLANNED.value,
    )
    db.add(milestone)
    await db.flush()
    await db.refresh(milestone)

    await audit_log(
        db,
        MILESTONE_ENTITY,
        milestone.id,
        AuditAction.CREATE,
        changes={
            "name": name,
            "amount": amount,
            "planned_delivery_date": (
                planned_delivery_date.isoformat() if planned_delivery_date else None
            ),
            "sort_order": sort_order,
            "status": MilestoneStatus.PLANNED.value,
        },
        user_id=current_user_id,
    )

    return _milestone_to_dict(milestone)


async def update_milestone(
    db: AsyncSession,
    milestone_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    **fields: Any,
) -> dict[str, Any]:
    milestone = await _load_milestone(db, milestone_id, project_id)

    if milestone.status != MilestoneStatus.PLANNED.value:
        raise ValidationError(
            "Milestone can only be edited while in PLANNED status", field="status"
        )

    if "amount" in fields and fields["amount"] is not None and fields["amount"] <= 0:
        raise ValidationError("Milestone amount must be positive", field="amount")

    changes: dict[str, tuple[Any, Any]] = {}
    updatable = {"name", "amount", "planned_delivery_date", "sort_order"}

    for field_name in updatable:
        if field_name not in fields:
            continue
        old_val = getattr(milestone, field_name)
        new_val = fields[field_name]
        if isinstance(old_val, Decimal):
            old_val = float(old_val)
        if isinstance(old_val, date):
            old_val = old_val.isoformat()
        if isinstance(new_val, date):
            new_val = new_val.isoformat()
        if old_val != new_val:
            changes[field_name] = (old_val, new_val)
            setattr(milestone, field_name, fields[field_name])

    if changes:
        await audit_log(
            db,
            MILESTONE_ENTITY,
            milestone.id,
            AuditAction.UPDATE,
            changes=changes,
            user_id=current_user_id,
        )

    await db.flush()
    await db.refresh(milestone)
    return _milestone_to_dict(milestone)


async def transition_milestone_status(
    db: AsyncSession,
    milestone_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    role_code: str,
    new_status: MilestoneStatus,
) -> dict[str, Any]:
    milestone = await _load_milestone(db, milestone_id, project_id)
    old_status = MilestoneStatus(milestone.status)

    is_forward = MILESTONE_FORWARD_TRANSITIONS.get(old_status) == new_status
    is_backward = MILESTONE_BACKWARD_TRANSITIONS.get(old_status) == new_status

    if not is_forward and not is_backward:
        raise ValidationError(
            f"Cannot transition milestone from {old_status.value} to {new_status.value}",
            field="status",
        )

    if (
        old_status.value,
        new_status.value,
    ) in FINANCE_ONLY_TRANSITIONS and role_code not in {"FINANCE", "CEO", "CTO"}:
        raise ForbiddenError()

    changes: dict[str, tuple[Any, Any]] = {"status": (old_status.value, new_status.value)}
    milestone.status = new_status.value

    if new_status == MilestoneStatus.DELIVERED and is_forward:
        today = datetime.now(UTC).date()
        changes["actual_delivery_date"] = (
            milestone.actual_delivery_date.isoformat() if milestone.actual_delivery_date else None,
            today.isoformat(),
        )
        milestone.actual_delivery_date = today

    backward_to_planned = (
        is_backward
        and old_status == MilestoneStatus.DELIVERED
        and new_status == MilestoneStatus.PLANNED
    )
    if backward_to_planned:
        changes["actual_delivery_date"] = (
            milestone.actual_delivery_date.isoformat() if milestone.actual_delivery_date else None,
            None,
        )
        milestone.actual_delivery_date = None

    await audit_log(
        db,
        MILESTONE_ENTITY,
        milestone.id,
        AuditAction.UPDATE,
        changes=changes,
        user_id=current_user_id,
    )

    await db.flush()
    await db.refresh(milestone)
    return _milestone_to_dict(milestone)


async def get_milestone(
    db: AsyncSession, milestone_id: uuid.UUID, project_id: uuid.UUID
) -> dict[str, Any]:
    milestone = await _load_milestone(db, milestone_id, project_id)
    return _milestone_to_dict(milestone)


# ── Invoice CRUD — See FSD §2.9, §6.3 ──


def _invoice_to_dict(invoice: Invoice) -> dict[str, Any]:
    return {
        "id": str(invoice.id),
        "project_id": str(invoice.project_id),
        "milestone_id": str(invoice.milestone_id) if invoice.milestone_id else None,
        "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "amount": float(invoice.amount) if invoice.amount is not None else None,
        "currency": invoice.currency,
        "exchange_rate": float(invoice.exchange_rate) if invoice.exchange_rate is not None else None,
        "amount_inr": float(invoice.amount_inr) if invoice.amount_inr is not None else None,
        "billing_period_start": (
            invoice.billing_period_start.isoformat() if invoice.billing_period_start else None
        ),
        "billing_period_end": (
            invoice.billing_period_end.isoformat() if invoice.billing_period_end else None
        ),
        "status": invoice.status,
        "notes": invoice.notes,
        "is_active": invoice.is_active,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
        "milestone": (
            _milestone_to_dict(invoice.milestone) if invoice.milestone else None
        ),
    }


async def _load_invoice(
    db: AsyncSession, invoice_id: uuid.UUID, project_id: uuid.UUID
) -> Invoice:
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.project_id == project_id,
            Invoice.is_active == True,  # noqa: E712
        )
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise NotFoundError("Invoice", str(invoice_id))
    return invoice


async def list_invoices(
    db: AsyncSession,
    project_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    # See FSD §6.3 — Invoice list with pagination
    query = select(Invoice).where(
        Invoice.project_id == project_id,
        Invoice.is_active == True,  # noqa: E712
    )
    if status:
        query = query.where(Invoice.status == status)

    count_result = await db.execute(
        select(Invoice.id).where(
            Invoice.project_id == project_id,
            Invoice.is_active == True,  # noqa: E712
            *([Invoice.status == status] if status else []),
        )
    )
    total = len(count_result.all())

    query = query.order_by(Invoice.invoice_date.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return [_invoice_to_dict(inv) for inv in result.scalars().all()], total


async def create_invoice(
    db: AsyncSession,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    *,
    invoice_date: date,
    amount: float,
    currency: str,
    exchange_rate: float | None = None,
    milestone_id: str | None = None,
    billing_period_start: date | None = None,
    billing_period_end: date | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    # See FSD §11 — Invoice validations
    if amount <= 0:
        raise ValidationError("Invoice amount must be positive", field="amount")

    if exchange_rate is not None and exchange_rate <= 0:
        raise ValidationError("Exchange rate must be positive", field="exchange_rate")

    # See BUSINESS-RULES.md §7.7 — auto 1.0 for INR
    if currency.upper() == "INR":
        exchange_rate = 1.0
    elif exchange_rate is None:
        raise ValidationError("Exchange rate is required for non-INR currencies", field="exchange_rate")

    amount_inr = round(amount * exchange_rate, 2)

    project = await get_project(db, project_id)

    # See FSD §11 — FP milestone required
    parsed_milestone_id: uuid.UUID | None = None
    if project.type == "FIXED_PRICE":
        if not milestone_id:
            raise ValidationError(
                "Fixed price invoices must be linked to a milestone", field="milestone_id"
            )
        parsed_milestone_id = uuid.UUID(milestone_id)
        milestone = await _load_milestone(db, parsed_milestone_id, project_id)
        if milestone.status != MilestoneStatus.APPROVED.value:
            raise ValidationError(
                "Milestone must be approved before invoicing", field="milestone_id"
            )

    invoice = Invoice(
        project_id=project_id,
        milestone_id=parsed_milestone_id,
        invoice_date=invoice_date,
        amount=amount,
        currency=currency.upper(),
        exchange_rate=exchange_rate,
        amount_inr=amount_inr,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        status=InvoiceStatus.DRAFT.value,
        notes=notes,
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)

    await audit_log(
        db,
        INVOICE_ENTITY,
        invoice.id,
        AuditAction.CREATE,
        changes={
            "invoice_date": invoice_date.isoformat(),
            "amount": amount,
            "currency": currency.upper(),
            "exchange_rate": exchange_rate,
            "amount_inr": amount_inr,
            "milestone_id": milestone_id,
            "status": InvoiceStatus.DRAFT.value,
        },
        user_id=current_user_id,
    )

    return _invoice_to_dict(invoice)


async def update_invoice(
    db: AsyncSession,
    invoice_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    **fields: Any,
) -> dict[str, Any]:
    invoice = await _load_invoice(db, invoice_id, project_id)

    if invoice.status != InvoiceStatus.DRAFT.value:
        raise ValidationError("Invoices can only be edited while in DRAFT status", field="status")

    if "amount" in fields and fields["amount"] is not None and fields["amount"] <= 0:
        raise ValidationError("Invoice amount must be positive", field="amount")

    if "exchange_rate" in fields and fields["exchange_rate"] is not None and fields["exchange_rate"] <= 0:
        raise ValidationError("Exchange rate must be positive", field="exchange_rate")

    changes: dict[str, tuple[Any, Any]] = {}
    updatable = {
        "invoice_date", "amount", "currency", "exchange_rate",
        "milestone_id", "billing_period_start", "billing_period_end", "notes",
    }

    for field_name in updatable:
        if field_name not in fields:
            continue
        old_val = getattr(invoice, field_name)
        new_val = fields[field_name]
        if field_name == "milestone_id" and new_val is not None:
            new_val = uuid.UUID(new_val) if isinstance(new_val, str) else new_val
        if isinstance(old_val, Decimal):
            old_val = float(old_val)
        if isinstance(old_val, (date, uuid.UUID)):
            old_val = str(old_val) if isinstance(old_val, uuid.UUID) else old_val.isoformat()
        if isinstance(new_val, (date, uuid.UUID)):
            new_val = str(new_val) if isinstance(new_val, uuid.UUID) else new_val.isoformat()
        if old_val != new_val:
            changes[field_name] = (old_val, new_val)
            setattr(invoice, field_name, fields[field_name] if field_name != "milestone_id" else (uuid.UUID(fields[field_name]) if fields[field_name] else None))

    # Recompute amount_inr if amount or exchange_rate changed
    curr_amount = float(invoice.amount) if isinstance(invoice.amount, Decimal) else invoice.amount
    curr_rate = float(invoice.exchange_rate) if isinstance(invoice.exchange_rate, Decimal) else invoice.exchange_rate

    if invoice.currency and invoice.currency.upper() == "INR":
        invoice.exchange_rate = 1.0
        curr_rate = 1.0

    new_amount_inr = round(curr_amount * curr_rate, 2)
    old_amount_inr = float(invoice.amount_inr) if isinstance(invoice.amount_inr, Decimal) else invoice.amount_inr
    if abs(new_amount_inr - old_amount_inr) > 0.001:
        changes["amount_inr"] = (old_amount_inr, new_amount_inr)
        invoice.amount_inr = new_amount_inr

    if changes:
        await audit_log(
            db,
            INVOICE_ENTITY,
            invoice.id,
            AuditAction.UPDATE,
            changes=changes,
            user_id=current_user_id,
        )

    await db.flush()
    await db.refresh(invoice)
    return _invoice_to_dict(invoice)


async def _sync_milestone_on_invoice_transition(
    db: AsyncSession,
    invoice: Invoice,
    new_invoice_status: InvoiceStatus,
    current_user_id: uuid.UUID,
) -> None:
    # See FSD §6.3 — SUBMITTED/PAID invoice transitions cascade to milestone status
    target_milestone_status = {
        InvoiceStatus.SUBMITTED: MilestoneStatus.INVOICED,
        InvoiceStatus.PAID: MilestoneStatus.PAID,
    }.get(new_invoice_status)
    if target_milestone_status is None or invoice.milestone_id is None:
        return

    milestone = await _load_milestone(db, invoice.milestone_id, invoice.project_id)
    old_milestone_status = MilestoneStatus(milestone.status)
    if MILESTONE_FORWARD_TRANSITIONS.get(old_milestone_status) != target_milestone_status:
        return

    milestone.status = target_milestone_status.value
    await audit_log(
        db,
        MILESTONE_ENTITY,
        milestone.id,
        AuditAction.UPDATE,
        changes={"status": (old_milestone_status.value, target_milestone_status.value)},
        user_id=current_user_id,
    )


async def transition_invoice_status(
    db: AsyncSession,
    invoice_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    new_status: InvoiceStatus,
) -> dict[str, Any]:
    # See FSD §6.3 — Invoice forward-only transitions
    invoice = await _load_invoice(db, invoice_id, project_id)
    old_status = InvoiceStatus(invoice.status)

    if INVOICE_FORWARD_TRANSITIONS.get(old_status) != new_status:
        raise ValidationError(
            f"Cannot transition invoice from {old_status.value} to {new_status.value}",
            field="status",
        )

    changes: dict[str, tuple[Any, Any]] = {"status": (old_status.value, new_status.value)}
    invoice.status = new_status.value

    await audit_log(
        db,
        INVOICE_ENTITY,
        invoice.id,
        AuditAction.UPDATE,
        changes=changes,
        user_id=current_user_id,
    )

    await _sync_milestone_on_invoice_transition(db, invoice, new_status, current_user_id)

    await db.flush()
    await db.refresh(invoice)
    return _invoice_to_dict(invoice)


async def get_receivables(
    db: AsyncSession,
    status_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    # See FSD §6.3 — Outstanding receivables (status != PAID)
    query = (
        select(Invoice)
        .where(
            Invoice.is_active == True,  # noqa: E712
            Invoice.status != InvoiceStatus.PAID.value,
        )
        .options(selectinload(Invoice.project))
    )
    if status_filter:
        query = query.where(Invoice.status.in_(status_filter))

    query = query.order_by(Invoice.invoice_date.desc())
    result = await db.execute(query)
    invoices = result.scalars().all()

    items = []
    for inv in invoices:
        d = _invoice_to_dict(inv)
        d["project_name"] = inv.project.name if inv.project else None
        d["client_id"] = str(inv.project.client_id) if inv.project and inv.project.client_id else None
        d["client_name"] = inv.project.client.name if inv.project and inv.project.client else None
        items.append(d)
    return items
