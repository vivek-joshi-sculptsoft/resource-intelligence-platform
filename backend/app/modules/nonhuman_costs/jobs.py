"""See FSD §2.10 — Recurring cost processing scheduled job."""

import logging
import uuid
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.nonhuman_costs.models import NonHumanCost

logger = logging.getLogger(__name__)

SYSTEM_USER_ID = uuid.UUID(int=0)


async def run_process_recurring_costs(db: AsyncSession) -> dict:
    """See JOBS.md — Process all active recurring costs, creating monthly snapshots."""
    today = date.today()
    current_month_start = today.replace(day=1)

    result = await db.execute(
        select(NonHumanCost).where(
            NonHumanCost.is_recurring == True,  # noqa: E712
            NonHumanCost.is_active == True,  # noqa: E712
            NonHumanCost.cost_date <= today,
            NonHumanCost.recurring_end_date >= today,
        )
    )
    candidates = list(result.scalars().all())

    created_count = 0
    skipped_count = 0
    error_count = 0

    for parent_cost in candidates:
        try:
            existing = await db.execute(
                select(NonHumanCost).where(
                    and_(
                        NonHumanCost.project_id == parent_cost.project_id,
                        NonHumanCost.description == parent_cost.description,
                        NonHumanCost.category == parent_cost.category,
                        NonHumanCost.cost_date == current_month_start,
                        NonHumanCost.amount == parent_cost.amount,
                        NonHumanCost.currency == parent_cost.currency,
                        NonHumanCost.is_active == True,  # noqa: E712
                    )
                )
            )
            if existing.scalar_one_or_none() is not None:
                logger.info(
                    "Skipping duplicate for project %s, cost '%s' for %s",
                    parent_cost.project_id,
                    parent_cost.description,
                    current_month_start,
                )
                skipped_count += 1
                continue

            # See BUSINESS-RULES §7.7 — amount_inr = amount × exchange_rate
            amount_inr = float(parent_cost.amount) * float(parent_cost.exchange_rate)

            new_cost = NonHumanCost(
                id=uuid.uuid4(),
                project_id=parent_cost.project_id,
                description=parent_cost.description,
                category=parent_cost.category,
                amount=parent_cost.amount,
                currency=parent_cost.currency,
                exchange_rate=parent_cost.exchange_rate,
                amount_inr=amount_inr,
                cost_date=current_month_start,
                is_recurring=False,
                recurring_end_date=None,
                created_by=None,
            )
            db.add(new_cost)
            await db.flush()
            await db.refresh(new_cost)

            await audit_log(
                db,
                entity_type="NonHumanCost",
                entity_id=new_cost.id,
                action=AuditAction.CREATE,
                changes={
                    "description": new_cost.description,
                    "category": new_cost.category,
                    "amount": float(new_cost.amount),
                    "currency": new_cost.currency,
                    "exchange_rate": float(new_cost.exchange_rate),
                    "amount_inr": amount_inr,
                    "cost_date": current_month_start.isoformat(),
                    "source": f"recurring_from_{parent_cost.id}",
                },
                user_id=SYSTEM_USER_ID,
            )

            created_count += 1

        except Exception:
            logger.exception(
                "Failed to process recurring cost %s for project %s",
                parent_cost.id,
                parent_cost.project_id,
            )
            error_count += 1
            continue

    logger.info(
        "Recurring cost processing completed. Created %d, skipped %d, errors %d from %d templates.",
        created_count,
        skipped_count,
        error_count,
        len(candidates),
    )

    return {
        "candidates": len(candidates),
        "created": created_count,
        "skipped": skipped_count,
        "errors": error_count,
    }
