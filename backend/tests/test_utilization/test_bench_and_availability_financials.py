"""Tests for VRIP-102 — bench/availability financial enhancements.

GET /api/v1/bench, GET /api/v1/bench/summary,
GET /api/v1/availability/upcoming, GET /api/v1/availability/partial.
See modules/10-bench-forecasting/API.md.
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource, ResourceTag
from tests.conftest import login_as, login_as_role


async def _seed_resource(db: AsyncSession, name: str = "Dev 1", **kwargs) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=kwargs.get("employee_id", f"EMP-{uuid.uuid4().hex[:6]}"),
        name=name,
        designation=kwargs.get("designation", "Senior Developer"),
        technical_expertise=kwargs.get("technical_expertise", "Python"),
        date_of_joining=kwargs.get("date_of_joining", date.today() - timedelta(days=90)),
        loaded_cost_monthly=kwargs.get("loaded_cost_monthly"),
        is_active=kwargs.get("is_active", True),
    )
    db.add(r)
    await db.flush()
    return r


async def _seed_tags(db: AsyncSession, resource_id: uuid.UUID, tags: list[str]) -> None:
    for t in tags:
        db.add(ResourceTag(resource_id=resource_id, tag=t))
    await db.flush()


async def _seed_client(db: AsyncSession) -> Client:
    c = Client(id=uuid.uuid4(), name=f"Client-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(c)
    await db.flush()
    return c


async def _seed_project(db: AsyncSession, client_id, dm_id, pm_id, **kwargs) -> Project:
    p = Project(
        id=uuid.uuid4(),
        name=kwargs.get("name", f"Project-{uuid.uuid4().hex[:4]}"),
        client_id=client_id,
        dm_id=dm_id,
        pm_id=pm_id,
        status="ACTIVE",
        is_active=True,
    )
    db.add(p)
    await db.flush()
    return p


async def _seed_assignment(db: AsyncSession, project_id, resource_id, **kwargs) -> Assignment:
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


# --- GET /api/v1/bench ---


@pytest.mark.asyncio
async def test_bench_list_includes_cost_for_ceo(client: AsyncClient, db: AsyncSession):
    r = await _seed_resource(
        db,
        "Bench Dev",
        technical_expertise="React",
        date_of_joining=date.today() - timedelta(days=22),
        loaded_cost_monthly=66000,
    )
    await _seed_tags(db, r.id, ["frontend"])
    await db.commit()

    await login_as(client)
    resp = await client.get("/api/v1/bench")
    assert resp.status_code == 200
    data = resp.json()["data"]
    entry = next(b for b in data if b["id"] == str(r.id))
    assert float(entry["loaded_cost_monthly"]) == pytest.approx(66000.0)
    assert float(entry["daily_bench_cost_inr"]) == pytest.approx(3000.0)
    assert entry["days_on_bench"] == 22
    assert float(entry["total_bench_cost_inr"]) == pytest.approx(66000.0)


@pytest.mark.asyncio
async def test_bench_list_null_cost_for_unauthorized_role(client: AsyncClient, db: AsyncSession):
    r = await _seed_resource(db, "Bench Dev 2", loaded_cost_monthly=50000)
    await db.commit()

    dm_client, _ = await login_as_role(client, db, "DM")
    resp = await dm_client.get("/api/v1/bench")
    assert resp.status_code == 200
    entry = next(b for b in resp.json()["data"] if b["id"] == str(r.id))
    assert entry["loaded_cost_monthly"] is None
    assert entry["daily_bench_cost_inr"] is None
    assert entry["total_bench_cost_inr"] is None


@pytest.mark.asyncio
async def test_bench_list_visible_to_engineer_without_cost(client: AsyncClient, db: AsyncSession):
    r = await _seed_resource(db, "Bench Dev 3", loaded_cost_monthly=50000)
    await db.commit()

    eng_client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await eng_client.get("/api/v1/bench")
    assert resp.status_code == 200
    entry = next(b for b in resp.json()["data"] if b["id"] == str(r.id))
    assert entry["loaded_cost_monthly"] is None
    assert entry["days_on_bench"] >= 0


# --- GET /api/v1/bench/summary ---


@pytest.mark.asyncio
async def test_bench_summary_aggregates_cost_for_ceo(client: AsyncClient, db: AsyncSession):
    await _seed_resource(
        db, "Sum Dev 1", date_of_joining=date.today() - timedelta(days=10), loaded_cost_monthly=44000
    )
    await _seed_resource(
        db, "Sum Dev 2", date_of_joining=date.today() - timedelta(days=20), loaded_cost_monthly=66000
    )
    await db.commit()

    await login_as(client)
    resp = await client.get("/api/v1/bench/summary")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["bench_count"] >= 2
    assert float(data["total_bench_cost_monthly"]) >= 110000.0
    assert float(data["average_bench_duration"]) >= 0


@pytest.mark.asyncio
async def test_bench_summary_null_cost_for_unauthorized_role(client: AsyncClient, db: AsyncSession):
    await _seed_resource(db, "Sum Dev 3", loaded_cost_monthly=44000)
    await db.commit()

    pm_client, _ = await login_as_role(client, db, "PM")
    resp = await pm_client.get("/api/v1/bench/summary")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_bench_cost_monthly"] is None
    assert data["bench_count"] >= 1


# --- GET /api/v1/availability/upcoming ---


@pytest.mark.asyncio
async def test_availability_upcoming_default_window(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM")
    dev = await _seed_resource(db, "Upcoming Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id, name="Upcoming Proj")
    end = date.today() + timedelta(days=15)
    await _seed_assignment(db, p.id, dev.id, allocation_pct=80, end_date=end)
    await db.commit()

    await login_as(client)
    resp = await client.get("/api/v1/availability/upcoming")
    assert resp.status_code == 200
    data = resp.json()["data"]
    entry = next(item for item in data if item["resource"]["name"] == "Upcoming Dev")
    assert entry["project"]["name"] == "Upcoming Proj"
    assert entry["allocation_pct"] == 80
    assert entry["days_remaining"] == 15


@pytest.mark.asyncio
async def test_availability_upcoming_window_param(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM2")
    dev = await _seed_resource(db, "Window Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, p.id, dev.id, end_date=date.today() + timedelta(days=45))
    await db.commit()

    await login_as(client)
    data30 = (await client.get("/api/v1/availability/upcoming")).json()["data"]
    assert "Window Dev" not in [i["resource"]["name"] for i in data30]

    data60 = (await client.get("/api/v1/availability/upcoming?window=60")).json()["data"]
    assert "Window Dev" in [i["resource"]["name"] for i in data60]


@pytest.mark.asyncio
async def test_availability_upcoming_visible_to_engineer(client: AsyncClient, db: AsyncSession):
    eng_client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await eng_client.get("/api/v1/availability/upcoming")
    assert resp.status_code == 200


# --- GET /api/v1/availability/partial ---


@pytest.mark.asyncio
async def test_availability_partial_resource(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM3")
    dev = await _seed_resource(db, "Partial Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id, name="Partial Proj")
    await _seed_assignment(db, p.id, dev.id, allocation_pct=60)
    await db.commit()

    await login_as(client)
    resp = await client.get("/api/v1/availability/partial")
    assert resp.status_code == 200
    data = resp.json()["data"]
    entry = next(item for item in data if item["name"] == "Partial Dev")
    assert entry["total_allocation_pct"] == 60
    assert entry["spare_capacity_pct"] == 40
    assert any(proj["name"] == "Partial Proj" for proj in entry["projects"])


@pytest.mark.asyncio
async def test_availability_partial_excludes_fully_allocated_and_bench(
    client: AsyncClient, db: AsyncSession
):
    dm = await _seed_resource(db, "DM4")
    full_dev = await _seed_resource(db, "Full Dev")
    bench_dev = await _seed_resource(db, "Bench Dev 4")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, p.id, full_dev.id, allocation_pct=100)
    await db.commit()

    await login_as(client)
    resp = await client.get("/api/v1/availability/partial")
    names = [item["name"] for item in resp.json()["data"]]
    assert "Full Dev" not in names
    assert "Bench Dev 4" not in names


@pytest.mark.asyncio
async def test_availability_partial_visible_to_engineer(client: AsyncClient, db: AsyncSession):
    eng_client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await eng_client.get("/api/v1/availability/partial")
    assert resp.status_code == 200


# --- GET /api/v1/dashboard/availability — bench cost (VRIP-103) ---


@pytest.mark.asyncio
async def test_dashboard_availability_includes_bench_cost_for_ceo(
    client: AsyncClient, db: AsyncSession
):
    r = await _seed_resource(
        db,
        "Avail Bench Dev",
        date_of_joining=date.today() - timedelta(days=22),
        loaded_cost_monthly=66000,
    )
    await db.commit()

    await login_as(client)
    resp = await client.get("/api/v1/dashboard/availability")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["can_see_bench_cost"] is True
    entry = next(b for b in data["bench"] if b["id"] == str(r.id))
    assert float(entry["bench_cost_daily"]) == pytest.approx(3000.0)
    assert float(entry["bench_cost_total"]) == pytest.approx(66000.0)
    assert float(data["total_bench_cost_monthly"]) >= 66000.0


@pytest.mark.asyncio
async def test_dashboard_availability_null_bench_cost_for_unauthorized_role(
    client: AsyncClient, db: AsyncSession
):
    r = await _seed_resource(db, "Avail Bench Dev 2", loaded_cost_monthly=50000)
    await db.commit()

    dm_client, _ = await login_as_role(client, db, "DM")
    resp = await dm_client.get("/api/v1/dashboard/availability")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["can_see_bench_cost"] is False
    assert data["total_bench_cost_monthly"] is None
    entry = next(b for b in data["bench"] if b["id"] == str(r.id))
    assert entry["bench_cost_daily"] is None
    assert entry["bench_cost_total"] is None


@pytest.mark.asyncio
async def test_dashboard_availability_visible_to_engineer_without_cost(
    client: AsyncClient, db: AsyncSession
):
    r = await _seed_resource(db, "Avail Bench Dev 3", loaded_cost_monthly=50000)
    await db.commit()

    eng_client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await eng_client.get("/api/v1/dashboard/availability")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["can_see_bench_cost"] is False
    entry = next(b for b in data["bench"] if b["id"] == str(r.id))
    assert entry["bench_cost_daily"] is None
    assert entry["days_on_bench"] >= 0


# --- Unauthenticated ---


@pytest.mark.asyncio
async def test_unauthenticated_401(client: AsyncClient):
    for url in ["/api/v1/bench", "/api/v1/bench/summary", "/api/v1/availability/upcoming", "/api/v1/availability/partial"]:
        resp = await client.get(url)
        assert resp.status_code == 401
