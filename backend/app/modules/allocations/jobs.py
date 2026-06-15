"""See FSD §8 — Auto-release scheduled job."""

import logging
import uuid
from datetime import UTC, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.allocations.models import Assignment
from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log

logger = logging.getLogger(__name__)

SYSTEM_USER_ID = uuid.UUID(int=0)


async def run_auto_release(db: AsyncSession) -> list[dict]:
    """See FSD §8 — Process all ACTIVE assignments where end_date <= today."""
    from datetime import date as date_type

    today = date_type.today()

    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.resource), selectinload(Assignment.project))
        .where(
            Assignment.status == "ACTIVE",
            Assignment.end_date.isnot(None),
            Assignment.end_date <= today,
        )
    )
    candidates = list(result.scalars().all())
    released: list[dict] = []

    for assignment in candidates:
        try:
            released_at = datetime.combine(assignment.end_date, time(23, 59, 59), tzinfo=UTC)
            old_status = assignment.status
            assignment.status = "AUTO_RELEASED"
            assignment.released_at = released_at

            await audit_log(
                db,
                entity_type="assignment",
                entity_id=assignment.id,
                action=AuditAction.UPDATE,
                changes={
                    "status": (old_status, "AUTO_RELEASED"),
                    "released_at": (None, released_at.isoformat()),
                },
                user_id=SYSTEM_USER_ID,
            )

            resource_name = assignment.resource.name if assignment.resource else "Unknown"
            project_name = assignment.project.name if assignment.project else "Unknown"

            released.append(
                {
                    "id": str(assignment.id),
                    "resource_name": resource_name,
                    "project_name": project_name,
                }
            )

            logger.info(
                "Auto-released assignment %s: %s from %s",
                assignment.id,
                resource_name,
                project_name,
            )

        except Exception:
            logger.exception("Failed to auto-release assignment %s", assignment.id)
            continue

    if released:
        await db.flush()

    logger.info("Auto-release job completed. Processed %d assignments.", len(released))
    return released
