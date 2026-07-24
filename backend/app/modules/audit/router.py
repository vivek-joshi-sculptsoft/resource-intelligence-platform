"""Audit Log query endpoints. See FSD §13 and modules/13-audit-history/API.md."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.audit.schemas import AuditLogResponse
from app.modules.audit.service import get_entity_audit_logs, query_audit_logs
from app.modules.auth.models import User
from app.shared.access_control import Permission, check_access
from app.shared.exceptions import ForbiddenError
from app.shared.utils import build_pagination_meta

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit"])

ALLOWED_ROLES = {"CEO", "CTO", "DM", "PM"}


async def _check_audit_access(
    db: AsyncSession, user: User
) -> Permission:
    """CEO/CTO see ALL, DM/PM see OWN_PORTFOLIO, others get 403. See FSD §13."""
    from app.modules.auth.models import AccessLevel, Scope
    from sqlalchemy import select
    from app.modules.auth.models import Role

    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one()

    if role.code not in ALLOWED_ROLES:
        raise ForbiddenError()

    if role.code in ("CEO", "CTO"):
        return Permission(access_level=AccessLevel.VIEW, scope=Scope.ALL)
    return Permission(access_level=AccessLevel.VIEW, scope=Scope.OWN_PORTFOLIO)


@router.get("")
async def list_audit_logs(
    entity_type: str | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    changed_by: uuid.UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await _check_audit_access(db, current_user)

    items, total = await query_audit_logs(
        db,
        permission=permission,
        current_user=current_user,
        page=page,
        limit=limit,
        entity_type=entity_type,
        entity_id=entity_id,
        changed_by_id=changed_by,
        start_date=start_date,
        end_date=end_date,
        sort_order=sort,
    )

    return {
        "data": [item.model_dump(mode="json") for item in items],
        "meta": build_pagination_meta(total, page, limit),
    }


@router.get("/{entity_type}/{entity_id}")
async def get_entity_history(
    entity_type: str,
    entity_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await _check_audit_access(db, current_user)

    # See FSD §10 — OWN_PORTFOLIO: verify entity is in user's portfolio
    if permission.is_own_portfolio:
        from app.modules.audit.service import _get_portfolio_entity_ids, _get_portfolio_resource_ids

        if current_user.resource_id:
            visible = await _get_portfolio_entity_ids(db, current_user.resource_id)
            resource_ids = await _get_portfolio_resource_ids(db, current_user.resource_id)
            if str(entity_id) not in visible and str(entity_id) not in resource_ids:
                raise ForbiddenError()
        else:
            raise ForbiddenError()

    items, total = await get_entity_audit_logs(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        page=page,
        limit=limit,
    )

    return {
        "data": [item.model_dump(mode="json") for item in items],
        "meta": build_pagination_meta(total, page, limit),
    }
