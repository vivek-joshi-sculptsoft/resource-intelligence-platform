"""Tests for client_id filter on GET /api/v1/worklogs — See VRIP-134."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.modules.worklogs.models import Worklog
from tests.conftest import login_as


async def _seed_resource(db: AsyncSession, name: str) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name=name,
        designation="Developer",
        date_of_joining=date.today() - timedelta(days=90),
        is_active=True,
    )
    db.add(r)
    await db.flush()
    return r


async def _seed_client(db: AsyncSession, name: str) -> Client:
    c = Client(id=uuid.uuid4(), name=name, is_active=True)
    db.add(c)
    await db.flush()
    return c


async def _seed_project(db: AsyncSession, client_id, dm_id=None, pm_id=None, name=None) -> Project:
    p = Project(
        id=uuid.uuid4(),
        name=name or f"Proj-{uuid.uuid4().hex[:4]}",
        client_id=client_id,
        dm_id=dm_id,
        pm_id=pm_id,
        worklog_enabled=True,
        status="ACTIVE",
        is_active=True,
    )
    db.add(p)
    await db.flush()
    return p


async def _seed_worklog(db: AsyncSession, resource_id, project_id, days_ago=1, hours=4.0) -> Worklog:
    w = Worklog(
        id=uuid.uuid4(),
        resource_id=resource_id,
        project_id=project_id,
        log_date=date.today() - timedelta(days=days_ago),
        hours=hours,
        note=f"Work on day -{days_ago}",
    )
    db.add(w)
    await db.flush()
    return w


async def _setup_two_clients(db: AsyncSession):
    """Two clients, each with a project and worklogs."""
    res = await _seed_resource(db, "Dev One")
    dm_res = await _seed_resource(db, "DM For Tests")
    pm_res = await _seed_resource(db, "PM For Tests")
    client_a = await _seed_client(db, "Client Alpha")
    client_b = await _seed_client(db, "Client Beta")
    proj_a = await _seed_project(db, client_a.id, dm_id=dm_res.id, pm_id=pm_res.id, name="Alpha Project")
    proj_b = await _seed_project(db, client_b.id, dm_id=dm_res.id, pm_id=pm_res.id, name="Beta Project")

    db.add(Assignment(
        id=uuid.uuid4(), project_id=proj_a.id, resource_id=res.id,
        allocation_pct=100, billability_pct=100,
        start_date=date.today() - timedelta(days=60), status="ACTIVE",
    ))
    db.add(Assignment(
        id=uuid.uuid4(), project_id=proj_b.id, resource_id=res.id,
        allocation_pct=50, billability_pct=100,
        start_date=date.today() - timedelta(days=60), status="ACTIVE",
    ))

    wl_a1 = await _seed_worklog(db, res.id, proj_a.id, days_ago=1)
    wl_a2 = await _seed_worklog(db, res.id, proj_a.id, days_ago=2)
    wl_b1 = await _seed_worklog(db, res.id, proj_b.id, days_ago=3)

    await db.commit()
    return client_a, client_b, proj_a, proj_b, res


@pytest.mark.asyncio
async def test_filter_by_client_returns_only_client_worklogs(client: AsyncClient, db: AsyncSession):
    client_a, client_b, proj_a, proj_b, _ = await _setup_two_clients(db)
    await login_as(client)

    resp = await client.get(f"/api/v1/worklogs?client_id={client_a.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    project_names = {e["project"]["name"] for e in body["data"]}
    assert project_names == {"Alpha Project"}


@pytest.mark.asyncio
async def test_filter_by_other_client(client: AsyncClient, db: AsyncSession):
    client_a, client_b, _, _, _ = await _setup_two_clients(db)
    await login_as(client)

    resp = await client.get(f"/api/v1/worklogs?client_id={client_b.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["data"][0]["project"]["name"] == "Beta Project"


@pytest.mark.asyncio
async def test_filter_by_nonexistent_client_returns_empty(client: AsyncClient, db: AsyncSession):
    await _setup_two_clients(db)
    await login_as(client)

    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/worklogs?client_id={fake_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["data"] == []


@pytest.mark.asyncio
async def test_client_and_project_filter_combined(client: AsyncClient, db: AsyncSession):
    client_a, client_b, proj_a, proj_b, _ = await _setup_two_clients(db)
    await login_as(client)

    resp = await client.get(f"/api/v1/worklogs?client_id={client_a.id}&project_id={proj_a.id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    resp2 = await client.get(f"/api/v1/worklogs?client_id={client_a.id}&project_id={proj_b.id}")
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_client_filter_on_export_endpoint(client: AsyncClient, db: AsyncSession):
    client_a, _, _, _, _ = await _setup_two_clients(db)
    await login_as(client)

    resp = await client.get(f"/api/v1/worklogs/export?client_id={client_a.id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.mark.asyncio
async def test_no_client_filter_returns_all(client: AsyncClient, db: AsyncSession):
    await _setup_two_clients(db)
    await login_as(client)

    resp = await client.get("/api/v1/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3
