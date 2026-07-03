import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log
from app.modules.auth.models import Role, RolePermission, User
from app.shared.exceptions import (
    AppError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)

ph = PasswordHasher()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        ph.hash("dummy-to-prevent-timing-attack")
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    try:
        ph.verify(user.password_hash, password)
    except VerifyMismatchError as err:
        raise UnauthorizedError("Invalid email or password") from err

    if ph.check_needs_rehash(user.password_hash):
        user.password_hash = ph.hash(password)

    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.role), selectinload(User.resource)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_active_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    return user


async def list_users(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[User], int]:
    query = select(User).options(selectinload(User.role), selectinload(User.resource))
    count_query = select(func.count()).select_from(User)

    if status == "ACTIVE":
        query = query.where(User.is_active.is_(True))
        count_query = count_query.where(User.is_active.is_(True))
    elif status == "INACTIVE":
        query = query.where(User.is_active.is_(False))
        count_query = count_query.where(User.is_active.is_(False))

    if search:
        like_pattern = f"%{search}%"
        search_filter = User.name.ilike(like_pattern) | User.email.ilike(like_pattern)
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    users = list(result.scalars().all())

    return users, total


async def create_user(
    db: AsyncSession,
    email: str,
    name: str,
    password: str,
    role_id: uuid.UUID,
    resource_id: uuid.UUID | None,
    current_user_id: uuid.UUID,
) -> User:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise ConflictError("Email is already in use", field="email")

    role = await db.execute(select(Role).where(Role.id == role_id))
    if role.scalar_one_or_none() is None:
        raise NotFoundError("Role", str(role_id))

    user = User(
        id=uuid.uuid4(),
        email=email,
        name=name,
        password_hash=ph.hash(password),
        role_id=role_id,
        resource_id=resource_id,
    )
    db.add(user)
    await db.flush()

    await audit_log(
        db,
        entity_type="user",
        entity_id=user.id,
        action=AuditAction.CREATE,
        changes={"email": email, "name": name, "role_id": str(role_id)},
        user_id=current_user_id,
    )

    result = await db.execute(
        select(User).options(selectinload(User.role), selectinload(User.resource)).where(User.id == user.id)
    )
    return result.scalar_one()


async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    current_user_id: uuid.UUID,
    name: str | None = None,
    role_id: uuid.UUID | None = None,
    resource_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    password: str | None = None,
) -> User:
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User", str(user_id))

    changes: dict[str, tuple] = {}

    if name is not None and name != user.name:
        changes["name"] = (user.name, name)
        user.name = name

    if role_id is not None and role_id != user.role_id:
        role = await db.execute(select(Role).where(Role.id == role_id))
        if role.scalar_one_or_none() is None:
            raise NotFoundError("Role", str(role_id))
        changes["role_id"] = (str(user.role_id), str(role_id))
        user.role_id = role_id

    if resource_id is not None:
        old_val = str(user.resource_id) if user.resource_id else None
        new_val = str(resource_id) if resource_id else None
        if old_val != new_val:
            changes["resource_id"] = (old_val, new_val)
            user.resource_id = resource_id

    if is_active is not None and is_active != user.is_active:
        if not is_active:
            await _check_last_admin(db, user)
        changes["is_active"] = (user.is_active, is_active)
        user.is_active = is_active

    if password is not None:
        user.password_hash = ph.hash(password)
        changes["password"] = ("***", "***")

    if changes:
        await audit_log(
            db,
            entity_type="user",
            entity_id=user.id,
            action=AuditAction.UPDATE,
            changes=changes,
            user_id=current_user_id,
        )

    await db.flush()

    result = await db.execute(
        select(User).options(selectinload(User.role), selectinload(User.resource)).where(User.id == user.id)
    )
    return result.scalar_one()


async def _check_last_admin(db: AsyncSession, user: User) -> None:
    admin_roles = await db.execute(select(Role.id).where(Role.code.in_(["CEO", "CTO"])))
    admin_role_ids = [r.id for r in admin_roles.all()]

    active_admins = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.role_id.in_(admin_role_ids),
            User.is_active.is_(True),
            User.id != user.id,
        )
    )
    count = active_admins.scalar() or 0
    if count == 0:
        raise AppError(
            "Cannot deactivate the last active admin user",
            status_code=400,
        )


async def get_roles_with_permissions(db: AsyncSession) -> list[Role]:
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).order_by(Role.permission_level.desc())
    )
    return list(result.scalars().all())


async def get_role_by_id(db: AsyncSession, role_id: uuid.UUID) -> Role | None:
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    )
    return result.scalar_one_or_none()


async def get_role_permissions(db: AsyncSession, role_id: uuid.UUID) -> list[RolePermission]:
    role = await db.execute(select(Role).where(Role.id == role_id))
    if role.scalar_one_or_none() is None:
        raise NotFoundError("Role", str(role_id))

    result = await db.execute(select(RolePermission).where(RolePermission.role_id == role_id))
    return list(result.scalars().all())
