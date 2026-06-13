import os
import uuid

from fastapi import APIRouter, Depends, Request, Response
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.modules.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.modules.auth.schemas import LoginRequest, LoginResponse, RoleResponse, UserResponse
from app.modules.auth.service import authenticate_user, get_active_user_by_id
from app.shared.exceptions import UnauthorizedError

limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("TESTING") != "1",
)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _set_token_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    common = {
        "httponly": True,
        "samesite": "strict",
        "secure": not settings.DEBUG,
        "path": "/",
    }
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **common,
    )


def _clear_token_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def _build_user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=RoleResponse(
            id=user.role.id,
            code=user.role.code,
            name=user.role.name,
            permission_level=user.role.permission_level,
        ),
        resource_id=user.resource_id,
    )


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    user = await authenticate_user(db, body.email, body.password)

    access_token = create_access_token(user.id, user.role.code, user.role_id, user.resource_id)
    refresh_token = create_refresh_token(user.id)
    _set_token_cookies(response, access_token, refresh_token)

    return LoginResponse(user=_build_user_response(user))


@router.post("/logout")
async def logout(response: Response) -> dict:
    _clear_token_cookies(response)
    return {"success": True}


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise UnauthorizedError("No refresh token")

    try:
        payload = decode_refresh_token(token)
    except JWTError as err:
        _clear_token_cookies(response)
        raise UnauthorizedError("Invalid refresh token") from err

    user = await get_active_user_by_id(db, uuid.UUID(payload["sub"]))

    access_token = create_access_token(user.id, user.role.code, user.role_id, user.resource_id)
    new_refresh_token = create_refresh_token(user.id)
    _set_token_cookies(response, access_token, new_refresh_token)

    return LoginResponse(user=_build_user_response(user))


@router.get("/me")
async def me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise UnauthorizedError("Not authenticated")

    try:
        payload = decode_access_token(token)
    except JWTError as err:
        raise UnauthorizedError("Invalid or expired token") from err

    user = await get_active_user_by_id(db, uuid.UUID(payload["sub"]))
    return _build_user_response(user)
