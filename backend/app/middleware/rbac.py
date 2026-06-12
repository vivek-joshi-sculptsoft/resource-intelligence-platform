"""RBAC middleware — See FSD §10, shared/ACCESS-MATRIX.md"""
import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import AccessLevel, RolePermission, Scope, User
from app.shared.exceptions import ForbiddenError


@dataclass
class Permission:
    access_level: AccessLevel
    scope: Scope
    data_type: str
    is_configurable: bool


async def get_permission(
    db: AsyncSession, role_id: uuid.UUID, data_type: str
) -> Permission:
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.data_type == data_type,
        )
    )
    rp = result.scalar_one_or_none()
    if rp is None:
        return Permission(
            access_level=AccessLevel.NONE,
            scope=Scope.ALL,
            data_type=data_type,
            is_configurable=False,
        )
    return Permission(
        access_level=rp.access_level,
        scope=rp.scope,
        data_type=rp.data_type,
        is_configurable=rp.is_configurable,
    )


_LEVEL_ORDER = {AccessLevel.NONE: 0, AccessLevel.VIEW: 1, AccessLevel.EDIT: 2}


def require_access(data_type: str, min_level: AccessLevel = AccessLevel.VIEW):
    # See FSD §10 — Runtime Access Check Algorithm
    async def checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Permission:
        permission = await get_permission(db, current_user.role_id, data_type)
        if _LEVEL_ORDER[permission.access_level] < _LEVEL_ORDER[min_level]:
            raise ForbiddenError("Access denied")
        return permission

    return Depends(checker)


def require_write_access(data_type: str):
    return require_access(data_type, min_level=AccessLevel.EDIT)


def apply_scope_filter(query, permission: Permission, user: User, model=None):
    """Apply scope-based WHERE clause. See FSD §10 — Scope Rules."""
    if permission.scope == Scope.ALL:
        return query

    if permission.scope == Scope.SELF_ONLY:
        if model and hasattr(model, "resource_id"):
            return query.where(model.resource_id == user.resource_id)
        return query

    if permission.scope == Scope.OWN_PORTFOLIO:
        if model and hasattr(model, "dm_id") and hasattr(model, "pm_id"):
            return query.where(
                (model.dm_id == user.resource_id) | (model.pm_id == user.resource_id)
            )
        return query

    return query


SENSITIVE_FIELD_MAP: dict[str, list[str]] = {
    "ctc_loaded_cost": ["loaded_cost_monthly"],
    "billing_rates": ["billing_rate"],
    "billability": ["billability_pct"],
    "project_margin": [
        "projected_margin",
        "actual_margin",
        "margin_pct",
        "projected_revenue",
        "actual_revenue",
    ],
    "shadow_assignments": ["is_shadow"],
}

SENSITIVE_FIELD_VISIBLE_ROLES = {
    "loaded_cost_monthly": {"CEO", "CTO", "FINANCE"},
    "billing_rate": {"CEO", "CTO", "FINANCE", "DM"},
    "billability_pct": {"CEO", "CTO", "FINANCE", "DM", "PM"},
    "is_shadow": {"CEO", "CTO", "FINANCE", "DM", "PM"},
    "projected_margin": {"CEO", "CTO", "FINANCE", "DM"},
    "actual_margin": {"CEO", "CTO", "FINANCE", "DM"},
    "margin_pct": {"CEO", "CTO", "FINANCE", "DM"},
    "projected_revenue": {"CEO", "CTO", "FINANCE", "DM"},
    "actual_revenue": {"CEO", "CTO", "FINANCE", "DM"},
    "exchange_rate": {"CEO", "CTO", "FINANCE"},
}


def null_restricted_fields(
    data: dict[str, Any],
    role_code: str,
) -> dict[str, Any]:
    """Set sensitive fields to null for unauthorized roles. See FSD §10 — Field-Level Restrictions."""
    for field, allowed_roles in SENSITIVE_FIELD_VISIBLE_ROLES.items():
        if field in data and role_code not in allowed_roles:
            data[field] = None
    return data


def null_restricted_fields_list(
    items: list[dict[str, Any]],
    role_code: str,
) -> list[dict[str, Any]]:
    return [null_restricted_fields(item, role_code) for item in items]
