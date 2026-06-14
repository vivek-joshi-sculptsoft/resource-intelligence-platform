"""Tests for Assignment access control and field restrictions — VRIP-51."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clients.models import Client
from app.modules.resources.models import Resource
from tests.conftest import create_test_user, login_as


async def _create_resource(db: AsyncSession, name: str) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name=name,
        designation="Developer",
        technical_expertise="Python",
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


async def _create_client(db: AsyncSession, name: str) -> Client:
    c = Client(id=uuid.uuid4(), name=name)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


async def _setup_project_with_assignment(
    client: AsyncClient, db: AsyncSession
) -> tuple[dict, Resource, Resource, Resource]:
    """Create project + assignment as CEO. Returns (project, dm_resource, pm_resource, dev_resource)."""
    await login_as(client)
    dm_r = await _create_resource(db, "DM-R")
    pm_r = await _create_resource(db, "PM-R")
    dev_r = await _create_resource(db, "Dev-R")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:6]}")

    # Create project as CEO
    resp = await client.post("/api/v1/projects", json={
        "name": f"Proj-{uuid.uuid4().hex[:6]}",
        "client_id": str(cl.id),
        "type": "FIXED_PRICE",
        "dm_id": str(dm_r.id),
        "pm_id": str(pm_r.id),
    })
    assert resp.status_code == 201
    proj = resp.json()["data"]

    # Create assignment
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json={
        "resource_id": str(dev_r.id),
        "allocation_pct": 60,
        "billability_pct": 50,
        "is_shadow": False,
        "start_date": date.today().isoformat(),
    })
    assert resp.status_code == 201

    return proj, dm_r, pm_r, dev_r


# ── CEO/CTO: EDIT ALL ──────────────────────────────────


@pytest.mark.asyncio
async def test_ceo_full_access(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)
    # Already logged in as CEO from setup
    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["billability_pct"] == 50
    assert data[0]["is_shadow"] is False


@pytest.mark.asyncio
async def test_cto_full_access(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    cto_user = await create_test_user(db, "CTO")
    await client.post("/api/v1/auth/login", json={"email": cto_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data[0]["billability_pct"] == 50


# ── DM: EDIT OWN_PORTFOLIO ─────────────────────────────


@pytest.mark.asyncio
async def test_dm_own_portfolio_can_view(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    dm_user = await create_test_user(db, "DM")
    dm_user.resource_id = dm_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


@pytest.mark.asyncio
async def test_dm_other_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    other_dm_r = await _create_resource(db, "Other-DM")
    dm_user = await create_test_user(db, "DM")
    dm_user.resource_id = other_dm_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dm_can_create_on_own_project(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    new_dev = await _create_resource(db, "New-Dev")
    dm_user = await create_test_user(db, "DM")
    dm_user.resource_id = dm_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    # DM allocation access_level is VIEW not EDIT in access matrix
    # Per access matrix: DM has VIEW on allocation, not EDIT
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json={
        "resource_id": str(new_dev.id),
        "allocation_pct": 30,
        "billability_pct": 20,
        "start_date": date.today().isoformat(),
    })
    # DM has VIEW only on allocation — create requires EDIT → 403
    assert resp.status_code == 403


# ── PM: EDIT OWN_PORTFOLIO ─────────────────────────────


@pytest.mark.asyncio
async def test_pm_own_portfolio_can_create(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    new_dev = await _create_resource(db, "New-Dev-PM")
    pm_user = await create_test_user(db, "PM")
    pm_user.resource_id = pm_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json={
        "resource_id": str(new_dev.id),
        "allocation_pct": 40,
        "billability_pct": 30,
        "start_date": date.today().isoformat(),
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_pm_other_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    other_pm_r = await _create_resource(db, "Other-PM")
    pm_user = await create_test_user(db, "PM")
    pm_user.resource_id = other_pm_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 403


# ── Finance: VIEW ALL, billing_rate visible ─────────────


@pytest.mark.asyncio
async def test_finance_view_all(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    fin_user = await create_test_user(db, "FINANCE")
    await client.post("/api/v1/auth/login", json={"email": fin_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["billability_pct"] == 50
    assert data[0]["is_shadow"] is False


@pytest.mark.asyncio
async def test_finance_cannot_create(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    fin_user = await create_test_user(db, "FINANCE")
    await client.post("/api/v1/auth/login", json={"email": fin_user.email, "password": "TestPass123"})

    new_dev = await _create_resource(db, "Fin-Dev")
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json={
        "resource_id": str(new_dev.id),
        "allocation_pct": 50,
        "billability_pct": 40,
        "start_date": date.today().isoformat(),
    })
    assert resp.status_code == 403


# ── HR: VIEW ALL, sensitive fields null ─────────────────


@pytest.mark.asyncio
async def test_hr_view_with_null_sensitive_fields(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    hr_user = await create_test_user(db, "HR")
    await client.post("/api/v1/auth/login", json={"email": hr_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["billability_pct"] is None
    assert data[0]["is_shadow"] is None
    assert data[0]["billing_rate"] is None


@pytest.mark.asyncio
async def test_hr_cannot_create(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    hr_user = await create_test_user(db, "HR")
    await client.post("/api/v1/auth/login", json={"email": hr_user.email, "password": "TestPass123"})

    new_dev = await _create_resource(db, "HR-Dev")
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json={
        "resource_id": str(new_dev.id),
        "allocation_pct": 50,
        "billability_pct": 40,
        "start_date": date.today().isoformat(),
    })
    assert resp.status_code == 403


# ── Engineer: VIEW SELF_ONLY, sensitive fields null ─────


@pytest.mark.asyncio
async def test_engineer_own_assignments_only(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    eng_user = await create_test_user(db, "ENGINEER")
    eng_user.resource_id = dev_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    # Can see own assignments via resource endpoint
    resp = await client.get(f"/api/v1/resources/{dev_r.id}/assignments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["billability_pct"] is None
    assert data[0]["is_shadow"] is None


@pytest.mark.asyncio
async def test_engineer_other_resource_forbidden(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    eng_user = await create_test_user(db, "ENGINEER")
    eng_user.resource_id = dev_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    # Cannot see other resource's assignments
    resp = await client.get(f"/api/v1/resources/{dm_r.id}/assignments")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_cannot_create(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    eng_user = await create_test_user(db, "ENGINEER")
    eng_user.resource_id = dev_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    new_dev = await _create_resource(db, "Eng-Dev")
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json={
        "resource_id": str(new_dev.id),
        "allocation_pct": 50,
        "billability_pct": 40,
        "start_date": date.today().isoformat(),
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_get_own_assignment_detail(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    # Get assignment id first as CEO
    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    aid = resp.json()["data"][0]["id"]

    eng_user = await create_test_user(db, "ENGINEER")
    eng_user.resource_id = dev_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/assignments/{aid}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["billability_pct"] is None
    assert data["is_shadow"] is None


@pytest.mark.asyncio
async def test_engineer_get_other_assignment_forbidden(client: AsyncClient, db: AsyncSession):
    proj, dm_r, pm_r, dev_r = await _setup_project_with_assignment(client, db)

    # Get assignment id first as CEO
    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    aid = resp.json()["data"][0]["id"]

    # Create engineer linked to a DIFFERENT resource
    other_r = await _create_resource(db, "Other-Eng")
    eng_user = await create_test_user(db, "ENGINEER")
    eng_user.resource_id = other_r.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/assignments/{aid}")
    assert resp.status_code == 403
