"""Tests for GET /api/v1/dashboard/availability — See API.md §GET /dashboard/availability."""

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

URL = "/api/v1/dashboard/availability"


async def _seed_resource(db: AsyncSession, name: str = "Dev 1", **kwargs) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=kwargs.get("employee_id", f"EMP-{uuid.uuid4().hex[:6]}"),
        name=name,
        designation=kwargs.get("designation", "Senior Developer"),
        technical_expertise=kwargs.get("technical_expertise", "Python"),
        date_of_joining=kwargs.get("date_of_joining", date.today() - timedelta(days=90)),
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


async def _seed_project(db: AsyncSession, client_id: uuid.UUID, dm_id: uuid.UUID, pm_id: uuid.UUID, **kwargs) -> Project:
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


# --- Access control ---


@pytest.mark.asyncio
async def test_ceo_can_access(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(URL)
    assert resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["CTO", "DM", "PM", "FINANCE", "HR", "ENGINEER"])
async def test_all_roles_can_access(client: AsyncClient, db: AsyncSession, role: str):
    client, _ = await login_as_role(client, db, role)
    resp = await client.get(URL)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_401(client: AsyncClient):
    resp = await client.get(URL)
    assert resp.status_code == 401


# --- Response shape ---


@pytest.mark.asyncio
async def test_response_has_four_sections(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert set(data.keys()) == {"bench", "partial", "releasing_soon", "fully_allocated"}


# --- Bench bucket ---


@pytest.mark.asyncio
async def test_bench_resource_included(client: AsyncClient, db: AsyncSession):
    r = await _seed_resource(db, "Bench Dev", technical_expertise="React")
    await _seed_tags(db, r.id, ["frontend", "react"])
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    bench_ids = [b["id"] for b in data["bench"]]
    assert str(r.id) in bench_ids
    entry = next(b for b in data["bench"] if b["id"] == str(r.id))
    assert entry["technical_expertise"] == "React"
    assert set(entry["tags"]) == {"frontend", "react"}
    assert entry["days_on_bench"] >= 0


# --- Partial bucket ---


@pytest.mark.asyncio
async def test_partial_resource(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM")
    dev = await _seed_resource(db, "Partial Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id, name="Proj A")
    await _seed_assignment(db, p.id, dev.id, allocation_pct=60)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    partial_ids = [r["id"] for r in data["partial"]]
    assert str(dev.id) in partial_ids
    entry = next(r for r in data["partial"] if r["id"] == str(dev.id))
    assert entry["total_allocation_pct"] == 60
    assert entry["spare_capacity_pct"] == 40
    assert "Proj A" in entry["projects"]


# --- Fully allocated bucket ---


@pytest.mark.asyncio
async def test_fully_allocated_resource(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM")
    dev = await _seed_resource(db, "Full Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, p.id, dev.id, allocation_pct=100)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    full_names = [r["name"] for r in data["fully_allocated"]]
    assert "Full Dev" in full_names


@pytest.mark.asyncio
async def test_over_allocated_in_fully_bucket(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM")
    dev = await _seed_resource(db, "Over Dev")
    cl = await _seed_client(db)
    p1 = await _seed_project(db, cl.id, dm.id, dm.id)
    p2 = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, p1.id, dev.id, allocation_pct=60)
    await _seed_assignment(db, p2.id, dev.id, allocation_pct=60)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    entry = next((r for r in data["fully_allocated"] if r["name"] == "Over Dev"), None)
    assert entry is not None
    assert entry["total_allocation_pct"] == 120


# --- Releasing soon bucket ---


@pytest.mark.asyncio
async def test_releasing_soon_default_window(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM")
    dev = await _seed_resource(db, "Releasing Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id, name="Release Proj")
    end = date.today() + timedelta(days=20)
    await _seed_assignment(db, p.id, dev.id, allocation_pct=100, end_date=end)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    names = [r["name"] for r in data["releasing_soon"]]
    assert "Releasing Dev" in names
    entry = next(r for r in data["releasing_soon"] if r["name"] == "Releasing Dev")
    assert entry["days_remaining"] == 20
    assert entry["project_name"] == "Release Proj"


@pytest.mark.asyncio
async def test_window_param_filters(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM")
    dev = await _seed_resource(db, "Window Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, p.id, dev.id, end_date=date.today() + timedelta(days=45))
    await db.commit()

    await login_as(client)
    # Default window=30 should exclude
    data30 = (await client.get(URL)).json()["data"]
    names30 = [r["name"] for r in data30["releasing_soon"]]
    assert "Window Dev" not in names30

    # window=60 should include
    data60 = (await client.get(f"{URL}?window=60")).json()["data"]
    names60 = [r["name"] for r in data60["releasing_soon"]]
    assert "Window Dev" in names60


# --- No financial data exposed ---


@pytest.mark.asyncio
async def test_no_financial_fields(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    raw = str(data)
    for field in ["billing_rate", "billability", "loaded_cost", "ctc", "shadow"]:
        assert field not in raw.lower()


# --- Inactive resources excluded ---


@pytest.mark.asyncio
async def test_inactive_resources_excluded(client: AsyncClient, db: AsyncSession):
    await _seed_resource(db, "Inactive Dev", is_active=False)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    all_names = (
        [b["name"] for b in data["bench"]]
        + [p["name"] for p in data["partial"]]
        + [f["name"] for f in data["fully_allocated"]]
    )
    assert "Inactive Dev" not in all_names
