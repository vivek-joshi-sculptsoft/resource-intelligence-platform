import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import PermissionResponse, RoleDetailResponse
from app.modules.auth.service import get_role_by_id, get_role_permissions, get_roles_with_permissions
from app.shared.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/api/v1/roles", tags=["roles"])


def _require_admin(user: User) -> None:
    if user.role.code not in ("CEO", "CTO"):
        raise ForbiddenError("Access denied")


def _role_to_detail(role) -> dict:
    return {
        "id": role.id,
        "code": role.code,
        "name": role.name,
        "permission_level": role.permission_level,
        "is_active": role.is_active,
        "permissions": [
            {
                "data_type": p.data_type,
                "access_level": p.access_level.value,
                "scope": p.scope.value,
                "is_configurable": p.is_configurable,
            }
            for p in role.permissions
        ],
    }


@router.get("")
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(current_user)
    roles = await get_roles_with_permissions(db)
    return {"data": [_role_to_detail(r) for r in roles]}


@router.get("/{role_id}")
async def get_role(
    role_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(current_user)
    role = await get_role_by_id(db, role_id)
    if role is None:
        raise NotFoundError("Role", str(role_id))
    return {"data": _role_to_detail(role)}


@router.get("/{role_id}/permissions")
async def get_role_permissions_endpoint(
    role_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(current_user)
    permissions = await get_role_permissions(db, role_id)
    return {
        "data": [
            {
                "data_type": p.data_type,
                "access_level": p.access_level.value,
                "scope": p.scope.value,
                "is_configurable": p.is_configurable,
            }
            for p in permissions
        ]
    }
