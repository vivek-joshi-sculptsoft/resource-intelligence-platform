"""Tests for Milestone CRUD API + lifecycle transitions — VRIP-94."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import login_as, login_as_role


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


async def _create_client_entity(client: AsyncClient, name: str = "Test Client") -> dict:
    resp = await client.post("/api/v1/clients", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_project(
    client: AsyncClient, client_id: str, dm_id: str, pm_id: str, **overrides
) -> dict:
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


async def _setup_project(client: AsyncClient, **project_overrides) -> tuple[dict, dict, dict]:
    """Create client + dm/pm resources + project. Returns (project, dm_resource, pm_resource)."""
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, name="DM Resource")
    pm = await _create_resource(client, name="PM Resource")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"], **project_overrides)
    return proj, dm, pm


def _milestone_payload(**overrides) -> dict:
    return {
        "name": "Phase 1 Delivery",
        "amount": 50000.00,
        "planned_delivery_date": date.today().isoformat(),
        "sort_order": 1,
        **overrides,
    }


# ── Happy Path: Create / List / Get ──


@pytest.mark.asyncio
async def test_create_milestone(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["name"] == "Phase 1 Delivery"
    assert data["amount"] == 50000.0
    assert data["status"] == "PLANNED"
    assert data["sort_order"] == 1
    assert data["actual_delivery_date"] is None
    assert data["is_delayed"] is False


@pytest.mark.asyncio
async def test_create_milestone_rejects_non_fixed_price_project(
    client: AsyncClient, db: AsyncSession
):
    await login_as(client)
    proj, _, _ = await _setup_project(
        client, type="TIME_AND_MATERIAL", contract_end_date=(date.today() + timedelta(days=365)).isoformat()
    )

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    assert resp.status_code == 422
    assert resp.json()["field"] == "project_id"


@pytest.mark.asyncio
async def test_create_milestone_rejects_non_positive_amount(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload(amount=0)
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_milestones_ordered_by_sort_order(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)

    await client.post(
        f"/api/v1/projects/{proj['id']}/milestones",
        json=_milestone_payload(name="Second", sort_order=2),
    )
    await client.post(
        f"/api/v1/projects/{proj['id']}/milestones",
        json=_milestone_payload(name="First", sort_order=1),
    )

    resp = await client.get(f"/api/v1/projects/{proj['id']}/milestones")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()["data"]]
    assert names == ["First", "Second"]


@pytest.mark.asyncio
async def test_get_milestone_not_found(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)

    resp = await client.get(f"/api/v1/projects/{proj['id']}/milestones/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Update ──


@pytest.mark.asyncio
async def test_update_milestone_in_planned_status(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}",
        json={"name": "Updated Name", "amount": 60000.0},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Updated Name"
    assert data["amount"] == 60000.0


@pytest.mark.asyncio
async def test_update_milestone_rejected_outside_planned(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}", json={"name": "Should Fail"}
    )
    assert resp.status_code == 422
    assert resp.json()["field"] == "status"


# ── Status Lifecycle ──


@pytest.mark.asyncio
async def test_transition_planned_to_delivered_sets_actual_date(
    client: AsyncClient, db: AsyncSession
):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "DELIVERED"
    assert data["actual_delivery_date"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_transition_flags_delay_when_delivered_after_planned(
    client: AsyncClient, db: AsyncSession
):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones",
        json=_milestone_payload(
            planned_delivery_date=(date.today() - timedelta(days=5)).isoformat()
        ),
    )
    mid = create_resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_delayed"] is True


@pytest.mark.asyncio
async def test_full_forward_lifecycle_as_finance(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    for target in ["DELIVERED", "APPROVED", "INVOICED", "PAID"]:
        resp = await client.put(
            f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": target}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == target


@pytest.mark.asyncio
async def test_backward_transition_delivered_to_planned_clears_actual_date(
    client: AsyncClient, db: AsyncSession
):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]
    await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "PLANNED"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "PLANNED"
    assert data["actual_delivery_date"] is None


@pytest.mark.asyncio
async def test_backward_transition_approved_to_delivered(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]
    await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )
    await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "APPROVED"}
    )

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "DELIVERED"


@pytest.mark.asyncio
async def test_invalid_transition_rejected(client: AsyncClient, db: AsyncSession):
    """PLANNED -> APPROVED skips DELIVERED, not allowed."""
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "APPROVED"}
    )
    assert resp.status_code == 422
    assert resp.json()["field"] == "status"


@pytest.mark.asyncio
async def test_invoiced_and_paid_are_terminal(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]
    for target in ["DELIVERED", "APPROVED", "INVOICED"]:
        await client.put(
            f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": target}
        )

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "APPROVED"}
    )
    assert resp.status_code == 422

    await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "PAID"}
    )
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "INVOICED"}
    )
    assert resp.status_code == 422


# ── Role-Based Transition Permissions ──


@pytest.mark.asyncio
async def test_pm_can_transition_planned_to_approved(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, dm, pm = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    _, pm_user = await login_as_role(client, db, "PM")
    pm_user.resource_id = uuid.UUID(pm["id"])
    await db.commit()

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )
    assert resp.status_code == 200
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "APPROVED"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_pm_cannot_transition_approved_to_invoiced(client: AsyncClient, db: AsyncSession):
    """Only Finance/CEO/CTO may move APPROVED -> INVOICED."""
    await login_as(client)
    proj, dm, pm = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]
    for target in ["DELIVERED", "APPROVED"]:
        await client.put(
            f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": target}
        )

    _, pm_user = await login_as_role(client, db, "PM")
    pm_user.resource_id = uuid.UUID(pm["id"])
    await db.commit()

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "INVOICED"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_finance_can_transition_approved_to_invoiced(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]
    for target in ["DELIVERED", "APPROVED"]:
        await client.put(
            f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": target}
        )

    await login_as_role(client, db, "FINANCE")
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "INVOICED"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dm_or_pm_outside_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    # PM not linked to this project's resource_id
    await login_as_role(client, db, "PM")
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_has_no_access(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)

    await login_as_role(client, db, "ENGINEER")
    resp = await client.get(f"/api/v1/projects/{proj['id']}/milestones")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hr_has_no_access(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client)

    await login_as_role(client, db, "HR")
    resp = await client.get(f"/api/v1/projects/{proj['id']}/milestones")
    assert resp.status_code == 403


# ── Audit Logging ──


@pytest.mark.asyncio
async def test_create_milestone_creates_audit_log(client: AsyncClient, db: AsyncSession):
    from sqlalchemy import select

    from app.modules.audit.models import AuditLog

    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "Milestone", AuditLog.entity_id == uuid.UUID(mid)
        )
    )
    logs = result.scalars().all()
    assert any(log.action == "CREATE" for log in logs)


@pytest.mark.asyncio
async def test_status_transition_creates_audit_log(client: AsyncClient, db: AsyncSession):
    from sqlalchemy import select

    from app.modules.audit.models import AuditLog

    await login_as(client)
    proj, _, _ = await _setup_project(client)
    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones", json=_milestone_payload()
    )
    mid = create_resp.json()["data"]["id"]

    await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{mid}/status", json={"status": "DELIVERED"}
    )

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "Milestone",
            AuditLog.entity_id == uuid.UUID(mid),
            AuditLog.action == "UPDATE",
        )
    )
    logs = result.scalars().all()
    assert any(log.field_name == "status" for log in logs)
