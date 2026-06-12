import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import AccessLevel, User
from app.modules.auth.schemas import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.auth.service import (
    create_user,
    get_user_by_id,
    list_users,
    update_user,
)
from app.shared.exceptions import ForbiddenError, NotFoundError
from app.shared.utils import build_pagination_meta

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _require_admin(user: User) -> None:
    # See FSD §10 — CEO/CTO only for user management
    if user.role.code not in ("CEO", "CTO"):
        raise ForbiddenError("Access denied")


def _user_to_list_response(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": {
            "id": user.role.id,
            "code": user.role.code,
            "name": user.role.name,
            "permission_level": user.role.permission_level,
        },
        "resource_id": user.resource_id,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }


@router.get("")
async def list_users_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(current_user)
    users, total = await list_users(db, page=page, limit=limit, status=status, search=search)
    return {
        "data": [_user_to_list_response(u) for u in users],
        "meta": build_pagination_meta(total, page, limit),
    }


@router.post("", status_code=201)
async def create_user_endpoint(
    body: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(current_user)
    user = await create_user(
        db,
        email=body.email,
        name=body.name,
        password=body.password,
        role_id=body.role_id,
        resource_id=body.resource_id,
        current_user_id=current_user.id,
    )
    return {"data": _user_to_list_response(user)}


@router.get("/{user_id}")
async def get_user_endpoint(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(current_user)
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User", str(user_id))
    return {"data": _user_to_list_response(user)}


@router.put("/{user_id}")
async def update_user_endpoint(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(current_user)
    user = await update_user(
        db,
        user_id=user_id,
        current_user_id=current_user.id,
        name=body.name,
        role_id=body.role_id,
        resource_id=body.resource_id,
        is_active=body.is_active,
        password=body.password,
    )
    return {"data": _user_to_list_response(user)}
