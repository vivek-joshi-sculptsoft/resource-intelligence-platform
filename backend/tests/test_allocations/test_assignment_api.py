"""Tests for Assignment CRUD API — VRIP-49."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_as, login_as_role


async def _create_resource(client: AsyncClient, name: str = "Test Dev", **overrides) -> dict:
    payload = {
        "employee_id": f"EMP-{uuid.uuid4().hex[:6]}",
        "name": name,
        "designation": "Senior Developer",
        "technical_expertise": "Python",
        **overrides,
    }
    resp = await client.post("/api/v1/resources", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_client(client: AsyncClient, name: str = "Test Client") -> dict:
    resp = await client.post("/api/v1/clients", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_project(client: AsyncClient, client_id: str, dm_id: str, pm_id: str, **overrides) -> dict:
    payload = {
        "name": f"Project-{uuid.uuid4().hex[:6]}",
        "client_id": client_id,
        "type": "FIXED_PRICE",
        "dm_id": dm_id,
        "pm_id": pm_id,
        **overrides,
    }
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _setup_deps(client: AsyncClient) -> tuple[dict, dict, dict]:
    """Create client + 2 resources + project. Returns (project, resource1, resource2)."""
    cl = await _create_client(client)
    r1 = await _create_resource(client, name="DM Resource")
    r2 = await _create_resource(client, name="Dev Resource")
    proj = await _create_project(client, cl["id"], r1["id"], r2["id"])
    return proj, r1, r2


def _assignment_payload(resource_id: str, **overrides) -> dict:
    return {
        "resource_id": resource_id,
        "allocation_pct": 50,
        "billability_pct": 40,
        "is_shadow": False,
        "start_date": date.today().isoformat(),
        **overrides,
    }


# ── Happy Path ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_assignment(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    payload = _assignment_payload(r2["id"])

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["allocation_pct"] == 50
    assert data["billability_pct"] == 40
    assert data["resource"]["name"] == "Dev Resource"
    assert data["project"]["id"] == proj["id"]
    assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_list_project_assignments(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r1["id"]))
    await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


@pytest.mark.asyncio
async def test_list_project_assignments_filter_status(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r1["id"]))
    aid = resp.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))

    # Release one
    await client.post(f"/api/v1/assignments/{aid}/release")

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments?status=ACTIVE")
    assert len(resp.json()["data"]) == 1

    resp = await client.get(f"/api/v1/projects/{proj['id']}/assignments?status=RELEASED")
    assert len(resp.json()["data"]) == 1


@pytest.mark.asyncio
async def test_get_assignment(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/assignments/{aid}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == aid
    assert data["project"] is not None
    assert data["resource"] is not None


@pytest.mark.asyncio
async def test_update_assignment(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/assignments/{aid}", json={"allocation_pct": 80, "billability_pct": 60})
    assert resp.status_code == 200
    assert resp.json()["data"]["allocation_pct"] == 80
    assert resp.json()["data"]["billability_pct"] == 60


@pytest.mark.asyncio
async def test_list_resource_assignments(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))

    resp = await client.get(f"/api/v1/resources/{r2['id']}/assignments")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["project"] is not None


@pytest.mark.asyncio
async def test_effective_designation_fallback(client: AsyncClient, db: AsyncSession):
    """See FSD §11 — effective_designation uses project_designation if set, else resource.designation."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)

    # Without project_designation
    payload = _assignment_payload(r2["id"])
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    data = resp.json()["data"]
    assert data["effective_designation"] == "Senior Developer"

    # Release and create with project_designation
    await client.post(f"/api/v1/assignments/{data['id']}/release")
    payload["project_designation"] = "Lead Developer"
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    data = resp.json()["data"]
    assert data["effective_designation"] == "Lead Developer"


# ── Validation Tests (7 rules) ──────────────────────────


@pytest.mark.asyncio
async def test_validation_billability_exceeds_allocation(client: AsyncClient, db: AsyncSession):
    """Rule 3: billability_pct <= allocation_pct."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    payload = _assignment_payload(r2["id"], allocation_pct=50, billability_pct=60)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 422
    assert "billability_pct" in resp.json()["message"]


@pytest.mark.asyncio
async def test_validation_shadow_nonzero_billability(client: AsyncClient, db: AsyncSession):
    """Rule 4: shadow → billability must be 0."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    payload = _assignment_payload(r2["id"], is_shadow=True, billability_pct=10)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 422
    assert "Shadow" in resp.json()["message"]


@pytest.mark.asyncio
async def test_validation_shadow_zero_billability_ok(client: AsyncClient, db: AsyncSession):
    """Rule 4: shadow with billability=0 should succeed."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    payload = _assignment_payload(r2["id"], is_shadow=True, billability_pct=0)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_validation_end_date_before_start(client: AsyncClient, db: AsyncSession):
    """Rule 5: end_date must be after start_date."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    today = date.today()
    payload = _assignment_payload(r2["id"], start_date=today.isoformat(), end_date=(today - timedelta(days=1)).isoformat())

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 422
    assert "end_date" in resp.json().get("field", "") or "end_date" in resp.json()["message"]


@pytest.mark.asyncio
async def test_validation_end_date_equals_start(client: AsyncClient, db: AsyncSession):
    """Rule 5: end_date == start_date should also fail."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    today = date.today()
    payload = _assignment_payload(r2["id"], start_date=today.isoformat(), end_date=today.isoformat())

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_validation_duplicate_active_assignment(client: AsyncClient, db: AsyncSession):
    """Rule 6: one ACTIVE per (resource, project)."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    payload = _assignment_payload(r2["id"])

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 201

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 422
    assert "active assignment" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_validation_after_release_can_reassign(client: AsyncClient, db: AsyncSession):
    """Rule 6: after release, new ACTIVE assignment allowed."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    payload = _assignment_payload(r2["id"])

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    aid = resp.json()["data"]["id"]
    await client.post(f"/api/v1/assignments/{aid}/release")

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_validation_non_active_project(client: AsyncClient, db: AsyncSession):
    """Rule 7: no assignment on non-ACTIVE project."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)

    # Complete the project
    await client.put(f"/api/v1/projects/{proj['id']}/status", json={"status": "COMPLETED"})

    payload = _assignment_payload(r2["id"])
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 422
    assert "non-ACTIVE" in resp.json()["message"]


@pytest.mark.asyncio
async def test_validation_inactive_resource(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)

    # Create a separate resource not tied to any project as DM/PM
    r3 = await _create_resource(client, name="Inactive Dev")
    # Deactivate r3 (soft delete) — succeeds because r3 is not DM/PM on any project
    resp = await client.delete(f"/api/v1/resources/{r3['id']}")
    assert resp.status_code == 200

    payload = _assignment_payload(r3["id"])
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 422
    assert "not active" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_validation_nonexistent_resource(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    fake_id = str(uuid.uuid4())
    payload = _assignment_payload(fake_id)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_validation_nonexistent_project(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    fake_id = str(uuid.uuid4())
    r = await _create_resource(client)
    payload = _assignment_payload(r["id"])

    resp = await client.post(f"/api/v1/projects/{fake_id}/assignments", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pydantic_allocation_out_of_range(client: AsyncClient, db: AsyncSession):
    """Rules 1-2: Pydantic enforces allocation 1-100 and billability 0-100."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"], allocation_pct=0))
    assert resp.status_code == 422

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"], allocation_pct=101))
    assert resp.status_code == 422

    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"], billability_pct=-1))
    assert resp.status_code == 422


# ── Over-Allocation Warning ─────────────────────────────


@pytest.mark.asyncio
async def test_over_allocation_warning(client: AsyncClient, db: AsyncSession):
    """Over-allocation returns warning but doesn't block."""
    await login_as(client)
    cl = await _create_client(client)
    r1 = await _create_resource(client, name="DM")
    r2 = await _create_resource(client, name="Dev")

    p1 = await _create_project(client, cl["id"], r1["id"], r2["id"], name="P1")
    p2 = await _create_project(client, cl["id"], r1["id"], r2["id"], name="P2")

    # 70% on project 1
    await client.post(f"/api/v1/projects/{p1['id']}/assignments", json=_assignment_payload(r2["id"], allocation_pct=70))
    # 50% on project 2 — total 120%
    resp = await client.post(f"/api/v1/projects/{p2['id']}/assignments", json=_assignment_payload(r2["id"], allocation_pct=50))
    assert resp.status_code == 201
    assert "warnings" in resp.json()
    assert "120%" in resp.json()["warnings"][0]


# ── Update Validations ──────────────────────────────────


@pytest.mark.asyncio
async def test_update_revalidates_rules(client: AsyncClient, db: AsyncSession):
    """Update re-applies all 7 validations."""
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]

    # billability > allocation
    resp = await client.put(f"/api/v1/assignments/{aid}", json={"billability_pct": 90, "allocation_pct": 50})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_released_assignment_fails(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]

    await client.post(f"/api/v1/assignments/{aid}/release")

    resp = await client.put(f"/api/v1/assignments/{aid}", json={"allocation_pct": 80})
    assert resp.status_code == 422
    assert "released" in resp.json()["message"].lower()


# ── Release ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_release_assignment(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]

    resp = await client.post(f"/api/v1/assignments/{aid}/release")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "RELEASED"
    assert data["released_at"] is not None


@pytest.mark.asyncio
async def test_release_already_released_fails(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]

    await client.post(f"/api/v1/assignments/{aid}/release")
    resp = await client.post(f"/api/v1/assignments/{aid}/release")
    assert resp.status_code == 422


# ── Audit Logging ───────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_log_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))

    from app.modules.audit.models import AuditLog
    from sqlalchemy import select

    result = await db.execute(
        select(AuditLog).where(AuditLog.entity_type == "assignment", AuditLog.action == "CREATE")
    )
    entries = list(result.scalars().all())
    assert len(entries) >= 1


@pytest.mark.asyncio
async def test_audit_log_update(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]

    await client.put(f"/api/v1/assignments/{aid}", json={"allocation_pct": 80})

    from app.modules.audit.models import AuditLog
    from sqlalchemy import select

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "assignment",
            AuditLog.action == "UPDATE",
            AuditLog.field_name == "allocation_pct",
        )
    )
    entries = list(result.scalars().all())
    assert len(entries) >= 1


@pytest.mark.asyncio
async def test_audit_log_release(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, r1, r2 = await _setup_deps(client)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/assignments", json=_assignment_payload(r2["id"]))
    aid = resp.json()["data"]["id"]
    await client.post(f"/api/v1/assignments/{aid}/release")

    from app.modules.audit.models import AuditLog
    from sqlalchemy import select

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "assignment",
            AuditLog.action == "UPDATE",
            AuditLog.field_name == "status",
        )
    )
    entries = list(result.scalars().all())
    assert any(e.new_value and "RELEASED" in e.new_value for e in entries)


# ── Nonexistent assignment ──────────────────────────────


@pytest.mark.asyncio
async def test_get_nonexistent_assignment(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(f"/api/v1/assignments/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_assignment(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.put(f"/api/v1/assignments/{uuid.uuid4()}", json={"allocation_pct": 50})
    assert resp.status_code == 404
