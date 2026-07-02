"""Tests for GET /api/v1/dashboard/company — See FSD §7.1."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.clients.models import Client
from app.modules.invoicing.models import Milestone
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
        loaded_cost_monthly=kwargs.get("loaded_cost_monthly"),
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
        billing_rate=kwargs.get("billing_rate"),
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
    """See VRIP-128 — revenue/cost/margin fields removed; they now live on
    GET /api/v1/dashboard/company-finance instead."""
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
        "top_5_projects_by_team_size",
        "upcoming_releases_30d",
        "overdue_milestones_count",
        "overdue_milestones",
        "total_bench_cost_monthly",
    }
    assert expected_keys == set(data.keys())


@pytest.mark.asyncio
async def test_overdue_milestones_empty_when_no_data(client: AsyncClient, db: AsyncSession):
    """See VRIP-106 — with no projects/milestones seeded, milestone fields are an empty list."""
    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["overdue_milestones_count"] == 0
    assert data["overdue_milestones"] == []


# --- Utilization calculation tests ---


@pytest.mark.asyncio
async def test_empty_state_zero_utilization(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert data["active_project_count"] == 0
    assert data["active_projects_by_type"] == {}
    assert data["top_5_projects_by_team_size"] == []


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


# --- Overdue milestones (VRIP-106) ---


@pytest.mark.asyncio
async def test_overdue_milestones(client: AsyncClient, db: AsyncSession):
    """See FSD §12 — Overdue: planned_delivery_date < today AND status = PLANNED."""
    r1 = await _seed_resource(db, "DM")
    r2 = await _seed_resource(db, "PM")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, r1.id, r2.id, type="FIXED_PRICE", name="FP Project")
    await db.flush()

    overdue = Milestone(
        id=uuid.uuid4(),
        project_id=p.id,
        name="Overdue Milestone",
        amount=50000,
        planned_delivery_date=date.today() - timedelta(days=5),
        status="PLANNED",
    )
    not_overdue_future = Milestone(
        id=uuid.uuid4(),
        project_id=p.id,
        name="Future Milestone",
        amount=50000,
        planned_delivery_date=date.today() + timedelta(days=5),
        status="PLANNED",
    )
    not_overdue_delivered = Milestone(
        id=uuid.uuid4(),
        project_id=p.id,
        name="Delivered Milestone",
        amount=50000,
        planned_delivery_date=date.today() - timedelta(days=5),
        status="DELIVERED",
    )
    db.add_all([overdue, not_overdue_future, not_overdue_delivered])
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    names = [m["name"] for m in data["overdue_milestones"]]
    assert names == ["Overdue Milestone"]
    assert data["overdue_milestones_count"] == 1
    entry = data["overdue_milestones"][0]
    assert entry["days_overdue"] == 5
    assert entry["project_name"] == "FP Project"


# --- Top 5 projects by team size (VRIP-129) ---


@pytest.mark.asyncio
async def test_top_5_projects_ranked_by_team_size(client: AsyncClient, db: AsyncSession):
    """See BUSINESS-RULES.md §7.8 — projects ranked by DISTINCT resource count desc,
    limited to 5, includes dm/pm names."""
    dm = await _seed_resource(db, "DM Top5")
    pm = await _seed_resource(db, "PM Top5")
    cl = await _seed_client(db)

    big = await _seed_project(db, cl.id, dm.id, pm.id, name="Big Team Project")
    small = await _seed_project(db, cl.id, dm.id, pm.id, name="Small Team Project")

    for i in range(3):
        r = await _seed_resource(db, f"Big Dev {i}")
        await _seed_assignment(db, big.id, r.id)
    r_small = await _seed_resource(db, "Small Dev")
    await _seed_assignment(db, small.id, r_small.id)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    top5 = data["top_5_projects_by_team_size"]

    names = [p["project_name"] for p in top5]
    assert names.index("Big Team Project") < names.index("Small Team Project")

    big_entry = next(p for p in top5 if p["project_name"] == "Big Team Project")
    assert big_entry["team_size"] == 3
    assert big_entry["dm_name"] == "DM Top5"
    assert big_entry["pm_name"] == "PM Top5"
    assert big_entry["project_id"] == str(big.id)

    small_entry = next(p for p in top5 if p["project_name"] == "Small Team Project")
    assert small_entry["team_size"] == 1


@pytest.mark.asyncio
async def test_top_5_projects_limits_to_five_and_excludes_smallest(
    client: AsyncClient, db: AsyncSession
):
    """6 active projects with distinct team sizes — only the top 5 by size are returned."""
    dm = await _seed_resource(db, "DM Six")
    pm = await _seed_resource(db, "PM Six")
    cl = await _seed_client(db)

    sizes = [6, 5, 4, 3, 2, 1]
    projects = []
    for size in sizes:
        proj = await _seed_project(db, cl.id, dm.id, pm.id, name=f"Project Size {size}")
        for i in range(size):
            r = await _seed_resource(db, f"Res {size}-{i}")
            await _seed_assignment(db, proj.id, r.id)
        projects.append(proj)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    top5 = data["top_5_projects_by_team_size"]

    assert len(top5) == 5
    assert [p["team_size"] for p in top5] == [6, 5, 4, 3, 2]
    assert "Project Size 1" not in [p["project_name"] for p in top5]


@pytest.mark.asyncio
async def test_top_5_projects_tie_breaking_both_appear(client: AsyncClient, db: AsyncSession):
    """Two projects tied on team size — both must appear (no silent drop on ties)."""
    dm = await _seed_resource(db, "DM Tie")
    pm = await _seed_resource(db, "PM Tie")
    cl = await _seed_client(db)

    proj_a = await _seed_project(db, cl.id, dm.id, pm.id, name="Tie Project A")
    proj_b = await _seed_project(db, cl.id, dm.id, pm.id, name="Tie Project B")
    for proj in (proj_a, proj_b):
        for i in range(2):
            r = await _seed_resource(db, f"Tie Dev {proj.name}-{i}")
            await _seed_assignment(db, proj.id, r.id)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    top5 = data["top_5_projects_by_team_size"]
    names = [p["project_name"] for p in top5]
    assert "Tie Project A" in names
    assert "Tie Project B" in names
    for p in top5:
        if p["project_name"] in ("Tie Project A", "Tie Project B"):
            assert p["team_size"] == 2


@pytest.mark.asyncio
async def test_top_5_projects_counts_distinct_resources_not_assignment_rows(
    client: AsyncClient, db: AsyncSession
):
    """A resource with 2 ACTIVE assignments on the same project counts once (DISTINCT resource_id)."""
    dm = await _seed_resource(db, "DM Distinct")
    pm = await _seed_resource(db, "PM Distinct")
    cl = await _seed_client(db)
    proj = await _seed_project(db, cl.id, dm.id, pm.id, name="Double Assignment Project")
    r = await _seed_resource(db, "Double Assigned Dev")
    await _seed_assignment(db, proj.id, r.id)
    await _seed_assignment(db, proj.id, r.id)  # second ACTIVE assignment, same resource
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    entry = next(
        p for p in data["top_5_projects_by_team_size"] if p["project_name"] == "Double Assignment Project"
    )
    assert entry["team_size"] == 1


@pytest.mark.asyncio
async def test_top_5_projects_excludes_non_active_projects(client: AsyncClient, db: AsyncSession):
    """A COMPLETED project with active-looking assignments is excluded from the ranking."""
    dm = await _seed_resource(db, "DM Completed")
    pm = await _seed_resource(db, "PM Completed")
    cl = await _seed_client(db)
    completed = await _seed_project(
        db, cl.id, dm.id, pm.id, name="Completed Project", status="COMPLETED"
    )
    r = await _seed_resource(db, "Completed Dev")
    await _seed_assignment(db, completed.id, r.id)
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    names = [p["project_name"] for p in data["top_5_projects_by_team_size"]]
    assert "Completed Project" not in names


# --- Bench cost summary (VRIP-106) ---


@pytest.mark.asyncio
async def test_total_bench_cost_monthly_widget(client: AsyncClient, db: AsyncSession):
    """See BUSINESS-RULES.md §7.6 — total_bench_cost_monthly sums loaded_cost_monthly
    of resources with 0 ACTIVE assignments."""
    await _seed_resource(db, "Bench Dev 1", loaded_cost_monthly=30000)
    await _seed_resource(db, "Bench Dev 2", loaded_cost_monthly=50000)
    await _seed_resource(db, "Bench Dev No Cost")
    await db.commit()

    await login_as(client)
    data = (await client.get(URL)).json()["data"]
    assert float(data["total_bench_cost_monthly"]) == 80000.0
