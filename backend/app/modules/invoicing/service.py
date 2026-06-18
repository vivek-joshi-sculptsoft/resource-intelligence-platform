"""See FSD §2.8, §6.2 — Milestone business logic."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.invoicing.models import Milestone
from app.modules.invoicing.schemas import (
    FINANCE_ONLY_TRANSITIONS,
    MILESTONE_BACKWARD_TRANSITIONS,
    MILESTONE_FORWARD_TRANSITIONS,
    MilestoneStatus,
)
from app.modules.projects.service import get_project
from app.shared.exceptions import ForbiddenError, NotFoundError, ValidationError

ENTITY_TYPE = "Milestone"


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
        ENTITY_TYPE,
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
            ENTITY_TYPE,
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
        ENTITY_TYPE,
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
