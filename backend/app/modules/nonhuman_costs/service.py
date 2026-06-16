"""See FSD §2.10 — NonHumanCost business logic."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.nonhuman_costs.models import NonHumanCost
from app.modules.nonhuman_costs.schemas import CostCategory
from app.modules.projects.models import Project
from app.shared.exceptions import NotFoundError, ValidationError

ENTITY_TYPE = "NonHumanCost"
VALID_CATEGORIES = {c.value for c in CostCategory}


def _validate_cost_fields(
    amount: float | None,
    exchange_rate: float | None,
    currency: str | None,
    is_recurring: bool | None,
    recurring_end_date: date | None,
    cost_date: date | None,
) -> float:
    """Validate NonHumanCost fields per FSD §11. Returns resolved exchange_rate."""
    if amount is not None and amount <= 0:
        raise ValidationError("Cost amount must be positive", field="amount")

    # See FSD §11 — INR auto-rate
    resolved_rate = exchange_rate
    if currency == "INR":
        resolved_rate = 1.0
    elif resolved_rate is not None and resolved_rate <= 0:
        raise ValidationError("Exchange rate must be positive", field="exchange_rate")

    if is_recurring and recurring_end_date is None:
        raise ValidationError("Recurring costs must have an end date", field="recurring_end_date")

    if recurring_end_date is not None and cost_date is not None and recurring_end_date <= cost_date:
        raise ValidationError(
            "Recurring end date must be after cost date", field="recurring_end_date"
        )

    return resolved_rate if resolved_rate is not None else 1.0


def _cost_to_dict(cost: NonHumanCost) -> dict[str, Any]:
    return {
        "id": str(cost.id),
        "project_id": str(cost.project_id),
        "description": cost.description,
        "category": cost.category,
        "amount": float(cost.amount) if cost.amount is not None else None,
        "currency": cost.currency,
        "exchange_rate": float(cost.exchange_rate) if cost.exchange_rate is not None else None,
        "amount_inr": float(cost.amount_inr) if cost.amount_inr is not None else None,
        "cost_date": cost.cost_date.isoformat() if cost.cost_date else None,
        "is_recurring": cost.is_recurring,
        "recurring_end_date": (
            cost.recurring_end_date.isoformat() if cost.recurring_end_date else None
        ),
        "created_by": (
            {"id": str(cost.creator.id), "name": cost.creator.name} if cost.creator else None
        ),
        "is_active": cost.is_active,
        "created_at": cost.created_at.isoformat() if cost.created_at else None,
        "updated_at": cost.updated_at.isoformat() if cost.updated_at else None,
    }


async def _load_cost(db: AsyncSession, cost_id: uuid.UUID, project_id: uuid.UUID) -> NonHumanCost:
    result = await db.execute(
        select(NonHumanCost).where(
            NonHumanCost.id == cost_id,
            NonHumanCost.project_id == project_id,
            NonHumanCost.is_active == True,  # noqa: E712
        )
    )
    cost = result.scalar_one_or_none()
    if cost is None:
        raise NotFoundError("NonHumanCost", str(cost_id))
    return cost


async def _check_project_exists(db: AsyncSession, project_id: uuid.UUID) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", str(project_id))
    return project


async def create_cost(
    db: AsyncSession,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    *,
    description: str,
    category: str,
    amount: float,
    currency: str = "INR",
    exchange_rate: float | None = None,
    cost_date: date,
    is_recurring: bool = False,
    recurring_end_date: date | None = None,
) -> dict[str, Any]:
    await _check_project_exists(db, project_id)

    if category not in VALID_CATEGORIES:
        raise ValidationError(f"Invalid category: {category}", field="category")

    resolved_rate = _validate_cost_fields(
        amount, exchange_rate, currency, is_recurring, recurring_end_date, cost_date
    )

    # See BUSINESS-RULES §7.7 — amount_inr = amount × exchange_rate
    amount_inr = amount * resolved_rate

    cost = NonHumanCost(
        project_id=project_id,
        description=description,
        category=category,
        amount=amount,
        currency=currency.upper(),
        exchange_rate=resolved_rate,
        amount_inr=amount_inr,
        cost_date=cost_date,
        is_recurring=is_recurring,
        recurring_end_date=recurring_end_date,
        created_by=current_user_id,
    )
    db.add(cost)
    await db.flush()
    await db.refresh(cost)

    create_data = {
        "description": description,
        "category": category,
        "amount": amount,
        "currency": currency.upper(),
        "exchange_rate": resolved_rate,
        "amount_inr": amount_inr,
        "cost_date": cost_date.isoformat(),
        "is_recurring": is_recurring,
        "recurring_end_date": recurring_end_date.isoformat() if recurring_end_date else None,
    }
    await audit_log(
        db, ENTITY_TYPE, cost.id, AuditAction.CREATE, changes=create_data, user_id=current_user_id
    )

    return _cost_to_dict(cost)


async def update_cost(
    db: AsyncSession,
    cost_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
    **fields: Any,
) -> dict[str, Any]:
    cost = await _load_cost(db, cost_id, project_id)

    changes: dict[str, tuple[Any, Any]] = {}
    amount = fields.get("amount", cost.amount)
    currency = fields.get("currency", cost.currency)
    exchange_rate = fields.get("exchange_rate", cost.exchange_rate)
    is_recurring = fields.get("is_recurring", cost.is_recurring)
    recurring_end_date = fields.get("recurring_end_date", cost.recurring_end_date)
    cost_date = fields.get("cost_date", cost.cost_date)

    resolved_rate = _validate_cost_fields(
        float(amount) if amount is not None else None,
        float(exchange_rate) if exchange_rate is not None else None,
        currency,
        is_recurring,
        recurring_end_date,
        cost_date,
    )

    updatable = {
        "description",
        "category",
        "amount",
        "currency",
        "cost_date",
        "is_recurring",
        "recurring_end_date",
    }

    for field_name in updatable:
        if field_name not in fields:
            continue
        old_val = getattr(cost, field_name)
        new_val = fields[field_name]
        if isinstance(old_val, Decimal):
            old_val = float(old_val)
        if isinstance(old_val, date):
            old_val = old_val.isoformat()
        if isinstance(new_val, date):
            new_val = new_val.isoformat()
        if old_val != new_val:
            changes[field_name] = (old_val, new_val)
            setattr(cost, field_name, fields[field_name])

    if "category" in fields and fields["category"] not in VALID_CATEGORIES:
        raise ValidationError(f"Invalid category: {fields['category']}", field="category")

    # Recompute exchange_rate and amount_inr
    old_rate = (
        float(cost.exchange_rate) if isinstance(cost.exchange_rate, Decimal) else cost.exchange_rate
    )
    if old_rate != resolved_rate:
        changes["exchange_rate"] = (old_rate, resolved_rate)
        cost.exchange_rate = resolved_rate

    # See BUSINESS-RULES §7.7
    new_amount_inr = float(cost.amount) * resolved_rate
    old_amount_inr = (
        float(cost.amount_inr) if isinstance(cost.amount_inr, Decimal) else cost.amount_inr
    )
    if old_amount_inr != new_amount_inr:
        changes["amount_inr"] = (old_amount_inr, new_amount_inr)
        cost.amount_inr = new_amount_inr

    if changes:
        await audit_log(
            db, ENTITY_TYPE, cost.id, AuditAction.UPDATE, changes=changes, user_id=current_user_id
        )

    await db.flush()
    await db.refresh(cost)
    return _cost_to_dict(cost)


async def delete_cost(
    db: AsyncSession,
    cost_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user_id: uuid.UUID,
) -> None:
    cost = await _load_cost(db, cost_id, project_id)
    cost.is_active = False

    await audit_log(
        db,
        ENTITY_TYPE,
        cost.id,
        AuditAction.DELETE,
        changes={"description": cost.description, "amount_inr": float(cost.amount_inr)},
        user_id=current_user_id,
    )
    await db.flush()


async def get_cost(
    db: AsyncSession,
    cost_id: uuid.UUID,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    cost = await _load_cost(db, cost_id, project_id)
    return _cost_to_dict(cost)


async def list_costs(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    category: str | None = None,
    is_recurring: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    query = select(NonHumanCost).where(
        NonHumanCost.project_id == project_id,
        NonHumanCost.is_active == True,  # noqa: E712
    )

    if category is not None:
        query = query.where(NonHumanCost.category == category)
    if is_recurring is not None:
        query = query.where(NonHumanCost.is_recurring == is_recurring)
    if date_from is not None:
        query = query.where(NonHumanCost.cost_date >= date_from)
    if date_to is not None:
        query = query.where(NonHumanCost.cost_date <= date_to)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(NonHumanCost.cost_date.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    costs = result.scalars().all()

    return {
        "data": [_cost_to_dict(c) for c in costs],
        "total": total,
        "page": page,
        "limit": limit,
    }


async def get_cost_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """See API.md — aggregated cost summary by category and recurring type."""
    base = select(NonHumanCost).where(
        NonHumanCost.project_id == project_id,
        NonHumanCost.is_active == True,  # noqa: E712
    )
    result = await db.execute(base)
    costs = result.scalars().all()

    total_inr = 0.0
    one_time_inr = 0.0
    recurring_monthly_inr = 0.0
    by_category: dict[str, float] = {}

    for c in costs:
        amt = float(c.amount_inr)
        total_inr += amt
        cat = c.category
        by_category[cat] = by_category.get(cat, 0.0) + amt
        if c.is_recurring:
            recurring_monthly_inr += amt
        else:
            one_time_inr += amt

    return {
        "total_inr": round(total_inr, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "one_time_inr": round(one_time_inr, 2),
        "recurring_monthly_inr": round(recurring_monthly_inr, 2),
    }
