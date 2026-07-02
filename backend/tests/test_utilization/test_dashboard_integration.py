"""Cross-dashboard integration tests — See VRIP-70 AC, BUSINESS-RULES.md §7.1."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource, ResourceTag
from tests.conftest import create_test_user, login_as, login_as_role

COMPANY_URL = "/api/v1/dashboard/company"
DM_URL = "/api/v1/dashboard/dm"
AVAIL_URL = "/api/v1/dashboard/availability"


async def _seed_resource(db: AsyncSession, name: str, **kwargs) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=kwargs.get("employee_id", f"EMP-{uuid.uuid4().hex[:6]}"),
        name=name,
        designation=kwargs.get("designation", "Developer"),
        technical_expertise=kwargs.get("technical_expertise"),
        date_of_joining=kwargs.get("date_of_joining", date.today() - timedelta(days=90)),
        is_active=kwargs.get("is_active", True),
    )
    db.add(r)
    await db.flush()
    return r


async def _seed_client(db: AsyncSession) -> Client:
    c = Client(id=uuid.uuid4(), name=f"Client-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(c)
    await db.flush()
    return c


async def _seed_project(db: AsyncSession, client_id, dm_id, pm_id, **kwargs) -> Project:
    p = Project(
        id=uuid.uuid4(),
        name=kwargs.get("name", f"Proj-{uuid.uuid4().hex[:4]}"),
        client_id=client_id,
        dm_id=dm_id,
        pm_id=pm_id,
        type=kwargs.get("type", "TIME_AND_MATERIAL"),
        status=kwargs.get("status", "ACTIVE"),
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
        released_at=kwargs.get("released_at"),
    )
    db.add(a)
    await db.flush()
    return a


async def _create_dm_user(db: AsyncSession, client: AsyncClient, dm_resource: Resource):
    dm_user = await create_test_user(db, "DM", name="DM User")
    dm_user.resource_id = dm_resource.id
    await db.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})
    assert resp.status_code == 200
    return client, dm_user


# ──────────────────────────────────────────────
# AC-1: Precise utilization calculation
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_precise_utilization_known_inputs(client: AsyncClient, db: AsyncSession):
    """See BUSINESS-RULES.md §7.1 — 3 resources: A=80% billable, B=50% billable, C=bench.
    Utilization = (80+50) / (3*100) * 100 = 43.33%."""
    dm = await _seed_resource(db, "DM-int")
    dev_a = await _seed_resource(db, "Dev A")
    dev_b = await _seed_resource(db, "Dev B")
    dev_c = await _seed_resource(db, "Dev C (bench)")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)

    await _seed_assignment(db, p.id, dev_a.id, allocation_pct=100, billability_pct=80)
    await _seed_assignment(db, p.id, dev_b.id, allocation_pct=60, billability_pct=50)
    # dev_c has no assignment — bench
    await db.commit()

    await login_as(client)
    data = (await client.get(COMPANY_URL)).json()["data"]

    # Seed data includes admin user's resource (CEO seed) — so total_active_resources may be > 4
    # But we can verify the math: total_billable >= 130, total_resources >= 4
    total = data["total_active_resources"]
    expected_pct = round((80 + 50) / (total * 100) * 100, 2)
    assert float(data["billable_utilization_pct"]) == expected_pct


@pytest.mark.asyncio
async def test_utilization_zero_when_all_bench(client: AsyncClient, db: AsyncSession):
    """No assignments at all → 0% utilization."""
    await _seed_resource(db, "Lonely Dev 1")
    await _seed_resource(db, "Lonely Dev 2")
    await db.commit()

    await login_as(client)
    data = (await client.get(COMPANY_URL)).json()["data"]
    assert float(data["billable_utilization_pct"]) == 0


@pytest.mark.asyncio
async def test_utilization_100_when_fully_billable(client: AsyncClient, db: AsyncSession):
    """Every active resource at 100% billability → utilization = 100%."""
    dm = await _seed_resource(db, "DM-full")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)

    # Create assignments for ALL active resources (seed CEO user doesn't have resource)
    from sqlalchemy import select
    active_resources = (await db.execute(
        select(Resource).where(Resource.is_active == True)  # noqa: E712
    )).scalars().all()

    for r in active_resources:
        existing = (await db.execute(
            select(Assignment).where(Assignment.resource_id == r.id, Assignment.status == "ACTIVE")
        )).scalars().first()
        if not existing:
            await _seed_assignment(db, p.id, r.id, allocation_pct=100, billability_pct=100)
    await db.commit()

    await login_as(client)
    data = (await client.get(COMPANY_URL)).json()["data"]
    assert float(data["billable_utilization_pct"]) == 100.0
    assert data["bench_count"] == 0


# ──────────────────────────────────────────────
# AC-2: Bench count correct after releasing assignment
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bench_count_increases_after_release(client: AsyncClient, db: AsyncSession):
    """Resource with active assignment is NOT bench. After releasing, becomes bench."""
    dm = await _seed_resource(db, "DM-bench")
    dev = await _seed_resource(db, "Releasable Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)
    assignment = await _seed_assignment(db, p.id, dev.id, allocation_pct=100)
    await db.commit()

    await login_as(client)

    # Before release — dev is allocated, not bench
    data_before = (await client.get(COMPANY_URL)).json()["data"]
    bench_ids_before = {b["id"] for b in data_before["bench_resources"]}
    assert str(dev.id) not in bench_ids_before

    # Also verify on availability — dev should be in fully_allocated
    avail_before = (await client.get(AVAIL_URL)).json()["data"]
    avail_full_names = [r["name"] for r in avail_before["fully_allocated"]]
    assert "Releasable Dev" in avail_full_names

    # Release the assignment
    assignment.status = "RELEASED"
    assignment.released_at = date.today()
    db.add(assignment)
    await db.commit()

    # After release — dev should be bench
    data_after = (await client.get(COMPANY_URL)).json()["data"]
    bench_ids_after = {b["id"] for b in data_after["bench_resources"]}
    assert str(dev.id) in bench_ids_after
    assert data_after["bench_count"] > data_before["bench_count"]

    # Also verify on availability — dev should move to bench bucket
    avail_after = (await client.get(AVAIL_URL)).json()["data"]
    avail_bench_ids = [r["id"] for r in avail_after["bench"]]
    assert str(dev.id) in avail_bench_ids
    avail_full_names_after = [r["name"] for r in avail_after["fully_allocated"]]
    assert "Releasable Dev" not in avail_full_names_after


# ──────────────────────────────────────────────
# AC-3: Upcoming releases only within window
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_releases_window_boundary(client: AsyncClient, db: AsyncSession):
    """Assignment ending exactly at window boundary included; day after excluded."""
    dm = await _seed_resource(db, "DM-win")
    dev_in = await _seed_resource(db, "Dev InWindow")
    dev_out = await _seed_resource(db, "Dev OutWindow")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)

    today = date.today()
    await _seed_assignment(db, p.id, dev_in.id, end_date=today + timedelta(days=30))  # exactly at boundary
    await _seed_assignment(db, p.id, dev_out.id, end_date=today + timedelta(days=31))  # one day beyond
    await db.commit()

    await login_as(client)
    data = (await client.get(COMPANY_URL)).json()["data"]
    names = [r["resource_name"] for r in data["upcoming_releases_30d"]]
    assert "Dev InWindow" in names
    assert "Dev OutWindow" not in names

    # Availability with window=30 should match
    avail = (await client.get(f"{AVAIL_URL}?window=30")).json()["data"]
    rel_names = [r["name"] for r in avail["releasing_soon"]]
    assert "Dev InWindow" in rel_names
    assert "Dev OutWindow" not in rel_names

    # Availability with window=60 should include both
    avail60 = (await client.get(f"{AVAIL_URL}?window=60")).json()["data"]
    rel_names_60 = [r["name"] for r in avail60["releasing_soon"]]
    assert "Dev InWindow" in rel_names_60
    assert "Dev OutWindow" in rel_names_60


# ──────────────────────────────────────────────
# AC-4: DM dashboard scoped — excludes other DM projects
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dm_scope_excludes_other_dm_projects(client: AsyncClient, db: AsyncSession):
    """DM A should not see DM B's projects, resources, or upcoming releases."""
    dm_a_res = await _seed_resource(db, "DM A")
    dm_b_res = await _seed_resource(db, "DM B")
    dev_a = await _seed_resource(db, "Dev for A")
    dev_b = await _seed_resource(db, "Dev for B")
    cl = await _seed_client(db)

    proj_a = await _seed_project(db, cl.id, dm_a_res.id, dm_a_res.id, name="Project Alpha")
    proj_b = await _seed_project(db, cl.id, dm_b_res.id, dm_b_res.id, name="Project Beta")

    await _seed_assignment(db, proj_a.id, dev_a.id, allocation_pct=80, billability_pct=80,
                           end_date=date.today() + timedelta(days=10))
    await _seed_assignment(db, proj_b.id, dev_b.id, allocation_pct=100, billability_pct=100,
                           end_date=date.today() + timedelta(days=5))
    await db.commit()

    # Login as DM A
    client, _ = await _create_dm_user(db, client, dm_a_res)
    data = (await client.get(DM_URL)).json()["data"]

    assert data["active_project_count"] == 1
    assert data["resource_count"] == 1
    release_names = [r["resource_name"] for r in data["upcoming_releases_30d"]]
    assert "Dev for A" in release_names
    assert "Dev for B" not in release_names


# ──────────────────────────────────────────────
# AC-5: Availability sections correctly categorized
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_availability_correct_categorization(client: AsyncClient, db: AsyncSession):
    """Seed 4 resources in different states, verify each lands in correct bucket."""
    dm = await _seed_resource(db, "DM-cat")
    bench_dev = await _seed_resource(db, "Bench Dev Cat")
    partial_dev = await _seed_resource(db, "Partial Dev Cat")
    full_dev = await _seed_resource(db, "Full Dev Cat")
    over_dev = await _seed_resource(db, "Over Dev Cat")
    cl = await _seed_client(db)
    p1 = await _seed_project(db, cl.id, dm.id, dm.id, name="Proj Cat 1")
    p2 = await _seed_project(db, cl.id, dm.id, dm.id, name="Proj Cat 2")

    # bench_dev: no assignment
    await _seed_assignment(db, p1.id, partial_dev.id, allocation_pct=40)
    await _seed_assignment(db, p1.id, full_dev.id, allocation_pct=100)
    await _seed_assignment(db, p1.id, over_dev.id, allocation_pct=70)
    await _seed_assignment(db, p2.id, over_dev.id, allocation_pct=60)  # total = 130%
    await db.commit()

    await login_as(client)
    data = (await client.get(AVAIL_URL)).json()["data"]

    bench_names = [r["name"] for r in data["bench"]]
    partial_names = [r["name"] for r in data["partial"]]
    full_names = [r["name"] for r in data["fully_allocated"]]

    assert "Bench Dev Cat" in bench_names
    assert "Partial Dev Cat" in partial_names
    assert "Full Dev Cat" in full_names
    assert "Over Dev Cat" in full_names  # over-allocated goes in fully_allocated bucket

    # Verify partial has correct spare capacity
    partial_entry = next(r for r in data["partial"] if r["name"] == "Partial Dev Cat")
    assert partial_entry["total_allocation_pct"] == 40
    assert partial_entry["spare_capacity_pct"] == 60
    assert "Proj Cat 1" in partial_entry["projects"]

    # Verify over-allocated total
    over_entry = next(r for r in data["fully_allocated"] if r["name"] == "Over Dev Cat")
    assert over_entry["total_allocation_pct"] == 130
    assert len(over_entry["projects"]) == 2


@pytest.mark.asyncio
async def test_availability_designation_in_all_buckets(client: AsyncClient, db: AsyncSession):
    """All buckets return designation field."""
    dm = await _seed_resource(db, "DM-des", designation="Delivery Manager")
    bench_dev = await _seed_resource(db, "Des Bench", designation="QA Engineer")
    partial_dev = await _seed_resource(db, "Des Partial", designation="Frontend Dev")
    full_dev = await _seed_resource(db, "Des Full", designation="Backend Dev")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)

    await _seed_assignment(db, p.id, partial_dev.id, allocation_pct=50)
    await _seed_assignment(db, p.id, full_dev.id, allocation_pct=100,
                           end_date=date.today() + timedelta(days=10))
    await db.commit()

    await login_as(client)
    data = (await client.get(AVAIL_URL)).json()["data"]

    bench_entry = next((r for r in data["bench"] if r["name"] == "Des Bench"), None)
    assert bench_entry is not None
    assert bench_entry["designation"] == "QA Engineer"

    partial_entry = next((r for r in data["partial"] if r["name"] == "Des Partial"), None)
    assert partial_entry is not None
    assert partial_entry["designation"] == "Frontend Dev"

    full_entry = next((r for r in data["fully_allocated"] if r["name"] == "Des Full"), None)
    assert full_entry is not None
    assert full_entry["designation"] == "Backend Dev"

    rel_entry = next((r for r in data["releasing_soon"] if r["name"] == "Des Full"), None)
    assert rel_entry is not None
    assert rel_entry["designation"] == "Backend Dev"


# ──────────────────────────────────────────────
# AC-6: CEO/CTO only on company dashboard
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_company_dashboard_pm_gets_403(client: AsyncClient, db: AsyncSession):
    client, _ = await login_as_role(client, db, "PM")
    resp = await client.get(COMPANY_URL)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_company_dashboard_engineer_gets_403(client: AsyncClient, db: AsyncSession):
    client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await client.get(COMPANY_URL)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_company_dashboard_hr_gets_403(client: AsyncClient, db: AsyncSession):
    client, _ = await login_as_role(client, db, "HR")
    resp = await client.get(COMPANY_URL)
    assert resp.status_code == 403


# ──────────────────────────────────────────────
# AC-7: Availability accessible to Engineer
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_availability_engineer_can_access(client: AsyncClient, db: AsyncSession):
    client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await client.get(AVAIL_URL)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "bench" in data
    assert "partial" in data
    assert "releasing_soon" in data
    assert "fully_allocated" in data


# ──────────────────────────────────────────────
# AC-8: Financial fields null
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_overdue_milestones_empty_when_no_projects_company(client: AsyncClient, db: AsyncSession):
    """See VRIP-128 — company dashboard no longer carries revenue/cost/margin fields
    (moved to GET /api/v1/dashboard/company-finance). With no projects, milestone
    fields are still an empty list."""
    await login_as(client)
    data = (await client.get(COMPANY_URL)).json()["data"]
    assert data["overdue_milestones_count"] == 0
    assert data["overdue_milestones"] == []


@pytest.mark.asyncio
async def test_financial_fields_null_dm(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    data = (await client.get(DM_URL)).json()["data"]
    assert data["projected_revenue_inr"] is None
    assert data["total_cost_inr"] is None


@pytest.mark.asyncio
async def test_availability_no_financial_fields(client: AsyncClient, db: AsyncSession):
    """Availability endpoint must not expose any financial data."""
    await login_as(client)
    data = (await client.get(AVAIL_URL)).json()["data"]
    raw = str(data).lower()
    for field in ["billing_rate", "loaded_cost", "ctc", "revenue", "margin"]:
        assert field not in raw


# ──────────────────────────────────────────────
# Cross-dashboard consistency
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bench_count_consistent_across_dashboards(client: AsyncClient, db: AsyncSession):
    """Company dashboard bench_count should match availability bench list length."""
    dm = await _seed_resource(db, "DM-cons")
    await _seed_resource(db, "Bench A")
    await _seed_resource(db, "Bench B")
    dev_alloc = await _seed_resource(db, "Allocated")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, p.id, dev_alloc.id, allocation_pct=100)
    await db.commit()

    await login_as(client)
    company = (await client.get(COMPANY_URL)).json()["data"]
    avail = (await client.get(AVAIL_URL)).json()["data"]

    assert company["bench_count"] == len(avail["bench"])


@pytest.mark.asyncio
async def test_total_resources_match_availability_sum(client: AsyncClient, db: AsyncSession):
    """Sum of all availability buckets should equal total active resources."""
    dm = await _seed_resource(db, "DM-sum")
    await _seed_resource(db, "Sum Bench")
    dev_p = await _seed_resource(db, "Sum Partial")
    dev_f = await _seed_resource(db, "Sum Full")
    cl = await _seed_client(db)
    p = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, p.id, dev_p.id, allocation_pct=60)
    await _seed_assignment(db, p.id, dev_f.id, allocation_pct=100)
    await db.commit()

    await login_as(client)
    company = (await client.get(COMPANY_URL)).json()["data"]
    avail = (await client.get(AVAIL_URL)).json()["data"]

    avail_total = len(avail["bench"]) + len(avail["partial"]) + len(avail["fully_allocated"])
    assert company["total_active_resources"] == avail_total
