"""Tests for Worklog CRUD API — See VRIP-72 AC, FSD §2.11."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.modules.worklogs.models import Worklog
from tests.conftest import create_test_user, login_as

MY_URL = "/api/v1/worklogs/my"
BASE_URL = "/api/v1/worklogs"


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


async def _setup_engineer(db: AsyncSession, client: AsyncClient):
    """Create engineer user linked to resource, with project + assignment. Returns (client, resource, project)."""
    dm = await _seed_resource(db, "DM")
    resource = await _seed_resource(db, "Engineer Dev")
    cl = await _seed_client(db)
    project = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, project.id, resource.id)
    await db.commit()

    user = await create_test_user(db, "ENGINEER", name="Engineer User")
    user.resource_id = resource.id
    await db.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})
    assert resp.status_code == 200
    return client, resource, project


# ──────────────────────────────────────────────
# POST /api/v1/worklogs — Create
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_worklog_success(client: AsyncClient, db: AsyncSession):
    client, resource, project = await _setup_engineer(db, client)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today() - timedelta(days=1)),
        "hours": 4.0,
        "note": "Worked on feature X",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["hours"] == "4.0"
    assert data["note"] == "Worked on feature X"
    assert data["project"]["id"] == str(project.id)
    assert data["resource"]["id"] == str(resource.id)
    assert data["log_date"] == str(date.today() - timedelta(days=1))


@pytest.mark.asyncio
async def test_create_worklog_half_hour_increments(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 2.5,
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["hours"] == "2.5"


@pytest.mark.asyncio
async def test_create_worklog_unauthenticated(client: AsyncClient):
    resp = await client.post(BASE_URL, json={
        "project_id": str(uuid.uuid4()),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_worklog_no_resource_profile(client: AsyncClient, db: AsyncSession):
    """User without linked resource_id gets 403."""
    user = await create_test_user(db, "ENGINEER", name="No Resource")
    await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})
    resp = await client.post(BASE_URL, json={
        "project_id": str(uuid.uuid4()),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    assert resp.status_code == 403


# ──────────────────────────────────────────────
# Validation 1: worklog_enabled
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_fails_worklog_disabled(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM-dis")
    resource = await _seed_resource(db, "Dev-dis")
    cl = await _seed_client(db)
    project = await _seed_project(db, cl.id, dm.id, dm.id, worklog_enabled=False)
    await _seed_assignment(db, project.id, resource.id)
    await db.commit()

    user = await create_test_user(db, "ENGINEER")
    user.resource_id = resource.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})

    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    assert resp.status_code == 422
    assert "not enabled" in resp.json()["message"].lower()


# ──────────────────────────────────────────────
# Validation 2: active assignment covering log_date
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_fails_no_assignment(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM-noasgn")
    resource = await _seed_resource(db, "Dev-noasgn")
    cl = await _seed_client(db)
    project = await _seed_project(db, cl.id, dm.id, dm.id)
    # No assignment created
    await db.commit()

    user = await create_test_user(db, "ENGINEER")
    user.resource_id = resource.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})

    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    assert resp.status_code == 422
    assert "assignment" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_create_fails_date_before_assignment_start(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM-before")
    resource = await _seed_resource(db, "Dev-before")
    cl = await _seed_client(db)
    project = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, project.id, resource.id, start_date=date.today() - timedelta(days=5))
    await db.commit()

    user = await create_test_user(db, "ENGINEER")
    user.resource_id = resource.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})

    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today() - timedelta(days=10)),  # before assignment start
        "hours": 4.0,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_fails_date_after_assignment_end(client: AsyncClient, db: AsyncSession):
    dm = await _seed_resource(db, "DM-after")
    resource = await _seed_resource(db, "Dev-after")
    cl = await _seed_client(db)
    project = await _seed_project(db, cl.id, dm.id, dm.id)
    await _seed_assignment(db, project.id, resource.id,
                           start_date=date.today() - timedelta(days=30),
                           end_date=date.today() - timedelta(days=5))
    await db.commit()

    user = await create_test_user(db, "ENGINEER")
    user.resource_id = resource.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})

    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today() - timedelta(days=2)),  # after assignment end
        "hours": 4.0,
    })
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# Validation 3: no future dates
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_fails_future_date(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today() + timedelta(days=1)),
        "hours": 4.0,
    })
    assert resp.status_code == 422
    assert "future" in resp.json()["message"].lower()


# ──────────────────────────────────────────────
# Validation 4: hours range and increments
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_fails_hours_below_minimum(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 0.2,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_fails_hours_above_maximum(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 25.0,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_fails_hours_not_half_increment(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 3.3,
    })
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# Validation 5: duplicate entry → 409
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_fails_duplicate_entry(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    log_date = str(date.today() - timedelta(days=2))

    resp1 = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": log_date,
        "hours": 4.0,
    })
    assert resp1.status_code == 201

    resp2 = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": log_date,
        "hours": 2.0,
    })
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["message"].lower()


# ──────────────────────────────────────────────
# GET /api/v1/worklogs/my — List own
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_my_worklogs(client: AsyncClient, db: AsyncSession):
    client, resource, project = await _setup_engineer(db, client)
    # Create 2 entries
    for d in [1, 2]:
        await client.post(BASE_URL, json={
            "project_id": str(project.id),
            "log_date": str(date.today() - timedelta(days=d)),
            "hours": 4.0,
        })

    resp = await client.get(MY_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["data"]) == 2
    assert body["page"] == 1


@pytest.mark.asyncio
async def test_list_my_worklogs_filter_by_project(client: AsyncClient, db: AsyncSession):
    client, resource, project = await _setup_engineer(db, client)
    await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })

    resp = await client.get(f"{MY_URL}?project_id={project.id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp2 = await client.get(f"{MY_URL}?project_id={uuid.uuid4()}")
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_my_worklogs_filter_by_date_range(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    for d in [1, 3, 5]:
        await client.post(BASE_URL, json={
            "project_id": str(project.id),
            "log_date": str(date.today() - timedelta(days=d)),
            "hours": 2.0,
        })

    start = str(date.today() - timedelta(days=4))
    end = str(date.today() - timedelta(days=1))
    resp = await client.get(f"{MY_URL}?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2  # days 1 and 3


@pytest.mark.asyncio
async def test_list_my_worklogs_empty(client: AsyncClient, db: AsyncSession):
    client, _, _ = await _setup_engineer(db, client)
    resp = await client.get(MY_URL)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_list_my_worklogs_pagination(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    for d in range(5):
        await client.post(BASE_URL, json={
            "project_id": str(project.id),
            "log_date": str(date.today() - timedelta(days=d)),
            "hours": 2.0,
        })

    resp = await client.get(f"{MY_URL}?page=1&limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["data"]) == 2
    assert body["page"] == 1

    resp2 = await client.get(f"{MY_URL}?page=3&limit=2")
    assert len(resp2.json()["data"]) == 1


@pytest.mark.asyncio
async def test_list_my_worklogs_unauthenticated(client: AsyncClient):
    resp = await client.get(MY_URL)
    assert resp.status_code == 401


# ──────────────────────────────────────────────
# PUT /api/v1/worklogs/:id — Update
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_worklog_hours(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    create_resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    resp = await client.put(f"{BASE_URL}/{wl_id}", json={"hours": 6.5})
    assert resp.status_code == 200
    assert resp.json()["data"]["hours"] == "6.5"


@pytest.mark.asyncio
async def test_update_worklog_note(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    create_resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    resp = await client.put(f"{BASE_URL}/{wl_id}", json={"note": "Updated note"})
    assert resp.status_code == 200
    assert resp.json()["data"]["note"] == "Updated note"


@pytest.mark.asyncio
async def test_update_worklog_invalid_hours(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    create_resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    resp = await client.put(f"{BASE_URL}/{wl_id}", json={"hours": 0.3})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_worklog_not_found(client: AsyncClient, db: AsyncSession):
    client, _, _ = await _setup_engineer(db, client)
    resp = await client.put(f"{BASE_URL}/{uuid.uuid4()}", json={"hours": 4.0})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_worklog_not_owner(client: AsyncClient, db: AsyncSession):
    """User A cannot update User B's worklog."""
    # Setup user A
    client, resource_a, project = await _setup_engineer(db, client)
    create_resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    # Setup user B
    resource_b = await _seed_resource(db, "Other Engineer")
    await _seed_assignment(db, project.id, resource_b.id)
    await db.commit()
    user_b = await create_test_user(db, "ENGINEER", name="Other Eng")
    user_b.resource_id = resource_b.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user_b.email, "password": "TestPass123"})

    resp = await client.put(f"{BASE_URL}/{wl_id}", json={"hours": 8.0})
    assert resp.status_code == 403


# ──────────────────────────────────────────────
# DELETE /api/v1/worklogs/:id
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_worklog_success(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    create_resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    resp = await client.delete(f"{BASE_URL}/{wl_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify gone
    list_resp = await client.get(MY_URL)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_worklog_not_found(client: AsyncClient, db: AsyncSession):
    client, _, _ = await _setup_engineer(db, client)
    resp = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_worklog_not_owner(client: AsyncClient, db: AsyncSession):
    client, _, project = await _setup_engineer(db, client)
    create_resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    # Login as different user
    resource_b = await _seed_resource(db, "Other Eng B")
    await _seed_assignment(db, project.id, resource_b.id)
    await db.commit()
    user_b = await create_test_user(db, "ENGINEER", name="Eng B")
    user_b.resource_id = resource_b.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": user_b.email, "password": "TestPass123"})

    resp = await client.delete(f"{BASE_URL}/{wl_id}")
    assert resp.status_code == 403


# ──────────────────────────────────────────────
# Response shape
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_response_includes_project_and_resource_refs(client: AsyncClient, db: AsyncSession):
    client, resource, project = await _setup_engineer(db, client)
    create_resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    data = create_resp.json()["data"]
    assert "project" in data
    assert data["project"]["id"] == str(project.id)
    assert "name" in data["project"]
    assert "resource" in data
    assert data["resource"]["id"] == str(resource.id)
    assert "name" in data["resource"]
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_with_nonexistent_project(client: AsyncClient, db: AsyncSession):
    client, _, _ = await _setup_engineer(db, client)
    resp = await client.post(BASE_URL, json={
        "project_id": str(uuid.uuid4()),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    assert resp.status_code == 404
