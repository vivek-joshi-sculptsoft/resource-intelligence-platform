import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from tests.conftest import create_test_user, login_as, login_as_role


async def _create_client(db: AsyncSession, name: str = "Test Client") -> Client:
    c = Client(id=uuid.uuid4(), name=name, is_active=True)
    db.add(c)
    await db.commit()
    return c


async def _create_resource(db: AsyncSession, name: str = "Test Resource") -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name=name,
        designation="Senior Engineer",
        is_active=True,
    )
    db.add(r)
    await db.commit()
    return r


async def _setup_project_deps(db: AsyncSession):
    client = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    dm = await _create_resource(db, "DM Person")
    pm = await _create_resource(db, "PM Person")
    return client, dm, pm


def _project_payload(client_id, dm_id, pm_id, **overrides):
    payload = {
        "name": overrides.get("name", f"Project-{uuid.uuid4().hex[:6]}"),
        "client_id": str(client_id),
        "type": overrides.get("type", "TIME_AND_MATERIAL"),
        "dm_id": str(dm_id),
        "pm_id": str(pm_id),
        "contract_end_date": overrides.get("contract_end_date", "2026-12-31"),
    }
    payload.update({k: v for k, v in overrides.items() if k not in payload})
    return payload


# ===== CRUD Happy Paths =====


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    payload = _project_payload(cl.id, dm.id, pm.id, name="Alpha Project")

    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Alpha Project"
    assert data["client"]["id"] == str(cl.id)
    assert data["dm"]["id"] == str(dm.id)
    assert data["pm"]["id"] == str(pm.id)
    assert data["status"] == "ACTIVE"
    assert data["contract_value"] is None


@pytest.mark.asyncio
async def test_list_projects_paginated(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)

    for i in range(3):
        await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id, name=f"Proj-{i}"))

    resp = await client.get("/api/v1/projects?limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert data["meta"]["total"] >= 3


@pytest.mark.asyncio
async def test_list_projects_filter_status(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))

    resp = await client.get("/api/v1/projects?status=ACTIVE")
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_list_projects_filter_client(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))

    resp = await client.get(f"/api/v1/projects?client_id={cl.id}")
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["client_name"] == cl.name


@pytest.mark.asyncio
async def test_list_projects_filter_type(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm.id, pm.id, type="FIXED_PRICE"),
    )

    resp = await client.get("/api/v1/projects?type=FIXED_PRICE")
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["type"] == "FIXED_PRICE"


@pytest.mark.asyncio
async def test_list_projects_search(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm.id, pm.id, name="UniqueSearchName"),
    )

    resp = await client.get("/api/v1/projects?search=UniqueSearch")
    assert resp.status_code == 200
    assert any(p["name"] == "UniqueSearchName" for p in resp.json()["data"])


@pytest.mark.asyncio
async def test_get_project_detail(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["client"]["name"] == cl.name
    assert data["dm"]["name"] == dm.name
    assert data["pm"]["name"] == pm.name
    assert data["worklog_enabled"] is False


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/projects/{pid}", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_project_partial(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm.id, pm.id, name="Before", notes="old"),
    )
    pid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/projects/{pid}", json={"notes": "new notes"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["notes"] == "new notes"
    assert data["name"] == "Before"


# ===== Validation =====


@pytest.mark.asyncio
async def test_create_missing_required_fields(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.post("/api/v1/projects", json={"name": "Incomplete"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_tm_without_end_date(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    payload = _project_payload(cl.id, dm.id, pm.id, type="TIME_AND_MATERIAL")
    del payload["contract_end_date"]

    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_onboarding_without_end_date(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    payload = _project_payload(cl.id, dm.id, pm.id, type="CLIENT_ONBOARDING")
    del payload["contract_end_date"]

    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_fixed_price_without_end_date(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    payload = _project_payload(cl.id, dm.id, pm.id, type="FIXED_PRICE")
    del payload["contract_end_date"]

    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_with_inactive_client(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    inactive_client = Client(id=uuid.uuid4(), name="Inactive Co", is_active=False)
    db.add(inactive_client)
    await db.commit()
    _, dm, pm = await _setup_project_deps(db)

    payload = _project_payload(inactive_client.id, dm.id, pm.id)
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_with_inactive_dm(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, _, pm = await _setup_project_deps(db)
    inactive_dm = Resource(
        id=uuid.uuid4(), employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name="Inactive DM", designation="DM", is_active=False,
    )
    db.add(inactive_dm)
    await db.commit()

    payload = _project_payload(cl.id, inactive_dm.id, pm.id)
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_with_nonexistent_client(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    _, dm, pm = await _setup_project_deps(db)
    payload = _project_payload(uuid.uuid4(), dm.id, pm.id)
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_project(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{uuid.uuid4()}")
    assert resp.status_code == 404


# ===== Status Transitions =====


@pytest.mark.asyncio
async def test_transition_active_to_completed(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/projects/{pid}/status", json={"status": "COMPLETED"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_transition_active_to_on_hold(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/projects/{pid}/status", json={"status": "ON_HOLD"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ON_HOLD"


@pytest.mark.asyncio
async def test_transition_active_to_cancelled(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/projects/{pid}/status", json={"status": "CANCELLED"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_transition_on_hold_to_active(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    await client.put(f"/api/v1/projects/{pid}/status", json={"status": "ON_HOLD"})
    resp = await client.put(f"/api/v1/projects/{pid}/status", json={"status": "ACTIVE"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_transition_completed_to_active_blocked(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    await client.put(f"/api/v1/projects/{pid}/status", json={"status": "COMPLETED"})
    resp = await client.put(f"/api/v1/projects/{pid}/status", json={"status": "ACTIVE"})
    assert resp.status_code == 400
    assert "Cannot transition" in resp.json()["message"]


@pytest.mark.asyncio
async def test_transition_cancelled_blocked(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    await client.put(f"/api/v1/projects/{pid}/status", json={"status": "CANCELLED"})

    for target in ["ACTIVE", "COMPLETED", "ON_HOLD"]:
        resp = await client.put(f"/api/v1/projects/{pid}/status", json={"status": target})
        assert resp.status_code == 400


# ===== Access Control =====


@pytest.mark.asyncio
async def test_engineer_gets_403(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "ENGINEER")
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_finance_can_view(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))

    await login_as_role(client, db, "FINANCE")
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_finance_cannot_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)

    await login_as_role(client, db, "FINANCE")
    resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dm_sees_own_portfolio(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    dm_resource = await _create_resource(db, "DM Self")
    other_dm = await _create_resource(db, "Other DM")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    pm = await _create_resource(db, "PM")

    await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm_resource.id, pm.id, name="DM-Own-Project"),
    )
    await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, other_dm.id, pm.id, name="Other-DM-Project"),
    )

    dm_user = await create_test_user(db, "DM", email=f"dm-{uuid.uuid4().hex[:6]}@test.com")
    dm_user.resource_id = dm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()["data"]]
    assert "DM-Own-Project" in names
    assert "Other-DM-Project" not in names


@pytest.mark.asyncio
async def test_pm_sees_own_portfolio(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    pm_resource = await _create_resource(db, "PM Self")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    dm = await _create_resource(db, "DM")
    other_pm = await _create_resource(db, "Other PM")

    await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm.id, pm_resource.id, name="PM-Own-Project"),
    )
    await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm.id, other_pm.id, name="Other-PM-Project"),
    )

    pm_user = await create_test_user(db, "PM", email=f"pm-{uuid.uuid4().hex[:6]}@test.com")
    pm_user.resource_id = pm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()["data"]]
    assert "PM-Own-Project" in names
    assert "Other-PM-Project" not in names


@pytest.mark.asyncio
async def test_dm_forced_dm_id_on_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    dm_resource = await _create_resource(db, "DM Creator")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    pm = await _create_resource(db, "PM")
    other_dm = await _create_resource(db, "Other DM Attempt")

    dm_user = await create_test_user(db, "DM", email=f"dm-create-{uuid.uuid4().hex[:6]}@test.com")
    dm_user.resource_id = dm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})
    payload = _project_payload(cl.id, other_dm.id, pm.id, name="DM-Created")
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["dm"]["id"] == str(dm_resource.id)


@pytest.mark.asyncio
async def test_pm_cannot_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm_resource = await _setup_project_deps(db)

    pm_user = await create_test_user(db, "PM", email=f"pm-no-create-{uuid.uuid4().hex[:6]}@test.com")
    pm_user.resource_id = pm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})
    resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm_resource.id))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_pm_cannot_transition_status(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    pm_resource = await _create_resource(db, "PM No Transition")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    dm = await _create_resource(db, "DM")

    create_resp = await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm.id, pm_resource.id),
    )
    pid = create_resp.json()["data"]["id"]

    pm_user = await create_test_user(db, "PM", email=f"pm-no-trans-{uuid.uuid4().hex[:6]}@test.com")
    pm_user.resource_id = pm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})
    resp = await client.put(f"/api/v1/projects/{pid}/status", json={"status": "COMPLETED"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_pm_limited_edit(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    pm_resource = await _create_resource(db, "PM Limited")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    dm = await _create_resource(db, "DM")

    create_resp = await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm.id, pm_resource.id),
    )
    pid = create_resp.json()["data"]["id"]

    pm_user = await create_test_user(db, "PM", email=f"pm-limited-{uuid.uuid4().hex[:6]}@test.com")
    pm_user.resource_id = pm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})

    resp = await client.put(f"/api/v1/projects/{pid}", json={"worklog_enabled": True})
    assert resp.status_code == 200
    assert resp.json()["data"]["worklog_enabled"] is True

    resp = await client.put(f"/api/v1/projects/{pid}", json={"name": "Hacked Name"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dm_detail_own_portfolio_ok(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    dm_resource = await _create_resource(db, "DM Detail")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    pm = await _create_resource(db, "PM")

    create_resp = await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, dm_resource.id, pm.id),
    )
    pid = create_resp.json()["data"]["id"]

    dm_user = await create_test_user(db, "DM", email=f"dm-det-{uuid.uuid4().hex[:6]}@test.com")
    dm_user.resource_id = dm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})
    resp = await client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dm_detail_other_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    dm_resource = await _create_resource(db, "DM Blocked")
    other_dm = await _create_resource(db, "Other DM Owner")
    cl = await _create_client(db, f"Client-{uuid.uuid4().hex[:4]}")
    pm = await _create_resource(db, "PM")

    create_resp = await client.post(
        "/api/v1/projects",
        json=_project_payload(cl.id, other_dm.id, pm.id),
    )
    pid = create_resp.json()["data"]["id"]

    dm_user = await create_test_user(db, "DM", email=f"dm-blocked-{uuid.uuid4().hex[:6]}@test.com")
    dm_user.resource_id = dm_resource.id
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})
    resp = await client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 403


# ===== Audit =====


@pytest.mark.asyncio
async def test_audit_on_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "project",
            AuditLog.entity_id == uuid.UUID(pid),
        )
    )
    entries = result.scalars().all()
    assert len(entries) >= 1
    assert any(e.action.value == "CREATE" for e in entries)


@pytest.mark.asyncio
async def test_audit_on_update(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    await client.put(f"/api/v1/projects/{pid}", json={"name": "Audited Name"})

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "project",
            AuditLog.entity_id == uuid.UUID(pid),
            AuditLog.field_name == "name",
        )
    )
    entries = result.scalars().all()
    assert len(entries) >= 1


@pytest.mark.asyncio
async def test_audit_on_status_transition(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    await client.put(f"/api/v1/projects/{pid}/status", json={"status": "ON_HOLD"})

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "project",
            AuditLog.entity_id == uuid.UUID(pid),
            AuditLog.field_name == "status",
        )
    )
    entries = result.scalars().all()
    assert len(entries) >= 1


# ===== Relationship serialization =====


@pytest.mark.asyncio
async def test_list_includes_relationship_names(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))

    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    item = resp.json()["data"][0]
    assert "client_name" in item
    assert "dm_name" in item
    assert "pm_name" in item


@pytest.mark.asyncio
async def test_detail_has_nested_relationships(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl, dm, pm = await _setup_project_deps(db)
    create_resp = await client.post("/api/v1/projects", json=_project_payload(cl.id, dm.id, pm.id))
    pid = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/projects/{pid}")
    data = resp.json()["data"]
    assert isinstance(data["client"], dict)
    assert "id" in data["client"]
    assert "name" in data["client"]
    assert isinstance(data["dm"], dict)
    assert isinstance(data["pm"], dict)
