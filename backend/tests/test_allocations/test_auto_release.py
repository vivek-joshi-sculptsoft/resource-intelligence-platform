"""Tests for auto-release job — VRIP-52."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.jobs import run_auto_release
from app.modules.allocations.models import Assignment
from app.modules.audit.models import AuditLog
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from tests.conftest import create_test_user, login_as


async def _create_resource(db: AsyncSession, name: str) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name=name,
        designation="Developer",
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


async def _create_project_with_assignment(
    db: AsyncSession,
    end_date: date | None,
    dm: Resource,
    pm: Resource,
    dev: Resource,
    client_entity: Client,
) -> Assignment:
    proj = Project(
        id=uuid.uuid4(),
        name=f"Proj-{uuid.uuid4().hex[:6]}",
        client_id=client_entity.id,
        type="FIXED_PRICE",
        dm_id=dm.id,
        pm_id=pm.id,
    )
    db.add(proj)
    await db.flush()

    assignment = Assignment(
        id=uuid.uuid4(),
        project_id=proj.id,
        resource_id=dev.id,
        allocation_pct=50,
        billability_pct=40,
        start_date=date.today() - timedelta(days=30),
        end_date=end_date,
        status="ACTIVE",
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def _setup(db: AsyncSession) -> tuple[Client, Resource, Resource, Resource]:
    cl = Client(id=uuid.uuid4(), name=f"Client-{uuid.uuid4().hex[:6]}")
    db.add(cl)
    dm = await _create_resource(db, "DM")
    pm = await _create_resource(db, "PM")
    dev = await _create_resource(db, "Dev")
    await db.commit()
    await db.refresh(cl)
    return cl, dm, pm, dev


# ── Core auto-release behavior ──────────────────────────


@pytest.mark.asyncio
async def test_auto_release_expired_yesterday(db: AsyncSession):
    cl, dm, pm, dev = await _setup(db)
    yesterday = date.today() - timedelta(days=1)
    assignment = await _create_project_with_assignment(db, yesterday, dm, pm, dev, cl)

    released = await run_auto_release(db)
    assert len(released) == 1
    assert released[0]["id"] == str(assignment.id)

    await db.refresh(assignment)
    assert assignment.status == "AUTO_RELEASED"
    # SQLite strips tz info — compare naive
    expected = datetime.combine(yesterday, time(23, 59, 59))
    assert assignment.released_at.replace(tzinfo=None) == expected


@pytest.mark.asyncio
async def test_auto_release_end_date_today(db: AsyncSession):
    """end_date = today IS processed (end_date <= CURRENT_DATE)."""
    cl, dm, pm, dev = await _setup(db)
    today = date.today()
    assignment = await _create_project_with_assignment(db, today, dm, pm, dev, cl)

    released = await run_auto_release(db)
    assert len(released) == 1
    await db.refresh(assignment)
    assert assignment.status == "AUTO_RELEASED"


@pytest.mark.asyncio
async def test_auto_release_future_not_processed(db: AsyncSession):
    cl, dm, pm, dev = await _setup(db)
    tomorrow = date.today() + timedelta(days=1)
    await _create_project_with_assignment(db, tomorrow, dm, pm, dev, cl)

    released = await run_auto_release(db)
    assert len(released) == 0


@pytest.mark.asyncio
async def test_auto_release_null_end_date_not_processed(db: AsyncSession):
    cl, dm, pm, dev = await _setup(db)
    await _create_project_with_assignment(db, None, dm, pm, dev, cl)

    released = await run_auto_release(db)
    assert len(released) == 0


@pytest.mark.asyncio
async def test_auto_release_already_released_not_processed(db: AsyncSession):
    cl, dm, pm, dev = await _setup(db)
    yesterday = date.today() - timedelta(days=1)
    assignment = await _create_project_with_assignment(db, yesterday, dm, pm, dev, cl)

    # Manually set to RELEASED
    assignment.status = "RELEASED"
    assignment.released_at = datetime.now(timezone.utc)
    await db.commit()

    released = await run_auto_release(db)
    assert len(released) == 0


@pytest.mark.asyncio
async def test_auto_release_multiple(db: AsyncSession):
    cl, dm, pm, dev1 = await _setup(db)
    dev2 = await _create_resource(db, "Dev2")
    yesterday = date.today() - timedelta(days=1)

    await _create_project_with_assignment(db, yesterday, dm, pm, dev1, cl)
    await _create_project_with_assignment(db, yesterday, dm, pm, dev2, cl)

    released = await run_auto_release(db)
    assert len(released) == 2


@pytest.mark.asyncio
async def test_auto_release_idempotent(db: AsyncSession):
    """Running twice produces same result — already processed assignments skipped."""
    cl, dm, pm, dev = await _setup(db)
    yesterday = date.today() - timedelta(days=1)
    await _create_project_with_assignment(db, yesterday, dm, pm, dev, cl)

    released1 = await run_auto_release(db)
    await db.flush()
    released2 = await run_auto_release(db)

    assert len(released1) == 1
    assert len(released2) == 0


# ── Audit logging ───────────────────────────────────────


@pytest.mark.asyncio
async def test_auto_release_audit_entries(db: AsyncSession):
    cl, dm, pm, dev = await _setup(db)
    yesterday = date.today() - timedelta(days=1)
    assignment = await _create_project_with_assignment(db, yesterday, dm, pm, dev, cl)

    await run_auto_release(db)
    await db.flush()

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "assignment",
            AuditLog.entity_id == assignment.id,
            AuditLog.action == "UPDATE",
        )
    )
    entries = list(result.scalars().all())
    field_names = {e.field_name for e in entries}
    assert "status" in field_names
    assert "released_at" in field_names

    # changed_by should be SYSTEM (uuid(int=0))
    for e in entries:
        assert e.changed_by == uuid.UUID(int=0)


# ── Manual trigger endpoint ─────────────────────────────


@pytest.mark.asyncio
async def test_manual_trigger_as_ceo(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm, dev = await _setup(db)
    yesterday = date.today() - timedelta(days=1)
    await _create_project_with_assignment(db, yesterday, dm, pm, dev, cl)

    resp = await client.post("/api/v1/jobs/auto-release")
    assert resp.status_code == 200
    data = resp.json()
    assert data["released_count"] == 1
    assert len(data["assignments"]) == 1


@pytest.mark.asyncio
async def test_manual_trigger_non_admin_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    pm_user = await create_test_user(db, "PM")
    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})

    resp = await client.post("/api/v1/jobs/auto-release")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_manual_trigger_empty(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.post("/api/v1/jobs/auto-release")
    assert resp.status_code == 200
    assert resp.json()["released_count"] == 0
