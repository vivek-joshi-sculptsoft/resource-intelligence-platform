"""End-to-end smoke tests — See VRIP-77 AC.

Golden path, RBAC, data cascade, status lifecycle, auto-release.
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.modules.worklogs.models import Worklog
from tests.conftest import create_test_user, login_as, login_as_role


# ──────────────────────────────────────────────
# AC1: Golden path
# CEO → create client → create project → assign resource
# → dashboard updates → log worklog → worklog in project detail
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_golden_path_end_to_end(client: AsyncClient, db: AsyncSession):
    """Full happy path from login to worklog visible in project detail."""
    # 1. Login as CEO
    await login_as(client)

    # 2. Create client
    resp = await client.post("/api/v1/clients", json={
        "name": "Golden Client Ltd",
        "billing_currency": "INR",
    })
    assert resp.status_code == 201
    client_id = resp.json()["data"]["id"]

    # 3. Create resource (DM, PM, engineer)
    dm_res = Resource(
        id=uuid.uuid4(), employee_id="EMP-DM-GP", name="DM Golden",
        designation="Delivery Manager", date_of_joining=date.today() - timedelta(days=365),
        is_active=True,
    )
    pm_res = Resource(
        id=uuid.uuid4(), employee_id="EMP-PM-GP", name="PM Golden",
        designation="Project Manager", date_of_joining=date.today() - timedelta(days=300),
        is_active=True,
    )
    eng_res = Resource(
        id=uuid.uuid4(), employee_id="EMP-ENG-GP", name="Eng Golden",
        designation="Senior Developer", date_of_joining=date.today() - timedelta(days=200),
        is_active=True,
    )
    db.add_all([dm_res, pm_res, eng_res])
    await db.commit()

    # 4. Create project (T&M requires contract_end_date)
    resp = await client.post("/api/v1/projects", json={
        "name": "Golden Project",
        "client_id": client_id,
        "type": "TIME_AND_MATERIAL",
        "billing_currency": "INR",
        "dm_id": str(dm_res.id),
        "pm_id": str(pm_res.id),
        "worklog_enabled": True,
        "start_date": str(date.today() - timedelta(days=30)),
        "contract_end_date": str(date.today() + timedelta(days=180)),
    })
    assert resp.status_code == 201, resp.json()
    project_id = resp.json()["data"]["id"]

    # 5. Assign resource
    resp = await client.post(f"/api/v1/projects/{project_id}/assignments", json={
        "resource_id": str(eng_res.id),
        "allocation_pct": 80,
        "billability_pct": 80,
        "is_shadow": False,
        "start_date": str(date.today() - timedelta(days=20)),
    })
    assert resp.status_code == 201, resp.json()

    # 6. Dashboard updates — utilization shows data
    resp = await client.get("/api/v1/dashboard/company")
    assert resp.status_code == 200
    dashboard = resp.json()["data"]
    assert dashboard["total_active_resources"] >= 1

    # 7. Availability shows engineer as allocated
    resp = await client.get("/api/v1/dashboard/availability?window=30")
    assert resp.status_code == 200
    avail = resp.json()["data"]
    all_names = []
    for bucket in ["partial", "fully_allocated", "bench"]:
        all_names.extend(r["name"] for r in avail.get(bucket, []))
    assert "Eng Golden" in all_names

    # 8. Log worklog as engineer
    eng_user = await create_test_user(db, "ENGINEER", name="Eng Golden User")
    eng_user.resource_id = eng_res.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={
        "email": eng_user.email, "password": "TestPass123",
    })

    log_date = str(date.today() - timedelta(days=1))
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": project_id,
        "log_date": log_date,
        "hours": 6.0,
        "note": "Golden path worklog",
    })
    assert resp.status_code == 201, resp.json()

    # 9. Worklog visible via /my
    resp = await client.get("/api/v1/worklogs/my")
    assert resp.json()["total"] == 1
    assert resp.json()["data"][0]["note"] == "Golden path worklog"

    # 10. Worklog visible in project detail (CEO)
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{project_id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["data"][0]["resource"]["name"] == "Eng Golden"


# ──────────────────────────────────────────────
# AC2: RBAC smoke — each of 7 roles, correct 403s
# ──────────────────────────────────────────────


ROLE_EXPECTED = {
    "CEO":      {"clients": 200, "projects": 200, "resources": 200, "company_dash": 200, "create_client": 201},
    "CTO":      {"clients": 200, "projects": 200, "resources": 200, "company_dash": 200, "create_client": 201},
    "DM":       {"clients": 200, "projects": 200, "resources": 200, "company_dash": 403, "create_client": 403},
    "PM":       {"clients": 200, "projects": 200, "resources": 200, "company_dash": 403, "create_client": 403},
    "FINANCE":  {"clients": 200, "projects": 200, "resources": 200, "company_dash": 403, "create_client": 403},
    "HR":       {"clients": 200, "projects": 200, "resources": 200, "company_dash": 403, "create_client": 403},
    "ENGINEER": {"clients": 403, "projects": 403, "resources": 200, "company_dash": 403, "create_client": 403},
}


@pytest.mark.asyncio
@pytest.mark.parametrize("role_code", ["CEO", "CTO", "DM", "PM", "FINANCE", "HR", "ENGINEER"])
async def test_rbac_smoke_per_role(client: AsyncClient, db: AsyncSession, role_code: str):
    """AC: each of 7 roles → correct 403s on sample endpoints."""
    if role_code == "CEO":
        await login_as(client)
    else:
        client, _ = await login_as_role(client, db, role_code)

    expected = ROLE_EXPECTED[role_code]

    # GET /clients
    resp = await client.get("/api/v1/clients")
    assert resp.status_code == expected["clients"], f"{role_code} GET /clients: got {resp.status_code}"

    # GET /projects
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == expected["projects"], f"{role_code} GET /projects: got {resp.status_code}"

    # GET /resources
    resp = await client.get("/api/v1/resources")
    assert resp.status_code == expected["resources"], f"{role_code} GET /resources: got {resp.status_code}"

    # GET /dashboard/company
    resp = await client.get("/api/v1/dashboard/company")
    assert resp.status_code == expected["company_dash"], f"{role_code} GET company_dash: got {resp.status_code}"

    # POST /clients (create)
    resp = await client.post("/api/v1/clients", json={"name": f"RBAC-{role_code}-test"})
    if expected["create_client"] == 201:
        assert resp.status_code == 201, f"{role_code} POST /clients: got {resp.status_code}"
    else:
        assert resp.status_code == 403, f"{role_code} POST /clients: got {resp.status_code}"


# ──────────────────────────────────────────────
# AC3: Data cascade — deactivate resource → resource inactive
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deactivate_resource_cascade(client: AsyncClient, db: AsyncSession):
    """AC: deactivate resource → resource inactive, assignment status checked."""
    await login_as(client)

    # Seed resource with assignment
    dm = Resource(id=uuid.uuid4(), employee_id="EMP-DM-DC", name="DM Cascade",
                  designation="DM", date_of_joining=date.today() - timedelta(days=365), is_active=True)
    pm = Resource(id=uuid.uuid4(), employee_id="EMP-PM-DC", name="PM Cascade",
                  designation="PM", date_of_joining=date.today() - timedelta(days=365), is_active=True)
    eng = Resource(id=uuid.uuid4(), employee_id="EMP-ENG-DC", name="Eng Cascade",
                   designation="Developer", date_of_joining=date.today() - timedelta(days=200), is_active=True)
    cl = Client(id=uuid.uuid4(), name="Cascade Client", is_active=True)
    db.add_all([dm, pm, eng, cl])
    await db.flush()

    proj = Project(id=uuid.uuid4(), name="Cascade Proj", client_id=cl.id, dm_id=dm.id,
                   pm_id=pm.id, status="ACTIVE", is_active=True, worklog_enabled=False)
    db.add(proj)
    await db.flush()

    assignment = Assignment(id=uuid.uuid4(), project_id=proj.id, resource_id=eng.id,
                            allocation_pct=100, billability_pct=100,
                            start_date=date.today() - timedelta(days=30), status="ACTIVE")
    db.add(assignment)
    await db.commit()

    # Verify assignment is ACTIVE via API
    resp = await client.get(f"/api/v1/resources/{eng.id}/assignments?status=ACTIVE")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    # Deactivate resource via DELETE (soft delete)
    resp = await client.delete(f"/api/v1/resources/{eng.id}")
    assert resp.status_code == 200

    # Verify resource is now inactive
    resp = await client.get(f"/api/v1/resources/{eng.id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False

    # Resource no longer in active resources list
    resp = await client.get("/api/v1/resources?status=ACTIVE")
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()["data"]]
    assert "Eng Cascade" not in names


# ──────────────────────────────────────────────
# AC4: Status lifecycle — project ACTIVE → COMPLETED → assignments released
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_project_status_lifecycle(client: AsyncClient, db: AsyncSession):
    """AC: create → complete → assignments released → no further transitions."""
    await login_as(client)

    dm = Resource(id=uuid.uuid4(), employee_id="EMP-DM-SL", name="DM Lifecycle",
                  designation="DM", date_of_joining=date.today() - timedelta(days=365), is_active=True)
    pm = Resource(id=uuid.uuid4(), employee_id="EMP-PM-SL", name="PM Lifecycle",
                  designation="PM", date_of_joining=date.today() - timedelta(days=365), is_active=True)
    eng = Resource(id=uuid.uuid4(), employee_id="EMP-ENG-SL", name="Eng Lifecycle",
                   designation="Dev", date_of_joining=date.today() - timedelta(days=200), is_active=True)
    cl = Client(id=uuid.uuid4(), name="Lifecycle Client", is_active=True)
    db.add_all([dm, pm, eng, cl])
    await db.flush()

    proj = Project(id=uuid.uuid4(), name="Lifecycle Proj", client_id=cl.id, dm_id=dm.id,
                   pm_id=pm.id, status="ACTIVE", is_active=True, worklog_enabled=False)
    db.add(proj)
    await db.flush()

    assign = Assignment(id=uuid.uuid4(), project_id=proj.id, resource_id=eng.id,
                        allocation_pct=50, billability_pct=50,
                        start_date=date.today() - timedelta(days=30), status="ACTIVE")
    db.add(assign)
    await db.commit()

    # Transition ACTIVE → COMPLETED via PUT /status
    resp = await client.put(f"/api/v1/projects/{proj.id}/status", json={"status": "COMPLETED"})
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["status"] == "COMPLETED"

    # Assignment should be auto-released — re-fetch from fresh session
    await db.close()
    result = await db.execute(
        select(Assignment).where(Assignment.id == assign.id)
    )
    released = result.scalar_one()
    assert released.status in {"RELEASED", "AUTO_RELEASED"}

    # No further transitions from COMPLETED
    resp = await client.put(f"/api/v1/projects/{proj.id}/status", json={"status": "ACTIVE"})
    assert resp.status_code == 400


# ──────────────────────────────────────────────
# AC5: Auto-release simulation
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_auto_release_job_simulation(client: AsyncClient, db: AsyncSession):
    """AC: end_date=today → trigger job → AUTO_RELEASED."""
    await login_as(client)

    dm = Resource(id=uuid.uuid4(), employee_id="EMP-DM-AR", name="DM AutoRel",
                  designation="DM", date_of_joining=date.today() - timedelta(days=365), is_active=True)
    pm = Resource(id=uuid.uuid4(), employee_id="EMP-PM-AR", name="PM AutoRel",
                  designation="PM", date_of_joining=date.today() - timedelta(days=365), is_active=True)
    eng = Resource(id=uuid.uuid4(), employee_id="EMP-ENG-AR", name="Eng AutoRel",
                   designation="Dev", date_of_joining=date.today() - timedelta(days=200), is_active=True)
    cl = Client(id=uuid.uuid4(), name="AutoRel Client", is_active=True)
    db.add_all([dm, pm, eng, cl])
    await db.flush()

    proj = Project(id=uuid.uuid4(), name="AutoRel Proj", client_id=cl.id, dm_id=dm.id,
                   pm_id=pm.id, status="ACTIVE", is_active=True, worklog_enabled=False)
    db.add(proj)
    await db.flush()

    # Assignment with end_date = today (should be auto-released)
    assign = Assignment(id=uuid.uuid4(), project_id=proj.id, resource_id=eng.id,
                        allocation_pct=100, billability_pct=100,
                        start_date=date.today() - timedelta(days=30),
                        end_date=date.today(), status="ACTIVE")
    db.add(assign)
    await db.commit()

    # Trigger auto-release job
    resp = await client.post("/api/v1/jobs/auto-release")
    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert body["released_count"] >= 1

    # Verify assignment status from fresh query
    await db.close()
    result = await db.execute(
        select(Assignment).where(Assignment.id == assign.id)
    )
    released = result.scalar_one()
    assert released.status == "AUTO_RELEASED"
    assert released.released_at is not None

    # Verify resource now appears as bench in availability
    resp = await client.get("/api/v1/dashboard/availability?window=30")
    assert resp.status_code == 200
    avail = resp.json()["data"]
    bench_names = [r["name"] for r in avail.get("bench", [])]
    assert "Eng AutoRel" in bench_names


# ──────────────────────────────────────────────
# AC6: Cross-module consistency — create through API, verify all views
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cross_module_data_consistency(client: AsyncClient, db: AsyncSession):
    """Create data through APIs, verify consistency across modules."""
    await login_as(client)

    # Create resource via API
    resp = await client.post("/api/v1/resources", json={
        "employee_id": "EMP-XMOD-001",
        "name": "Cross Module Dev",
        "designation": "Full Stack Developer",
        "date_of_joining": str(date.today() - timedelta(days=100)),
    })
    assert resp.status_code == 201
    resource_id = resp.json()["data"]["id"]

    # Create client via API
    resp = await client.post("/api/v1/clients", json={"name": "Cross Module Client"})
    assert resp.status_code == 201
    client_id = resp.json()["data"]["id"]

    # Resource visible in resource list
    resp = await client.get("/api/v1/resources")
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()["data"]]
    assert "Cross Module Dev" in names

    # Client visible in client list
    resp = await client.get("/api/v1/clients")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()["data"]]
    assert "Cross Module Client" in names

    # Resource should appear on bench in availability
    resp = await client.get("/api/v1/dashboard/availability?window=30")
    assert resp.status_code == 200
    avail = resp.json()["data"]
    bench_names = [r["name"] for r in avail.get("bench", [])]
    assert "Cross Module Dev" in bench_names


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Sanity: health endpoint responds."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
