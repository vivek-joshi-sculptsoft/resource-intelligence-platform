import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.modules.auth.jwt import decode_access_token
from app.modules.auth.models import User
from app.modules.auth.service import get_active_user_by_id
from app.shared.exceptions import UnauthorizedError


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise UnauthorizedError("Not authenticated")

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    return await get_active_user_by_id(db, uuid.UUID(payload["sub"]))
