"""Tests for GET /api/v1/dashboard/company — See FSD §7.1."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from tests.conftest import login_as, login_as_role

URL = "/api/v1/dashboard/company"


async def _seed_resource(db: AsyncSession, name: str = "Dev 1", **kwargs) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=kwargs.get("employee_id", f"EMP-{uuid.uuid4().hex[:6]}"),
        name=name,
        designation=kwargs.get("designation", "Senior Developer"),
        date_of_joining=kwargs.get("date_of_joining", date.today() - timedelta(days=90)),
        is_active=kwargs.get("is_active", True),
    )
    db.add(r)
    await db.flush()
    return r


async def _seed_client(db: AsyncSession, name: str = "Acme Corp") -> Client:
    c = Client(id=uuid.uuid4(), name=name, is_active=True)
    db.add(c)
    await db.flush()
    return c


async def _seed_project(
    db: AsyncSession, client_id: uuid.UUID, dm_id: uuid.UUID, pm_id: uuid.UUID, **kwargs
) -> Project:
    p = Project(
        id=uuid.uuid4(),
        name=kwargs.get("name", f"Project-{uuid.uuid4().hex[:4]}"),
        client_id=client_id,
        type=kwargs.get("type", "TIME_AND_MATERIAL"),
        dm_id=dm_id,
        pm_id=pm_id,
        status=kwargs.get("status", "ACTIVE"),
        is_active=kwargs.get("is_active", True),
    )
    db.add(p)
    await db.flush()
    return p


async def _seed_assignment(db: AsyncSession, project_id: uuid.UUID, resource_id: uuid.UUID, **kwargs) -> Assignment:
    a = Assignment(
        id=uuid.uuid4(),
        project_id=project_id,
        resource_id=resource_id,
        allocation_pct=kwargs.get("allocation_pct", 100),
        billability_pct=kwargs.get("billability_pct", 100),
        is_shadow=kwargs.get("is_shadow", False),
        start_date=kwargs.get("start_date", date.today() - timedelta(days=30)),
        end_date=kwargs.get("end_date"),
        status=kwargs.get("status", "ACTIVE"),
    )
    db.add(a)
    await db.flush()
    return a


# --- Access control tests ---


@pytest.mark.asyncio
async def test_ceo_can_access(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(URL)
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_cto_can_access(client: AsyncClient, db: AsyncSession):
    client, _ = await login_as_role(client, db, "CTO")
    resp = await client.get(URL)
    assert resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["DM", "PM", "FINANCE", "HR", "ENGINEER"])
async def test_non_ceo_cto_get_403(client: AsyncClient, db: AsyncSession, role: str):
    client, _ = await login_as_role(client, db, role)
    resp = await client.get(URL)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_get_401(client: AsyncClient):
    resp = await client.get(URL)
    assert resp.status_code == 401


# --- Response shape tests ---


@pytest.mark.asyncio
async def test_response_has_all_fields(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(URL)
    data = resp.json()["data"]
    expected_keys = {
        "billable_utilization_pct",
        "total_active_resources",
        "bench_count",
        "bench_resources",
        "shadow_count",
        "shadow_total_allocation_pct",
        "active_project_count",
        "active_projects_by_type",
        "upcoming_releases_30d",
        "overdue_milestones_count",
        "overdue_milestones",
        "projected_revenue_inr",
        "actual_revenue_inr",
        "total_cost_inr",
    }
    assert expected_keys == set(data.keys())


@pytest.mark.asyncio
async def test_phase2_fields_are_null(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["projected_revenue_inr"] is None
    assert data["actual_revenue_inr"] is None
    assert data["total_cost_inr"] is None
    assert data["overdue_milestones_count"] is None
    assert data["overdue_milestones"] is None


# --- Utilization calculation tests ---


@pytest.mark.asyncio
async def test_empty_state_zero_utilization(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["active_project_count"] == 0
    assert data["active_projects_by_type"] == {}


@pytest.mark.asyncio
async def test_utilization_calculation(client: AsyncClient, db: AsyncSession):
    """See BUSINESS-RULES.md §7.1 — 2 active resources, 1 with 80% billability => 40%."""
    r1 = await _seed_resource(db, "Alice")
    r2 = await _seed_resource(db, "Bob")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, r1.id, r2.id)
    await _seed_assignment(db, p.id, r1.id, billability_pct=80)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["total_active_resources"] >= 2
    assert float(data["billable_utilization_pct"]) > 0


# --- Bench tests ---


@pytest.mark.asyncio
async def test_bench_resources(client: AsyncClient, db: AsyncSession):
    """Resource with no ACTIVE assignments is on bench."""
    bench_r = await _seed_resource(db, "Benchy", date_of_joining=date.today() - timedelta(days=10))
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    bench_ids = [b["id"] for b in data["bench_resources"]]
    assert str(bench_r.id) in bench_ids
    bench_entry = next(b for b in data["bench_resources"] if b["id"] == str(bench_r.id))
    assert bench_entry["days_on_bench"] == 10
    assert data["bench_count"] >= 1


# --- Shadow tests ---


@pytest.mark.asyncio
async def test_shadow_count_and_pct(client: AsyncClient, db: AsyncSession):
    r1 = await _seed_resource(db, "Shadow Dev")
    r2 = await _seed_resource(db, "DM")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, r2.id, r2.id)
    await _seed_assignment(db, p.id, r1.id, allocation_pct=30, billability_pct=0, is_shadow=True)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["shadow_count"] >= 1
    assert data["shadow_total_allocation_pct"] >= 30


# --- Active projects by type ---


@pytest.mark.asyncio
async def test_active_projects_by_type(client: AsyncClient, db: AsyncSession):
    r1 = await _seed_resource(db, "DM1")
    r2 = await _seed_resource(db, "PM1")
    cl = await _seed_client(db)
    await _seed_project(db, cl.id, r1.id, r2.id, type="FIXED_PRICE")
    await _seed_project(db, cl.id, r1.id, r2.id, type="FIXED_PRICE")
    await _seed_project(db, cl.id, r1.id, r2.id, type="TIME_AND_MATERIAL")
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["active_projects_by_type"].get("FIXED_PRICE", 0) >= 2
    assert data["active_projects_by_type"].get("TIME_AND_MATERIAL", 0) >= 1
    assert data["active_project_count"] >= 3


# --- Upcoming releases ---


@pytest.mark.asyncio
async def test_upcoming_releases_within_30d(client: AsyncClient, db: AsyncSession):
    r1 = await _seed_resource(db, "Releasing Dev")
    r2 = await _seed_resource(db, "DM")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, r2.id, r2.id, name="Release Project")
    end = date.today() + timedelta(days=15)
    await _seed_assignment(db, p.id, r1.id, end_date=end)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    names = [u["resource_name"] for u in data["upcoming_releases_30d"]]
    assert "Releasing Dev" in names
    entry = next(u for u in data["upcoming_releases_30d"] if u["resource_name"] == "Releasing Dev")
    assert entry["days_remaining"] == 15
    assert entry["project_name"] == "Release Project"


@pytest.mark.asyncio
async def test_releases_beyond_30d_excluded(client: AsyncClient, db: AsyncSession):
    r1 = await _seed_resource(db, "Far Future Dev")
    r2 = await _seed_resource(db, "DM")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, r2.id, r2.id)
    await _seed_assignment(db, p.id, r1.id, end_date=date.today() + timedelta(days=60))
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    names = [u["resource_name"] for u in data["upcoming_releases_30d"]]
    assert "Far Future Dev" not in names
