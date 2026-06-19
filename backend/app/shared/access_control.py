"""
Shared access control utility.
See FSD §10 — Runtime Access Check Algorithm.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import AccessLevel, RolePermission, Scope, User
from app.shared.exceptions import ForbiddenError


class Permission:
    """Result of an access check — carries scope for downstream query filtering."""

    def __init__(self, access_level: AccessLevel, scope: Scope):
        self.access_level = access_level
        self.scope = scope

    @property
    def can_edit(self) -> bool:
        return self.access_level == AccessLevel.EDIT

    @property
    def can_view(self) -> bool:
        return self.access_level in (AccessLevel.VIEW, AccessLevel.EDIT)

    @property
    def is_all(self) -> bool:
        return self.scope == Scope.ALL

    @property
    def is_own_portfolio(self) -> bool:
        return self.scope == Scope.OWN_PORTFOLIO

    @property
    def is_self_only(self) -> bool:
        return self.scope == Scope.SELF_ONLY


async def check_access(
    db: AsyncSession,
    user: User,
    data_type: str,
    require_edit: bool = False,
) -> Permission:
    # See FSD §10 — Runtime Access Check Algorithm
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == user.role_id,
            RolePermission.data_type == data_type,
        )
    )
    perm = result.scalar_one_or_none()

    if perm is None or perm.access_level == AccessLevel.NONE:
        raise ForbiddenError()

    if require_edit and perm.access_level != AccessLevel.EDIT:
        raise ForbiddenError()

    return Permission(access_level=perm.access_level, scope=perm.scope)


async def has_access(db: AsyncSession, user: User, data_type: str) -> bool:
    """Non-raising variant of check_access — for field-level masking decisions."""
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == user.role_id,
            RolePermission.data_type == data_type,
        )
    )
    perm = result.scalar_one_or_none()
    return perm is not None and perm.access_level != AccessLevel.NONE


def can_see_field(role_code: str, field: str) -> bool:
    """Check if a role can see a restricted field. See FSD §10 — Field-Level Restrictions."""
    restrictions: dict[str, set[str]] = {
        "loaded_cost_monthly": {"CEO", "CTO", "FINANCE"},
        "billing_rate": {"CEO", "CTO", "FINANCE", "DM"},
        "billability_pct": {"CEO", "CTO", "FINANCE", "DM", "PM"},
        "is_shadow": {"CEO", "CTO", "FINANCE", "DM", "PM"},
    }
    allowed = restrictions.get(field)
    if allowed is None:
        return True
    return role_code in allowed
