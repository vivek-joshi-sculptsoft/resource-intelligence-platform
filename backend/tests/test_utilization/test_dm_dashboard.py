"""Tests for GET /api/v1/dashboard/dm — See FSD §7.1, ACCESS-MATRIX.md."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from tests.conftest import create_test_user, login_as, login_as_role

URL = "/api/v1/dashboard/dm"


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


async def _create_dm_with_resource(db: AsyncSession, client: AsyncClient) -> tuple[AsyncClient, User, Resource]:
    """Create a DM user linked to a resource."""
    dm_resource = await _seed_resource(db, "DM Resource")
    await db.commit()
    dm_user = await create_test_user(db, "DM", email=f"dm-{uuid.uuid4().hex[:6]}@test.com", name="DM User")
    dm_user.resource_id = dm_resource.id
    await db.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})
    assert resp.status_code == 200
    return client, dm_user, dm_resource


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
async def test_dm_can_access(client: AsyncClient, db: AsyncSession):
    client, _, _ = await _create_dm_with_resource(db, client)
    resp = await client.get(URL)
    assert resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["PM", "FINANCE", "HR", "ENGINEER"])
async def test_non_authorized_roles_get_403(client: AsyncClient, db: AsyncSession, role: str):
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
    data = (await client.get(URL)).json()["data"]
    expected_keys = {
        "portfolio_utilization_pct",
        "active_project_count",
        "resource_count",
        "bench_count",
        "upcoming_releases_30d",
        "delivery_delays_count",
        "delivery_delays",
        "resource_cost_inr",
        "non_human_cost_inr",
        "total_cost_inr",
        "projected_revenue_inr",
        "projected_margin_inr",
        "projected_margin_pct",
    }
    assert expected_keys == set(data.keys())


@pytest.mark.asyncio
async def test_financial_fields_present(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert isinstance(data["delivery_delays_count"], int)
    assert "delivery_delays" in data
    assert "projected_revenue_inr" in data
    assert "total_cost_inr" in data
    assert "resource_cost_inr" in data
    assert "non_human_cost_inr" in data
    assert "projected_margin_inr" in data
    assert "projected_margin_pct" in data


# --- Scope tests ---


@pytest.mark.asyncio
async def test_dm_sees_only_own_portfolio(client: AsyncClient, db: AsyncSession):
    """DM sees only projects where dm_id = their resource_id."""
    client, dm_user, dm_resource = await _create_dm_with_resource(db, client)
    other_dm = await _seed_resource(db, "Other DM")
    cl = await _seed_client(db)

    # DM's project
    await _seed_project(db, cl.id, dm_resource.id, dm_resource.id, name="My Project")
    # Other DM's project
    await _seed_project(db, cl.id, other_dm.id, other_dm.id, name="Other Project")
    await db.commit()

    data = (await client.get(URL)).json()["data"]
    assert data["active_project_count"] == 1


@pytest.mark.asyncio
async def test_ceo_sees_all_projects(client: AsyncClient, db: AsyncSession):
    """CEO sees all projects (scope ALL)."""
    r1 = await _seed_resource(db, "DM1")
    r2 = await _seed_resource(db, "DM2")
    cl = await _seed_client(db)
    await _seed_project(db, cl.id, r1.id, r1.id)
    await _seed_project(db, cl.id, r2.id, r2.id)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["active_project_count"] >= 2


# --- Utilization calculation tests ---


@pytest.mark.asyncio
async def test_portfolio_utilization(client: AsyncClient, db: AsyncSession):
    """2 resources on portfolio, one with 80% billability => utilization = (80) / (2*100) * 100 = 40%."""
    client, _, dm_res = await _create_dm_with_resource(db, client)
    dev1 = await _seed_resource(db, "Dev1")
    dev2 = await _seed_resource(db, "Dev2")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm_res.id, dm_res.id)
    await _seed_assignment(db, p.id, dev1.id, billability_pct=80)
    await _seed_assignment(db, p.id, dev2.id, allocation_pct=50, billability_pct=0)
    await db.commit()

    data = (await client.get(URL)).json()["data"]
    assert data["resource_count"] == 2
    assert float(data["portfolio_utilization_pct"]) == 40.0


# --- Bench count tests ---


@pytest.mark.asyncio
async def test_bench_count_for_released_resources(client: AsyncClient, db: AsyncSession):
    """Resource with released assignment on DM's project and no other active assignments = bench."""
    client, _, dm_res = await _create_dm_with_resource(db, client)
    dev = await _seed_resource(db, "Released Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm_res.id, dm_res.id)
    await _seed_assignment(db, p.id, dev.id, status="RELEASED")
    await db.commit()

    data = (await client.get(URL)).json()["data"]
    assert data["bench_count"] >= 1


# --- Upcoming releases tests ---


@pytest.mark.asyncio
async def test_upcoming_releases_scoped_to_portfolio(client: AsyncClient, db: AsyncSession):
    client, _, dm_res = await _create_dm_with_resource(db, client)
    other_dm = await _seed_resource(db, "Other DM")
    dev1 = await _seed_resource(db, "My Dev")
    dev2 = await _seed_resource(db, "Other Dev")
    cl = await _seed_client(db)

    my_proj = await _seed_project(db, cl.id, dm_res.id, dm_res.id, name="My Proj")
    other_proj = await _seed_project(db, cl.id, other_dm.id, other_dm.id, name="Other Proj")

    end = date.today() + timedelta(days=10)
    await _seed_assignment(db, my_proj.id, dev1.id, end_date=end)
    await _seed_assignment(db, other_proj.id, dev2.id, end_date=end)
    await db.commit()

    data = (await client.get(URL)).json()["data"]
    names = [u["resource_name"] for u in data["upcoming_releases_30d"]]
    assert "My Dev" in names
    assert "Other Dev" not in names


# --- Empty portfolio tests ---


@pytest.mark.asyncio
async def test_empty_portfolio(client: AsyncClient, db: AsyncSession):
    """DM with no projects gets zeros."""
    client, _, _ = await _create_dm_with_resource(db, client)
    data = (await client.get(URL)).json()["data"]
    assert data["active_project_count"] == 0
    assert data["resource_count"] == 0
    assert data["bench_count"] == 0
    assert float(data["portfolio_utilization_pct"]) == 0
    assert data["upcoming_releases_30d"] == []
