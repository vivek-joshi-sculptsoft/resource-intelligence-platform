import asyncio
import os
import uuid

os.environ["TESTING"] = "1"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.modules.allocations.models import Assignment  # noqa: F401
from app.modules.audit.models import AuditLog  # noqa: F401
from app.modules.auth.models import Role, User
from app.modules.auth.seed import seed_all
from app.modules.clients.models import Client  # noqa: F401
from app.modules.projects.models import Project  # noqa: F401
from app.modules.resources.models import Resource, ResourceTag  # noqa: F401
from app.modules.worklogs.models import Worklog  # noqa: F401
from app.shared.models import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        await seed_all(session)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db():
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def client():
    from app.dependencies import get_db
    from app.main import app

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def db():
    async with test_session_factory() as session:
        yield session


async def login_as(client: AsyncClient, email: str = "admin@ri-platform.com", password: str = "ChangeMe123!") -> AsyncClient:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return client


async def create_test_user(
    db: AsyncSession,
    role_code: str,
    email: str | None = None,
    name: str = "Test User",
) -> User:
    from argon2 import PasswordHasher
    from sqlalchemy import select

    ph = PasswordHasher()
    role_result = await db.execute(select(Role).where(Role.code == role_code))
    role = role_result.scalar_one()

    user = User(
        id=uuid.uuid4(),
        email=email or f"{role_code.lower()}-{uuid.uuid4().hex[:6]}@test.com",
        name=name,
        password_hash=ph.hash("TestPass123"),
        role_id=role.id,
    )
    db.add(user)
    await db.commit()
    return user


async def login_as_role(client: AsyncClient, db: AsyncSession, role_code: str) -> tuple[AsyncClient, User]:
    user = await create_test_user(db, role_code)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "TestPass123"},
    )
    assert resp.status_code == 200
    return client, user
