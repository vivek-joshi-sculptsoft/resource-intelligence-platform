"""Cross-module worklog integration tests — See VRIP-76 AC."""

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
from tests.conftest import create_test_user, login_as, login_as_role


async def _seed_resource(db: AsyncSession, name: str, **kwargs) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name=name,
        designation=kwargs.get("designation", "Developer"),
        date_of_joining=date.today() - timedelta(days=90),
        is_active=True,
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
        worklog_enabled=kwargs.get("worklog_enabled", True),
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
        start_date=kwargs.get("start_date", date.today() - timedelta(days=60)),
        end_date=kwargs.get("end_date"),
        status=kwargs.get("status", "ACTIVE"),
    )
    db.add(a)
    await db.flush()
    return a


async def _setup_engineer(db: AsyncSession, client_http: AsyncClient, name="Eng A"):
    """Create full stack: resource → client → project → assignment → engineer user logged in."""
    dm = await _seed_resource(db, "DM Res")
    pm = await _seed_resource(db, "PM Res")
    eng = await _seed_resource(db, name, designation="Senior Developer")
    cl = await _seed_client(db)
    proj = await _seed_project(db, cl.id, dm.id, pm.id, name="Integration Proj")
    assign = await _seed_assignment(db, proj.id, eng.id)
    await db.commit()

    eng_user = await create_test_user(db, "ENGINEER", name=name)
    eng_user.resource_id = eng.id
    await db.commit()
    await client_http.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})
    return dm, pm, eng, cl, proj, assign, eng_user


# ──────────────────────────────────────────────
# 1. Full lifecycle: create → list → update → delete
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_lifecycle_create_list_update_delete(client: AsyncClient, db: AsyncSession):
    """AC: happy path — full CRUD lifecycle through API."""
    dm, pm, eng, cl, proj, assign, eng_user = await _setup_engineer(db, client)
    log_date = str(date.today() - timedelta(days=1))

    # Create
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": log_date,
        "hours": 4.0,
        "note": "Integration test work",
    })
    assert resp.status_code == 201
    wlog = resp.json()["data"]
    wlog_id = wlog["id"]
    assert float(wlog["hours"]) == 4.0
    assert wlog["project"]["name"] == "Integration Proj"
    assert wlog["resource"]["name"] == eng.name

    # List — appears in /my
    resp = await client.get("/api/v1/worklogs/my")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["data"][0]["id"] == wlog_id

    # Update hours
    resp = await client.put(f"/api/v1/worklogs/{wlog_id}", json={"hours": 6.5})
    assert resp.status_code == 200
    assert float(resp.json()["data"]["hours"]) == 6.5

    # Update note
    resp = await client.put(f"/api/v1/worklogs/{wlog_id}", json={"note": "Updated note"})
    assert resp.status_code == 200
    assert resp.json()["data"]["note"] == "Updated note"
    assert float(resp.json()["data"]["hours"]) == 6.5  # hours unchanged

    # Delete
    resp = await client.delete(f"/api/v1/worklogs/{wlog_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify gone
    resp = await client.get("/api/v1/worklogs/my")
    assert resp.json()["total"] == 0


# ──────────────────────────────────────────────
# 2. Cross-endpoint consistency
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_worklog_visible_across_all_three_endpoints(client: AsyncClient, db: AsyncSession):
    """Create via POST, verify appears in /my, /projects/:id/worklogs, /resources/:id/worklogs."""
    dm, pm, eng, cl, proj, assign, eng_user = await _setup_engineer(db, client)
    log_date = str(date.today() - timedelta(days=2))

    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": log_date,
        "hours": 3.0,
        "note": "Cross-endpoint test",
    })
    assert resp.status_code == 201

    # /my endpoint
    resp = await client.get("/api/v1/worklogs/my")
    assert resp.json()["total"] == 1

    # /resources/:id/worklogs (SELF_ONLY allows own)
    resp = await client.get(f"/api/v1/resources/{eng.id}/worklogs")
    assert resp.json()["total"] == 1
    assert resp.json()["data"][0]["note"] == "Cross-endpoint test"

    # /projects/:id/worklogs — engineer blocked (SELF_ONLY)
    resp = await client.get(f"/api/v1/projects/{proj.id}/worklogs")
    assert resp.status_code == 403

    # CEO can see via project endpoint
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{proj.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["data"][0]["resource"]["name"] == eng.name


# ──────────────────────────────────────────────
# 3. Update cannot change project_id or log_date (schema blocks)
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_ignores_project_id_and_log_date(client: AsyncClient, db: AsyncSession):
    """AC: project/date blocked on update — extra fields ignored by schema."""
    dm, pm, eng, cl, proj, assign, eng_user = await _setup_engineer(db, client)
    log_date = str(date.today() - timedelta(days=1))

    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": log_date,
        "hours": 2.0,
    })
    wlog_id = resp.json()["data"]["id"]

    # Attempt update with project_id and log_date — should be ignored
    resp = await client.put(f"/api/v1/worklogs/{wlog_id}", json={
        "hours": 3.0,
        "project_id": str(uuid.uuid4()),
        "log_date": str(date.today() - timedelta(days=10)),
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert float(data["hours"]) == 3.0
    # project and date unchanged
    assert data["project"]["id"] == str(proj.id)
    assert data["log_date"] == log_date


# ──────────────────────────────────────────────
# 4. Multi-engineer on same project
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_two_engineers_same_project_isolation(client: AsyncClient, db: AsyncSession):
    """Two engineers on same project — each sees only own worklogs via /my."""
    dm = await _seed_resource(db, "DM Multi")
    pm = await _seed_resource(db, "PM Multi")
    eng_a = await _seed_resource(db, "Engineer Alpha")
    eng_b = await _seed_resource(db, "Engineer Beta")
    cl = await _seed_client(db)
    proj = await _seed_project(db, cl.id, dm.id, pm.id, name="Multi-Eng Proj")
    await _seed_assignment(db, proj.id, eng_a.id)
    await _seed_assignment(db, proj.id, eng_b.id)
    await db.commit()

    # Engineer A logs
    user_a = await create_test_user(db, "ENGINEER", name="Alpha User")
    user_a.resource_id = eng_a.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user_a.email, "password": "TestPass123"})
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": str(date.today() - timedelta(days=1)),
        "hours": 4.0,
        "note": "Alpha work",
    })
    assert resp.status_code == 201

    # Engineer B logs
    user_b = await create_test_user(db, "ENGINEER", name="Beta User")
    user_b.resource_id = eng_b.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user_b.email, "password": "TestPass123"})
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": str(date.today() - timedelta(days=1)),
        "hours": 6.0,
        "note": "Beta work",
    })
    assert resp.status_code == 201

    # B sees only own via /my
    resp = await client.get("/api/v1/worklogs/my")
    assert resp.json()["total"] == 1
    assert resp.json()["data"][0]["note"] == "Beta work"

    # B can't see A's via /resources/:id
    resp = await client.get(f"/api/v1/resources/{eng_a.id}/worklogs")
    assert resp.status_code == 403

    # CEO sees both via /projects
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{proj.id}/worklogs")
    assert resp.json()["total"] == 2


# ──────────────────────────────────────────────
# 5. Released assignment blocks new worklogs
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_released_assignment_blocks_new_worklogs(client: AsyncClient, db: AsyncSession):
    """After assignment is released, new worklog creation should fail."""
    dm, pm, eng, cl, proj, assign, eng_user = await _setup_engineer(db, client)

    # Release assignment
    assign.status = "RELEASED"
    await db.commit()

    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": str(date.today() - timedelta(days=1)),
        "hours": 3.0,
    })
    assert resp.status_code == 422
    assert "assignment" in resp.json()["message"].lower()


# ──────────────────────────────────────────────
# 6. Existing worklogs survive assignment release
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_existing_worklogs_persist_after_release(client: AsyncClient, db: AsyncSession):
    """Worklogs created during active assignment should remain visible after release."""
    dm, pm, eng, cl, proj, assign, eng_user = await _setup_engineer(db, client)
    log_date = str(date.today() - timedelta(days=3))

    # Create worklog while active
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": log_date,
        "hours": 5.0,
        "note": "Before release",
    })
    assert resp.status_code == 201

    # Release assignment
    assign.status = "RELEASED"
    await db.commit()

    # Worklog still visible via /my
    resp = await client.get("/api/v1/worklogs/my")
    assert resp.json()["total"] == 1
    assert resp.json()["data"][0]["note"] == "Before release"

    # CEO still sees it via project
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{proj.id}/worklogs")
    assert resp.json()["total"] == 1


# ──────────────────────────────────────────────
# 7. DM portfolio scope — cross-project verification
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dm_sees_worklogs_only_on_own_projects(client: AsyncClient, db: AsyncSession):
    """DM can view project worklogs for projects they manage, not others."""
    dm_a = await _seed_resource(db, "DM Alpha")
    dm_b = await _seed_resource(db, "DM Beta")
    pm = await _seed_resource(db, "PM Shared")
    eng = await _seed_resource(db, "Eng Shared")
    cl = await _seed_client(db)

    proj_a = await _seed_project(db, cl.id, dm_a.id, pm.id, name="Proj Alpha")
    proj_b = await _seed_project(db, cl.id, dm_b.id, pm.id, name="Proj Beta")
    await _seed_assignment(db, proj_a.id, eng.id)
    await _seed_assignment(db, proj_b.id, eng.id)

    # Seed worklogs on both projects
    for proj, days in [(proj_a, 1), (proj_b, 2)]:
        w = Worklog(
            id=uuid.uuid4(),
            resource_id=eng.id,
            project_id=proj.id,
            log_date=date.today() - timedelta(days=days),
            hours=4.0,
            note=f"Work on {proj.name}",
        )
        db.add(w)
    await db.commit()

    # Login as DM Alpha
    dm_user_a = await create_test_user(db, "DM", name="DM Alpha User")
    dm_user_a.resource_id = dm_a.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user_a.email, "password": "TestPass123"})

    # Can see Proj Alpha worklogs
    resp = await client.get(f"/api/v1/projects/{proj_a.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # Cannot see Proj Beta worklogs
    resp = await client.get(f"/api/v1/projects/{proj_b.id}/worklogs")
    assert resp.status_code == 403

    # Can see eng's resource worklogs (eng is on DM Alpha's project)
    resp = await client.get(f"/api/v1/resources/{eng.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# ──────────────────────────────────────────────
# 8. All 5 validation errors end-to-end
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_all_five_validations_in_sequence(client: AsyncClient, db: AsyncSession):
    """AC: verify all 5 validation rules fire correctly in one test."""
    dm = await _seed_resource(db, "DM Val")
    pm = await _seed_resource(db, "PM Val")
    eng = await _seed_resource(db, "Eng Val")
    cl = await _seed_client(db)

    # Project with worklog disabled
    proj_disabled = await _seed_project(db, cl.id, dm.id, pm.id, name="Disabled Proj", worklog_enabled=False)
    proj_enabled = await _seed_project(db, cl.id, dm.id, pm.id, name="Enabled Proj", worklog_enabled=True)

    # Assignment only on enabled project, tight date range
    start = date.today() - timedelta(days=10)
    end = date.today() - timedelta(days=1)
    await _seed_assignment(db, proj_enabled.id, eng.id, start_date=start, end_date=end)
    await db.commit()

    user = await create_test_user(db, "ENGINEER", name="Eng Val User")
    user.resource_id = eng.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})

    valid_date = str(date.today() - timedelta(days=5))

    # V1: worklog_enabled=false → 422
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj_disabled.id),
        "log_date": valid_date,
        "hours": 4.0,
    })
    assert resp.status_code == 422
    assert "not enabled" in resp.json()["message"].lower()

    # V2: no active assignment (disabled proj has none)
    # Use enabled project but date outside range
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj_enabled.id),
        "log_date": str(date.today() - timedelta(days=30)),
        "hours": 4.0,
    })
    assert resp.status_code == 422
    assert "assignment" in resp.json()["message"].lower()

    # V3: future date → 422
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj_enabled.id),
        "log_date": str(date.today() + timedelta(days=1)),
        "hours": 4.0,
    })
    assert resp.status_code == 422
    assert "future" in resp.json()["message"].lower()

    # V4: hours invalid → 422
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj_enabled.id),
        "log_date": valid_date,
        "hours": 0.3,
    })
    assert resp.status_code == 422

    # V5: duplicate → 409 (create first, then try again)
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj_enabled.id),
        "log_date": valid_date,
        "hours": 4.0,
    })
    assert resp.status_code == 201

    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj_enabled.id),
        "log_date": valid_date,
        "hours": 3.0,
    })
    assert resp.status_code == 409
    assert "already exists" in resp.json()["message"].lower()


# ──────────────────────────────────────────────
# 9. Engineer delete isolation
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_engineer_cannot_delete_other_engineers_worklog(client: AsyncClient, db: AsyncSession):
    """AC: delete owner only — other engineer gets 403."""
    dm = await _seed_resource(db, "DM Del")
    pm = await _seed_resource(db, "PM Del")
    eng_a = await _seed_resource(db, "Eng Del A")
    eng_b = await _seed_resource(db, "Eng Del B")
    cl = await _seed_client(db)
    proj = await _seed_project(db, cl.id, dm.id, pm.id, name="Del Proj")
    await _seed_assignment(db, proj.id, eng_a.id)
    await _seed_assignment(db, proj.id, eng_b.id)

    # Seed worklog for eng_a directly
    wlog = Worklog(
        id=uuid.uuid4(),
        resource_id=eng_a.id,
        project_id=proj.id,
        log_date=date.today() - timedelta(days=1),
        hours=4.0,
    )
    db.add(wlog)
    await db.commit()

    # Login as eng_b
    user_b = await create_test_user(db, "ENGINEER", name="Del Eng B")
    user_b.resource_id = eng_b.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user_b.email, "password": "TestPass123"})

    resp = await client.delete(f"/api/v1/worklogs/{wlog.id}")
    assert resp.status_code == 403

    # Also can't update
    resp = await client.put(f"/api/v1/worklogs/{wlog.id}", json={"hours": 2.0})
    assert resp.status_code == 403


# ──────────────────────────────────────────────
# 10. Worklog with assignment start/end boundary
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_worklog_at_assignment_boundaries(client: AsyncClient, db: AsyncSession):
    """Can log on start_date and end_date, but not day before or day after."""
    dm = await _seed_resource(db, "DM Bound")
    pm = await _seed_resource(db, "PM Bound")
    eng = await _seed_resource(db, "Eng Bound")
    cl = await _seed_client(db)
    proj = await _seed_project(db, cl.id, dm.id, pm.id, name="Boundary Proj")

    start = date.today() - timedelta(days=10)
    end = date.today() - timedelta(days=2)
    await _seed_assignment(db, proj.id, eng.id, start_date=start, end_date=end)
    await db.commit()

    user = await create_test_user(db, "ENGINEER", name="Eng Bound User")
    user.resource_id = eng.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})

    # On start_date — OK
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": str(start),
        "hours": 4.0,
    })
    assert resp.status_code == 201

    # On end_date — OK
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": str(end),
        "hours": 3.0,
    })
    assert resp.status_code == 201

    # Day before start — fail
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": str(start - timedelta(days=1)),
        "hours": 2.0,
    })
    assert resp.status_code == 422

    # Day after end — fail
    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": str(end + timedelta(days=1)),
        "hours": 2.0,
    })
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# 11. Response shape verification
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_worklog_response_shape_complete(client: AsyncClient, db: AsyncSession):
    """Verify all response fields present and correctly typed."""
    dm, pm, eng, cl, proj, assign, eng_user = await _setup_engineer(db, client)
    log_date = str(date.today() - timedelta(days=1))

    resp = await client.post("/api/v1/worklogs", json={
        "project_id": str(proj.id),
        "log_date": log_date,
        "hours": 5.5,
        "note": "Shape test",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]

    # All required fields present
    assert "id" in data
    assert "project" in data
    assert "resource" in data
    assert "log_date" in data
    assert "hours" in data
    assert "note" in data
    assert "created_at" in data

    # Nested refs have id + name
    assert data["project"]["id"] == str(proj.id)
    assert data["project"]["name"] == "Integration Proj"
    assert data["resource"]["id"] == str(eng.id)
    assert data["resource"]["name"] == eng.name

    # Types — Decimal serializes to string
    assert float(data["hours"]) == 5.5
    assert data["note"] == "Shape test"
    assert data["log_date"] == log_date
